from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .serializers import WalletSerializer, WalletTransactionSerializer, TopUpSerializer
from domains.wallet_payments.models import Wallet, WalletTransaction
from domains.wallet_payments.services import WalletService
from core.permissions import IsPassenger

class WalletDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsPassenger]
    
    def get(self, request):
        wallet = get_object_or_404(Wallet, passenger=request.user)
        return Response(WalletSerializer(wallet).data)

class WalletTransactionsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsPassenger]
    
    def get(self, request):
        wallet = get_object_or_404(Wallet, passenger=request.user)
        # Limite à 50 (La pagination globale CursorPagination prend le relais ensuite)
        transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')[:50]
        return Response(WalletTransactionSerializer(transactions, many=True).data)

class TopUpAPIView(APIView):
    permission_classes = [IsAuthenticated, IsPassenger]
    
    def post(self, request):
        """
        DÉCISION CTO : Webhook simulé de paiement D17/ClicToPay.
        La transaction appelle la Service Layer pour garantir l'ACIDité.
        """
        serializer = TopUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        wallet = get_object_or_404(Wallet, passenger=request.user)
        
        # Appel de la logique métier ultra-sécurisée
        transaction_log = WalletService.credit_wallet(
            wallet_id=wallet.id,
            amount=data['amount'],
            gateway_ref=data['payment_token']
        )
        
        # Re-fetch du wallet pour avoir le solde exact post-transaction
        wallet.refresh_from_db()
        
        return Response({
            "message": "Recharge réussie.",
            "transaction_id": transaction_log.id,
            "new_balance": wallet.balance
        })
