from rest_framework import serializers
from domains.ticketing_validation.models import Ticket

class TicketPurchaseSerializer(serializers.Serializer):
    zone_validity = serializers.CharField(max_length=50, required=True)
    price = serializers.DecimalField(max_digits=12, decimal_places=3, required=True)

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['id', 'price_paid', 'zone_validity', 'cryptographic_signature', 'valid_from', 'valid_until', 'status']

class OfflineValidationSyncSerializer(serializers.Serializer):
    ticket_id = serializers.UUIDField(required=True)
    scan_location_lat = serializers.FloatField(required=True)
    scan_location_lng = serializers.FloatField(required=True)
    scanned_at = serializers.DateTimeField(required=True)
    is_cryptographically_valid = serializers.BooleanField(required=True)
    device_id = serializers.CharField(max_length=100, required=True)
