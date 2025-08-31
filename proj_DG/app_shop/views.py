import os
import json
import requests
from .utils import auth_api, make_post
from .models import APIToken
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render, redirect

TOKEN_VALIDITY_MINUTES = 10

def buy_now_view(request):
    if not request.user.is_authenticated:
        return redirect('signin')  # Use your login URL name

    # Check for a valid token
    now = timezone.now()
    valid_since = now - timedelta(minutes=TOKEN_VALIDITY_MINUTES)
    token_obj = APIToken.objects.filter(created_at__gte=valid_since).order_by('-created_at').first()

    if not token_obj:
        # Request new token from API
        auth_status, auth_res = auth_api()
        if auth_status == 200:
            # token = auth_res.get('sessionID')
            token_obj = APIToken.objects.create(token=auth_res)
        else:
            return render(request, 'app_shop/token_error.html', {'error': auth_res.get('error')})
    
    gold_price = make_post(token_obj.token, 'GOLD_PRICE_ENDPOINT', {"timeFrame": "1D"})

    if gold_price:
        try:
            request_data = json.loads(gold_price)
            if isinstance(request_data, list) and request_data:
                price = request_data[0].get('buy_pretax')
            else:
                price = None
        except Exception as e:
            price = None
            print("JSON decode error:", e)
    else:
        price = None

    print(gold_price, price)
    # Token is now available, proceed to product page
    return render(request, 'app_shop/product_page.html', {'price': price})

def product_page_view(request):
    return render(request, 'app_shop/product_page.html')
