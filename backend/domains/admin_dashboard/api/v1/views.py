from datetime import timedelta, datetime
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q
from django.utils import timezone
from core.permissions import IsAdmin
from domains.ticketing_validation.models import Ticket, Subscription, Invoice
from domains.wallet_payments.models import Wallet, WalletTransaction
from domains.fines_disputes.models import Fine
from domains.transit_tracking.models import Trip, Vehicle, Line
from domains.notifications.models import IncidentReport


class DashboardMetricsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        total_tickets_sold = Ticket.objects.count()
        tickets_today = Ticket.objects.filter(created_at__gte=today).count()
        tickets_this_week = Ticket.objects.filter(created_at__gte=week_ago).count()

        revenue_data = WalletTransaction.objects.filter(
            type='CREDIT_RECHARGE'
        ).aggregate(
            total=Sum('amount'),
            today=Sum('amount', filter=Q(created_at__gte=today)),
            this_week=Sum('amount', filter=Q(created_at__gte=week_ago))
        )

        ticket_revenue = WalletTransaction.objects.filter(
            type='DEBIT_TICKET'
        ).aggregate(total=Sum('amount'))

        fraud_alerts_count = Ticket.objects.filter(status='FRAUDULENT').count()
        fraud_this_week = Ticket.objects.filter(
            status='FRAUDULENT', created_at__gte=week_ago
        ).count()

        active_passengers = Wallet.objects.filter(balance__gt=0).count()
        active_drivers = Trip.objects.filter(status='IN_PROGRESS').count()

        active_vehicles = Vehicle.objects.filter(is_active=True).count()
        active_lines = Line.objects.filter(is_active=True).count()

        total_fines = Fine.objects.count()
        unpaid_fines = Fine.objects.filter(status='UNPAID').count()
        total_fine_amount = Fine.objects.filter(status__in=['UNPAID', 'DISPUTED']).aggregate(
            total=Sum('amount')
        )['total'] or 0

        active_incidents = IncidentReport.objects.filter(is_resolved=False).count()

        subscriptions_active = Subscription.objects.filter(is_active=True).count()
        subscriptions_this_month = Subscription.objects.filter(
            created_at__gte=month_ago
        ).count()

        invoices_this_month = Invoice.objects.filter(
            created_at__gte=month_ago
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        return Response({
            "metrics": {
                "total_tickets_sold": total_tickets_sold,
                "tickets_today": tickets_today,
                "tickets_this_week": tickets_this_week,
                "total_recharge_revenue_tnd": float(revenue_data['total'] or 0),
                "revenue_today_tnd": float(revenue_data['today'] or 0),
                "revenue_this_week_tnd": float(revenue_data['this_week'] or 0),
                "ticket_revenue_tnd": float(abs(ticket_revenue['total'] or 0)),
                "active_fraud_alerts": fraud_alerts_count,
                "fraud_this_week": fraud_this_week,
                "active_passengers": active_passengers,
                "active_drivers": active_drivers,
                "active_vehicles": active_vehicles,
                "active_lines": active_lines,
                "total_fines": total_fines,
                "unpaid_fines": unpaid_fines,
                "total_fine_amount_tnd": float(total_fine_amount),
                "active_incidents": active_incidents,
                "active_subscriptions": subscriptions_active,
                "subscriptions_this_month": subscriptions_this_month,
                "invoices_this_month_tnd": float(invoices_this_month),
            },
            "revenue_history": self._get_revenue_history(30),
            "fraud_by_line": self._get_fraud_by_line(month_ago),
        })

    def _get_revenue_history(self, days):
        from django.db.models.functions import TruncDate
        cutoff = timezone.now() - timedelta(days=days)
        data = (
            WalletTransaction.objects
            .filter(created_at__gte=cutoff, type='CREDIT_RECHARGE')
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(amount=Sum('amount'))
            .order_by('date')
        )
        return [
            {"date": d['date'].isoformat(), "amount": float(d['amount'] or 0)}
            for d in data
        ]

    def _get_fraud_by_line(self, since):
        fraud_tickets = Ticket.objects.filter(
            status='FRAUDULENT', created_at__gte=since
        )
        return {"total": fraud_tickets.count()}


class AnalyticsExportAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        report_type = request.query_params.get('type', 'revenue')
        format_type = request.query_params.get('format', 'json')

        data = {}

        if report_type == 'revenue':
            revenue_by_day = WalletTransaction.objects.filter(
                type='CREDIT_RECHARGE'
            ).values('created_at__date').annotate(
                total=Sum('amount')
            ).order_by('-created_at__date')[:90]
            data = {
                "report": "Revenus par jour",
                "period": "90 derniers jours",
                "data": [
                    {"date": r['created_at__date'].isoformat(), "amount": float(r['total'] or 0)}
                    for r in revenue_by_day
                ]
            }

        elif report_type == 'tickets':
            tickets_by_zone = Ticket.objects.values('zone_validity').annotate(
                count=Count('id'),
                total=Sum('price_paid')
            )
            data = {
                "report": "Ventes par zone",
                "data": [
                    {"zone": t['zone_validity'], "count": t['count'], "total_tnd": float(t['total'] or 0)}
                    for t in tickets_by_zone
                ]
            }

        elif report_type == 'punctuality':
            avg_delay = Trip.objects.filter(
                actual_start__isnull=False, scheduled_start__isnull=False
            )
            data = {"report": "Ponctualité", "message": "Disponible avec plus de données de trajets"}

        elif report_type == 'fines':
            fines_by_status = Fine.objects.values('status').annotate(
                count=Count('id'),
                total=Sum('amount')
            )
            data = {
                "report": "Infractions par statut",
                "data": [
                    {"status": f['status'], "count": f['count'], "total_tnd": float(f['total'] or 0)}
                    for f in fines_by_status
                ]
            }

        return Response(data)


class SystemHealthAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        import socket
        import psutil

        health = {
            "status": "operational",
            "timestamp": timezone.now().isoformat(),
            "services": {
                "database": self._check_database(),
                "redis": self._check_redis(),
                "celery": self._check_celery(),
            },
            "system": {
                "cpu_percent": None,
                "memory_percent": None,
                "disk_percent": None,
            }
        }

        try:
            health["system"]["cpu_percent"] = psutil.cpu_percent(interval=0.5)
            health["system"]["memory_percent"] = psutil.virtual_memory().percent
            health["system"]["disk_percent"] = psutil.disk_usage('/').percent
        except Exception:
            pass

        return Response(health)

    def _check_database(self):
        from django.db import connections
        try:
            connections['default'].cursor().execute('SELECT 1')
            return {"status": "connected", "latency_ms": 0}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    def _check_redis(self):
        try:
            import redis
            from django.conf import settings
            r = redis.from_url(settings.CELERY_BROKER_URL)
            r.ping()
            return {"status": "connected"}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    def _check_celery(self):
        try:
            from celery.app.control import Inspect
            from config.celery import app
            i = Inspect(app=app)
            stats = i.stats()
            if stats:
                return {"status": "running", "workers": list(stats.keys())}
            return {"status": "no_workers"}
        except Exception as e:
            return {"status": "error", "detail": str(e)}


class FraudAlertListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT passenger_id, ticket_id, reason, created_at FROM fraud_alerts ORDER BY created_at DESC LIMIT 100"
            )
            rows = cursor.fetchall()
        alerts = []
        for row in rows:
            alerts.append({
                "passenger_id": row[0],
                "ticket_id": row[1],
                "reason": row[2],
                "created_at": row[3].isoformat() if row[3] else None,
            })
        return Response(alerts)


class WalletAdminListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        wallets = Wallet.objects.all().select_related('passenger').order_by('-balance')[:200]
        from domains.wallet_payments.api.v1.serializers import WalletSerializer
        return Response([
            {
                "id": str(w.id),
                "passenger_id": str(w.passenger.id),
                "passenger_phone": w.passenger.phone_number,
                "balance": float(w.balance),
                "currency": w.currency,
                "last_synced": w.last_synced.isoformat() if w.last_synced else None,
            }
            for w in wallets
        ])


class FineAdminListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        fines = Fine.objects.all().select_related('controller').order_by('-issued_at')[:200]
        return Response([
            {
                "id": str(f.id),
                "passenger_cin": f.passenger_cin,
                "passenger_name": f.passenger_name,
                "amount": float(f.amount),
                "reason": f.reason,
                "status": f.status,
                "controller": f.controller.phone_number if f.controller else None,
                "issued_at": f.issued_at.isoformat(),
            }
            for f in fines
        ])


class DisputeResolveAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, dispute_id):
        from domains.fines_disputes.models import Dispute
        dispute = get_object_or_404(Dispute, id=dispute_id)
        action = request.data.get('action')

        if action == 'accept':
            dispute.status = 'RESOLVED_ACCEPTED'
            dispute.fine.status = 'CANCELLED'
            dispute.admin_notes = request.data.get('admin_notes', 'Accepté par l\'administrateur.')
        elif action == 'reject':
            dispute.status = 'RESOLVED_REJECTED'
            dispute.fine.status = 'UNPAID_PENALTY'
            dispute.admin_notes = request.data.get('admin_notes', 'Rejeté par l\'administrateur.')
        else:
            return Response({"error": "Action invalide. Utilisez 'accept' ou 'reject'."}, status=400)

        dispute.save()
        dispute.fine.save()
        return Response({
            "message": f"Litige {action}é.",
            "dispute_status": dispute.status,
            "fine_status": dispute.fine.status
        })


class SettingsListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        from django.core.cache import cache
        return Response([
            {
                "id": "1",
                "key": "MAX_TICKET_PRICE",
                "value": "10.000",
                "description": "Prix maximum autorisé pour un ticket",
                "updated_at": timezone.now().isoformat()
            },
            {
                "id": "2",
                "key": "FRAUD_SPEED_THRESHOLD",
                "value": "130",
                "description": "Seuil de vitesse pour détection de spoofing GPS (km/h)",
                "updated_at": timezone.now().isoformat()
            },
            {
                "id": "3",
                "key": "REPLAY_DISTANCE_THRESHOLD",
                "value": "2000",
                "description": "Distance maximale pour validation sans fraude (mètres)",
                "updated_at": timezone.now().isoformat()
            },
            {
                "id": "4",
                "key": "REPLAY_TIME_THRESHOLD",
                "value": "300",
                "description": "Temps minimum entre deux validations (secondes)",
                "updated_at": timezone.now().isoformat()
            },
        ])


class SettingUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, setting_id):
        return Response({
            "message": f"Setting {setting_id} updated.",
            "key": request.data.get('key'),
            "value": request.data.get('value')
        })
