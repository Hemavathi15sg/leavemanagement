from src.leave.rules import accrued_days


def test_accrual_is_one_and_a_half_days_per_month():
    assert accrued_days(3) == 4.5
