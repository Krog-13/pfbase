"""
Django settings for PFBase core.
Include:
- REST Framework
- SMTP
- Simple JWT
- MinIo S3 Storage
- Postgres with schemas public,dct,dcm,stm
- Logger
- Style grappelli
"""

import logging.config
from datetime import timedelta
from pathlib import Path

import os
from corsheaders.defaults import default_headers

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ["SECRET_KEY"]

DEBUG = os.environ["DEBUG"]
LOCAL = os.environ["LOCAL"]

ALLOWED_HOSTS = os.environ["ALLOWED_HOSTS"].split(",")

# Application definition
INSTALLED_APPS = [
    # Django admin css style
    'grappelli',

    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admindocs',
    'django.contrib.postgres',

    # Third-party
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'django_filters',
    'drf_spectacular',

    # Local
    'pfbase',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'petroflow.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'petroflow.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['DATABASE_NAME'],
        'USER': os.environ['DATABASE_USER'],
        'PASSWORD': os.environ['DATABASE_PASSWORD'],
        'HOST': os.environ['DATABASE_HOST'],
        'PORT': os.environ['DATABASE_PORT'],
        'OPTIONS': {
            'options': '-c search_path=public,dct,dcm,stm',
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = 'en'

TIME_ZONE = 'Asia/Almaty'

USE_I18N = False

USE_TZ = True

APPEND_SLASH = False

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# MinIO (S3-compatible) storage
MINIO_SERVER = os.environ["MINIO_SERVER"]
MINIO_ACCESS_KEY = os.environ["MINIO_ACCESS_KEY"]
MINIO_SECRET_KEY = os.environ["MINIO_SECRET_KEY"]
MINIO_BUCKET = os.environ["MINIO_BUCKET"]
MINIO_ENDPOINT_URL = os.environ["MINIO_ENDPOINT_URL"]

AWS_S3_ENDPOINT_URL = MINIO_ENDPOINT_URL
AWS_ACCESS_KEY_ID = MINIO_ACCESS_KEY
AWS_SECRET_ACCESS_KEY = MINIO_SECRET_KEY
AWS_STORAGE_BUCKET_NAME = MINIO_BUCKET
AWS_S3_REGION_NAME = "us-east-1"          # MinIO default
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_S3_ADDRESSING_STYLE = "path"          # required for MinIO
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = True               # signed (temporary) URLs; set False if bucket is public
AWS_S3_URL_PROTOCOL = "http:"

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# main config
SMTP_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
CONSOLE_BACKEND = "django.core.mail.backends.console.EmailBackend"

_BACKEND_ALIASES = {
    "smtp": SMTP_BACKEND,
    "console": CONSOLE_BACKEND,
}

EMAIL_BACKEND = SMTP_BACKEND
EMAIL_HOST = os.environ['EMAIL_HOST']
EMAIL_PORT = os.environ['EMAIL_PORT']
EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']
EMAIL_USE_TLS = os.environ['EMAIL_USE_TLS']
EMAIL_USE_SSL = os.environ['EMAIL_USE_SSL']
EMAIL_TIMEOUT = 10

MAILERS = {
    "default": {
        "BACKEND": _BACKEND_ALIASES["smtp"],
        "OPTIONS": {
            "host": EMAIL_HOST,
            "port": EMAIL_PORT,
            "password": EMAIL_HOST_PASSWORD,
            "username": EMAIL_HOST_USER,
            "use_tls": EMAIL_USE_TLS,
            "use_ssl": EMAIL_USE_SSL,
            "timeout": EMAIL_TIMEOUT,
        },
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Update default User
AUTH_USER_MODEL = 'pfbase.User'

REST_FRAMEWORK = {
    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    # 'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework.renderers.TemplateHTMLRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'file-upload': '10/min',
    },

    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

if LOCAL:
    # use local backend for local network
    CORS_ALLOW_HEADERS = list(default_headers) + [
        'ngrok-skip-browser-warning',
    ]
    CORS_ALLOW_ALL_ORIGINS = True
    # CORS_ORIGIN_WHITELIST = ["https://e792-176-98-224-108.ngrok-free.app", "http://localhost:5174"]
else:
    CORS_ALLOWED_ORIGINS = os.environ["CORS_ALLOWED_ORIGINS"]

CSRF_TRUSTED_ORIGINS = os.environ["CSRF_TRUSTED_ORIGINS"]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

SPECTACULAR_SETTINGS = {
    "TITLE": "Pfbase API",
    "DESCRIPTION": "API documentation for the Digital Twin project",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=360),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=2),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

LOGGING_CONFIG = None

LOGGING = {
    'version': 1,
    'disable_existing_logger': False,

    'formatters': {
        'default_formatter': {
            'format': '[%(levelname)s:%(asctime)s] %(message)s'
        },
    },
    'handlers': {
        'stream_handler': {
            'level': "INFO",
            'class': 'logging.StreamHandler',
            'formatter': 'default_formatter',
            'stream': 'ext://sys.stdout'
        },
        'file_handler': {
            'level': "WARNING",
            'filename': 'PF_LOG.log',
            'class': 'logging.FileHandler',
            'formatter': 'default_formatter',
            'mode': 'a'
        }
    },
    'loggers': {
        'pf_logger': {
            'handlers': ['stream_handler', 'file_handler'],
            'level': 'DEBUG',
            'propagate': False
        },
        'ief_logger': {
            'handlers': ['stream_handler', 'file_handler'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}


logging.config.dictConfig(LOGGING)
