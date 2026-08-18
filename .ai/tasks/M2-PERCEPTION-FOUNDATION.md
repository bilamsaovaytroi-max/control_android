# M2-PERCEPTION-FOUNDATION — Smart Locator base

## Goal

Build the first reusable perception layer for `control_android` by selectively adapting useful ideas from the pinned reference checkout `vendor/android-adb-automation-kit`, while preserving the existing project architecture and ADB/device core.

This task is a foundation task only. It must make later browser/app workflows resilient to UI layout changes without using hard-coded coordinates as the primary selector.

## Existing project assets that MUST be reused

- `src/control_android/adb.py` — existing `AdbTransport`; do not replace it with another subprocess wrapper.
- `src/control_android/device.py` — existing per-device `DeviceManager`, locks, screenshot, and UI XML transport; do not replace it with upstream device/tap controllers.
- `.ai/ARCHITECTURE.md` — authoritative perception order and evidence rules.
- `.ai/PROJECT.md` and `.ai/RULES.md` — authoritative lifecycle and engineering rules.

## Upstream reference

Read-only reference:

- repository: `Rtiming/android-adb-automation-kit`
- pinned commit: `7ed0059e6433269da4f031c25d9bb7a2c7c42289`
- local checkout: `vendor/android-adb-automation-kit`

Useful upstream concepts to inspect:

- `vision_controller.py`: `MatchResult`, OpenCV template matching, OCR bounding boxes, scroll/wait concepts.
- `ime_controller.py`: strategy separation only; DO NOT implement IME in this task.
- `tap_controller.py`: primitive semantics only; DO NOT port coordinate-first control into the primary locator design.

Do not copy upstream modules wholesale. Adapt only the minimum logic needed into the existing package structure.

## Required architecture

The resolver chain must preserve this order:

1. UI hierarchy / UIAutomator data: resource-id, accessibility/content-desc, exact text, then contains-text.
2. WebView provider slot: protocol/interface only in this task; no Selenium/DevTools implementation yet.
3. OpenCV template matching in an optional bounded ROI.
4. OCR text matching in an optional bounded ROI.
5. Safe unresolved result with evidence; no blind coordinate fallback.

All resolver results must use a common candidate model with at least:

- method/source;
- bounds;
- confidence;
- label/value;
- evidence metadata.

## Scope

### 1. Common perception models

Create a small perception package/module containing immutable/testable data models such as:

- `Bounds(left, top, right, bottom)` with validated dimensions and center calculation;
- `LocatorQuery` supporting optional `resource_id`, `content_desc`, `text`, `contains_text`, `template_path`, and ROI;
- `Candidate` carrying method, bounds, confidence, label/value, and evidence;
- `Resolution` or equivalent result object that can represent resolved and unresolved outcomes without silently swallowing errors.

Names may vary if Codex PM finds a clearer fit with the existing package, but behavior and separation must remain equivalent.

### 2. UI XML resolver

Implement a pure/testable resolver that accepts UI XML text already obtained from `DeviceManager.ui_xml` / `AdbTransport.dump_ui_xml`.

Requirements:

- parse Android bounds such as `[10,20][110,70]` safely;
- match in deterministic priority: resource-id -> content-desc/accessibility -> exact text -> contains-text;
- return candidates with bounds and evidence;
- malformed nodes are skipped with explicit/debuggable evidence where appropriate, not broad silent exception swallowing;
- no device subprocess calls inside the XML resolver;
- no hard-coded screen coordinates.

### 3. WebView provider boundary

Define a minimal protocol/interface for an optional WebView resolver so the Smart Locator can preserve architecture order without implementing Selenium/CDP in this task.

The default/no-provider behavior should simply produce no WebView candidates and continue to the next strategy.

### 4. Vision template adapter

Selectively adapt the template-matching concept from upstream `vision_controller.py`.

Requirements:

