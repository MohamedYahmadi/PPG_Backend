from django.urls import path
from .views import TicketPurchaseAPIView, TicketHistoryAPIView, OfflineValidationSyncAPIView, FraudAlertViewSet

urlpatterns = [
    path('purchase/', TicketPurchaseAPIView.as_view(), name='api_ticket_purchase'),
    path('history/', TicketHistoryAPIView.as_view(), name='api_ticket_history'),
    path('validate/sync/', OfflineValidationSyncAPIView.as_view(), name='api_ticket_validate_sync'),
    path('fraud/alerts/', FraudAlertViewSet.as_view({'get': 'list'}), name='api_fraud_alerts'),
]
