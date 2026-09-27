# Calendarium

**A date picker widget for Tkinter.** Day, month and year in three spinboxes,
validated as you type, with the result as a `datetime.date`. One Python file,
standard library only: copy it into your project and use it.

![Calendarium demo](https://raw.githubusercontent.com/1966bc/calendarium/master/docs/screenshot.png)

- **No dependencies** — `tkinter` and `datetime`, nothing to install.
- **One file** — `calendarium.py`, nothing else to carry around.
- **Keyboard first** — the user types the date; no pop-up calendar to click through.
- **Digits only** — letters and signs are refused as they are typed.
- **A date or `None`** — never a half-valid value: 31 February is `None`.
- **tk or ttk** — `Calendarium` for the classic look, `TtkCalendarium` to follow the ttk theme.
- **Any language, any order** — your own labels; day-month-year, month-day-year or year-month-day.
- **`<<DateChanged>>`** — a virtual event whenever the date changes.

## Requirements

Python 3.6 or later, with Tk. On Debian and Ubuntu Tk is a separate package:

```bash
sudo apt install python3-tk
```

## Installation

```bash
pip install calendarium
```

Or copy `calendarium.py` next to your code: it is one file with no
dependencies, so that is all it takes, also on a machine without pip.

## Usage

```python
import tkinter as tk
from calendarium import Calendarium

root = tk.Tk()

start_date = Calendarium(root, "Start Date")
start_date.pack(padx=8, pady=8)   # or .grid(row=0, column=0, sticky=tk.W)
start_date.set_today()

def on_save():
    if not start_date.is_valid:
        start_date.set_focus()
        return
    print(start_date.get_iso())   # "2026-09-27"

tk.Button(root, text="Save", command=on_save).pack(pady=8)
root.mainloop()
```

Use either `grid` or `pack` on the same parent, not both.

The same with ttk, Italian labels and the year first:

```python
from calendarium import TtkCalendarium

start_date = TtkCalendarium(root, "Data inizio",
                            labels=("Giorno", "Mese", "Anno"), order="ymd")
```

## Date format: European, American, ISO

The `order` argument decides the order of the three fields on screen:

| `order` | fields on screen | used in |
|---|---|---|
| `"dmy"` (default) | Day · Month · Year | Europe and most of the world |
| `"mdy"` | Month · Day · Year | United States |
| `"ymd"` | Year · Month · Day | ISO 8601, China, Japan, Korea |

```python
european = Calendarium(root, "Start Date")                # 27 · 9 · 2026
american = Calendarium(root, "Start Date", order="mdy")   # 9 · 27 · 2026
iso      = Calendarium(root, "Start Date", order="ymd")   # 2026 · 9 · 27
```

What changes is **only what the user sees**. The date itself is the same:
`get_date()` returns the same `datetime.date` and `get_iso()` the same
`"2026-09-27"` whatever the order, so the rest of your program does not need
to know which format the user chose.

`labels` names the fields in your language. They are always given as day,
month, year, whatever the order on screen:

```python
Calendarium(root, "Data inizio", labels=("Giorno", "Mese", "Anno"))
Calendarium(root, "Start Date", order="mdy")              # Month · Day · Year
```

The order is fixed when the widget is built. To let the user switch format
while the program runs, build the widget again in the new order and copy the
three fields across (`day`, `month`, `year` are `StringVar`s): the demo does
exactly this, with its **Date format** choice.

## Constructor

```python
Calendarium(parent, name, *, base_bg_color=None,
            year_from=datetime.MINYEAR, year_to=datetime.MAXYEAR,
            labels=("Day", "Month", "Year"), order="dmy", **kwargs)

TtkCalendarium(parent, name, *,
               year_from=datetime.MINYEAR, year_to=datetime.MAXYEAR,
               labels=("Day", "Month", "Year"), order="dmy", **kwargs)
```

| argument | meaning |
|---|---|
| `parent` | the parent widget |
| `name` | the caption of the frame, e.g. `"Start Date"`; `""` for none |
| `base_bg_color` | `Calendarium` only: background, as `"#f0f0ed"` or `(240, 240, 237)`; an invalid colour falls back to the theme. With ttk, colours belong to the style |
| `year_from`, `year_to` | the range of years accepted; outside it the date is not valid |
| `labels` | the captions of the three fields, always given as day, month, year — whatever the order on screen |
| `order` | `"dmy"` (default), `"mdy"` or `"ymd"`: the order of the fields on screen |
| `**kwargs` | passed on to `tk.LabelFrame` or `ttk.LabelFrame` |

A wrong `order` or a `labels` that is not three texts raises `ValueError`.

## Methods

| method | what it does |
|---|---|
| `set_today()` | set today's date |
| `set_date(date)` | set a `datetime.date` |
| `set_from_datetime(value)` | set from a `datetime.datetime` (the time is dropped) or a `date` |
| `set_days_ago(n)` | today minus `n` days |
| `set_days_ahead(n)` | today plus `n` days |
| `is_valid` | `True` if the three fields make a real date in range |
| `get_date()` | the `datetime.date`, or `None` if not valid |
| `get_iso()` | the date as `"YYYY-MM-DD"`, ready to store, or `None` |
| `get_timestamp()` | the date with the current time of day, or `None` |
| `set_state(state)` | `tk.NORMAL` or `tk.DISABLED`, for all three spinboxes |
| `set_focus()` | put the keyboard on the day |

**`is_valid` is a property: write it without parentheses.**
`if not start_date.is_valid:` is right. With parentheses Python raises
`TypeError: 'bool' object is not callable`.

The three fields are also available as `StringVar`s: `day`, `month`, `year`.

## Following changes

```python
from calendarium import DATE_CHANGED   # "<<DateChanged>>"

start_date.bind(DATE_CHANGED, on_date_changed)
```

The event is generated when the date changes by typing, by the arrows or by
a `set_` method, and also when it becomes invalid: check `is_valid` in the
handler. `set_date` writes three fields but generates one event, when Tk is
idle. It arrives even if the widget has not been displayed yet.

## Demo

```bash
python3 examples/demo.py
```

The period between two dates, recalculated as you type. The **Date format**
choice switches the fields between European, American and ISO order, keeping
what you typed; **Lock** disables them. For a quick look at the two classes
side by side:

```bash
python3 calendarium.py
```

## Tests

Standard library `unittest`. From the root of the repository:

```bash
python3 -m unittest discover -s tests -v
```

Tk needs a display. Without one, run them under `xvfb-run -a`, otherwise they
are skipped.

## Repository layout

```
calendarium.py      the widget: the one file to copy
examples/demo.py    a small application that uses it
tests/              unit tests
tools/              build tools, they need Pillow: make_icon.py draws the demo
                    icon, make_social_preview.py the GitHub social preview
docs/               the screenshots and the social preview
```

## License

MIT, see [LICENSE](https://github.com/1966bc/calendarium/blob/master/LICENSE).

Author: Giuseppe Costanzi ([1966bc](https://github.com/1966bc)).

Calendarium is primitive, but it works and it's light.
