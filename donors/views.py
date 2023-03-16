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
from django.core.mail import EmailMessage
from django.shortcuts import render
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
import logging

logger = logging.getLogger('main_logger')


@login_required
def dashboard(request):
    message = request.POST.get('message')
    return render(request, 'donors/dashboard.html', {'message': message})


# My Saved Searches
@login_required
def saved_searches(request):
    return render(request, 'donors/saved_searches.html')


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
        filter_encoded_url = ('?' + urllib.parse.urlencode(filters, True))
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
                  {'clinic_search_result': clinic_search_result,
                   'filter_encoded_url': '?' + urllib.parse.urlencode(filters, True)})


# Driver Search Facility
@login_required
def driver_search_facility(request):
    filters = get_filters(request)
    total_filtered_case_count, counts = get_driver_case_counts(filters)
    return render(request, 'donors/driver_search_facility.html',
                  {'counts': counts, 'total_filtered_case_count': total_filtered_case_count,
                   'filter_encoded_url': '?' + urllib.parse.urlencode(filters, True)})


@login_required
def search_tissue_samples(request):
    return render(request, 'donors/search_tissue_samples.html')


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
                  {'sample_filters': sample_filters})


@login_required
def make_application(request):
    return render(request, 'donors/application_form.html')


@login_required
def application_submit(request):
    datetime_now = datetime.now(pytz.timezone('US/Eastern'))
    user_email = request.user.email
    try:
        if not user_email:
            raise Exception('No email has been provided.')

        if request.method == 'POST':
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
                "overview": request.POST.get('overview'),
                "aims": request.POST.get('aims'),
                "experience": request.POST.get('experience'),
                "methods": request.POST.get('methods'),
                "submitted_datetime": datetime_now.strftime("%-m/%-d/%Y %H:%M %Z"),
                "pdf": True
            }
            is_file_option_on = (request.POST.get('upload_option') == 'on')
            uploaded_blob = None
            date_str = datetime_now.strftime("%-y_%m_%d_%H%M%S")
            user_str = user_email.split('@')[0].upper()
            destination_file_name = f"CTB_APPLICATION_{date_str}_{user_str}.pdf"

            if is_file_option_on and request.FILES:
                # uploaded project summary file
                uploaded_blob = request.FILES["project-summary-file"]
                if uploaded_blob.size > settings.CTB_FORM_FILE_SIZE_UPLOAD_MAX:
                    raise Exception('Project summary file you are trying to upload is too large.')
                application_content["project_summary"] = f"[Attached file: {destination_file_name}]"
                file_extension = uploaded_blob.name.split('.')[-1]
                destination_att_file_name = f"CTB_APPLICATION_{date_str}_{user_str}_ATTACHMENT.{file_extension}"
            template = get_template('donors/intake_form_wrapper.html')
            html_template = template.render(application_content)
            result = BytesIO()
            pdf = pisa.pisaDocument(BytesIO(html_template.encode("utf-8")), result)
            if pdf.err:
                raise Exception('Unable to generate an application file.')

            # upload application to cloud storage
            bucket_name = settings.GCP_APP_DOC_BUCKET
            upload_blob(bucket_name, destination_file_name, result, content_type='application/pdf')
            if is_file_option_on and uploaded_blob:  # attach a copy of the uploaded project summary file
                upload_blob(bucket_name, destination_att_file_name, uploaded_blob,
                            content_type=uploaded_blob.content_type)
            # notification email set up
            mail = EmailMessage(
                '[Chernobyl Tissue Bank] Application Submitted',
                '''
            
            A Chernobyl Tissue Bank application has been submitted.
            A copy of the application is attached to this email for you to review.
            Please contact feedback@isb-cgc.org if you have any questions or concerns.
            
            ISB-CGC Team''',
                settings.NOTIFICATION_EMAIL_FROM_ADDRESS,
                [settings.CTB_APPLICATION_RECEIVER_EMAIL, user_email])
            # attach a copy of the application in pdf to the email after rewinding result (ByteIO)
            result.seek(0)
            mail.attach(destination_file_name, result.read(), 'application/pdf')
            if is_file_option_on and uploaded_blob:
                # attach a copy of the uploaded project summary file to the email
                mail.attach(destination_att_file_name, uploaded_blob.open().read(), uploaded_blob.content_type)
            mail.send()
        else:  # method not POST
            raise Exception('Invalid request was made.')
    except Exception as e:
        return render(request, 'donors/application_post_submit.html', {'request': request,
                                                                       'error': e})
    return render(request, 'donors/application_post_submit.html',
                  {
                      'request': request,
                      'success': f'Application is submitted and a copy of the application is sent to {user_email}.'
                  })

