# from pathlib import Path
# from decouple import config
# from datetime import timedelta

# import environ, os

# env = environ.Env()
# environ.Env.read_env()

# # Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent


# # Quick-start development settings - unsuitable for production
# # See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# # SECURITY WARNING: keep the secret key used in production secret!

# """SECRET_KEY = 'django-insecure-lg2(^z#c407b!-kzwk^p+p%(-9du_2mrr1xds&biwu)izzpd^&'"""
# SECRET_KEY = config('SECRET_KEY', default='change-me-in-production')

# # SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = config('DEBUG', default=False, cast=bool)
# ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

# # Application definition

# DJANGO_APPS = [
#     'django.contrib.admin',
#     'django.contrib.auth',
#     'django.contrib.contenttypes',
#     'django.contrib.sessions',
#     'django.contrib.messages',
#     'django.contrib.staticfiles',
# ]

# THIRD_PARTY_APPS = [
#     'rest_framework',
#     'rest_framework_simplejwt',
#     'corsheaders',
#     'django_filters',
#     'drf_spectacular',
#     'phonenumber_field',
#     'django_celery_beat',
# ]

# LOCAL_APPS = [
#     'apps.users',
#     'apps.groups',
#     'apps.contributions',
#     'apps.emergencies',
#     'apps.mpesa',
#     'apps.notifications',
#     'apps.audit',
# ]

# INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


# MIDDLEWARE = [
#     'django.middleware.security.SecurityMiddleware',
#     'corsheaders.middleware.CorsMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
#     'utils.middleware.AuditLogMiddleware',
# ]

# ROOT_URLCONF = 'config.urls'
# AUTH_USER_MODEL = 'users.User'

# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [BASE_DIR / 'templates'],  # Add this line to specify the templates directory
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = 'config.wsgi.application'


# # Database
# # https://docs.djangoproject.com/en/6.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': config('DB_NAME', default='jamii_fund'),
#         'USER': config('DB_USER', default='root'),
#         'PASSWORD': config('DB_PASSWORD', default=''),
#         'HOST': config('DB_HOST', default='localhost'),
#         'PORT': config('DB_PORT', default='3306'),
#         'OPTIONS': {
#             'charset': 'utf8mb4',
#             'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
#         },
#         'CONN_MAX_AGE': 60,  # persistent connections for speed
#     }
# }

# # ── REST Framework ─────────────────────────────────────────────────────────────
# REST_FRAMEWORK = {
#     'DEFAULT_AUTHENTICATION_CLASSES': (
#         'rest_framework_simplejwt.authentication.JWTAuthentication',
#     ),
#     'DEFAULT_PERMISSION_CLASSES': (
#         'rest_framework.permissions.IsAuthenticated',
#     ),
#     'DEFAULT_FILTER_BACKENDS': [
#         'django_filters.rest_framework.DjangoFilterBackend',
#         'rest_framework.filters.SearchFilter',
#         'rest_framework.filters.OrderingFilter',
#     ],
#     'DEFAULT_PAGINATION_CLASS': 'utils.pagination.StandardPagination',
#     'PAGE_SIZE': 20,
#     'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
# }

# SIMPLE_JWT = {
#     'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
#     'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
#     'ROTATE_REFRESH_TOKENS': True,
# }

# # ── M-Pesa ─────────────────────────────────────────────────────────────────────
# MPESA_ENVIRONMENT = config('MPESA_ENVIRONMENT', default='sandbox')
# MPESA_CONSUMER_KEY = config('MPESA_CONSUMER_KEY', default='')
# MPESA_CONSUMER_SECRET = config('MPESA_CONSUMER_SECRET', default='')
# MPESA_SHORTCODE = config('MPESA_SHORTCODE', default='174379')
# MPESA_BUY_GOODS_TILL = config('MPESA_BUY_GOODS_TILL', default='')
# MPESA_PASSKEY = config('MPESA_PASSKEY', default='')
# MPESA_CALLBACK_URL = config('MPESA_CALLBACK_URL', default='https://yourdomain.com/api/mpesa/callback/')
# MPESA_B2C_INITIATOR = config('MPESA_B2C_INITIATOR', default='')
# MPESA_B2C_SECURITY_CREDENTIAL = config('MPESA_B2C_SECURITY_CREDENTIAL', default='')
# MPESA_B2C_QUEUE_TIMEOUT_URL = config('MPESA_B2C_QUEUE_TIMEOUT_URL', default='https://yourdomain.com/api/mpesa/b2c/timeout/')
# MPESA_B2C_RESULT_URL = config('MPESA_B2C_RESULT_URL', default='https://yourdomain.com/api/mpesa/b2c/result/')

