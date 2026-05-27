#app/shop/views.py
import os
import json
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django_ratelimit.decorators import ratelimit

from app_user.models import Profile
from .models import APIToken
from decimal import Decimal, InvalidOperation
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from app_shop.models import Holding,Balance,Transaction
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from app_trade.models import Quote
from app_trade.views import saveQuote
from .utils import (
    auth_api, make_post, get_token, generate_transaction_ref,
    get_gold_price, get_silver_price
)
from datetime import datetime, timedelta
import logging
from django.utils.timezone import now

def product_page_view(request):
    """
    Renders the product page with both gold and silver prices.
    Uses server-side fetch; JS polling is included in template if needed.
    """
    gold_price, gold_raw = get_gold_price()
    silver_price, silver_raw = get_silver_price()

    print("\n=== GOLD RAW ===")
    print(gold_raw)

    print("\n=== SILVER RAW ===")
    print(silver_raw)



    context = {
        'gold_price': gold_price,
        'silver_price': silver_price,
        # debug info (remove in production)
        # 'gold_raw': gold_raw,
        # 'silver_raw': silver_raw,
    }
    return render(request, 'app_shop/product_page.html', context)


def chk_price_view(request):
    """
    Legacy check — returns gold_price as currently expected by some routes.
    Kept for compatibility but safer.
    """
    res = make_post('GOLD_PRICE_ENDPOINT', {"timeFrame": "1D"})
    price = None
    try:
        if isinstance(res, dict) and res.get('data'):
            data = res.get('data')
            # If list-like
            if isinstance(data, (list, tuple)) and len(data) > 0 and isinstance(data[0], dict):
                price = data[0].get('buy_pretax') or data[0].get('buyPrice') or data[0].get('price')
            elif isinstance(data, dict):
                price = data.get('buy_pretax') or data.get('price') or data.get('last_price')
            if price is not None:
                price = float(price)
    except Exception as e:
        print("Error parsing chk_price_view response:", e)
        price = None

    return render(request, 'app_shop/product_page.html', {'price': price})

# def live_prices(request):
#     gold_price, _ = get_gold_price()
#     silver_price, _ = get_silver_price()

#     return JsonResponse({
#         "gold": gold_price,
#         "silver": silver_price,
#     })


def live_prices(request):

    hours = request.GET.get("hours")

    # ------------------------------
    # HOURLY DATA (for charts)
    # ------------------------------
    if hours:
        hours = int(hours)
        end_time = now().replace(minute=0, second=0, microsecond=0)

        gold_series = []
        silver_series = []

        for i in range(hours):
            ts = end_time - timedelta(hours=(hours - i))

            gold_price, _ = get_gold_price()     # replace with DB if available
            silver_price, _ = get_silver_price()

            gold_series.append([
                ts.isoformat(),
                float(gold_price)
            ])

            silver_series.append([
                ts.isoformat(),
                float(silver_price)
            ])

        return JsonResponse({
            "gold": gold_series,
            "silver": silver_series
        })

    # ------------------------------
    # LATEST PRICE (for cards)
    # ------------------------------
    gold_price, _ = get_gold_price()
    silver_price, _ = get_silver_price()

    return JsonResponse({
        "gold": float(gold_price),
        "silver": float(silver_price),
    })

def customer_detail(request):
    if not request.user.is_authenticated:
        return redirect('signin')

    try:
        custRefNo = Profile.objects.get(user=request.user).customerRefNo
    except Profile.DoesNotExist:
        messages.error(request, "Please complete your profile.")
        return redirect('profile')

    balances = Balance.objects.filter(custRefNo=custRefNo)
    context = {'balances': balances}
    return render(request, 'app_shop/balance.html', context)


