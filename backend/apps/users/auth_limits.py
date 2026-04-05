"""Account lockouts for login and OTP verification (cache-backed)."""

from __future__ import annotations

import hashlib

from django.conf import settings
from django.core.cache import cache
from rest_framework import serializers

from utils.request import get_client_ip


def _hash_id(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()[:40]


def _login_fail_key(identifier: str, ip: str) -> str:
    return f'auth:login_fail:v1:{_hash_id(identifier.strip().lower())}:{ip or "-"}'


def _login_lock_key(identifier: str, ip: str) -> str:
    return f'auth:login_lock:v1:{_hash_id(identifier.strip().lower())}:{ip or "-"}'


def assert_login_allowed(identifier: str, ip: str) -> None:
    if cache.get(_login_lock_key(identifier, ip)):
        raise serializers.ValidationError(
            'Too many failed login attempts. Please try again later.'
        )


def record_login_failure(identifier: str, ip: str) -> None:
    max_attempts = int(getattr(settings, 'AUTH_LOGIN_MAX_ATTEMPTS', 10))
    lockout = int(getattr(settings, 'AUTH_LOGIN_LOCKOUT_SECONDS', 900))

    fk = _login_fail_key(identifier, ip)
    try:
        n = int(cache.get(fk, 0))
    except (TypeError, ValueError):
        n = 0
    n += 1
    cache.set(fk, n, lockout)

    if n >= max_attempts:
        cache.set(_login_lock_key(identifier, ip), 1, lockout)
        cache.delete(fk)


def clear_login_failures(identifier: str, ip: str) -> None:
    cache.delete(_login_fail_key(identifier, ip))
    cache.delete(_login_lock_key(identifier, ip))


def _otp_fail_key(user_id: int, ip: str) -> str:
    return f'auth:otp_fail:v1:{user_id}:{ip or "-"}'


def _otp_lock_key(user_id: int, ip: str) -> str:
    return f'auth:otp_lock:v1:{user_id}:{ip or "-"}'


def assert_otp_verify_allowed(user_id: int, request) -> None:
    ip = get_client_ip(request)
    if cache.get(_otp_lock_key(user_id, ip)):
        raise serializers.ValidationError(
            'Too many invalid OTP attempts. Please try again later.'
        )


def record_otp_verify_failure(user_id: int, request) -> None:
    ip = get_client_ip(request)
    max_attempts = int(getattr(settings, 'AUTH_OTP_VERIFY_MAX_ATTEMPTS', 10))
    lockout = int(getattr(settings, 'AUTH_OTP_VERIFY_LOCKOUT_SECONDS', 900))

    fk = _otp_fail_key(user_id, ip)
    try:
        n = int(cache.get(fk, 0))
    except (TypeError, ValueError):
        n = 0
    n += 1
    cache.set(fk, n, lockout)
    if n >= max_attempts:
        cache.set(_otp_lock_key(user_id, ip), 1, lockout)
        cache.delete(fk)


def clear_otp_verify_failures(user_id: int, request) -> None:
    ip = get_client_ip(request)
    cache.delete(_otp_fail_key(user_id, ip))
    cache.delete(_otp_lock_key(user_id, ip))
