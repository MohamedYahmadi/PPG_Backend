from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DashboardMetricsAPIView, SystemSettingViewSet

router = DefaultRouter()
router.register(r'settings', SystemSettingViewSet, basename='admin-settings')

urlpatterns = [
    path('metrics/', DashboardMetricsAPIView.as_view(), name='api_admin_metrics'),
    path('', include(router.urls)),
]