def refresh_balance(request):
    if not request.user.is_authenticated:
        return redirect('signin')

    # Get customerRefNo from Profile
    try:
        custRefNo = Profile.objects.get(user=request.user).customerRefNo
    except Profile.DoesNotExist:
        messages.error(request, "Please complete your profile.")
        return redirect('profile')

    # Call API to fetch portfolio (only for KYC + blocked qty info)
    res = make_post('PORTFOLIO_ENDPOINT', {"customerRefNo": custRefNo})

    if not res or not isinstance(res, dict):
        messages.error(request, "Failed to fetch portfolio.")
        return redirect('balance', custRefNo=request.user.id)

    status = res.get('status')
    if not status or status < 200 or status >= 300:
        messages.error(request, f"Failed to fetch portfolio: {res.get('reason') or 'Unknown'}")
        return redirect('balance', custRefNo=request.user.id)

    data = res.get('data')
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception as e:
            print("JSON decode error in refresh_balance:", e)
            messages.error(request, "Malformed portfolio data.")
            return redirect('balance', custRefNo=request.user.id)

    customer_name = data.get("customerName")
    kyc_status = data.get("kycStatus")
    api_balances = data.get("balances") or []

    # ------------------------------------------------------------------
    # IMPORTANT:
    # DO NOT overwrite bal_quantity with API's 0.0000
    # API balance is NOT our internal wallet balance
    # ------------------------------------------------------------------

    for b in api_balances:
        try:
            currency_pair = b.get("currencyPair") or ""
            blocked_quantity = b.get("blockedQuantity") or 0

            # Update or create WITHOUT touching bal_quantity
            Balance.objects.update_or_create(
                custRefNo=custRefNo,
                currency_pair=currency_pair,
                defaults={
                    "customerName": customer_name,
                    "kyc_status": kyc_status,
                    "blocked_quantity": Decimal(blocked_quantity),
                    "balance_as_of": timezone.now(),  # we added this field
                }
            )

        except Exception as e:
            print("Error updating balance block:", e)
            continue

    messages.success(request, "Balance data refreshed successfully!")
    return redirect('balance', custRefNo=request.user.id)



logger = logging.getLogger(__name__)
@login_required
# def balance_page(request):
#     if not request.user.is_authenticated:
#         return redirect('signin')

#     user = request.user

#     # Purchase history (log)
#     holdings = Holding.objects.filter(user=user).order_by('-created_at')

#     # Load profile and custRefNo
#     try:
#         profile = Profile.objects.get(user=user)
#         custRefNo = profile.customerRefNo
#     except Profile.DoesNotExist:
#         messages.error(request, "Please complete your profile.")
#         return redirect('profile')

#     # Fetch balances for this customer
#     balances = Balance.objects.filter(custRefNo=custRefNo)

#     logger.debug("balance_page: found %s balance rows for custRefNo=%s", balances.count(), custRefNo)

#     gold_balance = Decimal("0")
#     silver_balance = Decimal("0")

#     for b in balances:
#         cp = (b.currency_pair or "").strip().upper()
#         try:
#             qty = Decimal(b.bal_quantity or 0)
#         except Exception:
#             qty = Decimal("0")
#         if "XAU" in cp:
#             gold_balance += qty
#         elif "XAG" in cp:
#             silver_balance += qty
#         else:
#             logger.debug("Unknown currency_pair for Balance id=%s pair=%r", getattr(b, 'id', None), cp)

#     context = {
#         "holdings": holdings,
#         "balances": balances,
#         "gold_balance": gold_balance,
#         "silver_balance": silver_balance,
#     }
#     return render(request, "app_shop/balance.html", context)



# def balance_page(request):
#     user = request.user

#     # -----------------------
#     # Load profile
#     # -----------------------
#     try:
#         profile = Profile.objects.get(user=user)
#         custRefNo = profile.customerRefNo
#     except Profile.DoesNotExist:
#         messages.error(request, "Please complete your profile.")
#         return redirect("profile")

#     # -----------------------
#     # Vault balances (SOURCE OF TRUTH)
#     # -----------------------
#     balances = Balance.objects.filter(custRefNo=custRefNo)

#     gold_balance = Decimal("0")
#     silver_balance = Decimal("0")

#     for b in balances:
#         cp = (b.currency_pair or "").upper()
#         qty = Decimal(b.bal_quantity or 0)

