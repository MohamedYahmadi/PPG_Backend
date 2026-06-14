import uuid
from django.db import models
from django.conf import settings
from django.contrib.gis.db import models as gis_models

class Ticket(models.Model):
    TICKET_STATUS = [
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('USED', 'Used'),
        ('FRAUDULENT', 'Fraudulent'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    passenger = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT)
    price_paid = models.DecimalField(max_digits=12, decimal_places=3)
    zone_validity = models.CharField(max_length=50)
    cryptographic_signature = models.TextField()
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    status = models.CharField(max_length=20, choices=TICKET_STATUS, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tickets'

class ValidationLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.RESTRICT)
    controller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT)
    scan_location = gis_models.PointField(srid=4326) # 🌍 PostGIS Natif EPSG:4326
    scanned_at = models.DateTimeField()
    is_cryptographically_valid = models.BooleanField()
    sync_status = models.CharField(max_length=20, default='PENDING_SYNC')
    device_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'validation_logs'


class SubscriptionType(models.Model):
    DURATION_CHOICES = [
        ('DAILY', 'Quotidien'),
        ('WEEKLY', 'Hebdomadaire'),
        ('MONTHLY', 'Mensuel'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    duration = models.CharField(max_length=10, choices=DURATION_CHOICES)
    duration_days = models.IntegerField(help_text="Nombre de jours de validité")
    price = models.DecimalField(max_digits=12, decimal_places=3)
    zone_validity = models.CharField(max_length=50, default='ALL')
    is_active = models.BooleanField(default=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'subscription_types'

    def __str__(self):
        return f"{self.name} - {self.price} TND/{self.duration}"


class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    passenger = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT)
    subscription_type = models.ForeignKey(SubscriptionType, on_delete=models.RESTRICT)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    price_paid = models.DecimalField(max_digits=12, decimal_places=3)
    is_active = models.BooleanField(default=True)
    auto_renew = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'subscriptions'

    def __str__(self):
        return f"Abonnement {self.subscription_type.name} - {self.passenger}"


class Fare(models.Model):
    FARE_CATEGORIES = [
        ('STANDARD', 'Standard'),
        ('STUDENT', 'Étudiant'),
        ('PMR', 'Personne à mobilité réduite'),
        ('CHILD', 'Enfant'),
        ('SENIOR', 'Senior'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.CharField(max_length=20, choices=FARE_CATEGORIES, default='STANDARD')
    zone_from = models.CharField(max_length=50)
    zone_to = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=12, decimal_places=3)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'fares'
        unique_together = ('category', 'zone_from', 'zone_to')

    def __str__(self):
        discount = f" (-{self.discount_percentage}%)" if self.discount_percentage else ""
        return f"{self.category}: {self.zone_from}->{self.zone_to} = {self.price} TND{discount}"


class Invoice(models.Model):
    INVOICE_TYPES = [
        ('TICKET', 'Ticket'),
        ('SUBSCRIPTION', 'Abonnement'),
        ('RECHARGE', 'Recharge'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    passenger = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT)
    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPES)
    reference_id = models.UUIDField(help_text="ID du ticket/abonnement/recharge associé")
    amount = models.DecimalField(max_digits=12, decimal_places=3)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=3)
    invoice_number = models.CharField(max_length=50, unique=True)
    pdf_url = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'invoices'

    def __str__(self):
        return f"Facture {self.invoice_number} - {self.total_amount} TND"


class MultiPassengerTicket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    purchaser = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.RESTRICT,
        related_name='purchased_tickets'
    )
    passengers = models.JSONField(
        help_text="Liste des passagers: [{'name': '...', 'cin': '...'}]"
    )
    tickets = models.ManyToManyField(Ticket, related_name='multi_passenger_group')
    total_price = models.DecimalField(max_digits=12, decimal_places=3)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'multi_passenger_tickets'
