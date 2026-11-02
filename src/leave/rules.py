"""Leave rules. Accrual, balance and working days are calculated here."""
from datetime import date, timedelta

ACCRUAL_PER_MONTH = 2.0  # days earned per full month worked
ANNUAL_CAP = 24.0        # accrued days cannot exceed this in one calendar year


def accrued_days(months_worked: int) -> float:
    """Days accrued this year, capped at ANNUAL_CAP."""
    return min(months_worked * ACCRUAL_PER_MONTH, ANNUAL_CAP)


# TODO: carry unused days into the next year (not built yet).
def balance(opening: float, months_worked: int, approved_days: float) -> float:
    """Days available now: opening balance plus accrual, minus approved leave."""
    return opening + accrued_days(months_worked) - approved_days


# TODO: exclude public holidays once a holiday calendar exists.
def working_days(start: date, end: date) -> int:
    """Count Monday to Friday days from start to end, inclusive."""
    days = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            days += 1
        current += timedelta(days=1)
    return days
