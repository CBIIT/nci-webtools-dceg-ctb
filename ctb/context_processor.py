from django.conf import settings # import the settings file
import sys

def additional_context(request):

    return {
            'SITE_GOOGLE_ANALYTICS_TRACKING_ID': settings.SITE_GOOGLE_ANALYTICS_TRACKING_ID,
            'SITE_GOOGLE_ANALYTICS': settings.SITE_GOOGLE_ANALYTICS,
            'GOOGLE_SITE_VERIFICATION_CODE': settings.GOOGLE_SITE_VERIFICATION_CODE,
            'BASE_URL': settings.BASE_URL,
            'STATIC_FILES_URL': settings.STATIC_URL,
            'STORAGE_URI': settings.GCS_STORAGE_URI,
            'FILE_SIZE_UPLOAD_MAX': settings.FILE_SIZE_UPLOAD_MAX,
            'RESTRICTED_ACCESS': settings.RESTRICT_ACCESS,
            'RESTRICTED_ACCESS_GROUPS': settings.RESTRICTED_ACCESS_GROUPS,
            'APP_VERSION': settings.APP_VERSION,
            'DEV_TIER': settings.DEV_TIER
    }
