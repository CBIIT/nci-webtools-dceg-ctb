###
# Copyright 2024, Institute for Systems Biology
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

import logging
import datetime
from pytz import timezone
from django.conf import settings
from django.core.mail import EmailMessage
from django.contrib.auth.signals import user_login_failed, user_logged_in
from allauth.account.signals import password_changed, email_confirmed, password_reset, user_signed_up
from django.dispatch import receiver
from allauth.account.decorators import verified_email_required

# debug = settings.DEBUG
logger = logging.getLogger('main_logger')



# @receiver(password_changed)
# def password_changed_callback(**kwargs):
#     print('password changed ')
#     # print(user)
#     try:
#         logger.info('[CTB PASSWORD CHANGED] Password changed')
#         # logger.info('[CTB PASSWORD CHANGED] Password changed for: {credentials}'.format(user=user))
#     except Exception as e:
#         logger.exception(e)


# @receiver(password_reset)
# def password_reset_callback(credentials, **kwargs):
#     print('password_reset')
#     try:
#         logger.info('[CTB PASSWORD RESET] Password is reset for: {credentials}'.format(credentials=credentials))
#     except Exception as e:
#         logger.exception(e)


@receiver(email_confirmed)
def email_confirmed_callback(sender, email_address, **kwargs):
    try:
        logger.info(f'[CTB EMAIL CONFIRMED] {email_address}')
        timestamp = datetime.datetime.now(timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S %Z")

        # send out a notification email to CTB_APPLICATION_RECEIVER team about the new account
        notification_mail_to_ctb_team = EmailMessage(
            '[Chernobyl Tissue Bank] A new account was created',
            f'''This is an email to inform you that a new user account was created for CTB:
        
    User account email: {email_address}
    Time of Application: {timestamp}
        
Please evaluate the account above and inform the ISB-CGC team whether to approve or disapprove it.
The user will not be able to access the biorepository until the account is approved.
A disapproved account will be deactivated, and cannot be reused again without an admin's assistance.
        
        
Sincerely,
Chernobyl Tissue Bank Team''',
            settings.NOTIFICATION_EMAIL_FROM_ADDRESS,
            [settings.CTB_APPLICATION_RECEIVER_EMAIL])
        notification_mail_to_ctb_team.send()

        notification_mail_to_user = EmailMessage(
            '[Chernobyl Tissue Bank] Your account was created',
            f'''Hello {email_address},

This is an email to inform you that your Chernobyl Tissue Bank account was created, but not yet approved. Please note that your account will need to be evaluated before it can be approved.
We will send you an email about approval soon.

If you have any questions, please send us an email to ctb-support@isb-cgc.org, and we will get back to you as soon as we can.


Sincerely,
Chernobyl Tissue Bank Team''',
            settings.NOTIFICATION_EMAIL_FROM_ADDRESS,
            [email_address])
        notification_mail_to_user.send()
    except Exception as e:
        logger.error("[ERROR] While attempting to send a new account notification email")
        logger.exception(e)


@receiver(user_logged_in)
@verified_email_required
def user_logged_in_callback(*args, **kwargs):
    try:
        logger.info(f"[CTB LOGIN] user_logged_in_callback")
    except Exception as e:
        logger.exception(e)


@receiver(user_signed_up)
def user_signed_up_callback(sender, request, user, **kwargs):
    try:
        logger.info(f'[CTB SIGN UP] A new user account \'{user}\' was created')
    except Exception as e:
        logger.exception(e)


@receiver(user_login_failed)
def user_login_failed_callback(sender, credentials, **kwargs):
    try:
        logger.info('[CTB LOGIN] Login FAILED for: {credentials}'.format(credentials=credentials))
    except Exception as e:
        logger.exception(e)

