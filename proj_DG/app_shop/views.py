import os
import json
import requests
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from app_user.models import Profile
from django.contrib import messages
from .models import APIToken, Balance
from app_trade.views import saveQuote
from django.shortcuts import render, redirect, get_object_or_404
from .utils import auth_api, make_post, get_token, generate_transaction_ref

def product_page_view(request):
    return render(request, 'app_shop/product_page.html')

def chk_price_view(request):
    # if not request.user.is_authenticated:
    #     return redirect('signin')  # Use your login URL name

    gold_price = make_post('GOLD_PRICE_ENDPOINT', {"timeFrame": "1D"})

    price = gold_price['data'][0]['buy_pretax']

    print(gold_price, price)
    # Token is now available, proceed to product page
    return render(request, 'app_shop/product_page.html', {'price': price})

def customer_detail(request):
    if not request.user.is_authenticated:
        return redirect('signin')
    custRefNo = Profile.objects.get(user=request.user).customerRefNo
    print("Customer Ref No:", custRefNo)
    balances = Balance.objects.filter(custRefNo=custRefNo)
    print("Balances fetched:", balances)

    context = {
        'balances': balances
    }

    return render(request, 'app_shop/balance.html', context)

def refresh_balance(request):
    if not request.user.is_authenticated:
        return redirect('signin')

    token_obj = get_token()
    # print("Using token to get price:", token_obj.token)
    custRefNo = Profile.objects.get(user=request.user).customerRefNo
    # print("Customer Ref No:", custRefNo)
    balance = make_post(token_obj.token, 'PORTFOLIO_ENDPOINT', {"customerRefNo": custRefNo})

    if balance:
        try:
            request_data = json.loads(balance)
            customer_name = request_data.get("customerName")
            kyc_status = request_data.get("kycStatus")
            balances = request_data.get("balances", [])
            for balance in balances:
                bal_quantity = balance.get("balQuantity")
                currency_pair = balance.get("currencyPair")
                blocked_quantity = balance.get("blockedQuantity")

                Balance.objects.create(
                        custRefNo=custRefNo,
                        customerName=customer_name,
                        kyc_status=kyc_status,
                        currency_pair=currency_pair,
                        bal_quantity=Decimal(bal_quantity),
                        blocked_quantity=Decimal(blocked_quantity)
                    )
            messages.success(request, "Balance data refreshed successfully!")

        except Exception as e:
            print("JSON decode error:", e)
    else:
        messages.success(request, "No Portfolio data found.")

    return redirect('balance', custRefNo=request.user.id)  # Redirect to the balance view with the user's ID

def tradeEstimateView(request, param1=None):
    if param1:
        first_char = param1[0]
        tp = "BUY" if first_char == 'B' else "SELL"          
        fourth_char = param1[3] if len(param1) > 3 else None
        cp = "XAU/INR" if fourth_char == 'G' else "XAG/INR"
    else:
        cp = "XAU/INR"
        tp = "BUY"
        #need to code for sell, lease and loan in a better way, sending parameter in URL is not a good idea

    if not request.user.is_authenticated:
        quote = make_post('ESTIMATE_ENDPOINT', {"currencyPair": cp, "type": tp})
        return render(request, 'app_shop/OneGram.html', {'estimate': quote['data']})
    else:
        try:
            profile = Profile.objects.get(user=request.user)
            transaction_ref = generate_transaction_ref(profile.customerRefNo, request.session.session_key)
            quote_data = {
                'customerRefNo': profile.customerRefNo,
                'currencyPair': cp,
                'transactionRefNo': transaction_ref
                }
            # print(quote_data)
            response = make_post('TRADE_BUY_ENDPOINT', payload=quote_data)
            quote_data = response["data"]
            quote_data['customerRefNo'] = profile.customerRefNo
            quote_data['transactionRefNo'] = transaction_ref
            quote_data['currencyPair'] = cp
            print("Response from Trade Buy API:", quote_data)
            if response.get("data"):
                saveQuote(request, quote_data)  # Save the quote data to the database
            else:
                messages.error(request, "Failed to generate quote.")
                return redirect('chk_price')

            return render(request, 'app_shop/initialQuote.html', {'estimate': quote_data})
        except Profile.DoesNotExist:
            messages.error(request, "Please update your profile for missing information.")
            return redirect('profile')
