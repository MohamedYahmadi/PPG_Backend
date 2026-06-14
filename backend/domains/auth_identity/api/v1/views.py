from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import viewsets, status
from django.shortcuts import get_object_or_404
from .serializers import (
    LoginRequestSerializer, LogoutRequestSerializer, SignupRequestSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    ProfileUpdateSerializer, UserSerializer
)
from domains.auth_identity.models import User
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
                role=serializer.validated_data.get('role', 'PASSENGER'),
                email=serializer.validated_data.get('email'),
                full_name=serializer.validated_data.get('full_name')
            )
            return Response({
                "message": "Utilisateur créé avec succès",
                "user_id": str(user.id)
            }, status=201)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)


class LoginAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        ip_address = request.META.get('REMOTE_ADDR', '0.0.0.0')

        tokens = AuthService.authenticate_user(
            phone_number=data['phone_number'],
            password=data['password'],
            device_id=data['device_id'],
            ip_address=ip_address
        )

        return Response(tokens, status=200)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        AuthService.blacklist_token(serializer.validated_data['refresh_token'])

        return Response({"message": "Déconnexion réussie. Token révoqué."}, status=200)


class PasswordResetRequestAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = AuthService.request_password_reset(
            serializer.validated_data['phone_number']
        )
        return Response(result)


class PasswordResetConfirmAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            AuthService.confirm_password_reset(
                token=serializer.validated_data['token'],
                new_password=serializer.validated_data['new_password']
            )
            return Response({"message": "Mot de passe réinitialisé avec succès."})
        except ValueError as e:
            return Response({"error": str(e)}, status=400)


class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = AuthService.update_profile(request.user, serializer.validated_data)
        return Response(UserSerializer(user).data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
