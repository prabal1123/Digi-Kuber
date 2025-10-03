import os
import json
import requests
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from app_user.models import Profile
from django.contrib import messages
from .models import APIToken, Balance
from django.shortcuts import render, redirect
from .utils import auth_api, make_post, get_token

def buy_now_view(request):
    if not request.user.is_authenticated:
        return redirect('signin')  # Use your login URL name

    gold_price = make_post('GOLD_PRICE_ENDPOINT', {"timeFrame": "1D"})

    price = gold_price['data'][0]['buy_pretax']

    print(gold_price, price)
    # Token is now available, proceed to product page
    return render(request, 'app_shop/product_page.html', {'price': price})

def product_page_view(request):
    return render(request, 'app_shop/product_page.html')

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

def tradeEstimateView(request):
    # if not request.user.is_authenticated:
    #     return redirect('signin')

    quote = make_post('ESTIMATE_ENDPOINT', {"currencyPair": "XAU/INR", "type": "BUY"})

    if request.method == 'GET':
        estimate = {
                "totalAmount": "6105.73", 
                "quantity": "1.0000", 
                "quoteValidityTime": "480000", 
                "taxType": "CGST/SGST", 
                "tax1Amt": "88.92", 
                "tax2Amt": "88.92", 
                "tax1Perc": "1.50", 
                "tax2Perc": "1.50", 
                "preTaxAmount": "5927.89",
                "taxAmount": "177.84", 
                "quoteId": "MPLXpSCMI3gCjv8o1AInbtAia", 
                "type": "BUY", 
                "createdAt": "2023-04-04T07:58:30.039Z", 
                "currencyPair": "XAU/INR" 
            }
        return render(request, 'app_shop/initialQuote.html', {'estimate': quote['data']})
    else:
        return render(request, 'app_shop/initialQuote.html')

