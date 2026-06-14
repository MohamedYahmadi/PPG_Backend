from rest_framework import serializers
from domains.notifications.models import Notification, IncidentReport


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'title', 'body', 'data', 'is_read', 'created_at']
        read_only_fields = ['id', 'created_at']


class BroadcastSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, required=True)
    body = serializers.CharField(required=True)
    notification_type = serializers.ChoiceField(
        choices=['DELAY', 'CANCELLATION', 'BROADCAST', 'INCIDENT'],
        default='BROADCAST'
    )


class IncidentReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentReport
        fields = [
            'id', 'incident_type', 'severity', 'description',
            'location_lat', 'location_lng', 'trip', 'vehicle',
            'photo_url', 'is_resolved', 'resolved_at', 'created_at'
        ]
        read_only_fields = ['id', 'is_resolved', 'resolved_at', 'created_at']


class IncidentReportCreateSerializer(serializers.Serializer):
    incident_type = serializers.ChoiceField(choices=[
        'TECHNICAL', 'ACCIDENT', 'SECURITY', 'DELAY', 'OTHER'
    ])
    severity = serializers.ChoiceField(
        choices=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
        default='MEDIUM'
    )
    description = serializers.CharField()
    location_lat = serializers.FloatField(required=False)
    location_lng = serializers.FloatField(required=False)
    trip_id = serializers.UUIDField(required=False)
    vehicle_id = serializers.UUIDField(required=False)
    photo_url = serializers.CharField(max_length=255, required=False)
