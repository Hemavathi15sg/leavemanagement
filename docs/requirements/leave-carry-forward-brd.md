# BRD: Leave carry-forward

Status: draft for confirmation. Open questions are listed at the end.

## Objective
Employees can keep up to 5 unused leave days from one year into the next. Today unused days are not carried forward. The code has an open TODO in `src/leave/rules.py` for this.

## Scope

**In scope**
- Calculate unused days at year end and carry up to 5 into the new year.
- Include carried days in the employee's available balance.
- Show carried days to the employee and the approver.

**Out of scope**
- Changing the accrual rate or the 24-day annual cap.
- Public holiday exclusion, half days, and authentication or manager roles.
- Paying out unused days.
- Expiry of carried days (see open question 3).

## Business rules

**Existing (from code)**
- BR1. Leave accrues at 2.0 days per full month worked, capped at 24. The README says 1.5 and needs confirming.
- BR2. Available days = opening balance + accrued days − approved days.
- BR3. Days requested are counted Monday to Friday.
- BR4. Only approved leave reduces the balance. Approval re-checks the balance.

**New (proposed)**
- BR5. Unused days at year end = available balance on 31 December.
- BR6. The carried amount is the lesser of unused days and 5. The excess is lost.
- BR7. Carried days are added to the next year's opening balance.
- BR8. Carry-forward runs once per employee per year.

## Assumptions
- A1. The year is the calendar year.
- A2. Carried days are stored in `opening_balance`, so no schema change is needed.
- A3. The 24-day cap applies to earned days only, as it does today. Carried days can take the total above 24.
- A4. `months_worked` is reset for the new year. Without that, earned days stay at the cap.
- A5. Pending requests at year end are not counted as used.

## Open questions
1. Is accrual 2.0 (code) or 1.5 (README)?
2. Is the cap meant per calendar year, or on total months of service?
3. Do carried days expire, for example on 31 March? Are they used before newly earned days?
4. Does the 5-day limit apply to the whole unused balance, including opening balance carried from earlier years?
5. What triggers carry-forward: a scheduled job or a manual run? Nothing runs on a schedule today.
6. What happens to pending requests at year end, and to requests that span 31 December?
7. How are fractional unused days handled?
