from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.shortcuts import redirect

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
    path('api/v1/notifications/', include('domains.notifications.api.v1.urls')),
    path('api/v1/transit/', include('domains.transit_tracking.api.v1.urls')),
    path('api/v1/admin/', include('domains.admin_dashboard.api.v1.urls')),

    # Frontend Compatibility Aliases
    path('api/v1/fines/all/', lambda r: redirect('/api/v1/admin/fines/all/')),
    path('api/v1/wallet/admin/list/', lambda r: redirect('/api/v1/admin/wallets/list/')),
    path('api/v1/transit/live-fleet/', lambda r: redirect('/api/v1/transit/live-vehicles/')),
    path('api/v1/transit/fraud/alerts/', lambda r: redirect('/api/v1/admin/fraud/alerts/')),
]
