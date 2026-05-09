from django.urls import path
from .views import WalletDetailAPIView, WalletTransactionsAPIView, TopUpAPIView

urlpatterns = [
    path('', WalletDetailAPIView.as_view(), name='api_wallet_detail'),
    path('transactions/', WalletTransactionsAPIView.as_view(), name='api_wallet_transactions'),
    path('top-up/', TopUpAPIView.as_view(), name='api_wallet_topup'),
]
