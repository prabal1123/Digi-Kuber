# import requests
# from django.conf import settings

# def provider_login():
#     """
#     Uses Basic Auth (username + password) and partner_id header
#     to get sessionId from MMTC-PAMP.
#     """
#     url = f"{settings.BASE_URL}/security/login"

#     headers = {
#         "partner_id": settings.PARTNER_ID,
#         "Accept": "application/json",
#     }

#     auth = (settings.USR_ID, settings.PASSWORD)  # Basic Auth

#     resp = requests.post(url, headers=headers, auth=auth)
#     resp.raise_for_status()

#     data = resp.json()
#     return data.get("sessionId"), data


import requests
from django.conf import settings
from urllib.parse import urlparse

ALLOWED_API_HOSTS = [
    "cemuat.mmtcpamp.com",    # staging
    "www.mmtcpamp.com",       # production
]

def _validate_url(url):
    parsed = urlparse(url)
    if parsed.hostname not in ALLOWED_API_HOSTS:
        raise ValueError(f"SSRF blocked: {parsed.hostname} is not whitelisted.")

def provider_login():
    url = f"{settings.BASE_URL}/security/login"

    _validate_url(url)  # SSRF check

    headers = {
        "partner_id": settings.PARTNER_ID,
        "Accept": "application/json",
    }

    auth = (settings.USR_ID, settings.PASSWORD)

    resp = requests.post(url, headers=headers, auth=auth)
    resp.raise_for_status()

    data = resp.json()
    return data.get("sessionId"), data