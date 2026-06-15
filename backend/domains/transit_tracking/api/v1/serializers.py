from rest_framework import serializers
from domains.transit_tracking.models import (
    DriverIncident, DriverSession, GPSLog, ImportedStation, ImportedRoute,
    ImportedRouteStation, Line, Trajet, TrajetStation, Station, Trip, Vehicle
)


class LineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Line
        fields = ['id', 'name', 'color_code', 'is_active']


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
        return obj.location_lat

    def get_longitude(self, obj):
        return obj.location_lng

    def create(self, validated_data):
        lat = validated_data.pop('lat')
        lng = validated_data.pop('lng')
        validated_data['location_lat'] = lat
        validated_data['location_lng'] = lng
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'lat' in validated_data and 'lng' in validated_data:
            lat = validated_data.pop('lat')
            lng = validated_data.pop('lng')
            instance.location_lat = lat
            instance.location_lng = lng
        return super().update(instance, validated_data)


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id', 'plate_number', 'fleet_id', 'driver_id', 'capacity']


class TrajetSerializer(serializers.ModelSerializer):
    start_station = serializers.SerializerMethodField()
    end_station = serializers.SerializerMethodField()

    class Meta:
        model = Trajet
        fields = ['id', 'name', 'line', 'start_station', 'end_station', 'is_active', 'gtfs_route_id']

    def get_start_station(self, obj):
        return StationSerializer(obj.start_station).data if obj.start_station else None

    def get_end_station(self, obj):
        return StationSerializer(obj.end_station).data if obj.end_station else None


class TrajetAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trajet
        fields = ['id', 'line', 'name', 'start_station', 'end_station', 'path_coordinates', 'is_active', 'gtfs_route_id']


class TripSerializer(serializers.ModelSerializer):
    trajet = TrajetSerializer(read_only=True)
    vehicle = VehicleSerializer(read_only=True)
    trajet_id = serializers.UUIDField(write_only=True)
    vehicle_id = serializers.UUIDField(write_only=True)
    current_station = serializers.SerializerMethodField()
    next_station = serializers.SerializerMethodField()
    destination_station = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            'id', 'trajet', 'trajet_id', 'vehicle', 'vehicle_id',
            'driver_id', 'current_station', 'next_station', 'destination_station',
            'last_latitude', 'last_longitude', 'last_gps_update_time',
            'scheduled_start', 'actual_start', 'actual_end', 'status'
        ]

    def get_current_station(self, obj):
        return StationSerializer(obj.current_station).data if obj.current_station else None

    def get_destination_station(self, obj):
        return StationSerializer(obj.destination_station).data if obj.destination_station else None

    def get_next_station(self, obj):
        if not obj.current_station:
            return None
        current_ts = TrajetStation.objects.filter(trajet=obj.trajet, station=obj.current_station).first()
        if not current_ts:
            return None
        next_ts = TrajetStation.objects.filter(trajet=obj.trajet, order_number__gt=current_ts.order_number).order_by('order_number').first()
        return StationSerializer(next_ts.station).data if next_ts else None


class DriverTripStartSerializer(serializers.Serializer):
    bus_id = serializers.UUIDField(required=True)
    trajet_id = serializers.UUIDField(required=True)


class GPSUpdateSerializer(serializers.Serializer):
    lat = serializers.FloatField(required=True)
    lng = serializers.FloatField(required=True)
    speed_kmh = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=0)
    heading = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=0)


class GPSLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = GPSLog
        fields = ['id', 'trip', 'vehicle_id', 'location_lat', 'location_lng', 'speed_kmh', 'heading', 'recorded_at']
        read_only_fields = fields


class DriverIncidentCreateSerializer(serializers.Serializer):
    trip_id = serializers.UUIDField(required=False)
    type = serializers.ChoiceField(choices=['DELAY', 'BREAKDOWN', 'ACCIDENT', 'SECURITY', 'OTHER'], default='OTHER')
    description = serializers.CharField(required=True)
    location_lat = serializers.FloatField(required=False)
    location_lng = serializers.FloatField(required=False)


class DriverIncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverIncident
        fields = ['id', 'trip', 'driver_id', 'type', 'description', 'location_lat', 'location_lng', 'status', 'created_at']
        read_only_fields = fields


class TrajetStationSerializer(serializers.ModelSerializer):
    station = StationSerializer(read_only=True)

    class Meta:
        model = TrajetStation
        fields = ['id', 'station', 'order_number', 'time_to_next_station']


class TrajetStationAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrajetStation
        fields = ['id', 'trajet', 'station', 'order_number']


class TrajetWithStationsSerializer(serializers.ModelSerializer):
    stations = serializers.SerializerMethodField()

    class Meta:
        model = Trajet
        fields = ['id', 'name', 'stations', 'gtfs_route_id']

    def get_stations(self, obj):
        return TrajetStationSerializer(obj.trajet_stations.select_related('station').all(), many=True).data


class DriverSessionSerializer(serializers.ModelSerializer):
    trajet = serializers.SerializerMethodField()
    departure_station = StationSerializer(read_only=True)
    arrival_station = StationSerializer(read_only=True)
    current_station = StationSerializer(read_only=True)

    class Meta:
        model = DriverSession
        fields = ['id', 'driver_id', 'trajet', 'vehicle_id', 'departure_station', 'arrival_station',
                  'current_station', 'current_order', 'status', 'started_at', 'updated_at', 'finished_at']

    def get_trajet(self, obj):
        return TrajetSerializer(obj.trajet).data


class StartJourneySerializer(serializers.Serializer):
    trajet_id = serializers.UUIDField(required=True)
    departure_station_id = serializers.UUIDField(required=True)
    arrival_station_id = serializers.UUIDField(required=True)


class UpdateStationSerializer(serializers.Serializer):
    station_id = serializers.UUIDField(required=True)


class StationWithETA(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    order = serializers.IntegerField()
    eta_minutes = serializers.IntegerField()


class BusSearchResultSerializer(serializers.Serializer):
    driver_session_id = serializers.UUIDField()
    driver_id = serializers.UUIDField()
    trajet_name = serializers.CharField()
    bus_current_station = StationSerializer()
    bus_current_order = serializers.IntegerField()
    user_stations = StationWithETA(many=True)
    destination_stations = StationWithETA(many=True)
    status = serializers.CharField()


class ImportedStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportedStation
        fields = ['id', 'name', 'formatted_address', 'latitude', 'longitude', 'source',
                  'external_id', 'type', 'city', 'region', 'is_approved',
                  'approved_station', 'created_at']
        read_only_fields = ['id', 'created_at']


class ImportedRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportedRoute
        fields = ['id', 'name', 'source', 'external_id', 'line_name',
                  'is_approved', 'approved_trajet', 'created_at']
        read_only_fields = ['id', 'created_at']


class ImportedRouteStationSerializer(serializers.ModelSerializer):
    imported_station = ImportedStationSerializer(read_only=True)

    class Meta:
        model = ImportedRouteStation
        fields = ['id', 'imported_route', 'imported_station', 'order_number', 'time_to_next_station']


class PromoteStationSerializer(serializers.Serializer):
    imported_station_ids = serializers.ListField(child=serializers.UUIDField(), required=True)


class PromoteRouteSerializer(serializers.Serializer):
    imported_route_ids = serializers.ListField(child=serializers.UUIDField(), required=True)
