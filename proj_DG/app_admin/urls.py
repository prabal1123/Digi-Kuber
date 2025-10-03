# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('manageCustomer/', views.manageCustomerView, name='manageCustomer'),
    path('create-profile/<str:user_id>/', views.createProfileView, name='create_profile'),
    path('fetch-profile/<str:user_id>/', views.fetchProfileView, name='fetch_profile'),
    path('forceUpdate/', views.updateDgCustId, name='update'),
    path('activateCustomer/<str:user_id>/', views.activateCustomer, name='activateCustomer'),
    path('deActivateCustomer/<str:user_id>/', views.deActivateCustomer, name='deActivateCustomer'),
    path('validateKYC/<str:user_id>/', views.validateKYC, name='validateKYC'),
    path('inValidateKYC/<str:user_id>/', views.inValidateKYC, name='inValidateKYC')
]
