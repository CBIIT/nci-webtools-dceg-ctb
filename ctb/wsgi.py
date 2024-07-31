"""
WSGI config for ctb project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application
from ctb.cron.cron_job import schedule_task, daily_task

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ctb.settings')

schedule_task(60*10, daily_task)

application = get_wsgi_application()
