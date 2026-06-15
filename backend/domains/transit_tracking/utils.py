import csv
import io
from domains.transit_tracking.models import ImportedRoute, ImportedRouteStation, ImportedStation, Line, Trajet, TrajetStation, Station


def decode_bytes(data):
    for encoding in ('utf-8-sig', 'utf-8', 'latin-1'):
        try:
            return data.decode(encoding).splitlines()
        except (UnicodeDecodeError, ValueError):
            continue
    return data.decode('utf-8', errors='replace').splitlines()


def parse_csv_lines(lines):
    reader = csv.DictReader(lines)
    return [row for row in reader]


def parse_and_import_gtfs(zf):
    required = ['stops.txt', 'routes.txt', 'trips.txt', 'stop_times.txt']
    missing = [f for f in required if f not in zf.namelist()]
    if missing:
        raise ValueError(f'Fichiers GTFS manquants: {", ".join(missing)}')

    stops = parse_csv_lines(decode_bytes(zf.read('stops.txt')))
    routes_data = parse_csv_lines(decode_bytes(zf.read('routes.txt')))
    trips_data = parse_csv_lines(decode_bytes(zf.read('trips.txt')))
    stop_times = parse_csv_lines(decode_bytes(zf.read('stop_times.txt')))

    created = {'stations': 0, 'routes': 0, 'route_stations': 0}

    for s in stops:
        stop_id = s.get('stop_id', '').strip()
        if not stop_id:
            continue
        stop_name = s.get('stop_name', '').strip()
        try:
            lat = float(s.get('stop_lat', 0))
            lng = float(s.get('stop_lon', 0))
        except (ValueError, TypeError):
            lat, lng = None, None
        station, was_created = ImportedStation.objects.update_or_create(
            external_id=stop_id,
            defaults={
                'name': stop_name or stop_id,
                'latitude': lat,
                'longitude': lng,
                'source': 'GTFS',
            },
        )
        if was_created:
            created['stations'] += 1

    for r in routes_data:
        route_id = r.get('route_id', '').strip()
        if not route_id:
            continue
        route_name = r.get('route_long_name', '') or r.get('route_short_name', '') or route_id
        route_obj, was_created = ImportedRoute.objects.update_or_create(
            external_id=route_id,
            defaults={
                'name': route_name,
                'source': 'GTFS',
                'line_name': 'Réseau GTFS',
                'is_active': True,
            },
        )
        if was_created:
            created['routes'] += 1

    trip_route_map = {}
    for t in trips_data:
        trip_id = t.get('trip_id', '').strip()
        route_id = t.get('route_id', '').strip()
        if trip_id and route_id:
            trip_route_map[trip_id] = route_id

    stop_times_by_route = {}
    for st in stop_times:
        trip_id = st.get('trip_id', '').strip()
        route_id = trip_route_map.get(trip_id)
        if not route_id:
            continue
        try:
            seq = int(st.get('stop_sequence', 0))
        except (ValueError, TypeError):
            continue
        stop_id = st.get('stop_id', '').strip()
        if not stop_id:
            continue
        key = (route_id, stop_id)
        existing_seq = stop_times_by_route.get(key)
        if existing_seq is None or seq < existing_seq:
            stop_times_by_route[key] = seq

    stops_by_route = {}
    for (route_id, stop_id), seq in stop_times_by_route.items():
        stops_by_route.setdefault(route_id, []).append((seq, stop_id))

    for route_id, items in stops_by_route.items():
        route_obj = ImportedRoute.objects.filter(external_id=route_id).first()
        if not route_obj:
            continue
        items.sort(key=lambda x: x[0])
        seen = set()
        ordered = []
        for seq, stop_id in items:
            if stop_id not in seen:
                seen.add(stop_id)
                ordered.append(stop_id)

        ImportedRouteStation.objects.filter(imported_route=route_obj).delete()
        for i, stop_id in enumerate(ordered, start=1):
            station_obj = ImportedStation.objects.filter(external_id=stop_id).first()
            if not station_obj:
                continue
            ImportedRouteStation.objects.create(imported_route=route_obj, imported_station=station_obj, order_number=i)
            created['route_stations'] += 1

    created['stations_total'] = ImportedStation.objects.count()
    created['routes_total'] = ImportedRoute.objects.count()
    created['route_stations_total'] = ImportedRouteStation.objects.count()
    return created
