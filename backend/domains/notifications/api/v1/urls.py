from django.urls import path
from .views import (
    NotificationListAPIView, NotificationMarkReadAPIView,
    MarkAllReadAPIView, BroadcastNotificationAPIView,
    IncidentReportListAPIView, IncidentReportCreateAPIView,
    IncidentResolveAPIView
)

urlpatterns = [
    path('', NotificationListAPIView.as_view(), name='api_notifications_list'),
    path('<uuid:notification_id>/read/', NotificationMarkReadAPIView.as_view(), name='api_notification_mark_read'),
    path('mark-all-read/', MarkAllReadAPIView.as_view(), name='api_notifications_mark_all_read'),
    path('broadcast/', BroadcastNotificationAPIView.as_view(), name='api_notification_broadcast'),
    path('incidents/', IncidentReportListAPIView.as_view(), name='api_incidents_list'),
    path('incidents/report/', IncidentReportCreateAPIView.as_view(), name='api_incident_report'),
    path('incidents/<uuid:incident_id>/resolve/', IncidentResolveAPIView.as_view(), name='api_incident_resolve'),
]
