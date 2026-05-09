from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdmin
from domains.ticketing_validation.models import Ticket
from domains.wallet_payments.models import WalletTransaction
from django.db.models import Sum

class DashboardMetricsAPIView(APIView):
    """
    DÉCISION CTO : Endpoint BI optimisé. 
    Effectue des agrégations directement via PostgreSQL (Count, Sum) 
    pour ne pas saturer la RAM du backend Django avec des objets ORM.
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        total_tickets_sold = Ticket.objects.count()
        
        # SUM natif SQL
        total_revenue_dict = WalletTransaction.objects.filter(type='CREDIT_RECHARGE').aggregate(Sum('amount'))
        total_revenue = total_revenue_dict['amount__sum'] or 0
        
        fraud_alerts_count = Ticket.objects.filter(status='FRAUDULENT').count()
        
        return Response({
            "metrics": {
                "total_tickets_sold": total_tickets_sold,
                "total_recharge_revenue_tnd": total_revenue,
                "active_fraud_alerts": fraud_alerts_count
            }
        })