# # ── CommsGrid SMS ─────────────────────────────────────────────────────────────
# COMMSGRID_API_KEY   = config('COMMSGRID_API_KEY',   default='')
# COMMSGRID_SENDER_ID = config('COMMSGRID_SENDER_ID', default='JamiiFund')

# # ── Celery ─────────────────────────────────────────────────────────────────────
# CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
# CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_TASK_SERIALIZER = 'json'

# # ── CORS ───────────────────────────────────────────────────────────────────────
# CORS_ALLOW_ALL_ORIGINS = DEBUG
# CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='').split(',')


# # Password validation
# # https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

# AUTH_PASSWORD_VALIDATORS = [
#     {
#         'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
#     },
# ]


# # Internationalization
# # https://docs.djangoproject.com/en/6.0/topics/i18n/

# LANGUAGE_CODE = 'en-us'

# TIME_ZONE = 'Africa/Nairobi'

# USE_I18N = True

# USE_TZ = True


# # Static files (CSS, JavaScript, Images)
# # https://docs.djangoproject.com/en/6.0/howto/static-files/

# STATIC_URL = 'static/'
# MEDIA_URL = '/media/'
# MEDIA_ROOT = BASE_DIR / 'media'
# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# SPECTACULAR_SETTINGS = {
#     'TITLE': 'JamiiFund API',
#     'DESCRIPTION': (
#         'REST API for **JamiiFund** — a community emergency medical fund platform '
#         'for Kenyan chamas/welfare groups, powered by Safaricom M-Pesa.\n\n'
#         '## Authentication\n'
#         'All protected endpoints require a **Bearer JWT** token in the `Authorization` header.\n'
#         '```\nAuthorization: Bearer <access_token>\n```\n'
#         'Obtain tokens from `POST /api/auth/login/`.  '
#         'Refresh with `POST /api/auth/refresh/`.'
#     ),
#     'VERSION': '1.0.0',
#     'CONTACT': {'name': 'JamiiFund Team'},
#     'LICENSE': {'name': 'Proprietary'},
#     'SERVERS': [
#         {'url': 'http://127.0.0.1:8000', 'description': 'Local development'},
#     ],
#     # JWT auth — adds the Authorize 🔒 button in Swagger UI
#     'SECURITY': [{'BearerAuth': []}],
#     'COMPONENTS': {
#         'securitySchemes': {
#             'BearerAuth': {
#                 'type': 'http',
#                 'scheme': 'bearer',
#                 'bearerFormat': 'JWT',
#             }
#         }
#     },
#     # Group endpoints by URL prefix tag
#     'SORT_OPERATIONS': False,
#     'TAGS': [
#         {'name': 'Auth',          'description': 'Registration, login, JWT refresh, OTP verification'},
#         {'name': 'Groups',        'description': 'Chama/welfare group management'},
#         {'name': 'Contributions', 'description': 'Monthly contribution payments via M-Pesa STK Push'},
#         {'name': 'Emergencies',   'description': 'Emergency requests, admin voting, disbursement'},
#         {'name': 'M-Pesa',        'description': 'Safaricom Daraja API webhook callbacks (internal use)'},
#         {'name': 'Notifications', 'description': 'In-app notification inbox'},
#         {'name': 'Audit',         'description': 'Audit log trail (admin only)'},
#     ],
#     'SWAGGER_UI_SETTINGS': {
#         'deepLinking': True,
#         'persistAuthorization': True,
#         'displayRequestDuration': True,
#         'filter': True,
#     },
#     'SERVE_INCLUDE_SCHEMA': False,
# }


from pathlib import Path
from decouple import config
from datetime import timedelta
import os

from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ───────────────────────────────────────────────────────────────────
# Local dev: optional default. Production (DEBUG=False): set SECRET_KEY (e.g. Railway Variables).
_DEV_SECRET_KEY = 'django-insecure-local-only-set-secret-key-env-in-production'
DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY', default=_DEV_SECRET_KEY)
if not DEBUG and SECRET_KEY == _DEV_SECRET_KEY:
    raise ImproperlyConfigured(
        'SECRET_KEY is missing or still the dev default while DEBUG=False. '
        'Add SECRET_KEY in your host (Railway: Project → Variables → New Variable).'
    )
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

# ── Applications ───────────────────────────────────────────────────────────────
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    'phonenumber_field',
    'django_celery_beat',
]

