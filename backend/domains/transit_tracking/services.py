import logging
from math import radians, sin, cos, sqrt, atan2
from datetime import timedelta
from django.utils import timezone
from django.db.models import Avg
from .models import GPSLog, Station, Trip

logger = logging.getLogger(__name__)


def _haversine(lat1, lng1, lat2, lng2):
    earth_radius = 6371000
    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lng / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return earth_radius * c


class ETAService:

    @staticmethod
    def estimate_arrival_time(trip_id, target_station_id):
        try:
            trip = Trip.objects.select_related('trajet').get(id=trip_id)
            station = Station.objects.get(id=target_station_id)
        except (Trip.DoesNotExist, Station.DoesNotExist):
            return None

        recent_logs = GPSLog.objects.filter(
            trip=trip, recorded_at__gte=timezone.now() - timedelta(minutes=5)
        ).order_by('-recorded_at')

        if not recent_logs.exists():
            return None

        latest = recent_logs.first()

        if not latest.location_lat or not latest.location_lng or not station.location_lat or not station.location_lng:
            return None

        distance_to_station = _haversine(
            latest.location_lat, latest.location_lng,
            station.location_lat, station.location_lng
        )

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
            trip = Trip.objects.select_related('trajet').get(id=trip_id)
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
