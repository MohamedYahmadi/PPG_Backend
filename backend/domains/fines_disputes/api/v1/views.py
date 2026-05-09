from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.gis.geos import Point
from django.shortcuts import get_object_or_404
from .serializers import FineSerializer, FineCreateSerializer, DisputeSerializer, DisputeCreateSerializer
from domains.fines_disputes.models import Fine, Dispute
from core.permissions import IsController, IsPassenger

class IssueFineAPIView(APIView):
    """
    DÉCISION CTO : Réservé aux contrôleurs équipés de terminaux.
    L'amende est géolocalisée (PostGIS) pour des raisons légales et d'auditabilité.
    """
    permission_classes = [IsAuthenticated, IsController]
    
    def post(self, request):
        serializer = FineCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        location = None
        if 'location_lat' in data and 'location_lng' in data:
            location = Point(data['location_lng'], data['location_lat'], srid=4326)
            
        fine = Fine.objects.create(
            controller=request.user,
            passenger_cin=data['passenger_cin'],
            passenger_name=data.get('passenger_name'),
            amount=data['amount'],
            reason=data['reason'],
            infraction_location=location,
            status='UNPAID'
        )
        return Response(FineSerializer(fine).data, status=201)

class CreateDisputeAPIView(APIView):
    """
    Workflow Légal : Le passager conteste son amende depuis l'App Mobile.
    L'amende passe en mode DISPUTED bloquant ainsi les pénalités de retard.
    """
    permission_classes = [IsAuthenticated, IsPassenger]
    
    def post(self, request):
        serializer = DisputeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        fine = get_object_or_404(Fine, id=data['fine_id'])
        
        # 1. Geler le statut de l'amende
        fine.status = 'DISPUTED'
        fine.save()
        
        # 2. Créer le litige
        dispute = Dispute.objects.create(
            fine=fine,
            passenger=request.user,
            reason=data['reason'],
            status='OPEN'
        )
        return Response(DisputeSerializer(dispute).data, status=201)
