from rest_framework import serializers
from domains.transit_tracking.models import (
    Line, Route, Station, Vehicle, Trip, Schedule, LineConnection, GPSLog
)
from django.contrib.gis.geos import Point


class LineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Line
        fields = ['id', 'name', 'color_code', 'is_active']


class RouteSerializer(serializers.ModelSerializer):
    line = LineSerializer(read_only=True)
    line_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Route
        fields = ['id', 'name', 'line', 'line_id', 'path_geom', 'is_active']
        read_only_fields = ['id']


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id', 'plate_number', 'fleet_id', 'capacity', 'is_active']
        read_only_fields = ['id']


class StationSerializer(serializers.ModelSerializer):
    lat = serializers.FloatField(write_only=True)
    lng = serializers.FloatField(write_only=True)
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model = Station
        fields = ['id', 'name', 'has_kiosk', 'lat', 'lng', 'latitude', 'longitude']
        read_only_fields = ['id', 'latitude', 'longitude']

    def get_latitude(self, obj):
        return obj.location.y if obj.location else None

    def get_longitude(self, obj):
        return obj.location.x if obj.location else None

    def create(self, validated_data):
        lat = validated_data.pop('lat')
        lng = validated_data.pop('lng')
        validated_data['location'] = Point(lng, lat, srid=4326)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'lat' in validated_data and 'lng' in validated_data:
            lat = validated_data.pop('lat')
            lng = validated_data.pop('lng')
            instance.location = Point(lng, lat, srid=4326)
        return super().update(instance, validated_data)


class TripSerializer(serializers.ModelSerializer):
    route = RouteSerializer(read_only=True)
    route_id = serializers.UUIDField(write_only=True)
    vehicle = VehicleSerializer(read_only=True)
    vehicle_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Trip
        fields = [
            'id', 'route', 'route_id', 'vehicle', 'vehicle_id',
            'driver_id', 'scheduled_start', 'actual_start', 'actual_end', 'status'
        ]
        read_only_fields = ['id']


class TripCreateSerializer(serializers.Serializer):
    route_id = serializers.UUIDField(required=True)
    vehicle_id = serializers.UUIDField(required=True)
    driver_id = serializers.UUIDField(required=True)
    scheduled_start = serializers.DateTimeField(required=True)
    status = serializers.ChoiceField(
        choices=['SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'],
        default='SCHEDULED'
    )


class ScheduleSerializer(serializers.ModelSerializer):
    route = RouteSerializer(read_only=True)
    route_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Schedule
        fields = [
            'id', 'route', 'route_id', 'day_type', 'departure_time',
            'arrival_time', 'frequency_minutes', 'is_active'
        ]
        read_only_fields = ['id']


class LineConnectionSerializer(serializers.ModelSerializer):
    from_line = LineSerializer(read_only=True)
    from_line_id = serializers.UUIDField(write_only=True)
    to_line = LineSerializer(read_only=True)
    to_line_id = serializers.UUIDField(write_only=True)
    from_station = StationSerializer(read_only=True)
    from_station_id = serializers.UUIDField(write_only=True)
    to_station = StationSerializer(read_only=True)
    to_station_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = LineConnection
        fields = [
            'id', 'from_line', 'from_line_id', 'to_line', 'to_line_id',
            'from_station', 'from_station_id', 'to_station', 'to_station_id',
            'transfer_time_minutes', 'is_active'
        ]
        read_only_fields = ['id']


class GPSLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = GPSLog
        fields = ['id', 'trip', 'vehicle_id', 'latitude', 'longitude', 'speed_kmh', 'heading', 'recorded_at']
        read_only_fields = ['id']


class GPSPushSerializer(serializers.Serializer):
    trip_id = serializers.UUIDField(required=True)
    vehicle_id = serializers.UUIDField(required=True)
    lat = serializers.FloatField(required=True)
    lng = serializers.FloatField(required=True)
    speed_kmh = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=0)
    heading = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=0)
    timestamp = serializers.DateTimeField(required=False)


class SimulationSerializer(serializers.Serializer):
    route_id = serializers.UUIDField(required=True)
    vehicle_id = serializers.UUIDField(required=True)
    driver_id = serializers.UUIDField(required=False)
    interval_seconds = serializers.IntegerField(default=10, min_value=1, max_value=300)
    total_points = serializers.IntegerField(default=20, min_value=1, max_value=500)
