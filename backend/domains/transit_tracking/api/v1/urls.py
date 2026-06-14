from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RouteListAPIView, TripListAPIView, TripViewSet, TripCreateAPIView,
    TripStartAPIView, TripEndAPIView, LiveVehiclesAPIView,
    StationViewSet, VehicleViewSet, LineViewSet,
    ScheduleViewSet, LineConnectionViewSet,
    GPSPushAPIView, SimulationStartAPIView, RouteViewSet,
    ETADetailView, ETAAllStationsView
)

router = DefaultRouter()
router.register(r'stations', StationViewSet, basename='admin-stations')
router.register(r'vehicles', VehicleViewSet, basename='admin-vehicles')
router.register(r'lines', LineViewSet, basename='admin-lines')
router.register(r'routes', RouteViewSet, basename='admin-routes')
router.register(r'trips', TripViewSet, basename='admin-trips')
router.register(r'schedules', ScheduleViewSet, basename='admin-schedules')
router.register(r'connections', LineConnectionViewSet, basename='admin-connections')

urlpatterns = [
    path('routes/', RouteListAPIView.as_view(), name='api_transit_routes'),
    path('trips/', TripListAPIView.as_view(), name='api_transit_trips'),
    path('trips/create/', TripCreateAPIView.as_view(), name='api_transit_trip_create'),
    path('trips/<uuid:trip_id>/start/', TripStartAPIView.as_view(), name='api_transit_trip_start'),
    path('trips/<uuid:trip_id>/end/', TripEndAPIView.as_view(), name='api_transit_trip_end'),
    path('live-vehicles/', LiveVehiclesAPIView.as_view(), name='api_transit_live_vehicles'),
    path('gps/push/', GPSPushAPIView.as_view(), name='api_transit_gps_push'),
    path('simulation/start/', SimulationStartAPIView.as_view(), name='api_transit_simulation_start'),
    path('eta/<uuid:trip_id>/station/<uuid:station_id>/', ETADetailView.as_view(), name='api_transit_eta'),
    path('eta/<uuid:trip_id>/all/', ETAAllStationsView.as_view(), name='api_transit_eta_all'),
    path('', include(router.urls)),
]
