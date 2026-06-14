from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdmin
from domains.ticketing_validation.models import Ticket
from domains.wallet_payments.models import WalletTransaction
from django.db.models import Sum
from rest_framework import viewsets
from .serializers import SystemSettingSerializer
from domains.admin_dashboard.models import SystemSetting

from django.utils import timezone
from datetime import timedelta
from domains.auth_identity.models import User
from domains.transit_tracking.models import Route

class DashboardMetricsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        # 1. Basic Counts
        total_tickets_sold = Ticket.objects.count()
        total_revenue_dict = WalletTransaction.objects.filter(type='CREDIT_RECHARGE').aggregate(Sum('amount'))
        total_revenue = total_revenue_dict['amount__sum'] or 0
        fraud_alerts_count = Ticket.objects.filter(status='FRAUDULENT').count()
        active_passengers_count = User.objects.filter(role='PASSENGER', is_active=True).count()
        
        # 2. Revenue History (Last 7 days)
        revenue_history = []
        now = timezone.now()
        for i in range(6, -1, -1):
            day = now - timedelta(days=i)
            day_name = day.strftime('%a')
            day_revenue = WalletTransaction.objects.filter(
                type='CREDIT_RECHARGE', 
                created_at__date=day.date()
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            # If no data, use a small randomized value for demo purposes if needed, 
            # but here we'll stick to real data (even if 0)
            revenue_history.append({"name": day_name, "value": float(day_revenue)})

        # 3. Fraud by Line (Mocked since Ticket doesn't have Route yet, but based on real Route names)
        routes = Route.objects.all()[:4]
        fraud_by_line = []
        for route in routes:
            # Pseudo-random fraud count based on route ID for stability in demo
            fraud_count = (hash(str(route.id)) % 500) + 50
            fraud_by_line.append({"name": route.name, "value": fraud_count})

        if not fraud_by_line: # Fallback
            fraud_by_line = [
                {"name": "Ligne 1", "value": 400},
                {"name": "Ligne 2", "value": 300},
            ]

        return Response({
            "metrics": {
                "total_tickets_sold": total_tickets_sold,
                "total_recharge_revenue_tnd": float(total_revenue),
                "active_fraud_alerts": fraud_alerts_count,
                "active_passengers": active_passengers_count,
                "revenue_growth": 12.5, # Static for now
                "tickets_growth": 18.2,
                "passengers_growth": 5.4
            },
            "revenue_history": revenue_history,
            "fraud_by_line": fraud_by_line
        })

class SystemSettingViewSet(viewsets.ModelViewSet):
    queryset = SystemSetting.objects.all()
    serializer_class = SystemSettingSerializer
    permission_classes = [IsAuthenticated]
