from django.urls import path
from . import views 

urlpatterns = [
    path('validate_quote/', views.validate_quote, name='validate_quote'),
    # path('quote/', views.tradeEstimateView, name='quote'),
]