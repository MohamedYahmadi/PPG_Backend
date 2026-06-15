import time
import requests
from ..models import ImportedStation


STATION_TYPE_QUERIES = {
    'BUS': 'bus station in {}',
    'METRO': 'metro station in {}',
    'TRAIN': 'train station in {}',
}


def fetch_and_store_stations(city, station_type):
    query = STATION_TYPE_QUERIES.get(station_type)
    if not query:
        raise ValueError(f"Invalid station_type '{station_type}'. Must be one of: {', '.join(STATION_TYPE_QUERIES)}.")

    search_query = query.format(city)
    results = _nominatim_search(search_query)

    created = 0
    updated = 0
    skipped = 0

    for place in results:
        place_id = place.get('osm_id')
        if not place_id:
            skipped += 1
            continue
        place_id = str(place_id)

        lat = place.get('lat')
        lng = place.get('lon')

        defaults = {
            'name': place.get('display_name', '').split(',')[0],
            'formatted_address': place.get('display_name', ''),
            'latitude': float(lat) if lat else 0,
            'longitude': float(lng) if lng else 0,
            'type': station_type,
            'city': city,
            'source': 'OSM',
        }

        obj, was_created = ImportedStation.objects.update_or_create(
            external_id=place_id,
            defaults=defaults,
        )

        if was_created:
            created += 1
        else:
            updated += 1

    return {
        'message': 'Stations fetched successfully',
        'created': created,
        'updated': updated,
        'skipped': skipped,
    }


def _nominatim_search(query):
    url = 'https://nominatim.openstreetmap.org/search'
    params = {
        'q': query,
        'format': 'json',
        'limit': 30,
    }
    headers = {
        'User-Agent': 'SITP-App/1.0 (transit app for Tunisia)',
    }

    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    results = resp.json()

    if not results:
        return []

    time.sleep(1)
    return results
