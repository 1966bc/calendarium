#!/usr/bin/python3
# -----------------------------------------------------------------------------
# project:  calendarium
# authors:  1966bc aka Giuseppe Costanzi
# licence:  MIT, see LICENSE
# -----------------------------------------------------------------------------
"""
Unit tests for Calendarium.

Run from the repository root:

    python3 -m unittest discover -s tests -v

Tk needs a display. Without one (e.g. a headless CI) the tests are skipped.
"""

import datetime as _dt
import tkinter as tk
import unittest

from calendarium import Calendarium


def _make_root():
    try:
        root = tk.Tk()
    except tk.TclError:
        return None
    root.withdraw()
    return root


class CalendariumTestCase(unittest.TestCase):
    """One hidden Tk root for the whole class: creating it is the slow part."""

    root = None

    @classmethod
    def setUpClass(cls):
        cls.root = _make_root()
        if cls.root is None:
            raise unittest.SkipTest("no display available for Tk")

    @classmethod
    def tearDownClass(cls):
        if cls.root is not None:
            cls.root.destroy()

    def setUp(self):
        self.cal = Calendarium(self.root, "Test")

    def tearDown(self):
        self.cal.destroy()

    def set_fields(self, day, month, year):
        self.cal.day.set(day)
        self.cal.month.set(month)
        self.cal.year.set(year)

    def type_into(self, part, text):
        """Insert text into a spinbox the way a keystroke does, through validation."""
        spin = self.cal._spinboxes[part]
        spin.delete(0, tk.END)
        spin.insert(tk.END, text)
        return spin.get()


class TestConstruction(CalendariumTestCase):

    def test_starts_on_today(self):
        self.assertEqual(self.cal.get_date(), _dt.date.today())

    def test_caption_is_the_labelframe_text(self):
        self.assertEqual(self.cal.cget("text"), "Test")

    def test_is_a_labelframe(self):
        self.assertIsInstance(self.cal, tk.LabelFrame)

    def test_variables_are_stringvars(self):
        for var in (self.cal.day, self.cal.month, self.cal.year):
            self.assertIsInstance(var, tk.StringVar)


class TestSetAndGet(CalendariumTestCase):

    def test_set_date_round_trip(self):
        d = _dt.date(2024, 3, 15)
        self.cal.set_date(d)
        self.assertEqual(self.cal.get_date(), d)

    def test_set_date_writes_plain_strings(self):
        self.cal.set_date(_dt.date(2024, 3, 5))
        self.assertEqual(
            (self.cal.day.get(), self.cal.month.get(), self.cal.year.get()),
            ("5", "3", "2024"),
        )

    def test_set_today(self):
        self.cal.set_date(_dt.date(2000, 1, 1))
        self.cal.set_today()
        self.assertEqual(self.cal.get_date(), _dt.date.today())

    def test_set_from_datetime_drops_the_time(self):
        self.cal.set_from_datetime(_dt.datetime(2024, 3, 15, 23, 59, 59))
        self.assertEqual(self.cal.get_date(), _dt.date(2024, 3, 15))

    def test_set_from_datetime_accepts_a_date(self):
        self.cal.set_from_datetime(_dt.date(2024, 3, 15))
        self.assertEqual(self.cal.get_date(), _dt.date(2024, 3, 15))

    def test_leading_zeros_are_read(self):
        self.set_fields("05", "03", "2024")
        self.assertEqual(self.cal.get_date(), _dt.date(2024, 3, 5))


class TestValidity(CalendariumTestCase):

    def test_is_valid_is_a_property(self):
        # Callers write 'if not cal.is_valid:' - it must stay a property,
        # otherwise that test is always false and bad dates slip through.
        self.assertIsInstance(type(self.cal).__dict__["is_valid"], property)
        self.assertIs(self.cal.is_valid, True)

    def test_impossible_days(self):
        for day, month, year in (("31", "2", "2024"), ("30", "2", "2024"),
                                 ("31", "4", "2024"), ("32", "1", "2024"),
                                 ("0", "1", "2024"), ("1", "13", "2024"),
                                 ("1", "0", "2024")):
            with self.subTest(date=(day, month, year)):
                self.set_fields(day, month, year)
                self.assertFalse(self.cal.is_valid)
                self.assertIsNone(self.cal.get_date())

    def test_leap_years(self):
        cases = (("2024", True), ("2023", False), ("2000", True), ("1900", False))
        for year, valid in cases:
            with self.subTest(year=year):
                self.set_fields("29", "2", year)
                self.assertIs(self.cal.is_valid, valid)

    def test_empty_field_is_invalid(self):
        for part in ("day", "month", "year"):
            with self.subTest(part=part):
                self.cal.set_today()
                getattr(self.cal, part).set("")
                self.assertFalse(self.cal.is_valid)
                self.assertIsNone(self.cal.get_date())

    def test_non_numeric_value_is_invalid_not_a_crash(self):
        # The variable can be written directly, bypassing keystroke validation.
        self.set_fields("x", "1", "2024")
        self.assertFalse(self.cal.is_valid)
        self.assertIsNone(self.cal.get_date())

    def test_year_zero_is_invalid(self):
        self.set_fields("1", "1", "0")
        self.assertFalse(self.cal.is_valid)

    def test_year_range(self):
        cal = Calendarium(self.root, "Range", year_from=2000, year_to=2030)
        try:
            for year, valid in (("1999", False), ("2000", True),
                                ("2030", True), ("2031", False)):
                with self.subTest(year=year):
                    cal.day.set("1")
                    cal.month.set("1")
                    cal.year.set(year)
                    self.assertIs(cal.is_valid, valid)
        finally:
            cal.destroy()


