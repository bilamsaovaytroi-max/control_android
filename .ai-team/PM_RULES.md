# PM Execution Rules — Codex PM direct loop

`.ai/PM_WORKFLOW.md` is authoritative. The old ChatGPT-PM / Bridge reviewer flow is deprecated for this branch.

## Role boundary

- Top-level Codex invocation is PM/reviewer/test owner.
- Exactly one child Codex invocation is the implementation Worker.
- Worker receives `ROLE=WORKER` and `.ai/codex/WORKER_CONTRACT.md`.
- Claude CLI is review-only and may not edit source.
- No additional coding workers, audit workers, agent frameworks, watchers, or redesign agents.

## Pre-plan gate

Before Worker implementation, Codex PM must produce a non-empty plan and bounded Worker brief containing:

1. goal;
2. concrete steps;
3. scope and out-of-scope;
4. allowed files/modules;
5. acceptance criteria;
6. required tests.

The plan and brief are reviewed by local Claude CLI before Worker execution. Codex PM decides which Claude findings are valid.

## Claude liveness

Claude review is invoked directly in non-interactive mode with a finite timeout. Default timeout: 120 seconds.

If Claude returns TIMEOUT, UNAVAILABLE, or CLI ERROR:

1. record exact evidence;
2. do not wait again indefinitely;
3. Codex PM continues with its own review;
4. never claim Claude PASS if Claude did not return one.

## Worker liveness

Worker must return code changes, command evidence, or an exact `WORKER_BLOCKED` reason. It may not spawn another Worker or reviewer. A stalled/failed Worker is returned to the Codex PM; PM writes a fix-only brief and reuses the same single-Worker mechanism.

## Test/fix loop

After each Worker pass:

1. Codex PM reviews the exact diff against the brief.
2. Required task-specific checks run.
3. Hard gate runs `compileall`, `pytest`, and `adb devices` at minimum.
4. On failure, capture a failure packet and send it to Claude CLI for read-only failure analysis.
5. Codex PM writes the smallest bounded fix brief.
6. Worker applies only the fix brief.
7. Repeat until PASS or a real external blocker is proven.

## User handoff

Do not request user testing until the final PM report is `RESULT: READY_FOR_USER_TEST`. Code generation alone is never enough.
