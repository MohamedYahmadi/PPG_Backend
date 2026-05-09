from rest_framework import serializers
from domains.wallet_payments.models import Wallet, WalletTransaction

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'balance', 'currency', 'last_synced']

class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ['id', 'amount', 'type', 'created_at', 'reference_id', 'payment_gateway_ref']

class TopUpSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=3, required=True)
    gateway = serializers.ChoiceField(choices=['D17', 'ClicToPay'], required=True)
    payment_token = serializers.CharField(max_length=255, required=True)
