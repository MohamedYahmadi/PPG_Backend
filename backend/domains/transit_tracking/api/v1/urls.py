from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RouteViewSet, TripListAPIView, LiveFleetAPIView, StationViewSet, LineViewSet

router = DefaultRouter()
router.register(r'stations', StationViewSet, basename='admin-stations')
router.register(r'routes', RouteViewSet, basename='admin-routes')
router.register(r'lines', LineViewSet, basename='admin-lines')

urlpatterns = [
    path('trips/', TripListAPIView.as_view(), name='api_transit_trips'),
    path('live-fleet/', LiveFleetAPIView.as_view(), name='api_transit_live_fleet'),
    path('', include(router.urls)),
]
