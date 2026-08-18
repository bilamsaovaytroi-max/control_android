# control_android — Codex PM + Claude CLI + Single Worker Workflow

## Purpose

This document is the authoritative execution workflow for `control_android` when Codex is used to plan, implement, test, review, and fix project work.

The goal is a zero-copy/paste loop:

`User brief -> Codex PM -> Claude CLI review -> one bounded Codex Worker -> Codex PM review/test -> PASS or Claude-assisted fix loop -> READY_FOR_USER_TEST`.

The Worker is an implementation executor only. It does not own architecture, scope, acceptance criteria, model allocation, or final status.

---

## 1. Role ownership

### User

The user provides the goal and performs real-world/manual testing only after the PM reports `READY_FOR_USER_TEST`.

The user should not be required to move prompts, code, logs, or error messages between Codex and Claude when the local workflow can do it automatically.

### Codex PM

The top-level Codex invocation is the Project Manager.

PM owns:

- requirement interpretation;
- architecture;
- scope and out-of-scope;
- task decomposition;
- acceptance criteria;
- model allocation;
- Claude CLI review requests;
- Worker implementation brief;
- code/diff review;
- automated test selection;
- test result interpretation;
- root-cause analysis;
- fix brief creation;
- final `PASS`, `FIX`, `READY_FOR_USER_TEST`, or `BLOCKED` decision.

PM must not directly implement product-source code when the task requires the Worker.

### Claude CLI

Claude CLI is a review/advisory component only.

Allowed uses:

- pre-plan review;
- architecture/scope challenge;
- review of a proposed implementation plan;
- post-code audit;
- failure/root-cause review after a failed gate.

Claude CLI must not:

- edit source files;
- implement the task;
- choose a new architecture independently;
- expand scope;
- assign workers;
- declare project completion.

Claude calls must be non-interactive and finite. Default timeout: 120 seconds. A timeout/unavailable Claude path must produce explicit evidence and must never leave the workflow waiting indefinitely.

### Single Codex Worker

Exactly one implementation Worker is allowed per active task.

Worker mode is identified by a prompt beginning with:

`ROLE=WORKER`

The Worker may:

- read the PM-approved brief;
- read only the project files needed for that brief;
- edit files inside the approved boundary;
- add/update tests required by the brief;
- run bounded local checks useful for implementation;
- return changed files, commands run, results, and blockers.

The Worker must not:

- redesign architecture;
- reinterpret the user goal;
- add features not requested;
- expand scope;
- perform speculative refactors;
- create another worker/sub-agent;
- invoke Claude;
- choose the next task;
- change acceptance criteria;
- declare `DONE` or `READY_FOR_USER_TEST`.

If the brief is impossible or internally contradictory, the Worker returns `BLOCKED` with exact evidence to PM instead of inventing an alternative.

---

## 2. Model allocation

Use model capacity intentionally instead of using the strongest model for every step.

### Tier A — PM / architecture / difficult failure analysis

Preferred model: `gpt-5.6-sol`

Reasoning effort: `high` by default; use `xhigh` only for genuinely difficult architecture or root-cause work.

Use for:

- interpreting a new goal;
- architecture decisions;
- scope boundaries;
- acceptance criteria;
- reconciling conflicting review feedback;
- difficult failures that survived one normal fix pass;
- final PM review.

### Tier B — Implementation Worker

Preferred model: `gpt-5.3-codex`

Reasoning effort:

- `medium` for bounded routine implementation;
- `high` for multi-file implementation, concurrency, state machines, device behavior, difficult tests, or a fix after a failed first implementation.

The Worker still follows the PM brief exactly regardless of reasoning level.

### Tier C — Mechanical work

Preferred model: no model when a deterministic script/test can do the work.

If an LLM is genuinely needed for low-risk mechanical processing, use `gpt-5.6-luna` with low/medium reasoning.

Examples:

- summarizing raw test output;
- formatting a deterministic report;
- classifying known gate results.

Do not spend Sol-level reasoning on command execution, file copying, or simple report formatting.

### Claude CLI allocation

Claude CLI uses the locally configured Claude model and is review-only.

Default policy:

- pre-plan: one review call;
- post-code audit: one review call when required by the task;
- failure review: one call only after a real failing execution/test result;
- do not repeatedly call Claude with unchanged evidence.

---

