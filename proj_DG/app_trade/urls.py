from django.urls import path
from . import views 

urlpatterns = [
    path('generate_quote/', views.generate_quote, name='generate_quote'),
    path('validate/', views.validate_quote, name='confirm_quote'),
    # path('payment/', views.create_order, name='payment_page'),
    # path('create_order/', views.create_order, name='create_order'),
    # path('quote/', views.tradeEstimateView, name='quote'),
]