import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'JamiiAfya.settings')

application = get_wsgi_application()