## 3. Mandatory task lifecycle

Every task follows this lifecycle:

`TODO -> PLANNING -> CLAUDE_PREPLAN -> BRIEF_READY -> WORKER_RUNNING -> CODE_COMPLETE -> PM_REVIEW -> TESTING -> AUDIT -> READY_FOR_USER_TEST`

Failure states:

- `FIX_REQUIRED`
- `BLOCKED`
- `CLAUDE_TIMEOUT`
- `WORKER_STALLED`
- `TEST_FAILED`

Only PM may transition a task into `READY_FOR_USER_TEST`.

---

## 4. New-task execution loop

### Step 1 — PM reads project truth

Before planning, PM reads in this order:

1. `AGENTS.md`
2. `.agents/skills/control-android-pm/SKILL.md`
3. `.ai/PROJECT.md`
4. `.ai/ARCHITECTURE.md`
5. `.ai/RULES.md`
6. `.ai/project_state.json`
7. active task file referenced by `.ai/codex/DISPATCH.json`
8. directly relevant source/tests only.

PM must inspect existing implementation before proposing replacements.

### Step 2 — PM writes a bounded plan

Every implementation plan must contain:

- task id;
- goal;
- current-state summary;
- architecture decision;
- explicit scope;
- explicit out-of-scope;
- files allowed to change;
- files forbidden to change if important;
- implementation steps;
- invariants that must remain true;
- acceptance criteria;
- required automated tests;
- required device/live checks;
- rollback/failure evidence requirements.

A plan without these fields is incomplete and must not be sent to the Worker.

### Step 3 — Claude CLI pre-plan review

PM sends the complete plan plus relevant architecture constraints to Claude CLI.

Claude is asked to find:

- architecture conflicts;
- missing edge cases;
- hidden scope expansion;
- unsafe assumptions;
- missing tests;
- unnecessary complexity.

Required Claude output format:

- `REVIEW_RESULT: PASS` or `REVIEW_RESULT: FIX`
- concise findings;
- concrete changes to the plan only.

PM decides whether each recommendation is accepted. Claude does not directly rewrite project architecture.

If Claude times out:

- record `CLAUDE_TIMEOUT`;
- do not wait forever;
- PM may continue only if the task policy marks Claude advisory rather than mandatory;
- if Claude is mandatory for the current gate, report `BLOCKED_CLAUDE_REVIEW` with evidence.

### Step 4 — PM creates Worker brief

The Worker brief is an implementation contract, not an open-ended problem statement.

It must include:

- `ROLE=WORKER`;
- exact task id;
- objective;
- exact files allowed;
- exact behavior to implement;
- interfaces/types to preserve or introduce;
- implementation constraints;
- tests to add/update;
- commands to run;
- forbidden changes;
- acceptance checklist;
- required Worker report format.

The brief should contain enough detail that the Worker does not need to make an architecture decision.

### Step 5 — one Worker implements

PM invokes exactly one Worker using the selected Worker model.

Do not fan out multiple coding Workers.

Worker returns:

- `WORKER_RESULT: CODE_COMPLETE` or `WORKER_RESULT: BLOCKED`;
- files changed;
- concise implementation summary;
- tests/commands run;
- raw failing evidence if blocked;
- no completion declaration.

### Step 6 — PM reviews the diff

Before testing, PM checks:

- diff is within allowed files;
- no scope expansion;
- no architecture drift;
- no duplicate subsystem introduced;
- no hard-coded coordinates as a primary locator;
- error handling is explicit;
- test coverage matches acceptance criteria;
- no hidden dependency or destructive behavior was added.

If diff violates the brief, PM creates a fix-only brief and sends it to the same Worker.

### Step 7 — deterministic test gate

Run deterministic gates before asking any model to reason about success.

Baseline:

```text
python -m compileall src
python -m pytest -q
adb devices
```

Add task-specific tests defined in the task brief.

For device-required tasks, capture at minimum:

- device serial;
- command;
- exit code;
- stdout/stderr;
- relevant screenshot/UI XML/evidence path;
- executed git revision.

A missing device should be reported as `PENDING_DEVICE` or `BLOCKED_DEVICE`, not a fake PASS.

### Step 8 — PASS path

If all required gates pass:

1. optionally run Claude post-code audit if required by task policy;
2. PM reviews the exact changed revision and evidence;
3. update project state;
4. emit `READY_FOR_USER_TEST`.

