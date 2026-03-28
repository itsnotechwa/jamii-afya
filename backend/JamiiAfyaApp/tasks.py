from celery import shared_task
import logging

logger = logging.getLogger(__name__)


# ── Helper ─────────────────────────────────────────────────────────────────────

def _create_and_sms(recipient, event_type, title, body, reference_id, sms_message):
    """Create an in-app notification and fire an SMS in one step."""
    from apps.notifications.models import Notification
    from utils.sms import send_sms

    notif = Notification.objects.create(
        recipient=recipient,
        event_type=event_type,
        channel='both',
        title=title,
        body=body,
        reference_id=reference_id,
    )
    phone = str(recipient.phone_number)
    send_sms(phone=phone, message=sms_message, notification=notif)


# ── Task 1: New emergency raised — alert all group admins ──────────────────────

@shared_task
def notify_admins_new_emergency(emergency_id: int):
    from apps.emergencies.models import EmergencyRequest
    from apps.groups.models import GroupMember
    from apps.notifications.sms_service import SMSTemplates

    emergency = EmergencyRequest.objects.select_related('claimant', 'group').get(id=emergency_id)
    admins    = GroupMember.objects.filter(
        group=emergency.group, role='admin', status='active'
    ).select_related('user')

    for membership in admins:
        admin = membership.user
        sms   = SMSTemplates.emergency_raised_admin(
            claimant_name  = emergency.claimant.get_full_name(),
            emergency_type = emergency.emergency_type,
            amount         = float(emergency.amount_requested),
            group_name     = emergency.group.name,
        )
        _create_and_sms(
            recipient    = admin,
            event_type   = 'emergency_raised',
            title        = 'New Emergency Request',
            body         = (
                f"{emergency.claimant.get_full_name()} has raised a "
                f"{emergency.emergency_type} emergency requesting "
                f"KES {emergency.amount_requested:,} in {emergency.group.name}. "
                f"Your vote is needed."
            ),
            reference_id = emergency_id,
            sms_message  = sms,
        )

    logger.info(f"Notified {admins.count()} admins (in-app + SMS) about emergency {emergency_id}")


# ── Task 2: Emergency approved — notify claimant ───────────────────────────────

@shared_task
def notify_emergency_approved(emergency_id: int):
    from apps.emergencies.models import EmergencyRequest
    from apps.notifications.sms_service import SMSTemplates

    emergency = EmergencyRequest.objects.select_related('claimant', 'group').get(id=emergency_id)
    sms = SMSTemplates.emergency_approved_claimant(
        amount     = float(emergency.amount_approved),
        group_name = emergency.group.name,
    )
    _create_and_sms(
        recipient    = emergency.claimant,
        event_type   = 'emergency_approved',
        title        = 'Emergency Approved ✅',
        body         = (
            f"Your emergency request in {emergency.group.name} has been approved. "
            f"KES {emergency.amount_approved:,} will be disbursed to your M-Pesa shortly."
        ),
        reference_id = emergency_id,
        sms_message  = sms,
    )


# ── Task 3: Emergency rejected — notify claimant ───────────────────────────────

@shared_task
def notify_emergency_rejected(emergency_id: int):
    from apps.emergencies.models import EmergencyRequest
    from apps.notifications.sms_service import SMSTemplates

    emergency = EmergencyRequest.objects.select_related('claimant', 'group').get(id=emergency_id)
    sms = SMSTemplates.emergency_rejected(
        group_name = emergency.group.name,
        reason     = emergency.rejection_reason or 'Insufficient approvals.',
    )
    _create_and_sms(
        recipient    = emergency.claimant,
        event_type   = 'emergency_rejected',
        title        = 'Emergency Request Not Approved',
        body         = (
            f"Your emergency request in {emergency.group.name} was not approved. "
            f"Reason: {emergency.rejection_reason or 'Insufficient approvals.'}"
        ),
        reference_id = emergency_id,
        sms_message  = sms,
    )


# ── Task 4: Vote cast — notify the voting admin + update remaining count ───────

@shared_task
def notify_vote_cast(emergency_id: int, admin_id: int, decision: str):
    from apps.emergencies.models import EmergencyRequest
    from apps.users.models import User
    from apps.notifications.sms_service import SMSTemplates

    emergency = EmergencyRequest.objects.select_related('group').get(id=emergency_id)
    admin     = User.objects.get(id=admin_id)
    approvals = emergency.approvals.filter(decision='approve').count()
    remaining = max(0, emergency.group.approval_threshold - approvals)

    sms = SMSTemplates.vote_cast(
        emergency_id = emergency_id,
        decision     = decision,
        remaining    = remaining,
    )
    _create_and_sms(
        recipient    = admin,
        event_type   = 'vote_cast',
        title        = f'Vote recorded: {decision.upper()}',
        body         = (
            f"Your {decision} vote on emergency #{emergency_id} has been recorded. "
            f"{remaining} more approval(s) needed."
        ),
        reference_id = emergency_id,
        sms_message  = sms,
    )


# ── Task 5: Payout success or failure ─────────────────────────────────────────

