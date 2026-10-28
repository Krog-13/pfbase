"""Disposable PostgreSQL database for integration tests; no production writes."""
from copy import deepcopy
from uuid import uuid4
import logging

from .settings import *  # noqa: F403

DEBUG = False
ALLOWED_HOSTS = ['testserver', 'localhost']
DATABASES = deepcopy(DATABASES)
DATABASES['default']['TEST'] = {'NAME': 'test_pfbase_security_' + uuid4().hex[:12]}
DATABASES['default']['OPTIONS']['connect_timeout'] = 5
TEST_RUNNER = 'petroflow.test_runner.SchemaTestRunner'
MAILERS = {'default': {'BACKEND': 'django.core.mail.backends.locmem.EmailBackend'}}
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
logging.getLogger('django.request').setLevel(logging.ERROR)
