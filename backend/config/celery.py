import os
from celery import Celery

# Définir le module de configuration par défaut de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')

app = Celery('sitp_backend')

# Utilise un namespace 'CELERY' dans le fichier settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découvre automatiquement les tâches dans tous les apps installés
app.autodiscover_tasks()

# Configuration du routing Celery pour l'Enterprise
# Les tâches urgentes ou lourdes sont routées vers des queues spécifiques.
app.conf.task_routes = {
    'domains.wallet_payments.tasks.*': {'queue': 'critical_payments'},
    'domains.transit_tracking.tasks.*': {'queue': 'gps_processing'},
    'domains.ticketing_validation.tasks.fraud_detection_engine': {'queue': 'fraud_analysis'},
    'domains.notifications.tasks.*': {'queue': 'push_notifications'},
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
