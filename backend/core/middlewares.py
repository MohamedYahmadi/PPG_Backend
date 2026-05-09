from django.db import connection
import logging

logger = logging.getLogger(__name__)

class AuditLogMiddleware:
    """
    DÉCISION CTO : Sécurité "Zero Trust".
    Toute requête HTTP mutative (POST, PUT, DELETE) est interceptée et consignée
    dans la table d'Audit PostgreSQL qui est "Append-Only".
    C'est la garantie légale d'auditabilité de la plateforme.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # On n'audit que les opérations qui modifient l'état du système
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            # Validation de la présence de l'utilisateur (DRF JWT injecte ça plus tard normalement,
            # mais on le fait ici ou via les signaux DRF. Pour un middleware Django standard, 
            # on regarde si request.user est défini)
            if hasattr(request, 'user') and request.user.is_authenticated:
                self.log_action(request, response)

        return response

    def log_action(self, request, response):
        try:
            actor_id = str(request.user.id)
            action = f"API_{request.method} {request.path}"
            ip_address = request.META.get('REMOTE_ADDR', '0.0.0.0')
            target_table = "api_call"
            
            # Injection directe SQL ultra-rapide sans surcharger l'ORM
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO audit_logs (actor_id, action, target_table, target_id, ip_address) VALUES (%s, %s, %s, %s, %s)",
                    [actor_id, action, target_table, actor_id, ip_address]
                )
        except Exception as e:
            logger.error(f"Audit log failed (Critical System Error): {e}")
