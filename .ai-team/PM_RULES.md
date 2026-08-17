# PM Execution Rules

## Pre-plan request guard

Before creating any `ai-review-request:` commit, ChatGPT PM must validate `.ai-team/EXECUTION_PLAN.json`.

The plan must not be an empty placeholder and must contain, at minimum:

1. a non-empty `goal`;
2. one or more concrete `steps`;
3. explicit `scope` and `out_of_scope`;
4. `files_allowed` or an equivalent file boundary;
5. measurable `acceptance_criteria`;
6. explicit `required_tests`.

If any required field is missing, PM must update `EXECUTION_PLAN.json` first and must not trigger Claude pre-plan review yet.

Claude pre-plan rejection caused by an empty or incomplete plan is treated as a PM contract failure, not a Worker failure.

## Worker liveness / escalation

The coding worker must always produce observable progress: a source commit, test evidence, or an exact BLOCKED reason.

If the worker produces no new code, no commit, and no evidence while remaining PENDING or IN_PROGRESS beyond the expected task window, treat the worker as STALLED.

STALLED flow:

1. Alert ChatGPT PM.
2. PM inspects the blocker.
3. PM re-pushes the brief or re-assigns exactly one coding worker.
4. Continue the same Goal.

Do not wait forever. Do not fan out multiple coding workers. Only PM decides re-push or re-assignment.

## User test handoff

Do not ask the user to run a manual test immediately after code generation.

Only send READY FOR USER TEST after the final source commit completes all required gates:

1. Codex pull/update succeeds.
2. Automated tests pass.
3. Required live/E2E checks pass when applicable.
4. Claude audit passes.
5. ChatGPT PM final review passes.

If any required gate is PENDING or FAILED, keep the Goal internal and continue the fix loop.

When READY FOR USER TEST is reached, provide only the exact start command/script, the user action to perform, and the expected result.
