"""
Africa's Talking SMS Service
Handles all outbound SMS for JamiiFund events.
Docs: https://developers.africastalking.com/docs/sms/sending
"""
import logging
import africastalking
from django.conf import settings

logger = logging.getLogger(__name__)


class ATSmsService:
    """
    Thin wrapper around the Africa's Talking SMS API.
    Initialises once; switch AT_ENVIRONMENT=production to go live.
    """

    _initialised = False

    @classmethod
    def _init(cls):
        if not cls._initialised:
            africastalking.initialize(
                username=settings.AT_USERNAME,
                api_key=settings.AT_API_KEY,
            )
            cls._initialised = True

    @classmethod
    def _normalize_phone(cls, phone: str) -> str:
        """Ensure phone is in international format e.g. +254712345678"""
        phone = str(phone).strip().replace(' ', '')
        if phone.startswith('0'):
            phone = '+254' + phone[1:]
        elif phone.startswith('254') and not phone.startswith('+'):
            phone = '+' + phone
        return phone

    @classmethod
    def send(cls, phone: str, message: str) -> dict:
        """
        Send a single SMS.
        Returns the Africa's Talking response dict.
        Logs errors but does NOT raise — SMS failure must never break app flow.
        """
        cls._init()
        phone = cls._normalize_phone(phone)

        try:
            sms      = africastalking.SMS
            response = sms.send(
                message=message,
                recipients=[phone],
                sender_id=settings.AT_SENDER_ID or None,  # None = shortcode default
            )
            logger.info(f"AT SMS sent to {phone}: {response}")
            return response
        except Exception as exc:
            logger.error(f"AT SMS FAILED to {phone}: {exc}")
            return {'error': str(exc)}

    @classmethod
    def send_bulk(cls, recipients: list[dict], message: str) -> dict:
        """
        Send the same message to multiple phones.
        recipients: [{'phone': '+254...', 'name': 'John'}, ...]
        """
        cls._init()
        phones = [cls._normalize_phone(r['phone']) for r in recipients]

        try:
            sms      = africastalking.SMS
            response = sms.send(
                message=message,
                recipients=phones,
                sender_id=settings.AT_SENDER_ID or None,
            )
            logger.info(f"AT bulk SMS to {len(phones)} recipients: {response}")
            return response
        except Exception as exc:
            logger.error(f"AT bulk SMS FAILED: {exc}")
            return {'error': str(exc)}


# ── Pre-built message templates ───────────────────────────────────────────────

class SMSTemplates:

    @staticmethod
    def emergency_raised_admin(claimant_name: str, emergency_type: str,
                               amount: float, group_name: str) -> str:
        return (
            f"[JamiiFund] URGENT: {claimant_name} in {group_name} needs "
            f"KES {amount:,.0f} for {emergency_type}. "
            f"Log in to review and vote: jamii.fund/emergencies"
        )

    @staticmethod
    def emergency_approved_claimant(amount: float, group_name: str) -> str:
        return (
            f"[JamiiFund] Good news! Your emergency request in {group_name} "
            f"has been approved. KES {amount:,.0f} will be sent to your M-Pesa shortly."
        )

    @staticmethod
    def payout_success(amount: float, mpesa_receipt: str) -> str:
        return (
            f"[JamiiFund] KES {amount:,.0f} sent to your M-Pesa. "
            f"Receipt: {mpesa_receipt}. Wishing you a quick recovery."
        )

    @staticmethod
    def payout_failed(group_name: str) -> str:
        return (
            f"[JamiiFund] We could not complete your payout from {group_name}. "
            f"Please contact your group admin. We apologise for the inconvenience."
        )

    @staticmethod
    def contribution_confirmed(amount: float, period: str, group_name: str,
                               mpesa_receipt: str) -> str:
        return (
            f"[JamiiFund] Contribution confirmed: KES {amount:,.0f} "
            f"for {period} in {group_name}. Receipt: {mpesa_receipt}. Asante!"
        )

    @staticmethod
    def contribution_reminder(member_name: str, amount: float,
                              group_name: str, period: str) -> str:
        return (
            f"[JamiiFund] Hi {member_name}, your KES {amount:,.0f} "
            f"contribution for {period} in {group_name} is due. "
            f"Pay via M-Pesa to stay eligible for emergency support."
        )

    @staticmethod
    def vote_cast(emergency_id: int, decision: str, remaining: int) -> str:
        return (
            f"[JamiiFund] Vote recorded: {decision.upper()} on emergency #{emergency_id}. "
            f"{remaining} more vote(s) needed to reach threshold."
        )

    @staticmethod
    def emergency_rejected(group_name: str, reason: str) -> str:
        return (
            f"[JamiiFund] Your emergency request in {group_name} was not approved. "
            f"Reason: {reason[:80]}. Contact your admin for more info."
        )
