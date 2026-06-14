import os
import sys
import django
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from domains.auth_identity.models import User

print("--- USERS IN DB ---")
for u in User.objects.all():
    print(f"Phone: {u.phone_number} | Role: {u.role} | Active: {u.is_active}")
