"""
utils/sms.py
Central helper: sends via Africa's Talking and writes an SMSLog row atomically.
Import this everywhere instead of calling ATSmsService directly.
"""
import logging
from apps.notifications.sms_service import ATSmsService

logger = logging.getLogger(__name__)


def send_sms(phone: str, message: str, notification=None) -> bool:
    """
    Send an SMS and record it in SMSLog.

    Args:
        phone:        Recipient phone (any format — normalised internally)
        message:      Plain-text message body (keep ≤160 chars for 1 unit)
        notification: Optional Notification FK for traceability

    Returns:
        True if Africa's Talking reports success, False otherwise.
    """
    from apps.notifications.models import SMSLog

    log = SMSLog.objects.create(
        notification=notification,
        recipient_phone=phone,
        message=message,
        status='pending',
    )

    response = ATSmsService.send(phone=phone, message=message)

    # Parse Africa's Talking response structure
    # Success shape: {'SMSMessageData': {'Recipients': [{'status': 'Success', ...}]}}
    try:
        recipients = response.get('SMSMessageData', {}).get('Recipients', [])
        if recipients:
            first       = recipients[0]
            at_status   = first.get('status', '')
            success     = at_status.lower() == 'success'
            log.status        = 'sent' if success else 'failed'
            log.at_message_id = first.get('messageId', '')
            log.at_cost       = first.get('cost', '')
            log.at_status_code = str(first.get('statusCode', ''))
        elif 'error' in response:
            success    = False
            log.status = 'failed'
        else:
            success    = False
            log.status = 'failed'
    except Exception as exc:
        logger.error(f"SMS log parse error: {exc}")
        success    = False
        log.status = 'failed'

    log.raw_response = response
    log.save(update_fields=['status', 'at_message_id', 'at_cost',
                             'at_status_code', 'raw_response'])
    return success
