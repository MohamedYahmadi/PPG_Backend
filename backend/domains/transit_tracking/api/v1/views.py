import io
import zipfile
from math import atan2, cos, radians, sin, sqrt
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.decorators import action
from .serializers import (
    BusSearchResultSerializer, DriverIncidentCreateSerializer, DriverIncidentSerializer,
    DriverSessionSerializer, DriverTripStartSerializer, GPSLogSerializer, GPSUpdateSerializer,
    ImportedRouteSerializer, ImportedRouteStationSerializer, ImportedStationSerializer,
    LineSerializer, PromoteRouteSerializer, PromoteStationSerializer,
    TrajetAdminSerializer, TrajetSerializer, TrajetStationAdminSerializer,
    TrajetStationSerializer, TrajetWithStationsSerializer,
    StartJourneySerializer, StationSerializer, StationWithETA, TripSerializer,
    UpdateStationSerializer, VehicleSerializer
)
from core.permissions import IsAdmin, IsDriver
from domains.transit_tracking.models import (
    DriverIncident, DriverSession, GPSLog, ImportedRoute, ImportedRouteStation,
    ImportedStation, Line, Trajet, TrajetStation, Station, Trip, Vehicle
)
from domains.transit_tracking.services.google_places import fetch_and_store_stations
from domains.transit_tracking.utils import parse_and_import_gtfs


def distance_meters(lat1, lng1, lat2, lng2):
    earth_radius = 6371000
    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lng / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return earth_radius * c


def get_next_trajet_station(trip):
    if not trip.current_station:
        return None
    current_ts = TrajetStation.objects.filter(trajet=trip.trajet, station=trip.current_station).first()
    if not current_ts:
        return None
    return TrajetStation.objects.filter(trajet=trip.trajet, order_number__gt=current_ts.order_number).order_by('order_number').first()


def move_trip_to_next_station(trip):
    next_ts = get_next_trajet_station(trip)
    if not next_ts:
        trip.status = 'COMPLETED'
        trip.actual_end = timezone.now()
        trip.save(update_fields=['status', 'actual_end'])
        return trip
    trip.current_station = next_ts.station
    update_fields = ['current_station']
    if trip.destination_station_id == next_ts.station_id:
        trip.status = 'COMPLETED'
        trip.actual_end = timezone.now()
        update_fields.extend(['status', 'actual_end'])
    trip.save(update_fields=update_fields)
    return trip


def get_station_order(trajet_id, station_id):
    ts = TrajetStation.objects.filter(trajet_id=trajet_id, station_id=station_id).first()
    return ts.order_number if ts else None


def get_trajet_stations_between(trajet_id, from_order, to_order):
    return list(TrajetStation.objects.filter(
        trajet_id=trajet_id, order_number__gte=from_order, order_number__lte=to_order
    ).select_related('station').order_by('order_number'))


def calculate_eta(stations, from_index):
    return sum(ts.time_to_next_station for ts in stations[from_index:-1])


# ==============================================================================
# PUBLIC ENDPOINTS
# ==============================================================================

class TrajetListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        trajets = Trajet.objects.filter(is_active=True)
        return Response(TrajetSerializer(trajets, many=True).data)


class TripListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        trips = Trip.objects.filter(status='IN_PROGRESS').select_related('trajet', 'vehicle')
        return Response(TripSerializer(trips, many=True).data)


class PassengerLiveTripsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        trips = Trip.objects.filter(status__in=['IN_PROGRESS', 'COMPLETED']).select_related(
            'trajet', 'vehicle', 'current_station', 'destination_station'
        ).order_by('-actual_start', '-scheduled_start')[:50]
        return Response(TripSerializer(trips, many=True).data)


class LiveVehiclesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.core.cache import cache
        active_trips = Trip.objects.filter(status='IN_PROGRESS').select_related('trajet__line', 'vehicle')
        result = []
        for trip in active_trips:
            cache_key = f"vehicle_last_loc_{trip.vehicle_id}"
            last_loc = cache.get(cache_key)
            result.append({
                "id": str(trip.vehicle.id),
                "fleet_id": trip.vehicle.fleet_id,
                "plate_number": trip.vehicle.plate_number,
                "line": trip.trajet.line.name if trip.trajet and trip.trajet.line else None,
                "line_color": trip.trajet.line.color_code if trip.trajet and trip.trajet.line else None,
                "route_name": trip.trajet.name if trip.trajet else None,
                "trip_id": str(trip.id),
                "driver_id": str(trip.driver_id),
                "status": trip.status,
                "lat": last_loc.get('geom', {}).get('lat') if last_loc else (float(trip.last_latitude) if trip.last_latitude else None),
                "lng": last_loc.get('geom', {}).get('lng') if last_loc else (float(trip.last_longitude) if trip.last_longitude else None),
                "speed": last_loc.get('speed', 0) if last_loc else 0,
            })
        return Response(result)


