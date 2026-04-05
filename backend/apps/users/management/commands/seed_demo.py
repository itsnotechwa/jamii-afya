"""
Load deterministic demo users, group, sample contribution, emergency, and hospital.

Safe to run multiple times (idempotent). Does not affect automated tests (they use a separate DB).

Matches README demo phones: admin +254700000000, member +254712345678; password 123456.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.contributions.models import Contribution
from apps.emergencies.models import EmergencyRequest, Hospital
from apps.groups.models import Group, GroupMember
from apps.users.models import User

DEMO_ADMIN_PHONE = '+254700000000'
DEMO_MEMBER_PHONE = '+254712345678'
DEMO_PASSWORD = '123456'
DEMO_GROUP_INVITE = 'JAMIIDEMO01'
DEMO_GROUP_NAME = 'Jamii Demo Chama'


class Command(BaseCommand):
    help = (
        'Create demo admin & member users, a group, memberships, sample contribution & emergency, '
        'and one hospital. Idempotent.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-passwords',
            action='store_true',
            help='Reset demo users’ passwords to 123456 (if they already exist).',
        )

    def handle(self, *args, **options):
        reset_pw = options['reset_passwords']

        with transaction.atomic():
            admin, admin_created = self._ensure_demo_user(
                DEMO_ADMIN_PHONE,
                email='admin@demo.jamii.local',
                is_staff=True,
                is_superuser=True,
                reset_password=reset_pw,
            )
            member, member_created = self._ensure_demo_user(
                DEMO_MEMBER_PHONE,
                email='member@demo.jamii.local',
                is_staff=False,
                is_superuser=False,
                reset_password=reset_pw,
            )

            if admin_created:
                self.stdout.write(self.style.SUCCESS(f'Created demo admin {DEMO_ADMIN_PHONE}'))
            else:
                self.stdout.write(f'Demo admin {DEMO_ADMIN_PHONE} already exists')
                if reset_pw:
                    self.stdout.write(self.style.WARNING('  Password reset to 123456'))

            if member_created:
                self.stdout.write(self.style.SUCCESS(f'Created demo member {DEMO_MEMBER_PHONE}'))
            else:
                self.stdout.write(f'Demo member {DEMO_MEMBER_PHONE} already exists')
                if reset_pw:
                    self.stdout.write(self.style.WARNING('  Password reset to 123456'))

            group, g_created = Group.objects.get_or_create(
                invite_code=DEMO_GROUP_INVITE,
                defaults={
                    'name': DEMO_GROUP_NAME,
                    'description': 'Seeded group for local testing (seed_demo).',
                    'created_by': admin,
                    'approval_threshold': 1,
                    'min_contributions_to_qualify': 0,
                    'max_payout_amount': Decimal('500000.00'),
                    'contribution_amount': Decimal('500.00'),
                    'contribution_frequency': Group.ContributionFrequency.MONTHLY,
                },
            )
            if g_created:
                self.stdout.write(self.style.SUCCESS(f'Created group "{group.name}" (invite {DEMO_GROUP_INVITE})'))
            else:
                self.stdout.write(f'Group with invite {DEMO_GROUP_INVITE} already exists')

            GroupMember.objects.get_or_create(
                group=group,
                user=admin,
                defaults={
                    'role': GroupMember.Role.ADMIN,
                    'status': GroupMember.Status.ACTIVE,
                },
            )
            GroupMember.objects.get_or_create(
                group=group,
                user=member,
                defaults={
                    'role': GroupMember.Role.MEMBER,
                    'status': GroupMember.Status.ACTIVE,
                },
            )
            self.stdout.write('Ensured group memberships (admin + member).')

            period = timezone.now().strftime('%Y-%m')
            _, c_created = Contribution.objects.get_or_create(
                group=group,
                member=member,
                period=period,
                defaults={
                    'amount': Decimal('500.00'),
                    'status': Contribution.Status.CONFIRMED,
                },
            )
            if c_created:
                self.stdout.write(self.style.SUCCESS(f'Created sample contribution for {period}'))
            else:
                self.stdout.write(f'Contribution for {period} already exists')

            if not EmergencyRequest.objects.filter(group=group).exists():
                EmergencyRequest.objects.create(
                    group=group,
                    claimant=member,
                    emergency_type=EmergencyRequest.EmergencyType.OTHER,
                    description='Demo emergency — safe to delete after testing.',
                    amount_requested=Decimal('80000.00'),
                    payout_phone='254712345678',
                    status=EmergencyRequest.Status.PENDING,
                )
                self.stdout.write(self.style.SUCCESS('Created sample pending emergency'))
            else:
                self.stdout.write('Sample emergency already present for demo group')

            if not Hospital.objects.filter(name='Demo County Hospital').exists():
                Hospital.objects.create(
                    name='Demo County Hospital',
                    location='Nairobi, Kenya',
                    paybill='',
                )
                self.stdout.write(self.style.SUCCESS('Created demo hospital'))
            else:
                self.stdout.write('Demo hospital already exists')

        self.stdout.write(self.style.SUCCESS('\nDone. Login with README phones; password 123456'))

    def _ensure_demo_user(self, phone, *, email, is_staff, is_superuser, reset_password):
        user, created = User.objects.get_or_create(
            phone_number=phone,
            defaults={
                'username': phone,
                'email': email,
                'is_staff': is_staff,
                'is_superuser': is_superuser,
                'is_verified': True,
            },
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
        else:
            updates = []
            if user.is_staff != is_staff:
                user.is_staff = is_staff
                updates.append('is_staff')
            if user.is_superuser != is_superuser:
                user.is_superuser = is_superuser
                updates.append('is_superuser')
            if not user.is_verified:
                user.is_verified = True
                updates.append('is_verified')
            if user.email != email:
                user.email = email
                updates.append('email')
            if updates:
                user.save(update_fields=updates)
            if reset_password:
                user.set_password(DEMO_PASSWORD)
                user.save(update_fields=['password'])

        return user, created
