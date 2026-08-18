# CONTROL_ANDROID PM Workflow

This file is the authoritative orchestration rule for this project.

## Roles

- User: briefs the job and only needs to test when PM declares READY_FOR_USER_TEST.
- ChatGPT PM: owns scope, architecture, task breakdown, pre-code review, Worker assignment, code review, fix decisions, and final gate.
- Exactly one ChatGPT Code Worker: produces code only from the PM-approved brief. It must not redesign, expand scope, spawn other implementation workers, or choose the next task.
- Independent ChatGPT Audit Worker: review-only. It receives the exact GitHub revision plus Codex execution/test evidence, may not modify source, and returns AUDIT_RESULT: PASS or FAIL with concrete findings.
- Codex Desktop/local: executor only. It pulls the PM/Worker-approved code from GitHub, applies/updates the local project, runs commands/tests/device checks, and reports raw evidence/errors. Codex does not own architecture or scope and does not redesign.
- GitHub: handoff/bridge between PM+Worker and the local Codex executor, and the return channel for execution/audit reports.
- Claude CLI: optional secondary reviewer only. It is NOT a blocking gate unless a future local execution cycle produces verifiable invocation evidence.

## Mandatory flow

1. User briefs PM.
2. PM performs the pre-code architecture/scope review and writes a bounded implementation brief.
3. Exactly one ChatGPT Code Worker generates code according to the PM-approved brief.
4. PM reviews Worker output before publishing it to GitHub.
5. PM pushes the approved code/task revision to GitHub.
6. Codex Desktop/local pulls the exact approved GitHub revision and only executes it:
   - update/apply local files,
   - compile/run,
   - automated tests,
   - ADB/device smoke when required,
   - capture exact stdout/stderr and executed revision.
7. Independent ChatGPT Audit Worker reviews the exact changed revision plus test/device evidence in a fresh review context.
   - Required gate: `AUDIT_RESULT: PASS`.
8. If Codex or Audit Worker reports FAIL:
   - raw failure evidence returns to PM,
   - PM analyzes the failure and defines the fix,
   - the same single ChatGPT Code Worker generates the bounded fix,
   - PM reviews/pushes,
   - Codex pulls/reruns,
   - Audit Worker reviews again.
9. Repeat until every required execution/test/audit gate is PASS.
10. Only ChatGPT PM may declare `READY_FOR_USER_TEST` or `DONE`.

## Claude optional-evidence rule

Claude CLI may be used as an extra reviewer, but a Claude invocation counts only when the local executor publishes verifiable evidence for the same task/revision, including:
- task id and Git revision,
- invocation timestamp,
- non-interactive Claude command/mode,
- process exit code,
- captured raw output (prefer JSON output mode),
- explicit review result.

If that evidence is absent, PM treats Claude as NOT INVOKED and does not block the workflow on it.

## Hard rules

- PM performs the required pre-code review before every new code/fix generation.
- Use exactly one ChatGPT Code Worker for implementation.
- Audit Worker is separate and review-only; it must not edit source.
- Codex is executor/tester, not the architecture owner and not an autonomous redesign agent.
- No scope expansion without PM approval.
- No fake PASS/DONE. Evidence must come from the actual local execution cycle.
- Do not ask the user to copy/paste tasks, code, or errors between agents when GitHub/local reporting can carry them.
- PM must keep iterating internally until the build/test/audit gates pass; only then notify the user to perform real-world testing.
- Do not introduce additional bridges, watchers, daemons, multi-agent frameworks, or orchestration layers unless the user explicitly asks for them.

## Recommended model allocation

- PM / architecture / failure analysis: GPT-5.6 Sol High.
- Code Worker: GPT-5.6 Terra for bounded routine coding; escalate the same Worker task to GPT-5.6 Sol High for complex implementation or difficult fixes.
- Audit Worker: GPT-5.6 Sol High in a fresh review context, read-only.
- Codex executor: GPT-5.6 Terra is sufficient for pull/apply/run/test/report duties; use Sol only when command interpretation/debug evidence is unusually complex.

## Current job

`UI-MVP-01`: build a Windows desktop UI with ADB device discovery and a Connect Device button. Reuse the existing ADB transport. Out of scope for this job: screen control, tap/swipe, OCR, OpenCV, WebView, perception, workflows, and mirroring.
