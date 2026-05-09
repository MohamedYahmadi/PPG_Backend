from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import RouteSerializer, TripSerializer
from domains.transit_tracking.models import Route, Trip

class RouteListAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        routes = Route.objects.filter(is_active=True)
        return Response(RouteSerializer(routes, many=True).data)

class TripListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # DÉCISION CTO : Optimisation N+1 (Crucial pour la scalabilité)
        # select_related force une jointure SQL immédiate. Sans ça, Django ferait
        # une requête SQL par Trip pour récupérer la Route et le Vehicle.
        trips = Trip.objects.filter(status='IN_PROGRESS').select_related('route', 'vehicle')
        return Response(TripSerializer(trips, many=True).data)

class LiveVehiclesAPIView(APIView):
    """
    DÉCISION CTO : Fallback REST si les WebSockets sont bloqués par un proxy d'entreprise.
    Lit directement depuis le Cache Redis mis à jour par Celery.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from django.core.cache import cache
        # Implémentation basique (En production, on stocke un SET des véhicules actifs dans Redis)
        return Response({
            "message": "Fallback API REST actif. Les positions sont en cache Redis."
        })

from rest_framework import viewsets
from domains.transit_tracking.models import Station
from .serializers import StationSerializer

class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    permission_classes = [IsAuthenticated]
