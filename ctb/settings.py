###
# Copyright 2015-2023, Institute for Systems Biology
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

from __future__ import print_function
from builtins import str
from builtins import object
import os
import re
import datetime
from os.path import join, dirname, exists
from pathlib import Path
import sys
import dotenv
from socket import gethostname, gethostbyname
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pymysql

APP_ENGINE_FLEX = 'aef-'
APP_ENGINE = 'Google App Engine/'

SECURE_LOCAL_PATH = os.environ.get('SECURE_LOCAL_PATH', '')

if not exists(join(dirname(__file__), '../{}.env'.format(SECURE_LOCAL_PATH))):
    print("[ERROR] Couldn't open .env file expected at {}!".format(
        join(dirname(__file__), '../{}.env'.format(SECURE_LOCAL_PATH)))
    )
    print("[ERROR] Exiting settings.py load - check your Pycharm settings and secure_path.env file.")
    exit(1)

dotenv.read_dotenv(join(dirname(__file__), '../{}.env'.format(SECURE_LOCAL_PATH)))
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + os.sep

SHARED_SOURCE_DIRECTORIES = []

# Add the shared Django application subdirectory to the Python module search path
for directory_name in SHARED_SOURCE_DIRECTORIES:
    sys.path.append(os.path.join(BASE_DIR, directory_name))

DEBUG = (os.environ.get('DEBUG', 'False') == 'True')
CONNECTION_IS_LOCAL = (os.environ.get('DATABASE_HOST', '127.0.0.1') == 'localhost')
IS_CIRCLE = (os.environ.get('CI', None) is not None)
DEBUG_TOOLBAR = ((os.environ.get('DEBUG_TOOLBAR', 'False') == 'True') and CONNECTION_IS_LOCAL)
LOCAL_RESPONSE_PAGES = (os.environ.get('LOCAL_RESPONSE_PAGES', 'False') == 'True')

print("[STATUS] DEBUG mode is {}".format(str(DEBUG)), file=sys.stdout)

RESTRICT_ACCESS = (os.environ.get('RESTRICT_ACCESS', 'True') == 'True')
RESTRICTED_ACCESS_GROUPS = os.environ.get('RESTRICTED_ACCESS_GROUPS', '').split(',')

if RESTRICT_ACCESS:
    print("[STATUS] Access to the site is restricted to members of the {} group(s).".format(
        ", ".join(RESTRICTED_ACCESS_GROUPS)), file=sys.stdout)
else:
    print("[STATUS] Access to the site is NOT restricted!", file=sys.stdout)

# Theoretically Nginx allows us to use '*' for ALLOWED_HOSTS but...
ALLOWED_HOSTS = list(
    set(os.environ.get('ALLOWED_HOST', 'localhost').split(',') + ['localhost', '127.0.0.1', '[::1]', gethostname(),
                                                                  gethostbyname(gethostname()), ]))
#ALLOWED_HOSTS = ['localhost','127.0.0.1']

SSL_DIR = os.path.abspath(os.path.dirname(__file__)) + os.sep

ADMINS = ()
MANAGERS = ADMINS

GCLOUD_PROJECT_ID = os.environ.get('GCLOUD_PROJECT_ID', '')
GCLOUD_PROJECT_NUMBER = os.environ.get('GCLOUD_PROJECT_NUMBER', '')
BIGQUERY_PROJECT_ID = os.environ.get('BIGQUERY_PROJECT_ID', GCLOUD_PROJECT_ID)
BIGQUERY_DATA_PROJECT_ID = os.environ.get('BIGQUERY_DATA_PROJECT_ID', GCLOUD_PROJECT_ID)
BIGQUERY_USER_DATA_PROJECT_ID = os.environ.get('BIGQUERY_USER_DATA_PROJECT_ID', GCLOUD_PROJECT_ID)
BIGQUERY_USER_MANIFEST_DATASET = os.environ.get('BIGQUERY_USER_MANIFEST_DATASET', 'dev_user_dataset')
BIGQUERY_USER_MANIFEST_TIMEOUT = int(os.environ.get('BIGQUERY_USER_MANIFEST_TIMEOUT', '7'))

