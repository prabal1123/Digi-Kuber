# import re
# from django.shortcuts import render, redirect
# from django.contrib import messages
# from django.contrib.auth import login, logout
# from app_user.models import Profile
# from django.conf import settings
# from app_shop.utils import make_post


# from app_user.forms import ProfileForm

# from .forms import (
#     SignupForm,
#     PasswordForm,
#     #ProfileForm,
#     SigninForm,
#     EmailTokenConfirmForm,
# )
# from .models import (
#     CustomUser,
#     EmailVerification,
#     PhoneVerification,
# )
# from .utils import send_confirmation_email, send_otp


# def is_email_or_phone(value):
#     if re.match(r"[^@]+@[^@]+\.[^@]+", value):
#         return 'email'
#     elif re.match(r"^\+?\d{10,15}$", value):
#         return 'phone'
#     return None


# def home_view(request):
#     return render(request, 'home.html')


# def signup_view(request):
#     if request.method == 'POST':
#         form = SignupForm(request.POST)
#         if form.is_valid():
#             identifier = form.cleaned_data['email_or_phone']
#             kind = is_email_or_phone(identifier)

#             if kind == 'email':
#                 token = EmailVerification.generate_token()
#                 EmailVerification.objects.update_or_create(
#                     email=identifier,
#                     defaults={'token': token, 'is_used': False}

#                 )
#                 send_confirmation_email(identifier, token)
#                 messages.success(request, 'Confirmation email sent')
#                 return render(
#                     request,
#                     'app_login/confirm_email_sent.html',
#                     {'email': identifier}
#                 )

#             elif kind == 'phone':
#                 otp = PhoneVerification.generate_otp()
#                 PhoneVerification.objects.update_or_create(
#                     phone_number=identifier,
#                     defaults={'otp': otp, 'used': False}
#                 )
#                 request.session['pending_phone'] = identifier
#                 send_otp(identifier, otp)
#                 return redirect('confirm_phone')

#             else:
#                 form.add_error('email_or_phone', 'Enter a valid email or phone')

#     else:
#         form = SignupForm()

#     return render(request, 'app_login/signup.html', {'form': form})


# def confirm_email_view(request):
#     token = request.GET.get('token')

#     if not token:
#         messages.error(request, "Invalid confirmation link")
#         return redirect('signup')

#     if request.method == 'POST':
#         try:
#             verification = EmailVerification.objects.get(
#                 token=token,
#                 is_used=False
#             )
#         except EmailVerification.DoesNotExist:
#             messages.error(request, "Invalid or expired code")
#             return render(request, 'app_login/confirm_email.html')

#         if not verification.is_valid():
#             messages.error(request, "Token expired")
#             return render(request, 'app_login/confirm_email.html')

#         verification.is_used = True
#         verification.save()

#         request.session['confirmed_email'] = verification.email
#         return redirect('create_password')

#     return render(request, 'app_login/confirm_email.html')


# def confirm_phone_view(request):
#     if request.method == 'POST':
#         otp = request.POST.get('otp')
#         phone = request.session.get('pending_phone')

#         try:
#             verification = PhoneVerification.objects.get(
#             phone_number=phone,
#             otp=otp,
#             is_used=False
#         )

#         except PhoneVerification.DoesNotExist:
#             return render(
#                 request,
#                 'app_login/confirm_phone.html',
#                 {'error': 'Invalid OTP'}
#             )

#         verification.is_used = True

#         verification.save()

#         request.session['confirmed_phone'] = phone
#         return redirect('create_password')

#     return render(request, 'app_login/confirm_phone.html')


# def create_password_view(request):
#     email = request.session.get('confirmed_email')
#     phone = request.session.get('confirmed_phone')

#     if not email and not phone:
#         return redirect('signup')

#     if request.method == 'POST':
#         form = PasswordForm(request.POST)
#         if form.is_valid():

#             if email and CustomUser.objects.filter(email=email).exists():
#                 form.add_error(None, 'Email already registered')
#                 return render(request, 'app_login/create_password.html', {'form': form})

#             if phone and CustomUser.objects.filter(phone=phone).exists():
#                 form.add_error(None, 'Phone already registered')
#                 return render(request, 'app_login/create_password.html', {'form': form})

#             if email:
#                 user = CustomUser.objects.create(email=email)
#             else:
#                 user = CustomUser.objects.create(phone=phone)

#             user.set_password(form.cleaned_data['password'])
#             user.save()

#             request.session['user_id'] = user.id
#             request.session.modified = True
#             request.session.pop('confirmed_email', None)
#             request.session.pop('confirmed_phone', None)
#             request.session.pop('pending_phone', None)

#             #return redirect('complete_details')
#             return redirect('complete_profile')

