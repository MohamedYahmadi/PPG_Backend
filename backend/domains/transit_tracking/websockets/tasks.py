from math import radians, sin, cos, sqrt, atan2
from celery import shared_task
from django.core.cache import cache
from dateutil.parser import parse
import logging
from ..models import GPSLog

logger = logging.getLogger(__name__)


def _distance_meters(lat1, lng1, lat2, lng2):
    earth_radius = 6371000
    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lng / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return earth_radius * c


@shared_task(queue='gps_processing')
def process_gps_batch(driver_id: str, payload: dict):
    """
    Moteur Anti-Spoofing & Insertion Massif
    S'assure que le chauffeur ne triche pas avec une fausse application GPS.
    """
    trip_id = payload.get('trip_id')
    vehicle_id = payload.get('vehicle_id')
    points = payload.get('points', [])

    cache_key = f"vehicle_last_loc_{vehicle_id}"
    last_known = cache.get(cache_key)

    valid_logs = []

    for pt in points:
        lat = pt.get('lat')
        lng = pt.get('lng')
        timestamp = parse(pt.get('timestamp'))

        current_geom = {'lat': float(lat), 'lng': float(lng)}

        if last_known:
            last_geom = last_known['geom']
            last_time = last_known['time']

            time_delta_seconds = (timestamp - last_time).total_seconds()
            if time_delta_seconds <= 0:
                continue

            distance_meters = _distance_meters(
                last_geom['lat'], last_geom['lng'],
                current_geom['lat'], current_geom['lng']
            )
            calculated_speed_kmh = (distance_meters / 1000) / (time_delta_seconds / 3600)

            if calculated_speed_kmh > 130:
                logger.warning(f"GPS SPOOFING BLOCKED: Vehicle {vehicle_id} computed speed {calculated_speed_kmh} km/h. Dropping coordinate.")
                continue

        valid_logs.append(
            GPSLog(
                trip_id=trip_id,
                vehicle_id=vehicle_id,
                location_lat=current_geom['lat'],
                location_lng=current_geom['lng'],
                speed_kmh=pt.get('speed_kmh', 0),
                heading=pt.get('heading', 0),
                recorded_at=timestamp
            )
        )

        last_known = {'geom': current_geom, 'time': timestamp}
        cache.set(cache_key, last_known, timeout=3600)

        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"live_trip_{trip_id}",
            {
                "type": "gps_update",
                "vehicle_id": vehicle_id,
                "lat": lat,
                "lng": lng,
                "speed": pt.get('speed_kmh', 0)
            }
        )

    if valid_logs:
        GPSLog.objects.bulk_create(valid_logs)


def _interpolate_path(path_coords, total_points):
    if not path_coords:
        return []
    pairs = []
    for part in path_coords.split(';'):
        part = part.strip()
        if not part:
            continue
        try:
            lat, lng = part.split(',')
            pairs.append((float(lat), float(lng)))
        except (ValueError, TypeError):
            continue
    if not pairs:
        return []
    if len(pairs) < total_points:
        steps = total_points // len(pairs)
        expanded = []
        for i in range(len(pairs) - 1):
            for s in range(steps):
                frac = s / steps
                expanded.append({
                    'lat': pairs[i][0] + (pairs[i + 1][0] - pairs[i][0]) * frac,
                    'lng': pairs[i][1] + (pairs[i + 1][1] - pairs[i][1]) * frac,
                    'speed_kmh': 30,
                    'heading': 0,
                })
        expanded.append({'lat': pairs[-1][0], 'lng': pairs[-1][1], 'speed_kmh': 0, 'heading': 0})
        return expanded[:total_points]
    step = len(pairs) / total_points
    result = []
    for i in range(total_points):
        idx = int(i * step)
        if idx >= len(pairs):
            idx = len(pairs) - 1
        result.append({'lat': pairs[idx][0], 'lng': pairs[idx][1], 'speed_kmh': 30 if idx < len(pairs) - 1 else 0, 'heading': 0})
    return result


@shared_task(queue='gps_processing', bind=True, max_retries=1)
def simulate_gps_route(self, route_id, vehicle_id, driver_id, interval_seconds=10, total_points=20):
    from django.utils import timezone
    from ..models import Trajet, Trip, Vehicle

    try:
        trajet = Trajet.objects.get(id=route_id)
        vehicle = Vehicle.objects.get(id=vehicle_id)
    except (Trajet.DoesNotExist, Vehicle.DoesNotExist) as e:
        logger.error(f"SIMULATION ERROR: {e}")
        return "ROUTE_OR_VEHICLE_NOT_FOUND"

    points = _interpolate_path(trajet.path_coordinates, total_points)
    if not points:
        return "NO_POINTS_GENERATED"

    trip = Trip.objects.create(
        trajet=trajet,
        vehicle=vehicle,
        driver_id=driver_id,
        scheduled_start=timezone.now(),
        actual_start=timezone.now(),
        status='IN_PROGRESS'
    )

    import time
    for pt in points:
        payload = {
            'trip_id': str(trip.id),
            'vehicle_id': str(vehicle_id),
            'points': [{
                'lat': pt['lat'],
                'lng': pt['lng'],
                'speed_kmh': pt['speed_kmh'],
                'heading': pt['heading'],
                'timestamp': timezone.now().isoformat()
            }]
        }
        process_gps_batch(driver_id, payload)
        time.sleep(interval_seconds)

    trip.actual_end = timezone.now()
    trip.status = 'COMPLETED'
    trip.save()

    logger.info(f"SIMULATION COMPLETE: Trip {trip.id} with {total_points} points")
    return f"SIMULATED_{total_points}_POINTS"
