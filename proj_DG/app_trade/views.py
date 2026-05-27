import requests
from django.shortcuts import render, redirect
from decimal import Decimal
from datetime import timedelta

from .models import Quote
from app_user.models import Profile
from app_shop.api_config import ExternalAPI
from app_shop.utils import make_post, generate_transaction_ref, create_razorpay_order

from django.utils import timezone
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from decimal import Decimal, InvalidOperation
from datetime import datetime
from django.contrib.auth.decorators import login_required
from app_shop.utils import make_post
import uuid
from django_ratelimit.decorators import ratelimit
import razorpay

def post_login_handler(request):
    next_url = request.session.get('next', '/')
    return redirect(next_url)

def verify_payment(request):
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    payment_id = request.GET.get('payment_id')
    order_id = request.GET.get('order_id')
    signature = request.GET.get('signature')

    try:
        # Check signature validity
        client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        })
        # Payment is successful
        return JsonResponse({'status': 'success'})
    except razorpay.errors.SignatureVerificationError:
        # Payment failed
        return JsonResponse({'status': 'failure'})

# def saveQuote(request, quote_data):
#     check = Quote.objects.filter(quoteId=quote_data['quoteId']).exists()
#     if check:
#         Quote.objects.filter(quoteId=quote_data['quoteId']).update(
#             customerRefNo=quote_data['customerRefNo'],
#             totalAmt=quote_data['totalAmount'],
#             preTaxAmt=quote_data['preTaxAmount'],
#             quantity=quote_data['quantity'],
#             taxAmount=float(quote_data['tax1Amt']) + float(quote_data['tax2Amt']),
#             tax1Amt=quote_data['tax1Amt'],
#             tax2Amt=quote_data['tax2Amt'],
#             isValidated=True,
#             )
#         msg = "Existing Quote updated in database."
#     else:
#         Quote.objects.create(
#             customerRefNo=quote_data['customerRefNo'],
#             totalAmt=quote_data['totalAmount'],
#             unitPriceAmt=quote_data['preTaxAmount'],
#             preTaxAmt=quote_data['preTaxAmount'],
#             quantity=quote_data['quantity'],
#             taxAmount=quote_data['taxAmount'],
#             tax1Perc=quote_data['tax1Perc'],
#             tax2Perc=quote_data['tax2Perc'],
#             tax1Amt=quote_data['tax1Amt'],
#             tax2Amt=quote_data['tax2Amt'],
#             # tax3Perc=quote_data['tax3Perc'],
#             transactionOrderID=quote_data['transactionRefNo'],
#             quoteId=quote_data['quoteId'],
#             currencyPair=quote_data['currencyPair'],
#             transactionType=quote_data['type'], #BUY/SELL/Transfer
#             taxType=quote_data.get('taxType'),
#             createdAt=quote_data['createdAt'],
#             )

#         msg = "New Quote saved to database."
#     return msg

def saveQuote(request, quote_data):
    _, created = Quote.objects.update_or_create(
        quoteId=quote_data['quoteId'],
        defaults={
            'customerRefNo': quote_data['customerRefNo'],
            'totalAmt': quote_data['totalAmount'],
            'unitPriceAmt': quote_data['preTaxAmount'],
            'preTaxAmt': quote_data['preTaxAmount'],
            'quantity': quote_data['quantity'],
            'taxAmount': quote_data.get('taxAmount') or (
                float(quote_data.get('tax1Amt', 0)) + float(quote_data.get('tax2Amt', 0))
            ),
            'tax1Perc': quote_data.get('tax1Perc', 0),
            'tax2Perc': quote_data.get('tax2Perc', 0),
            'tax1Amt': quote_data.get('tax1Amt', 0),
            'tax2Amt': quote_data.get('tax2Amt', 0),
            'transactionOrderID': quote_data.get('transactionRefNo'),
            'currencyPair': quote_data.get('currencyPair', 'XAU/INR'),
            'transactionType': quote_data.get('type', 'BUY'),
            'taxType': quote_data.get('taxType'),
            'createdAt': quote_data.get('createdAt'),
            'isValidated': True,
        }
    )
    return "New Quote saved." if created else "Existing Quote updated."

