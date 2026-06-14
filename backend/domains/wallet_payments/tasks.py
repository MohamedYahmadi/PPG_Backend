import logging
from celery import shared_task
from django.db import transaction

logger = logging.getLogger(__name__)


@shared_task(queue='critical_payments', bind=True, max_retries=3)
def process_payment_webhook(self, wallet_id, amount, gateway_ref, gateway):
    try:
        from .services import WalletService
        transaction_log = WalletService.credit_wallet(
            wallet_id=wallet_id,
            amount=amount,
            gateway_ref=gateway_ref
        )
        logger.info(f"PAYMENT: Wallet {wallet_id} credited with {amount} via {gateway} (ref: {gateway_ref})")
        return f"PAYMENT_SUCCESS_{transaction_log.id}"
    except Exception as exc:
        logger.error(f"PAYMENT FAILED: Wallet {wallet_id}, amount {amount}, gateway {gateway}: {exc}")
        self.retry(exc=exc, countdown=120)


@shared_task(queue='critical_payments')
def refund_wallet(wallet_id, amount, reference_id):
    from .services import WalletService
    from decimal import Decimal
    try:
        WalletService.credit_wallet(
            wallet_id=wallet_id,
            amount=Decimal(str(amount)),
            gateway_ref=f"REFUND_{reference_id}"
        )
        logger.info(f"REFUND: Wallet {wallet_id} refunded {amount} (ref: {reference_id})")
        return "REFUND_SUCCESS"
    except Exception as e:
        logger.error(f"REFUND FAILED: {e}")
        return "REFUND_FAILED"
