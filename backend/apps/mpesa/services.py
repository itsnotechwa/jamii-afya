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
    def _generate_password(cls, shortcode: str = None):
        """Generate Daraja password.  shortcode defaults to MPESA_SHORTCODE."""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        sc        = shortcode or settings.MPESA_SHORTCODE
        raw       = f"{sc}{settings.MPESA_PASSKEY}{timestamp}"
        password  = base64.b64encode(raw.encode()).decode()
        return password, timestamp

    # ── C2B: STK Push (contributions) ─────────────────────────────────────────
    @classmethod
    def stk_push(cls, phone: str, amount: float, account_ref: str, description: str,
                 tx_type: str = 'buy_goods', shortcode_override: str = None) -> dict:
        """
        Initiate an STK Push (C2B).

        tx_type='buy_goods'  (default — Lipa Na M-Pesa till)
            BusinessShortCode = MPESA_SHORTCODE
            PartyB            = shortcode_override or MPESA_BUY_GOODS_TILL
            TransactionType   = CustomerBuyGoodsOnline
            Password uses     MPESA_SHORTCODE

        tx_type='paybill'
            BusinessShortCode = shortcode_override (the paybill number)
            PartyB            = shortcode_override
            TransactionType   = CustomerPayBillOnline
            Password uses     shortcode_override
        """
        # Normalize phone
        phone = phone.lstrip('+').replace(' ', '')
        if phone.startswith('0'):
            phone = '254' + phone[1:]

        if tx_type == 'paybill':
            paybill          = shortcode_override
            password, timestamp = cls._generate_password(shortcode=paybill)
            payload = {
                'BusinessShortCode': paybill,
                'Password':          password,
                'Timestamp':         timestamp,
                'TransactionType':   'CustomerPayBillOnline',
                'Amount':            int(amount),
                'PartyA':            phone,
                'PartyB':            paybill,
                'PhoneNumber':       phone,
                'CallBackURL':       settings.MPESA_CALLBACK_URL,
                'AccountReference':  account_ref,
                'TransactionDesc':   description,
            }
        else:  # buy_goods (default)
            till             = shortcode_override or settings.MPESA_BUY_GOODS_TILL
            password, timestamp = cls._generate_password()  # uses MPESA_SHORTCODE
            payload = {
                'BusinessShortCode': settings.MPESA_SHORTCODE,
                'Password':          password,
                'Timestamp':         timestamp,
                'TransactionType':   'CustomerBuyGoodsOnline',
                'Amount':            int(amount),
                'PartyA':            phone,
                'PartyB':            till,
                'PhoneNumber':       phone,
                'CallBackURL':       settings.MPESA_CALLBACK_URL,
                'AccountReference':  account_ref,
                'TransactionDesc':   description,
            }

        url  = f"{cls._base_url()}/mpesa/stkpush/v1/processrequest"
        resp = requests.post(url, json=payload, headers=cls._headers(), timeout=15)
        return resp.json()

    # ── C2B: STK Push Query (recheck status) ──────────────────────────────────
    @classmethod
    def stk_query(cls, checkout_request_id: str) -> dict:
        """
        Query the current status of an STK Push request.
        Use this when the callback has not arrived within the expected window.

        Returns a Daraja response dict with keys:
          ResponseCode, ResultCode, ResultDesc
          (and CallbackMetadata on success, same as callback payload)
        """
        password, timestamp = cls._generate_password()
        payload = {
            'BusinessShortCode': settings.MPESA_SHORTCODE,
            'Password':          password,
            'Timestamp':         timestamp,
            'CheckoutRequestID': checkout_request_id,
        }
        url  = f"{cls._base_url()}/mpesa/stkpushquery/v1/query"
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
