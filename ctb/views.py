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

# About the Project > Aims of the Project
def aims(request):
    return render(request, 'ctb/aims.html', {
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
def about_page(request):
    return render(request, 'ctb/about.html', {'request': request})

# Fact Sheet
def fact_sheet(request):
    return render(request, 'ctb/fact_sheet.html', {'request': request})

# Management of the Project
def management_page(request):
    return render(request, 'ctb/management_page.html', {'request': request})

# For Researchers
def researchers_page(request):
    return render(request, 'ctb/researchers_page.html', {'request': request})

# Access to materials
def access_to_materials(request):
    return render(request, 'ctb/access_to_materials.html', {'request': request})

# research-projects
def research_projects(request):
    return render(request, 'ctb/research_projects.html', {'request': request})

# research-projects 2001-2009
def research_projects_2001_2009(request):
    return render(request, 'ctb/research_projects_2001_2009.html', {'request': request})

# research-projects 2010-2019
def research_projects_2010_2019(request):
    return render(request, 'ctb/research_projects_2010_2019.html', {'request': request})

# Schema Review of Applications
def schema_review_of_applications(request):
    return render(request, 'ctb/schema_review_of_applications.html', {'request': request})


# Material Available
def material_available(request):
    return render(request, 'ctb/material_available.html', {'request': request})


# #Resources
# def resources(request):
#     return render(request, 'ctb/resources.html', {'request': request})


# Bibliography: Publications using CTB samples and data
def bibliography(request):
    return render(request, 'ctb/bibliography.html', {'request': request})

# Useful links: Links to further information on the Chernobyl accident
def useful_links(request):
    return render(request, 'ctb/useful_links.html', {'request': request})

# Useful podcasts and videos: Podcasts and Videos by CTB project participants
def podcasts_and_videos(request):
    return render(request, 'ctb/podcasts_and_videos.html', {'request': request})

# Latest News
def news(request):
    return render(request, 'ctb/news.html', {'request': request})

# Latest News
def contact(request):
    return render(request, 'ctb/contact.html', {'request': request})

# Dashboard
def dashboard(request):
    saved_search_list = [
        {'name': 'Follicular Female',
         'type': 'Biosample',
         'results': 29,
         'proceed': 'driver'},
        {'name': 'Example 2',
         'type': 'Biosample',
         'results': 42,
         'proceed': 'driver'},
    ]
    return render(request, 'ctb/dashboard.html', {'request': request, 'saved_search_list': saved_search_list})

#temporary data

    return render(request, 'ctb/saved_searches.html', {'request': request, 'saved_search_list': saved_search_list})

# Search Tissue Samples
def search_tissue_samples(request):
    # hard coded data
    tissue = {
        'rna': {
            'normal': 323,
            'tumor': 534,
            'metastatic': 115
        },
        'dna': {
            'normal': 634,
            'tumor': 274,
            'metastatic': 284
        },
        'ffpe': {
            'normal': 26,
            'tumor': 734,
            'metastatic': 623
        }
    }
    blood ={
        'dna': 23,
        'serum':32
    }
    total = 735
    return render(request, 'ctb/search_tissue_samples.html', {'request': request, 'tissue': tissue, 'blood': blood, 'total': total})

# My Saved Searches
def saved_searches(request):
    #temporary data
    saved_search_list = [
        {'name': 'Follicular Female',
         'type': 'Biosample',
         'results': 29,
         'proceed': 'driver'},
        {'name': 'Example 2',
         'type': 'Biosample',
         'results': 42,
         'proceed': 'driver'},
    ]
    return render(request, 'ctb/saved_searches.html', {'request': request, 'saved_search_list': saved_search_list})


# Clinical Search Intro
def search_clinical(request):
    return render(request, 'ctb/search_clinical.html', {'request': request})

# Clinical Search Facility
def clinical_search_facility(request):
    return render(request, 'ctb/clinical_search_facility.html', {'request': request})

# Driver Search Facility
def driver_search_facility(request):
    return render(request, 'ctb/driver_search_facility.html', {'request': request})

# Driver Search Facility
def clinical_search_facility_results(request):
    return render(request, 'ctb/clinical_search_facility_results.html', {'request': request})

