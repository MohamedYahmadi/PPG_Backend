from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import viewsets, status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .serializers import (
    RouteSerializer, TripSerializer, TripCreateSerializer,
    VehicleSerializer, StationSerializer, LineSerializer,
    ScheduleSerializer, LineConnectionSerializer, GPSLogSerializer,
    GPSPushSerializer, SimulationSerializer
)
from domains.transit_tracking.services import ETAService
from domains.transit_tracking.models import (
    Route, Trip, Vehicle, Station, Line, Schedule, LineConnection, GPSLog
)
from core.permissions import IsAdmin, IsDriver


class LineViewSet(viewsets.ModelViewSet):
    queryset = Line.objects.all()
    serializer_class = LineSerializer
    permission_classes = [IsAuthenticated]


class RouteListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        routes = Route.objects.filter(is_active=True).select_related('line')
        return Response(RouteSerializer(routes, many=True).data)


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all().select_related('line')
    serializer_class = RouteSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    permission_classes = [IsAuthenticated]


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class TripListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        trips = Trip.objects.filter(status='IN_PROGRESS').select_related('route__line', 'vehicle')
        return Response(TripSerializer(trips, many=True).data)


class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all().select_related('route__line', 'vehicle')
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


class TripCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        serializer = TripCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        trip = Trip.objects.create(
            route_id=data['route_id'],
            vehicle_id=data['vehicle_id'],
            driver_id=data['driver_id'],
            scheduled_start=data['scheduled_start'],
            status=data.get('status', 'SCHEDULED')
        )
        return Response(TripSerializer(trip).data, status=201)


class TripStartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_id):
        trip = get_object_or_404(Trip, id=trip_id)
        if request.user.role == 'DRIVER' and str(request.user.id) != str(trip.driver_id):
            return Response({"error": "Ce trajet ne vous est pas assigné."}, status=403)
        trip.actual_start = timezone.now()
        trip.status = 'IN_PROGRESS'
        trip.save()
        return Response({"message": "Trajet démarré.", "trip": TripSerializer(trip).data})


class TripEndAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_id):
        trip = get_object_or_404(Trip, id=trip_id)
        if request.user.role == 'DRIVER' and str(request.user.id) != str(trip.driver_id):
            return Response({"error": "Ce trajet ne vous est pas assigné."}, status=403)
        trip.actual_end = timezone.now()
        trip.status = 'COMPLETED'
        trip.save()
        return Response({"message": "Trajet terminé.", "trip": TripSerializer(trip).data})


class LiveVehiclesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.core.cache import cache
        active_trips = Trip.objects.filter(status='IN_PROGRESS').select_related('route__line', 'vehicle')
        result = []
        for trip in active_trips:
            cache_key = f"vehicle_last_loc_{trip.vehicle_id}"
            last_loc = cache.get(cache_key)
            result.append({
                "id": str(trip.vehicle.id),
                "fleet_id": trip.vehicle.fleet_id,
                "plate_number": trip.vehicle.plate_number,
                "line": trip.route.line.name if trip.route.line else None,
                "line_color": trip.route.line.color_code if trip.route.line else None,
                "route_name": trip.route.name,
                "trip_id": str(trip.id),
                "driver_id": str(trip.driver_id),
                "status": trip.status,
                "lat": last_loc['geom'].y if last_loc and last_loc.get('geom') else None,
                "lng": last_loc['geom'].x if last_loc and last_loc.get('geom') else None,
                "speed": last_loc.get('speed', 0) if last_loc else 0,
            })
        return Response(result)


class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all().select_related('route')
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class LineConnectionViewSet(viewsets.ModelViewSet):
    queryset = LineConnection.objects.all().select_related(
        'from_line', 'to_line', 'from_station', 'to_station'
    )
    serializer_class = LineConnectionSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class GPSPushAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def post(self, request):
        serializer = GPSPushSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        from domains.transit_tracking.websockets.tasks import process_gps_batch
        process_gps_batch.delay(
            str(request.user.id),
            {
                'trip_id': str(data['trip_id']),
                'vehicle_id': str(data['vehicle_id']),
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


class SimulationStartAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        serializer = SimulationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        route = get_object_or_404(Route, id=data['route_id'])
        vehicle = get_object_or_404(Vehicle, id=data['vehicle_id'])

        from domains.transit_tracking.websockets.tasks import simulate_gps_route
        simulate_gps_route.delay(
            str(route.id),
            str(vehicle.id),
            str(data.get('driver_id', request.user.id)),
            data['interval_seconds'],
            data['total_points']
        )
        return Response({
            "message": "Simulation GPS démarrée.",
            "route": route.name,
            "vehicle": vehicle.plate_number,
            "total_points": data['total_points'],
            "interval_seconds": data['interval_seconds']
        }, status=202)


class ETADetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_id, station_id):
        eta = ETAService.estimate_arrival_time(trip_id, station_id)
        if not eta:
            return Response({"error": "ETA indisponible pour ce trajet/station."}, status=404)
        return Response(eta)


class ETAAllStationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_id):
        etas = ETAService.estimate_all_stations(trip_id)
        return Response(etas)
