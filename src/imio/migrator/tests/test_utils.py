# -*- coding: utf-8 -*-

from freezegun import freeze_time
from imio.migrator.migrator import Migrator
from imio.migrator.testing import IntegrationTestCase
from imio.migrator.utils import end_time
from imio.migrator.utils import ensure_upgraded


START_TIME = 1735732800.0  # 2025-01-01 12:00:00


class TestUtils(IntegrationTestCase):

    def setUp(self):
        self.portal = self.layer["portal"]
        self.migrator = Migrator(self.portal)
        self.migrator.display_mem = False

    def test_ensure_upgraded(self):
        self.migrator.ps.setLastVersionForProfile("imio.migrator:testing", "999")
        info = self.migrator.installer.upgrade_info("imio.migrator")
        self.assertEqual(info["installedVersion"], "999")
        ensure_upgraded("imio.migrator", profile_name="testing")
        info = self.migrator.installer.upgrade_info("imio.migrator")
        self.assertEqual(info["installedVersion"], "1000")

    @freeze_time("2025-01-01 12:00:05")
    def test_end_time_seconds_only(self):
        msg = end_time(START_TIME)
        self.assertEqual(msg, "Migration finished in 5 second(s).")

    @freeze_time("2025-01-01 12:01:05")
    def test_end_time_minutes_and_seconds(self):
        msg = end_time(START_TIME)
        self.assertEqual(msg, "Migration finished in 1 minute(s), 5 second(s).")

    @freeze_time("2025-01-01 14:02:03")
    def test_end_time_hours_minutes_seconds(self):
        msg = end_time(START_TIME)
        self.assertEqual(
            msg, "Migration finished in 2 hour(s), 2 minute(s), 3 second(s)."
        )

    @freeze_time("2025-01-02 13:01:01")
    def test_end_time_days_hours_minutes_seconds(self):
        msg = end_time(START_TIME)
        self.assertEqual(
            msg, "Migration finished in 1 day(s), 1 hour(s), 1 minute(s), 1 second(s)."
        )

    @freeze_time("2025-01-01 12:00:10")
    def test_end_time_return_seconds_flag(self):
        msg, seconds = end_time(START_TIME, return_seconds=True)
        self.assertEqual(msg, "Migration finished in 10 second(s).")
        self.assertEqual(seconds, 10)

    @freeze_time("2025-01-01 12:00:10")
    def test_end_time_total_number(self):
        msg = end_time(START_TIME, total_number=50)
        self.assertEqual(
            msg,
            "Migration finished in 10 second(s). Updated 50 elements, that is 5 by second.",
        )

    @freeze_time("2025-01-01 12:00:00")
    def test_end_time_total_number_zero_seconds(self):
        msg = end_time(START_TIME, total_number=10)
        self.assertEqual(
            msg,
            "Migration finished in 0 second(s). Updated 10 elements, that is 10 by second.",
        )
