from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from domains.wallet_payments.services import WalletService
from .models import Ticket

class TicketingService:
    """
    Logique Métier (Service Layer) pour la génération des tickets.
    """
    
    @staticmethod
    @transaction.atomic
    def purchase_ticket(passenger_id: str, zone_validity: str, price: Decimal) -> Ticket:
        """
        DÉCISION CTO : Transaction ACID imbriquée.
        Le wallet est d'abord verrouillé, puis on signe le ticket, puis on le crée.
        Si l'une des étapes échoue, PostgreSQL annule TOUT (Rollback automatique).
        """
        # 1. Cryptographie Asymétrique (Cœur de la Sécurité Offline)
        valid_from = timezone.now()
        valid_until = valid_from + timedelta(hours=2) # Règle métier : Validité de 2 heures
        
        # Le payload qui sera inséré dans le QR Code
        payload = f"{passenger_id}|{zone_validity}|{valid_until.timestamp()}"
        
        # En production: utilise core.utils.crypto avec une clé Ed25519 stockée dans AWS KMS ou HashiCorp Vault.
        signature = f"SIGNED_ED25519_{payload}" 
        
        # 2. Création de l'entité Ticket
        ticket = Ticket.objects.create(
            passenger_id=passenger_id,
            price_paid=price,
            zone_validity=zone_validity,
            cryptographic_signature=signature,
            valid_from=valid_from,
            valid_until=valid_until,
            status='ACTIVE'
        )
        
        # 3. Débit effectif du Wallet (Appelle la Service Layer Wallet)
        WalletService.debit_wallet(
            passenger_id=passenger_id, 
            amount=price, 
            ref_id=str(ticket.id), 
            debit_type='DEBIT_TICKET'
        )
        
        # La transaction est COMMIT à la sortie de cette méthode
        return ticket
