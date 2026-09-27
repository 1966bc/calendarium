#!/usr/bin/python3
# -----------------------------------------------------------------------------
# project:  calendarium
# authors:  1966bc aka Giuseppe Costanzi
# licence:  MIT, see LICENSE
# -----------------------------------------------------------------------------
"""
Calendarium - a date picker widget for Tkinter, in one file.

Day, month and year in three spinboxes. Two classes, one API:

    Calendarium     built from tk widgets, the classic look (base_bg_color)
    TtkCalendarium  built from ttk widgets, follows the ttk theme

Usage:

    from calendarium import Calendarium
    self.start_date = Calendarium(frm_left, "Start Date")
    self.start_date.pack(padx=2, pady=2)  # or grid, not both on one parent
    self.start_date.set_today()
    self.start_date.bind("<<DateChanged>>", self.on_date_changed)

    Features:
    - Set current date, or a date some days ago / ahead.
    - Validate via the read-only property is_valid and retrieve selected date.
    - Get a timestamp using the current time of day combined with the selected date.
    - Get the date as ISO 8601 text, ready to be stored.
    - Enable/disable the three fields at once, move the focus to the day.
    - Labels and order of the fields (day-month-year, month-day-year,
      year-month-day) chosen by the caller.
    - A <<DateChanged>> virtual event when the date changes.
"""

import datetime as _dt
import tkinter as tk
from tkinter import ttk

__version__ = "2.5"

#: The three parts in the order they are shown, for each accepted order.
ORDERS = {
    "dmy": ("day", "month", "year"),
    "mdy": ("month", "day", "year"),
    "ymd": ("year", "month", "day"),
}

#: Generated when the date changes, by typing, by the arrows or by a set_ method.
DATE_CHANGED = "<<DateChanged>>"


class _CalendariumBase:
    """The logic, shared by both classes: they differ only in the widgets."""

    _WIDTHS = {"day": 2, "month": 2, "year": 5}

    @staticmethod
    def _check_options(labels, order):
        """Called before the widget exists, so a bad option leaves nothing behind."""
        if order not in ORDERS:
            raise ValueError(f"order must be one of {', '.join(ORDERS)}, not {order!r}")
        labels = tuple(labels)
        if len(labels) != 3:
            raise ValueError(f"labels must be three texts, day, month and year, not {len(labels)}")
        return labels

    # Not _setup: tkinter.BaseWidget has a _setup of its own, called while the
    # widget is being built, and a mixin method of that name replaces it.
    def _init_calendarium(self, year_from, year_to, labels, order):
        self._year_from = int(year_from)
        self._year_to = int(year_to)
        self._labels = dict(zip(("day", "month", "year"), labels))
        self._order = ORDERS[order]

        today = _dt.date.today()
        self.day = tk.StringVar(self, value=str(today.day))
        self.month = tk.StringVar(self, value=str(today.month))
        self.year = tk.StringVar(self, value=str(today.year))

        self._vcmd = (self.register(self._digits_only), "%d", "%P", "%S")

        self._spinboxes = {}
        self._build_ui()

        self._pending = None
        for var in (self.day, self.month, self.year):
            var.trace_add("write", self._on_write)

    def _build_ui(self):
        ranges = {"day": (1, 31), "month": (1, 12),
                  "year": (self._year_from, self._year_to)}
        for part in self._order:
            frame = self._make_frame(self._labels[part])
            low, high = ranges[part]
            spin = self._make_spinbox(frame, part, low, high)
            frame.pack(side=tk.LEFT, fill=tk.X, padx=2)
            spin.pack(padx=2, pady=2)
            self._spinboxes[part] = spin

    def _on_write(self, *args):
        # set_date writes three variables: one event for all three, when idle.
        if self._pending is None:
            self._pending = self.after_idle(self._fire_changed)

    def _fire_changed(self):
        self._pending = None
        # Tk drops a virtual event aimed at a widget whose window does not
        # exist yet, i.e. one never displayed: a set_date while a form is
        # being built would go unannounced. winfo_id makes the window exist,
        # so the event arrives whether or not the widget has been shown.
        self.winfo_id()
        self.event_generate(DATE_CHANGED)

    def destroy(self):
        pending = getattr(self, "_pending", None)
        if pending is not None:
            self.after_cancel(pending)
            self._pending = None
        super().destroy()

    @staticmethod
    def _digits_only(action, value, text):
        # isdecimal, not isdigit: '²'.isdigit() is True but int('²') raises.
        if action == "1":
            return text.isdecimal() or value == ""
        return True

    def _parse_int(self, var):
        s = var.get()
        if s == "":
            return None
        try:
            return int(s)
        except ValueError:
            return None

    def set_today(self):
        t = _dt.date.today()
        self.set_date(t)

    def set_date(self, date_obj):
        self.day.set(str(date_obj.day))
        self.month.set(str(date_obj.month))
        self.year.set(str(date_obj.year))

    def set_from_datetime(self, dt_obj):
        if isinstance(dt_obj, _dt.datetime):
            dt_obj = dt_obj.date()
        self.set_date(dt_obj)

    def set_days_ago(self, days):
        self.set_date(_dt.date.today() - _dt.timedelta(days=days))

    def set_days_ahead(self, days):
        self.set_date(_dt.date.today() + _dt.timedelta(days=days))

    def set_state(self, state):
        """tk.NORMAL or tk.DISABLED, for all three spinboxes at once."""
        for spin in self._spinboxes.values():
            spin.configure(state=state)

    def set_focus(self):
        """Keyboard focus on the day, where an invalid date usually is."""
        self._spinboxes["day"].focus_set()

    @property
    def is_valid(self):
        d = self._parse_int(self.day)
        m = self._parse_int(self.month)
        y = self._parse_int(self.year)
        if d is None or m is None or y is None:
            return False
        if not (self._year_from <= y <= self._year_to):
            return False
        try:
            _dt.date(y, m, d)
            return True
        except ValueError:
            return False

    def get_date(self):
        if not self.is_valid:
            return None
        return _dt.date(int(self.year.get()), int(self.month.get()), int(self.day.get()))

    def get_timestamp(self):
        d = self.get_date()
        if d is None:
            return None
        now = _dt.datetime.now().time()
        return _dt.datetime.combine(d, now)

    def get_iso(self):
        """The date as ISO 8601 text (YYYY-MM-DD), or None if invalid."""
        d = self.get_date()
        if d is None:
            return None
        return d.isoformat()


