from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from domains.wallet_payments.services import WalletService
from .models import Ticket, Subscription, SubscriptionType, Fare, Invoice, MultiPassengerTicket


class TicketingService:

    @staticmethod
    @transaction.atomic
    def purchase_ticket(passenger_id: str, zone_validity: str, price: Decimal) -> Ticket:
        valid_from = timezone.now()
        valid_until = valid_from + timedelta(hours=2)

        payload = f"{passenger_id}|{zone_validity}|{valid_until.timestamp()}"
        signature = f"SIGNED_ED25519_{payload}"

        ticket = Ticket.objects.create(
            passenger_id=passenger_id,
            price_paid=price,
            zone_validity=zone_validity,
            cryptographic_signature=signature,
            valid_from=valid_from,
            valid_until=valid_until,
            status='ACTIVE'
        )

        WalletService.debit_wallet(
            passenger_id=passenger_id,
            amount=price,
            ref_id=str(ticket.id),
            debit_type='DEBIT_TICKET'
        )

        TicketingService.generate_invoice(ticket.passenger, 'TICKET', ticket.id, price)

        return ticket

    @staticmethod
    @transaction.atomic
    def purchase_subscription(passenger_id: str, subscription_type_id: str) -> Subscription:
        sub_type = SubscriptionType.objects.get(id=subscription_type_id, is_active=True)
        valid_from = timezone.now()
        valid_until = valid_from + timedelta(days=sub_type.duration_days)

        subscription = Subscription.objects.create(
            passenger_id=passenger_id,
            subscription_type=sub_type,
            valid_from=valid_from,
            valid_until=valid_until,
            price_paid=sub_type.price,
            is_active=True
        )

        WalletService.debit_wallet(
            passenger_id=passenger_id,
            amount=sub_type.price,
            ref_id=str(subscription.id),
            debit_type='DEBIT_TICKET'
        )

        TicketingService.generate_invoice(
            subscription.passenger, 'SUBSCRIPTION', subscription.id, sub_type.price
        )

        return subscription

    @staticmethod
    @transaction.atomic
    def purchase_multi_passenger(purchaser_id: str, passengers: list, zone_validity: str) -> MultiPassengerTicket:
        price_per_ticket = TicketingService.calculate_fare('STANDARD', zone_validity, zone_validity)
        total_price = price_per_ticket * len(passengers)

        multi = MultiPassengerTicket.objects.create(
            purchaser_id=purchaser_id,
            passengers=passengers,
            total_price=total_price
        )

        tickets = []
        for p in passengers:
            ticket = TicketingService.purchase_ticket(purchaser_id, zone_validity, price_per_ticket)
            tickets.append(ticket)

        multi.tickets.set(tickets)
        return multi

    @staticmethod
    def calculate_fare(category: str, zone_from: str, zone_to: str) -> Decimal:
        try:
            fare = Fare.objects.get(
                category=category, zone_from=zone_from, zone_to=zone_to, is_active=True
            )
            if fare.discount_percentage:
                return fare.price * (1 - fare.discount_percentage / 100)
            return fare.price
        except Fare.DoesNotExist:
            return Decimal('1.500')

    @staticmethod
    def mark_ticket_used(ticket_id: str, controller) -> Ticket:
        try:
            ticket = Ticket.objects.get(id=ticket_id)
        except Ticket.DoesNotExist:
            raise ValueError("Ticket introuvable.")

        if ticket.status != 'ACTIVE':
            raise ValueError(f"Ce ticket est déjà {ticket.get_status_display().lower()}.")

        if ticket.valid_until < timezone.now():
            ticket.status = 'EXPIRED'
            ticket.save()
            raise ValueError("Ce ticket a expiré.")

        ticket.status = 'USED'
        ticket.save()
        return ticket

    @staticmethod
    def generate_invoice(passenger, invoice_type: str, reference_id, amount: Decimal) -> Invoice:
        import uuid
        invoice_number = f"INV-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        tax_rate = Decimal('0.19')
        tax_amount = amount * tax_rate
        invoice = Invoice.objects.create(
            passenger=passenger,
            invoice_type=invoice_type,
            reference_id=reference_id,
            amount=amount,
            tax_amount=tax_amount,
            total_amount=amount + tax_amount,
            invoice_number=invoice_number
        )
        return invoice

    @staticmethod
    def get_user_invoices(passenger_id: str):
        return Invoice.objects.filter(passenger_id=passenger_id).order_by('-created_at')
