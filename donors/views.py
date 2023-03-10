###
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
###

from django.conf import settings
from django.shortcuts import render
# from django.core.mail import send_mail
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.template.loader import get_template
from .metadata_count import get_sample_case_counts, get_clinical_case_counts, get_driver_case_counts
from .models import Filter
from .utils import upload_blob
import urllib
import pytz
from io import BytesIO
from xhtml2pdf import pisa
from datetime import datetime


@login_required
def dashboard(request):
    message = request.POST.get('message')
    return render(request, 'donors/dashboard.html',
                  {'request': request, 'message': message})


# My Saved Searches
@login_required
def saved_searches(request):
    return render(request, 'donors/saved_searches.html',
                  {'request': request})


@login_required
def get_search_list(request):
    return JsonResponse(get_saved_searches(request.user), safe=False)


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


@login_required
def delete_filters(request, filter_id):
    owner = request.user
    message = Filter.destroy(filter_id=filter_id, owner=owner)
    return JsonResponse(message)


@login_required
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


@login_required
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
@login_required
def driver_search_facility(request):
    filters = get_filters(request)
    total_filtered_case_count, counts = get_driver_case_counts(filters)
    return render(request, 'donors/driver_search_facility.html',
                  {'request': request, 'counts': counts, 'total_filtered_case_count': total_filtered_case_count,
                   'filter_encoded_url': '?' + urllib.parse.urlencode(filters, True)})


@login_required
def search_tissue_samples(request):
    return render(request, 'donors/search_tissue_samples.html', {'request': request})


@login_required
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


@login_required
def filter_tissue_samples(request):
    filters = get_filters(request)
    case_counts = get_sample_case_counts(filters)
    return JsonResponse(case_counts)


# Clinical Search Facility
@login_required
def clinical_search_facility(request):
    sample_filters = get_filters(request)
    return render(request, 'donors/clinical_search_facility.html',
                  {'request': request, 'sample_filters': sample_filters})


@login_required
def make_application(request):
    return render(request, 'donors/application_form.html', {'request': request})


@login_required
def application_submit(request):
    datetime_now = datetime.now(pytz.timezone('US/Eastern'))
    application_content = {
        "first_name": request.POST.get('first-name'),
        "last_name": request.POST.get('last-name'),
        "pi_title": request.POST.get('pi-title'),
        "institution": request.POST.get('institution'),
        "address1": request.POST.get('address1'),
        "address2": request.POST.get('address2'),
        "zipcode": request.POST.get('zipcode'),
        "country": request.POST.get('country'),
        "phone": request.POST.get('phone'),
        "email": request.POST.get('email'),
        "prj_title": request.POST.get('prj-title'),
        "project_summary": request.POST.get('project-summary'),
        "project_summary_file": request.POST.get('project-summary-file'),
        "overview": request.POST.get('overview'),
        "aims": request.POST.get('aims'),
        "experience": request.POST.get('experience'),
        "methods": request.POST.get('methods'),
        "submitted_datetime": datetime_now.strftime("%-m/%-d/%Y %H:%M"),
        "pdf": True
    }
    user_email = request.user.email
    error_message = None
    if not user_email:
        error_message = 'No email has been provided.'
    else:
        template = get_template('donors/intake_form_wrapper.html')
        html_template = template.render(application_content)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html_template.encode("utf-8")), result)
        if pdf.err:
            error_message = "Unable to generate an application file."
        else:
            bucket_name = settings.GCP_APP_DOC_BUCKET
            date_str = datetime_now.strftime("%-y_%m_%d_%H%M%S")
            user_str = user_email.split('@')[0].upper()
            destination_file_name = f"CTB_APPLICATION_{date_str}_{user_str}.pdf"
            upload_result = upload_blob(bucket_name, destination_file_name, result, content_type='application/pdf')
            if upload_result.get('err', None):
                error_message = upload_result.get('err')
            # else:
            #     send_mail(
            #         '[Chernobyl Tissue Bank] Application from Chernobyl Tissue Bank',
            #         'Application has been submitted.',
            #         user_email,
            #         [settings.CTB_APPLICATION_RECEIVER_EMAIL, user_email],
            #         fail_silently=False,
            #     )

    if error_message:
        main_message = {
            'error': f'There has been an error while submitting your application: {error_message} Please try again.'
        }
    else:
        main_message = {
            'success': f'Application has been submitted. A copy of the application has been sent to {user_email}.'
        }
    return render(request, 'donors/application_post_submit.html', {'request': request, 'main_message': main_message})
