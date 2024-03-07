###
# Copyright 2015-2019, Institute for Systems Biology
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

from builtins import object
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect
from django.conf import settings
from functools import reduce
from allauth.account.models import EmailAddress
import re


# Requires:
# RESTRICT_ACCESS: boolean, toggles checking of access privs; note that the default of RESTRICT_ACCESS is **True**
# RESTRICTED_ACCESS_GROUPS: string list, names of user groups to allow access; access is OR'd (only one required)
class TeamOnly(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.RESTRICT_ACCESS:
            # Allow access to the landing page, and Google logins, because otherwise we'll have no idea who
            # this even is.
            if request.path != '/' and not re.match('/?accounts(/google)?/log(out|in)/?.*', request.path, re.I):
                if request.user.is_authenticated:
                    message = None
                    if not (request.user.is_superuser and re.match('/admin/?.*', request.path, re.I)):
                        if not EmailAddress.objects.filter(
                                user=request.user, verified=True
                        ).exists():
                            message = "We have sent an e-mail to you for verification. Please <a href=\'#logout-modal\' data-bs-toggle=\'modal\' data-bs-target=\'#logout-modal\'>log out</a> and follow the link provided to finalize the signup process. If you have any questions, please email us at <a href='mailto:ctb-support@isb-cgc.org'>ctb-support@isb-cgc.org</a>"
                        elif not request.user.groups.filter(
                                reduce(lambda q, g: q | Q(name__icontains=g), settings.RESTRICTED_ACCESS_GROUPS,
                                       Q())).exists():
                            message = "Your account application will need to be evaluated before an account can be approved. You will get an email about approval. If you have any questions, please email us at <a href='mailto:ctb-support@isb-cgc.org'>ctb-support@isb-cgc.org</a>"
                    if message:
                        messages.warning(request, message)
                        return redirect('landing_page')
        response = self.get_response(request)
        return response
