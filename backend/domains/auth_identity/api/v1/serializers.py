from rest_framework import serializers
from domains.auth_identity.models import User


class LoginRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20, required=True)
    password = serializers.CharField(write_only=True, required=True)
    device_id = serializers.CharField(max_length=100, required=True, help_text="Identifiant unique du téléphone (Fingerprint)")


class SignupRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20, required=True)
    password = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(choices=['PASSENGER', 'DRIVER', 'CONTROLLER'], default='PASSENGER')
    email = serializers.EmailField(max_length=254, required=False, allow_null=True)
    full_name = serializers.CharField(max_length=150, required=False, allow_null=True)


class LogoutRequestSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20, required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)


class ProfileUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150, required=False)
    email = serializers.EmailField(max_length=254, required=False)
    avatar_url = serializers.CharField(max_length=500, required=False)
    preferences = serializers.JSONField(required=False)
    language = serializers.ChoiceField(choices=['fr', 'en', 'ar'], required=False)


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'phone_number', 'email', 'full_name', 'avatar_url',
            'role', 'is_active', 'password', 'preferences', 'language', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        password = validated_data.pop('password', 'defaultpassword123')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
