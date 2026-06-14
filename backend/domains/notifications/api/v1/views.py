from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from domains.notifications.models import Notification
from .serializers import NotificationSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='broadcast')
    def broadcast(self, request):
        title = request.data.get('title')
        message = request.data.get('message')
        
        if not title or not message:
            return Response({"error": "Title and message are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # In a real app, this would also trigger FCM/Push notifications
        notification = Notification.objects.create(
            title=title,
            message=message,
            user=None # None means broadcast to all
        )
        
        return Response(NotificationSerializer(notification).data, status=status.HTTP_201_CREATED)
