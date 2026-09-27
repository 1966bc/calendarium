# Changelog

All notable changes to Calendarium, newest first. Earlier history is in the
git log.

## [Unreleased]

### Added

- Packaging for PyPI: `pyproject.toml` (setuptools, SPDX licence), so
  `pip install calendarium` works. The version is `calendarium.__version__`,
  read by the build, instead of a line in the docstring.
- `tools/make_social_preview.py` composes `docs/social-preview.png`, the
  1280x640 image GitHub shows when the repository is shared, from
  `docs/demo-large.png`, a capture of the demo drawn at a larger scale.

### Changed

- Demo: the Period button is gone - the period is recalculated as you type,
  through `<<DateChanged>>`. A **Date format** choice (Europe, USA, ISO)
  rebuilds the two widgets in the new order, keeping what was typed.
- README: a section on the date format, `order` and `labels`; installation
  with pip; absolute links, which PyPI needs.

## [2.5] - 2026-09-27

### Added

- `TtkCalendarium`: the same widget and API, built from ttk widgets so it
  follows the ttk theme. `Calendarium` stays tk and unchanged.
- `labels=`: the captions of the three fields, e.g.
  `("Giorno", "Mese", "Anno")`. Always given as day, month, year.
- `order=`: `"dmy"` (default), `"mdy"` or `"ymd"`, the order of the fields
  on screen. A wrong order or labels raise `ValueError` before any widget
  is created.
- `<<DateChanged>>` (also `calendarium.DATE_CHANGED`): a virtual event when
  the date changes, by typing, by the arrows or by a `set_` method. One
  event per change, even when `set_date` writes three fields, and it
  arrives even if the widget has not been displayed yet.
- Tests run on both classes: 87 in all.

### Changed

- The day, month and year variables belong to the widget (`StringVar(self)`)
  instead of the default root.
- The demo follows the dates as they change, through `<<DateChanged>>`.
- `python3 calendarium.py` shows both classes side by side.

## [2.4] - 2026-09-27

### Added

- Unit tests in `tests/`, standard library `unittest` only. They are skipped
  when Tk has no display, and run under `xvfb-run -a`.
- `set_days_ago(n)` and `set_days_ahead(n)`: today minus or plus `n` days.
- `get_iso()`: the date as `"YYYY-MM-DD"`, or `None` if not valid.
- `set_state(state)`: `tk.NORMAL` or `tk.DISABLED` for all three spinboxes.
- `set_focus()`: the keyboard on the day.
- An icon for the demo, drawn by `tools/make_icon.py`.

### Fixed

- An out-of-range RGB background such as `(300, 0, 0)` crashed the
  constructor with `invalid color name`. The colour is now checked with Tk
  and an invalid one falls back to the theme colour.
- The spinboxes accepted `²` and other characters that `isdigit()` calls
  digits and `int()` refuses. The check now uses `isdecimal()`.

### Changed

- The demo is `examples/demo.py`, rewritten to use only the public API. It
  imports the widget from the root of the repository instead of keeping a
  copy of it, which had drifted out of date.
- `tkinter.messagebox` is imported only by the `__main__` demo, no longer by
  the widget.
- Repository layout: `examples/`, `tests/`, `tools/`, `docs/`.
- The source headers state the licence as MIT, as in `LICENSE`. The old
  docstring said GNU GPL v3, which contradicted it.
- README rewritten: requirements, installation, constructor and methods.
