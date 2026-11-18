# isb-cgc-ctb
Chernobyl Tissue Bank

## Authentication runtime

The application targets Python 3.12, Django 5.2 LTS, and django-allauth 65.x.
Exact versions, including django-two-factor-auth, django-otp, and Axes, are pinned
in `requirements.txt`. The deployment Dockerfile selects Python 3.12 explicitly;
the GitHub deployment workflows build that image rather than selecting a host
Python interpreter.

The custom authentication backend retains its existing import path for stored
sessions, but delegates password checks to allauth. Password-reset handling keeps
CTB's inactive-account email and uses allauth's public form implementation for
active and unknown addresses. Empty password-policy allowance entries no longer
match the temporarily blank username used during signup validation.

Axes uses its database handler outside `IS_DEV` mode because Django's database
cache does not provide the atomic counters required by the Axes cache handler.
The existing local-development dummy handler is unchanged.

The application still starts its existing daily-management thread from WSGI.
The unused, Django-5-incompatible django-cron wrapper has been removed; this does
not move jobs to a new scheduler. Set `DAILY_MANAGEMENT_ENABLED=False` when jobs
must not run. No migrations are executed at application startup.

## Isolated regression tests

Run these commands only with the test settings, not deployment settings:

```bash
python manage.py test accounts ctb adminrestrict --settings=ctb.test_settings --noinput
```

`ctb.test_settings` ignores local `.env` files and service credentials, uses
in-memory SQLite by default, captures email locally, and disables scheduling.
Google's token exchange and identity response, cloud-storage writes, and
scheduled-management calls are mocked. These tests do not establish that real
Google credentials, email delivery, or deployed proxy configuration work.

The tests cover signup/verification, active/inactive/unknown password resets,
reset-token reuse, password changes/history/expiration, TOTP/email/backup-token
login, approval restrictions, lockouts, Google callback integration, public and
admin pages, authentication templates, application submission/PDF generation,
and scheduler isolation.

`accounts.test_migrations` starts from the allauth 0.54/Axes 5.20 migration states
with synthetic records, applies the new package migrations, and checks account
status, email normalization/verification, Google associations/tokens, password
hashes/history/expiration, TOTP secrets, and login-attempt deduplication.

The legacy `donors` app has no production migrations. Test settings alone map it
to `ctb.test_migrations.donors`, so a new MySQL test database can create its tables
after `auth_user`. These test-only migrations are not enabled in deployment
settings and do not propose donor/clinical schema changes.

### Docker and disposable MySQL

Use a clean checkout without deployment `.env` files or credentials in the build
context. The test password below is only for the disposable local MySQL service.

```bash
docker build --platform linux/amd64 --tag ctb-upgrade:11038 .
docker run --rm ctb-upgrade:11038 python --version
docker run --rm ctb-upgrade:11038 python -m pip check
docker run --rm ctb-upgrade:11038 \
  python manage.py test accounts ctb adminrestrict --settings=ctb.test_settings --noinput

docker run --detach --name ctb-upgrade-mysql \
  --env MYSQL_ROOT_PASSWORD=ctb-ci-only --env MYSQL_DATABASE=ctb_upgrade mysql:8.0
docker exec ctb-upgrade-mysql mysqladmin ping --host=127.0.0.1 --password=ctb-ci-only
```

After MySQL reports ready, run the migration plan, migrations, pending-migration
check, and regression suite against that container only:

```bash
docker run --rm --network container:ctb-upgrade-mysql \
  --env CTB_TEST_MYSQL_PORT=3306 --env CTB_TEST_MYSQL_PASSWORD=ctb-ci-only \
  ctb-upgrade:11038 sh -ec '
    python manage.py migrate --plan --settings=ctb.test_settings
    python manage.py migrate --noinput --settings=ctb.test_settings
    python manage.py migrate --check --settings=ctb.test_settings
    python manage.py test accounts ctb adminrestrict --settings=ctb.test_settings --noinput
  '
docker rm --force --volumes ctb-upgrade-mysql
```

With MySQL's default case-insensitive collation, the upstream lowercase-email
data migration can retain existing mixed-case values because its equality filter
already considers them equal. SQLite normalizes the synthetic mixed-case values.
The rehearsal checks the actual backend behavior and retained account identity;
shared-tier verification must use its real collation and data.

MySQL does not enforce the conditional unique constraints used by allauth for
verified and primary email addresses. Django reports that limitation; allauth's
application-level checks remain important. A pre-existing duplicate template-tag
name (`session_security_tags`) also produces a system-check warning.

`.github/workflows/test.yml` repeats the deployment-image build and isolated
SQLite/MySQL checks on pull requests to `dev`. It uses no deployment environment,
cloud credentials, real accounts, or live database.

## Shared-tier migration gate

Container checks are not permission to migrate or deploy a shared tier. First
obtain approval, inspect its actual pending migration plan, check account-data
conflicts and existing JSON validity, verify a protected backup/recovery path,
and rehearse on an approved isolated copy. Apply package migrations once during
a controlled rollout without concurrent application or scheduled writes, then
verify login, verification/approval, 2FA, password-reset, and application flows.
Recovery must pair compatible code with database state; a package downgrade alone
does not undo email normalization or other data migrations.

Neither GitHub deployment workflow currently runs migrations. The older
`shell/database-setup.sh` does, but also changes database users/grants, can import
seed data, and inserts configuration records. It is not a migration-only utility
for shared tiers. `shell/database-refresh.sh` drops/recreates a local database.
The legacy Vagrant/CircleCI scripts are not the Python-3.12 container validation
path described above.
