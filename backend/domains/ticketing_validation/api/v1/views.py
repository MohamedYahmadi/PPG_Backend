from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from django.contrib.gis.geos import Point
from django.shortcuts import get_object_or_404
from .serializers import (
    TicketPurchaseSerializer, TicketSerializer, OfflineValidationSyncSerializer,
    SubscriptionTypeSerializer, SubscriptionPurchaseSerializer, SubscriptionSerializer,
    FareSerializer, MarkTicketUsedSerializer, InvoiceSerializer,
    MultiPassengerPurchaseSerializer, MultiPassengerTicketSerializer
)
from domains.ticketing_validation.services import TicketingService
from domains.ticketing_validation.models import (
    Ticket, ValidationLog, SubscriptionType, Subscription, Fare, Invoice, MultiPassengerTicket
)
from domains.wallet_payments.services import InsufficientFundsException
from core.permissions import IsPassenger, IsController, IsAdmin


class TicketPurchaseAPIView(APIView):
    permission_classes = [IsAuthenticated, IsPassenger]

    def post(self, request):
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
            return Response({"detail": str(e)}, status=402)
        except Exception as e:
            return Response({"detail": str(e)}, status=400)


class TicketHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated, IsPassenger]

    def get(self, request):
        tickets = Ticket.objects.filter(passenger=request.user).order_by('-created_at')[:50]
        return Response(TicketSerializer(tickets, many=True).data)


class OfflineValidationSyncAPIView(APIView):
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
                scan_location=Point(data['scan_location_lng'], data['scan_location_lat'], srid=4326),
                scanned_at=data['scanned_at'],
                is_cryptographically_valid=data['is_cryptographically_valid'],
                sync_status='SYNCED',
                device_id=data['device_id']
            )
            created_logs.append(log)

        ValidationLog.objects.bulk_create(created_logs)

        from domains.ticketing_validation.tasks import fraud_detection_engine
        for log in created_logs:
            fraud_detection_engine.delay(str(log.ticket_id))

        return Response({
            "message": f"{len(created_logs)} validations synchronisées avec succès."
        }, status=201)


class MarkTicketUsedAPIView(APIView):
    permission_classes = [IsAuthenticated, IsController]

    def post(self, request):
        serializer = MarkTicketUsedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            ticket = TicketingService.mark_ticket_used(
                serializer.validated_data['ticket_id'],
                request.user
            )
            return Response({
                "message": "Ticket marqué comme utilisé.",
                "ticket": TicketSerializer(ticket).data
            })
        except ValueError as e:
            return Response({"error": str(e)}, status=400)


class SubscriptionTypeListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        types = SubscriptionType.objects.filter(is_active=True)
        return Response(SubscriptionTypeSerializer(types, many=True).data)


class SubscriptionPurchaseAPIView(APIView):
    permission_classes = [IsAuthenticated, IsPassenger]

    def post(self, request):
        serializer = SubscriptionPurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            subscription = TicketingService.purchase_subscription(
                passenger_id=request.user.id,
                subscription_type_id=serializer.validated_data['subscription_type_id']
            )
            return Response(SubscriptionSerializer(subscription).data, status=201)
        except InsufficientFundsException as e:
            return Response({"detail": str(e)}, status=402)
        except Exception as e:
            return Response({"detail": str(e)}, status=400)


class SubscriptionHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated, IsPassenger]

    def get(self, request):
        subs = Subscription.objects.filter(passenger=request.user).order_by('-created_at')[:50]
        return Response(SubscriptionSerializer(subs, many=True).data)


class FareViewSet(viewsets.ModelViewSet):
    queryset = Fare.objects.all()
    serializer_class = FareSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class FareCalculateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        category = request.data.get('category', 'STANDARD')
        zone_from = request.data.get('zone_from', request.data.get('zone_validity'))
        zone_to = request.data.get('zone_to', request.data.get('zone_validity'))
        price = TicketingService.calculate_fare(category, zone_from, zone_to)
        return Response({
            "category": category,
            "zone_from": zone_from,
            "zone_to": zone_to,
            "price": str(price)
        })


class InvoiceListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsPassenger]

    def get(self, request):
        invoices = TicketingService.get_user_invoices(request.user.id)
        return Response(InvoiceSerializer(invoices, many=True).data)


class MultiPassengerPurchaseAPIView(APIView):
    permission_classes = [IsAuthenticated, IsPassenger]

    def post(self, request):
        serializer = MultiPassengerPurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            multi = TicketingService.purchase_multi_passenger(
                purchaser_id=request.user.id,
                passengers=serializer.validated_data['passengers'],
                zone_validity=serializer.validated_data['zone_validity']
            )
            return Response(MultiPassengerTicketSerializer(multi).data, status=201)
        except Exception as e:
            return Response({"detail": str(e)}, status=400)
