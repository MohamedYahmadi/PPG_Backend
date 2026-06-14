from rest_framework import serializers
from domains.transit_tracking.models import Route, Trip, Vehicle, Line

class LineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Line
        fields = ['id', 'name', 'color_code', 'is_active']

class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ['id', 'line', 'name', 'path_geom', 'is_active']

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id', 'plate_number', 'capacity']

class TripSerializer(serializers.ModelSerializer):
    # Nested serializers pour limiter les requêtes SQL (select_related en amont)
    route = RouteSerializer(read_only=True)
    vehicle = VehicleSerializer(read_only=True)
    
    class Meta:
        model = Trip
        fields = ['id', 'route', 'vehicle', 'scheduled_start', 'status']

from domains.transit_tracking.models import Station
from django.contrib.gis.geos import Point

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
        # Point(x=longitude, y=latitude, srid=4326)
        validated_data['location'] = Point(lng, lat, srid=4326)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'lat' in validated_data and 'lng' in validated_data:
            lat = validated_data.pop('lat')
            lng = validated_data.pop('lng')
            instance.location = Point(lng, lat, srid=4326)
        return super().update(instance, validated_data)
