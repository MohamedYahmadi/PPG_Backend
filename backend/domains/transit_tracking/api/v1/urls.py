from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RouteListAPIView, TripListAPIView, LiveVehiclesAPIView, StationViewSet

router = DefaultRouter()
router.register(r'stations', StationViewSet, basename='admin-stations')

urlpatterns = [
    path('routes/', RouteListAPIView.as_view(), name='api_transit_routes'),
    path('trips/', TripListAPIView.as_view(), name='api_transit_trips'),
    path('live-vehicles/', LiveVehiclesAPIView.as_view(), name='api_transit_live_vehicles'),
    path('', include(router.urls)),
]
