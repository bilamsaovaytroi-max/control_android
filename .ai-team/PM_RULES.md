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

## Claude reviewer liveness / timeout

Claude pre-plan and Claude audit gates must never remain in WAITING indefinitely.

For a pre-plan request:

1. PM pushes exactly one `ai-review-request:` commit and leaves it as repository HEAD until the reviewer consumes it.
2. The normal Bridge reviewer path gets a maximum observation window of 120 seconds.
3. If `.ai-team/reviews/preplan_latest.md` is not generated within that window, mark the reviewer path `STALLED_REVIEWER` instead of continuing to wait.
4. Retry the Bridge reviewer path at most once after confirming the request schema and current HEAD.
5. If the second attempt still produces no review output, the infrastructure is `BLOCKED_CLAUDE_REVIEW_PATH`; stop re-pushing commits and escalate to PM with exact evidence.
6. The preferred infrastructure repair is a direct non-interactive `claude.cmd` fallback with a finite timeout that writes the same review artifact and result token expected by the Bridge.
7. A Claude CLI health PASS is not equivalent to an end-to-end reviewer-path PASS.

The Bridge health check should eventually verify the real path:

`review request -> Claude invocation -> preplan_latest.md -> ai-claude-review commit`.

Do not bypass a mandatory Claude gate silently. PM may only use an explicit documented temporary fallback that still executes Claude and preserves the review artifact.

## Visible status / heartbeat

ChatGPT PM must maintain `.ai-team/STATUS.md` as the human-readable live project status.

Update `STATUS.md` whenever there is a meaningful transition, including:

- review requested / review PASS / review FAIL;
- worker started / worker stalled / source ready;
- source promoted to `ai/goal-current`;
- Codex execution started / PASS / FAIL;
- Claude audit started / PASS / FAIL;
- PM final review;
- READY_FOR_USER_TEST.

`STATUS.md` must show at minimum:

- current goal;
- current gate;
- current status;
- last observable progress;
- blocker, if any;
- next automatic action;
- whether user action is required.

Do not claim ACTIVE work if there is no current observable activity. Use `WAITING`, `STALLED`, `FAILED`, or `READY_FOR_USER_TEST` accurately.

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
