import base64
import requests
from datetime import datetime
from django.conf import settings


class MpesaService:
    """
    Thin wrapper around the Safaricom Daraja API.
    Swap MPESA_ENVIRONMENT=production to go live — nothing else changes.
    """

    BASE_URLS = {
        'sandbox':    'https://sandbox.safaricom.co.ke',
        'production': 'https://api.safaricom.co.ke',
    }

    @classmethod
    def _base_url(cls):
        return cls.BASE_URLS[settings.MPESA_ENVIRONMENT]

    @classmethod
    def _get_access_token(cls):
        url  = f"{cls._base_url()}/oauth/v1/generate?grant_type=client_credentials"
        auth = (settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET)
        resp = requests.get(url, auth=auth, timeout=10)
        resp.raise_for_status()
        return resp.json()['access_token']

    @classmethod
    def _headers(cls):
        return {'Authorization': f'Bearer {cls._get_access_token()}',
                'Content-Type': 'application/json'}

    @classmethod
    def _generate_password(cls):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        raw       = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
        password  = base64.b64encode(raw.encode()).decode()
        return password, timestamp

    # ── C2B: STK Push (contributions) ─────────────────────────────────────────
    @classmethod
    def stk_push(cls, phone: str, amount: float, account_ref: str, description: str) -> dict:
        password, timestamp = cls._generate_password()
        # Normalize phone: strip leading + or 0, add 254
        phone = phone.lstrip('+').replace(' ', '')
        if phone.startswith('0'):
            phone = '254' + phone[1:]

        payload = {
            'BusinessShortCode': settings.MPESA_SHORTCODE,
            'Password':          password,
            'Timestamp':         timestamp,
            'TransactionType':   'CustomerPayBillOnline',
            'Amount':            int(amount),
            'PartyA':            phone,
            'PartyB':            settings.MPESA_SHORTCODE,
            'PhoneNumber':       phone,
            'CallBackURL':       settings.MPESA_CALLBACK_URL,
            'AccountReference':  account_ref,
            'TransactionDesc':   description,
        }
        url  = f"{cls._base_url()}/mpesa/stkpush/v1/processrequest"
        resp = requests.post(url, json=payload, headers=cls._headers(), timeout=15)
        return resp.json()

    # ── B2C: Disburse payout to member ────────────────────────────────────────
    @classmethod
    def b2c_payment(cls, phone: str, amount: float, occasion: str) -> dict:
        phone = phone.lstrip('+').replace(' ', '')
        if phone.startswith('0'):
            phone = '254' + phone[1:]

        payload = {
            'InitiatorName':      settings.MPESA_B2C_INITIATOR,
            'SecurityCredential': settings.MPESA_B2C_SECURITY_CREDENTIAL,
            'CommandID':          'BusinessPayment',
            'Amount':             int(amount),
            'PartyA':             settings.MPESA_SHORTCODE,
            'PartyB':             phone,
            'Remarks':            occasion,
            'QueueTimeOutURL':    settings.MPESA_B2C_QUEUE_TIMEOUT_URL,
            'ResultURL':          settings.MPESA_B2C_RESULT_URL,
            'Occasion':           occasion,
        }
        url  = f"{cls._base_url()}/mpesa/b2c/v1/paymentrequest"
        resp = requests.post(url, json=payload, headers=cls._headers(), timeout=15)
        return resp.json()
