from django.contrib import admin
from .models import (
    DriverIncident, DriverSession, GPSLog, ImportedStation, ImportedRoute,
    ImportedRouteStation, Line, Trajet, TrajetStation, Station, Trip, Vehicle
)


@admin.register(DriverSession)
class DriverSessionAdmin(admin.ModelAdmin):
    list_display = ['driver_id', 'trajet', 'current_station', 'current_order', 'status', 'started_at', 'updated_at']
    list_filter = ['status']
    search_fields = ['driver_id']


@admin.register(ImportedStation)
class ImportedStationAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'source', 'type', 'latitude', 'longitude', 'is_approved', 'created_at']
    list_filter = ['source', 'type', 'is_approved']
    search_fields = ['name', 'city', 'external_id']
    readonly_fields = ['created_at']


@admin.register(ImportedRoute)
class ImportedRouteAdmin(admin.ModelAdmin):
    list_display = ['name', 'source', 'line_name', 'is_approved', 'created_at']
    list_filter = ['source', 'is_approved']
    search_fields = ['name', 'line_name', 'external_id']


@admin.register(ImportedRouteStation)
class ImportedRouteStationAdmin(admin.ModelAdmin):
    list_display = ['imported_route', 'imported_station', 'order_number', 'time_to_next_station']
    list_filter = ['imported_route']
    ordering = ['imported_route', 'order_number']


@admin.register(Line)
class LineAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_code', 'is_active']


@admin.register(Trajet)
class TrajetAdmin(admin.ModelAdmin):
    list_display = ['name', 'line', 'start_station', 'end_station', 'is_active', 'gtfs_route_id']
    search_fields = ['name']


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ['name', 'location_lat', 'location_lng', 'has_kiosk', 'is_verified', 'gtfs_stop_id']
    list_filter = ['is_verified']
    search_fields = ['name', 'gtfs_stop_id']


@admin.register(TrajetStation)
class TrajetStationAdmin(admin.ModelAdmin):
    list_display = ['trajet', 'station', 'order_number', 'time_to_next_station']
    list_filter = ['trajet']
    ordering = ['trajet', 'order_number']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['plate_number', 'fleet_id', 'driver_id', 'capacity', 'is_active']


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['trajet', 'vehicle', 'driver_id', 'current_station', 'status', 'actual_start', 'actual_end']


@admin.register(GPSLog)
class GPSLogAdmin(admin.ModelAdmin):
    list_display = ['trip', 'vehicle_id', 'location_lat', 'location_lng', 'recorded_at']


@admin.register(DriverIncident)
class DriverIncidentAdmin(admin.ModelAdmin):
    list_display = ['driver_id', 'type', 'status', 'created_at']
    list_filter = ['type', 'status']
