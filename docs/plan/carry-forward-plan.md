# Leave carry-forward: WBS and RAID plan

Sources: `docs/requirements/leave-carry-forward-brd.md` (draft), `docs/requirements/leave-carry-forward.feature` (draft), `docs/analysis/carry-forward-impact.md`, and a search of the code for TODO and FIXME notes.

**All story-point (SP) values in this plan are assumptions.** They are relative estimates made without team velocity data, and they assume the default decisions in section 3. Re-estimate after the decisions are made.

## 1. Code notes (TODO and FIXME search)

| Location | Note | Status in plan |
|---|---|---|
| `src/leave/rules.py:13` | TODO: carry unused days into the next year | In scope. API-01, API-02 |
| `src/leave/rules.py:19` | TODO: exclude public holidays | Out of scope (BRD). Not in WBS |
| `app.py:78` | FIXME: pending requests not counted, so two pending requests can overbook | Not in BRD scope. Tracked as R6 |
| `app.py:111` | FIXME: no authentication. Any caller can approve or reject | Linked to carry run access (D8, API-08). Approver auth is out of scope, tracked as R5 and I3 |

Line check: the impact doc places `approved_days()` at `app.py:22`. In the current file it is at `app.py:14`. The `balance()` return is at `rules.py:16`, not line 19 as the impact doc states.

## 2. Scope

- In: carry up to 5 unused days at year end, carried days in the balance and request checks, separate display of carried and earned days, idempotent year-end run, migration of existing `leave.db`.
- Out (BRD): accrual change, 24-day cap change, public holidays, half days, authentication and manager roles, payout, expiry (v1).

## 3. Decisions gate (must close before build)

Each row gives the default this plan assumes. The plan is built on the default until the business confirms otherwise.

| ID | Decision | Default assumed | Source |
|---|---|---|---|
| D1 | Carry storage | Separate ledger table `carry_forward`, not `opening_balance` (replaces BRD A2) | Impact doc; Story 4 |
| D2 | Accrual rate | 2.0 days per month (code and feature). Fix README | BRD Q1 |
| D3 | Cap period | Calendar year | BRD Q2, A1 |
| D4 | Does the 5-day cap include carried-in days? | Yes, applies to total unused | BRD Q4 |
| D5 | Trigger | Manual CLI command, run once per year | BRD Q5 |
| D6 | Pending and 31 Dec-spanning requests | Pending ignored (A5). Days split by calendar year | BRD Q6 |
| D7 | Fractional unused days | Carried as-is, capped at 5 | BRD Q7 |
| D8 | Who can run carry-forward | CLI only, no HTTP route. Access by OS account on the server | FIXME `app.py:111`; BRD out of scope |
| D9 | Expiry and order of use | Out of scope for v1 | BRD Q3 |

## 4. Work breakdown structure

Columns: **SP** = story points (assumed). **Depends on** = task IDs or decision IDs. **Source** = BRD, feature scenario or test case ID (TC-CF = proposed in the impact doc).

### 4.1 Database

| ID | Task | SP (assumed) | Depends on | Source |
|---|---|---|---|---|
| DB-01 | Add `carry_forward` table to the schema in `db.py`: `employee_id`, `year`, `carried_days`, `run_at`. Primary key `(employee_id, year)` | 2 | D1 | BR7, BR8 |
| DB-02 | Add index on `leave_requests (employee_id, status, start_date)` for year-scoped approved sums | 1 | none | DR-01 |
| DB-03 | Migration for an existing `leave.db`: create the new table and keep all data. Run before any carry run | 3 | DB-01 | DR-03, TC-CF-13 |
| DB-04 | Year rollover of `months_worked` (reset to 0 for the new year) as part of the carry transaction | 1 | DB-01, D3 | A4 |
| DB-05 | Update `seed.py`: add prior-year approved leave and a carry row so the demo shows carried days | 2 | DB-01 | Demo data |
| | **Subtotal** | **9** | | |

### 4.2 API

