import logging
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from .models import Notification, NotificationTemplate, IncidentReport

logger = logging.getLogger(__name__)


class NotificationService:

    @staticmethod
    def send_notification(recipient, notification_type, title, body, data=None):
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            body=body,
            data=data or {}
        )
        if recipient.fcm_token:
            from .tasks import send_push_notification
            send_push_notification.delay(
                str(notification.id),
                recipient.fcm_token,
                title,
                body,
                data
            )
            notification.sent_via_push = True
            notification.save(update_fields=['sent_via_push'])

        return notification

    @staticmethod
    def send_broadcast(notification_type, title, body, data=None):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        notifications = []
        recipients = User.objects.filter(is_active=True)

        for user in recipients:
            notifications.append(Notification(
                recipient=user,
                notification_type=notification_type,
                title=title,
                body=body,
                data=data or {},
                sent_via_push=bool(user.fcm_token)
            ))

        Notification.objects.bulk_create(notifications)

        fcm_recipients = recipients.exclude(fcm_token__isnull=True).exclude(fcm_token__exact='')
        for user in fcm_recipients:
            notification = Notification.objects.filter(recipient=user, title=title, body=body).first()
            if notification:
                from .tasks import send_push_notification
                send_push_notification.delay(
                    str(notification.id),
                    user.fcm_token,
                    title,
                    body,
                    data
                )

        return len(notifications)

    @staticmethod
    def notify_delay(trip, delay_minutes):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        passengers = User.objects.filter(
            role='PASSENGER',
            is_active=True
        ).select_related('wallet')

        title = f"Retard signalé - {trip.route.name}"
        body = f"Le trajet {trip.route.name} a {delay_minutes} minutes de retard."

        count = 0
        for passenger in passengers:
            try:
                NotificationService.send_notification(
                    passenger, 'DELAY', title, body,
                    {'trip_id': str(trip.id), 'delay_minutes': delay_minutes}
                )
                count += 1
            except Exception as e:
                logger.error(f"Failed to notify passenger {passenger.id}: {e}")

        return count

    @staticmethod
    def notify_ticket_expiring(ticket):
        title = "Votre ticket expire bientôt"
        body = f"Votre ticket ({ticket.zone_validity}) expire dans 15 minutes."
        NotificationService.send_notification(
            ticket.passenger, 'TICKET_EXPIRING', title, body,
            {'ticket_id': str(ticket.id)}
        )

    @staticmethod
    def report_incident(reporter, incident_type, severity, description, **kwargs):
        report = IncidentReport.objects.create(
            reporter=reporter,
            incident_type=incident_type,
            severity=severity,
            description=description,
            **kwargs
        )

        from django.contrib.auth import get_user_model
        User = get_user_model()
        admins = User.objects.filter(role__in=['ADMIN', 'SUPER_ADMIN'], is_active=True)
        for admin in admins:
            NotificationService.send_notification(
                admin, 'INCIDENT',
                f"Incident: {incident_type}",
                f"{severity} - {description[:100]}",
                {'incident_id': str(report.id)}
            )

        return report

    @staticmethod
    def resolve_incident(incident_id, admin_user):
        report = IncidentReport.objects.get(id=incident_id)
        report.is_resolved = True
        report.resolved_at = timezone.now()
        report.save()
        NotificationService.send_notification(
            report.reporter, 'INCIDENT',
            "Incident résolu",
            f"Votre incident ({report.incident_type}) a été marqué comme résolu."
        )
        return report
