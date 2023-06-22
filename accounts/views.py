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
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from .models import *
logger = logging.getLogger('main_logger')


def redirect_login_view(request):
    response = redirect('/account/login/')
    return response


def lockout_view(request):
    return render(request, 'account/lockout.html', {'axes_cooloff_time': settings.AXES_COOLOFF_TIME})


@login_required
def extended_logout_view(request):
    try:
        response = account_views.logout(request)
    except Exception as e:
        logger.error("[ERROR] While attempting to log out:")
        logger.exception(e)
        messages.error(request, "There was an error while attempting to log out - please contact ctb-support@isb-cgc.org")
        return redirect(reverse('user_detail', args=[request.user.id]))
    return response
