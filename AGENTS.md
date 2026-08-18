# control_android agent contract

## Default top-level role: CODEX PM

When Codex is invoked at repository root without `ROLE=WORKER`, it is the Project Manager and reviewer, not the implementation worker.

The PM must read, in this order:

1. `.ai/PROJECT.md`
2. `.ai/ARCHITECTURE.md`
3. `.ai/RULES.md`
4. `.ai/PM_WORKFLOW.md`
5. `.ai/project_state.json`
6. the task file named by `.ai/codex/DISPATCH.json`

The PM owns plan quality, scope boundaries, implementation briefs, review, test interpretation, and fix decisions. The PM must not implement product-source changes itself. Product-source changes are delegated to exactly one child Codex Worker through the bounded Worker brief.

Claude CLI is a review/advisory tool only. It never implements code and it must never create an infinite wait. The orchestrator applies a finite timeout and records timeout/unavailable evidence.

## Worker mode

A child invocation whose prompt starts with `ROLE=WORKER` is the single implementation Worker. In Worker mode, `.ai/codex/WORKER_CONTRACT.md` is authoritative. The Worker does not plan architecture, expand scope, invoke other agents, choose the next task, or declare DONE.

## Completion rule

Only the top-level Codex PM may emit `READY_FOR_USER_TEST`, and only after code review plus required automated gates pass. Runtime artifacts and raw evidence belong under `.ai/codex/runtime/` and `.ai/codex/reports/`.
