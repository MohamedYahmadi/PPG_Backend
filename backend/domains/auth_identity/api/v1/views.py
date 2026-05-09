from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import LoginRequestSerializer, LogoutRequestSerializer, SignupRequestSerializer
from domains.auth_identity.services import AuthService

class SignupAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = AuthService.register_user(
                phone_number=serializer.validated_data['phone_number'],
                password=serializer.validated_data['password'],
                role=serializer.validated_data.get('role', 'PASSENGER')
            )
            return Response({"message": "Utilisateur créé avec succès", "user_id": str(user.id)}, status=201)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

class LoginAPIView(APIView):
    """
    DÉCISION CTO : Cette vue REST respecte le pattern "Fat Services / Thin Views".
    Elle ne fait que: Parser l'input -> Appeler la Service Layer -> Retourner la réponse.
    Aucune logique métier ni de requête ORM ici.
    """
    authentication_classes = []
    permission_classes = [AllowAny] # Limité par RateLimitMiddleware
    
    def post(self, request):
        # 1. Validation de la payload via DTO/Serializer
        serializer = LoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        ip_address = request.META.get('REMOTE_ADDR', '0.0.0.0')
        
        # 2. Délégation stricte au Service Layer
        tokens = AuthService.authenticate_user(
            phone_number=data['phone_number'],
            password=data['password'],
            device_id=data['device_id'],
            ip_address=ip_address
        )
        
        # 3. Réponse standardisée
        return Response(tokens, status=200)

class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = LogoutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Invalidation immédiate du token (Redis Blacklist)
        AuthService.blacklist_token(serializer.validated_data['refresh_token'])
        
        return Response({"message": "Déconnexion réussie. Token révoqué."}, status=200)

from rest_framework import viewsets
from domains.auth_identity.models import User
from .serializers import UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated] # + IsAdmin later if needed
