from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.contributions.models import Contribution
from apps.groups.models import Group, GroupMember
from apps.mpesa.models import MpesaTransaction
from apps.users.models import User


class ContributionSummaryTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.member = User.objects.create_user(
            username='+254712000010',
            phone_number='+254712000010',
            email='m@example.com',
            password='testpass12',
        )
        self.other = User.objects.create_user(
            username='+254712000011',
            phone_number='+254712000011',
            email='o@example.com',
            password='testpass12',
        )
        self.owner = User.objects.create_user(
            username='+254712000012',
            phone_number='+254712000012',
            email='ow@example.com',
            password='testpass12',
        )
        self.group = Group.objects.create(
            name='G1',
            created_by=self.owner,
            invite_code='TESTINV1',
            approval_threshold=1,
            min_contributions_to_qualify=0,
        )
        GroupMember.objects.create(group=self.group, user=self.member, role='member')
        Contribution.objects.create(
            group=self.group,
            member=self.member,
            amount=Decimal('100.00'),
            status='confirmed',
            period='2026-04',
        )

    def test_summary_403_non_member(self):
        self.client.force_authenticate(user=self.other)
        r = self.client.get('/api/contributions/summary/', {'group_id': self.group.id})
        self.assertEqual(r.status_code, 403)

    def test_summary_ok_member(self):
        self.client.force_authenticate(user=self.member)
        r = self.client.get('/api/contributions/summary/', {'group_id': self.group.id})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['count'], 1)


@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
)
class RecheckUpstreamErrorTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='+254712000020',
            phone_number='+254712000020',
            email='r@example.com',
            password='testpass12',
        )
        self.group = Group.objects.create(
            name='G2',
            created_by=self.user,
            invite_code='TESTINV2',
            approval_threshold=1,
            min_contributions_to_qualify=0,
        )
        GroupMember.objects.create(group=self.group, user=self.user, role='admin')
        self.contrib = Contribution.objects.create(
            group=self.group,
            member=self.user,
            amount=Decimal('50.00'),
            status='pending',
            period='2026-05',
        )
        self.tx = MpesaTransaction.objects.create(
            user=self.user,
            tx_type='stk_push',
            status='initiated',
            phone='254712000020',
            amount=Decimal('50.00'),
            checkout_request_id='ws_cov_ck_1',
            reference_id=self.contrib.id,
        )

    @patch(
        'apps.mpesa.services.MpesaService.stk_query',
        side_effect=RuntimeError('upstream down'),
    )
    def test_recheck_no_exception_detail_to_client(self, _mock):
        self.client.force_authenticate(user=self.user)
        r = self.client.post(
            '/api/contributions/recheck/',
            {'checkout_request_id': 'ws_cov_ck_1'},
            format='json',
        )
        self.assertEqual(r.status_code, 502)
        self.assertNotIn('upstream', r.data.get('detail', ''))
