###
# Copyright 2015-2023, Institute for Systems Biology
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

import logging
logger = logging.getLogger('main_logger')


# def validate_token(request):
#     try:
#         auth_header = request.headers.get('Authorization','').split()
#
#         # Make sure our Auth Header is the expected size
#         if len(auth_header) == 1 or len(auth_header) > 2:
#             return {'message': 'Cron access token not provided, or the wrong key was used.'}
#
#         # Check for our Auth Header Token key, whatever that is.
#         if not auth_header or auth_header[0].lower() != settings.CRON_AUTH_KEY.lower():
#             return {'message':'Cron access token not provided, or the wrong key was used.'}
#
#         # Now actually validate with the token
#         token = auth_header[1]
#         token_obj = Token.objects.select_related('user').get(key=token)
#
#         # If a user was found, we've received a valid Cron call, and can proceed.
#         if token_obj and token_obj.user.username.lower() == settings.CRON_USER.lower():
#             return {settings.CRON_USER: True}
#
#     except (ObjectDoesNotExist, UnicodeError):
#         return {'message': 'Invalid Cron auth token supplied.'}


def validate_header(request):
    # Requests from the Cron Service need to be validated using a header
    try:
        auth_header = request.headers.get(settings.CRON_HEADER, None)

        if not auth_header or auth_header != settings.CRON_HEADER_VAL:
            return {
                'result': 'INVALID',
                'message': 'AppEngine Cron header not seen.'
            }
        else:
            return {'result': 'VALIDATED'}

    except Exception as e:
        logger.error("[ERROR] While validating Cron AppEngine header:")
        logger.exception(e)
        return {
            'result': 'INVALID',
            'message': 'Encountered an error while validating Cron AppEngine header.'
        }


# decorator for cron request
def validate_request(request):
    response_obj = {}
    try:
        # validate header first
        validated = validate_header(request)
        validated_result = validated.get('result', 'INVALID')
        if validated_result == 'VALIDATED':
            response_obj['code'] = 200
        else:
            error_msg = '[Error] Invalid cron request has been made. No Cron AppEngine header nor valid token was found.'
            logger.error(error_msg)
            response_obj['message'] = error_msg
            response_obj['code'] = 403

    except Exception as e:
        logger.error("[ERROR] While validating cron job request:")
        logger.exception(e)
        response_obj['message'] = e
        response_obj['code'] = 500
    return response_obj
