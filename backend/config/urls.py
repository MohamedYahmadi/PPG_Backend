from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "ok", "service": "sitp_core"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check),
    
    # Modular Monolith - Routing API v1
    path('api/v1/auth/', include('domains.auth_identity.api.v1.urls')),
    path('api/v1/wallet/', include('domains.wallet_payments.api.v1.urls')),
    path('api/v1/tickets/', include('domains.ticketing_validation.api.v1.urls')),
    path('api/v1/fines/', include('domains.fines_disputes.api.v1.urls')),
    path('api/v1/admin/', include('domains.admin_dashboard.api.v1.urls')),
]