@login_required
def generate_quote(request):
    ep = 'TRADE_BUY_ENDPOINT'
    if not request.user.is_authenticated:
        return redirect('signin')
    else:
        if request.method == 'POST':
            quote_data = {
                'value': request.POST.get('pta'),
                'currencyPair': request.POST.get('currency-pair'),
                'type': "A"
            }
            profile = Profile.objects.get(user=request.user)
            if not profile.customerRefNo:
                messages.error(request, "Please update your profile for missing information.")
                return redirect('profile')
            else:
                transaction_ref = generate_transaction_ref(profile.customerRefNo, request.session.session_key)
                quote_data['customerRefNo'] = profile.customerRefNo
                quote_data['transactionRefNo'] = transaction_ref
                print(quote_data)
                response = make_post(endpoint=ep, payload=quote_data)
                print("Response from Trade Buy API:", response['data'])
                if response.get("data"):
                    saveQuote(request, response['data'])  # Save the quote data to the database
                else:
                    messages.error(request, "Failed to generate quote.")
                    return redirect('chk_price')

            return render(request, 'app_shop/validateQuote.html', {'estimate': response['data']})
    return render(request, 'app_shop/validateQuote.html', {'estimate': response['data']})



@login_required
def validate_quote(request):
    from decimal import Decimal, InvalidOperation

    ep = 'TRADE_VALIDATE_ENDPOINT_PG'
    print("🔥 POST DATA =", request.POST)
    
    if request.method != 'POST':
        messages.error(request, "Invalid request.")
        return redirect('chk_price')

    currency_pair = requests.request.POST.get("currency-pair", "").strip()
    if currency_pair not in ("XAU/INR", "XAG/INR"):
        messages.error(request, "Invalid currency pair.")
        return redirect('chk_price')

    # validate customerRefNo
    customer_ref_no = request.POST.get('cid', '').strip()
    if not customer_ref_no or len(customer_ref_no) > 100:
        messages.error(request, "Invalid customer reference.")
        return redirect('chk_price')

    # validate quoteId
    quote_id = request.POST.get('qid', '').strip()
    if not quote_id or len(quote_id) > 512:
        messages.error(request, "Invalid quote ID.")
        return redirect('chk_price')

    # verify customerRefNo belongs to logged in user
    try:
        profile = Profile.objects.get(user=request.user)
        if profile.customerRefNo != customer_ref_no:
            messages.error(request, "Unauthorized.")
            return redirect('chk_price')
    except Profile.DoesNotExist:
        messages.error(request, "Profile not found.")
        return redirect('chk_price')

    # raw values
    pta_raw = request.POST.get('pta')
    cgst_raw = request.POST.get('cgstAmt')
    sgst_raw = request.POST.get('sgstAmt')
    tax_amount_raw = request.POST.get('taxAmount')
    qty_raw = requests.request.POST.get('qty')

    # compute unit price correctly (per-unit)
    try:
        pta_dec = Decimal(str(pta_raw))
        qty_dec = Decimal(str(qty_raw))
        unit_price_raw = (pta_dec / qty_dec).quantize(Decimal('0.01'))
    except Exception:
        messages.error(request, "Invalid numeric values for price/quantity.")
        return redirect('chk_price')

    def fmt(n):
        try:
            if n is None:
                return None
            d = Decimal(str(n))
            return format(d.quantize(Decimal('0.01')), 'f')
        except:
            return None

    def safe_div_pct(numer, denom):
        try:
            if numer is None or denom is None:
                return None
            n = Decimal(str(numer))
            d = Decimal(str(denom))
            if d == 0:
                return None
            return format((n / d * Decimal('100')).quantize(Decimal('0.01')), 'f')
        except:
            return None

    # GST percentage (normalize)
    tax1_perc = request.POST.get('tax1Perc') or safe_div_pct(cgst_raw, pta_raw)
    tax2_perc = request.POST.get('tax2Perc') or safe_div_pct(sgst_raw, pta_raw)
    if tax1_perc is not None:
        tax1_perc = str(Decimal(str(tax1_perc)).normalize())
    if tax2_perc is not None:
        tax2_perc = str(Decimal(str(tax2_perc)).normalize())

    tax_type = request.POST.get('taxType') or 'GST'

    # --- USE provider quote timestamp stored earlier ---
    transaction_date = request.session.get('quote_timestamp')
    # fallback for debugging only (not reliable for silver)
    if not transaction_date:
        transaction_date = request.POST.get('createdAt') or request.POST.get('transactionDate')

    # transaction refs
    transaction_refno = request.POST.get('tid') or request.POST.get('transactionRefNo') or request.POST.get('transactionOrderID')

    # clean quantity ("1.0000" → "1")
    try:
        #qty_clean = str(Decimal(qty_raw).normalize())
        #qty_clean = format(Decimal(qty_raw), "f")
        qty_clean = format(Decimal(qty_raw).quantize(Decimal("0.0000")),"f")


    except Exception:
        messages.error(request, "Invalid quantity.")
        return redirect('chk_price')
    print("🔥DEBUG QTY CLEAN =", qty_clean)

    # correct metal + product codes
    if currency_pair == "XAG/INR":
        metal_type = "SILVER"
        product_code = "XAG"
    else:
        metal_type = "GOLD"
        product_code = "XAU"

    # payload
    # validate_data = {
    #     "customerRefNo": request.POST.get('cid'),
    #     "calculationType": "Q",
    #     "preTaxAmount": fmt(pta_raw),
    #     "quantity": qty_clean,
    #     "quoteId": request.POST.get('qid'),

    #     "tax1Amt": fmt(cgst_raw),
    #     "tax2Amt": fmt(sgst_raw),
    #     "taxAmount": fmt(tax_amount_raw),
    #     "tax1Perc": tax1_perc,
    #     "tax2Perc": tax2_perc,
    #     "taxType": tax_type,

    #     "unitPriceAmt": fmt(unit_price_raw),
    #     "unitPrice": fmt(unit_price_raw),

    #     "transactionDate": transaction_date,
    #     "createdAt": transaction_date,
    #     "transactionOrderID": transaction_refno,
    #     #"transactionOrderID": str(uuid.uuid4()),

    #     "transactionRefNo": transaction_refno,
    #     #"transactionRefNo": str(uuid.uuid4()),

    #     "productCode": product_code,
    #     "assetCode": product_code,
    #     "metalCode": product_code,
    #     "instrumentCode": product_code,
    #     "metalType": metal_type,

    #     "totalAmount": fmt(request.POST.get('totalAmount')),
    #     "currencyPair": currency_pair,
    #     "transactionType": request.POST.get('type') or "BUY",
    #     "type": request.POST.get('type') or "BUY",
    # }
    validate_data = {
    "customerRefNo": request.POST.get("cid"),
    "calculationType": "A",

    "preTaxAmount": fmt(pta_raw),
    "quantity": qty_clean,              # "7.0000"
    "quoteId": request.POST.get("qid"),

    "tax1Amt": fmt(cgst_raw),
    "tax2Amt": fmt(sgst_raw),
    "taxAmount": fmt(tax_amount_raw),

    "transactionDate": transaction_date,
    "transactionOrderID": transaction_refno,

    "totalAmount": fmt(request.POST.get("totalAmount")),
}



    # remove None
    validate_data = {k: v for k, v in validate_data.items() if v is not None}

    print("\n🔥 VALIDATE QUOTE PAYLOAD =", validate_data)
    print("=====================================\n")

    response = make_post(endpoint=ep, payload=validate_data)
    print("Validate Response:", response)

    if response.get("status") == 200:
        saveQuote(request, validate_data)
        try:
            amt = Decimal(str(validate_data.get("totalAmount")))
            request.session['payment_amount'] = int((amt * Decimal('100')).quantize(Decimal('1')))
        except: 
            messages.error(request, "Invalid total amount for payment.")
            return redirect('chk_price')

        request.session['payment_quote_id'] = validate_data.get('quoteId')
        request.session['payment_customerRefNo'] = validate_data.get('customerRefNo')
        return redirect('/payments/payment/')

    messages.error(request, "Quote validation failed. Try again.")
    return redirect('chk_price')
