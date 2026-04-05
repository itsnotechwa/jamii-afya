from utils.request_id import new_request_id, request_id_var


class RequestIdMiddleware:
    """Attach X-Request-ID (or generate) and expose it on logs via RequestIdFilter."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        rid = new_request_id(request.META.get('HTTP_X_REQUEST_ID'))
        request.request_id = rid
        token = request_id_var.set(rid)
        try:
            response = self.get_response(request)
            response.headers['X-Request-ID'] = rid
            return response
        finally:
            request_id_var.reset(token)
