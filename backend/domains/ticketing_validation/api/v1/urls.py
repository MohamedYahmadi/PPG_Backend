from django.urls import path
from .views import TicketPurchaseAPIView, TicketHistoryAPIView, OfflineValidationSyncAPIView

urlpatterns = [
    path('purchase/', TicketPurchaseAPIView.as_view(), name='api_ticket_purchase'),
    path('history/', TicketHistoryAPIView.as_view(), name='api_ticket_history'),
    path('validate/sync/', OfflineValidationSyncAPIView.as_view(), name='api_ticket_validate_sync'),
]
