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
from django.http import HttpResponse

from allauth.account import views as account_views
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from django.core.mail import send_mail
from .models import *
from auth.auth import validate_request

logger = logging.getLogger('main_logger')


@login_required
def extended_logout_view(request):
    try:
        response = account_views.logout(request)
    except Exception as e:
        logger.error("[ERROR] While attempting to log out:")
        logger.exception(e)
        messages.error(request, "There was an error while attempting to log out - please contact feedback@isb-cgc.org")
        return redirect(reverse('user_detail', args=[request.user.id]))
    return response


def manage_inactive_accounts(request):
    validate_resp = validate_request(request)
    if validate_resp.get('code') != 200:
        return HttpResponse(validate_resp['message'], status=validate_resp['code'])
    warn_user_list = []
    deactivate_user_list = []
    inactive_user_list = User.objects.filter(is_active=True, is_staff=False)
    logger.info("[STATUS] scanning for all inactive accounts.")
    for inactive_user in inactive_user_list:
        user_last_login_date = inactive_user.last_login.date()
        if user_last_login_date == warning_last_login_date_utc():
            warn_user_list.append(inactive_user)
        elif user_last_login_date == expiry_last_login_date_utc():
            deactivate_user_list.append(inactive_user)
    # send a warning email to users
    for warn_user in warn_user_list:
        logger.info("[STATUS] Sending a notification email to {user_email}.".format(user_email=warn_user.email))
        send_mail(
            '[Chernobyl Tissue Bank] Your account is expiring in {} days'.format(settings.EXPIRATION_WARNING_DAYS),
            '''
            Dear {user_email},

            Your CTB will expire on {expiration_date} ({warning_period} days from today).
            Please visit {website} and login to your account before it expires, to ensure uninterrupted access.

            If you need assistance with your login then please email us at feedback@isb-cgc.org

            Sincerely,
            ISB-CGC Team'''.format(
                user_email=warn_user.email, expiration_date=warn_expiration_date_utc(),
                warning_period=settings.EXPIRATION_WARNING_DAYS,
                website=request.build_absolute_uri('/accounts/login/')),
            settings.NOTIFICATION_EMAIL_FROM_ADDRESS,
            ['elee@systemsbiology.org', warn_user.email],
            fail_silently=False,
        )
    for deactivate_user in deactivate_user_list:
        logger.info("[STATUS] deactivating account {user_email}.".format(user_email=deactivate_user.email))
        deactivate_account(deactivate_user.id)
        send_mail(
            '{account_email_subject_prefix} Your account has been deactivated'.format(
                account_email_subject_prefix=settings.ACCOUNT_EMAIL_SUBJECT_PREFIX),
            '''
            Dear {user_email},

            Your CTB account has been deactivated due to {max_inactive_period} days of inactivity.
            Please contact {support_email} in order to reactivate your account.
            If you would like more information regarding CTB policies on account deactivation, please contact {support_email}.

            Sincerely,
            ISB-CGC Team'''.format(
                user_email=deactivate_user.email, max_inactive_period=settings.MAX_INACTIVE_PERIOD, support_email=settings.SUPPORT_EMAIL),
                settings.NOTIFICATION_EMAIL_FROM_ADDRESS,
            ['elee@systemsbiology.org', deactivate_user.email],
            fail_silently=False,
        )

    return HttpResponse("manage_inactive_accounts called.", status=200)