#     else:
#         form = PasswordForm()

#     return render(request, 'app_login/create_password.html', {'form': form})


# def complete_details_view(request):
#     user_id = request.session.get('user_id')
#     if not user_id:
#         return redirect('signup')

#     user = CustomUser.objects.get(id=user_id)

#     # 🔥 ENSURE PROFILE EXISTS
#     profile, _ = Profile.objects.get_or_create(user=user)

#     if request.method == 'POST':
#         form = ProfileForm(request.POST, instance=profile)
#         if form.is_valid():
#             profile = form.save()

#             # 🔥 CREATE DG CUSTOMER HERE
#             create_dg_customer(profile)

#             request.session.pop('user_id', None)
#             return redirect('signin')
#     else:
#         form = ProfileForm(instance=profile)

#     return render(request, 'app_login/update_details.html', {'form': form})


# def signin_view(request):
#     if request.method == 'POST':
#         form = SigninForm(request.POST)
#         if form.is_valid():
#             identifier = form.cleaned_data['email_or_phone']
#             password = form.cleaned_data['password']
#             kind = is_email_or_phone(identifier)

#             if kind == 'email':
#                 user = CustomUser.objects.filter(email=identifier).first()
#             elif kind == 'phone':
#                 user = CustomUser.objects.filter(phone=identifier).first()
#             else:
#                 user = None

#             if user and user.check_password(password):
#                 login(request, user)
#                 return redirect('home')
#             else:
#                 form.add_error(None, 'Invalid credentials')

#     else:
#         form = SigninForm()

#     return render(request, 'app_login/signin.html', {'form': form})


# def logout_view(request):
#     logout(request)
#     return redirect('home')


# def complete_profile_view(request):
#     user_id = request.session.get("user_id")
#     if not user_id:
#         return redirect("signup")

#     user = CustomUser.objects.get(id=user_id)
#     profile, _ = Profile.objects.get_or_create(user=user)

#     if request.method == "POST":
#         form = ProfileForm(request.POST, instance=profile, user=user)
#         if form.is_valid():
#             entered_phone = form.cleaned_data.get("phone")
#             if entered_phone and not user.phone:
#                 user.phone = entered_phone
#                 user.save(update_fields=["phone"])
                
#             profile = form.save(commit=False)
#             profile.user = user

#             # ---------- build addresses ----------
#             billingAddress = {
#                 "line1": form.cleaned_data.get("bLine1"),
#                 "line2": form.cleaned_data.get("bLine2"),
#                 "city": form.cleaned_data.get("bCity"),
#                 "state": form.cleaned_data.get("bState"),
#                 "zip": int(form.cleaned_data.get("bZip") or 0),
#                 "country": "India",
#                 "mobileNumber": user.phone,
#                 "statecode": "07",
#             }

#             deliveryAddress = {
#                 "line1": form.cleaned_data.get("dLine1"),
#                 "line2": form.cleaned_data.get("dLine2"),
#                 "city": form.cleaned_data.get("dCity"),
#                 "state": form.cleaned_data.get("dState"),
#                 "zip": int(form.cleaned_data.get("dZip") or 0),
#                 "country": "India",
#                 "mobileNumber": user.phone,
#                 "statecode": "07",
#             }

#             if form.cleaned_data.get("same_as_delivery"):
#                 profile.billingAddress = billingAddress
#                 profile.deliveryAddress = billingAddress
#             else:
#                 profile.billingAddress = billingAddress
#                 profile.deliveryAddress = deliveryAddress

#             if not profile.billingAddressId:
#                 profile.billingAddressId = f"{profile.customerRefNo}_BILL"

#             profile.save()

#             # ---------- DG CREATE PROFILE ----------
#             if not profile.dgcustomerRefNo:
#                 payload = {
#                     "mobileNumber": user.phone,
#                     "customerRefNo": profile.customerRefNo,
#                     "fullName": profile.name,
#                     "kycStatus": profile.kycStatus,
#                     "partner_id": settings.PARTNER_ID,
#                     "emailAddress": user.email,
#                     "billingAddress": profile.billingAddress,
#                     "deliveryAddress": profile.deliveryAddress,
#                 }

#                 resp = make_post(endpoint="CREATE_PROFILE_ENDPOINT", payload=payload)
#                 if resp and resp.get("status") == 200:
#                     data = resp.get("data")
#                     if isinstance(data, list) and data:
#                         profile.dgcustomerRefNo = data[0].get("dgCustomerRefNo")
#                         profile.save(update_fields=["dgcustomerRefNo"])

#             request.session.pop("user_id", None)
#             return redirect("signin")

#     else:
#         form = ProfileForm(instance=profile, user=user)

