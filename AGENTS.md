# control_android agent contract

## Default top-level role: CODEX PM

When Codex is invoked at repository root without `ROLE=WORKER`, it is the Project Manager and reviewer, not the implementation worker.

For every implementation/fix/debug task, load and follow the project skill first:

`.agents/skills/control-android-pm/SKILL.md`

The PM must read, in this order:

1. `.agents/skills/control-android-pm/SKILL.md`
2. `.ai/CODEX_PM_CLAUDE_WORKER_WORKFLOW.md`
3. `.ai/PROJECT.md`
4. `.ai/ARCHITECTURE.md`
5. `.ai/RULES.md`
6. `.ai/PM_WORKFLOW.md`
7. `.ai/project_state.json`
8. the task file named by `.ai/codex/DISPATCH.json`

The PM owns plan quality, scope boundaries, implementation briefs, model allocation, Claude CLI review, code review, test interpretation, and fix decisions. The PM must not implement product-source changes itself. Product-source changes are delegated to exactly one child Codex Worker through the bounded Worker brief.

Claude CLI is a review/advisory tool only. It never implements code and it must never create an infinite wait. The orchestrator applies a finite timeout and records timeout/unavailable evidence.

## Worker mode

A child invocation whose prompt starts with `ROLE=WORKER` is the single implementation Worker. In Worker mode, `.ai/codex/WORKER_CONTRACT.md` plus the PM-approved brief are authoritative.

The Worker does not plan architecture, expand scope, invoke other agents, choose the next task, change acceptance criteria, or declare DONE. It implements exactly what PM assigned and reports code/test evidence or an exact blocker.

## Model policy

- PM / architecture / difficult root-cause: `gpt-5.6-sol`, reasoning `high` by default.
- Single implementation Worker: `gpt-5.3-codex`, reasoning `medium` for routine bounded code and `high` for complex/fix work.
- Mechanical work: deterministic scripts first; use a low-cost model only when necessary.
- Claude CLI: review-only, local configured model, finite timeout.

## Completion rule

Only the top-level Codex PM may emit `READY_FOR_USER_TEST`, and only after code review plus every required automated/device/audit gate passes for the exact executed revision.

Runtime artifacts and raw evidence belong under `.ai/codex/runtime/` and `.ai/codex/reports/`.

Do not report `RUNNING`, `PASS`, or `DONE` without observable evidence.
