from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('create-password/', views.create_password_view, name='create_password'),
    path('complete-details/', views.complete_details_view, name='complete_details'),
    path('signin/', views.signin_view, name='signin'),
    #path('confirm-email/', views.confirm_email_view, name='confirm_email'),  # Add this line
    path('confirm-phone/', views.confirm_phone_view, name='confirm_phone'),  # If you use phone OTP
    path('logout/', views.logout_view, name='logout'),
    path("complete-profile/", views.complete_profile_view, name="complete_profile"),
    path("confirm-email-otp/", views.confirm_email_otp_view, name="confirm_email_otp"),

]