class TestTimestamp(CalendariumTestCase):

    def test_combines_the_date_with_the_current_time(self):
        self.cal.set_date(_dt.date(2024, 3, 15))
        before = _dt.datetime.now().time()
        ts = self.cal.get_timestamp()
        after = _dt.datetime.now().time()
        self.assertEqual(ts.date(), _dt.date(2024, 3, 15))
        self.assertTrue(before <= ts.time() <= after)

    def test_none_when_invalid(self):
        self.set_fields("31", "2", "2024")
        self.assertIsNone(self.cal.get_timestamp())


class TestAdditions(CalendariumTestCase):
    """Methods added in 2.4, taken from the ttk copies in biovarase/CDTrack."""

    def test_set_days_ago(self):
        self.cal.set_days_ago(30)
        self.assertEqual(self.cal.get_date(),
                         _dt.date.today() - _dt.timedelta(days=30))

    def test_set_days_ahead(self):
        self.cal.set_days_ahead(365)
        self.assertEqual(self.cal.get_date(),
                         _dt.date.today() + _dt.timedelta(days=365))

    def test_get_iso(self):
        self.cal.set_date(_dt.date(2024, 3, 5))
        self.assertEqual(self.cal.get_iso(), "2024-03-05")

    def test_get_iso_none_when_invalid(self):
        self.set_fields("31", "2", "2024")
        self.assertIsNone(self.cal.get_iso())

    def test_set_state_applies_to_all_three(self):
        self.cal.set_state(tk.DISABLED)
        for spin in self.cal._spinboxes.values():
            self.assertEqual(str(spin.cget("state")), tk.DISABLED)
        self.cal.set_state(tk.NORMAL)
        for spin in self.cal._spinboxes.values():
            self.assertEqual(str(spin.cget("state")), tk.NORMAL)

    def test_set_focus_goes_to_the_day(self):
        # focus_lastfor, not focus_get: without a window manager (xvfb) the
        # application itself never has the focus, so focus_get answers None.
        # And the root must be mapped: Tk records no focus on a hidden window.
        self.root.deiconify()
        try:
            self.cal.pack()
            self.cal.set_focus()
            self.root.update()
            self.assertIs(self.root.focus_lastfor(), self.cal._spinboxes["day"])
        finally:
            self.root.withdraw()


class TestKeystrokeValidation(CalendariumTestCase):

    def test_digits_are_accepted(self):
        self.assertEqual(self.type_into("day", "12"), "12")

    def test_letters_and_signs_are_refused(self):
        for text in ("a", "1a", "-1", "+1", " ", "1.5", "1/2"):
            with self.subTest(text=text):
                self.assertEqual(self.type_into("day", text), "")

    def test_superscript_digits_are_refused(self):
        # '²'.isdigit() is True but int('²') raises: it must not get in.
        self.assertEqual(self.type_into("day", "²"), "")

    def test_deleting_is_always_allowed(self):
        self.type_into("year", "2024")
        spin = self.cal._spinboxes["year"]
        spin.delete(0, tk.END)
        self.assertEqual(spin.get(), "")


class TestBackground(CalendariumTestCase):

    def test_hex_colour(self):
        cal = Calendarium(self.root, "Hex", base_bg_color="#f0f0ed")
        try:
            self.assertEqual(cal.cget("background"), "#f0f0ed")
        finally:
            cal.destroy()

    def test_rgb_tuple(self):
        cal = Calendarium(self.root, "RGB", base_bg_color=(240, 240, 237))
        try:
            self.assertEqual(cal.cget("background"), "#f0f0ed")
        finally:
            cal.destroy()

    def test_rgb_out_of_range_falls_back_instead_of_crashing(self):
        cal = Calendarium(self.root, "Bad", base_bg_color=(300, 0, 0))
        try:
            self.assertEqual(cal.cget("background"), self.root.cget("background"))
        finally:
            cal.destroy()


if __name__ == "__main__":
    unittest.main()
