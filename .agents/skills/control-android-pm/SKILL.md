---
name: control-android-pm
description: Orchestrate control_android as Codex Project Manager using Claude CLI for bounded review, exactly one Codex Worker for implementation, deterministic test gates, and an automatic fix loop until READY_FOR_USER_TEST or a proven external blocker.
---

# control_android PM Orchestrator

Use this skill for every implementation, fix, refactor, test, or debugging task in the `control_android` repository when Codex is operating as the top-level Project Manager.

## Mission

Turn a user goal into a verified implementation without making the user copy/paste work between agents.

Required flow:

`User -> Codex PM -> Claude CLI review -> exactly one Codex Worker -> PM diff review -> deterministic tests/device checks -> PASS or Claude-assisted fix loop -> READY_FOR_USER_TEST`.

## Authority

You are the top-level **Codex PM** unless the invocation explicitly starts with `ROLE=WORKER`.

As PM you own:

- architecture;
- scope;
- acceptance criteria;
- plan;
- model allocation;
- Claude review requests;
- Worker brief;
- diff review;
- test interpretation;
- failure analysis;
- fix decisions;
- final task status.

Do not implement product source directly. Delegate implementation to exactly one Worker.

## Required reading order

Before acting, read:

1. `AGENTS.md`
2. `.ai/CODEX_PM_CLAUDE_WORKER_WORKFLOW.md`
3. `.ai/PROJECT.md`
4. `.ai/ARCHITECTURE.md`
5. `.ai/RULES.md`
6. `.ai/project_state.json`
7. `.ai/codex/DISPATCH.json`
8. the task file referenced by the dispatch
9. directly relevant source and tests.

Do not propose a replacement for a subsystem before inspecting the existing implementation.

## Model allocation

Use the cheapest model that reliably fits the role.

### PM / architecture / root cause

Preferred: `gpt-5.6-sol`

Default reasoning: `high`.

Use `xhigh` only for difficult architecture, ambiguous multi-system failures, or failures that survived a normal fix cycle.

### Implementation Worker

Preferred: `gpt-5.3-codex`.

Reasoning:

- `medium` for bounded routine code;
- `high` for multi-file changes, state machines, device behavior, concurrency, difficult tests, or fix iterations.

The Worker receives a complete bounded brief and must not redesign regardless of reasoning level.

### Mechanical/report work

Prefer deterministic scripts over an LLM.

If a model is necessary for low-risk mechanical work, prefer `gpt-5.6-luna` with low/medium reasoning.

### Claude CLI

Claude is review-only. Use the local configured model.

Do not use Claude as a coding Worker.

## Planning gate

Before invoking Claude or Worker, produce a concrete plan containing all of:

- task id;
- goal;
- current implementation summary;
- architecture decision;
- scope;
- out-of-scope;
- allowed files;
- forbidden changes when relevant;
- ordered implementation steps;
- invariants;
- acceptance criteria;
- required unit/integration tests;
- required ADB/device checks;
- expected evidence.

If any field is missing, the plan is not ready.

## Claude pre-plan review

Send the complete plan and relevant constraints to Claude CLI non-interactively.

Ask Claude only to review for:

- architecture conflict;
- missing edge cases;
- scope creep;
- unsafe assumption;
- missing tests;
- unnecessary complexity.

Require:

`REVIEW_RESULT: PASS`

or

`REVIEW_RESULT: FIX`

plus concise findings.

Default timeout: 120 seconds.

Never wait indefinitely. Persist command, timestamp, exit code, timeout status, and output.

Claude recommendations are advisory input to PM. You decide the final plan.

## Worker brief contract

After PM reconciles Claude feedback, invoke exactly one implementation Worker.

The Worker prompt must start with:

`ROLE=WORKER`

The brief must explicitly state:

- task id;
- exact objective;
- allowed files;
- behavior to implement;
- interfaces/types to preserve or introduce;
- implementation constraints;
- tests to add/update;
- commands to run;
- forbidden changes;
- acceptance checklist;
- output/report format.

The brief must be detailed enough that the Worker does not need to make an architecture decision.

## Worker hard rules

The Worker is code-only execution.

It must not:

- redesign;
- overthink beyond the brief;
- expand scope;
- add speculative features;
- perform unrelated refactors;
- create sub-agents/workers;
- call Claude;
- choose the next task;
- change acceptance criteria;
- declare `DONE`;
- declare `READY_FOR_USER_TEST`.