class Calendarium(_CalendariumBase, tk.LabelFrame):
    """Composite date widget using three tk Spinboxes (day, month, year)."""

    def __init__(
        self,
        parent,
        name,
        *,
        base_bg_color=None,
        year_from=_dt.MINYEAR,
        year_to=_dt.MAXYEAR,
        labels=("Day", "Month", "Year"),
        order="dmy",
        **kwargs
    ) -> None:
        labels = self._check_options(labels, order)
        super().__init__(parent, text=name, **kwargs)
        self._set_label_frame_background(base_bg_color)
        self._init_calendarium(year_from, year_to, labels, order)

    def _make_frame(self, text):
        return tk.LabelFrame(self, text=text, bg=self._base_bg_color)

    def _make_spinbox(self, frame, part, low, high):
        return tk.Spinbox(frame, width=self._WIDTHS[part], from_=low, to=high,
                          fg="blue", textvariable=getattr(self, part),
                          validate="key", validatecommand=self._vcmd)

    def _set_label_frame_background(self, base_bg_color=None):
        color = base_bg_color

        if isinstance(color, tuple) and len(color) == 3:
            try:
                r, g, b = color
                color = f"#{r:02x}{g:02x}{b:02x}"
            except (TypeError, ValueError):
                color = None

        # Formatting never fails on out-of-range values ((300, 0, 0) gives
        # "#12c0000"): only Tk can tell whether a colour is real, so ask it.
        if color is not None:
            try:
                self.winfo_rgb(color)
            except tk.TclError:
                color = None

        if color is None:
            try:
                color = self.cget("bg")  # fallback to current theme color
            except tk.TclError:
                color = "#d9d9d9"  # final safe fallback (light gray)

        self._base_bg_color = color
        try:
            self.configure(background=color)
        except tk.TclError:
            pass


class TtkCalendarium(_CalendariumBase, ttk.LabelFrame):
    """The same widget built from ttk, so it follows the ttk theme.

    No base_bg_color: with ttk the colours belong to the style.
    """

    _WIDTHS = {"day": 3, "month": 3, "year": 5}

    def __init__(
        self,
        parent,
        name,
        *,
        year_from=_dt.MINYEAR,
        year_to=_dt.MAXYEAR,
        labels=("Day", "Month", "Year"),
        order="dmy",
        **kwargs
    ) -> None:
        labels = self._check_options(labels, order)
        super().__init__(parent, text=name, **kwargs)
        self._init_calendarium(year_from, year_to, labels, order)

    def _make_frame(self, text):
        return ttk.LabelFrame(self, text=text)

    def _make_spinbox(self, frame, part, low, high):
        return ttk.Spinbox(frame, width=self._WIDTHS[part], from_=low, to=high,
                           justify=tk.CENTER, textvariable=getattr(self, part),
                           validate="key", validatecommand=self._vcmd)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Calendarium")

    classic = Calendarium(root, "Calendarium")
    themed = TtkCalendarium(root, "TtkCalendarium", order="ymd")
    classic.pack(padx=8, pady=(8, 4))
    themed.pack(padx=8, pady=4)

    shown = tk.StringVar(root)

    def show(evt=None):
        shown.set(f"{classic.get_iso() or 'invalid'}   {themed.get_iso() or 'invalid'}")

    for calendar in (classic, themed):
        calendar.bind(DATE_CHANGED, show)
    show()

    tk.Label(root, textvariable=shown).pack(padx=8, pady=(4, 8))
    root.mainloop()
