import uuid
from django.db import models
from django.conf import settings

class Wallet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    passenger = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT)
    # NUMERIC(12,3) imposé au niveau DB, mappé en DecimalField(decimal_places=3)
    balance = models.DecimalField(max_digits=12, decimal_places=3, default=0.000)
    currency = models.CharField(max_length=3, default='TND')
    last_synced = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wallets'

    def __str__(self):
        return f"Wallet {self.id} - Solde: {self.balance} {self.currency}"

class WalletTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('CREDIT_RECHARGE', 'Credit Recharge'),
        ('DEBIT_TICKET', 'Debit Ticket'),
        ('REFUND_DISPUTE', 'Refund Dispute'),
        ('DEBIT_FINE', 'Debit Fine'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.RESTRICT, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=3)
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    reference_id = models.UUIDField(null=True, blank=True)
    payment_gateway_ref = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wallet_transactions'
