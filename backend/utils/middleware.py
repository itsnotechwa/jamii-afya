import json
import logging

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
                ip_address=self._get_ip(request),
            )
        except Exception as e:
            logger.error(f"AuditLog write failed: {e}")

        return response

    @staticmethod
    def _get_ip(request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
