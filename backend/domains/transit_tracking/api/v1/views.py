from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import RouteSerializer, TripSerializer, LineSerializer
from domains.transit_tracking.models import Route, Trip, Line

class LineViewSet(viewsets.ModelViewSet):
    queryset = Line.objects.all()
    serializer_class = LineSerializer
    permission_classes = [IsAuthenticated]

class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    permission_classes = [IsAuthenticated]

class TripListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # DÉCISION CTO : Optimisation N+1 (Crucial pour la scalabilité)
        # select_related force une jointure SQL immédiate. Sans ça, Django ferait
        # une requête SQL par Trip pour récupérer la Route et le Vehicle.
        trips = Trip.objects.filter(status='IN_PROGRESS').select_related('route', 'vehicle')
        return Response(TripSerializer(trips, many=True).data)

from domains.transit_tracking.models import Route, Trip, Line, Station, GPSLog

class LiveFleetAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        active_trips = Trip.objects.filter(status='IN_PROGRESS').select_related('vehicle', 'route')
        fleet_data = []
        
        for trip in active_trips:
            latest_log = GPSLog.objects.filter(trip=trip).order_by('-recorded_at').first()
            fleet_data.append({
                "id": str(trip.vehicle.id),
                "fleet_id": trip.vehicle.fleet_id,
                "line": trip.route.line.name,
                "status": trip.status,
                "lat": latest_log.location.y if latest_log else 36.8, # Fallback Tunis
                "lng": latest_log.location.x if latest_log else 10.1,
                "speed": float(latest_log.speed_kmh) if latest_log else 0,
                "driver": "Driver " + str(trip.driver_id)[:8]
            })
            
        return Response(fleet_data)

from rest_framework import viewsets
from domains.transit_tracking.models import Station
from .serializers import StationSerializer

class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    permission_classes = [IsAuthenticated]
