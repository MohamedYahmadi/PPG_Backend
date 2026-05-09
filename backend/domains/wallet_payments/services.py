from decimal import Decimal
from django.db import transaction
import logging
from .models import Wallet, WalletTransaction

logger = logging.getLogger(__name__)

class InsufficientFundsException(Exception):
    pass

class WalletService:
    """
    Logique Financière Isolé (Zero Trust)
    """
    
    @staticmethod
    @transaction.atomic
    def debit_wallet(passenger_id: str, amount: Decimal, ref_id: str, debit_type: str = 'DEBIT_TICKET') -> WalletTransaction:
        """
        DÉCISION CTO : Cette méthode financière vit dans une transaction ACID stricte.
        Le "Pessimistic Locking" (select_for_update) empêche 100% des cas de Double-Spending.
        Aucune course (Race Condition) n'est possible, même sous attaque.
        """
        if amount <= 0:
            raise ValueError("L'API a bloqué une tentative de débit avec un montant négatif ou nul.")
            
        try:
            # LOCK LIGNE SQL : Bloque les autres threads jusqu'au COMMIT ou ROLLBACK.
            wallet = Wallet.objects.select_for_update().get(passenger_id=passenger_id)
        except Wallet.DoesNotExist:
            raise Exception("Portefeuille introuvable.")
            
        if wallet.balance < amount:
            logger.warning(f"FINANCE: Tentative d'achat sans provision (Wallet {wallet.id})")
            raise InsufficientFundsException("Solde insuffisant pour cette opération.")
            
        # 1. Mise à jour du Solde
        wallet.balance -= amount
        wallet.save()
        
        # 2. Création de la trace (Table SQL Append-Only)
        transaction_log = WalletTransaction.objects.create(
            wallet=wallet,
            amount=-amount, # Trace comptable (Négatif = Sortie)
            type=debit_type,
            reference_id=ref_id
        )
        
        logger.info(f"FINANCE: Débit réussi de {amount} TND sur le Wallet {wallet.id}")
        return transaction_log
        
    @staticmethod
    @transaction.atomic
    def credit_wallet(wallet_id: str, amount: Decimal, gateway_ref: str) -> WalletTransaction:
        """Appelé par la tâche Celery post-Webhook D17 / ClicToPay"""
        wallet = Wallet.objects.select_for_update().get(id=wallet_id)
        wallet.balance += amount
        wallet.save()
        
        return WalletTransaction.objects.create(
            wallet=wallet,
            amount=amount,
            type='CREDIT_RECHARGE',
            payment_gateway_ref=gateway_ref
        )
