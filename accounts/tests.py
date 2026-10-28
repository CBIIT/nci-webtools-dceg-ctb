import re
from datetime import timedelta
from unittest.mock import patch
from urllib.parse import parse_qs, urlencode, urlsplit

from allauth.account.auth_backends import AuthenticationBackend
from allauth.account.models import EmailAddress, EmailConfirmationHMAC
from allauth.account.signals import password_changed, password_reset, password_set, user_signed_up
from allauth.socialaccount.models import SocialAccount, SocialApp
from allauth.socialaccount.providers.google.provider import GoogleProvider
from axes.helpers import get_client_ip_address
from django.conf import settings
from django.contrib.auth import SESSION_KEY, get_user_model
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.core import mail
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase, override_settings
from django.urls import resolve, reverse
from django.utils import timezone
from django_otp.oath import totp
from django_otp.plugins.otp_email.models import EmailDevice
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice

from accounts.auth_backends import CustomAuthenticationBackend
from accounts.models import PasswordExpiration, PasswordHistory
from accounts.views import extended_logout_view, redirect_login_view
from ctb.validators import PasswordComplexityValidator, PasswordReuseValidator


PASSWORD = 'SyntheticStrongPass12!'
NEW_PASSWORD = 'DifferentStrongPass34!'


class AccountTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user(
            username='synthetic-user', email='synthetic@example.org', password=PASSWORD,
        )
        self.address = EmailAddress.objects.create(
            user=self.user, email=self.user.email, verified=True, primary=True,
        )
        PasswordExpiration.objects.create(user=self.user)

    def reset_request(self, email):
        response = self.client.post(reverse('account_reset_password'), {'email': email})
        self.assertRedirects(response, reverse('account_reset_password_done'), fetch_redirect_response=False)
        return mail.outbox[-1]

    def reset_link(self):
        message = self.reset_request(self.user.email)
        match = re.search(r'https?://\S+/accounts/password/reset/key/\S+', message.body)
        self.assertIsNotNone(match)
        return urlsplit(match.group()).path

    def test_custom_backend_returns_user_not_boolean(self):
        request = self.client.request().wsgi_request
        backend = CustomAuthenticationBackend()
        self.assertEqual(backend.authenticate(request, email=self.user.email, password=PASSWORD), self.user)
        self.assertIsNone(backend.authenticate(request, email=self.user.email, password='wrong'))
        self.assertIsNone(backend.authenticate(request, username='unknown', password=PASSWORD))
        AuthenticationBackend.unstash_authenticated_user()

    def test_custom_backend_rejects_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        request = self.client.request().wsgi_request
        self.assertIsNone(CustomAuthenticationBackend().authenticate(
            request, email=self.user.email, password=PASSWORD,
        ))
        AuthenticationBackend.unstash_authenticated_user()

    def test_login_route_reaches_two_factor_wizard(self):
        self.assertEqual(resolve(reverse('account_login')).func, redirect_login_view)
        response = self.client.get(reverse('account_login'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'two_factor/core/login.html')

    def test_logout_route_uses_wrapper_and_accepts_anonymous_stage_cancel(self):
        self.assertEqual(resolve(reverse('account_logout')).func, extended_logout_view)
        session = self.client.session
        session['account_login'] = {'pending': True}
        session.save()
        response = self.client.post(reverse('account_logout'))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('account_login', self.client.session)

    def test_logout_is_post_only(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('account_logout')).status_code, 200)
        self.assertIn(SESSION_KEY, self.client.session)
        self.assertEqual(self.client.post(reverse('account_logout')).status_code, 302)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_active_password_reset_sends_reset_link(self):
        message = self.reset_request(self.user.email.upper())
        self.assertEqual(message.to, [self.user.email])
        self.assertIn('/accounts/password/reset/key/', message.body)
        self.assertNotIn('deactivated', message.body.lower())

    def test_unknown_password_reset_sends_unknown_account_message(self):
        message = self.reset_request('unknown@example.org')
        self.assertEqual(message.to, ['unknown@example.org'])
        self.assertNotIn('/password/reset/key/', message.body)
        self.assertIn('account', message.body.lower())
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_inactive_password_reset_sends_custom_message_without_token(self):
        self.user.is_active = False
        self.user.save()
        message = self.reset_request(self.user.email)
        self.assertEqual(message.to, [self.user.email])
        self.assertIn('deactivated', message.body.lower())
        self.assertNotIn('/password/reset/key/', message.body)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_invalid_reset_email_sends_nothing(self):
        response = self.client.post(reverse('account_reset_password'), {'email': 'not-an-email'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(mail.outbox)

    def test_password_reset_round_trip_updates_history_and_expiry(self):
        path = self.reset_link()
        response = self.client.get(path, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'logout-from-stage')
        response = self.client.post(response.context['action_url'], {
            'password1': NEW_PASSWORD, 'password2': NEW_PASSWORD,
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))
        self.assertTrue(PasswordHistory.objects.filter(user=self.user, password_hash=self.user.password).exists())
        self.assertGreater(self.user.passwordexpiration.expiration_date, timezone.now() + timedelta(days=119))
        response = self.client.get(path, follow=True)
        self.assertContains(response, 'Bad Token')

    def test_signup_preserves_required_email_passwords_and_no_username_field(self):
        response = self.client.get(reverse('account_signup'))
        self.assertEqual(set(response.context['form'].fields), {'email', 'password1', 'password2'})
        response = self.client.post(reverse('account_signup'), {
            'email': 'signup@example.org', 'password1': PASSWORD, 'password2': PASSWORD,
        })
        self.assertRedirects(response, reverse('account_email_verification_sent'), fetch_redirect_response=False)
        user = get_user_model().objects.get(email='signup@example.org')
        self.assertFalse(EmailAddress.objects.get(user=user).verified)
        self.assertTrue(PasswordExpiration.objects.filter(user=user).exists())
        self.assertTrue(PasswordHistory.objects.filter(user=user, password_hash=user.password).exists())
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertTrue(mail.outbox)

    @override_settings(ACCOUNTS_ALLOWANCES=[''], IS_DEV=False)
    def test_blank_signup_username_never_receives_password_policy_exception(self):
        validator = PasswordComplexityValidator(min_length=16, special_char_list='!@#$%^&*+:;?')
        user = get_user_model()(username='')
        validator.validate(PASSWORD, user)
        with self.assertRaises(ValidationError):
            validator.validate('MissingSymbolPassword12', user)

    @override_settings(ACCOUNTS_ALLOWANCES=['service-account'], IS_DEV=False)
    def test_named_password_policy_exception_is_preserved(self):
        user = get_user_model()(username='service-account')
        validator = PasswordComplexityValidator()
        validator.validate('ServiceAccountPasswordWithoutSymbols123456', user)
        with self.assertRaises(ValidationError):
            validator.validate('TooShort123', user)

    def test_email_confirmation_notifies_user_and_reviewers(self):
        self.address.verified = False
        self.address.save()
        key = EmailConfirmationHMAC(self.address).key
        response = self.client.post(reverse('account_confirm_email', args=[key]))
        self.assertEqual(response.status_code, 302)
        self.address.refresh_from_db()
        self.assertTrue(self.address.verified)
        recipients = [recipient for message in mail.outbox for recipient in message.to]
        self.assertIn(self.user.email, recipients)
        self.assertIn(settings.CTB_APPLICATION_RECEIVER_EMAIL, recipients)

    def test_password_change_preserves_validation_history_and_expiry(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('account_change_password'), {
            'oldpassword': PASSWORD, 'password1': NEW_PASSWORD, 'password2': NEW_PASSWORD,
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))
        self.assertTrue(PasswordHistory.objects.filter(user=self.user, password_hash=self.user.password).exists())

    def test_password_signal_handlers_keep_bounded_history(self):
        with override_settings(ACCOUNTS_PASSWORD_HISTORY=2):
            for signal, password in zip(
                (password_set, user_signed_up, password_changed, password_reset),
                ('FirstStrongPass12!', 'SecondStrongPass12!', 'ThirdStrongPass12!', NEW_PASSWORD),
            ):
                self.user.set_password(password)
                self.user.save()
                signal.send(sender=type(self.user), request=None, user=self.user)
            self.assertEqual(PasswordHistory.objects.filter(user=self.user).count(), 2)
            with self.assertRaises(ValidationError):
                PasswordReuseValidator().validate(NEW_PASSWORD, self.user)

    def test_expired_password_redirects_before_dashboard(self):
        self.client.force_login(self.user)
        PasswordExpiration.objects.filter(user=self.user).update(expiration_date=timezone.now() - timedelta(days=1))
        response = self.client.get(reverse('extended_login'))
        self.assertRedirects(response, reverse('account_change_password'), fetch_redirect_response=False)

    def wizard_credentials(self):
        url = reverse('two_factor:login')
        self.client.get(url)
        return self.client.post(url, {
            'login_view-current_step': 'auth', 'auth-username': self.user.email, 'auth-password': PASSWORD,
        })

    def test_totp_requires_second_factor_before_login(self):
        device = TOTPDevice.objects.create(user=self.user, name='default', confirmed=True)
        response = self.wizard_credentials()
        self.assertEqual(response.context['wizard']['steps'].current, 'token')
        self.assertNotIn(SESSION_KEY, self.client.session)
        token = totp(device.bin_key, step=device.step, t0=device.t0, digits=device.digits, drift=device.drift)
        response = self.client.post(reverse('two_factor:login'), {
            'login_view-current_step': 'token', 'token-otp_token': str(token).zfill(device.digits),
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session[SESSION_KEY], str(self.user.pk))
        self.assertEqual(self.client.session['otp_device_id'], device.persistent_id)

    def test_backup_token_is_consumed(self):
        TOTPDevice.objects.create(user=self.user, name='default', confirmed=True)
        device = StaticDevice.objects.create(user=self.user, name='backup')
        token = StaticToken.objects.create(device=device, token='12345678')
        self.wizard_credentials()
        self.client.post(reverse('two_factor:login'), {'wizard_goto_step': 'backup'})
        response = self.client.post(reverse('two_factor:login'), {
            'login_view-current_step': 'backup', 'backup-otp_token': token.token,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session[SESSION_KEY], str(self.user.pk))
        self.assertFalse(StaticToken.objects.filter(pk=token.pk).exists())

    def test_email_second_factor_is_required_and_consumed(self):
        device = EmailDevice.objects.create(user=self.user, name='default', confirmed=True)
        response = self.wizard_credentials()
        self.assertEqual(response.context['wizard']['steps'].current, 'token')
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertEqual(mail.outbox[-1].to, [self.user.email])
        device.refresh_from_db()
        self.assertTrue(device.token)
        response = self.client.post(reverse('two_factor:login'), {
            'login_view-current_step': 'token', 'token-otp_token': device.token,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session[SESSION_KEY], str(self.user.pk))
        device.refresh_from_db()
        self.assertIsNone(device.token)

    def test_google_routes_remain_available(self):
        self.assertEqual(resolve('/accounts/google/login/').url_name, 'google_login')
        self.assertEqual(resolve('/accounts/google/login/callback/').url_name, 'google_callback')

    @patch('allauth.socialaccount.providers.oauth2.client.OAuth2Client.get_access_token')
    @patch('allauth.socialaccount.providers.google.views.GoogleOAuth2Adapter.complete_login')
    def test_google_callback_preserves_existing_account_and_requires_otp(self, complete_login, get_access_token):
        app = SocialApp.objects.create(
            provider='google', name='Synthetic Google app',
            client_id='synthetic-client', secret='synthetic-secret',
        )
        app.sites.add(Site.objects.get(pk=settings.SITE_ID))
        account = SocialAccount.objects.create(user=self.user, provider='google', uid='synthetic-google-subject')
        get_access_token.return_value = {'access_token': 'synthetic-token', 'token_type': 'Bearer'}

        def provider_login(request, app, token, **kwargs):
            provider = GoogleProvider(request=request, app=app)
            return provider.sociallogin_from_response(request, {
                'sub': account.uid, 'email': self.user.email, 'email_verified': True,
            })

        complete_login.side_effect = provider_login
        response = self.client.post(reverse('google_login'))
        self.assertEqual(response.status_code, 302)
        location = urlsplit(response.url)
        self.assertEqual(location.netloc, 'accounts.google.com')
        query = parse_qs(location.query)
        self.assertEqual(query['client_id'], ['synthetic-client'])
        response = self.client.get(reverse('google_callback') + '?' + urlencode({
            'state': query['state'][0], 'code': 'synthetic-authorization-code',
        }))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session[SESSION_KEY], str(self.user.pk))
        self.assertNotIn('otp_device_id', self.client.session)
        self.assertEqual(SocialAccount.objects.filter(user=self.user).count(), 1)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('two_factor:setup')))

    @override_settings(RESTRICT_ACCESS=True, RESTRICTED_ACCESS_GROUPS=['ctb_team'])
    def test_approval_and_email_verification_gate_is_preserved(self):
        self.client.force_login(self.user)
        device = TOTPDevice.objects.create(user=self.user, name='default', confirmed=True)
        session = self.client.session
        session['otp_device_id'] = device.persistent_id
        session.save()
        self.assertRedirects(self.client.get(reverse('dashboard')), reverse('landing_page'))
        self.user.groups.add(Group.objects.create(name='ctb_team'))
        self.address.verified = False
        self.address.save()
        self.assertRedirects(self.client.get(reverse('dashboard')), reverse('landing_page'))
        self.address.verified = True
        self.address.save()
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 200)

    @override_settings(AXES_IPWARE_PROXY_COUNT=1)
    def test_axes_proxy_settings_resolve_original_client(self):
        request = RequestFactory().get(
            '/', HTTP_X_FORWARDED_FOR='203.0.113.10, 192.0.2.1', REMOTE_ADDR='192.0.2.1',
        )
        self.assertEqual(get_client_ip_address(request), '203.0.113.10')

    @override_settings(AXES_FAILURE_LIMIT=2)
    def test_axes_lockout_uses_custom_response(self):
        url = reverse('two_factor:login')
        self.client.get(url)
        for _ in range(2):
            response = self.client.post(url, {
                'login_view-current_step': 'auth', 'auth-username': self.user.email, 'auth-password': 'wrong',
            })
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, 'accounts/account/lockout.html')
