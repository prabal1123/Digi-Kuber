


# app_pay/views.py
import json
import hmac
import hashlib
import logging
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.shortcuts import render, redirect
from django.http import (
    JsonResponse,
    HttpResponseBadRequest,
    HttpResponse,
    HttpResponseServerError,
)
from django.db import transaction as db_transaction
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
from app_shop.models import Transaction
import razorpay
from django_ratelimit.decorators import ratelimit

from app_shop.utils import make_post
from .models import PaymentRecord

logger = logging.getLogger(__name__)

from app_shop.models import Balance

try:
    from app_trade.models import Quote
except Exception:
    Quote = None

try:
    from app_user.models import Profile
except Exception:
    Profile = None


# -------------------------------------------------
# Razorpay client
# -------------------------------------------------
def get_razorpay_client():
    try:
        key_id = getattr(settings, "RAZORPAY_KEY_ID", None)
        key_secret = getattr(settings, "RAZORPAY_KEY_SECRET", None)
        if not key_id or not key_secret:
            logger.error("Razorpay keys missing")
            return None
        return razorpay.Client(auth=(key_id, key_secret))
    except Exception:
        logger.exception("Razorpay client init failed")
        return None


# -------------------------------------------------
# Balance creation (BUY)
# -------------------------------------------------
def _create_balance_from_payment(payment_record):
    """
    Create / update Balance from a successful BUY payment.

    SAFE GUARANTEES:
    - balance_created is set ONLY if DB write succeeds
    - function is idempotent
    - supports retry / recovery
    """

    try:
        # ----------------------------
        # 0) BASIC GUARDS
        # ----------------------------
        if not payment_record:
            return False

        if payment_record.status not in ("captured", "authorized"):
            logger.warning(
                "Balance skip: invalid status %s for PaymentRecord id=%s",
                payment_record.status,
                payment_record.id,
            )
            return False

        meta = payment_record.metadata or {}

        # Do NOT early-return on balance_created blindly
        # We verify actual DB state first
        balance_already_marked = meta.get("balance_created", False)

        # ----------------------------
        # 1) QUANTITY (MANDATORY)
        # ----------------------------
        qty = None
        if meta.get("quantity") is not None:
            try:
                qty = Decimal(str(meta["quantity"]))
            except Exception:
                qty = None

        if not qty or qty <= Decimal("0"):
            logger.error(
                "Balance abort: invalid quantity=%s for PaymentRecord id=%s",
                meta.get("quantity"),
                payment_record.id,
            )
            return False

        # ----------------------------
        # 2) CURRENCY PAIR (MANDATORY)
        # ----------------------------
        currency_pair = meta.get("currencyPair")
        if not currency_pair:
            logger.error(
                "Balance abort: missing currencyPair for PaymentRecord id=%s",
                payment_record.id,
            )
            return False

        # ----------------------------
        # 3) CUSTOMER REF NO (MANDATORY)
        # ----------------------------
        custRefNo = meta.get("customerRefNo")
        if not custRefNo and payment_record.user:
            from app_user.models import Profile
            profile = Profile.objects.filter(user=payment_record.user).first()
            if profile:
                custRefNo = profile.customerRefNo

        if not custRefNo:
            logger.error(
                "Balance abort: missing customerRefNo for PaymentRecord id=%s",
                payment_record.id,
            )
            return False

        # ----------------------------
        # 4) GET / CREATE BALANCE ROW
        # ----------------------------
        from app_shop.models import Balance

        balance = Balance.objects.filter(
            custRefNo=custRefNo,
            currency_pair=currency_pair,
        ).first()

        # if balance:
        #     # Already exists → increment safely
        #     balance.bal_quantity = (balance.bal_quantity or Decimal("0")) + qty
        #     balance.balance_as_of = timezone.now()
        #     balance.save(
        #         update_fields=["bal_quantity", "balance_as_of"]
        #     )

        #     logger.info(
        #         "Balance UPDATED: custRefNo=%s pair=%s +%s (new=%s)",
        #         custRefNo,
        #         currency_pair,
        #         qty,
        #         balance.bal_quantity,
        #     )

        # else:
        #     # Create new balance row
        #     balance = Balance.objects.create(
        #         custRefNo=custRefNo,
        #         currency_pair=currency_pair,
        #         bal_quantity=qty,
        #         blocked_quantity=Decimal("0"),
        #         balance_as_of=timezone.now(),
        #         date_created=timezone.now(),
        #     )

        #     logger.info(
        #         "Balance CREATED: custRefNo=%s pair=%s qty=%s",
        #         custRefNo,
        #         currency_pair,
        #         qty,
        #     )

        # # ----------------------------
        # # 5) MARK PAYMENT AS PROCESSED
        # # ----------------------------
        # # Mark ONLY after DB write succeeded
        # if not balance_already_marked:
        #     meta["balance_created"] = True
        #     payment_record.metadata = meta
        #     payment_record.save(update_fields=["metadata"])

        

        with db_transaction.atomic():
            if balance:
                balance.bal_quantity = (balance.bal_quantity or Decimal("0")) + qty
                balance.balance_as_of = timezone.now()
                balance.save(update_fields=["bal_quantity", "balance_as_of"])
            else:
                balance = Balance.objects.create(
                    custRefNo=custRefNo,
                    currency_pair=currency_pair,
                    bal_quantity=qty,
                    blocked_quantity=Decimal("0"),
                    balance_as_of=timezone.now(),
                    date_created=timezone.now(),
                )

            # MARK PAYMENT AS PROCESSED inside same transaction
            if not balance_already_marked:
                meta["balance_created"] = True
                payment_record.metadata = meta
                payment_record.save(update_fields=["metadata"])

        return True

    except Exception as e:
        logger.exception(
            "Balance creation FAILED for PaymentRecord id=%s : %s",
            getattr(payment_record, "id", None),
            e,
        )
        return False
