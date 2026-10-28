import re
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.template.loader import get_template
from django.test import TestCase
from django.urls import reverse
from django_otp.plugins.otp_totp.models import TOTPDevice
from xhtml2pdf import pisa

from accounts.models import PasswordExpiration
from donors.models import Submissions


class CompatibilityTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_public_pages_and_health(self):
        for path in ('/', '/about/', '/research/', '/contact/', '/privacy/', '/_ah/health', '/_ah/vm_health'):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_authentication_overrides_compile(self):
        templates = Path(settings.BASE_DIR) / 'templates'
        for directory in ('accounts', 'two_factor'):
            for template in (templates / directory).rglob('*'):
                if template.is_file():
                    name = template.relative_to(templates / 'accounts' if directory == 'accounts' else templates)
                    with self.subTest(template=str(name)):
                        get_template(str(name))

    def test_blacklist_regex_is_valid_on_python_312(self):
        pattern = re.compile(settings.BLACKLIST_RE)
        self.assertIsNotNone(pattern.search('<SCRIPT>'))
        self.assertIsNotNone(pattern.search('</IFRAME>'))

    def test_application_pdf_is_valid(self):
        template = get_template('donors/intake_form_wrapper.html')
        result = BytesIO()
        pdf = pisa.CreatePDF(template.render({'pdf': True, 'first_name': 'Synthetic'}), dest=result)
        self.assertEqual(pdf.err, 0)
        self.assertTrue(result.getvalue().startswith(b'%PDF-'))

    @patch('ctb.cron.cron_job.daily_management')
    def test_daily_job_uses_existing_management_function(self, daily_management):
        from ctb.cron.cron_job import daily_task
        daily_task()
        daily_management.assert_called_once_with(None)

    @patch('ctb.cron.cron_job.daily_management', side_effect=RuntimeError('synthetic failure'))
    def test_daily_job_logs_failures(self, daily_management):
        from ctb.cron.cron_job import daily_task
        with self.assertLogs('main_logger', level='ERROR') as logs:
            daily_task()
        self.assertIn('Daily management failed', logs.output[0])

    @patch('ctb.cron.cron_job.schedule_task')
    def test_wsgi_does_not_start_scheduler_in_test_settings(self, schedule_task):
        from ctb.wsgi import application
        self.assertTrue(callable(application))
        schedule_task.assert_not_called()

    @patch('donors.views.upload_blob')
    def test_application_submission_uses_pdf_and_test_email(self, upload_blob):
        user = get_user_model().objects.create_user(username='applicant', email='applicant@example.org')
        PasswordExpiration.objects.create(user=user)
        self.client.force_login(user)
        device = TOTPDevice.objects.create(user=user, name='default', confirmed=True)
        session = self.client.session
        session['otp_device_id'] = device.persistent_id
        session.save()
        response = self.client.post(reverse('application_submit'), {
            'first-name': 'Synthetic', 'last-name': 'Applicant', 'email': user.email,
            'project-summary': 'Synthetic regression test data only.',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.context)
        upload_blob.assert_called_once()
        self.assertTrue(Submissions.objects.filter(owner=user).exists())