LOCAL_APPS = [
    'apps.users',
    'apps.groups',
    'apps.contributions',
    'apps.emergencies',
    'apps.mpesa',
    'apps.notifications',
    'apps.audit',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ── Middleware ─────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # serves static files on Render
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'utils.middleware.AuditLogMiddleware',
]

ROOT_URLCONF = 'config.urls'
AUTH_USER_MODEL = 'users.User'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ── Database (Aiven MySQL) ─────────────────────────────────────────────────────
# CA cert is written to disk at build time from the AIVEN_CA_BASE64 env variable.
# See build.sh for how the cert file is created.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'ssl': {
                'ca': config('DB_SSL_CA', default='/etc/ssl/aiven-ca.pem'),
            },
        },
        'CONN_MAX_AGE': 60,
    }
}

# ── Static & Media ─────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── REST Framework ─────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'utils.pagination.StandardPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

# ── CORS ───────────────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='').split(',')

# ── Celery ─────────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

# ── M-Pesa ─────────────────────────────────────────────────────────────────────
MPESA_ENVIRONMENT = config('MPESA_ENVIRONMENT', default='sandbox')
MPESA_CONSUMER_KEY = config('MPESA_CONSUMER_KEY', default='')
MPESA_CONSUMER_SECRET = config('MPESA_CONSUMER_SECRET', default='')
MPESA_SHORTCODE = config('MPESA_SHORTCODE', default='174379')
MPESA_BUY_GOODS_TILL = config('MPESA_BUY_GOODS_TILL', default='')
MPESA_PASSKEY = config('MPESA_PASSKEY', default='')
MPESA_CALLBACK_URL = config('MPESA_CALLBACK_URL', default='')
MPESA_B2C_INITIATOR = config('MPESA_B2C_INITIATOR', default='')
MPESA_B2C_SECURITY_CREDENTIAL = config('MPESA_B2C_SECURITY_CREDENTIAL', default='')
MPESA_B2C_QUEUE_TIMEOUT_URL = config('MPESA_B2C_QUEUE_TIMEOUT_URL', default='')
MPESA_B2C_RESULT_URL = config('MPESA_B2C_RESULT_URL', default='')

# ── CommsGrid SMS ──────────────────────────────────────────────────────────────
COMMSGRID_API_KEY   = config('COMMSGRID_API_KEY',   default='')
COMMSGRID_SENDER_ID = config('COMMSGRID_SENDER_ID', default='JamiiFund')

# ── Password Validation ────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── Internationalisation ───────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

# ── DRF Spectacular ────────────────────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    'TITLE': 'JamiiFund API',
    'DESCRIPTION': (
        'REST API for **JamiiFund** — a community emergency medical fund platform '
        'for Kenyan chamas/welfare groups, powered by Safaricom M-Pesa.\n\n'
        '## Authentication\n'
        'All protected endpoints require a **Bearer JWT** token in the `Authorization` header.\n'
        '```\nAuthorization: Bearer <access_token>\n```\n'
        'Obtain tokens from `POST /api/auth/login/`.  '
        'Refresh with `POST /api/auth/refresh/`.'
    ),
    'VERSION': '1.0.0',
    'CONTACT': {'name': 'JamiiFund Team'},
    'LICENSE': {'name': 'Proprietary'},
    'SERVERS': [
        {'url': 'https://your-app.onrender.com', 'description': 'Production'},
        {'url': 'http://127.0.0.1:8000',         'description': 'Local development'},
    ],
    'SECURITY': [{'BearerAuth': []}],
    'COMPONENTS': {
        'securitySchemes': {
            'BearerAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
            }
        }
    },
    'SORT_OPERATIONS': False,
    'TAGS': [
        {'name': 'Auth',          'description': 'Registration, login, JWT refresh, OTP verification'},
        {'name': 'Groups',        'description': 'Chama/welfare group management'},
        {'name': 'Contributions', 'description': 'Monthly contribution payments via M-Pesa STK Push'},
        {'name': 'Emergencies',   'description': 'Emergency requests, admin voting, disbursement'},
        {'name': 'M-Pesa',        'description': 'Safaricom Daraja API webhook callbacks (internal use)'},
        {'name': 'Notifications', 'description': 'In-app notification inbox'},
        {'name': 'Audit',         'description': 'Audit log trail (admin only)'},
    ],
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayRequestDuration': True,
        'filter': True,
    },
    'SERVE_INCLUDE_SCHEMA': False,
}