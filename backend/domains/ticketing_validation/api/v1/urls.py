from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TicketPurchaseAPIView, TicketHistoryAPIView, OfflineValidationSyncAPIView,
    MarkTicketUsedAPIView, SubscriptionTypeListAPIView, SubscriptionPurchaseAPIView,
    SubscriptionHistoryAPIView, FareViewSet, FareCalculateAPIView,
    InvoiceListAPIView, MultiPassengerPurchaseAPIView
)

router = DefaultRouter()
router.register(r'fares', FareViewSet, basename='admin-fares')

urlpatterns = [
    path('purchase/', TicketPurchaseAPIView.as_view(), name='api_ticket_purchase'),
    path('history/', TicketHistoryAPIView.as_view(), name='api_ticket_history'),
    path('validate/sync/', OfflineValidationSyncAPIView.as_view(), name='api_ticket_validate_sync'),
    path('validate/mark-used/', MarkTicketUsedAPIView.as_view(), name='api_ticket_mark_used'),
    path('subscriptions/types/', SubscriptionTypeListAPIView.as_view(), name='api_subscription_types'),
    path('subscriptions/purchase/', SubscriptionPurchaseAPIView.as_view(), name='api_subscription_purchase'),
    path('subscriptions/history/', SubscriptionHistoryAPIView.as_view(), name='api_subscription_history'),
    path('fares/calculate/', FareCalculateAPIView.as_view(), name='api_fare_calculate'),
    path('invoices/', InvoiceListAPIView.as_view(), name='api_invoice_list'),
    path('multi-passenger/purchase/', MultiPassengerPurchaseAPIView.as_view(), name='api_multi_passenger_purchase'),
    path('', include(router.urls)),
]
