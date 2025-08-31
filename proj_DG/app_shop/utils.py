import json
import base64
import requests
from django.conf import settings
from .api_config import ExternalAPI
from requests.exceptions import RequestException

def make_post(token, endpoint, payload):
    base_url = ExternalAPI.EXTERNAL_APIS['BASE_URL']
    ep = ExternalAPI.EXTERNAL_APIS[endpoint]
    url = f"{base_url}{ep}"

    headers = {
        'Accept': 'application/json',
        'Cookie': f'sessionId={token}',
        'Content-Type': 'application/json',
        }
    try:
        response = requests.post(url, json=payload, headers=headers)
        # Handle response
        if response.status_code == 200:
            data = response.json()  # Or response.text, depending on API
            # print("Status Code:", response.status_code)
            # print("Response Body:", response.text)
            return response.text
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None

    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None

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

    print("Status Code:", response.status_code)
    print("Response Body:", token)
    return response.status_code, token