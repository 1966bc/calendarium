#!/usr/bin/python3
# -----------------------------------------------------------------------------
# project:  calendarium
# authors:  1966bc aka Giuseppe Costanzi
# licence:  MIT, see LICENSE
# -----------------------------------------------------------------------------
"""
Calendarium - a date picker widget for Tkinter, in one file.

Usage:

    from calendarium import Calendarium
    self.start_date = Calendarium(frm_left, "Start Date")
    self.start_date.pack(padx=2, pady=2)  # or grid, not both on one parent
    self.start_date.set_today()

    Features:
    - Set current date, or a date some days ago / ahead.
    - Validate via the read-only property is_valid and retrieve selected date.
    - Get a timestamp using the current time of day combined with the selected date.
    - Get the date as ISO 8601 text, ready to be stored.
    - Enable/disable the three fields at once, move the focus to the day.

Version: 2.4
"""

import datetime as _dt
import tkinter as tk


class Calendarium(tk.LabelFrame):
    """Composite date widget using three Spinboxes (day, month, year)."""

    def __init__(
        self,
        parent,
        name,
        *,
        base_bg_color=None,
        year_from=_dt.MINYEAR,
        year_to=_dt.MAXYEAR,
        **kwargs
    ) -> None:
        super().__init__(parent, text=name, **kwargs)

        self._year_from = int(year_from)
        self._year_to = int(year_to)

        today = _dt.date.today()
        self.day = tk.StringVar(value=str(today.day))
        self.month = tk.StringVar(value=str(today.month))
        self.year = tk.StringVar(value=str(today.year))

        self._vcmd = (self.register(self._digits_only), "%d", "%P", "%S")

        self._set_label_frame_background(base_bg_color)

        self._spinboxes = {}
        self._build_ui()

    def _build_ui(self):
        lf_kwargs = {"bg": getattr(self, "_base_bg_color", None)}

        day_frame = tk.LabelFrame(self, text="Day", **lf_kwargs)
        day_spin = tk.Spinbox(day_frame, width=2, from_=1, to=31, fg="blue", textvariable=self.day, validate="key", validatecommand=self._vcmd)
        day_frame.pack(side=tk.LEFT, fill=tk.X, padx=2)
        day_spin.pack(padx=2, pady=2)
        self._spinboxes["day"] = day_spin

        month_frame = tk.LabelFrame(self, text="Month", **lf_kwargs)
        month_spin = tk.Spinbox(month_frame, width=2, from_=1, to=12, fg="blue", textvariable=self.month, validate="key", validatecommand=self._vcmd)
        month_frame.pack(side=tk.LEFT, fill=tk.X, padx=2)
        month_spin.pack(padx=2, pady=2)
        self._spinboxes["month"] = month_spin

        year_frame = tk.LabelFrame(self, text="Year", **lf_kwargs)
        year_spin = tk.Spinbox(year_frame, width=5, fg="blue", from_=self._year_from, to=self._year_to, textvariable=self.year, validate="key", validatecommand=self._vcmd)
        year_frame.pack(side=tk.LEFT, fill=tk.X, padx=2)
        year_spin.pack(padx=2, pady=2)
        self._spinboxes["year"] = year_spin

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


if __name__ == "__main__":
    from tkinter import messagebox

    root = tk.Tk()
    root.title("Calendarium Demo")

    my_cal = Calendarium(root, "Select Date")
    my_cal.pack(padx=8, pady=8)
    my_cal.set_today()

    def show_date():
        result = my_cal.get_date()
        if result is not None:
            messagebox.showinfo("Selected Date", str(result))
        else:
            messagebox.showwarning("Selected Date", "Invalid date")

    def show_timestamp():
        result = my_cal.get_timestamp()
        if result is not None:
            messagebox.showinfo("Timestamp", str(result))
        else:
            messagebox.showwarning("Timestamp", "Invalid date")

    tk.Button(root, text="Get Date", command=show_date).pack(pady=5)
    tk.Button(root, text="Get Timestamp", command=show_timestamp).pack(pady=5)

    root.mainloop()
