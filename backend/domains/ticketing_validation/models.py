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
