import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('Le numéro de téléphone est obligatoire.')
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('role', 'SUPER_ADMIN')
        return self.create_user(phone_number, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('PASSENGER', 'Passenger'),
        ('DRIVER', 'Driver'),
        ('CONTROLLER', 'Controller'),
        ('ADMIN', 'Admin')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='PASSENGER')
    is_active = models.BooleanField(default=True)
    fcm_token = models.CharField(max_length=255, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['role']

    class Meta:
        db_table = 'users'
        # DÉCISION CTO: L'ORM Django ne doit JAMAIS altérer notre schéma DBA strict.
        # Les partitions et triggers sont gérés via le DDL SQL.
        # managed = False 

    def __str__(self):
        return f"{self.phone_number} ({self.role})"
