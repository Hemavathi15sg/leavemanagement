from datetime import date

from src.leave.rules import accrued_days, balance, days_in_year, working_days


def test_accrual_is_two_days_per_month():
    assert accrued_days(3) == 6.0


def test_accrual_is_capped_at_24_days():
    assert accrued_days(20) == 24.0


def test_working_days_skip_weekend():
    # Mon 9 Nov 2026 to Sun 15 Nov 2026
    assert working_days(date(2026, 11, 9), date(2026, 11, 15)) == 5


def test_balance_subtracts_approved_leave():
    assert balance(opening=3, months_worked=14, approved_days=7) == 20.0


def test_balance_includes_carried_days():
    # 5 carried + 2 months worked (4 earned) = 9 available
    assert balance(opening=0, months_worked=2, approved_days=0, carried_days=5) == 9.0


def test_days_in_year_inside_one_year():
    assert days_in_year(date(2026, 11, 9), date(2026, 11, 15), 2026) == 5


def test_days_in_year_outside_year_is_zero():
    assert days_in_year(date(2026, 11, 9), date(2026, 11, 15), 2027) == 0


def test_days_in_year_splits_request_across_new_year():
    # Mon 28 Dec 2026 to Tue 5 Jan 2027: 4 working days in 2026, 3 in 2027
    start, end = date(2026, 12, 28), date(2027, 1, 5)
    assert days_in_year(start, end, 2026) == 4
    assert days_in_year(start, end, 2027) == 3
