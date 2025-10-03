from app_user.models import Profile
from django.conf import settings
from django.contrib import messages
from app_shop.utils import make_post, auth_api, get_token
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

def prepRequest(request, custRefID):
    customer = get_object_or_404(Profile, customerRefNo = custRefID)
    mobile = customer.user.phone
    refNo = customer.customerRefNo
    payload={}
    if refNo is None:
        fetchId = "mobile"
        fetchVal = mobile
    else:
        fetchId = "customerRefNo"
        fetchVal = refNo
    return (fetchId, fetchVal)  

def parseResp(response):
    print("Response in parseResp:", response)
    if response.status == 400:
        code = response.get("code")
        reason = response.get("reason")
        messages.warning(request, reason)
    else:
        messages.success(request, reason)
    return reason

@login_required
def manageCustomerView(request):
    # Get all users where profile exists and dgcustomerRefNo is null
    customers = Profile.objects.all()
    return render(request, 'app_admin/manageCustomer.html', {'customers': customers})

@login_required
def createProfileView(request, user_id):
    customer = get_object_or_404(Profile, customerRefNo = user_id)
    if customer.kycStatus == 1:
        kycStatus = 'Y'
    else:
        kycStatus = 'N'
    payload={
        "mobileNumber": customer.user.phone,
        "emailAddress": customer.user.email,
        "customerRefNo": customer.customerRefNo,
        "fullName": customer.name,
        "kycStatus": kycStatus,
        "kycInfo": {
            "nameProofType": customer.nameProofType,
            "nameProofId": customer.nameProofId,
            "addressProofType": customer.addressProofType,
            "addressProofId": customer.addressProofId,
        },
        "partner_id": settings.PARTNER_ID,
        "deliveryAddress": customer.deliveryAddress,
        "billingAddress": customer.billingAddress,
    }
    print("Payload:", payload)
    resp = make_post(endpoint='CREATE_PROFILE_ENDPOINT', payload=payload)
    print(resp)
    if resp:
        try:
            request_data = json.loads(resp)
            if isinstance(request_data, list) and request_data:
                dgCustomerRefNo = request_data[0].get('dgCustomerRefNo')
                if dgCustomerRefNo:
                    customer.dgcustomerRefNo = dgCustomerRefNo
                    customer.save()
            else:
                dgCustomerRefNo = None
        except Exception as e:
            dgCustomerRefNo = None
            print("JSON decode error:", e)
    else:
        dgCustomerRefNo = None
    return redirect('createCustomer')

@login_required
def fetchProfileView(request, user_id):
    customer = get_object_or_404(Profile, customerRefNo = user_id)
    mobile = customer.user.phone
    refNo = customer.customerRefNo
    tokenObj = get_token()
    payload={}
    if refNo is None:
        fetchId = "mobile"
        fetchVal = mobile
    else:
        fetchId = "customerRefNo"
        fetchVal = refNo
    resp = make_post(token=tokenObj.token, endpoint='GET_PROFILE_ENDPOINT', payload=payload, fetchId=fetchId, fetchVal=fetchVal)
    print(resp)
    # if resp:
    #     try:
    #         request_data = json.loads(resp)
    #         if isinstance(request_data, list) and request_data:
    #             dgCustomerRefNo = request_data[0].get('dgCustomerRefNo')
    #             if dgCustomerRefNo:
    #                 customer.dgcustomerRefNo = dgCustomerRefNo
    #                 customer.save()
    #         else:
    #             dgCustomerRefNo = None
    #     except Exception as e:
    #         dgCustomerRefNo = None
    #         print("JSON decode error:", e)
    # else:
    #     dgCustomerRefNo = None
    return redirect('home')
    
def updateDgCustId(request):
    customer = get_object_or_404(Profile, user=3)
    customer.dgcustomerRefNo = "C8K7A75QYG83" # URMH5ERYG172, 7OTY2ZCOE6ST
    customer.save()
    print("Updated")
    return redirect('home')

def activateCustomer(request, user_id):
    fetchId, fetchVal = prepRequest(request, custRefID=user_id)
    payload={}
    response = make_post(endpoint='ACTIVATE_CUSTOMER_ENDPOINT', payload=payload, fetchId=fetchId, fetchVal=fetchVal)
    reason = parseResp(response)
    return redirect('manageCustomer')

def deActivateCustomer(request, user_id):
    fetchId, fetchVal = prepRequest(request, custRefID=user_id)
    payload={}
    response = make_post(endpoint='DEACTIVATE_CUSTOMER_ENDPOINT', payload=payload, fetchId=fetchId, fetchVal=fetchVal)
    reason = parseResp(response)
    return redirect('manageCustomer')

def validateKYC(request, user_id):
    fetchId, fetchVal = prepRequest(request, custRefID=user_id)
    payload={}
    response = make_post(endpoint='VALIDATE_CUSTOMER_ENDPOINT', payload=payload, fetchId=fetchId, fetchVal=fetchVal)
    reason = parseResp(response)
    return redirect('manageCustomer')

def inValidateKYC(request, user_id):
    fetchId, fetchVal = prepRequest(request, custRefID=user_id)
    payload={}
    response = make_post(endpoint='INVALIDATE_CUSTOMER_ENDPOINT', payload=payload, fetchId=fetchId, fetchVal=fetchVal)
    reason = parseResp(response)
    return redirect('manageCustomer')

