"""
CommsGrid SMS Service
Handles all outbound SMS for JamiiFund events.
Docs: https://sms.paygrid.co.ke
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

COMMSGRID_API_URL = "https://sms.paygrid.co.ke/api/sms/send"


class CommsGridSmsService:
    """
    Thin wrapper around the CommsGrid SMS REST API.
    Raises no exceptions — SMS failure must never break app flow.
    """

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """Ensure phone is in international format e.g. 254712345678 (no + prefix)."""
        phone = str(phone).strip().replace(' ', '').replace('+', '')
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        return phone

    @classmethod
    def send(cls, phone: str, message: str) -> dict:
        """
        Send a single SMS via CommsGrid.

        Returns the parsed JSON response dict, or an error dict on failure.
        Never raises — callers check the returned dict.
        """
        phone = cls._normalize_phone(phone)

        payload = {
            "recipient": phone,
            "message":   message,
            "sender_id": settings.COMMSGRID_SENDER_ID,
        }
        headers = {
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {settings.COMMSGRID_API_KEY}",
        }

        try:
            resp = requests.post(
                COMMSGRID_API_URL,
                json=payload,
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info(f"CommsGrid SMS sent to {phone}: {data}")
            return data
        except requests.exceptions.HTTPError as exc:
            logger.error(f"CommsGrid SMS HTTP error to {phone}: {exc} — {exc.response.text}")
            return {"error": str(exc), "detail": exc.response.text}
        except Exception as exc:
            logger.error(f"CommsGrid SMS FAILED to {phone}: {exc}")
            return {'error': str(exc)}

    @classmethod
    def send_bulk(cls, recipients: list[dict], message: str) -> list[dict]:
        """
        Send the same message to multiple phones via CommsGrid.
        recipients: [{'phone': '0712345678', 'name': 'John'}, ...]
        Returns a list of per-recipient result dicts.
        """
        results = []
        for recipient in recipients:
            result = cls.send(recipient['phone'], message)
            result['phone'] = cls._normalize_phone(recipient['phone'])
            results.append(result)
        return results


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
