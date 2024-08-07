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
from django.http import JsonResponse, HttpResponse
from django_otp.decorators import otp_required
from django.template.loader import get_template
from .metadata_count import get_sample_case_counts, get_clinical_case_counts, get_driver_case_counts
from .models import Filter, Submissions
from .utils import upload_blob, read_blob
import urllib
import pytz
from io import BytesIO
from xhtml2pdf import pisa
from datetime import datetime
import logging
from accounts.decorators import password_change_required
from ctb.settings import TIER,ACCOUNT_EMAIL_SUBJECT_PREFIX 

logger = logging.getLogger('main_logger')

@otp_required
@password_change_required
def dashboard(request):
    message = request.POST.get('message')
    return render(request, 'donors/dashboard.html', {'message': message})


# My Saved Searches
@otp_required
@password_change_required
def saved_searches(request):
    return render(request, 'donors/saved_searches.html')


@otp_required
def get_search_list(request):
    return JsonResponse(get_saved_searches(request.user), safe=False)


@otp_required
def get_submissions_list(request):
    return JsonResponse(get_my_application_list(request.user), safe=False)


def get_my_application_list(owner):
    my_application_list = []
    user_application_object_list = Submissions.get_list(owner)
    for u_filter in user_application_object_list:
        my_application_list.append(
            {
                'submitted_date': datetime.strftime(u_filter.submitted_date, '%b %-d %Y at %-I:%M %p (%Z)'),
                'submission_id': u_filter.id,
                'entry_form_path': int(bool(u_filter.entry_form_path)),
                'summary_file_path': int(bool(u_filter.summary_file_path))
            }
        )
    return my_application_list


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
                'filter_encoded_url': u_filter.value,
                'saved_date': datetime.strftime(u_filter.last_date_saved, '%b %-d %Y at %-I:%M %p (%Z)')
            }
        )
    return saved_search_list


@otp_required
def delete_filters(request, filter_id):
    owner = request.user
    message = Filter.destroy(filter_id=filter_id, owner=owner)
    if message['success']:
        logger.info(f"[INFO] User '{owner}': {message['success']}")
    elif message['error']:
        logger.error(f"[ERROR] User '{owner}': {message['error']}")
    return JsonResponse(message)


@otp_required
def open_file(request, submission_id, att):
    owner = request.user
    filename = Submissions.get_submission_filename(owner, submission_id, (att == "1"))
    if filename:
        bucket_name = settings.GCP_APP_DOC_BUCKET
        file_blob = read_blob(bucket_name=bucket_name, blob_name=filename)
        file_bytes = file_blob.download_as_bytes()
        logger.info(f"[INFO] File {filename} accessed by '{owner}' for reading from [{bucket_name}].")
        return HttpResponse(file_bytes, content_type=file_blob.content_type)
    else:
        return render(request, '400.html', {'error': "Unable to find the requested file."})


@otp_required
def save_filters(request):
    filters = get_filters(request)
    name = filters.get('title', 'Untitled')
    if 'title' in filters:
        filters.pop('title')
    search_type = filters.get('search_type', 'Biosample');
    if 'search_type' in filters:
        filters.pop('search_type')
    case_count = filters.get('total', 0)
    if 'total' in filters and search_type != 'Clinical':
        filters.pop('total')
    if 'filter_encoded_url' in filters:
        filter_encoded_url = filters.get('filter_encoded_url', 0)
        filters.pop('filter_encoded_url')
    else:
        filter_encoded_url = ('?' + urllib.parse.urlencode(filters, True))
    Filter.create(name, search_type, case_count, filter_encoded_url, request.user)
    return JsonResponse({'message': 'Your search \'' + name + '\' has been saved.'})


@otp_required
@password_change_required
def search_clinical(request):
    filters = get_filters(request)
    total = filters.get('total', 5516)
    title = filters.get('title', '')
    if 'title' in filters:
        filters.pop('title')
    if 'csrfmiddlewaretoken' in filters:
        filters.pop('csrfmiddlewaretoken')
    case_counts = get_clinical_case_counts(filters)
    clinic_search_result = {
        'total': total,
        'avail': case_counts
    }
    return render(request, 'donors/clinical_search_facility_result.html',
                  {'clinic_search_result': clinic_search_result, 'title': title,
                   'filter_encoded_url': '?' + urllib.parse.urlencode(filters, True)})


# Driver Search Facility
@otp_required
@password_change_required
def driver_search_facility(request):
    filters = get_filters(request)
    title = filters.get('title', '')
    if 'title' in filters:
        filters.pop('title')
    total_filtered_case_count, counts = get_driver_case_counts(filters)
    return render(request, 'donors/driver_search_facility.html',
                  {'counts': counts, 'title': title, 'total_filtered_case_count': total_filtered_case_count,
                   'filter_encoded_url': '?' + urllib.parse.urlencode(filters, True)})


@otp_required
@password_change_required
def search_tissue_samples(request):
    return render(request, 'donors/search_tissue_samples.html', {'total_counts': settings.BLANK_TISSUE_FILTER_CASE_COUNT})


@otp_required
def get_filters(request):
    sample_filters = {}
    request_method = request.GET if request.method == 'GET' else request.POST
    for key in request_method:
        if key.endswith('[]'):
            sample_filters[key] = request_method.getlist(key)
        else:
            val = request_method.get(key)
            if val:
                sample_filters[key] = request_method.get(key)
    return sample_filters


@otp_required
def filter_tissue_samples(request):
    filters = get_filters(request)
    case_counts = get_sample_case_counts(filters)
    return JsonResponse(case_counts)


# Clinical Search Facility
@otp_required
@password_change_required
def clinical_search_facility(request):
    filters = get_filters(request)
    title = filters.get('title', '')
    if 'title' in filters:
        filters.pop('title')
    return render(request, 'donors/clinical_search_facility.html',
                  {'sample_filters': filters, 'title': title})


@otp_required
@password_change_required
def make_application(request):
    return render(request, 'donors/application_form.html')


@otp_required
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
            destination_att_file_name = None
            if is_file_option_on and request.FILES:
                # uploaded project summary file
                uploaded_blob = request.FILES["project-summary-file"]
                if uploaded_blob.size > settings.CTB_FORM_FILE_SIZE_UPLOAD_MAX:
                    raise Exception('Project summary file you are trying to upload is too large.')

                file_extension = uploaded_blob.name.split('.')[-1]
                destination_att_file_name = f"CTB_APPLICATION_{date_str}_{user_str}_ATTACHMENT.{file_extension}"
                application_content["project_summary"] = f"[Attached file: {destination_att_file_name}]"
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
                f'{TIER}{ACCOUNT_EMAIL_SUBJECT_PREFIX} Application Submitted',
                '''
            
            A Chernobyl tissue bank application has been submitted.
            A copy of the application is attached to this email for you to review.
            Please contact ctbWebAdmin@mail.nih.gov if you have any questions or concerns.
            
            CTB Web Team''',
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
        Submissions.create(entry_form_path=destination_file_name, summary_file_path=destination_att_file_name, owner=request.user)
    except Exception as e:
        logger.error("[ERROR] While attempting to submit an application of user {}:".format(user_email))
        logger.exception(e)
        return render(request, 'donors/application_post_submit.html', {'request': request,
                                                                       'error': e})
    logger.info("[CTB APPLICATION] Application is submitted and a copy of the application is sent to {}".format(user_email))
    return render(request, 'donors/application_post_submit.html',
                  {
                      'request': request,
                      'success': f'Application is submitted and a copy of the application is sent to {user_email}.'
                  })

