from celery import shared_task
from django.contrib.gis.geos import Point
from django.core.cache import cache
from dateutil.parser import parse
import logging
from ..models import GPSLog

logger = logging.getLogger(__name__)

@shared_task(queue='gps_processing')
def process_gps_batch(driver_id: str, payload: dict):
    """
    DÉCISION CTO : Moteur Anti-Spoofing & Insertion Massif PostGIS
    S'assure que le chauffeur ne triche pas avec une fausse application GPS.
    """
    trip_id = payload.get('trip_id')
    vehicle_id = payload.get('vehicle_id')
    points = payload.get('points', [])
    
    # 1. Récupérer le cache ultra-rapide Redis de la dernière position connue
    cache_key = f"vehicle_last_loc_{vehicle_id}"
    last_known = cache.get(cache_key)
    
    valid_logs = []
    
    for pt in points:
        lat = pt.get('lat')
        lng = pt.get('lng')
        timestamp = parse(pt.get('timestamp'))
        
        current_geom = Point(float(lng), float(lat), srid=4326) # 🌍 PostGIS GEOMETRY
        
        # ==========================================================
        # 2. ANTI-SPOOFING ENGINE (Validation de Physique Spatiale)
        # ==========================================================
        if last_known:
            last_geom = last_known['geom']
            last_time = last_known['time']
            
            time_delta_seconds = (timestamp - last_time).total_seconds()
            if time_delta_seconds <= 0:
                continue # Rejet des timestamps altérés ou retour dans le passé
                
            distance_meters = last_geom.distance(current_geom) * 111000 # Formule approx degrés->mètres
            calculated_speed_kmh = (distance_meters / 1000) / (time_delta_seconds / 3600)
            
            # Règle Physique de Base: Un bus ne peut pas rouler à plus de 130 km/h.
            # Si c'est le cas, soit le GPS saute (Glitch urbain), soit le chauffeur triche (Spoofing).
            if calculated_speed_kmh > 130:
                logger.warning(f"GPS SPOOFING BLOCKED: Vehicle {vehicle_id} computed speed {calculated_speed_kmh} km/h. Dropping coordinate.")
                continue # ON IGNORE LE POINT TOTALEMENT
                
        # Le point est certifié physiquement cohérent.
        valid_logs.append(
            GPSLog(
                trip_id=trip_id,
                vehicle_id=vehicle_id,
                location=current_geom,
                speed_kmh=pt.get('speed_kmh', 0),
                heading=pt.get('heading', 0),
                recorded_at=timestamp
            )
        )
        
        # Update Redis Cache
        last_known = {'geom': current_geom, 'time': timestamp}
        cache.set(cache_key, last_known, timeout=3600)
        
        # ==========================================================
        # 3. LIVE MAP BROADCASTING (Redis Pub/Sub -> Django Channels)
        # ==========================================================
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        # O(1) Broadcast à tous les passagers connectés
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

    # 4. Insertion Groupée (Préserve la base PostgreSQL des I/O saturants)
    if valid_logs:
        GPSLog.objects.bulk_create(valid_logs)
