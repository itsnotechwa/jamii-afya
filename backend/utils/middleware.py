import json
import logging

from utils.request import get_client_ip

logger = logging.getLogger(__name__)

WRITE_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}
SKIP_PATHS    = {'/api/mpesa/callback/', '/api/mpesa/b2c/result/', '/api/mpesa/b2c/timeout/'}


class AuditLogMiddleware:
    """
    Logs every write request to AuditLog after the response is returned.
    Skips M-Pesa webhook endpoints (high volume, Safaricom IPs) and GET requests.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Cache the raw body BEFORE passing to the view so that both DRF and
        # this middleware can read it without exhausting the stream.
        if request.method in WRITE_METHODS and request.content_type == 'application/json':
            try:
                # Reading here populates Django's internal _body cache.
                # Subsequent reads (by DRF or us) hit the cache, not the stream.
                _ = request.body
            except Exception:
                pass

        response = self.get_response(request)

        if request.method not in WRITE_METHODS:
            return response
        if request.path in SKIP_PATHS:
            return response

        try:
            from apps.audit.models import AuditLog
            payload = {}
            if request.content_type == 'application/json':
                try:
                    payload = json.loads(request.body or '{}')
                except json.JSONDecodeError:
                    pass
            # Scrub passwords
            payload.pop('password',  None)
            payload.pop('password2', None)

            AuditLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action=request.method,
                endpoint=request.path,
                payload=payload,
                response_code=response.status_code,
                ip_address=get_client_ip(request),
            )
        except Exception as e:
            logger.error(f"AuditLog write failed: {e}")

        return response
