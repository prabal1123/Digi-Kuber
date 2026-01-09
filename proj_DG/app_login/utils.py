# from django.conf import settings
# from django.core.mail import send_mail

# def send_confirmation_email(email, token):
#     link = f"http://localhost:8000/confirm-email/?token={token}"
#     send_mail(
#         'Confirm your email',
#         f'Click the link to confirm your email: {link}',
#         settings.DEFAULT_FROM_EMAIL,
#         [email],
#         fail_silently=False,
#     )

# def send_otp(phone, otp):
#     # Implement SMS sending logic here (use a service like Twilio)
#     print(f"Send OTP {otp} to phone {phone}")



from azure.communication.email import EmailClient
from django.conf import settings


def send_confirmation_email(email, token):
    try:
        client = EmailClient.from_connection_string(
            settings.AZURE_EMAIL_CONNECTION_STRING
        )

        confirm_link = f"{settings.FRONTEND_URL}/confirm-email/?token={token}"

        message = {
            "senderAddress": settings.AZURE_EMAIL_SENDER,
            "recipients": {
                "to": [{"address": email}]
            },
            "content": {
                "subject": "Confirm your email",
                "html": f"""
                <html>
                    <body>
                        <h3>Email Verification</h3>
                        <p>Click below to confirm your email:</p>
                        <a href="{confirm_link}">Confirm Email</a>
                    </body>
                </html>
                """,
                "plainText": f"Confirm your email: {confirm_link}"
            },
        }

        poller = client.begin_send(message)
        poller.result()
        return True

    except Exception as e:
        print("Email error:", e)
        return False


def send_otp(phone, otp):
    print(f"Send OTP {otp} to phone {phone}")
