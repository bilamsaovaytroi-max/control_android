# ITEM-INFORMATION-01 — Item Information workflow

## Goal

Add a separate `Item Information` workflow button that operates from an eBay item detail page.

Flow:

1. detect item page;
2. find product image/gallery from any scroll position;
3. open gallery;
4. verify gallery;
5. scroll gallery down;
6. close gallery through `X`/Close;
7. verify original item detail page/link is restored;
8. save evidence.

## Current implementation

This branch contains a first scaffold implementation:

- `src/control_android/item_information.py`
  - workflow contract;
  - bounded step definition;
  - close-gallery requirement;
  - safe gallery tap helper avoiding heart/favorite overlay;
  - evidence-capturing runner;
  - structured blocker if SmartLocator engine is not attached.
- `src/control_android/desktop.py`
  - adds `Item Information` button;
  - runs workflow in background;
  - shows workflow status/evidence path.
- `tests/test_item_information.py`
  - covers workflow identity;
  - open/scroll/close/restore sequence;
  - bounded scroll-until-found;
  - no primary coordinates;
  - close hints/fallback;
  - heart-overlay avoidance;
  - structured blocker/evidence when no engine exists.

## PM/Worker instruction

Top-level Codex must act as PM.

Before further coding:

1. sync `ai/goal-current`;
2. read `AGENTS.md`;
3. read `.agents/skills/control-android-pm/SKILL.md`;
4. read `.ai/CODEX_PM_CLAUDE_WORKER_WORKFLOW.md`;
5. read this task file;
6. run Claude CLI review on this implementation plan/diff;
7. assign exactly one Worker for implementation/fix if required;
8. run test gates.

## Acceptance criteria

- `Item Information` button exists in desktop UI.
- Button does not block UI indefinitely.
- Workflow captures baseline screenshot/UI XML evidence.
- Workflow definition includes:
  - ensure item page;
  - find gallery with bounded scroll up/down;
  - open gallery;
  - verify gallery;
  - scroll gallery down;
  - close gallery;
  - verify item page restored;
  - final evidence.
- Gallery close uses semantic hints before fallback.
- Safe fallback to Android back is documented and evidence-bound.
- No hard-coded screen coordinate is used as primary selector.
- Existing ADB/device core is reused; no duplicate ADB transport is introduced.
- Tests cover workflow/button contract.

## Required checks

Run:

```bash
python -m compileall src
python -m pytest -q
adb devices
```

If a connected Android device is available, perform the live workflow smoke check from an eBay item page:

1. connect device;
2. open a product detail page;
3. click `Item Information`;
4. verify gallery opens;
5. verify gallery scrolls down;
6. verify close returns to the item page;
7. verify evidence artifacts are saved.

## Known expected blocker

Until M2 SmartLocator/perception engine is fully attached, runtime may return:

`BLOCKED_PERCEPTION_ENGINE_REQUIRED`

This is acceptable only as an intermediate blocker. Codex PM should decide whether to attach the available SmartLocator implementation now or produce a bounded Worker fix task.
