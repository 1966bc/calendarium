#!/usr/bin/python3
# -----------------------------------------------------------------------------
# project:  calendarium
# authors:  1966bc aka Giuseppe Costanzi
# licence:  MIT, see LICENSE
# -----------------------------------------------------------------------------
"""Calendarium in a small application: the period between two dates.

Every call goes through the public API, so this is also the place to copy
from: set_date, set_days_ago and set_today to fill a field, is_valid and
get_date to read it, get_iso to store it, set_state to lock it and
set_focus to point the operator at the one that is wrong.

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

from calendarium import Calendarium  # noqa: E402
from icon import PNG  # noqa: E402


class Main(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=8)
        self.parent = parent
        self.locked = False
        self.result = tk.StringVar()
        self.buttons = {}
        self.init_ui()

    def init_ui(self):
        dates = ttk.Frame(self)
        self.start_date = Calendarium(dates, "Start Date", year_from=1900, year_to=2100)
        self.end_date = Calendarium(dates, "End Date", year_from=1900, year_to=2100)
        self.start_date.pack(fill=tk.X, pady=(0, 6))
        self.end_date.pack(fill=tk.X)
        dates.grid(row=0, column=0, sticky=tk.NW)

        commands = ttk.Frame(self)
        items = (
            ("period", "Period", 0, self.on_period, "<Alt-p>"),
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
        commands.grid(row=0, column=1, sticky=tk.N, padx=(12, 0))

        ttk.Label(self, textvariable=self.result, anchor=tk.W).grid(
            row=1, column=0, columnspan=2, sticky=tk.EW, pady=(8, 0))

    def on_open(self):
        today = datetime.date.today()
        self.start_date.set_date(datetime.date(today.year, 1, 1))
        self.end_date.set_today()
        self.on_period()

    def get_period(self):
        """Both dates, or None after pointing at the first one that is wrong."""
        for calendar in (self.start_date, self.end_date):
            if not calendar.is_valid:
                self.result.set(f"{calendar.cget('text')} is not a valid date")
                calendar.set_focus()
                return None
        return self.start_date.get_date(), self.end_date.get_date()

    def on_period(self, evt=None):
        period = self.get_period()
        if period is None:
            return
        start, end = period
        if start > end:
            self.result.set("Start Date comes after End Date")
            self.start_date.set_focus()
            return
        days = (end - start).days
        self.result.set(
            f"From {self.start_date.get_iso()} to {self.end_date.get_iso()}: {days} days")

    def on_last_30_days(self, evt=None):
        if self.locked:
            return
        self.start_date.set_days_ago(30)
        self.end_date.set_today()
        self.on_period()

    def on_today(self, evt=None):
        if self.locked:
            return
        self.start_date.set_today()
        self.end_date.set_today()
        self.on_period()

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
