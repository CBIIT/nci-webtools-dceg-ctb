###
# Copyright 2015-2021, Institute for Systems Biology
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

from builtins import str
import time
import json
import logging
import sys
import datetime
import re
import copy

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages

from google_helpers.stackdriver import StackDriverLogger
#from cohorts.models import Cohort, Cohort_Perms
#from allauth.socialaccount.models import SocialAccount
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver

debug = settings.DEBUG
logger = logging.getLogger('main_logger')

BQ_ATTEMPT_MAX = 10
WEBAPP_LOGIN_LOG_NAME = settings.WEBAPP_LOGIN_LOG_NAME


# The site's homepage
@never_cache
def landing_page(request):
    # return redirect('account_login')
    return render(request, 'ctb/landing.html', {
        'request': request,
    })


# Displays the privacy policy
def privacy_policy(request):
    return render(request, 'ctb/privacy.html', {'request': request, })


# Displays the privacy policy
def search(request):
    return render(request, 'ctb/search.html', {'request': request, })


# User details page
@login_required
def user_detail(request, user_id):
    if debug: logger.debug('Called ' + sys._getframe().f_code.co_name)

    if int(request.user.id) == int(user_id):

        user = User.objects.get(id=user_id)
        # try:
        #     social_account = SocialAccount.objects.get(user_id=user_id, provider='google')
        # except Exception as e:
        #     # This is a local account
        #     social_account = None
        user_details = {
            'date_joined':  user.date_joined,
            'email':        user.email,
            'id':           user.id,
            'last_login':   user.last_login
        }

        # if social_account:
        #     user_details['extra_data'] = social_account.extra_data if social_account else None
        #     user_details['first_name'] = user.first_name
        #     user_details['last_name'] = user.last_name
        # else:
        user_details['username'] = user.username

        return render(request, 'ctb/user_detail.html',
                      {'request': request,
                       'user': user,
                       'user_details': user_details,
                       'unconnected_local_account': True #bool(social_account is None),
                       #'social_account': bool(social_account is not None)
                       })
    else:
        return render(request, '403.html')


@receiver(user_login_failed)
def user_login_failed_callback(sender, credentials, **kwargs):
    try:
        # Write log entry
        st_logger = StackDriverLogger.build_from_django_settings()
        log_name = WEBAPP_LOGIN_LOG_NAME
        st_logger.write_text_log_entry(
            log_name,
            '[WEBAPP LOGIN] Login FAILED for: {credentials}'.format(credentials=credentials)
        )

    except Exception as e:
        logger.exception(e)


# Extended login view so we can track user logins, redirects to data exploration page
def extended_login_view(request):
    try:
        # Write log entry
        st_logger = StackDriverLogger.build_from_django_settings()
        log_name = WEBAPP_LOGIN_LOG_NAME
        user = User.objects.get(id=request.user.id)
        st_logger.write_text_log_entry(
            log_name,
            "[WEBAPP LOGIN] User {} logged in to the web application at {}".format(user.email,
                                                                                   datetime.datetime.utcnow())
        )

    except Exception as e:
        logger.exception(e)

    return redirect(reverse('explore_data'))


# Health check callback
#
# Because the match for vm_ is always done regardless of its presense in the URL
# we must always provide an argument slot for it
def health_check(request, match):
    return HttpResponse('')


# Callback for recording the user's agreement to the warning popup
def warn_page(request):
    request.session['seenWarning'] = True;
    return JsonResponse({'warning_status': 'SEEN'}, status=200)


# About page
def about_page(request):
    return render(request, 'ctb/about.html', {'request': request})
