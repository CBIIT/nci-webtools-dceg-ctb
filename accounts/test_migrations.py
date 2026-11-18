import json
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone
from django_otp.plugins.otp_totp.models import TOTPDevice

from accounts.models import PasswordExpiration, PasswordHistory


class AuthenticationMigrationTests(TransactionTestCase):
    """Rehearse the pinned allauth/Axes upgrade using synthetic records only."""

    def setUp(self):
        executor = MigrationExecutor(connection)
        self.latest = executor.loader.graph.leaf_nodes()
        self.addCleanup(self.restore_schema)
        baseline = [
            node for node in self.latest
            if node[0] not in {'account', 'socialaccount', 'axes'}
        ] + [
            ('account', '0002_email_max_length'),
            ('socialaccount', '0003_extra_data_default_dict'),
            ('axes', '0006_remove_accesslog_trusted'),
        ]
        executor.migrate(baseline)
        self.old_apps = executor.loader.project_state(baseline).apps

    def restore_schema(self):
        MigrationExecutor(connection).migrate(self.latest)

    def test_upgrade_preserves_accounts_google_tokens_passwords_and_totp(self):
        User = self.old_apps.get_model('auth', 'User')
        EmailAddress = self.old_apps.get_model('account', 'EmailAddress')
        SocialAccount = self.old_apps.get_model('socialaccount', 'SocialAccount')
        SocialApp = self.old_apps.get_model('socialaccount', 'SocialApp')
        SocialToken = self.old_apps.get_model('socialaccount', 'SocialToken')
        AccessAttempt = self.old_apps.get_model('axes', 'AccessAttempt')
        password_hash = make_password('SyntheticMigrationPassword12!')
        user = User.objects.create(
            username='migration-user', email='Mixed.Case@EXAMPLE.ORG',
            password=password_hash, is_active=True,
        )
        inactive = User.objects.create(
            username='inactive-migration-user', email='Inactive@EXAMPLE.ORG',
            password=password_hash, is_active=False,
        )
        address = EmailAddress.objects.create(
            user=user, email=user.email, verified=True, primary=True,
        )
        # MySQL's case-insensitive collations can make the upstream normalization a no-op.
        with connection.cursor() as cursor:
            cursor.execute('SELECT email = LOWER(email) FROM auth_user WHERE id = %s', (user.pk,))
            expected_user_email = user.email if cursor.fetchone()[0] else user.email.lower()
            cursor.execute('SELECT email = LOWER(email) FROM account_emailaddress WHERE id = %s', (address.pk,))
            expected_address_email = address.email if cursor.fetchone()[0] else address.email.lower()
        app = SocialApp.objects.create(
            provider='google', name='Synthetic Google app',
            client_id='synthetic-client', secret='synthetic-secret',
        )
        account = SocialAccount.objects.create(
            user=user, provider='google', uid='synthetic-google-subject',
            extra_data=json.dumps({'email': user.email, 'email_verified': True}),
        )
        token = SocialToken.objects.create(
            app=app, account=account, token='synthetic-access-token',
            token_secret='synthetic-refresh-token',
        )
        expiration_date = timezone.now() + timedelta(days=77)
        PasswordExpiration.objects.create(user_id=user.pk, expiration_date=expiration_date)
        history = PasswordHistory.objects.create(user_id=user.pk, password_hash=password_hash)
        device = TOTPDevice.objects.create(user_id=user.pk, name='default', confirmed=True)
        original_key = device.key
        for _ in range(2):
            AccessAttempt.objects.create(
                username=user.username, ip_address='192.0.2.1', user_agent='synthetic-test',
                failures_since_start=1,
            )

        executor = MigrationExecutor(connection)
        executor.migrate(self.latest)
        apps = executor.loader.project_state(self.latest).apps
        migrated_user = apps.get_model('auth', 'User').objects.get(pk=user.pk)
        self.assertEqual(migrated_user.email, expected_user_email)
        self.assertEqual(migrated_user.password, password_hash)
        self.assertTrue(migrated_user.is_active)
        self.assertFalse(apps.get_model('auth', 'User').objects.get(pk=inactive.pk).is_active)
        migrated_address = apps.get_model('account', 'EmailAddress').objects.get(pk=address.pk)
        self.assertEqual(migrated_address.email, expected_address_email)
        self.assertEqual(migrated_address.email.lower(), migrated_user.email.lower())
        self.assertTrue(migrated_address.verified)
        self.assertTrue(migrated_address.primary)
        migrated_account = apps.get_model('socialaccount', 'SocialAccount').objects.get(pk=account.pk)
        self.assertEqual(migrated_account.uid, 'synthetic-google-subject')
        self.assertEqual(migrated_account.extra_data, {'email': user.email, 'email_verified': True})
        migrated_token = apps.get_model('socialaccount', 'SocialToken').objects.get(pk=token.pk)
        self.assertEqual(migrated_token.token, 'synthetic-access-token')
        self.assertEqual(migrated_token.token_secret, 'synthetic-refresh-token')
        self.assertEqual(migrated_token.app_id, app.pk)
        self.assertEqual(PasswordHistory.objects.get(pk=history.pk).password_hash, password_hash)
        self.assertEqual(PasswordExpiration.objects.get(user_id=user.pk).expiration_date, expiration_date)
        self.assertEqual(TOTPDevice.objects.get(pk=device.pk).key, original_key)
        self.assertEqual(apps.get_model('axes', 'AccessAttempt').objects.filter(username=user.username).count(), 1)
