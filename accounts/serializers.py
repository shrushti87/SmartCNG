"""
Serializers for user registration and authentication.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'phone',
                  'vehicle_number', 'vehicle_type', 'first_name', 'last_name')

    def validate_vehicle_number(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Vehicle number is required.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile display and updates."""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'phone', 'vehicle_number', 'vehicle_type', 'date_joined', 'is_staff', 'is_superuser')
        read_only_fields = ('id', 'username', 'date_joined', 'is_staff', 'is_superuser')

    def validate_vehicle_number(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Vehicle number is required.")
        return value


class LoginSerializer(serializers.Serializer):
    """Serializer for login input validation."""
    username = serializers.CharField()
    password = serializers.CharField()
