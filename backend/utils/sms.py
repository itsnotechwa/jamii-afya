"""
utils/sms.py
Central helper: sends via CommsGrid and writes an SMSLog row atomically.
Import this everywhere instead of calling CommsGridSmsService directly.
"""
import logging
from apps.notifications.sms_service import CommsGridSmsService

logger = logging.getLogger(__name__)


def send_sms(phone: str, message: str, notification=None) -> bool:
    """
    Send an SMS and record it in SMSLog.

    Args:
        phone:        Recipient phone (any format — normalised internally)
        message:      Plain-text message body (keep ≤160 chars for 1 unit)
        notification: Optional Notification FK for traceability

    Returns:
        True if CommsGrid reports success, False otherwise.
    """
    from apps.notifications.models import SMSLog

    log = SMSLog.objects.create(
        notification=notification,
        recipient_phone=phone,
        message=message,
        status='pending',
    )

    response = CommsGridSmsService.send(phone=phone, message=message)

    # CommsGrid success shape:
    # {"status": "success", "message": "...", "data": {"sent": 1, "details": [{"message_id": "...", "status": "SENT"}]}}
    try:
        success = response.get('status', '').lower() == 'success'
        log.status          = 'sent' if success else 'failed'
        log.provider_status = response.get('status', '')
        # message_id lives inside data.details[0]
        details = response.get('data', {}).get('details', [])
        log.provider_message_id = str(details[0].get('message_id', '')) if details else ''
    except Exception as exc:
        logger.error(f"SMS log parse error: {exc}")
        success    = False
        log.status = 'failed'

    log.raw_response = response
    log.save(update_fields=['status', 'provider_message_id', 'provider_status', 'raw_response'])
    return success