| ID | Task | SP (assumed) | Depends on | Source |
|---|---|---|---|---|
| API-01 | Add pure function `carry_amount(unused) = min(max(unused, 0), 5)` in `rules.py`. Remove TODO at line 13 | 1 | D4, D7 | BR6, TC-CF-01a–d |
| API-02 | Extend `balance()` to take `carried_days`. Remove TODO at line 13 once API-01 is done | 2 | API-01, D1 | BR7, Story 2 |
| API-03 | Make `approved_days()` year-scoped (current year only). Split requests that span 31 Dec by day | 3 | D6, DB-02 | DR-01, TC-CF-10 |
| API-04 | `employee_balance()` returns `earned_days`, `carried_days`, `available_days`. Keep `available_days` so existing UI still works | 2 | API-02, API-03 | Story 4, TC-CF-08 |
| API-05 | `create_request` and `change_status` use the new balance, so carried days can be requested and approval re-checks correctly | 1 | API-04 | Story 2 scenario 2, BR4 |
| API-06 | Carry-forward service: for each employee with no ledger row for the year, compute unused days on 31 Dec (approved only), write ledger row, reset `months_worked`. One transaction per employee | 5 | API-01, API-03, DB-01, DB-04, D5, D6 | BR5, BR6, BR8, A5 |
| API-07 | CLI entry point, for example `python carry_forward.py --year 2027`, calling API-06 | 2 | API-06, D5 | Q5 |
| API-08 | Restrict run access per D8: CLI only, no HTTP route. Document the run's required OS permissions | 3 | D8, API-07 | DR-02, TC-CF-12 |
| API-09 | Run log and non-zero exit code on failure, so a missed or failed run is visible | 2 | API-07 | Impact doc, scheduled jobs |
| | **Subtotal** | **21** | | |

### 4.3 UI

| ID | Task | SP (assumed) | Depends on | Source |
|---|---|---|---|---|
| UI-01 | Approver view (`index.html`): show earned, carried and available columns. Today only available is shown | 3 | API-04 | Story 4, TC-CF-08 |
| UI-02 | Employee request form: show carried days next to available days, if the form already shows a balance. Confirm first | 2 | API-05, confirm form shows balance | Story 2 |
| UI-03 | Regression check of existing screens after the balance response changes | 1 | API-04 | BR2 |
| | **Subtotal** | **6** | | |

### 4.4 QA

| ID | Task | SP (assumed) | Depends on | Source |
|---|---|---|---|---|
| QA-01 | Unit tests for `carry_amount`: 0, 3, 5, 8 unused | 1 | API-01 | TC-CF-01a–d; Story 1 outline |
| QA-02 | Unit tests for `balance()` with carried days: 5 carried, 2 months, expects 9 | 1 | API-02 | TC-CF-04; Story 2 |
| QA-03 | Unit or API tests for year scoping, including a request that spans 31 Dec | 2 | API-03 | TC-CF-10 |
| QA-04 | Carry-run tests: unused calculation, pending ignored, second run has no effect, `months_worked` reset | 3 | API-06, DB-04 | TC-CF-02, 03, 06, 07, 09; Story 3 |
| QA-05 | Flask test-client tests: request with carried days only, balance response fields, approve re-check | 3 | API-04, API-05 | TC-CF-05, TC-CF-08, TC-CF-14 (BR4 gap) |
| QA-06 | Migration test: upgrade a copy of a current `leave.db`, check rows and balances unchanged | 2 | DB-03 | TC-CF-13 |
| QA-07 | Choose a BDD approach (for example `pytest-bdd`) or map each `.feature` scenario to a pytest test by hand. Feature has no step definitions today | 3 | none | Impact doc, tests |
| QA-08 | Correct README accrual from 1.5 to 2.0 and document the carry rule | 1 | D2 | BR1 |
| QA-09 | Business UAT of the default decisions and the examples in the feature file. Block TC-CF-11 until D5 is confirmed and TC-CF-12 until D8 is confirmed | 2 | QA-01–QA-06, UI-01, D1–D9 | All |
| | **Subtotal** | **18** | | |

**Total: 54 SP (assumed).** Breakdown: Database 9, API 21, UI 6, QA 18.

## 5. RAID log

Owners are roles, not named people. Assign names at kick-off. L = likelihood, I = impact (H, M, L).

### 5.1 Risks

