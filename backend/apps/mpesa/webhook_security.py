"""
M-Pesa Daraja webhook verification: optional shared secret, IP allowlist,
payload shape checks, and replay/idempotency via cache.

Safaricom does not sign STK/B2C callbacks with HMAC; perimeter controls
(secret token on URL or reverse-proxy header, CIDR/IP allowlist) are the
practical hardening layers.
"""
from __future__ import annotations

import hmac
import logging
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from rest_framework.request import Request
from rest_framework.response import Response

from utils.request import get_client_ip

logger = logging.getLogger(__name__)

REPLAY_TTL_SECONDS = 72 * 3600  # Safaricom may retry; keep wide window


def assert_production_webhook_config() -> None:
    """Require at least one webhook authenticity control when DEBUG is False."""
    if settings.DEBUG:
        return
    secret = (getattr(settings, 'MPESA_WEBHOOK_SECRET', None) or '').strip()
    ips = getattr(settings, 'MPESA_CALLBACK_ALLOWED_IPS', None) or []
    if not secret and not ips:
        raise ImproperlyConfigured(
            'Production requires MPESA_WEBHOOK_SECRET (URL ?token=, header, or Bearer) '
            'and/or MPESA_CALLBACK_ALLOWED_IPS for M-Pesa callbacks.'
        )


def _secret_ok(request: Request, secret: str) -> bool:
    if not secret:
        return False
    q = (request.query_params.get('token') or '').strip()
    if q and hmac.compare_digest(secret, q):
        return True
    hdr = (request.META.get('HTTP_X_MPESA_WEBHOOK_SECRET') or '').strip()
    if hdr and hmac.compare_digest(secret, hdr):
        return True
    auth = request.META.get('HTTP_AUTHORIZATION') or ''
    if auth.startswith('Bearer '):
        tok = auth[7:].strip()
        if tok and hmac.compare_digest(secret, tok):
            return True
    return False


def _ip_allowed(request: Request, allowed: list[str]) -> bool:
    if not allowed:
        return True
    ip = get_client_ip(request)
    return ip in allowed


def verify_mpesa_webhook(request: Request) -> Response | None:
    """
    Return a DRF Response if the request must be rejected; None if OK.
    """
    assert_production_webhook_config()

    secret = (getattr(settings, 'MPESA_WEBHOOK_SECRET', None) or '').strip()
    allowed_ips = list(getattr(settings, 'MPESA_CALLBACK_ALLOWED_IPS', None) or [])

    if not settings.DEBUG and not secret and not allowed_ips:
        logger.critical(
            'M-Pesa webhook verification has no secret or IP allowlist (misconfiguration).'
        )
        return Response({'ResultCode': 1, 'ResultDesc': 'Service Unavailable'}, status=503)

    if settings.DEBUG and not secret and not allowed_ips:
        logger.warning(
            'M-Pesa webhook accepted with no MPESA_WEBHOOK_SECRET or MPESA_CALLBACK_ALLOWED_IPS '
            '(DEBUG=True only). Configure before exposing callbacks to the internet.'
        )

    if secret and not _secret_ok(request, secret):
        logger.warning('M-Pesa webhook rejected: invalid or missing shared secret')
        return Response({'ResultCode': 1, 'ResultDesc': 'Unauthorized'}, status=401)

    if allowed_ips and not _ip_allowed(request, allowed_ips):
        logger.warning('M-Pesa webhook rejected: IP %s not in allowlist', get_client_ip(request))
        return Response({'ResultCode': 1, 'ResultDesc': 'Forbidden'}, status=403)

    return None


def _coerce_items(items: Any) -> list[dict]:
    if items is None:
        return []
    if isinstance(items, dict):
        return [items]
    if isinstance(items, list):
        return [x for x in items if isinstance(x, dict)]
    return []


def parse_stk_callback_payload(data: dict) -> dict[str, Any]:
    """Validate STK callback JSON; raise ValueError on bad shape."""
    if not isinstance(data, dict):
        raise ValueError('Body must be a JSON object')
    body = data.get('Body')
    if not isinstance(body, dict):
        raise ValueError('Missing Body object')
    cb = body.get('stkCallback')
    if not isinstance(cb, dict):
        raise ValueError('Missing Body.stkCallback')
    checkout_id = (cb.get('CheckoutRequestID') or '').strip()
    if not checkout_id:
        raise ValueError('Missing CheckoutRequestID')
    if 'ResultCode' not in cb:
        raise ValueError('Missing ResultCode')
    result_code = str(cb.get('ResultCode', ''))
    meta = cb.get('CallbackMetadata') or {}
    if meta is not None and not isinstance(meta, dict):
        raise ValueError('Invalid CallbackMetadata')
    item = _coerce_items((meta or {}).get('Item'))
    return {
        'checkout_id': checkout_id,
        'result_code': result_code,
        'result_desc': cb.get('ResultDesc', '') or '',
        'callback': cb,
        'metadata_items': item,
        'raw': data,
    }


def parse_b2c_result_payload(data: dict) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError('Body must be a JSON object')
    result = data.get('Result')
    if not isinstance(result, dict):
        raise ValueError('Missing Result object')
    conv_id = (result.get('ConversationID') or '').strip()
    if not conv_id:
        raise ValueError('Missing ConversationID')
    if 'ResultCode' not in result:
        raise ValueError('Missing ResultCode')
    result_code = str(result.get('ResultCode', ''))
    rparams = result.get('ResultParameters') or {}
    if rparams is not None and not isinstance(rparams, dict):
        raise ValueError('Invalid ResultParameters')
    params_list = _coerce_items((rparams or {}).get('ResultParameter'))
    return {
        'conversation_id': conv_id,
        'result_code': result_code,
        'result_desc': result.get('ResultDesc', '') or '',
        'result': result,
        'params_list': params_list,
        'raw': data,
    }


def parse_b2c_timeout_payload(data: dict) -> str:
    if not isinstance(data, dict):
        raise ValueError('Body must be a JSON object')
    result = data.get('Result')
    if not isinstance(result, dict):
        raise ValueError('Missing Result object')
    conv_id = (result.get('ConversationID') or '').strip()
    if not conv_id:
        raise ValueError('Missing ConversationID')
    return conv_id


def replay_cache_key(kind: str, checkout_or_conv_id: str, result_code: str) -> str:
    return f'mpesa:cb:{kind}:v1:{checkout_or_conv_id}:{result_code}'


def should_skip_replay(kind: str, checkout_or_conv_id: str, result_code: str) -> bool:
    """True if this exact callback outcome was already accepted (idempotent)."""
    key = replay_cache_key(kind, checkout_or_conv_id, result_code)
    return cache.get(key) == '1'


def mark_replay_processed(kind: str, checkout_or_conv_id: str, result_code: str) -> None:
    cache.set(replay_cache_key(kind, checkout_or_conv_id, result_code), '1', REPLAY_TTL_SECONDS)