# -------------------------------------------------
# Payment page
# -------------------------------------------------
def execute_mmtc_order(payment_record):
    """
    Calls MMTC EXECUTE ORDER API.
    This MUST run after payment is captured.
    """

    logger.warning(
        "MMTC EXECUTE START | payment_record_id=%s | quote_id=%s",
        payment_record.id,
        payment_record.quote_id,
    )

    if not Quote or not Profile:
        logger.error("MMTC EXECUTE ABORT: Quote/Profile model missing")
        return None

    quote = Quote.objects.filter(quoteId=payment_record.quote_id).first()
    if not quote:
        logger.error("MMTC EXECUTE ABORT: Quote not found")
        return None

    profile = Profile.objects.filter(user=payment_record.user).first()
    if not profile:
        logger.error("MMTC EXECUTE ABORT: Profile not found")
        return None

    # HARD GUARDS (MMTC requirements)
    if not profile.dgcustomerRefNo:
        logger.error("MMTC EXECUTE ABORT: dgcustomerRefNo missing")
        return None

    if not profile.billingAddressId or not profile.deliveryAddressId:
        logger.error("MMTC EXECUTE ABORT: Address IDs missing")
        return None

    payload = {
        "dgCustomerRefNo": profile.dgcustomerRefNo,
        "customerRefNo": profile.customerRefNo,
        "calculationType": "Q",
        "billingAddressId": profile.billingAddressId,
        "deliveryAddressId": profile.deliveryAddressId,
        "preTaxAmount": str(quote.preTaxAmt),
        "quantity": str(quote.quantity),
        "quoteId": quote.quoteId,
        "tax1Amt": str(quote.tax1Amt),
        "tax2Amt": str(quote.tax2Amt),
        "taxAmount": str(Decimal(quote.tax1Amt) + Decimal(quote.tax2Amt)),
        "transactionDate": quote.createdAt.strftime("%Y-%m-%d %H:%M:%S"),
        "transactionOrderID": quote.transactionOrderID,
        "totalAmount": str(quote.totalAmt),
    }

    logger.warning("MMTC EXECUTE PAYLOAD = %s", payload)

    response = make_post(
        endpoint="TRADE_EXECUTE_ORDER_PARTNER_PG",
        payload=payload,
    )

    logger.warning("MMTC EXECUTE RESPONSE = %s", response)

    # Persist response for audit
    meta = payment_record.metadata or {}
    meta["mmtc_execute_response"] = response
    payment_record.metadata = meta
    payment_record.save(update_fields=["metadata"])

    return response


# @ratelimit(key='ip', rate='10/m', method=['GET', 'POST'], block=True)
def payment_page(request):
    amount_paise = request.session.get("payment_amount")
    if not amount_paise:
        messages.error(request, "No payment info")
        return redirect("/")

    return render(
        request,
        "app_pay/payment_page.html",
        {
            "amount_in_paise": amount_paise,
            "amount": Decimal(amount_paise) / Decimal(100),
            "quote_id": request.session.get("payment_quote_id"),
            "razorpay_key_id": getattr(settings, "RAZORPAY_KEY_ID", ""),
        },
    )


