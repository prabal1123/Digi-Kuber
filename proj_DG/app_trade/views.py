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

def saveQuote(request, quote_data):
    check = Quote.objects.filter(quoteId=quote_data['quoteId']).exists()
    if check:
        Quote.objects.filter(quoteId=quote_data['quoteId']).update(
            customerRefNo=quote_data['customerRefNo'],
            totalAmt=quote_data['totalAmount'],
            preTaxAmt=quote_data['preTaxAmount'],
            quantity=quote_data['quantity'],
            taxAmount=float(quote_data['tax1Amt']) + float(quote_data['tax2Amt']),
            tax1Amt=quote_data['tax1Amt'],
            tax2Amt=quote_data['tax2Amt'],
            isValidated=True,
            )
        msg = "Existing Quote updated in database."
    else:
        Quote.objects.create(
            customerRefNo=quote_data['customerRefNo'],
            totalAmt=quote_data['totalAmount'],
            unitPriceAmt=quote_data['preTaxAmount'],
            preTaxAmt=quote_data['preTaxAmount'],
            quantity=quote_data['quantity'],
            taxAmount=quote_data['taxAmount'],
            tax1Perc=quote_data['tax1Perc'],
            tax2Perc=quote_data['tax2Perc'],
            tax1Amt=quote_data['tax1Amt'],
            tax2Amt=quote_data['tax2Amt'],
            # tax3Perc=quote_data['tax3Perc'],
            transactionOrderID=quote_data['transactionRefNo'],
            quoteId=quote_data['quoteId'],
            currencyPair=quote_data['currencyPair'],
            transactionType=quote_data['type'], #BUY/SELL/Transfer
            taxType=quote_data.get('taxType'),
            createdAt=quote_data['createdAt'],
            )

        msg = "New Quote saved to database."
    return msg

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

def validate_quote(request):
    ep = 'TRADE_VALIDATE_ENDPOINT_PG'
    if not request.user.is_authenticated:
        messages.info(request, "Please sign in to proceed with the quote validation.")
        return redirect('signin')  # Or your login/signup route
    elif request.method == 'POST':
        validate_data = {
            "customerRefNo": request.POST.get('cid'), 
            "calculationType": "Q", 
            "preTaxAmount": request.POST.get('pta'),
            "quantity": request.POST.get('qty'),
            "quoteId": request.POST.get('qid'), 
            "tax1Amt": request.POST.get('cgstAmt'),
            "tax2Amt": request.POST.get('sgstAmt'),
            "transactionDate": request.POST.get('createdAt'), 
            "transactionOrderID": request.POST.get('tid'), 
            "totalAmount": request.POST.get('totalAmount')
            }
        print("Quote Data Received for Validation:**************************************")
        print(validate_data)
        print(validate_data['totalAmount'])
        response = make_post(endpoint=ep, payload=validate_data)
        print("Response from Trade Validate API:", response)
        if response.get("status") == 200:
            saveQuote(request, validate_data)  # Save current quote data to db in Quote model
            orderId = create_razorpay_order(amount=validate_data['totalAmount']*100)
            return redirect('payment_page')
        else:
            messages.error(request, "Quote validation failed. Please try again.")
            return redirect('chk_price')  # or some other appropriate page
    # else:
    #     return redirect('chk_price')  # or some other appropriate page





