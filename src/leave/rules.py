"""Leave rules. Accrual, balance and working days are calculated here."""
from datetime import date, timedelta

ACCRUAL_PER_MONTH = 1.5  # days earned per full month worked


def accrued_days(months_worked: int) -> float:
    return months_worked * ACCRUAL_PER_MONTH



def working_days(start: date, end: date) -> int:
    """Count Monday to Friday days from start to end, inclusive."""
    days = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            days += 1
        current += timedelta(days=1)
    return days
