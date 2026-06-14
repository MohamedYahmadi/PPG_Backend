import logging
from datetime import timedelta
from django.utils import timezone
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db.models import Avg
from .models import GPSLog, Route, Station, Trip, Schedule

logger = logging.getLogger(__name__)


class ETAService:

    @staticmethod
    def estimate_arrival_time(trip_id, target_station_id):
        try:
            trip = Trip.objects.select_related('route').get(id=trip_id)
            station = Station.objects.get(id=target_station_id)
        except (Trip.DoesNotExist, Station.DoesNotExist):
            return None

        recent_logs = GPSLog.objects.filter(
            trip=trip, recorded_at__gte=timezone.now() - timedelta(minutes=5)
        ).order_by('-recorded_at')

        if not recent_logs.exists():
            return None

        latest = recent_logs.first()
        vehicle_location = latest.location

        from django.contrib.gis.geos import LineString
        route_geom = trip.route.path_geom

        if not route_geom or not station.location:
            return None

        distance_to_station = vehicle_location.distance(station.location) * 111000

        avg_speed = recent_logs.aggregate(Avg('speed_kmh'))['speed_kmh__avg'] or 20

        if avg_speed <= 0:
            avg_speed = 20

        eta_seconds = (distance_to_station / 1000) / (avg_speed / 3600)

        from django.core.cache import cache
        cache_key = f"eta_{trip_id}_{target_station_id}"
        cache.set(cache_key, {
            'eta_seconds': eta_seconds,
            'distance_meters': distance_to_station,
            'avg_speed_kmh': avg_speed,
            'estimated_at': timezone.now().isoformat()
        }, timeout=120)

        return {
            'eta_seconds': eta_seconds,
            'eta_minutes': round(eta_seconds / 60, 1),
            'distance_meters': round(distance_to_station, 0),
            'avg_speed_kmh': round(avg_speed, 1),
        }

    @staticmethod
    def estimate_all_stations(trip_id):
        try:
            trip = Trip.objects.select_related('route').get(id=trip_id)
        except Trip.DoesNotExist:
            return []

        stations = Station.objects.all()
        results = []
        for station in stations:
            eta = ETAService.estimate_arrival_time(trip_id, station.id)
            if eta:
                results.append({
                    'station_id': str(station.id),
                    'station_name': station.name,
                    **eta
                })
        return results


class SimulationService:

    @staticmethod
    def generate_simulated_points(route_geom, num_points=20):
        if not route_geom:
            return []
        points = []
        for i in range(num_points):
            fraction = i / max(num_points - 1, 1)
            try:
                point = route_geom.interpolate(fraction, normalized=True)
                points.append({
                    'lat': point.y,
                    'lng': point.x,
                    'speed_kmh': 30 + (i % 10) * 2,
                    'heading': 90,
                })
            except Exception:
                continue
        return points
