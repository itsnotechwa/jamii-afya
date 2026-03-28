from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def notify_admins_new_emergency(emergency_id: int):
    """Alert all group admins when a new emergency request is raised."""
    from apps.emergencies.models import EmergencyRequest
    from apps.groups.models import GroupMember
    from .models import Notification

    emergency = EmergencyRequest.objects.select_related('claimant', 'group').get(id=emergency_id)
    admins    = GroupMember.objects.filter(
        group=emergency.group, role='admin', status='active'
    ).select_related('user')

    notifications = [
        Notification(
            recipient=m.user,
            event_type='emergency_raised',
            title='New Emergency Request',
            body=(
                f"{emergency.claimant.get_full_name()} has raised an emergency "
                f"({emergency.emergency_type}) requesting KES {emergency.amount_requested:,}. "
                f"Your vote is needed."
            ),
            reference_id=emergency_id,
        )
        for m in admins
    ]
    Notification.objects.bulk_create(notifications)
    logger.info(f"Notified {len(notifications)} admins about emergency {emergency_id}")


@shared_task
def notify_payout_result(emergency_id: int, success: bool):
    """Notify claimant whether their payout succeeded or failed."""
    from apps.emergencies.models import EmergencyRequest
    from .models import Notification

    emergency = EmergencyRequest.objects.select_related('claimant').get(id=emergency_id)

    if success:
        title = "Payout Successful 🎉"
        body  = (
            f"KES {emergency.amount_approved:,} has been sent to {emergency.payout_phone} "
            f"via M-Pesa. Receipt: {emergency.mpesa_ref}"
        )
        event = 'payout_success'
    else:
        title = "Payout Failed"
        body  = (
            "Your emergency payout could not be processed. "
            "Please contact your group admin for assistance."
        )
        event = 'payout_failed'

    Notification.objects.create(
        recipient=emergency.claimant,
        event_type=event,
        title=title,
        body=body,
        reference_id=emergency_id,
    )

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
