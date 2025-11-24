import json
import base64
import requests
from .models import APIToken
from django.utils import timezone
from django.conf import settings
from .api_config import ExternalAPI
from requests.exceptions import RequestException
from datetime import datetime, timedelta
import razorpay
from razorpay.errors import (
    BadRequestError,
    GatewayError,
    SignatureVerificationError,
    ServerError,
)

from django.conf import settings

TOKEN_VALIDITY_MINUTES = 10
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def get_token():
    try:
        token_obj = APIToken.objects.latest('created_at')
        print("Existing token found:", token_obj.token)
        if timezone.now() < token_obj.created_at + timedelta(minutes=TOKEN_VALIDITY_MINUTES):
            return token_obj
        else:
            print("Token expired, refreshing...")
            status_code, new_token = auth_api()
            if status_code == 200 and new_token:
                token_obj = APIToken.objects.create(token=new_token)
                print("New token obtained:", token_obj.token)
                return token_obj
            else:
                # print("Failed to refresh token")
                return render(request, 'app_shop/token_error.html', {'error': auth_res.get('error')})
    except APIToken.DoesNotExist:
        print("No existing token, obtaining new one...")
        status_code, new_token = auth_api()
        if status_code == 200 and new_token:
            token_obj = APIToken.objects.create(token=new_token)
            print("New token obtained:", token_obj.token)
            return token_obj
        else:
            # print("Failed to obtain initial token")
            return render(request, 'app_shop/token_error.html', {'error': auth_res.get('error')})

def make_post(endpoint, payload, fetchId=None, fetchVal=None):
    base_url = ExternalAPI.EXTERNAL_APIS['BASE_URL']
    ep = ExternalAPI.EXTERNAL_APIS[endpoint]
    url = f"{base_url}{ep}"
    token = get_token().token
    print("Making POST request to:", ep)
    headers = {
            'Accept': 'application/json',
            'Cookie': f'sessionId={token}',
            'Content-Type': 'application/json',
            }
    if fetchId is not None and fetchId == "mobile":
        headers['mobileNumber'] = fetchVal
    elif fetchId is not None and fetchId == "customerRefNo":
        headers['customerRefNo'] = fetchVal
    try:
        response = requests.post(url, json=payload, headers=headers)
        return_value = {
            "status": response.status_code,
            "code": None,
            "data": None,
            "reason": None
        }
        # paste the print block here to debug response
        try:
            content = response.json()
        except ValueError:
            content = response.text.strip()
        # ---- SUCCESS HANDLING ----
        if response.ok:  # 200–299
            if isinstance(content, (dict, list)):
                # JSON success response
                return_value["code"] = "Success"
                return_value["data"] = content
            elif isinstance(content, str):
                # Plain text success like "Data Validated"
                return_value["code"] = "Success"
                return_value["data"] = {"message": content}
            else:
                return_value["code"] = "Success"
                return_value["data"] = {"raw": str(content)}
         # ---- ERROR HANDLING ----
        else:
            if isinstance(content, dict):
                # Error codes like {"code": 39, "reason": "..."}
                return_value["code"] = str(content.get("code", "Error"))
                return_value["reason"] = content.get("reason") or str(content)
            else:
                return_value["code"] = "Error"
                return_value["reason"] = str(content)
        return return_value

    except requests.RequestException as e:
        return {
            "status": None,
            "code": "RequestFailed",
            "data": None,
            "reason": str(e)
        }

def auth_api():

    partner_id = settings.PARTNER_ID
    username = settings.USR_ID
    password = settings.PASSWORD
    url = settings.BASE_URL + ExternalAPI.EXTERNAL_APIS['AUTH_ENDPOINT']
    
    credentials = f'{username}:{password}'
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    auth_header = f'Basic {encoded_credentials}'

    headers = {
        'partner_id': partner_id,
        'Accept': 'application/json',
        'Authorization': auth_header,
        }

    response = requests.post(url, headers=headers)

    data = json.loads(response.text)  # Converts JSON string → dict
    token = data.get('sessionId')

    # print("Status Code:", response.status_code)
    # print("Response Body:", token)
    return response.status_code, token

def generate_transaction_ref(csRefNo, session):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"TRX-{csRefNo}-{session}-{timestamp}"

def create_razorpay_order(amount, currency='INR'):
    try:
        data = {
            'amount': amount,  # Razorpay expects amount in paise
            'currency': currency,
            'payment_capture': '1'  # Auto-capture payment after successful authorization
        }
        order = client.order.create(data=data)
        return order['id']
    except (BadRequestError, GatewayError, SignatureVerificationError, ServerError) as e:
        print("Razorpay Error:", e)
        return None

# print("###############################################################")
# print("Request URL:", url)
# print("###############################################################")
# print("Request Headers:", headers)
# print("###############################################################")
# print("Request Payload:", payload)
# print("###############################################################")
# print("Status Code:", response.status_code)
# print("###############################################################")
# print("Response recieved:", response)
# print("###############################################################")
# print("Response Content-Type:", response.headers['Content-Type'])
# print(response.text) 
# print("###############################################################")