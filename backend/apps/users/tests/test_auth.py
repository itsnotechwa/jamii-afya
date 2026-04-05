from django.contrib.auth.hashers import identify_hasher
from django.core.cache import cache
from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.users.models import OTPCode, User


@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    AUTH_LOGIN_MAX_ATTEMPTS=3,
    AUTH_LOGIN_LOCKOUT_SECONDS=60,
)
class LoginAndOtpTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='+254712000001',
            phone_number='+254712000001',
            email='a@example.com',
            password='testpass12',
        )

    def test_login_returns_token(self):
        r = self.client.post(
            '/api/auth/login/',
            {'identifier': '+254712000001', 'password': 'testpass12'},
            format='json',
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn('token', r.data)
        self.assertIn('refresh', r.data)

    def test_login_lockout_after_failures(self):
        for _ in range(3):
            self.client.post(
                '/api/auth/login/',
                {'identifier': '+254712000001', 'password': 'wrong'},
                format='json',
            )
        r = self.client.post(
            '/api/auth/login/',
            {'identifier': '+254712000001', 'password': 'testpass12'},
            format='json',
        )
        self.assertEqual(r.status_code, 400)

    @patch('utils.sms.send_sms')
    def test_otp_stored_hashed(self, _mock_sms):
        self.client.force_authenticate(user=self.user)
        r = self.client.post('/api/auth/verify/send/', {}, format='json')
        self.assertEqual(r.status_code, 200)
        otp = OTPCode.objects.get(user=self.user)
        self.assertNotEqual(len(otp.code), 6)
        identify_hasher(otp.code)
