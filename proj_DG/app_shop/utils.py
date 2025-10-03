import json
import base64
import requests
from .models import APIToken
from django.utils import timezone
from django.conf import settings
from .api_config import ExternalAPI
from requests.exceptions import RequestException
from datetime import datetime, timedelta

TOKEN_VALIDITY_MINUTES = 10

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
        # print("Status Code:", response.status_code)
        # print("###############################################################")
        # print("Response recieved:", response)
        # print("###############################################################")
        # # print("Response Content-Type:", response.headers['Content-Type'])
        # print(response.text) 
        # print("###############################################################")
        
        if response.status_code == 200:
            try:
                request_data = response.json()
                return_value = {}
                return_value["status"] = response.status_code
                return_value["code"] = "Success"
                return_value["data"] = request_data
                return return_value
            except Exception as e:
                if response.text == "OK":
                    return_value = {}
                    return_value["status"] = response.status_code
                    return_value["code"] = "Success"
                    return_value["reason"] = response.text
                    return return_value
                else:
                    print("JSON decode error:", e)
                    return None
        elif response.status_code == 400:
            request_data = response.json()
            return_value = {}
            return_value["status"] = response.status_code
            return_value["code"] = request_data.get("code")
            return_value["reason"] = request_data.get("reason")
            return return_value

    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return (f"Request failed: {e}")

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

