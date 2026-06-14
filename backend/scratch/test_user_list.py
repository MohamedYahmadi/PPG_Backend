import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from domains.auth_identity.models import User
from domains.auth_identity.api.v1.serializers import UserSerializer

try:
    users = User.objects.all().order_by('-created_at')
    serializer = UserSerializer(users, many=True)
    print(f"Successfully serialized {len(users)} users.")
except Exception as e:
    print(f"Error: {e}")
