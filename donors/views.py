###
# Copyright 2015-2022, Institute for Systems Biology
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

from django.shortcuts import render, redirect
from django.core.mail import send_mail
# from django.urls import reverse
from django.http import JsonResponse
from .metadata_count import get_sample_case_counts, get_clinical_case_counts, get_driver_case_counts
from .models import Filter
import urllib


def get_saved_searches(owner):
    saved_search_list = []
    user_filter_object_list = Filter.get_list(owner)
    for u_filter in user_filter_object_list:
        saved_search_list.append(
            {
                'filter_id': u_filter.id,
                'name': u_filter.name,
                'search_type': u_filter.search_type,
                'case_count': u_filter.case_count,
                'filter_encoded_url': u_filter.value
            }
        )
    return saved_search_list


def dashboard(request):
    message = request.POST.get('message')
    # saved_search_list = get_saved_searches(request.user)
    return render(request, 'donors/dashboard.html',
                  {'request': request, 'message': message})
                  # {'request': request, 'saved_search_list': saved_search_list})


# My Saved Searches
def saved_searches(request):
    # saved_search_list = get_saved_searches(request.user)
    return render(request, 'donors/saved_searches.html',
                  {'request': request})
                  # {'request': request, 'saved_search_list': saved_search_list})


def get_search_list(request):
    return JsonResponse(get_saved_searches(request.user), safe=False)


def delete_filters(request, filter_id):
    owner = request.user
    message = Filter.destroy(filter_id=filter_id, owner=owner)
    return JsonResponse(message)


def save_filters(request):
    filters = get_filters(request, for_save=True)
    name = filters.get('title', 'Untitled')
    if 'title' in filters:
        filters.pop('title')
    search_type = filters.get('search_type', 'Biosample');
    if 'search_type' in filters:
        filters.pop('search_type')
    case_count = filters.get('total', 0)
    if 'total' in filters and search_type != 'Clinic':
        filters.pop('total')
    if 'filter_encoded_url' in filters:
        filter_encoded_url = filters.get('filter_encoded_url', 0)
        filters.pop('filter_encoded_url')
    else:
        filter_encoded_url = ('?'+urllib.parse.urlencode(filters, True))
    Filter.create(name, search_type, case_count, filter_encoded_url, request.user)
    return JsonResponse({'message': 'Your search \'' + name + '\' has been saved.'})


def search_clinical(request):
    filters = get_filters(request)
    total = filters.get('total', 5516)
    if 'csrfmiddlewaretoken' in filters:
        filters.pop('csrfmiddlewaretoken')
    case_counts = get_clinical_case_counts(filters)
    clinic_search_result = {
        'total': total,
        'avail': case_counts
    }
    return render(request, 'donors/clinical_search_facility_result.html',
                  {'request': request, 'clinic_search_result': clinic_search_result,
                   'filter_encoded_url': '?' + urllib.parse.urlencode(filters, True)})


# Driver Search Facility
def driver_search_facility(request):
    filters = get_filters(request)
    total_filtered_case_count, counts = get_driver_case_counts(filters)
    return render(request, 'donors/driver_search_facility.html',
                  {'request': request, 'counts': counts, 'total_filtered_case_count': total_filtered_case_count,
                   'filter_encoded_url': '?' + urllib.parse.urlencode(filters, True)})


def search_tissue_samples(request):
    return render(request, 'donors/search_tissue_samples.html', {'request': request})


def get_filters(request, for_save=False):
    sample_filters = {}
    request_method = request.GET if request.method == 'GET' else request.POST
    for key in request_method:
        if key.endswith('[]'):
            sample_filters[key] = request_method.getlist(key)
        elif for_save or key != 'title':
            val = request_method.get(key)
            if val:
                sample_filters[key] = request_method.get(key)
    return sample_filters


def filter_tissue_samples(request):
    filters = get_filters(request)
    case_counts = get_sample_case_counts(filters)
    return JsonResponse(case_counts)


# Clinical Search Facility
def clinical_search_facility(request):
    sample_filters = get_filters(request)
    return render(request, 'donors/clinical_search_facility.html',
                  {'request': request, 'sample_filters': sample_filters})


def make_application(request):
    return render(request, 'donors/application_form.html', {'request': request})


def application_submit(request):
    pi_email = request.POST.get('pi_email')
    if pi_email:
        send_mail(
            '[Chernobyl Tissue Bank] Application from Chernobyl Tissue Bank',
            'Application has been submitted.',
            pi_email,

            ['elee@systemsbiology.org', pi_email],
            fail_silently=False,
        )
        main_message = {
            'success': 'Application has been submitted. A copy of the application has been sent to {email}.'.format(
                email=pi_email)
        }
    else:
        error_message = 'No email has been provided.'
        main_message = {
            'error': 'There has been an error while submitting your application: {error_message} Please try again.'.format(
                error_message=error_message)
        }
    return render(request, 'donors/application_post_submit.html', {'request': request, 'main_message': main_message})
