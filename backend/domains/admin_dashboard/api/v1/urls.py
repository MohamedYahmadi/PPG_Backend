from django.urls import path
from .views import (
    DashboardMetricsAPIView, AnalyticsExportAPIView, SystemHealthAPIView,
    FraudAlertListAPIView, WalletAdminListAPIView, FineAdminListAPIView,
    DisputeResolveAPIView, SettingsListAPIView, SettingUpdateAPIView
)

urlpatterns = [
    path('metrics/', DashboardMetricsAPIView.as_view(), name='api_admin_metrics'),
    path('analytics/export/', AnalyticsExportAPIView.as_view(), name='api_admin_analytics_export'),
    path('health/', SystemHealthAPIView.as_view(), name='api_admin_health'),
    path('fraud/alerts/', FraudAlertListAPIView.as_view(), name='api_admin_fraud_alerts'),
    path('wallets/list/', WalletAdminListAPIView.as_view(), name='api_admin_wallets'),
    path('fines/all/', FineAdminListAPIView.as_view(), name='api_admin_fines'),
    path('disputes/<uuid:dispute_id>/resolve/', DisputeResolveAPIView.as_view(), name='api_admin_dispute_resolve'),
    path('settings/', SettingsListAPIView.as_view(), name='api_admin_settings'),
    path('settings/<uuid:setting_id>/', SettingUpdateAPIView.as_view(), name='api_admin_setting_update'),
]
