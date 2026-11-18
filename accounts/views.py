#
# Copyright 2023, Institute for Systems Biology
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
#
from __future__ import absolute_import
from allauth.account import views as account_views
from django.shortcuts import render, redirect
import datetime
import logging
from axes.helpers import get_failure_limit, get_client_username, get_cool_off, get_cool_off_iso8601

logger = logging.getLogger('main_logger')


def redirect_login_view(request):
    response = redirect('/account/login/')
    return response


def extended_logout_view(request):
    user = request.user
    response = account_views.logout(request)
    if request.method == 'POST' and user.is_authenticated:
        logger.info("[CTB LOGOUT] User {} logged out from the web application at {}".format(
            user.email, datetime.datetime.utcnow()))
    return response


def lockout(request, credentials, *args, **kwargs):
    status = 403
    context = {
        "failure_limit": get_failure_limit(request, credentials),
        "username": get_client_username(request, credentials) or "",
    }

    cool_off = get_cool_off(request)
    if cool_off:
        context.update(
            {
                "cooloff_time": get_cool_off_iso8601(
                    cool_off
                ),  # differing old name is kept for backwards compatibility
                "cooloff_timedelta": cool_off,
            }
        )
    logger.info("[CTB LOCKOUT] User {} is locked out due to too many login failures [{}].".format(context['username'],
                                                                                                  datetime.datetime.utcnow()))
    return render(request, 'accounts/account/lockout.html', context, status=status)
