"""Leave rules. Accrual is calculated here."""

ACCRUAL_PER_MONTH = 1.5  # days earned per full month worked


def accrued_days(months_worked: int) -> float:
    return months_worked * ACCRUAL_PER_MONTH
