#!/usr/bin/python3
# -----------------------------------------------------------------------------
# project:  calendarium
# authors:  1966bc aka Giuseppe Costanzi
# licence:  MIT, see LICENSE
# -----------------------------------------------------------------------------
"""Calendarium in a small application: the period between two dates.

Every call goes through the public API, so this is also the place to copy
from: set_date, set_days_ago and set_today to fill a field, is_valid and
get_date to read it, get_iso to store it, set_state to lock it, set_focus
to put the keyboard on it, <<DateChanged>> to follow every change as it
happens, and order= to show the date the European, American or ISO way.

    python3 examples/demo.py
"""

import datetime
import os
import sys
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

# The widget is the one file at the root of the repository, the file you copy
# into your own project. The demo imports it from there instead of keeping a
# copy of its own, which is how copies drift apart.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calendarium import DATE_CHANGED, Calendarium  # noqa: E402
from icon import PNG  # noqa: E402

#: (order, radio button text, underlined letter, accelerator)
FORMATS = (
    ("dmy", "Europe  dd mm yyyy", 0, "<Alt-e>"),
    ("mdy", "USA  mm dd yyyy", 0, "<Alt-u>"),
    ("ymd", "ISO  yyyy mm dd", 0, "<Alt-i>"),
)


class Main(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=8)
        self.parent = parent
        self.locked = False
        self.order = tk.StringVar(value="dmy")
        self.result = tk.StringVar()
        self.buttons = {}
        self.start_date = None
        self.end_date = None
        self.init_ui()

    def init_ui(self):
        self.dates = ttk.Frame(self)
        self.dates.grid(row=0, column=0, sticky=tk.NW)
        self.build_calendars()

        formats = ttk.LabelFrame(self, text="Date format", padding=4)
        for order, text, underline, key in FORMATS:
            ttk.Radiobutton(formats, text=text, underline=underline, value=order,
                            variable=self.order, command=self.on_format).pack(anchor=tk.W)
            self.parent.bind(key, lambda evt, order=order: self.set_format(order))
        formats.grid(row=1, column=0, sticky=tk.EW, pady=(6, 0))

        commands = ttk.Frame(self)
        items = (
            ("last", "Last 30 days", 0, self.on_last_30_days, "<Alt-l>"),
            ("today", "Today", 0, self.on_today, "<Alt-t>"),
            ("lock", "Lock", 3, self.on_lock, "<Alt-k>"),
            ("close", "Close", 0, self.on_close, "<Alt-c>"),
        )
        for name, text, underline, cmd, key in items:
            button = ttk.Button(commands, text=text, underline=underline, command=cmd)
            button.pack(fill=tk.X, pady=2)
            self.buttons[name] = button
            self.parent.bind(key, cmd)
        commands.grid(row=0, column=1, rowspan=2, sticky=tk.N, padx=(12, 0))

        ttk.Label(self, textvariable=self.result, anchor=tk.W).grid(
            row=2, column=0, columnspan=2, sticky=tk.EW, pady=(8, 0))

    def build_calendars(self):
        """The two widgets, in the chosen order, keeping what they held.

        The order of the fields is fixed when a widget is built, so a new
        format means new widgets. What was typed is carried over as text,
        so that a date still being written survives the change too.
        """
        texts = None
        if self.start_date is not None:
            texts = [(cal.day.get(), cal.month.get(), cal.year.get())
                     for cal in (self.start_date, self.end_date)]
            self.start_date.destroy()
            self.end_date.destroy()

        order = self.order.get()
        self.start_date = Calendarium(self.dates, "Start Date", order=order,
                                      year_from=1900, year_to=2100)
        self.end_date = Calendarium(self.dates, "End Date", order=order,
                                    year_from=1900, year_to=2100)
        self.start_date.pack(fill=tk.X, pady=(0, 6))
        self.end_date.pack(fill=tk.X)

        for calendar in (self.start_date, self.end_date):
            calendar.bind(DATE_CHANGED, self.on_date_changed)
            if self.locked:
                calendar.set_state(tk.DISABLED)

        if texts is not None:
            for calendar, (day, month, year) in zip((self.start_date, self.end_date), texts):
                calendar.day.set(day)
                calendar.month.set(month)
                calendar.year.set(year)

    def on_open(self):
        today = datetime.date.today()
        self.start_date.set_date(datetime.date(today.year, 1, 1))
        self.end_date.set_today()
        self.show_period()

    def show_period(self):
        """Say what the two dates make, or which one is not a date."""
        for calendar in (self.start_date, self.end_date):
            if not calendar.is_valid:
                self.result.set(f"{calendar.cget('text')} is not a valid date")
                return
        start, end = self.start_date.get_date(), self.end_date.get_date()
        if start > end:
            self.result.set("Start Date comes after End Date")
            return
        days = (end - start).days
        self.result.set(
            f"From {self.start_date.get_iso()} to {self.end_date.get_iso()}: {days} days")

    def on_date_changed(self, evt=None):
        self.show_period()

    def set_format(self, order):
        self.order.set(order)
        self.on_format()

    def on_format(self, evt=None):
        self.build_calendars()
        self.show_period()
        if not self.locked:
            self.start_date.set_focus()

    def on_last_30_days(self, evt=None):
        if self.locked:
            return
        self.start_date.set_days_ago(30)
        self.end_date.set_today()

    def on_today(self, evt=None):
        if self.locked:
            return
        self.start_date.set_today()
        self.end_date.set_today()

    def on_lock(self, evt=None):
        self.locked = not self.locked
        state = tk.DISABLED if self.locked else tk.NORMAL
        for calendar in (self.start_date, self.end_date):
            calendar.set_state(state)
        for name in ("last", "today"):
            self.buttons[name].configure(state=state)
        self.buttons["lock"].configure(
            text="Unlock" if self.locked else "Lock",
            underline=5 if self.locked else 3)

    def on_close(self, evt=None):
        self.parent.on_exit()


class App(tk.Tk):
    """Start here."""

    def __init__(self):
        super().__init__()
        self.protocol("WM_DELETE_WINDOW", self.on_exit)
        self.set_title()
        self.set_icon()
        main = Main(self)
        main.pack(fill=tk.BOTH, expand=1)
        main.on_open()

    def set_title(self):
        self.title("Calendarium Demo")

    def set_icon(self):
        # Kept on the instance: a PhotoImage nobody holds is collected,
        # leaving an empty icon.
        self.icon = tk.PhotoImage(data="".join(PNG))
        self.iconphoto(True, self.icon)

    def on_exit(self):
        if messagebox.askokcancel(self.title(), "Do you want to quit?", parent=self):
            self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
