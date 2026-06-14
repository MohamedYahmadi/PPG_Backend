import logging
import hashlib
import secrets
from datetime import timedelta
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from .models import User, PasswordResetToken

logger = logging.getLogger(__name__)


class AuthService:
    """
    Logique Métier (Service Layer) pour l'Authentification.
    Zero Trust: Toute tentative est journalisée. La logique est isolée de views.py.
    """
    
    @staticmethod
    def register_user(phone_number: str, password: str, role: str = 'PASSENGER',
                      email: str = None, full_name: str = None) -> User:
        if User.objects.filter(phone_number=phone_number).exists():
            raise ValueError("Un utilisateur avec ce numéro de téléphone existe déjà.")
        if email and User.objects.filter(email=email).exists():
            raise ValueError("Un utilisateur avec cet email existe déjà.")

        user = User.objects.create_user(
            phone_number=phone_number,
            password=password,
            role=role,
            email=email,
            full_name=full_name
        )
        logger.info(f"SUCCESS: New user registered: {phone_number} as {role}")
        return user

    @staticmethod
    def authenticate_user(phone_number: str, password: str, device_id: str, ip_address: str) -> dict:
        user = authenticate(phone_number=phone_number, password=password)
        
        if not user:
            logger.warning(f"SECURITY ALERT: Failed login attempt for {phone_number} from IP {ip_address}")
            raise AuthenticationFailed("Identifiants incorrects ou compte suspendu.")
            
        if not user.is_active:
            logger.warning(f"SECURITY ALERT: Login attempt on suspended account {user.id}")
            raise AuthenticationFailed("Ce compte a été suspendu pour fraude.")
            
        refresh = RefreshToken.for_user(user)
        refresh['device_id'] = device_id
        
        logger.info(f"SUCCESS: User {user.id} logged in from device {device_id}")
        
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'role': user.role,
            'user_id': str(user.id)
        }

    @staticmethod
    def blacklist_token(refresh_token: str) -> None:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception as e:
            logger.error(f"Failed to blacklist token: {str(e)}")
            raise ValueError("Token invalide ou déjà expiré.")

    @staticmethod
    def request_password_reset(phone_number: str) -> dict:
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return {"message": "Si ce numéro est associé à un compte, un SMS a été envoyé."}

        import hashlib
        import secrets
        raw_token = secrets.token_hex(32)
        hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()

        PasswordResetToken.objects.create(
            user=user,
            token=hashed_token,
            expires_at=timezone.now() + timedelta(hours=1)
        )

        logger.info(f"PASSWORD RESET: Token generated for user {user.id}")
        return {
            "message": "Si ce numéro est associé à un compte, un code de réinitialisation a été envoyé.",
            "reset_token": raw_token
        }

    @staticmethod
    def confirm_password_reset(token: str, new_password: str) -> None:
        import hashlib
        hashed_token = hashlib.sha256(token.encode()).hexdigest()
        
        try:
            reset_token = PasswordResetToken.objects.get(token=hashed_token, is_used=False)
        except PasswordResetToken.DoesNotExist:
            raise ValueError("Token invalide ou déjà utilisé.")

        if not reset_token.is_valid():
            reset_token.is_used = True
            reset_token.save()
            raise ValueError("Le token a expiré. Veuillez refaire une demande.")

        user = reset_token.user
        user.set_password(new_password)
        user.save()

        reset_token.is_used = True
        reset_token.save()

        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
        outstanding = OutstandingToken.objects.filter(user=user)
        for token in outstanding:
            BlacklistedToken.objects.get_or_create(token=token)

        logger.info(f"PASSWORD RESET: Password changed for user {user.id}")

    @staticmethod
    def update_profile(user, data: dict) -> User:
        allowed_fields = ['full_name', 'email', 'avatar_url', 'preferences', 'language']
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        user.save()
        return user
