from decimal import Decimal
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.contributions.models import Contribution
from apps.emergencies.models import EmergencyRequest
from apps.groups.models import Group, GroupMember
from apps.mpesa.models import MpesaTransaction
from apps.users.models import User


@override_settings(
    DEBUG=True,
    MPESA_WEBHOOK_SECRET='hooksecret',
    MPESA_CALLBACK_ALLOWED_IPS=[],
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
)
class MpesaWebhookTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='+254712000030',
            phone_number='+254712000030',
            email='mp@example.com',
            password='testpass12',
        )
        self.group = Group.objects.create(
            name='Gm',
            created_by=self.user,
            invite_code='INVMPESA',
            approval_threshold=1,
            min_contributions_to_qualify=0,
        )
        GroupMember.objects.create(group=self.group, user=self.user, role='member')
        self.contrib = Contribution.objects.create(
            group=self.group,
            member=self.user,
            amount=Decimal('100.00'),
            status='pending',
            period='2026-06',
        )
        self.tx = MpesaTransaction.objects.create(
            user=self.user,
            tx_type='stk_push',
            status='initiated',
            phone='254712000030',
            amount=Decimal('100.00'),
            checkout_request_id='cb_ck_1',
            reference_id=self.contrib.id,
        )

    def test_stk_callback_rejects_without_secret(self):
        payload = {
            'Body': {
                'stkCallback': {
                    'CheckoutRequestID': 'cb_ck_1',
                    'ResultCode': 0,
                    'ResultDesc': 'The service request is processed successfully.',
                    'CallbackMetadata': {
                        'Item': [
                            {'Name': 'MpesaReceiptNumber', 'Value': 'R123'},
                            {'Name': 'TransactionID', 'Value': 'T999'},
                        ]
                    },
                }
            }
        }
        r = self.client.post('/api/mpesa/callback/', payload, format='json')
        self.assertEqual(r.status_code, 401)

    @patch('apps.notifications.tasks.notify_contribution_confirmed.delay')
    def test_stk_callback_confirms_contribution(self, _mock_notify):
        payload = {
            'Body': {
                'stkCallback': {
                    'CheckoutRequestID': 'cb_ck_1',
                    'ResultCode': 0,
                    'ResultDesc': 'The service request is processed successfully.',
                    'CallbackMetadata': {
                        'Item': [
                            {'Name': 'MpesaReceiptNumber', 'Value': 'R124'},
                            {'Name': 'TransactionID', 'Value': 'T1000'},
                        ]
                    },
                }
            }
        }
        r = self.client.post(
            '/api/mpesa/callback/?token=hooksecret',
            payload,
            format='json',
        )
        self.assertEqual(r.status_code, 200)
        self.contrib.refresh_from_db()
        self.assertEqual(self.contrib.status, 'confirmed')

    @patch('apps.notifications.tasks.notify_payout_result.delay')
    def test_b2c_result_marks_emergency_paid(self, mock_notify):
        admin = User.objects.create_user(
            username='+254712000031',
            phone_number='+254712000031',
            email='adm@example.com',
            password='testpass12',
        )
        GroupMember.objects.create(group=self.group, user=admin, role='admin')
        em = EmergencyRequest.objects.create(
            group=self.group,
            claimant=self.user,
            emergency_type='other',
            description='test',
            amount_requested=Decimal('5000.00'),
            payout_phone='254712000030',
            status='approved',
            amount_approved=Decimal('5000.00'),
        )
        b2c_tx = MpesaTransaction.objects.create(
            user=self.user,
            tx_type='b2c',
            status='initiated',
            phone='254712000030',
            amount=Decimal('5000.00'),
            checkout_request_id='conv-b2c-1',
            reference_id=em.id,
        )
        payload = {
            'Result': {
                'ConversationID': 'conv-b2c-1',
                'ResultCode': 0,
                'ResultDesc': 'Completed',
                'ResultParameters': {
                    'ResultParameter': [
                        {'Key': 'TransactionReceipt', 'Value': 'RZZ1'},
                    ]
                },
            }
        }
        r = self.client.post(
            '/api/mpesa/b2c/result/?token=hooksecret',
            payload,
            format='json',
        )
        self.assertEqual(r.status_code, 200)
        em.refresh_from_db()
        self.assertEqual(em.status, 'paid')
        mock_notify.assert_called_once()
