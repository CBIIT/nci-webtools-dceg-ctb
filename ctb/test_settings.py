"""Isolated application settings: no local secrets, live database, mail, or scheduler."""

import os
from unittest.mock import patch


with patch.dict(os.environ, {
    'CTB_ENV_FILE': os.devnull,
    'IS_GAE_DEPLOYMENT': 'True',
    'DATABASE_ENGINE': 'django.db.backends.sqlite3',
    'DATABASE_NAME': ':memory:',
    'SECRET_KEY': 'ctb-tests-only-not-a-deployment-secret-key',
    'SECURE_SSL_REDIRECT': 'False',
    'CSRF_COOKIE_SECURE': 'False',
    'SESSION_COOKIE_SECURE': 'False',
    'DAILY_MANAGEMENT_ENABLED': 'False',
    'SUPPORT_EMAIL': 'support@example.invalid',
    'DEFAULT_FROM_EMAIL': 'noreply@example.invalid',
    'CTB_APPLICATION_RECEIVER_EMAIL': 'reviewers@example.invalid',
    'CTB_LOGIN_URL': 'http://localhost/account/login/',
}, clear=True):
    from .settings import *  # noqa: F403

ALLOWED_HOSTS = ['localhost', 'testserver']
SITE_ID = 1
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
MIDDLEWARE = [
    middleware for middleware in MIDDLEWARE
    if middleware != 'ctb.redirect_middleware.RedirectMiddleware'
]
RESTRICT_ACCESS = False
AXES_IPWARE_PROXY_COUNT = 0
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles-test')
MIGRATION_MODULES = {'donors': 'ctb.test_migrations.donors'}

if os.environ.get('CTB_TEST_MYSQL_PORT'):
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': '127.0.0.1',
        'PORT': os.environ['CTB_TEST_MYSQL_PORT'],
        'NAME': 'ctb_upgrade',
        'USER': 'root',
        'PASSWORD': os.environ['CTB_TEST_MYSQL_PASSWORD'],
        'TEST': {'NAME': 'test_ctb_upgrade'},
    }}
