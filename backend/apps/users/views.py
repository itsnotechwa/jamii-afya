from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, inline_serializer
from drf_spectacular.openapi import AutoSchema
import rest_framework.fields as f


from .serializers import RegisterSerializer, LoginSerializer, UserProfileSerializer

import random

from django.utils import timezone
from datetime import timedelta

from .models import User, OTPCode


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh['role'] = 'admin' if user.is_staff else 'member'
    refresh['id'] = user.id
    return {
        'token': str(refresh.access_token),
        'refresh': str(refresh),
        'role': 'admin' if user.is_staff else 'member',
        'id': user.id,
    }


@extend_schema(tags=['Auth'])
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {'message': 'Account created. Verify your phone to continue.'},
            status=status.HTTP_201_CREATED
        )


@extend_schema(
    tags=['Auth'],
    request=LoginSerializer,
    responses={200: {'type': 'object', 'properties': {
        'token':   {'type': 'string'},
        'refresh': {'type': 'string'},
        'role':    {'type': 'string'},
        'id':      {'type': 'integer'},
    }}},
    description='Login with phone number or email + password. Returns JWT access & refresh tokens.',
)
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


@extend_schema(tags=['Auth'])
class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class   = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(
    tags=['Auth'],
    request=inline_serializer('SendOTPRequest', fields={}),
    responses={200: inline_serializer('OTPSentResponse', fields={'detail': f.CharField()})},
    description='Send a 6-digit OTP to the authenticated user\'s registered phone number.',
)
class SendOTPView(APIView):
    """
    Send a 6-digit OTP to the authenticated user's phone number.
    Invalidates any unused OTPs issued in the last 5 minutes before creating a new one.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.is_verified:
            return Response({'detail': 'Phone number already verified.'}, status=status.HTTP_400_BAD_REQUEST)

        # Expire any unused codes older than 5 minutes (mark used so they can't be replayed)
        cutoff = timezone.now() - timedelta(minutes=5)
        OTPCode.objects.filter(user=user, is_used=False, created_at__lt=cutoff).update(is_used=True)

        # Rate-limit: at most one active OTP per 60 seconds
        recent_cutoff = timezone.now() - timedelta(seconds=60)
        if OTPCode.objects.filter(user=user, is_used=False, created_at__gte=recent_cutoff).exists():
            return Response(
                {'detail': 'An OTP was already sent recently. Please wait before requesting again.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        code = f"{random.randint(100000, 999999)}"
        OTPCode.objects.create(user=user, code=code)

        from utils.sms import send_sms
        message = f"[JamiiFund] Your verification code is {code}. It expires in 5 minutes."
        send_sms(phone=str(user.phone_number), message=message)

        return Response({'detail': 'OTP sent to your registered phone number.'}, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Auth'],
    request=inline_serializer('VerifyOTPRequest', fields={'code': f.CharField(max_length=6)}),
    responses={200: inline_serializer('OTPVerifiedResponse', fields={'detail': f.CharField()})},
    description='Verify the 6-digit OTP. Marks the user phone as verified on success.',
)
class VerifyOTPView(APIView):
    """
    Confirm the OTP and mark the user's phone as verified.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        code = request.data.get('code', '').strip()

        if not code:
            return Response({'detail': 'OTP code is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if user.is_verified:
            return Response({'detail': 'Phone number already verified.'}, status=status.HTTP_400_BAD_REQUEST)

        # Valid window: issued within the last 5 minutes and not yet used
        cutoff = timezone.now() - timedelta(minutes=5)
        otp = OTPCode.objects.filter(
            user=user,
            code=code,
            is_used=False,
            created_at__gte=cutoff,
        ).order_by('-created_at').first()

        if not otp:
            return Response({'detail': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        otp.is_used = True
        otp.save(update_fields=['is_used'])

        user.is_verified = True
        user.save(update_fields=['is_verified'])

        return Response({'detail': 'Phone number verified successfully.'}, status=status.HTTP_200_OK)

