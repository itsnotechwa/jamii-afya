"""HTTP helpers shared across apps."""


def get_client_ip(request) -> str:
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return (request.META.get('REMOTE_ADDR') or '').strip()
