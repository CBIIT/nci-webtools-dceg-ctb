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

### Run a read-only dev plan from GitHub Actions

**Plan CTB dev database migration** is a manual workflow with no inputs and no
apply mode. It builds the selected `dev` commit, verifies the serving App Engine
service's SQL attachment, and runs the image **by digest** in a private Cloud
Run Job. The job checks the effective Django settings, database, authenticated
MySQL account and grants before running `showmigrations --plan` and `migrate
--plan`. The plan stays in Cloud Logging; the Actions summary records the commit,
digest and a link to the job executions. No backup, clone, deployment or
migration is performed. Publishing the image and updating/executing the
dedicated plan job are the only intended GCP changes.

**One-time setup (requires existing provisioning authority):**

1. In the dev app project, enable Cloud Run, Artifact Registry and App Engine
   Admin APIs; enable Cloud SQL Admin, Secret Manager, and WIF/IAM Credentials
   APIs in the relevant projects. Provision a regional Docker repository and
   a dedicated, **single-container** Cloud Run Job in that same region. Use a
   private network route as required by the SQL instance, attach the approved
   Cloud SQL connection, and set the job's working directory to `/app`.
   Only the trusted dispatcher should update this job; never point it at the
   deployed web service or a job with a write-capable identity.
2. Create a dedicated MySQL account with direct `SELECT` on the CTB dev
   schema only. The plan rejects roles, write privileges and grant options.
   Put its password in a dedicated Secret Manager CTB config, **not** the
   deployment `ENV_FILE`. Mount the secret in the job and set `CTB_ENV_FILE`
   to its absolute path. Set `DATABASE_ENGINE=django.db.backends.mysql`,
   `DATABASE_HOST=/cloudsql/<approved-connection-name>`, `DATABASE_NAME`,
   `DATABASE_USER`, `DATABASE_PASSWORD` and CTB's required `SECRET_KEY` there.
   Do not define `CI`, `IS_DEV=True`, or `DAILY_MANAGEMENT_ENABLED=True`.
   Give the job's runtime service account Cloud SQL Client in the SQL project
   and Secret Accessor on this secret only. Do not grant backup or restore.
3. Configure GitHub OIDC/WIF to impersonate a dedicated dispatcher, restricted
   to this repository, the trusted workflow on `refs/heads/dev`, and the
   protected environment. Grant it App Engine service/version read access,
   Artifact Registry read/write on the dedicated repository, permission to
   get/update/run the dedicated job and wait for its operations/executions,
   and `iam.serviceAccounts.actAs` on **only** its runtime account. The
   dispatcher does not need MySQL credentials. Give authorized operators
   private access to job executions and logs.
4. The workflow reads two existing **repository Actions secrets**:
   `GCP_DEV_PROJECT_ID` (the dev App Engine project ID) and
   `WORKLOAD_IDENTITY_PROVIDER` (the full provider resource name).
   In **Settings → Environments**, create `ctb-dev-plan`, restrict deployment
   branches to `dev`, and set these eight **environment variables**. Do not
   copy the `dev` deployment secrets or add a database password to GitHub.

   | Variables | Values |
   |---|---|
   | `PLAN_DISPATCHER_SA` | Dedicated dispatcher service-account email |
   | `GAE_SERVICE` | Serving App Engine service name in the dev app project |
   | `RUN_REGION`, `AR_REPOSITORY`, `PLAN_JOB` | Region, Docker repository ID and Cloud Run Job name (not URLs) |
   | `SQL_CONNECTION_NAME`, `SQL_DATABASE` | Approved `project:region:instance` (may belong to a different project) and CTB database name |
   | `SQL_READONLY_ACCOUNT` | Exact result of MySQL `CURRENT_USER()` for the approved planner, including its host, e.g. `ctb_plan@%` |

5. GitHub requires the `workflow_dispatch` file to be present on the repository's
   **default branch (`main`)** to register the workflow. Landing this PR on
   `dev` alone is not enough: include the workflow on `main` through the
   normal release/review process. Then go to **Actions → Plan CTB dev database
   migration → Run workflow → Branch: dev**. Other branches are skipped.
   Open the private executions link in the run summary with the CTB dev app
   project selected in the Cloud Console, then open the matching execution's
   logs to read the plan. A successful run with pending migrations is
   expected; it does not authorize applying them.

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
