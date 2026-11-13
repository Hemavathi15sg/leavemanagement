# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- Install: `pip install -r requirements.txt` (Python 3.10+)
- Create or reset the database: `python seed.py`. This deletes `leave.db` and reseeds it. Run it before the app, because `app.py` never creates the schema.
- Run the app: `python app.py` (Flask debug mode, http://127.0.0.1:5000)
- Run all tests: `pytest`
- Run one test: `pytest test_leave.py::test_balance_subtracts_approved_leave`
- Lint/format: none configured.

Run everything from the repo root. `src/` has no `__init__.py`, so the `src.leave` imports rely on namespace packages and resolve only from the root.

## Architecture

- `app.py`: all Flask routes in one module. `/` serves `index.html`. Approve and reject both go through `change_status()`, which re-checks the balance before approving.
- `src/leave/rules.py`: pure business rules with no I/O. Accrual is 2.0 days per month, capped at 24 per year. `balance()` and `working_days()` (Mon–Fri only) are also here. This is the only place accrual is defined. The README still says 1.5 days per month.
- `src/leave/db.py`: thin sqlite3 wrapper with `sqlite3.Row` rows and a raw SQL schema string. No ORM. The path comes from the `LEAVE_DB` env var, defaulting to `leave.db`.
- `index.html`: a single file of vanilla JS that calls `/api/*`. There is no build step and no separate static directory.

## Key behaviour

- Balance is derived, not stored: `opening_balance + accrued_days(months_worked) - sum(approved days)`. Only `opening_balance` and `months_worked` are stored, and nothing increments `months_worked`.
- Pending requests do not reserve days, so two pending requests can overbook. The FIXME in `create_request` covers this.
- Request states: `pending` → `approved` or `rejected`. Only pending requests can change state (409 otherwise).
- Tests cover only `src/leave/rules.py`. The API routes and `db.py` have no tests.
- Open work is marked with TODO/FIXME comments in `app.py` and `src/leave/rules.py`. Search for them rather than assuming they are complete.