- use optional/lazy OpenCV import so the base package can still import when vision extras are not installed;
- accept a screenshot/image supplied by the caller rather than creating a second ADB/subprocess transport;
- support a configurable threshold;
- support an optional bounded ROI and translate matched ROI coordinates back to absolute screen bounds;
- return common `Candidate` objects;
- do not tap/click from the vision resolver;
- do not use global screen dimensions/config copied from upstream.

### 5. OCR adapter

Selectively adapt the OCR bounding-box concept from upstream.

Requirements:

- optional/lazy OCR dependencies;
- OCR only on the supplied screenshot and optional ROI;
- deterministic text matching and confidence filtering;
- return common `Candidate` objects with absolute bounds;
- no Google Cloud OCR in this task;
- no network calls;
- no tap/click side effects.

### 6. Smart Locator orchestration

Implement a `SmartLocator` (or equivalent) that composes providers in the authoritative order.

Requirements:

- UI resolver first;
- optional WebView provider second;
- template provider third when a template is supplied;
- OCR provider fourth when text fallback is applicable;
- stop/choose deterministically according to explicit confidence/priority rules;
- unresolved result must describe attempted methods/evidence;
- locator itself does not perform the final tap/action;
- no coordinate fallback as success.

## Allowed files

Codex PM may narrow this list further. Worker may edit only these areas unless PM explicitly adds a strictly necessary adjacent file:

- `src/control_android/perception/**` (preferred new package), OR an equivalently small set of new modules under `src/control_android/` if PM justifies it;
- `tests/test_perception*.py` and perception-specific test fixtures;
- `pyproject.toml` only if optional dependency metadata must be adjusted;
- `src/control_android/__init__.py` only if a minimal public export is required.

Do NOT edit in this task:

- `src/control_android/adb.py` unless PM proves a tiny compatibility change is unavoidable;
- `src/control_android/device.py` unless PM proves a tiny compatibility change is unavoidable;
- `src/control_android/desktop.py`;
- `START_CONTROL_ANDROID.bat`;
- existing desktop/UI behavior;
- GitHub workflow/orchestration files.

## Out of scope

- end-user workflow YAML/JSON engine;
- action/tap engine;
- IME/text input;
- keyboard automation;
- scroll state machine;
- browser-specific profiles;
- Selenium/CDP/WebView implementation;
- Google Cloud Vision OCR;
- AI/VLM recovery;
- Maestro;
- mirroring/scrcpy;
- desktop UI changes;
- rewriting ADB/device management;
- copying the upstream repository into application source.

## Required tests

Worker must add deterministic unit tests that do not require an Android device for the perception logic.

At minimum test:

1. Android bounds parsing and center calculation.
2. UI XML resource-id wins over lower-priority text/OCR strategies.
3. content-desc/accessibility resolution.
4. exact text before contains-text.
5. malformed/unresolved XML behavior is explicit and safe.
6. Smart Locator strategy order using fake providers.
7. WebView provider slot is called in the correct position when supplied.
8. ROI coordinate translation for template/OCR adapters without requiring real ADB.
9. optional vision dependency missing produces an explicit unavailable/error result rather than breaking package import.
10. existing tests remain passing.

Hard gate after implementation:

- `python -m compileall src`
- `pytest -q`
- `adb devices`

## Acceptance criteria

PASS only when all are true:

- existing ADB/device core is reused, not duplicated;
- common Candidate/Bounds/evidence model exists;
- UI XML resolver is deterministic and tested;
- WebView boundary exists without implementing WebView automation;
- OpenCV template and OCR adapters are pure perception components using supplied screenshots;
- Smart Locator preserves UI -> WebView -> template -> OCR order;
- no hard-coded coordinate is used as a primary locator;
- no resolver performs click/tap side effects;
- optional dependencies do not break base import;
- new and existing unit tests pass;
- Codex PM review returns PASS;
- hard gate passes.

## User-test boundary

This foundation task does not require the user to exercise a full browser workflow. `READY_FOR_USER_TEST` means the perception foundation passed automated gates and is ready for the next device-level integration task. Do not claim a production workflow is complete.
