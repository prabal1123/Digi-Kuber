# import os
# import json
import requests
from django.shortcuts import render, redirect

from .models import TradeBuy, Quote
from app_user.models import Profile
from app_shop.utils import make_post #, auth_api, get_token

from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.contrib import messages

def post_login_handler(request):
    next_url = request.session.get('next', '/')
    return redirect(next_url)

def saveQuote(request, quote_data):
    Quote.objects.create(
            currencyPair=quote_data['currency_pair'],
            basePrice=quote_data['base_price'],
            quantity=quote_data['quantity'],
            value=quote_data['value'],
            tax1Perc=quote_data['tax1_perc'],
            tax2Perc=quote_data['tax2_perc'],
            sessionKey=request.session.session_key  # Track session for guest users
            user=quote_data['user'] if 'user' in quote_data else None,  # None if not logged in
            customer_ref_no=quote_data['customer_ref_no'] if 'customer_ref_no' in quote_data else None  # None if not logged in
        )

def validate_quote(request):
    quote_data = {
        'base_price': request.POST.get('today-price'),
        'quantity': request.POST.get('quantity'),
        'value': request.POST.get('pre-tax-amount'),
        'tax1_perc': request.POST.get('tax1Perc'),
        'tax2_perc': request.POST.get('tax2Perc'),
        'currency_pair': request.POST.get('currency-pair'),
    }

    if not request.user.is_authenticated:
        saveQuote(request, quote_data)  # Save current quote data to db in Quote model
        # request.session['next'] = '/quote/validate'  # or use request.path
        return redirect('signin')  # Or your login/signup route
    elif request.method == 'POST':
        quote_data['user'] = request.user
        profile = Profile.objects.get(user=request.user)
        if not profile.customerRefNo:
            saveQuote(request, quote_data)  # Save current quote data to db in Quote model
            messages.error(request, "Please update your profile for missing information.")
            return redirect('profile')
        else:
            quote_data['customer_ref_no'] = profile.customerRefNo
            print(quote_data)
            saveQuote(request, quote_data)  # Save current quote data to db in Quote model
            # proceed to validate API call
            pre_tax_total = Decimal(quote_data['value']) * Decimal(quote_data['quantity'])
            tax1_amt = pre_tax_total * Decimal(quote_data['tax1_perc']) / Decimal(100)
            tax2_amt = pre_tax_total * Decimal(quote_data['tax2_perc']) / Decimal(100)
            total_tax = tax1_amt + tax2_amt
            total_amount = pre_tax_total + total_tax    
        return redirect('quote_confirm')
    else:
        return redirect('quote_editor')  # or some other appropriate page

# def validateQuote(request):
#     if not request.user.is_authenticated:
#         # Save current quote data to session
#         quote_data = {
#             'quantity': request.POST.get('quantity'),
#             'amount': request.POST.get('amount'),
#             'quoteId': request.POST.get('quoteId'),
#             # Add other fields as needed
#         }
#         request.session['pending_quote'] = quote_data
#         # Save where to return after login
#         request.session['next'] = reverse('quote_editor')  # or use request.path
#         return redirect('signin')
#     else:
#         profile = Profile.objects.get(user=request.user)
#         if not profile.customerRefNo:
#             messages.error(request, "Please update your profile with Customer Reference Number.")
#             return redirect('profile')
#         else:
#             pass # proceed to new code to validate API call