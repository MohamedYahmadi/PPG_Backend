from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.gis.geos import Point
from .serializers import TicketPurchaseSerializer, TicketSerializer, OfflineValidationSyncSerializer
from domains.ticketing_validation.services import TicketingService
from domains.ticketing_validation.models import Ticket, ValidationLog
from domains.wallet_payments.services import InsufficientFundsException
from core.permissions import IsPassenger, IsController

class TicketPurchaseAPIView(APIView):
    permission_classes = [IsAuthenticated, IsPassenger]
    
    def post(self, request):
        """
        DÉCISION CTO : L'API ne gère aucune transaction. 
        Elle se contente de passer la commande à TicketingService (Service Layer) 
        qui lui exécute le pessimistic locking du Wallet et la création du Ticket.
        """
        serializer = TicketPurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        try:
            ticket = TicketingService.purchase_ticket(
                passenger_id=request.user.id,
                zone_validity=data['zone_validity'],
                price=data['price']
            )
            return Response(TicketSerializer(ticket).data, status=201)
        except InsufficientFundsException as e:
            return Response({"detail": str(e)}, status=402) # 402 Payment Required
        except Exception as e:
            return Response({"detail": str(e)}, status=400)

class TicketHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated, IsPassenger]
    
    def get(self, request):
        tickets = Ticket.objects.filter(passenger=request.user).order_by('-created_at')[:50]
        return Response(TicketSerializer(tickets, many=True).data)

class OfflineValidationSyncAPIView(APIView):
    """
    DÉCISION CTO : Cet Endpoint reçoit les logs accumulés par les contrôleurs 
    lorsqu'ils étaient hors-ligne (ex: dans le métro). 
    L'ingestion se fait en batch optimisé.
    """
    permission_classes = [IsAuthenticated, IsController]
    
    def post(self, request):
        is_many = isinstance(request.data, list)
        serializer = OfflineValidationSyncSerializer(data=request.data, many=is_many)
        serializer.is_valid(raise_exception=True)
        
        validations_data = serializer.validated_data if is_many else [serializer.validated_data]
        
        created_logs = []
        for data in validations_data:
            log = ValidationLog(
                ticket_id=data['ticket_id'],
                controller=request.user,
                scan_location=Point(data['scan_location_lng'], data['scan_location_lat'], srid=4326), # PostGIS
                scanned_at=data['scanned_at'],
                is_cryptographically_valid=data['is_cryptographically_valid'],
                sync_status='SYNCED',
                device_id=data['device_id']
            )
            created_logs.append(log)
            
        # Bulk insert ultra-rapide
        ValidationLog.objects.bulk_create(created_logs)
        
        # Déclenchement ASYNCHRONE (Celery) du Moteur Anti-Fraude
        from domains.ticketing_validation.tasks import fraud_detection_engine
        for log in created_logs:
            fraud_detection_engine.delay(str(log.ticket_id))
            
        return Response({"message": f"{len(created_logs)} validations synchronisées avec succès."}, status=201)
