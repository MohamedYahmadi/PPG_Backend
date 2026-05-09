from rest_framework import serializers
from domains.fines_disputes.models import Fine, Dispute

class FineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fine
        fields = ['id', 'passenger_cin', 'passenger_name', 'amount', 'reason', 'status', 'issued_at']

class FineCreateSerializer(serializers.Serializer):
    passenger_cin = serializers.CharField(max_length=20, required=True)
    passenger_name = serializers.CharField(max_length=100, required=False)
    amount = serializers.DecimalField(max_digits=12, decimal_places=3, required=True)
    reason = serializers.CharField(required=True)
    location_lat = serializers.FloatField(required=False)
    location_lng = serializers.FloatField(required=False)

class DisputeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispute
        fields = ['id', 'fine', 'reason', 'status', 'created_at']

class DisputeCreateSerializer(serializers.Serializer):
    fine_id = serializers.UUIDField(required=True)
    reason = serializers.CharField(required=True)
