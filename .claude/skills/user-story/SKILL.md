---
name: user-story
description: Write a user story with Gherkin acceptance criteria for the Leave Management app. Use this whenever the user asks for user stories, requirements, acceptance criteria, Given/When/Then scenarios, a .feature file, or wants a request from a stakeholder turned into testable stories, even if they don't say "user story".
---

# User story and Gherkin acceptance criteria

Turn a business request into one or more user stories, each with Gherkin acceptance criteria that QA and test tools can run.

## Before writing

1. Read the code that the request touches (for example `src/leave/rules.py`, `app.py`, `index.html`). Business rules must come from the code, the BRD, or the user's message. Do not invent rules.
2. If a rule the request depends on is not in the code, list it under open questions instead of guessing.

## Output format

The output is a valid `.feature` file, in the same layout as `docs/requirements/leave-carry-forward.feature`:

```gherkin
# Draft for confirmation. See <brd-file> for open questions.

Feature: <feature name>
  <one-line summary of the feature>

  # Story 1: <short title>
  # As a <role>, I want <capability>, so that <benefit>.

  Scenario Outline: <scenario name>
    Given <precondition with <placeholder>>
    When <one action>
    Then <observable result with <placeholder>>

    Examples:
      | placeholder | result |
      | value       | value  |

  Scenario: <scenario name without a table>
    Given <precondition>
    And <extra precondition>
    When <one action>
    Then <observable result>
```

- Start the file with a one-line draft note that points to the BRD. Put one `# Story N:` header and one `# As a ..., I want ..., so that ...` line above each group of scenarios.
- Use `Scenario Outline` with an `Examples` table when several values test the same rule. Use plain `Scenario` otherwise.
- Use `Given` for setup, `When` for one action, `Then` for an outcome that can be checked. Use `And` to extend a step.
- Use concrete values (for example "5 days", "2025-12-31") instead of vague words like "some" or "enough".
- Cover the normal path and at least one boundary value (for example exactly at a limit). Add a rejection or error scenario when the request involves a check.
- Cite the BRD business rule IDs (BR1, BR6, and so on) in the draft note or the story header when a scenario relies on a rule from the BRD. Do not add rules that are not in the code or the BRD.

## Open questions

Do not put open questions inside the `.feature` file. Report them in the chat as a separate list, with what is unknown and who could answer it. In the demo files, the open questions live in the BRD.

## Saving

If the user asks to save, write the stories as a `.feature` file to the path they give, or to `docs/requirements/<short-slug>.feature` by default. Keep the Gherkin in the file and the prose story in a separate Markdown file only if the user asks for one.
