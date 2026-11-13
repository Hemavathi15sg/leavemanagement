# Draft for confirmation. See leave-carry-forward-brd.md for open questions.

Feature: Leave carry-forward
  Unused leave days carry into the next year, up to 5 days.

  # Story 1: Carry forward unused days
  # As an employee, I want my unused days carried into next year, up to 5, so I don't lose all my leave.

  Scenario Outline: Carry forward is capped at 5 days
    Given an employee has <unused> unused days on 31 December
    When year-end carry-forward runs
    Then <carried> days are added to their opening balance for the new year

    Examples:
      | unused | carried |
      | 0      | 0       |
      | 3      | 3       |
      | 5      | 5       |
      | 8      | 5       |

  # Story 2: Carried days count in the balance
  # As an employee, I want carried days included in my available leave, so I can book them.

  Scenario: Carried days increase the new year balance
    Given an employee had 5 days carried forward
    And they have worked 2 months in the new year
    When they view their available balance
    Then it shows 9 days

  Scenario: Carried days can be requested
    Given an employee has 0 earned days and 5 carried days
    When they submit a 4 working day request
    Then the request is accepted as pending

  # Story 3: Carry-forward runs once
  # As an administrator, I want the run to be safe to repeat, so balances are never double-counted.

  Scenario: Running carry-forward twice has no extra effect
    Given carry-forward has already run for an employee this year
    When it runs again
    Then their opening balance does not change

  Scenario: Pending requests do not reduce the carry amount
    Given an employee has 6 unused days and a pending 2 day request on 31 December
    When year-end carry-forward runs
    Then 5 days are carried forward

  # Story 4: Visibility
  # As an approver, I want to see carried days separately, so I understand an employee's balance.
  # Needs a decision first: the API returns only available_days today (see BRD assumption A2 and open question 4).

  Scenario: Carried days are shown separately
    Given an employee has 5 carried days and 4 earned days
    When an approver views their balance
    Then the balance shows 5 carried days, 4 earned days and 9 available days
