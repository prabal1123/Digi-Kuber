from django.urls import path
from . import views 

urlpatterns = [
    path('editQuote/', views.editQuote, name='editQuote'),
    # path('quote/', views.tradeEstimateView, name='quote'),
]