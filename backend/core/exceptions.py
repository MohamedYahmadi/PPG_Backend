from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework.exceptions import Throttled
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    DÉCISION CTO : Ne jamais fuiter de stacktraces (Sécurité).
    Intercepte les exceptions non gérées et retourne une APIException JSON structurée.
    """
    response = exception_handler(exc, context)

    if isinstance(exc, Throttled):
        custom_response_data = {
            'detail': 'Trop de requêtes. Veuillez ralentir.',
            'available_in': f'{exc.wait} seconds'
        }
        response.data = custom_response_data

    if response is not None:
        response.data['status_code'] = response.status_code
    else:
        # Erreur interne non gérée (ex: Bug Python ou DB Down)
        logger.critical(f"CRITICAL SYSTEM ERROR: {exc}", exc_info=True)
        return Response({
            "detail": "Erreur interne du système SITP. Les ingénieurs ont été notifiés.",
            "status_code": 500
        }, status=500)

    return response
