from src.leave.rules import accrued_days


def test_accrual_is_two_days_per_month():
    assert accrued_days(3) == 6.0


def test_accrual_is_capped_at_24_days():
    assert accrued_days(20) == 24.0
