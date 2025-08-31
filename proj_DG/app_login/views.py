import re
import random
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate, login
from .forms import SignupForm, PasswordForm, ProfileForm, SigninForm
from .models import CustomUser

def is_email_or_phone(value):
    # Simple check for email
    if re.match(r"[^@]+@[^@]+\.[^@]+", value):
        return 'email'
    # Simple check for phone (digits, optional +)
    elif re.match(r"^\+?\d{10,15}$", value):
        return 'phone'
    return None

def home_view(request):
    return render(request, 'home.html')

def send_confirmation_email(email, token):
    link = f"http://localhost:8000/auth/confirm-email/?token={token}"
    send_mail(
        'Confirm your email',
        f'Click the link to confirm your email: {link}',
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )

def send_otp(phone, otp):
    # Implement SMS sending logic here (use a service like Twilio)
    print(f"Send OTP {otp} to phone {phone}")

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data.get('email_or_phone')
            kind = is_email_or_phone(identifier)
            if kind == 'email':
                token = str(random.randint(100000, 999999))  # Use a secure token in production
                request.session['pending_email'] = identifier
                request.session['email_token'] = token
                send_confirmation_email(identifier, token)
                return render(request, 'app_login/confirm_email_sent.html', {'email': identifier})
            elif kind == 'phone':
                otp = str(random.randint(100000, 999999))
                request.session['pending_phone'] = identifier
                request.session['phone_otp'] = otp
                send_otp(identifier, otp)
                return redirect('confirm_phone')
            else:
                form.add_error('email_or_phone', 'Enter a valid email or phone number.')
    else:
        form = SignupForm()
    return render(request, 'app_login/signup.html', {'form': form})

def confirm_email_view(request):
    if request.method == 'POST':
        token = request.POST.get('token')
        if token == request.session.get('email_token'):
            request.session['confirmed_email'] = request.session.get('pending_email')
            return redirect('create_password')
        else:
            return render(request, 'app_login/confirm_email.html', {'error': 'Invalid token'})
    return render(request, 'app_login/confirm_email.html')

def confirm_phone_view(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        if otp == request.session.get('phone_otp'):
            request.session['confirmed_phone'] = request.session.get('pending_phone')
            return redirect('create_password')
        else:
            return render(request, 'app_login/confirm_phone.html', {'error': 'Invalid OTP'})
    return render(request, 'app_login/confirm_phone.html')

def create_password_view(request):
    email = request.session.get('confirmed_email')
    phone = request.session.get('confirmed_phone')
    if not email and not phone:
        return redirect('signup')
    if request.method == 'POST':
        form = PasswordForm(request.POST)
        if form.is_valid():
            # Check if user already exists (prevent duplicate)
            if email and CustomUser.objects.filter(email=email).exists():
                form.add_error(None, "Email already registered.")
                return render(request, 'app_login/create_password.html', {'form': form})
            if phone and CustomUser.objects.filter(phone=phone).exists():
                form.add_error(None, "Phone already registered.")
                return render(request, 'app_login/create_password.html', {'form': form})
            # Create user only after confirmation
            if email:
                user = CustomUser.objects.create(email=email)
            else:
                user = CustomUser.objects.create(phone=phone)
            user.set_password(form.cleaned_data['password'])
            user.save()
            request.session['user_id'] = user.id
            # Remove confirmation from session
            request.session.pop('confirmed_email', None)
            request.session.pop('confirmed_phone', None)
            return redirect('complete_details')
    else:
        form = PasswordForm()
    return render(request, 'app_login/create_password.html', {'form': form})

def complete_details_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('signup')
    user = CustomUser.objects.get(id=user_id)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('signin')
    else:
        form = ProfileForm(instance=user)
    return render(request, 'app_login/update_details.html', {'form': form})

def signin_view(request):
    if request.method == 'POST':
        form = SigninForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['email_or_phone']
            kind = is_email_or_phone(identifier)
            if kind == 'email':
                user = CustomUser.objects.filter(email=identifier).first()
            elif kind == 'phone':
                user = CustomUser.objects.filter(phone=identifier).first()
            else:
                user = None
            password = form.cleaned_data['password']
            if user and user.check_password(password):
                login(request, user)
                return redirect('home')
            else:
                form.add_error(None, "Invalid credentials")
    else:
        form = SigninForm()
    return render(request, 'app_login/signin.html', {'form': form})
