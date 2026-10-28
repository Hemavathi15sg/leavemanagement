from datetime import date

from src.leave.rules import accrued_days, working_days


def test_accrual_is_two_days_per_month():
    assert accrued_days(3) == 6.0


def test_accrual_is_capped_at_24_days():
    assert accrued_days(20) == 24.0


def test_working_days_skip_weekend():
    # Mon 9 Nov 2026 to Sun 15 Nov 2026
    assert working_days(date(2026, 11, 9), date(2026, 11, 15)) == 5
