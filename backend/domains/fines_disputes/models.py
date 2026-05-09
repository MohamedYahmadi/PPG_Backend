import uuid
from django.contrib.gis.db import models as gis_models
from django.db import models
from django.conf import settings

class Fine(models.Model):
    FINE_STATUS = [
        ('UNPAID', 'Unpaid'),
        ('PAID', 'Paid'),
        ('DISPUTED', 'Disputed'),
        ('UNPAID_PENALTY', 'Unpaid Penalty'),
        ('CANCELLED', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    controller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT)
    passenger_cin = models.CharField(max_length=20)
    passenger_name = models.CharField(max_length=100, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=3)
    reason = models.TextField()
    infraction_location = gis_models.PointField(srid=4326, null=True, blank=True) # PostGIS
    status = models.CharField(max_length=20, choices=FINE_STATUS, default='UNPAID')
    proof_photo_url = models.CharField(max_length=255, null=True, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fines'

class Dispute(models.Model):
    DISPUTE_STATUS = [
        ('OPEN', 'Open'),
        ('UNDER_REVIEW', 'Under Review'),
        ('RESOLVED_REJECTED', 'Resolved Rejected'),
        ('RESOLVED_ACCEPTED', 'Resolved Accepted'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fine = models.ForeignKey(Fine, on_delete=models.RESTRICT)
    passenger = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT)
    reason = models.TextField()
    proof_url = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=25, choices=DISPUTE_STATUS, default='OPEN')
    admin_notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'disputes'