User handoff contains only:

- exact start command/script;
- exact manual action to perform;
- expected result;
- what evidence to send back if it differs.

### Step 9 — FAIL path

When any real gate fails:

1. preserve raw failure evidence;
2. PM summarizes reproduction and suspected failure surface;
3. send only the real failure evidence + relevant diff/architecture context to Claude CLI for failure review;
4. PM reconciles Claude feedback;
5. PM writes a narrow fix-only Worker brief;
6. same single Worker implements the fix;
7. PM reviews the diff;
8. rerun the failed gate plus regression suite;
9. repeat until PASS or a genuine external blocker is proven.

Do not ask the user to debug intermediate failures that the local automation can continue handling.

---

## 5. `control_android` architecture constraints

These rules remain authoritative for Android automation implementation.

### Perception order

1. UIAutomator resource-id/accessibility/text/hierarchy
2. WebView DOM/role/aria-label/text/bounds with stale-DOM protection
3. OpenCV template matching in a bounded ROI
4. OCR on a cropped ROI
5. safe unresolved result with evidence

Coordinates are never the primary selector.

### Action lifecycle

Every action follows:

`precondition -> resolve -> act -> wait -> verify`

Avoid fixed sleeps when state/change detection can be used.

### Device boundary

ADB remains the transport boundary.

Each serial has isolated device context/locking. Do not create a second independent ADB subsystem when the existing `AdbTransport`/`DeviceManager` can be extended.

### Upstream Android ADB Automation Kit

Reference upstream:

`Rtiming/android-adb-automation-kit`

Pinned reference revision:

`7ed0059e6433269da4f031c25d9bb7a2c7c42289`

Use upstream as read-only reference. Do not blindly copy or execute upstream scripts.

Port only reviewed primitives that fit the existing architecture, especially useful perception concepts from `vision_controller.py` and IME ideas when explicitly in scope.

Do not replace the existing project device/ADB core with upstream `device_controller.py` or `tap_controller.py` unless PM explicitly approves a future architecture change.

---

## 6. M2 Perception Foundation contract

Current customization direction:

- candidate/bounds model;
- UI XML locator;
- optional WebView resolver interface/slot;
- OpenCV template resolver;
- OCR resolver;
- SmartLocator ordered fallback chain;
- confidence + method + bounds + evidence returned for every successful candidate;
- unresolved targets produce evidence instead of blind coordinate clicks.

Expected locator order:

`resource-id -> accessibility/content-desc -> exact text -> contains text -> WebView -> OpenCV -> OCR -> UNRESOLVED`

OpenCV/OCR components perform perception only. They must not independently capture through a second ADB implementation and must not tap the screen themselves.

---

## 7. Liveness rules

### Claude liveness

- finite timeout, default 120 seconds;
- maximum one unchanged retry;
- no infinite `WAITING` state;
- persist exit code/output/timeout evidence.

### Worker liveness

A Worker must produce one of:

- code change;
- test evidence;
- exact `BLOCKED` reason.

No silent/stalled state is accepted.

If Worker stalls, PM terminates that invocation and re-invokes exactly one Worker with the same bounded task/fix brief. Do not create parallel implementation Workers.

### PM liveness

PM continues automatically through review/test/fix loops while the next action is locally resolvable.

PM stops only when:

- `READY_FOR_USER_TEST`, or
- a genuine external blocker requires user action.

---

## 8. Status reporting

Do not report activity without evidence.

Examples:

Bad:

`Codex is coding now.`

Good:

`WORKER_RUNNING — worker process started; PID/command evidence recorded.`

Bad:

`Tests passed.`

Good:

`PYTEST PASS — exit 0, 23 passed, executed revision abc123.`

If dispatch exists but no runner receipt/report exists, status is:

`DISPATCHED_RECEIPT_NOT_VERIFIED`

not `RUNNING`.

---

## 9. Final completion gate

PM may emit `READY_FOR_USER_TEST` only when all task-required items are true:

- implementation matches the approved brief;
- diff review PASS;
- compile/test gates PASS;
- required ADB/device gates PASS or are explicitly not applicable;
- required audit PASS;
- no unresolved blocker;
- evidence references the exact executed revision.

`DONE` should be reserved for completion after the required user/manual acceptance when the task requires it.
