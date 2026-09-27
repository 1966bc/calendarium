#!/usr/bin/python3
# -----------------------------------------------------------------------------
# project:  calendarium
# authors:  1966bc aka Giuseppe Costanzi
# licence:  MIT, see LICENSE
# -----------------------------------------------------------------------------
"""
Unit tests for Calendarium and TtkCalendarium.

Run from the repository root:

    python3 -m unittest discover -s tests -v

The two classes share one API, so every behaviour is tested on both: the
shared tests live in WidgetTests and run once per class. What belongs to one
class only (the tk background, the ttk look) is tested apart.

Tk needs a display. Without one (e.g. a headless CI) the tests are skipped.
"""

import datetime as _dt
import tkinter as tk
import unittest
from tkinter import ttk

from calendarium import DATE_CHANGED, ORDERS, Calendarium, TtkCalendarium


def _make_root():
    try:
        root = tk.Tk()
    except tk.TclError:
        return None
    root.withdraw()
    return root


class RootTestCase(unittest.TestCase):
    """One hidden Tk root for the whole class: creating it is the slow part."""

    widget = Calendarium
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
        self.cal = self.make("Test")

    def tearDown(self):
        self.cal.destroy()

    def make(self, name="Other", **kwargs):
        """A second widget, destroyed at the end of the test."""
        cal = self.widget(self.root, name, **kwargs)
        self.addCleanup(cal.destroy)
        return cal

    def set_fields(self, day, month, year, cal=None):
        cal = cal or self.cal
        cal.day.set(day)
        cal.month.set(month)
        cal.year.set(year)

    def type_into(self, part, text):
        """Insert text into a spinbox the way a keystroke does, through validation."""
        spin = self.cal._spinboxes[part]
        spin.delete(0, tk.END)
        spin.insert(tk.END, text)
        return spin.get()


