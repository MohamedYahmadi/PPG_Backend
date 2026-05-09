from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LoginAPIView, LogoutAPIView, UserViewSet, SignupAPIView

router = DefaultRouter()
router.register(r'admin/users', UserViewSet, basename='admin-users')

urlpatterns = [
    path('register/', SignupAPIView.as_view(), name='api_auth_register'),
    path('login/', LoginAPIView.as_view(), name='api_auth_login'),
    path('logout/', LogoutAPIView.as_view(), name='api_auth_logout'),
    # L'Endpoint natif de SimpleJWT pour rafraichir le token d'accès sans mot de passe
    path('token/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('', include(router.urls)),
]
