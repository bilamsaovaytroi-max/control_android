# CONTROL_ANDROID PM Workflow

This file is the authoritative orchestration rule for this project.

## Roles

- User: briefs the job and only needs to test when PM declares READY_FOR_USER_TEST.
- ChatGPT PM: owns scope, architecture, task breakdown, review, fix decisions, and final gate.
- Claude CLI: mandatory pre-code review and post-test audit; also reviews failure/fix plans before new code is produced.
- Exactly one ChatGPT Worker: produces code only from the PM-approved brief. It must not redesign, expand scope, spawn other workers, or choose the next task.
- Codex Desktop/local: executor only. It pulls the PM/Worker-approved code from GitHub, applies/updates the local project, runs commands/tests/device checks, and reports raw evidence/errors. Codex does not own architecture or scope.
- GitHub: handoff/bridge between PM+Worker and the local Codex executor, and the return channel for execution/audit reports.

## Mandatory flow

1. User briefs PM.
2. PM writes a bounded task/spec.
3. Claude CLI PRE-REVIEW reviews plan/scope before code generation.
   - Required gate: `PREPLAN_RESULT: PASS`.
   - On FAIL: no code is produced; PM revises the brief/fix plan and sends it back for Claude review.
4. Exactly one ChatGPT Worker produces the code according to the approved brief.
5. PM reviews Worker output before publishing it to GitHub.
6. PM pushes the approved code/task revision to GitHub.
7. Codex Desktop/local pulls the approved GitHub revision and only executes it:
   - update/apply local files,
   - compile/run,
   - automated tests,
   - ADB/device smoke when required,
   - capture exact stdout/stderr and changed revision.
8. Claude CLI POST-REVIEW audits the executed code and test evidence.
   - Required gate: `AUDIT_RESULT: PASS`.
9. If Codex or Claude reports FAIL:
   - raw failure evidence returns to PM,
   - PM briefs Claude on the failure and proposed fix,
   - Claude reviews the fix plan,
   - same single Worker generates the fix,
   - PM reviews/pushes,
   - Codex pulls/reruns,
   - Claude audits again.
10. Repeat until every required gate is PASS.
11. Only ChatGPT PM may declare `READY_FOR_USER_TEST` or `DONE`.

## Hard rules

- Claude review is mandatory BEFORE every new code/fix generation.
- Use exactly one ChatGPT Worker for implementation.
- Codex is executor/tester, not the architecture owner and not an autonomous redesign agent.
- No scope expansion without PM approval.
- No fake PASS/DONE. Evidence must come from the actual local execution cycle.
- Do not ask the user to copy/paste tasks, code, or errors between agents when GitHub/local reporting can carry them.
- PM must keep iterating internally until the build/test/audit gates pass; only then notify the user to perform real-world testing.
- Do not introduce additional bridges, watchers, daemons, multi-agent frameworks, or orchestration layers unless the user explicitly asks for them.

## Current job

`UI-MVP-01`: build a Windows desktop UI with ADB device discovery and a Connect Device button. Reuse the existing ADB transport. Out of scope for this job: screen control, tap/swipe, OCR, OpenCV, WebView, perception, workflows, and mirroring.
