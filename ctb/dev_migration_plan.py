"""Inspect CTB's pending dev migrations without applying them."""

import os
import sys

from django.conf import settings
from django.core.management import call_command
from django.db import connection


def read_only_grants(rows):
    if not rows:
        return False
    for (grant,) in rows:
        privileges, sep, _ = grant.partition(" ON ")
        if not sep or not privileges.startswith("GRANT ") or " WITH GRANT OPTION" in grant:
            return False
        if not set(privileges[6:].split(", ")) <= {"USAGE", "SELECT", "SHOW VIEW"}:
            return False
    return True


def run(instance, database, account):
    import django

    os.environ.pop("CI", None)
    os.environ.update(DJANGO_SETTINGS_MODULE="ctb.settings", IS_DEV="False",
                      DAILY_MANAGEMENT_ENABLED="False")
    if not os.path.isfile(os.environ.get("CTB_ENV_FILE", "")):
        raise SystemExit("Missing dedicated planning configuration mount.")
    config = settings.DATABASES["default"]
    if ("CI" in os.environ or settings.IS_DEV or settings.DAILY_MANAGEMENT_ENABLED
            or config["ENGINE"] != "django.db.backends.mysql"
            or config["HOST"] != f"/cloudsql/{instance}" or config["NAME"] != database
            or config["USER"] != account.partition("@")[0]):
        raise SystemExit("The effective settings do not match the approved planning target.")

    django.setup()
    with connection.cursor() as cursor:
        cursor.execute("SELECT DATABASE(), CURRENT_USER(), VERSION()")
        name, user, version = cursor.fetchone()
        if (name, user) != (database, account):
            raise SystemExit("Connected database or authenticated account does not match.")
        cursor.execute("SHOW GRANTS FOR CURRENT_USER")
        if not read_only_grants(cursor.fetchall()):
            raise SystemExit("Planning requires direct read-only grants; refusing this account.")
        cursor.execute("SET SESSION TRANSACTION READ ONLY")
    print(f"Verified planning target: {instance}/{database}; MySQL {version}", flush=True)
    call_command("showmigrations", plan=True, no_color=True)
    call_command("migrate", plan=True, interactive=False, no_color=True)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Expected a Cloud SQL connection name, database and authenticated account.")
    run(*sys.argv[1:])