# Log Names
# WEBAPP_LOGIN_LOG_NAME         = os.environ.get('WEBAPP_LOGIN_LOG_NAME', 'local_dev_logging')
# COHORT_CREATION_LOG_NAME      = os.environ.get('COHORT_CREATION_LOG_NAME', 'local_dev_logging')

BASE_URL = os.environ.get('BASE_URL', 'https://chernobyltissuebank-dev.cancer.gov')

# BigQuery cohort storage settings
BIGQUERY_COHORT_DATASET_ID = os.environ.get('BIGQUERY_COHORT_DATASET_ID', 'cohort_dataset')
BIGQUERY_COHORT_TABLE_ID = os.environ.get('BIGQUERY_COHORT_TABLE_ID', 'developer_cohorts')
MAX_BQ_INSERT = int(os.environ.get('MAX_BQ_INSERT', '500'))

database_config = {
    'default': {
        'ENGINE': os.environ.get('DATABASE_ENGINE', 'django.db.backends.mysql'),
        'HOST': os.environ.get('DATABASE_HOST', '127.0.0.1'),
        'NAME': os.environ.get('DATABASE_NAME', 'dev'),
        'USER': os.environ.get('DATABASE_USER', 'django-user'),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD')
    }
}
#print(database_config)

# On the build system, we need to use build-system specific database information
if os.environ.get('CI', None) is not None:
    database_config = {
        'default': {
            'ENGINE': os.environ.get('DATABASE_ENGINE', 'django.db.backends.mysql'),
            'HOST': os.environ.get('DATABASE_HOST_BUILD', '127.0.0.1'),
            'NAME': os.environ.get('DATABASE_NAME_BUILD', ''),
            'PORT': 3306,
            'USER': os.environ.get('DATABASE_USER_BUILD'),
            'PASSWORD': os.environ.get('MYSQL_ROOT_PASSWORD_BUILD')
        }
    }

DATABASES = database_config
DB_SOCKET = database_config['default']['HOST'] if 'cloudsql' in database_config['default']['HOST'] else None

IS_DEV = (os.environ.get('IS_DEV', 'False') == 'True')
IS_APP_ENGINE_FLEX = os.getenv('GAE_INSTANCE', '').startswith(APP_ENGINE_FLEX)
IS_APP_ENGINE = os.getenv('SERVER_SOFTWARE', '').startswith(APP_ENGINE)

VERSION = "{}.{}".format("local-dev", datetime.datetime.now().strftime('%Y%m%d%H%M'))

if exists(join(dirname(__file__), '../version.env')):
    dotenv.read_dotenv(join(dirname(__file__), '../version.env'))

APP_VERSION = os.environ.get("APP_VERSION", VERSION)

DEV_TIER = bool(DEBUG or re.search(r'^dev\.', APP_VERSION))

# If this is a GAE-Flex deployment, we don't need to specify SSL; the proxy will take
# care of that for us
if 'DB_SSL_CERT' in os.environ and not IS_APP_ENGINE_FLEX:
    DATABASES['default']['OPTIONS'] = {
        'ssl': {
            'ca': os.environ.get('DB_SSL_CA'),
            'cert': os.environ.get('DB_SSL_CERT'),
            'key': os.environ.get('DB_SSL_KEY')
        }
    }

# Default to localhost for the site ID
SITE_ID = 2

if IS_APP_ENGINE_FLEX or IS_APP_ENGINE:
    print("[STATUS] AppEngine Flex detected.", file=sys.stdout)
    SITE_ID = 3

# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.humanize',
    'anymail',
    'ctb',
    'offline',
    'adminrestrict',
    'axes',
    'donors',
    # 'searches',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'ctb.checkreqsize_middleware.CheckReqSize',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'adminrestrict.middleware.AdminPagesRestrictMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'ctb.team_only_middleware.TeamOnly',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'request_logging.middleware.LoggingMiddleware',
    'offline.middleware.OfflineMiddleware',
]

