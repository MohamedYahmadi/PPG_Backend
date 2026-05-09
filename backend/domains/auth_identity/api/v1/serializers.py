from rest_framework import serializers

class LoginRequestSerializer(serializers.Serializer):
    """
    DTO (Data Transfer Object) strict pour valider l'input.
    """
    phone_number = serializers.CharField(max_length=20, required=True)
    password = serializers.CharField(write_only=True, required=True)
    device_id = serializers.CharField(max_length=100, required=True, help_text="Identifiant unique du téléphone (Fingerprint)")

class SignupRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20, required=True)
    password = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(choices=['PASSENGER', 'DRIVER'], default='PASSENGER')

class LogoutRequestSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)

from domains.auth_identity.models import User

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'phone_number', 'role', 'is_active', 'password', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        password = validated_data.pop('password', 'defaultpassword123') # fallback password
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