@shared_task
def notify_payout_result(emergency_id: int, success: bool):
    from apps.emergencies.models import EmergencyRequest
    from apps.notifications.sms_service import SMSTemplates

    emergency = EmergencyRequest.objects.select_related('claimant', 'group').get(id=emergency_id)

    if success:
        sms = SMSTemplates.payout_success(
            amount        = float(emergency.amount_approved),
            mpesa_receipt = emergency.mpesa_ref or 'N/A',
        )
        _create_and_sms(
            recipient    = emergency.claimant,
            event_type   = 'payout_success',
            title        = 'Payout Successful 🎉',
            body         = (
                f"KES {emergency.amount_approved:,} has been sent to "
                f"{emergency.payout_phone} via M-Pesa. "
                f"Receipt: {emergency.mpesa_ref}. Wishing you a quick recovery."
            ),
            reference_id = emergency_id,
            sms_message  = sms,
        )
    else:
        sms = SMSTemplates.payout_failed(group_name=emergency.group.name)
        _create_and_sms(
            recipient    = emergency.claimant,
            event_type   = 'payout_failed',
            title        = 'Payout Failed',
            body         = (
                "Your emergency payout could not be processed. "
                "Please contact your group admin for assistance."
            ),
            reference_id = emergency_id,
            sms_message  = sms,
        )


# ── Task 6: Contribution confirmed ────────────────────────────────────────────

@shared_task
def notify_contribution_confirmed(contribution_id: int):
    from apps.contributions.models import Contribution
    from apps.notifications.sms_service import SMSTemplates

    contribution = Contribution.objects.select_related('member', 'group').get(id=contribution_id)
    sms = SMSTemplates.contribution_confirmed(
        amount        = float(contribution.amount),
        period        = contribution.period,
        group_name    = contribution.group.name,
        mpesa_receipt = contribution.mpesa_ref or 'N/A',
    )
    _create_and_sms(
        recipient    = contribution.member,
        event_type   = 'contribution_confirmed',
        title        = 'Contribution Confirmed ✅',
        body         = (
            f"KES {contribution.amount:,} contribution for {contribution.period} "
            f"in {contribution.group.name} confirmed. Receipt: {contribution.mpesa_ref}."
        ),
        reference_id = contribution_id,
        sms_message  = sms,
    )


# ── Task 7: Monthly contribution reminder (scheduled via Celery Beat) ──────────

@shared_task
def send_contribution_reminders(group_id: int, period: str, amount: float):
    """
    Remind members who haven't paid yet for the given period.
    Schedule this monthly in django-celery-beat.
    """
    from apps.groups.models import GroupMember
    from apps.contributions.models import Contribution
    from apps.notifications.sms_service import SMSTemplates

    paid_member_ids = set(
        Contribution.objects.filter(
            group_id=group_id, period=period, status='confirmed'
        ).values_list('member_id', flat=True)
    )

    unpaid_members = GroupMember.objects.filter(
        group_id=group_id, status='active'
    ).exclude(user_id__in=paid_member_ids).select_related('user', 'group')

    for membership in unpaid_members:
        user = membership.user
        sms  = SMSTemplates.contribution_reminder(
            member_name = user.get_full_name() or str(user.phone_number),
            amount      = amount,
            group_name  = membership.group.name,
            period      = period,
        )
        _create_and_sms(
            recipient    = user,
            event_type   = 'contribution_due',
            title        = f'Contribution Reminder — {period}',
            body         = (
                f"Your KES {amount:,} contribution for {period} "
                f"in {membership.group.name} is due."
            ),
            reference_id = group_id,
            sms_message  = sms,
        )

    logger.info(f"Sent contribution reminders to {unpaid_members.count()} members "
                f"in group {group_id} for {period}")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def disburse_emergency_payout(self, emergency_id: int):
    """
    Triggered after approval threshold is met.
    Sends B2C payment and records result.
    """
    from apps.emergencies.models import EmergencyRequest
    from apps.mpesa.services import MpesaService
    from apps.mpesa.models import MpesaTransaction
    from apps.notifications.tasks import notify_payout_result

    try:
        emergency = EmergencyRequest.objects.select_related('claimant', 'group').get(id=emergency_id)

        if emergency.status != 'approved':
            logger.warning(f"Emergency {emergency_id} not in approved state. Skipping.")
            return

        tx = MpesaTransaction.objects.create(
            user=emergency.claimant,
            tx_type='b2c',
            phone=emergency.payout_phone,
            amount=emergency.amount_approved,
            reference_id=emergency_id,
        )

        result = MpesaService.b2c_payment(
            phone=emergency.payout_phone,
            amount=float(emergency.amount_approved),
            occasion=f"Emergency-{emergency_id}",
        )

        if result.get('ResponseCode') == '0':
            tx.status = 'initiated'
            tx.checkout_request_id = result.get('ConversationID', '')
            tx.save(update_fields=['status', 'checkout_request_id'])
            logger.info(f"B2C initiated for emergency {emergency_id}")
        else:
            tx.status      = 'failed'
            tx.result_desc = result.get('ResponseDescription', 'Unknown error')
            tx.save(update_fields=['status', 'result_desc'])
            emergency.status = 'failed'
            emergency.save(update_fields=['status'])
            notify_payout_result.delay(emergency_id, success=False)

    except Exception as exc:
        logger.error(f"Payout task failed for emergency {emergency_id}: {exc}")
        raise self.retry(exc=exc)
