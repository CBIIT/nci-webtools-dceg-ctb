"""
WSGI config for ctb project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os
from whitenoise import WhiteNoise
from django.conf import settings
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ctb.settings')

application = get_wsgi_application()
if settings.DAILY_MANAGEMENT_ENABLED:
    from ctb.cron.cron_job import schedule_task, daily_task
    schedule_task(60*60*24, daily_task)

application = WhiteNoise(application, root=os.path.join(settings.BASE_DIR, "static"), prefix="/static")
