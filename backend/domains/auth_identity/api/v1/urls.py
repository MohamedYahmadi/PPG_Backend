from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginAPIView, LogoutAPIView, UserViewSet, SignupAPIView,
    PasswordResetRequestAPIView, PasswordResetConfirmAPIView,
    ProfileAPIView
)

router = DefaultRouter()
router.register(r'admin/users', UserViewSet, basename='admin-users')

urlpatterns = [
    path('register/', SignupAPIView.as_view(), name='api_auth_register'),
    path('login/', LoginAPIView.as_view(), name='api_auth_login'),
    path('logout/', LogoutAPIView.as_view(), name='api_auth_logout'),
    path('password-reset/request/', PasswordResetRequestAPIView.as_view(), name='api_password_reset_request'),
    path('password-reset/confirm/', PasswordResetConfirmAPIView.as_view(), name='api_password_reset_confirm'),
    path('me/', ProfileAPIView.as_view(), name='api_auth_profile'),
    path('token/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('', include(router.urls)),
]
