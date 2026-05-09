from django.urls import path
from .views import DashboardMetricsAPIView

urlpatterns = [
    path('metrics/', DashboardMetricsAPIView.as_view(), name='api_admin_metrics'),
]
