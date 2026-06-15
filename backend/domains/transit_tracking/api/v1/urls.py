from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdminImportSummaryAPIView, DriverCurrentJourneyAPIView, DriverEndTripAPIView,
    DriverFinishJourneyAPIView, DriverGPSUpdateAPIView, DriverIncidentAPIView,
    DriverScheduleAPIView, DriverStartJourneyAPIView, DriverStartTripAPIView,
    DriverStationTripStartAPIView, DriverStationTripUpdateAPIView,
    DriverTripSetupAPIView, DriverUpdateStationAPIView, FetchStationsAPIView,
    GTFSImportAPIView, GTFSSyncAPIView, ImportedRouteStationViewSet,
    ImportedRouteViewSet, ImportedStationViewSet, LineViewSet,
    TrajetListAPIView, TrajetStationViewSet, TrajetViewSet,
    PassengerLiveTripsAPIView, TripListAPIView, LiveVehiclesAPIView,
    PromoteRoutesAPIView, PromoteStationsAPIView, StationViewSet,
    UserSearchBusAPIView, VehicleViewSet, TripViewSet,
    SimulationStartAPIView, ETADetailView, ETAAllStationsView
)

router = DefaultRouter()
router.register(r'stations', StationViewSet, basename='admin-stations')
router.register(r'admin/lines', LineViewSet, basename='admin-lines')
router.register(r'admin/buses', VehicleViewSet, basename='admin-buses')
router.register(r'admin/trajets', TrajetViewSet, basename='admin-trajets')
router.register(r'admin/trajet-stations', TrajetStationViewSet, basename='admin-trajet-stations')
router.register(r'admin/imported-stations', ImportedStationViewSet, basename='admin-imported-stations')
router.register(r'admin/imported-routes', ImportedRouteViewSet, basename='admin-imported-routes')
router.register(r'admin/imported-route-stations', ImportedRouteStationViewSet, basename='admin-imported-route-stations')
router.register(r'trips', TripViewSet, basename='admin-trips')

urlpatterns = [
    path('trajets/', TrajetListAPIView.as_view(), name='api_transit_trajets'),
    path('trips/active/', TripListAPIView.as_view(), name='api_transit_trips_active'),
    path('passenger/live-trips/', PassengerLiveTripsAPIView.as_view(), name='api_passenger_live_trips'),
    path('live-vehicles/', LiveVehiclesAPIView.as_view(), name='api_transit_live_vehicles'),
    path('driver/setup/', DriverTripSetupAPIView.as_view(), name='api_driver_trip_setup'),
    path('driver/schedule/', DriverScheduleAPIView.as_view(), name='api_driver_schedule'),
    path('driver/trips/start-station/', DriverStationTripStartAPIView.as_view(), name='api_driver_station_trip_start'),
    path('driver/trips/<uuid:trip_id>/update-station/', DriverStationTripUpdateAPIView.as_view(), name='api_driver_station_trip_update'),
    path('driver/trips/<uuid:trip_id>/start/', DriverStartTripAPIView.as_view(), name='api_driver_start_trip'),
    path('driver/trips/<uuid:trip_id>/end/', DriverEndTripAPIView.as_view(), name='api_driver_end_trip'),
    path('driver/trips/<uuid:trip_id>/gps/', DriverGPSUpdateAPIView.as_view(), name='api_driver_gps_update'),
    path('driver/incidents/', DriverIncidentAPIView.as_view(), name='api_driver_incidents'),
    path('admin/gtfs-import/', GTFSImportAPIView.as_view(), name='api_admin_gtfs_import'),
    path('admin/gtfs-sync/', GTFSSyncAPIView.as_view(), name='api_admin_gtfs_sync'),
    path('admin/fetch-stations/', FetchStationsAPIView.as_view(), name='api_admin_fetch_stations'),
    path('admin/promote-stations/', PromoteStationsAPIView.as_view(), name='api_admin_promote_stations'),
    path('admin/promote-routes/', PromoteRoutesAPIView.as_view(), name='api_admin_promote_routes'),
    path('admin/import-summary/', AdminImportSummaryAPIView.as_view(), name='api_admin_import_summary'),
    path('driver/start/', DriverStartJourneyAPIView.as_view(), name='api_driver_start_journey'),
    path('driver/update-station/', DriverUpdateStationAPIView.as_view(), name='api_driver_update_station'),
    path('driver/finish/', DriverFinishJourneyAPIView.as_view(), name='api_driver_finish_journey'),
    path('driver/current/', DriverCurrentJourneyAPIView.as_view(), name='api_driver_current_journey'),
    path('user/search-bus/', UserSearchBusAPIView.as_view(), name='api_user_search_bus'),
    path('simulation/start/', SimulationStartAPIView.as_view(), name='api_transit_simulation_start'),
    path('eta/<uuid:trip_id>/station/<uuid:station_id>/', ETADetailView.as_view(), name='api_transit_eta'),
    path('eta/<uuid:trip_id>/all/', ETAAllStationsView.as_view(), name='api_transit_eta_all'),
    path('', include(router.urls)),
]
