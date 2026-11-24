from types import SimpleNamespace
import os
import unittest
from unittest.mock import MagicMock, patch

from ctb import dev_migration_plan as plan


class PlanTests(unittest.TestCase):
    def test_grants_fail_closed(self):
        for grant in ("GRANT ALL PRIVILEGES ON *.* TO u", "GRANT SELECT, INSERT ON db.* TO u",
                      "GRANT SELECT ON db.* TO u WITH GRANT OPTION", "GRANT `writer`@`%` TO u"):
            with self.subTest(grant=grant):
                self.assertFalse(plan.read_only_grants([(grant,)]))
        self.assertFalse(plan.read_only_grants([]))

    def test_only_verified_connection_can_plan(self):
        expected = ("p:region:i", "ctb_db", "reader@%")
        for case in ("valid", "wrong-socket", "wrong-account", "write-grant"):
            with self.subTest(case=case):
                db = dict(ENGINE="django.db.backends.mysql", NAME="ctb_db", USER="reader",
                          HOST="/cloudsql/" + ("other" if case == "wrong-socket" else expected[0]))
                config = SimpleNamespace(DATABASES={"default": db}, IS_DEV=False, DAILY_MANAGEMENT_ENABLED=False)
                cx = MagicMock()
                cursor = cx.cursor.return_value.__enter__.return_value
                cursor.fetchone.return_value = ("ctb_db", "other@%" if case == "wrong-account" else "reader@%", "8.0")
                cursor.fetchall.return_value = [("GRANT USAGE ON *.* TO u",),
                                                (f"GRANT {'UPDATE' if case == 'write-grant' else 'SELECT'} ON db.* TO u",)]
                with (patch.dict(os.environ, {"CTB_ENV_FILE": __file__}), patch.object(plan, "connection", cx),
                      patch.dict(plan.__dict__, settings=config), patch("django.setup"),
                      patch.object(plan, "call_command") as command):
                    if case == "valid":
                        plan.run(*expected)
                        self.assertEqual([c.args for c in command.call_args_list], [("showmigrations",), ("migrate",)])
                        self.assertTrue(all(c.kwargs["plan"] for c in command.call_args_list))
                    else:
                        with self.assertRaises(SystemExit):
                            plan.run(*expected)
                        command.assert_not_called()
