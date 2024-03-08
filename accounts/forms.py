#
# Copyright 2015-2024, Institute for Systems Biology
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

from allauth.account.forms import ResetPasswordForm
from allauth.account.adapter import get_adapter
from allauth.account.utils import (
    filter_users_by_email,
)
from allauth.utils import (
    build_absolute_uri
)
from django.contrib.sites.shortcuts import get_current_site
from ctb.settings import SUPPORT_EMAIL
from django.urls import reverse


class CustomResetPasswordForm(ResetPasswordForm):
    def save(self, request, **kwargs):
        email = self.cleaned_data["email"]
        if not self.users:
            inactive_users = filter_users_by_email(email, is_active=False)
            if inactive_users:
                self._send_inactive_account_mail(request, email)
            else:
                self._send_unknown_account_mail(request, email)
        else:
            self._send_password_reset_mail(request, email, self.users, **kwargs)
        return email

    def _send_unknown_account_mail(self, request, email):
        signup_url = build_absolute_uri(request, reverse("account_signup"))
        context = {
            "current_site": get_current_site(request),
            "email": email,
            "help_email": SUPPORT_EMAIL,
            "request": request,
            "signup_url": signup_url,
        }
        get_adapter(request).send_mail("account/email/unknown_account", email, context)

    def _send_inactive_account_mail(self, request, email):
        context = {
            "current_site": get_current_site(request),
            "email": email,
            "help_email": SUPPORT_EMAIL,
            "request": request,
        }
        get_adapter(request).send_mail("account/email/inactive_account_reset", email, context)