| ID | Risk | Owner | L | I | Mitigation | Links |
|---|---|---|---|---|---|---|
| R1 | `approved_days()` is not year-scoped. After rollover, last year's leave is deducted again | Dev lead | H | H | Implement API-03 before any run. Add QA-03 test | API-03, QA-03 |
| R2 | Carry run repeated, or partly run, double-counts days | Dev lead | M | H | Ledger primary key (DB-01). One transaction per employee. QA-04 covers repeat runs | DB-01, API-06, QA-04 |
| R3 | Annual run missed or failed silently. Carried days lost with no alert | Ops / admin | M | H | Run log and exit code (API-09). Named owner for the annual run. Scheduler later if needed | API-09 |
| R4 | Migration corrupts or drops data in an existing `leave.db`. `seed.py` deletes the database | Dev lead | M | H | Migration (DB-03) and test (QA-06). Back up `leave.db` before running. Warn in the README that `seed.py` deletes data | DB-03, QA-06 |
| R5 | No authentication. Any caller can approve or reject, and anyone with access could change balances | Product owner | H | H | Carry run is CLI only (D8). Approver auth is out of scope for this change, so it needs its own item before pilot | D8, API-08, I3 |
| R6 | Pending requests are not counted against the balance, so two pending requests can overbook (FIXME `app.py:78`) | Product owner | M | M | Out of scope for carry-forward per BRD A5. Decide separately whether to fix before pilot | I4 |
| R7 | Feature scenarios are not executed (no step definitions, no runner). Acceptance drift from the code | QA lead | H | M | QA-07 chooses a runner. Map each scenario to a test ID | QA-07 |
| R8 | Carry cap interpreted differently (D4). If the 5-day limit excludes carried days, API-01 and API-02 change | BA | M | M | Confirm D4 before build. Keep `carry_amount` as a single function so the change is small | D4, API-01 |
| R9 | Requests spanning 31 Dec counted in the wrong year | Dev lead | M | M | Split by day (API-03). Confirm rule under D6 | D6, API-03 |
| R10 | Response shape change breaks the UI or any other client | Dev lead | L | M | Keep `available_days` in the response (API-04). UI-03 regression | API-04, UI-03 |
| R11 | Fractional unused days cause rounding errors in the carry amount | Dev lead | M | L | Confirm D7. Test with 4.5 and 5.5 | D7, API-01 |
| R12 | README says 1.5 days per month, code says 2.0. Demo users misled | BA | H | L | QA-08 | QA-08, D2 |

### 5.2 Assumptions

| ID | Assumption | Owner | Validate by |
|---|---|---|---|
| A-SP | All story-point values are relative estimates made without team velocity data | Delivery lead | First sprint review |
| A-D1 | Ledger table is used instead of `opening_balance` | BA | Decision gate (D1) |
| A-D3 | Calendar year is the cap period | BA | D3 |
| A-D5 | Carry runs as a manual CLI command once a year | Product owner | D5 |
| A-D8 | No HTTP carry route. Authentication for approvers stays out of scope | Product owner | D8 |
| A-D9 | Expiry and order of use are out of scope for v1 | Product owner | D9 |
| A-SQ | SQLite is the only database and runs on one machine. No concurrent carry runs | Dev lead | Deployment review |
| A-AC | Accrual stays at 2.0 days per month and the 24-day cap stays for earned days | Product owner | D2 |

### 5.3 Issues (open now)

| ID | Issue | Owner | Impact | Action |
|---|---|---|---|---|
| I1 | BRD is a draft. Open questions Q1–Q7 are unanswered | BA | Blocks API-01, API-03, API-06, UI-02 | Close decisions gate (section 3) |
| I2 | Feature file is a draft and has no step definitions | QA lead | Blocks QA-07 | Decide runner (QA-07) |
| I3 | FIXME `app.py:111` (no authentication) conflicts with DR-02 in the impact doc. The BRD puts authentication out of scope | Product owner | Blocks TC-CF-12 | Decide D8. Record approver auth as separate work |
| I4 | FIXME `app.py:78` (overbooking) is not covered by the BRD | Product owner | Possible balance drift before pilot | Decide whether to add it to scope |

### 5.4 Dependencies (outside the code)

| ID | Dependency | Owner | Needed by |
|---|---|---|---|
| X1 | Business sign-off on D1–D9 | Product owner | Start of build |
| X2 | Agreed owner and time for the annual CLI run | Ops / admin | Before first year-end (API-07 go-live) |
| X3 | Backup process for `leave.db` before migration | Ops / admin | DB-03 go-live |
| X4 | Confirmation of whether the request form shows a balance | Frontend owner | UI-02 |