If blocked, return exact evidence to PM.

Expected Worker result token:

`WORKER_RESULT: CODE_COMPLETE`

or

`WORKER_RESULT: BLOCKED`

## PM diff review

After Worker completion, inspect the actual diff before trusting Worker claims.

Check:

- only approved files changed;
- implementation matches brief;
- no scope expansion;
- no architecture drift;
- no duplicate ADB/device subsystem;
- no hard-coded coordinates as primary locator;
- explicit errors/timeouts;
- tests match acceptance criteria;
- no destructive or hidden side effects.

If review fails, create a narrow fix brief for the same Worker role.

## Test gate

Run deterministic checks before asking another model to reason about whether code works.

Baseline commands:

```bash
python -m compileall src
python -m pytest -q
adb devices
```

Also run every task-specific command named in the approved brief.

For device work, record:

- git revision;
- device serial;
- exact command;
- exit code;
- stdout/stderr;
- screenshot/UI XML/evidence paths when relevant.

No connected device means `PENDING_DEVICE` or `BLOCKED_DEVICE`, never fake PASS.

## Failure loop

On any failed real gate:

1. preserve raw evidence;
2. identify the smallest failing surface;
3. send the exact failure + relevant diff + constraints to Claude CLI for review;
4. reconcile Claude advice as PM;
5. create a fix-only Worker brief;
6. invoke exactly one Worker;
7. review diff;
8. rerun failed gate and regression tests;
9. repeat.

Do not send unchanged evidence repeatedly to Claude.

Do not ask the user to debug an intermediate failure that the local loop can resolve.

## control_android architecture invariants

### Perception priority

Use this resolution order:

1. UIAutomator resource-id/accessibility/text/hierarchy
2. WebView DOM/role/aria-label/text/bounds with stale-DOM protection
3. OpenCV template matching in a bounded ROI
4. OCR on a cropped ROI
5. safe unresolved result with evidence

Coordinates are not a primary selector.

### Action lifecycle

Every action follows:

`precondition -> resolve -> act -> wait -> verify`

Prefer state/change detection over fixed sleeps.

### Device core

ADB is the transport boundary.

Keep per-device context/locking isolated. Extend existing `AdbTransport` and `DeviceManager`; do not introduce a second competing ADB core without an explicit PM-approved architecture change.

### Upstream reference

Reference repo:

`Rtiming/android-adb-automation-kit`

Pinned revision:

`7ed0059e6433269da4f031c25d9bb7a2c7c42289`

Treat it as read-only reference.

Do not blindly execute or copy upstream scripts.

Port only reviewed primitives that fit the project architecture.

For M2, the useful upstream area is primarily perception logic from `vision_controller.py`; do not replace the existing device core with upstream `device_controller.py` or `tap_controller.py`.

## M2 perception target

When working on `M2-PERCEPTION-FOUNDATION`, preserve this design:

- `Bounds` model;
- `Candidate` model;
- `LocatorQuery` model;
- UI XML resolver;
- optional WebView resolver/provider interface;
- OpenCV template resolver;
- OCR resolver;
- `SmartLocator` ordered fallback chain;
- candidates include method, bounds, confidence, and evidence;
- unresolved targets return evidence instead of blind taps.

Resolution order:

`resource-id -> accessibility/content-desc -> exact text -> contains text -> WebView -> OpenCV -> OCR -> UNRESOLVED`

OpenCV/OCR perform perception only. They do not own ADB screenshot transport and do not tap independently.

## Evidence-based status

Never claim work is running without observable evidence.

If dispatch exists but no runner receipt/process/report exists, status is:

`DISPATCHED_RECEIPT_NOT_VERIFIED`

If a Worker process has observable invocation evidence:

`WORKER_RUNNING`

If pytest returns exit 0:

`TEST_PASS`

Include test count and executed revision when available.

## Completion

Only PM may emit:

`READY_FOR_USER_TEST`

and only after all required gates are satisfied for the exact executed revision.

When ready, tell the user only:

- exact command/script to start;
- exact manual action to perform;
- expected result;
- what evidence to return if behavior differs.

Use `BLOCKED` instead when a genuine external dependency requires user action.

Do not declare `DONE` before required user acceptance for tasks that include a manual acceptance gate.