# ==============================================================================
# DRIVER ENDPOINTS
# ==============================================================================

class DriverTripSetupAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def post(self, request):
        serializer = DriverTripStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        trajet = get_object_or_404(Trajet, id=data['trajet_id'])
        vehicle = get_object_or_404(Vehicle, id=data['bus_id'])
        if not trajet.start_station:
            return Response({"error": "Ce trajet n'a pas de station de départ."}, status=400)
        session = DriverSession.objects.create(
            driver_id=request.user.id,
            trajet=trajet,
            vehicle=vehicle,
            departure_station=trajet.start_station,
            arrival_station=trajet.end_station,
            current_station=trajet.start_station,
            current_order=1,
            status='IN_PROGRESS',
            started_at=timezone.now(),
        )
        return Response(DriverSessionSerializer(session).data, status=201)


class DriverScheduleAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def get(self, request):
        now = timezone.now()
        active_session = DriverSession.objects.filter(driver_id=request.user.id, status='IN_PROGRESS').first()
        return Response({
            'active_session': DriverSessionSerializer(active_session).data if active_session else None
        })


class DriverStationTripStartAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def post(self, request):
        serializer = StartJourneySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        trajet = get_object_or_404(Trajet, id=data['trajet_id'])
        departure = get_object_or_404(Station, id=data['departure_station_id'])
        arrival = get_object_or_404(Station, id=data['arrival_station_id'])
        departure_order = get_station_order(trajet.id, departure.id)
        if departure_order is None:
            return Response({'error': 'Station de départ invalide pour ce trajet.'}, status=400)
        trip = Trip.objects.create(
            trajet=trajet,
            vehicle=None,
            driver_id=request.user.id,
            current_station=departure,
            destination_station=arrival,
            scheduled_start=timezone.now(),
            actual_start=timezone.now(),
            status='IN_PROGRESS',
        )
        return Response(TripSerializer(trip).data, status=201)


class DriverStationTripUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def post(self, request, trip_id):
        trip = get_object_or_404(Trip, id=trip_id)
        move_trip_to_next_station(trip)
        return Response(TripSerializer(trip).data)


class DriverStartTripAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_id):
        trip = get_object_or_404(Trip, id=trip_id)
        if request.user.role == 'DRIVER' and str(request.user.id) != str(trip.driver_id):
            return Response({"error": "Ce trajet ne vous est pas assigné."}, status=403)
        trip.actual_start = timezone.now()
        trip.status = 'IN_PROGRESS'
        trip.save()
        return Response({"message": "Trajet démarré.", "trip": TripSerializer(trip).data})


class DriverEndTripAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_id):
        trip = get_object_or_404(Trip, id=trip_id)
        if request.user.role == 'DRIVER' and str(request.user.id) != str(trip.driver_id):
            return Response({"error": "Ce trajet ne vous est pas assigné."}, status=403)
        trip.actual_end = timezone.now()
        trip.status = 'COMPLETED'
        trip.save()
        return Response({"message": "Trajet terminé.", "trip": TripSerializer(trip).data})


class DriverGPSUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def post(self, request):
        serializer = GPSUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        from domains.transit_tracking.websockets.tasks import process_gps_batch
        process_gps_batch.delay(
            str(request.user.id),
            {
                'trip_id': str(data.get('trip_id', '')),
                'vehicle_id': str(data.get('vehicle_id', '')),
                'points': [{
                    'lat': float(data['lat']),
                    'lng': float(data['lng']),
                    'speed_kmh': float(data.get('speed_kmh', 0)),
                    'heading': float(data.get('heading', 0)),
                    'timestamp': (data.get('timestamp') or timezone.now()).isoformat()
                }]
            }
        )
        return Response({"message": "Position GPS envoyée pour traitement."}, status=202)


class DriverIncidentAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def get(self, request):
        incidents = DriverIncident.objects.filter(driver_id=request.user.id).order_by('-created_at')
        return Response(DriverIncidentSerializer(incidents, many=True).data)

    def post(self, request):
        serializer = DriverIncidentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        incident = DriverIncident.objects.create(
            driver_id=request.user.id,
            trip_id=data.get('trip_id'),
            type=data['type'],
            description=data['description'],
            location_lat=data.get('location_lat'),
            location_lng=data.get('location_lng'),
        )
        return Response(DriverIncidentSerializer(incident).data, status=201)


# ==============================================================================
# PASSENGER ENDPOINTS
# ==============================================================================

class UserSearchBusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_lat = request.query_params.get('lat')
        user_lng = request.query_params.get('lng')
        if not user_lat or not user_lng:
            return Response({"error": "Paramètres 'lat' et 'lng' requis."}, status=400)
        try:
            user_lat = float(user_lat)
            user_lng = float(user_lng)
        except (ValueError, TypeError):
            return Response({"error": "lat/lng invalides."}, status=400)

        radius_km = float(request.query_params.get('radius', 2))
        max_dist = radius_km * 1000

        active_sessions = DriverSession.objects.filter(status='IN_PROGRESS').select_related('trajet', 'current_station')
        results = []
        for session in active_sessions:
            bus_lat = session.current_station.location_lat if session.current_station else None
            bus_lng = session.current_station.location_lng if session.current_station else None
            if bus_lat is None or bus_lng is None:
                continue
            dist = distance_meters(user_lat, user_lng, bus_lat, bus_lng)
            if dist > max_dist:
                continue

            trajet_stations = list(TrajetStation.objects.filter(
                trajet=session.trajet
            ).select_related('station').order_by('order_number'))

            current_order = session.current_order
            user_stations = []
            dest_stations = []
            for ts in trajet_stations:
                dist_to_user = distance_meters(user_lat, user_lng, ts.station.location_lat, ts.station.location_lng)
                if dist_to_user < 500:
                    idx = trajet_stations.index(ts)
                    eta = calculate_eta(trajet_stations, current_order - 1) - calculate_eta(trajet_stations, idx)
                    user_stations.append(StationWithETA({
                        'id': ts.station.id,
                        'name': ts.station.name,
                        'order': ts.order_number,
                        'eta_minutes': max(0, eta),
                    }))
                if ts.order_number >= current_order:
                    eta = calculate_eta(trajet_stations, current_order - 1) - calculate_eta(trajet_stations, trajet_stations.index(ts))
                    dest_stations.append(StationWithETA({
                        'id': ts.station.id,
                        'name': ts.station.name,
                        'order': ts.order_number,
                        'eta_minutes': max(0, eta),
                    }))

            if user_stations:
                results.append(BusSearchResultSerializer({
                    'driver_session_id': session.id,
                    'driver_id': session.driver_id,
                    'trajet_name': session.trajet.name,
                    'bus_current_station': session.current_station,
                    'bus_current_order': session.current_order,
                    'user_stations': user_stations,
                    'destination_stations': dest_stations,
                    'status': session.status,
                }).data)

        return Response(results)


# ==============================================================================
# JOURNEY ENDPOINTS (Driver app)
# ==============================================================================

class DriverStartJourneyAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def post(self, request):
        serializer = StartJourneySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        trajet = get_object_or_404(Trajet, id=data['trajet_id'])
        departure = get_object_or_404(Station, id=data['departure_station_id'])
        arrival = get_object_or_404(Station, id=data['arrival_station_id'])
        departure_order = get_station_order(trajet.id, departure.id)
        if departure_order is None:
            return Response({'error': 'Station de départ invalide.'}, status=400)
        session = DriverSession.objects.create(
            driver_id=request.user.id,
            trajet=trajet,
            departure_station=departure,
            arrival_station=arrival,
            current_station=departure,
            current_order=departure_order,
            status='IN_PROGRESS',
            started_at=timezone.now(),
        )
        return Response(DriverSessionSerializer(session).data, status=201)


class DriverUpdateStationAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def post(self, request):
        serializer = UpdateStationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        station_id = serializer.validated_data['station_id']
        session = DriverSession.objects.filter(driver_id=request.user.id, status='IN_PROGRESS').first()
        if not session:
            return Response({'error': 'Aucune session active.'}, status=400)
        ts = TrajetStation.objects.filter(trajet=session.trajet, station_id=station_id).first()
        if not ts:
            return Response({'error': 'Station invalide pour ce trajet.'}, status=400)
        session.current_station = ts.station
        session.current_order = ts.order_number
        session.status = 'ARRIVED_AT_STATION' if ts.station_id == session.arrival_station_id else 'IN_PROGRESS'
        session.save(update_fields=['current_station', 'current_order', 'status'])
        return Response(DriverSessionSerializer(session).data)


class DriverFinishJourneyAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def post(self, request):
        session = DriverSession.objects.filter(driver_id=request.user.id, status='IN_PROGRESS').first()
        if not session:
            return Response({'error': 'Aucune session active.'}, status=400)
        session.status = 'FINISHED'
        session.finished_at = timezone.now()
        session.save(update_fields=['status', 'finished_at'])
        return Response({'message': 'Session terminée.'})


class DriverCurrentJourneyAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def get(self, request):
        session = DriverSession.objects.filter(driver_id=request.user.id, status='IN_PROGRESS').first()
        return Response(DriverSessionSerializer(session).data if session else None)


# ==============================================================================
# ADMIN CRUD VIEWSETS
# ==============================================================================

class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    permission_classes = [IsAuthenticated]


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all().order_by('plate_number')
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class LineViewSet(viewsets.ModelViewSet):
    queryset = Line.objects.all().order_by('name')
    serializer_class = LineSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class TrajetViewSet(viewsets.ModelViewSet):
    queryset = Trajet.objects.all().order_by('name')
    serializer_class = TrajetAdminSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class TrajetStationViewSet(viewsets.ModelViewSet):
    queryset = TrajetStation.objects.all().order_by('trajet_id', 'order_number')
    serializer_class = TrajetStationAdminSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class ImportedStationViewSet(viewsets.ModelViewSet):
    queryset = ImportedStation.objects.all().order_by('-created_at')
    serializer_class = ImportedStationSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class ImportedRouteViewSet(viewsets.ModelViewSet):
    queryset = ImportedRoute.objects.all().order_by('-created_at')
    serializer_class = ImportedRouteSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class ImportedRouteStationViewSet(viewsets.ModelViewSet):
    queryset = ImportedRouteStation.objects.all().order_by('imported_route', 'order_number')
    serializer_class = ImportedRouteStationSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all().select_related('trajet__line', 'vehicle')
    serializer_class = TripSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter.upper())
        driver = self.request.query_params.get('driver_id')
        if driver:
            qs = qs.filter(driver_id=driver)
        return qs

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        trip = self.get_object()
        if trip.status != 'SCHEDULED':
            return Response({'error': 'Seuls les trajets planifiés peuvent être démarrés.'}, status=400)
        trip.status = 'IN_PROGRESS'
        trip.actual_start = timezone.now()
        trip.save(update_fields=['status', 'actual_start'])
        return Response(TripSerializer(trip).data)

    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        trip = self.get_object()
        if trip.status != 'IN_PROGRESS':
            return Response({'error': 'Seuls les trajets en cours peuvent être terminés.'}, status=400)
        trip.status = 'COMPLETED'
        trip.actual_end = timezone.now()
        trip.save(update_fields=['status', 'actual_end'])
        return Response(TripSerializer(trip).data)


# ==============================================================================
# GTFS IMPORT / SYNC / PROMOTE
# ==============================================================================

class GTFSImportAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "Fichier GTFS (.zip) requis."}, status=400)
        try:
            zf = zipfile.ZipFile(io.BytesIO(file.read()))
            result = parse_and_import_gtfs(zf)
            return Response(result, status=201)
        except zipfile.BadZipFile:
            return Response({"error": "Le fichier n'est pas un ZIP valide."}, status=400)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": f"Erreur GTFS : {str(e)}"}, status=500)


class GTFSSyncAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        from django.utils import timezone
        imported = ImportedRoute.objects.filter(is_approved=True, approved_trajet__isnull=True).count()
        return Response({"message": "Sync terminé.", "imported_routes_pending": imported})


class FetchStationsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        city = request.data.get('city')
        station_type = request.data.get('station_type', 'BUS')
        if not city:
            return Response({"error": "Paramètre 'city' requis."}, status=400)
        result = fetch_and_store_stations(city, station_type)
        return Response(result, status=201)


class PromoteStationsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        serializer = PromoteStationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data['imported_station_ids']
        promoted = 0
        for imp_station in ImportedStation.objects.filter(id__in=ids, is_approved=False):
            station, created = Station.objects.get_or_create(
                name=imp_station.name,
                defaults={
                    'location_lat': imp_station.latitude,
                    'location_lng': imp_station.longitude,
                    'has_kiosk': False,
                    'is_verified': True,
                }
            )
            imp_station.approved_station = station
            imp_station.is_approved = True
            imp_station.save(update_fields=['approved_station', 'is_approved'])
            promoted += 1
        return Response({"message": f"{promoted} stations promues."})


class PromoteRoutesAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        serializer = PromoteRouteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data['imported_route_ids']
        promoted = 0
        for imp_route in ImportedRoute.objects.filter(id__in=ids, is_approved=False):
            line, _ = Line.objects.get_or_create(name=imp_route.line_name or imp_route.name)
            trajet = Trajet.objects.create(
                line=line,
                name=imp_route.name,
                is_active=True,
            )
            imp_route.approved_trajet = trajet
            imp_route.is_approved = True
            imp_route.save(update_fields=['approved_trajet', 'is_approved'])
            route_stations = imp_route.imported_stations.select_related('imported_station').order_by('order_number')
            for rs in route_stations:
                imp_station = rs.imported_station
                station, _ = Station.objects.get_or_create(
                    name=imp_station.name,
                    defaults={
                        'location_lat': imp_station.latitude,
                        'location_lng': imp_station.longitude,
                        'is_verified': True,
                    }
                )
                if not imp_station.is_approved:
                    imp_station.approved_station = station
                    imp_station.is_approved = True
                    imp_station.save(update_fields=['approved_station', 'is_approved'])
                TrajetStation.objects.get_or_create(
                    trajet=trajet,
                    station=station,
                    defaults={'order_number': rs.order_number}
                )
            promoted += 1
        return Response({"message": f"{promoted} routes promues."})


class AdminImportSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        return Response({
            "stations": ImportedStation.objects.count(),
            "routes": ImportedRoute.objects.count(),
            "route_stations": ImportedRouteStation.objects.count(),
            "pending_stations": ImportedStation.objects.filter(is_approved=False).count(),
            "pending_routes": ImportedRoute.objects.filter(is_approved=False).count(),
        })


# ==============================================================================
# SIMULATION
# ==============================================================================

class SimulationStartAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        serializer = serializers.Serializer(data=request.data)
        serializer.route_id = serializers.UUIDField(required=True)
        serializer.vehicle_id = serializers.UUIDField(required=True)
        serializer.driver_id = serializers.UUIDField(required=False)
        serializer.interval_seconds = serializers.IntegerField(default=10, min_value=1, max_value=300)
        serializer.total_points = serializers.IntegerField(default=20, min_value=1, max_value=500)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        trajet = get_object_or_404(Trajet, id=data['route_id'])
        vehicle = get_object_or_404(Vehicle, id=data['vehicle_id'])

        from domains.transit_tracking.websockets.tasks import simulate_gps_route
        simulate_gps_route.delay(
            str(trajet.id),
            str(vehicle.id),
            str(data.get('driver_id', request.user.id)),
            data['interval_seconds'],
            data['total_points']
        )
        return Response({
            "message": "Simulation GPS démarrée.",
            "route": trajet.name,
            "vehicle": vehicle.plate_number,
            "total_points": data['total_points'],
            "interval_seconds": data['interval_seconds']
        }, status=202)


# ==============================================================================
# ETA
# ==============================================================================

class ETADetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_id, station_id):
        from domains.transit_tracking.services import ETAService
        eta = ETAService.estimate_arrival_time(trip_id, station_id)
        if not eta:
            return Response({"error": "ETA indisponible pour ce trajet/station."}, status=404)
        return Response(eta)


class ETAAllStationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_id):
        from domains.transit_tracking.services import ETAService
        etas = ETAService.estimate_all_stations(trip_id)
        return Response(etas)
