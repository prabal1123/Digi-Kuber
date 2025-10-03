from django.urls import path
from . import views 

urlpatterns = [
    path('buy-now/', views.buy_now_view, name='buy_now'),
    path('quote/', views.tradeEstimateView, name='quote'),
    path('product/', views.product_page_view, name='product_page'),
    path('balance/', views.customer_detail, name='balance'),
    path('balance/', views.refresh_balance, name='refresh_balance'),
]