#         if "XAU" in cp:
#             gold_balance += qty
#         elif "XAG" in cp:
#             silver_balance += qty

#     # -----------------------
#     # Transaction Ledger (BUY + SELL)
#     # -----------------------
#     quotes = Quote.objects.filter(
#         customerRefNo=custRefNo
#     ).values(
#         "transactionType",
#         "currencyPair",
#         "quantity",
#         "totalAmt",
#         "transactionDate",
#     )

#     transactions = []

#     for q in quotes:
#         tx_type = q.get("transactionType")

#         # 🔒 Only real BUY / SELL
#         if tx_type not in ("BUY", "SELL"):
#             continue

#         qty = q.get("quantity")
#         if not qty or Decimal(qty) == 0:
#             continue

#         cp = (q.get("currencyPair") or "").upper()
#         if "XAU" in cp:
#             metal = "GOLD"
#         elif "XAG" in cp:
#             metal = "SILVER"
#         else:
#             continue

#         # 🔒 Block dummy SELL rows
#         if tx_type == "SELL" and Decimal(qty) > 0:
#             continue

#         transactions.append({
#             "type": tx_type,
#             "metal": metal,
#             "quantity": qty,      # SELL already negative
#             "total": q.get("totalAmt"),
#             "date": q.get("transactionDate"),
#         })

#     transactions.sort(
#         key=lambda x: x["date"] or timezone.now(),
#         reverse=True
#     )

#     context = {
#         "balances": balances,
#         "gold_balance": gold_balance,
#         "silver_balance": silver_balance,
#         "transactions": transactions,   # SINGLE SOURCE LEDGER
#     }

#     return render(request, "app_shop/balance.html", context)

def balance_page(request):
    user = request.user

    # -----------------------
    # Load profile
    # -----------------------
    try:
        profile = Profile.objects.get(user=user)
        custRefNo = profile.customerRefNo
    except Profile.DoesNotExist:
        messages.error(request, "Please complete your profile.")
        return redirect("profile")

    # -----------------------
    # Vault balances (MMTC SOURCE)
    # -----------------------
    balances = Balance.objects.filter(custRefNo=custRefNo)

    gold_balance = Decimal("0")
    silver_balance = Decimal("0")

    for b in balances:
        cp = (b.currency_pair or "").upper()
        qty = Decimal(b.bal_quantity or 0)

        if "XAU" in cp:
            gold_balance += qty
        elif "XAG" in cp:
            silver_balance += qty

    # -----------------------
    # TRANSACTION HISTORY (REAL ONLY)
    # -----------------------
    tx_qs = Transaction.objects.filter(
        customerRefNo=custRefNo,
        status="EXECUTED"
    ).order_by("-transactionDate")

    transactions = []

    for tx in tx_qs:
        cp = (tx.currencyPair or "").upper()

        if "XAU" in cp:
            metal = "GOLD"
        elif "XAG" in cp:
            metal = "SILVER"
        else:
            continue

        transactions.append({
            "type": tx.transactionType,
            "metal": metal,
            "quantity": abs(tx.quantity),
            "total": tx.totalAmt,
            "date": tx.transactionDate,
        })

    context = {
        "balances": balances,
        "gold_balance": gold_balance,
        "silver_balance": silver_balance,
        "transactions": transactions,
    }

    return render(request, "app_shop/balance.html", context)

