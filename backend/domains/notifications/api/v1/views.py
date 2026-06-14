from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .serializers import (
    NotificationSerializer, BroadcastSerializer,
    IncidentReportSerializer, IncidentReportCreateSerializer
)
from domains.notifications.models import Notification, IncidentReport
from domains.notifications.services import NotificationService
from core.permissions import IsAdmin


class NotificationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(
            recipient=request.user
        ).order_by('-created_at')[:100]
        return Response(NotificationSerializer(notifications, many=True).data)


class NotificationMarkReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        notification = get_object_or_404(
            Notification, id=notification_id, recipient=request.user
        )
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({"message": "Notification marquée comme lue."})


class MarkAllReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        updated = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).update(is_read=True)
        return Response({"message": f"{updated} notifications marquées comme lues."})


class BroadcastNotificationAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        serializer = BroadcastSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        count = NotificationService.send_broadcast(
            notification_type=serializer.validated_data['notification_type'],
            title=serializer.validated_data['title'],
            body=serializer.validated_data['body']
        )
        return Response({
            "message": f"Notification diffusée à {count} utilisateurs."
        }, status=201)


class IncidentReportListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role in ['ADMIN', 'SUPER_ADMIN']:
            reports = IncidentReport.objects.all().order_by('-created_at')
        else:
            reports = IncidentReport.objects.filter(reporter=request.user)
        return Response(
            IncidentReportSerializer(reports, many=True).data
        )


class IncidentReportCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = IncidentReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        report = NotificationService.report_incident(
            reporter=request.user,
            incident_type=data['incident_type'],
            severity=data['severity'],
            description=data['description'],
            location_lat=data.get('location_lat'),
            location_lng=data.get('location_lng'),
            trip_id=data.get('trip_id'),
            vehicle_id=data.get('vehicle_id'),
            photo_url=data.get('photo_url')
        )
        return Response(IncidentReportSerializer(report).data, status=201)


class IncidentResolveAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, incident_id):
        report = NotificationService.resolve_incident(incident_id, request.user)
        return Response({"message": "Incident résolu.", "id": str(report.id)})