class WidgetTests:
    """The shared API. Mixed into one TestCase per class, at the bottom."""

    # --- construction -------------------------------------------------------

    def test_starts_on_today(self):
        self.assertEqual(self.cal.get_date(), _dt.date.today())

    def test_caption_is_the_labelframe_text(self):
        self.assertEqual(str(self.cal.cget("text")), "Test")

    def test_variables_are_stringvars(self):
        for var in (self.cal.day, self.cal.month, self.cal.year):
            self.assertIsInstance(var, tk.StringVar)

    # --- set and get --------------------------------------------------------

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

    def test_leading_zeros_are_read_as_decimal(self):
        self.set_fields("08", "09", "2024")
        self.assertEqual(self.cal.get_date(), _dt.date(2024, 9, 8))
        self.set_fields("1", "010", "02024")
        self.assertEqual(self.cal.get_date(), _dt.date(2024, 10, 1))

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

    # --- validity -----------------------------------------------------------

    def test_is_valid_is_a_property(self):
        # Callers write 'if not cal.is_valid:' - it must stay a property,
        # otherwise that test is always false and bad dates slip through.
        self.assertIsInstance(getattr(self.widget, "is_valid"), property)
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
        cal = self.make(year_from=2000, year_to=2030)
        for year, valid in (("1999", False), ("2000", True),
                            ("2030", True), ("2031", False)):
            with self.subTest(year=year):
                self.set_fields("1", "1", year, cal)
                self.assertIs(cal.is_valid, valid)

    def test_every_reader_answers_none_when_invalid(self):
        self.set_fields("31", "2", "2024")
        self.assertIsNone(self.cal.get_date())
        self.assertIsNone(self.cal.get_iso())
        self.assertIsNone(self.cal.get_timestamp())

    # --- timestamp ----------------------------------------------------------

    def test_timestamp_combines_the_date_with_the_current_time(self):
        self.cal.set_date(_dt.date(2024, 3, 15))
        before = _dt.datetime.now().time()
        ts = self.cal.get_timestamp()
        after = _dt.datetime.now().time()
        self.assertEqual(ts.date(), _dt.date(2024, 3, 15))
        self.assertTrue(before <= ts.time() <= after)

    # --- keystrokes ---------------------------------------------------------

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

    # --- state and focus ----------------------------------------------------

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
            self.cal.pack_forget()
            self.root.withdraw()

    def test_set_focus_goes_to_the_day_whatever_the_order(self):
        cal = self.make(order="ymd")
        self.root.deiconify()
        try:
            cal.pack()
            cal.set_focus()
            self.root.update()
            self.assertIs(self.root.focus_lastfor(), cal._spinboxes["day"])
        finally:
            cal.pack_forget()
            self.root.withdraw()

    # --- labels and order ---------------------------------------------------

    def get_shown(self, cal):
        """The parts in the order they appear, left to right."""
        frames = [str(frame) for frame in cal.pack_slaves()]
        by_frame = {str(spin.master): part for part, spin in cal._spinboxes.items()}
        return tuple(by_frame[frame] for frame in frames)

    def test_default_labels(self):
        texts = [str(self.cal._spinboxes[p].master.cget("text"))
                 for p in ("day", "month", "year")]
        self.assertEqual(texts, ["Day", "Month", "Year"])

    def test_labels_are_given_as_day_month_year(self):
        cal = self.make(labels=("Giorno", "Mese", "Anno"), order="ymd")
        texts = {p: str(cal._spinboxes[p].master.cget("text"))
                 for p in ("day", "month", "year")}
        self.assertEqual(texts, {"day": "Giorno", "month": "Mese", "year": "Anno"})

    def test_default_order_is_day_month_year(self):
        self.assertEqual(self.get_shown(self.cal), ("day", "month", "year"))

    def test_every_order_is_shown_as_asked(self):
        for order, parts in ORDERS.items():
            with self.subTest(order=order):
                self.assertEqual(self.get_shown(self.make(order=order)), parts)

    def test_order_does_not_change_the_date(self):
        cal = self.make(order="mdy")
        cal.set_date(_dt.date(2024, 3, 5))
        self.assertEqual(cal.get_date(), _dt.date(2024, 3, 5))
        self.assertEqual(cal.get_iso(), "2024-03-05")

    def test_unknown_order_is_refused_and_leaves_nothing(self):
        before = len(self.root.winfo_children())
        with self.assertRaises(ValueError):
            self.widget(self.root, "Bad", order="dym")
        self.assertEqual(len(self.root.winfo_children()), before)

    def test_wrong_number_of_labels_is_refused_and_leaves_nothing(self):
        before = len(self.root.winfo_children())
        with self.assertRaises(ValueError):
            self.widget(self.root, "Bad", labels=("Day", "Month"))
        self.assertEqual(len(self.root.winfo_children()), before)

    # --- <<DateChanged>> ----------------------------------------------------

    def count_events(self, cal):
        seen = []
        cal.bind(DATE_CHANGED, lambda evt: seen.append(evt.widget))
        return seen

    def test_set_date_fires_one_event_not_three(self):
        seen = self.count_events(self.cal)
        self.cal.set_date(_dt.date(2024, 3, 5))
        self.root.update()
        self.assertEqual(seen, [self.cal])

    def test_typing_fires_the_event(self):
        seen = self.count_events(self.cal)
        self.type_into("day", "12")
        self.root.update()
        self.assertEqual(len(seen), 1)

    def test_an_invalid_date_fires_too(self):
        # The event says the fields changed; is_valid says what they hold.
        seen = self.count_events(self.cal)
        self.set_fields("31", "2", "2024")
        self.root.update()
        self.assertEqual(len(seen), 1)
        self.assertFalse(self.cal.is_valid)

    def test_no_change_no_event(self):
        seen = self.count_events(self.cal)
        self.root.update()
        self.assertEqual(seen, [])

    def test_destroy_with_an_event_pending_is_clean(self):
        errors = []
        saved = self.root.report_callback_exception
        self.root.report_callback_exception = lambda *exc: errors.append(exc)
        try:
            cal = self.widget(self.root, "Gone")
            cal.set_date(_dt.date(2024, 3, 5))
            cal.destroy()
            self.root.update()
        finally:
            self.root.report_callback_exception = saved
        self.assertEqual(errors, [])


class TestCalendarium(WidgetTests, RootTestCase):
    widget = Calendarium

    def test_is_a_tk_labelframe(self):
        self.assertIsInstance(self.cal, tk.LabelFrame)
        for spin in self.cal._spinboxes.values():
            self.assertIsInstance(spin, tk.Spinbox)

    def test_hex_colour(self):
        cal = self.make(base_bg_color="#f0f0ed")
        self.assertEqual(cal.cget("background"), "#f0f0ed")

    def test_rgb_tuple(self):
        cal = self.make(base_bg_color=(240, 240, 237))
        self.assertEqual(cal.cget("background"), "#f0f0ed")

    def test_rgb_out_of_range_falls_back_instead_of_crashing(self):
        cal = self.make(base_bg_color=(300, 0, 0))
        self.assertEqual(cal.cget("background"), self.root.cget("background"))

    def test_invalid_colour_name_falls_back_instead_of_crashing(self):
        cal = self.make(base_bg_color="not-a-colour")
        self.assertEqual(cal.cget("background"), self.root.cget("background"))


class TestTtkCalendarium(WidgetTests, RootTestCase):
    widget = TtkCalendarium

    def test_is_a_ttk_labelframe(self):
        self.assertIsInstance(self.cal, ttk.LabelFrame)
        for spin in self.cal._spinboxes.values():
            self.assertIsInstance(spin, ttk.Spinbox)

    def test_has_no_background_option(self):
        # With ttk the colours belong to the style: Tk refuses the option.
        with self.assertRaises(tk.TclError):
            TtkCalendarium(self.root, "Bad", base_bg_color="#f0f0ed")


if __name__ == "__main__":
    unittest.main()