# @ratelimit(key='ip', rate='20/m', method=['GET', 'POST'], block=True)
def tradeEstimateView(request, param1=None):
    """
    Original flow preserved.
    - GET: call TRADE_BUY_ENDPOINT (same as before), show estimate.
    - POST: two actions:
        - action=update_qty -> recalc totals with new quantity and re-render
        - action=pay -> create razorpay order and re-render with `razorpay_order_id` (and amount)
    """
    # determine currency pair & type (same as original)
    if param1:
        first_char = param1[0]
        tp = "BUY" if first_char == 'B' else "SELL"
        fourth_char = param1[3] if len(param1) > 3 else None
        cp = "XAU/INR" if fourth_char == 'G' else "XAG/INR"
    else:
        cp = "XAU/INR"
        tp = "BUY"

    # default quantity (grams or units) 
    default_qty = Decimal('1')  # default 1 gram

    # If user is not authenticated, keep original simple behaviour
    if not request.user.is_authenticated:
        quote = make_post('ESTIMATE_ENDPOINT', {"currencyPair": cp, "type": tp})
        # return render(request, 'app_shop/OneGram.html', {'estimate': quote.get('data') if isinstance(quote, dict) else None}) 
        return render(
        request,'app_shop/initialQuote.html',
        {
        'estimate': quote.get('data') if isinstance(quote, dict) else None
        }
    )


    # For authenticated users, handle GET and POST
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        messages.error(request, "Please update your profile for missing information.")
        return redirect('profile')

    # Build the payload and request quote from backend (same as before)
    transaction_ref = generate_transaction_ref(profile.customerRefNo, request.session.session_key or '')
    payload = {
        'customerRefNo': profile.customerRefNo,
        'currencyPair': cp,
        'transactionRefNo': transaction_ref,
        'type': 'BUY'
    }

    response = make_post('TRADE_BUY_ENDPOINT', payload=payload)
    if not response or response.get('status') is None:
        messages.error(request, "Failed to generate quote.")
        return redirect('chk_price')

    quote_data = response.get('data')
    if not quote_data:
        messages.error(request, "Failed to generate quote.")
        return redirect('chk_price')

    # normalize to dict (if list returned, take first element)
    if isinstance(quote_data, (list, tuple)) and len(quote_data) > 0 and isinstance(quote_data[0], dict):
        quote_flat = quote_data[0].copy()
    elif isinstance(quote_data, dict):
        quote_flat = quote_data.copy()
    else:
        # fallback: wrap primitive
        quote_flat = {'value': quote_data}

    # ensure basic fields exist
    quote_flat['customerRefNo'] = profile.customerRefNo
    quote_flat['transactionRefNo'] = transaction_ref
    quote_flat['currencyPair'] = cp
    quote_flat['type'] = 'BUY'


    # determine unit price (prefer buy_pretax or price)
    unit_price = None
    for k in ('buy_pretax', 'buyPrice', 'price', 'rate'):
        if k in quote_flat and quote_flat[k] not in (None, ''):
            try:
                unit_price = Decimal(str(quote_flat[k]))
                break
            except (InvalidOperation, TypeError):
                unit_price = None

    # handle POST actions (update quantity or pay)
    razorpay_order_id = None
    razorpay_amount = None  # in paise (int) for Razorpay
    qty = default_qty

    if request.method == 'POST':
        action = request.POST.get('action')
        # quantity from form (fallback to default)
        # qty_str = request.POST.get('quantity')
        # try:
        #     if qty_str:
        #         qty = Decimal(qty_str)
        #         if qty <= 0:
        #             qty = default_qty
        # except (InvalidOperation, TypeError):
        #     qty = default_qty

        qty_str = request.POST.get('quantity')
        MAX_QTY = Decimal('10000')  # max 10kg gold/silver per order
        try:
            if qty_str:
                qty = Decimal(qty_str)
                if qty <= 0 or qty > MAX_QTY:
                    messages.error(request, "Invalid quantity. Must be between 0 and 10,000 grams.")
                    return redirect('chk_price')
        except (InvalidOperation, TypeError):
            qty = default_qty
        # recalc total
        if unit_price is not None:
            total_amount = (unit_price * qty).quantize(Decimal('0.01'))  # 2 decimals
        else:
            total_amount = None

        if action == 'update_qty':
            # re-render with updated totals (no payment yet)
            estimate_pairs = []
            # priority fields
            if unit_price is not None:
                estimate_pairs.append(('Unit Price', f"{unit_price:.2f}"))
                estimate_pairs.append(('Quantity', str(qty)))
                estimate_pairs.append(('Total', f"{total_amount:.2f}"))
            # include other fields
            for k, v in quote_flat.items():
                if k not in ('buy_pretax', 'price', 'rate'):
                    estimate_pairs.append((k, v))
            # save quote (best-effort)
            try:
                print("DEBUG QUOTE (PAY) →", quote_flat)
                saveQuote(request, quote_flat)
            except Exception as e:
                print("Warning: saveQuote failed", e)

            return render(request, 'app_shop/initialQuote.html', {
                'estimate': quote_flat,
                'estimate_pairs': estimate_pairs,
                'unit_price': unit_price,
                'quantity': qty,
                'total_amount': total_amount,
                'razorpay_order_id': None
            })

        elif action == 'pay':
            request.session["buy_quantity"] = str(qty)
            request.session["currency_pair"] = cp  # cp = "XAU/INR" or "XAG/INR"
            request.session["payment_customerRefNo"] = profile.customerRefNo

            print("DEBUG SESSION → buy_quantity =", request.session.get("buy_quantity"))
            print("DEBUG SESSION → currency_pair =", request.session.get("currency_pair"))
            print("DEBUG SESSION → payment_customerRefNo =", request.session.get("payment_customerRefNo"))


            # create razorpay order and show payment details
            if unit_price is None:
                messages.error(request, "Cannot proceed to payment: unit price unavailable.")
                return redirect('chk_price')
            request.session['payment_quantity'] = str(qty)

            try:
                total_amount = (unit_price * qty).quantize(Decimal('0.01'))
                # razorpay expects amount in paise (integer)
                razorpay_amount_int = int((total_amount * Decimal('100')).to_integral_value())
                razorpay_order_id = create_razorpay_order(razorpay_amount_int, currency='INR')
                razorpay_amount = razorpay_amount_int
                if not razorpay_order_id:
                    messages.error(request, "Payment initialization failed. Try again.")
                    # fallthrough to render page with error
            except Exception as e:
                print("Error creating razorpay order:", e)
                messages.error(request, "Payment initialization error.")
                razorpay_order_id = None

            # Save quote (best-effort)
            try:
                saveQuote(request, quote_flat)
            except Exception as e:
                print("Warning: saveQuote failed", e)

            estimate_pairs = []
            if unit_price is not None:
                estimate_pairs.append(('Unit Price', f"{unit_price:.2f}"))
                estimate_pairs.append(('Quantity', str(qty)))
                estimate_pairs.append(('Total', f"{total_amount:.2f}"))
            for k, v in quote_flat.items():
                if k not in ('buy_pretax', 'price', 'rate'):
                    estimate_pairs.append((k, v))

            return render(request, 'app_shop/initialQuote.html', {
                'estimate': quote_flat,
                'estimate_pairs': estimate_pairs,
                'unit_price': unit_price,
                'quantity': qty,
                'total_amount': total_amount,
                'razorpay_order_id': razorpay_order_id,
                'razorpay_amount': razorpay_amount
            })

    # Default GET render
    # prepare estimate_pairs for template (unit price first)
    estimate_pairs = []
    if unit_price is not None:
        estimate_pairs.append(('Unit Price', f"{unit_price:.2f}"))
        estimate_pairs.append(('Quantity', str(default_qty)))
        
        total_default = (unit_price * default_qty).quantize(Decimal('0.01'))
        estimate_pairs.append(('Total', f"{total_default:.2f}"))

    for k, v in quote_flat.items():
        if k not in ('buy_pretax', 'price', 'rate'):
            estimate_pairs.append((k, v))

    # Save quote (best-effort)
    try:
        saveQuote(request, quote_flat)
    except Exception as e:
        print("Warning: saveQuote failed", e)

    return render(request, 'app_shop/initialQuote.html', {
        'estimate': quote_flat,
        'estimate_pairs': estimate_pairs,
        'unit_price': unit_price,
        'quantity': default_qty,
        'total_amount': (unit_price * default_qty).quantize(Decimal('0.01')) if unit_price is not None else None,
        'razorpay_order_id': None
    })