#     return render(request, "app_user/profile.html", {
#         "form": form,
#         "editing": True,
#         "signup_flow": True,
#     })






import re
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from app_user.models import Profile
from django.conf import settings
from app_shop.utils import make_post


from app_user.forms import ProfileForm

from .forms import (
    SignupForm,
    PasswordForm,
    #ProfileForm,
    SigninForm,
    EmailTokenConfirmForm,
)
from .models import (
    CustomUser,
    EmailVerification,
    PhoneVerification,
)
from .utils import send_confirmation_email, send_otp


def is_email_or_phone(value):
    if re.match(r"[^@]+@[^@]+\.[^@]+", value):
        return 'email'
    elif re.match(r"^\+?\d{10,15}$", value):
        return 'phone'
    return None


def home_view(request):
    return render(request, 'home.html')


def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['email_or_phone']
            kind = is_email_or_phone(identifier)

            if kind == 'email':
                otp = EmailVerification.generate_token()


                EmailVerification.objects.update_or_create(
                email=identifier,
                defaults={'token': otp, 'is_used': False}
                )

                request.session["pending_email"] = identifier
                send_confirmation_email(identifier, f"Your OTP is {otp}")

                return redirect("confirm_email_otp")


            elif kind == 'phone':
                otp = PhoneVerification.generate_otp()
                PhoneVerification.objects.update_or_create(
                    phone_number=identifier,
                    defaults={'otp': otp, 'used': False}
                )
                request.session['pending_phone'] = identifier
                send_otp(identifier, otp)
                return redirect('confirm_phone')

            else:
                form.add_error('email_or_phone', 'Enter a valid email or phone')

    else:
        form = SignupForm()

    return render(request, 'app_login/signup.html', {'form': form})


def confirm_email_otp_view(request):
    email = request.session.get("pending_email")
    if not email:
        return redirect("signup")

    if request.method == "POST":
        otp = request.POST.get("otp")

        try:
            verification = EmailVerification.objects.get(
                email=email,
                token=otp,
                is_used=False
            )
        except EmailVerification.DoesNotExist:
            return render(
                request,
                "app_login/confirm_email_otp.html",
                {"error": "Invalid OTP"}
            )

        verification.is_used = True
        verification.save()

        request.session["confirmed_email"] = email
        request.session.pop("pending_email", None)

        return redirect("create_password")

    return render(request, "app_login/confirm_email_otp.html")

def confirm_phone_view(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        phone = request.session.get('pending_phone')

        try:
            verification = PhoneVerification.objects.get(
            phone_number=phone,
            otp=otp,
            is_used=False
        )

        except PhoneVerification.DoesNotExist:
            return render(
                request,
                'app_login/confirm_phone.html',
                {'error': 'Invalid OTP'}
            )

        verification.is_used = True

        verification.save()

        request.session['confirmed_phone'] = phone
        return redirect('create_password')

    return render(request, 'app_login/confirm_phone.html')


# def create_password_view(request):
#     email = request.session.get('confirmed_email')
#     phone = request.session.get('confirmed_phone')

#     if not email and not phone:
#         return redirect('signup')

#     if request.method == 'POST':
#         form = PasswordForm(request.POST)
#         if form.is_valid():

#             if email and CustomUser.objects.filter(email=email).exists():
#                 form.add_error(None, 'Email already registered')
#                 return render(request, 'app_login/create_password.html', {'form': form})

#             if phone and CustomUser.objects.filter(phone=phone).exists():
#                 form.add_error(None, 'Phone already registered')
#                 return render(request, 'app_login/create_password.html', {'form': form})

#             if email:
#                 user = CustomUser.objects.create(email=email)
#             else:
#                 user = CustomUser.objects.create(phone=phone)

#             user.set_password(form.cleaned_data['password'])
#             user.save()

#             request.session['user_id'] = user.id
#             request.session.modified = True
#             request.session.pop('confirmed_email', None)
#             request.session.pop('confirmed_phone', None)
#             request.session.pop('pending_phone', None)

#             #return redirect('complete_details')
#             return redirect('complete_profile')

#     else:
#         form = PasswordForm()

#     return render(request, 'app_login/create_password.html', {'form': form})


def create_password_view(request):
    email = request.session.get('confirmed_email')
    phone = request.session.get('confirmed_phone')

    # Ensure the user has actually passed the OTP verification step
    if not email and not phone:
        return redirect('signup')

    if request.method == 'POST':
        form = PasswordForm(request.POST)
        if form.is_valid():

            # Double-check that the email or phone hasn't been registered 
            # while the user was filling out the password form
            if email and CustomUser.objects.filter(email=email).exists():
                form.add_error(None, 'Email already registered')
                return render(request, 'app_login/create_password.html', {'form': form})

            if phone and CustomUser.objects.filter(phone=phone).exists():
                form.add_error(None, 'Phone already registered')
                return render(request, 'app_login/create_password.html', {'form': form})

            # FIX: Use create_user() instead of create() to ensure 
            # standard user permissions (is_staff=False) are applied correctly.
            if email:
                user = CustomUser.objects.create_user(email=email)
            else:
                user = CustomUser.objects.create_user(phone=phone)

            # Set the password using Django's hashing mechanism
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Since the app is stateless, storing the ID in the session 
            # allows the next view to fetch the user from Supabase.
            request.session['user_id'] = user.id
            request.session.modified = True
            
            # Clean up verification session data
            request.session.pop('confirmed_email', None)
            request.session.pop('confirmed_phone', None)
            request.session.pop('pending_phone', None)

            return redirect('complete_profile')

    else:
        form = PasswordForm()

    return render(request, 'app_login/create_password.html', {'form': form})

def complete_details_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('signup')

    user = CustomUser.objects.get(id=user_id)

    # 🔥 ENSURE PROFILE EXISTS
    profile, _ = Profile.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save()

            # 🔥 CREATE DG CUSTOMER HERE
            create_dg_customer(profile)

            request.session.pop('user_id', None)
            return redirect('signin')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'app_login/update_details.html', {'form': form})


