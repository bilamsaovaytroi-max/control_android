# CONTROL_ANDROID — Codex PM / Claude / Single Worker Workflow

This file is the authoritative orchestration rule for `control_android`.

## Roles

- **User**: defines the goal and performs the final real-device acceptance test only after `READY_FOR_USER_TEST`.
- **Codex PM**: owns task analysis, bounded plan, Claude review handoff, Worker brief, code review, automated test gate, failure diagnosis, fix brief, and final readiness decision.
- **Exactly one Codex Worker**: implementation only. It edits code strictly within the PM-approved brief. It does not redesign, expand scope, invoke other agents, choose the next task, or declare DONE.
- **Claude CLI**: read-only second opinion for pre-plan review and failure analysis. Claude never edits source. Claude is invoked directly in non-interactive mode with a finite timeout; a timeout/unavailable result is recorded and must not freeze the pipeline.
- **GitHub self-hosted runner**: transport/execution host. It syncs `ai/goal-current`, clones the pinned upstream reference, invokes the PM loop, records evidence, and pushes the resulting source/report commit.

## Mandatory execution loop

1. Sync `ai/goal-current` into `C:\Users\OS\Desktop\Tools MMO\eBay Tool\control_android`.
2. Clone or refresh `Rtiming/android-adb-automation-kit` into `vendor/android-adb-automation-kit` at the pinned reviewed commit. The vendor checkout is reference-only; never edit or commit it.
3. Codex PM reads project contracts, current dispatch/task, current source, tests, and the upstream reference.
4. Codex PM writes a bounded implementation plan and a first Worker brief. PM does not edit product source.
5. The orchestrator sends the plan + brief to local Claude CLI for **PREPLAN REVIEW**.
6. Codex PM reconciles Claude findings. Claude is advisory; valid findings are incorporated, invalid findings are rejected. Timeout/unavailable evidence is accepted without stalling.
7. Codex PM finalizes the Worker brief with:
   - exact scope and out-of-scope,
   - allowed files/modules,
   - required behavior,
   - acceptance criteria,
   - required tests,
   - explicit no-redesign/no-scope-expansion rule.
8. Exactly one Codex Worker receives `ROLE=WORKER` + the final brief and implements only that brief.
9. Code returns to Codex PM. PM reviews the exact diff against the brief and runs task-specific checks.
10. A hard gate independently runs at minimum:
    - `python -m compileall src`,
    - `pytest -q`,
    - `adb devices`.
11. If PM review and all required gates PASS: write `RESULT: READY_FOR_USER_TEST` and publish source + report.
12. If anything FAILS:
    - capture Worker result, PM review, hard-gate output, and git diff into a failure packet;
    - send the failure packet to Claude CLI for **FAILURE ANALYSIS**;
    - Codex PM decides the root cause and writes a minimal fix-only Worker brief;
    - the same single-Worker mechanism applies the fix;
    - return to step 9.
13. If there is a real external blocker (missing Codex, missing task file, broken repository, etc.), report `BLOCKED` with exact evidence. Never fake PASS.

## PM/Worker separation

Codex PM may edit orchestration artifacts under `.ai/` and may run commands/tests, but it must not author product-source implementation changes. The Worker is the only role allowed to make implementation changes under `src/`, `tests/`, configuration, or other task-scoped product files.

The Worker must be mechanical:

- no brainstorming;
- no alternative architecture;
- no optional refactors;
- no dependency changes unless the brief explicitly allows them;
- no extra features;
- no second Worker;
- no Claude call;
- no self-assigned next task.

## Claude liveness rule

Claude is invoked directly through local `claude`/`claude.cmd` using non-interactive print mode and plan permission mode. The default review timeout is 120 seconds. `TIMEOUT`, `UNAVAILABLE`, or CLI error is written to the review artifact and the Codex PM continues using its own review instead of waiting indefinitely.

## Upstream integration rule

`vendor/android-adb-automation-kit` is a reference checkout, not application code. Codex PM must selectively port/adapt useful primitives into the existing `src/control_android` architecture. Do not replace the project wholesale and do not import hard-coded coordinate-first design as the primary locator strategy.

Current perception order remains:

1. UIAutomator resource-id/accessibility/text/hierarchy
2. WebView DOM/role/aria-label/text/bounds where applicable
3. bounded OpenCV template matching
4. cropped OCR fallback
5. safe failure with screenshot/UI XML/evidence

## User handoff

Do not ask the user to test after code generation alone. Only hand off when the PM report says `READY_FOR_USER_TEST`. The report must include the exact task id, automated gate result, and the final real-device action the user should perform.
