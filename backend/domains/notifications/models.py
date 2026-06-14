import uuid
from django.db import models
from django.conf import settings

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('DELAY', 'Retard'),
        ('CANCELLATION', 'Annulation'),
        ('IMMINENT_ARRIVAL', 'Arrivée imminente'),
        ('TICKET_EXPIRING', 'Expiration ticket'),
        ('BROADCAST', 'Diffusion générale'),
        ('INCIDENT', 'Incident signalé'),
        ('FRAUD_ALERT', 'Alerte fraude'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        null=True, blank=True, related_name='notifications'
    )
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    body = models.TextField()
    data = models.JSONField(null=True, blank=True, default=dict)
    is_read = models.BooleanField(default=False)
    sent_via_push = models.BooleanField(default=False)
    sent_via_sms = models.BooleanField(default=False)
    sent_via_email = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"[{self.notification_type}] {self.title} -> {self.recipient}"


class NotificationTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notification_type = models.CharField(
        max_length=30, choices=Notification.NOTIFICATION_TYPES, unique=True
    )
    title_template = models.CharField(max_length=200)
    body_template = models.TextField()
    push_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    email_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_templates'


class IncidentReport(models.Model):
    INCIDENT_TYPES = [
        ('TECHNICAL', 'Panne technique'),
        ('ACCIDENT', 'Accident'),
        ('SECURITY', 'Incident sécurité'),
        ('DELAY', 'Retard majeur'),
        ('OTHER', 'Autre'),
    ]
    SEVERITY_LEVELS = [
        ('LOW', 'Faible'),
        ('MEDIUM', 'Moyen'),
        ('HIGH', 'Élevé'),
        ('CRITICAL', 'Critique'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.RESTRICT,
        related_name='incident_reports'
    )
    incident_type = models.CharField(max_length=20, choices=INCIDENT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='MEDIUM')
    description = models.TextField()
    location_lat = models.FloatField(null=True, blank=True)
    location_lng = models.FloatField(null=True, blank=True)
    trip = models.ForeignKey(
        'transit_tracking.Trip', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    vehicle = models.ForeignKey(
        'transit_tracking.Vehicle', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    photo_url = models.CharField(max_length=255, null=True, blank=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'incident_reports'
        ordering = ['-created_at']
