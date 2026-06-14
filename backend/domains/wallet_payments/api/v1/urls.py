from django.urls import path
from .views import WalletDetailAPIView, WalletTransactionsAPIView, TopUpAPIView, AdminWalletListView

urlpatterns = [
    path('', WalletDetailAPIView.as_view(), name='api_wallet_detail'),
    path('transactions/', WalletTransactionsAPIView.as_view(), name='api_wallet_transactions'),
    path('top-up/', TopUpAPIView.as_view(), name='api_wallet_topup'),
    path('admin/list/', AdminWalletListView.as_view(), name='api_admin_wallet_list'),
]