#############################
#  django-session-security  #
#############################
INSTALLED_APPS += ('session_security',)
SESSION_SECURITY_WARN_AFTER = int(os.environ.get('SESSION_SECURITY_WARN_AFTER', '540'))
SESSION_SECURITY_EXPIRE_AFTER = int(os.environ.get('SESSION_SECURITY_EXPIRE_AFTER', '600'))
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
MIDDLEWARE.append(
    # for django-session-security -- must go *after* AuthenticationMiddleware
    'session_security.middleware.SessionSecurityMiddleware',
)
###############################
# End django-session-security #
###############################

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue'
        },
    },
    'formatters': {
        'verbose': {
            'format': '[%(levelname)s] @%(asctime)s in %(module)s/%(process)d/%(thread)d - %(message)s'
        },
        'simple': {
            'format': '[%(levelname)s] @%(asctime)s in %(module)s: %(message)s'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console_dev': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'console_prod': {
            'level': 'DEBUG',
            'filters': ['require_debug_false'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console_dev', 'console_prod'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'main_logger': {
            'handlers': ['console_dev', 'console_prod'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'axes': {
            'handlers': ['console_dev', 'console_prod'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'allauth': {
            'handlers': ['console_dev', 'console_prod'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'google_helpers': {
            'handlers': ['console_dev', 'console_prod'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Force allauth to only use https
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
# ...but not if this is a local dev build
if IS_DEV:
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'http'

##########################
#  Start django-allauth  #
##########################
LOGIN_URL = 'two_factor:login'
LOGIN_REDIRECT_URL = '/extended_login/'
OTP_LOGIN_URL = 'two_factor:setup'
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = '/dashboard/'

INSTALLED_APPS += (
    'accounts',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    # 2FA support
    'django_otp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_email',  # <- if you want email capability.
    'two_factor',
    # 'two_factor.plugins.phonenumber',  # <- if you want phone number capability.
    'two_factor.plugins.email',  # <- if you want email capability.
)

ROOT_URLCONF = 'ctb.urls'

# Template Engine Settings
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # add any necessary template paths here
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'templates', 'accounts'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            # add any context processors here
            'context_processors': (
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.tz',
                'finalware.context_processors.contextify',
                'ctb.context_processor.additional_context',
            ),
            'debug': DEBUG,
        },
    },
]

##########################
#  Start django-allauth  #
##########################

AUTHENTICATION_BACKENDS = (
    # Prevent login hammering
    "axes.backends.AxesBackend",
    # Local account logins
    "django.contrib.auth.backends.ModelBackend",
    # Custom Authentication Backend, subclassed of allauth.account.auth_backends.AuthenticationBackend
    "accounts.auth_backends.CustomAuthenticationBackend",
    # "allauth.account.auth_backends.AuthenticationBackend",
)

ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = bool(os.environ.get('ACCOUNT_USERNAME_REQUIRED', 'False') == 'True')
ACCOUNT_EMAIL_VERIFICATION = os.environ.get('ACCOUNT_EMAIL_VERIFICATION', 'mandatory').lower()

ACCOUNT_EMAIL_SUBJECT_PREFIX = "[Chernobyl Tissue Bank] "
ACCOUNTS_PASSWORD_EXPIRATION = os.environ.get('ACCOUNTS_PASSWORD_EXPIRATION', 120)  # Max password age in days
ACCOUNTS_PASSWORD_HISTORY = os.environ.get('ACCOUNTS_PASSWORD_HISTORY', 5)  # Max password history kept
ACCOUNTS_ALLOWANCES = list(set(os.environ.get('ACCOUNTS_ALLOWANCES', '').split(',')))

##########################
#   End django-allauth   #
##########################

WSGI_APPLICATION = 'ctb.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 16,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'ctb.validators.PasswordComplexityValidator',
        'OPTIONS': {
            'min_length': 16,
            'special_char_list': '!@#$%^&*+:;?'
        }
    },
    {
        'NAME': 'ctb.validators.PasswordReuseValidator'
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

ACCOUNT_FORMS = {'reset_password': 'accounts.forms.CustomResetPasswordForm'}

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CSRF_COOKIE_SECURE = bool(os.environ.get('CSRF_COOKIE_SECURE', 'True') == 'True')
SESSION_COOKIE_SECURE = bool(os.environ.get('SESSION_COOKIE_SECURE', 'True') == 'True')
SECURE_SSL_REDIRECT = bool(os.environ.get('SECURE_SSL_REDIRECT', 'True') == 'True')

SECURE_REDIRECT_EXEMPT = []

if SECURE_SSL_REDIRECT:
    # Exempt the health check so it can go through
    SECURE_REDIRECT_EXEMPT = [r'^_ah/(vm_)?health$', ]

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_FOLDER = os.environ.get('MEDIA_FOLDER', 'uploads/')
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), '..', '..', MEDIA_FOLDER)
MEDIA_ROOT = os.path.normpath(MEDIA_ROOT)

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"

STATIC_ROOT = os.environ.get('STATIC_ROOT', '')


# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

GCS_STORAGE_URI = os.environ.get('GCS_STORAGE_URI', 'https://storage.googleapis.com/')

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    "static/",
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ.get('SECRET_KEY', '')

SECURE_HSTS_INCLUDE_SUBDOMAINS = (os.environ.get('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'True') == 'True')
SECURE_HSTS_PRELOAD = (os.environ.get('SECURE_HSTS_PRELOAD', 'True') == 'True')
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '3600'))

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

#########################################
# Cache Setting                         #
#########################################

if not IS_DEV:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "django_cache",
        }
    }
else:
    CACHES = {
        "default": {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
        }
    }

#########################################
# Axes Settings
#########################################
AXES_HANDLER = 'axes.handlers.cache.AxesCacheHandler' if not IS_DEV else 'axes.handlers.dummy.AxesDummyHandler'
AXES_META_PRECEDENCE_ORDER = [
    'HTTP_X_FORWARDED_FOR',
    'REMOTE_ADDR',
]
AXES_PROXY_COUNT = 1
AXES_COOLOFF_TIME = int(os.environ.get('AXES_COOLOFF_TIME', '5'))
AXES_USERNAME_FORM_FIELD = "email"
AXES_LOCKOUT_CALLABLE = "accounts.views.lockout"
# AXES_LOCKOUT_TEMPLATE = "accounts/account/lockout.html"
#########################################
# Request Logging
#########################################
REQUEST_LOGGING_MAX_BODY_LENGTH = int(os.environ.get('REQUEST_LOGGING_MAX_BODY_LENGTH', '1000'))
REQUEST_LOGGING_ENABLE_COLORIZE = bool(os.environ.get('REQUEST_LOGGING_ENABLE_COLORIZE', 'False') == 'True')

#########################################
#   MailGun Email Settings for requests #
#########################################
#
# These settings allow use of MailGun as a simple API call
#EMAIL_SERVICE_API_URL = os.environ.get('EMAIL_SERVICE_API_URL', '')

#EMAIL_SERVICE_API_KEY = os.environ.get('EMAIL_SERVICE_API_KEY', '')

#NOTIFICATION_EMAIL_FROM_ADDRESS = os.environ.get('NOTIFICATION_EMAIL_FROM_ADDRESS', 'noreply@isb-cgc.org')

#########################
# django-anymail        #
#########################

#########################
# django-smtp-email     #
#########################
#EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
#EMAIL_HOST = os.environ.get('EMAIL_SMTP_SERVER', '')
#EMAIL_PORT = os.environ.get('EMAIL_SERVICE_PORT', '')
#EMAIL_USE_TLS=True
#EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_SERVICE_PASSWORD', '')
#EMAIL_HOST_USERNAME = os.environ.get('EMAIL_SERVICE_USERNAME', '')

EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = os.environ.get('EMAIL_PORT', '')
EMAIL_USE_TLS=True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

DEFAULT_FROM_EMAIL=os.environ.get('DEFAULT_FROM_EMAIL', '')
NOTIFICATION_EMAIL_FROM_ADDRESS = DEFAULT_FROM_EMAIL
SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', '')

if os.environ.get('IS_GAE_DEPLOYMENT', 'False') != 'True':
    GOOGLE_APPLICATION_CREDENTIALS = join(dirname(__file__), '../{}{}'.format(SECURE_LOCAL_PATH, os.environ.get(
        'GOOGLE_APPLICATION_CREDENTIALS', '')))
    if not exists(GOOGLE_APPLICATION_CREDENTIALS):
        print("[ERROR] Google application credentials file wasn't found! Provided path: {}".format(
            GOOGLE_APPLICATION_CREDENTIALS))
        exit(1)

OAUTH2_CLIENT_ID = os.environ.get('OAUTH2_CLIENT_ID', '')
OAUTH2_CLIENT_SECRET = os.environ.get('OAUTH2_CLIENT_SECRET', '')



##############################
#   Start django-finalware   #
##############################
#
# This should only be done on a local system which is running against its own VM, or during CircleCI testing.
# Deployed systems will already have a site superuser so this would simply overwrite that user.
# NEVER ENABLE this in production!
#
if (IS_DEV and CONNECTION_IS_LOCAL) or IS_CIRCLE:
    INSTALLED_APPS += (
        'finalware',)

    SITE_SUPERUSER_USERNAME = os.environ.get('SITE_SUPERUSER_USERNAME', '')
    SITE_SUPERUSER_EMAIL = ''
    SITE_SUPERUSER_PASSWORD = os.environ.get('SITE_SUPERUSER_PASSWORD')
#
############################
#   End django-finalware   #
############################

CONN_MAX_AGE = 60

############################
#   METRICS SETTINGS
############################
SITE_GOOGLE_ANALYTICS = bool(os.environ.get('SITE_GOOGLE_ANALYTICS', None) is not None)
SITE_GOOGLE_ANALYTICS_TRACKING_ID = os.environ.get('SITE_GOOGLE_ANALYTICS_TRACKING_ID', '')
GOOGLE_SITE_VERIFICATION_CODE = os.environ.get('GOOGLE_SITE_VERIFICATION_CODE', '')
ADOBE_DTM_PATH = os.environ.get('ADOBE_DTM_PATH', None)
ADOBE_N_DAP_ANALYTICS = bool(ADOBE_DTM_PATH is not None)

# Rough max file size to allow for eg. barcode list upload, to prevent triggering RequestDataTooBig
FILE_SIZE_UPLOAD_MAX = 1950000
CTB_FORM_FILE_SIZE_UPLOAD_MAX = 65536
# DATA_UPLOAD_MAX_MEMORY_SIZE = 131072
# REQUEST_LOGGING_MAX_BODY_LENGTH = 5242880
# Explicitly check for known problems in descrpitions and names provided by users
BLACKLIST_RE = r'((?i)<script>|(?i)</script>|!\[\]|!!\[\]|\[\]\[\".*\"\]|(?i)<iframe>|(?i)</iframe>)'
BLANK_TISSUE_FILTERS = {'country': 'ukraine', 'patient_residency': 'both', 'patient_gender': 'both', 'dob': 'both'}
# ,
#                     'age_at_operation_min': '',
#                     'age_at_operation_max': '', 'age_at_exposure_min': '', 'age_at_exposure_max': ''}

BLANK_TISSUE_FILTER_CASE_COUNT = {
    'tissue': {
        'rna': {
            'normal': 2839,
            'tumour': 3034,
            'metastatic': 370
        },
        'dna': {
            'normal': 2827,
            'tumour': 3022,
            'metastatic': 370
        },
        'ffpe': {
            'normal': 1967,
            'tumour': 3691,
            'metastatic': 858

        }
    },
    'blood': {
        'dna': 2379,
        'serum': 2017,
        'blood': 2239
    },
    'total': 4052
}

GCP_APP_DOC_BUCKET = os.environ.get('GCP_APP_DOC_BUCKET', 'ctb-dev-app-doc-files')
CTB_APPLICATION_RECEIVER_EMAIL = os.environ.get('CTB_APPLICATION_RECEIVER_EMAIL', 'ctbWebAdmin@mail.nih.gov')
GOOGLE_SE_ID = os.environ.get('GOOGLE_SE_ID', None)
# print(GOOGLE_SE_ID)
if DEBUG and DEBUG_TOOLBAR:
    INSTALLED_APPS += ('debug_toolbar',)
    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware', )
    DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
    ]
    SHOW_TOOLBAR_CALLBACK = True
    INTERNAL_IP = (os.environ.get('INTERNAL_IP', ''),)

# AxesMiddleware should be the last middleware in the MIDDLEWARE list.
# It only formats user lockout messages and renders Axes lockout responses
# on failed user authentication attempts from login views.
# If you do not want Axes to override the authentication response
# you can skip installing the middleware and use your own views.
MIDDLEWARE.append('axes.middleware.AxesMiddleware', )
MIDDLEWARE.append('django_otp.middleware.OTPMiddleware', )
# LOGIN_URL = 'bogus'
# REDIRECT_FIELD_NAME = 'bogus'

# Log the version of our app
#print(EMAIL_HOST)
print("[STATUS] Application Version is {}".format(APP_VERSION))

###############################################################################333
# Cron job settings
###############################################################################333
#CONNECTION_NAME = os.environ.get('DATABASE_HOST', '127.0.0.1'),
#DB_USER = os.environ.get('DATABASE_USER', 'django-user'),
#DB_PASSWORD = os.environ.get('DATABASE_PASSWORD')
#DB_NAME = os.environ.get('DATABASE_NAME', 'dev'),


# mailgun api
#EMAIL_SERVICE_API_KEY = getenv("EMAIL_SERVICE_API_KEY")
#EMAIL_SERVICE_API_URL = getenv("EMAIL_SERVICE_API_URL")
#NOTIFICATION_EMAIL_FROM_ADDRESS = getenv("NOTIFICATION_EMAIL_FROM_ADDRESS")

#EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
#EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# website login url
CTB_LOGIN_URL = os.environ.get("CTB_LOGIN_URL")
#SUPPORT_EMAIL = getenv("SUPPORT_EMAIL", "ctb-support@isb-cgc.org")
#CTB_REVIEWER_EMAIL = getenv("CTB_REVIEWER_EMAIL", "elee@isb-cgc.org")

INSTALLED_APPS += (
    'django_cron',
)

CRONJOBS = [
     ('0 1 * * *', 'ctb.cron.cron_jobs.DailyManagementCronJob'),
    #'ctb.cron.cron_jobs.DailyManagementCronJob',  # 
]

#mysql_config_for_cloud_functions = {
    #'unix_socket': f'/cloudsql/{CONNECTION_NAME}',
    #'user': DB_USER,
    #'password': DB_PASSWORD,
    #'db': DB_NAME,
    #'charset': 'utf8mb4',
    #'cursorclass': pymysql.cursors.DictCursor
#}


#def send_ctb_email(to_list, subject, mail_content, bcc_ctb_reviewer=False):
#    bcc_list = ([CTB_APPLICATION_RECEIVER_EMAIL ] if bcc_ctb_reviewer else [])
#    return requests.post(
#        EMAIL_HOST_USER , #EMAIL_SERVICE_API_URL,
#        auth=("api", EMAIL_HOST_PASSWORD), ##EMAIL_SERVICE_API_KEY
#        data={"from": f"Chernobyl Tissue Bank no-reply <{NOTIFICATION_EMAIL_FROM_ADDRESS}>",
#              "to": to_list,
#              "bcc": bcc_list,
#              "subject": subject,
#              "html": mail_content})


mysql_config_for_cloud_functions = {
    'host': os.environ.get('DATABASE_HOST', 'localhost'),
    'user': os.environ.get('DATABASE_USER', 'django-user'),
    'password':  os.environ.get('DATABASE_PASSWORD'),
    'db':os.environ.get('DATABASE_NAME', 'ctb'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
}


def send_ctb_email(to_list, subject, mail_content, bcc_ctb_reviewer=False):
    bcc_list = ([CTB_APPLICATION_RECEIVER_EMAIL ] if bcc_ctb_reviewer else [])

    msg = MIMEMultipart()
    msg['From'] = f"Chernobyl Tissue Bank no-reply <{SUPPORT_EMAIL}>"
    msg['To'] = ", ".join(to_list)
    msg['Bcc'] = ", ".join(bcc_list)  # Bcc recipients are added to the headers to be included in the send
    msg['Subject'] = subject

    # Attach the HTML content
    msg.attach(MIMEText(mail_content, 'html'))
    # Convert the message to a string
    email_text = msg.as_string()

    # Send the email
    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD) 
        server.sendmail(SUPPORT_EMAIL, to_list + bcc_list, email_text)
        server.close()
  
    except Exception as e:
        print(f"Error: {e}")

