from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from utils.request import get_client_ip

from .auth_limits import (
    assert_login_allowed,
    clear_login_failures,
    record_login_failure,
)
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'phone_number',
                  'national_id', 'email', 'password', 'password2']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.username = str(validated_data['phone_number'])
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """
    Accept login via phone_number OR email, per the PDF spec.
    Tries phone first; falls back to email lookup if the identifier contains '@'.
    """
    identifier = serializers.CharField(
        help_text='Phone number (+254...) or email address'
    )
    password   = serializers.CharField(write_only=True)

    def validate(self, data):
        identifier = data['identifier'].strip()
        password   = data['password']
        request = self.context.get('request')
        ip = get_client_ip(request) if request else ''

        assert_login_allowed(identifier, ip)

        user = None

        if '@' in identifier:
            # Email path: look up user by email then authenticate by phone (USERNAME_FIELD)
            try:
                u = User.objects.get(email__iexact=identifier)
                user = authenticate(username=str(u.phone_number), password=password)
            except User.DoesNotExist:
                pass
        else:
            # Phone path
            user = authenticate(username=identifier, password=password)

        if not user:
            record_login_failure(identifier, ip)
            raise serializers.ValidationError("Invalid credentials.")

        clear_login_failures(identifier, ip)

        tokens = RefreshToken.for_user(user)
        return {
            'user':    UserProfileSerializer(user).data,
            'access':  str(tokens.access_token),
            'refresh': str(tokens),
        }


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'first_name', 'last_name', 'phone_number',
                  'national_id', 'email', 'is_verified', 'profile_pic', 'is_staff']
        read_only_fields = ['is_verified', 'is_staff', 'phone_number']
        extra_kwargs = {'national_id': {'allow_null': True, 'required': False}}
