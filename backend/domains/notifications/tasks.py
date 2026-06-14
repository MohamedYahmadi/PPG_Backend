import logging
from celery import shared_task
from django.core.cache import cache

logger = logging.getLogger(__name__)


@shared_task(queue='push_notifications', bind=True, max_retries=3)
def send_push_notification(self, notification_id, fcm_token, title, body, data=None):
    try:
        cache_key = f"push_sent_{notification_id}"
        if cache.get(cache_key):
            return "ALREADY_SENT"

        logger.info(f"PUSH NOTIFICATION [{notification_id}] to {fcm_token[:20]}...: {title}")

        from firebase_admin import messaging, initialize_app, get_app
        try:
            get_app()
        except ValueError:
            initialize_app()

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            token=fcm_token,
        )
        response = messaging.send(message, app=get_app())
        logger.info(f"FCM sent: {response}")

        cache.set(cache_key, True, timeout=3600)
        return f"SENT_{response}"

    except Exception as exc:
        logger.error(f"FCM failed for notification {notification_id}: {exc}")
        self.retry(exc=exc, countdown=60)


@shared_task(queue='push_notifications')
def cleanup_expired_notifications():
    from django.utils import timezone
    from datetime import timedelta
    from .models import Notification

    cutoff = timezone.now() - timedelta(days=90)
    deleted, _ = Notification.objects.filter(created_at__lt=cutoff, is_read=True).delete()
    return f"Cleaned up {deleted} old notifications"
