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
import sys
import datetime
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse, JsonResponse, FileResponse, Http404
from accounts.decorators import password_change_required
from .cron.fn_account_approval import account_approval
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json

debug = settings.DEBUG
logger = logging.getLogger('main_logger')


# The site's homepage
@never_cache
def landing_page(request):
    return render(request, 'ctb/landing.html')


# Displays the privacy policy
def privacy_policy(request):
    return render(request, 'ctb/privacy.html')


# Displays the search result page
def search(request):
    return render(request, 'ctb/search.html')


# User details page
@login_required
@password_change_required
def user_detail(request, user_id):
    if debug: logger.debug('Called ' + sys._getframe().f_code.co_name)

    if int(request.user.id) == int(user_id):

        user = User.objects.get(id=user_id)
        user_details = {'date_joined': user.date_joined, 'email': user.email, 'id': user.id,
                        'last_login': user.last_login, 'username': user.username}

        return render(request, 'ctb/user_detail.html',
                      {'user': user,
                       'user_details': user_details,
                       'unconnected_local_account': True
                       })
    else:
        return render(request, '403.html')


# Extended login view so we can track user logins, redirects to data exploration page
@password_change_required
def extended_login_view(request):
    try:
        user = User.objects.get(id=request.user.id)
        logger.info("[CTB LOGIN] User {} logged in to the web application at {}".format(user.email,
                                                                                   datetime.datetime.utcnow()))

    except Exception as e:
        logger.error("[ERROR] While attempting to log in:")
        logger.exception(e)
    return redirect(reverse('dashboard'))


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
def about(request):
    return render(request, 'ctb/about.html')


# For Researchers
def research(request):
    return render(request, 'ctb/research.html')


# research-projects
def research_projects(request):
    return render(request, 'ctb/research_projects.html')


# Contact
def contact(request):
    return render(request, 'ctb/contact.html')


# CTB Keyword Search
def ctb_search(request):
    if settings.GOOGLE_SE_ID:
        if request.method == 'POST':
            q_keyword = request.POST.get('q', '')
        elif request.method == 'GET':
            q_keyword = request.GET.get('q', '')
        else:
            q_keyword = ''
        return render(request, 'ctb/ctb_search.html', {'google_se_id':settings.GOOGLE_SE_ID, 'q_keyword': q_keyword})
    else:
        raise Http404()


# sitemap.xml
def sitemap(request):
    try:
        return FileResponse(open('static/sitemap.xml', 'rb'), content_type='text/xml')
    except FileNotFoundError:
        raise Http404()
    

# User details page
@csrf_exempt
@require_POST
def approve_account(request):
  # check if user_id is admin
    data = json.loads(request.body)
    user_email = data.get('user_email')
    is_approved = data.get('is_approved')
    admin_token = data.get('admin_token')
    request_data = {'admin_token': admin_token, 'user_email': user_email, 'is_approved': is_approved}
    approval_status = account_approval(request_data)
    status =approval_status.get('code')
    msg= approval_status.get('message')
    print(status,msg)

    if status == 200:
        if is_approved:
           return JsonResponse({'message':"The account has been approved"})
        else:
           return JsonResponse({'message':"The account has been disapproved"})
    else:
        return JsonResponse({'status': status, 'message': msg}, status=status)

    

 
