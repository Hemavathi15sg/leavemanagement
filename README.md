# Leave Management

A small app for tracking annual leave: a Flask API, a sigle-page UI and SQLite.

## Features

- Employee leave balances
- Leave requests with approve and reject
- Leave accrues at 1.5 days per month worked

## Setup

1. Install Python 3.10 or later.
2. `pip install -r requirements.txt`
3. `python seed.py` creates the database with demo data.
4. `python app.py`, then open http://127.0.0.1:5000

## Tests

`pytest`
