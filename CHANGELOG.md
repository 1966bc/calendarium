# Changelog

All notable changes to Calendarium, newest first. Earlier history is in the
git log.

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
