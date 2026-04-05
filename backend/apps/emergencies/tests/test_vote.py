from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from apps.emergencies.models import EmergencyRequest
from apps.groups.models import Group, GroupMember
from apps.users.models import User


class EmergencyVotePayoutTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username='+254712000040',
            phone_number='+254712000040',
            email='adm2@example.com',
            password='testpass12',
        )
        self.claimant = User.objects.create_user(
            username='+254712000041',
            phone_number='+254712000041',
            email='cl@example.com',
            password='testpass12',
        )
        self.group = Group.objects.create(
            name='Gvote',
            created_by=self.admin,
            invite_code='VOTEINV01',
            approval_threshold=1,
            min_contributions_to_qualify=0,
            max_payout_amount=Decimal('100000.00'),
        )
        GroupMember.objects.create(group=self.group, user=self.admin, role='admin')
        GroupMember.objects.create(group=self.group, user=self.claimant, role='member')

    @patch('apps.mpesa.tasks.disburse_emergency_payout.delay')
    @patch('apps.notifications.tasks.notify_vote_cast.delay')
    @patch('apps.notifications.tasks.notify_emergency_approved.delay')
    @patch('apps.notifications.tasks.notify_admins_new_emergency.delay')
    def test_vote_approve_triggers_payout_task(
        self,
        _mock_admins,
        _mock_approved,
        _mock_vote,
        mock_payout,
    ):
        self.client.force_authenticate(user=self.claimant)
        cr = self.client.post(
            '/api/emergencies/',
            {
                'group': self.group.id,
                'emergency_type': 'other',
                'description': 'Need help',
                'amount_requested': '10000.00',
                'payout_phone': '254712000041',
            },
            format='json',
        )
        self.assertEqual(cr.status_code, 201)
        em_id = cr.data['id']

        self.client.force_authenticate(user=self.admin)
        vr = self.client.post(
            f'/api/emergencies/{em_id}/vote/',
            {'decision': 'approve'},
            format='json',
        )
        self.assertEqual(vr.status_code, 200)
        em = EmergencyRequest.objects.get(id=em_id)
        self.assertEqual(em.status, 'approved')
        mock_payout.assert_called_once_with(em_id)
