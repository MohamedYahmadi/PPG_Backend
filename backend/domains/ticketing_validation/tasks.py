from celery import shared_task
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
import logging
from .models import ValidationLog, Ticket

logger = logging.getLogger(__name__)

@shared_task(queue='fraud_analysis', bind=True, max_retries=3)
def fraud_detection_engine(self, ticket_id: str):
    """
    DÉCISION CTO : Ce moteur tourne en arrière-plan (Asynchrone via Celery).
    Il est déclenché chaque fois qu'un terminal de Contrôleur synchronise ses données hors-ligne.
    Il cherche le "Replay Attack" : Le même QR Code scanné par 2 personnes différentes à 2 endroits éloignés.
    """
    try:
        # On récupère l'historique des validations de ce ticket, trié chronologiquement
        logs = list(ValidationLog.objects.filter(ticket_id=ticket_id).order_by('scanned_at'))
        
        if len(logs) < 2:
            return "NO_FRAUD" # Pas de double validation, pas de risque
            
        for i in range(len(logs) - 1):
            log_a = logs[i]
            log_b = logs[i+1]
            
            # Delta de Temps
            time_diff_seconds = (log_b.scanned_at - log_a.scanned_at).total_seconds()
            
            # PostGIS: Calcul de la distance géospatiale exacte entre les 2 scans
            # (Utilisation des méthodes natives GEOS)
            distance_meters = log_a.scan_location.distance(log_b.scan_location) * 111000 # Approximation simple des degrés vers Mètres pour SRID 4326
            
            # ==============================================================
            # RÈGLE MÉTIER ANTI-FRAUDE STRICTE (Zero Trust)
            # Si le ticket a été validé avec une distance > 2 kilomètres
            # dans un intervalle de temps < 5 minutes (Impossible physiquement)
            # ==============================================================
            if distance_meters > 2000 and time_diff_seconds < 300:
                logger.critical(f"🚨 FRAUD DETECTED: Ticket {ticket_id} (Replay Attack). Dist: {distance_meters}m in {time_diff_seconds}s.")
                
                # 1. Neutraliser le Ticket
                Ticket.objects.filter(id=ticket_id).update(status='FRAUDULENT')
                
                # 2. Suspendre le Passager de façon préventive
                ticket = Ticket.objects.select_related('passenger').get(id=ticket_id)
                ticket.passenger.is_active = False
                ticket.passenger.save()
                
                # 3. Générer une alerte Admin
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO fraud_alerts (passenger_id, ticket_id, reason) VALUES (%s, %s, %s)",
                        [str(ticket.passenger.id), ticket_id, "Impossible Replay Attack Detected"]
                    )
                
                # 4. Trigger un push FCM au passager "Compte Bloqué"
                # push_notification.delay(ticket.passenger.fcm_token, "Alerte de Sécurité", "Votre compte est suspendu.")
                
                return "FRAUD_DETECTED_AND_ISOLATED"
                
        return "NO_FRAUD"
        
    except Exception as exc:
        logger.error(f"Erreur dans le Fraud Engine pour le ticket {ticket_id}: {exc}")
        self.retry(exc=exc, countdown=60) # Exponential backoff automatique
