import random
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
import rest_framework.fields as f
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .auth_limits import (
    assert_otp_verify_allowed,
    clear_otp_verify_failures,
    record_otp_verify_failure,
)
from .models import OTPCode, User
from .serializers import LoginSerializer, RegisterSerializer, UserProfileSerializer


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
        'access':  {'type': 'string'},
        'refresh': {'type': 'string'},
        'user':    {'type': 'object'},
    }}},
    description='Login with phone number or email + password. Returns JWT access & refresh tokens.',
)
class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        return Response(
            {
                'token': data['access'],
                'access': data['access'],
                'refresh': data['refresh'],
                'user': data['user'],
            },
            status=status.HTTP_200_OK,
        )


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
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'otp_send'

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

        # One active OTP per user: avoids multi-row verify loops (timing) and ambiguous validity.
        OTPCode.objects.filter(user=user, is_used=False).update(is_used=True)

        code = f"{random.randint(100000, 999999)}"
        OTPCode.objects.create(user=user, code=make_password(code))

        from utils.sms import send_sms
        message = f"[Jamii Afya] Your verification code is {code}. It expires in 5 minutes."
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
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'otp_verify'

    def post(self, request):
        user = request.user
        code = request.data.get('code', '').strip()

        if not code:
            return Response({'detail': 'OTP code is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if user.is_verified:
            return Response({'detail': 'Phone number already verified.'}, status=status.HTTP_400_BAD_REQUEST)

        assert_otp_verify_allowed(user.id, request)

        # Valid window: issued within the last 5 minutes and not yet used
        cutoff = timezone.now() - timedelta(minutes=5)
        otp_row = (
            OTPCode.objects.filter(
                user=user,
                is_used=False,
                created_at__gte=cutoff,
            )
            .order_by('-created_at')
            .first()
        )
        otp = otp_row if otp_row and check_password(code, otp_row.code) else None

        if not otp:
            record_otp_verify_failure(user.id, request)
            return Response({'detail': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        clear_otp_verify_failures(user.id, request)

        otp.is_used = True
        otp.save(update_fields=['is_used'])

        user.is_verified = True
        user.save(update_fields=['is_verified'])

        return Response({'detail': 'Phone number verified successfully.'}, status=status.HTTP_200_OK)