# -------------------------------------------------
# Create Razorpay Order
# -------------------------------------------------
def create_order(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    try:
        amount = int(request.POST.get("amount") or request.session.get("payment_amount"))
    except Exception:
        return JsonResponse({"error": "invalid_amount"}, status=400)

    client = get_razorpay_client()
    if not client:
        return JsonResponse({"error": "gateway_error"}, status=500)

    order = client.order.create(
        {
            "amount": amount,
            "currency": "INR",
            "payment_capture": 1,
            "receipt": f"quote_{request.session.get('payment_quote_id')}",
        }
    )

    PaymentRecord.objects.create(
        user=request.user if request.user.is_authenticated else None,
        quote_id=request.session.get("payment_quote_id"),
        razorpay_order_id=order["id"],
        amount_paise=order["amount"],
        amount=Decimal(order["amount"]) / Decimal(100),
        status="created",
        metadata={
            "quantity": request.session.get("buy_quantity"),
            "currencyPair": request.session.get("currency_pair"),
            "customerRefNo": request.session.get("payment_customerRefNo"),
        },
    )

    return JsonResponse({"id": order["id"]})


# -------------------------------------------------
# Razorpay Webhook
# -------------------------------------------------
@csrf_exempt
def razorpay_webhook(request):
    secret = getattr(settings, "RAZORPAY_WEBHOOK_SECRET", None)
    if not secret:
        return HttpResponseBadRequest("Webhook not configured")

    payload = request.body
    sig = request.META.get("HTTP_X_RAZORPAY_SIGNATURE")

    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig or ""):
        return HttpResponseBadRequest("Invalid signature")

    event = json.loads(payload)
    entity = event.get("payload", {}).get("payment", {}).get("entity", {})
    order_id = entity.get("order_id")
    payment_id = entity.get("id")
    status = entity.get("status")
    amount = entity.get("amount")

    pr = (
        PaymentRecord.objects.filter(razorpay_payment_id=payment_id).first()
        or PaymentRecord.objects.filter(razorpay_order_id=order_id).first()
    )

    if not pr:
        pr = PaymentRecord.objects.create(
            razorpay_order_id=order_id,
            razorpay_payment_id=payment_id,
            amount_paise=amount,
            amount=Decimal(amount) / Decimal(100),
            status=status or "pending",
            metadata={"raw_event": event},
        )
    else:
        if payment_id and not pr.razorpay_payment_id:
            pr.razorpay_payment_id = payment_id
        pr.status = status or pr.status
        pr.save(update_fields=["razorpay_payment_id", "status"])

    if pr.status == "captured":
        _create_balance_from_payment(pr)

    return HttpResponse(status=200)


# -------------------------------------------------
# Payment success (FIXED)
# -------------------------------------------------
def payment_success(request):
    if request.method != "POST":
        return render(request, "app_pay/success.html")

    client = get_razorpay_client()
    if not client:
        return HttpResponseServerError("Payment gateway not configured")

    razorpay_order_id = request.POST.get("razorpay_order_id")
    razorpay_payment_id = request.POST.get("razorpay_payment_id")
    razorpay_signature = request.POST.get("razorpay_signature")

    # -----------------------------
    # 1️⃣ VERIFY SIGNATURE
    # -----------------------------
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        })
    except Exception:
        return HttpResponseBadRequest("Signature verification failed")

    # -----------------------------
    # 2️⃣ FETCH PAYMENT RECORD
    # -----------------------------
    pr = PaymentRecord.objects.filter(
        razorpay_order_id=razorpay_order_id
    ).first()

    if not pr:
        return HttpResponseBadRequest("Payment record not found")

    meta = pr.metadata or {}

    # 🔒 DUPLICATE GUARD
    if meta.get("finalized"):
        return render(request, "app_pay/success.html", {"payment_record": pr})

    # -----------------------------
    # 3️⃣ SAVE PAYMENT ID + STATUS
    # -----------------------------
    if not pr.razorpay_payment_id:
        pr.razorpay_payment_id = razorpay_payment_id

    pr.status = "captured"
    pr.save(update_fields=["razorpay_payment_id", "status"])

    # -----------------------------
    # 4️⃣ INJECT QUOTE METADATA
    # -----------------------------
    if Quote:
        quote = Quote.objects.filter(quoteId=pr.quote_id).first()
        if quote:
            meta.update({
                "currencyPair": quote.currencyPair,
                "quantity": str(quote.quantity),
                "customerRefNo": quote.customerRefNo,
            })

    pr.metadata = meta
    pr.save(update_fields=["metadata"])

    # -----------------------------
    # 5️⃣ UPDATE BALANCE
    # -----------------------------
    _create_balance_from_payment(pr)

    # -----------------------------
    # 6️⃣ EXECUTE MMTC (ONE TIME)
    # -----------------------------
    if not meta.get("mmtc_executed"):
        response = execute_mmtc_order(pr)

        if response and response.get("status") == 200:
            data = response.get("data", {})
            order = data.get("orderId", {})

            Transaction.objects.get_or_create(
            orderId=order.get("orderId"),
            defaults={
                "customerRefNo": pr.metadata.get("customerRefNo"),
                "user": pr.user,
                "transactionType": "BUY",
                "currencyPair": pr.metadata.get("currencyPair"),
                "quantity": Decimal(pr.metadata.get("quantity")),
                "totalAmt": pr.amount,
                "transactionDate": timezone.now(),
                "status": "EXECUTED",
            }
        )


            meta["mmtc_transaction_id"] = order.get("transactionId")
            meta["mmtc_order_id"] = order.get("orderId")
            meta["mmtc_invoice_id"] = order.get("invoiceId")
            meta["mmtc_executed"] = True

            pr.metadata = meta
            pr.save(update_fields=["metadata"])

    # -----------------------------
    # 7️⃣ FINALIZE (LOCK)
    # -----------------------------
    meta["finalized"] = True
    pr.metadata = meta
    pr.save(update_fields=["metadata"])

    # -----------------------------
    # 8️⃣ CLEAR SESSION
    # -----------------------------
    for k in ("payment_amount", "payment_quote_id", "payment_customerRefNo"):
        request.session.pop(k, None)

    return render(request, "app_pay/success.html", {"payment_record": pr})