def signin_view(request):
    if request.method == 'POST':
        form = SigninForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['email_or_phone']
            password = form.cleaned_data['password']
            kind = is_email_or_phone(identifier)

            if kind == 'email':
                user = CustomUser.objects.filter(email=identifier).first()
            elif kind == 'phone':
                user = CustomUser.objects.filter(phone=identifier).first()
            else:
                user = None

            if user and user.check_password(password):
                login(request, user)
                return redirect('home')
            else:
                form.add_error(None, 'Invalid credentials')

    else:
        form = SigninForm()

    return render(request, 'app_login/signin.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


def complete_profile_view(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("signup")

    user = CustomUser.objects.get(id=user_id)
    profile, _ = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile, user=user)
        if form.is_valid():
            entered_phone = form.cleaned_data.get("phone")
            if entered_phone and not user.phone:
                user.phone = entered_phone
                user.save(update_fields=["phone"])
                
            profile = form.save(commit=False)
            profile.user = user

            # ---------- build addresses ----------
            billingAddress = {
                "line1": form.cleaned_data.get("bLine1"),
                "line2": form.cleaned_data.get("bLine2"),
                "city": form.cleaned_data.get("bCity"),
                "state": form.cleaned_data.get("bState"),
                "zip": int(form.cleaned_data.get("bZip") or 0),
                "country": "India",
                "mobileNumber": user.phone,
                "statecode": "07",
            }

            deliveryAddress = {
                "line1": form.cleaned_data.get("dLine1"),
                "line2": form.cleaned_data.get("dLine2"),
                "city": form.cleaned_data.get("dCity"),
                "state": form.cleaned_data.get("dState"),
                "zip": int(form.cleaned_data.get("dZip") or 0),
                "country": "India",
                "mobileNumber": user.phone,
                "statecode": "07",
            }

            if form.cleaned_data.get("same_as_delivery"):
                profile.billingAddress = billingAddress
                profile.deliveryAddress = billingAddress
            else:
                profile.billingAddress = billingAddress
                profile.deliveryAddress = deliveryAddress

            if not profile.billingAddressId:
                profile.billingAddressId = f"{profile.customerRefNo}_BILL"

            profile.save()

            # ---------- DG CREATE PROFILE ----------
            if not profile.dgcustomerRefNo:
                payload = {
                    "mobileNumber": user.phone,
                    "customerRefNo": profile.customerRefNo,
                    "fullName": profile.name,
                    "kycStatus": profile.kycStatus,
                    "partner_id": settings.PARTNER_ID,
                    "emailAddress": user.email,
                    "billingAddress": profile.billingAddress,
                    "deliveryAddress": profile.deliveryAddress,
                }

                resp = make_post(endpoint="CREATE_PROFILE_ENDPOINT", payload=payload)
                if resp and resp.get("status") == 200:
                    data = resp.get("data")
                    if isinstance(data, list) and data:
                        profile.dgcustomerRefNo = data[0].get("dgCustomerRefNo")
                        profile.save(update_fields=["dgcustomerRefNo"])

            request.session.pop("user_id", None)
            return redirect("signin")

    else:
        form = ProfileForm(instance=profile, user=user)

    return render(request, "app_user/profile.html", {
        "form": form,
        "editing": True,
        "signup_flow": True,
    })
