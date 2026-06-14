from rest_framework import serializers
from domains.ticketing_validation.models import (
    Ticket, Subscription, SubscriptionType, Fare, Invoice, MultiPassengerTicket
)


class TicketPurchaseSerializer(serializers.Serializer):
    zone_validity = serializers.CharField(max_length=50, required=True)
    price = serializers.DecimalField(max_digits=12, decimal_places=3, required=True)


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['id', 'price_paid', 'zone_validity', 'cryptographic_signature', 'valid_from', 'valid_until', 'status']


class SubscriptionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionType
        fields = ['id', 'name', 'duration', 'duration_days', 'price', 'zone_validity', 'is_active', 'description']


class SubscriptionPurchaseSerializer(serializers.Serializer):
    subscription_type_id = serializers.UUIDField(required=True)


class SubscriptionSerializer(serializers.ModelSerializer):
    subscription_type = SubscriptionTypeSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = ['id', 'subscription_type', 'price_paid', 'valid_from', 'valid_until', 'is_active', 'auto_renew', 'created_at']


class FareSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fare
        fields = ['id', 'category', 'zone_from', 'zone_to', 'price', 'discount_percentage', 'is_active']


class OfflineValidationSyncSerializer(serializers.Serializer):
    ticket_id = serializers.UUIDField(required=True)
    scan_location_lat = serializers.FloatField(required=True)
    scan_location_lng = serializers.FloatField(required=True)
    scanned_at = serializers.DateTimeField(required=True)
    is_cryptographically_valid = serializers.BooleanField(required=True)
    device_id = serializers.CharField(max_length=100, required=True)


class MarkTicketUsedSerializer(serializers.Serializer):
    ticket_id = serializers.UUIDField(required=True)


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ['id', 'invoice_type', 'reference_id', 'amount', 'tax_amount', 'total_amount', 'invoice_number', 'pdf_url', 'created_at']


class MultiPassengerPurchaseSerializer(serializers.Serializer):
    passengers = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        max_length=20
    )
    zone_validity = serializers.CharField(max_length=50, required=True)


class MultiPassengerTicketSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = MultiPassengerTicket
        fields = ['id', 'passengers', 'tickets', 'total_price', 'created_at']
