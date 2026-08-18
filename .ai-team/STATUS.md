# CONTROL_ANDROID — Live Status

**Orchestration:** CODEX_PM_DIRECT  
**Project registration:** PASS  
**Codex CLI:** configured for local non-interactive PM/Worker execution  
**Claude CLI:** configured as direct read-only reviewer with finite timeout  
**Tracked project:** `control_android`  
**Execution branch:** `ai/goal-current`  
**Current milestone:** M2  
**Current task:** `M2-PERCEPTION-FOUNDATION`  
**Current gate:** DISPATCHED_TO_SELF_HOSTED_RUNNER  
**Status:** DISPATCHED_RECEIPT_NOT_YET_VERIFIED  
**Last observable progress:** Dispatch sequence 6 was pushed for `.ai/tasks/M2-PERCEPTION-FOUNDATION.md`. The branch contains the Codex PM contract, single Worker contract, Claude review contract, deterministic `tools/pm_loop.py`, and the self-hosted runner workflow. No M2 result/report commit has returned yet, so local clone/execution is not claimed as started until observable evidence appears.  
**Upstream reference:** `Rtiming/android-adb-automation-kit@7ed0059e6433269da4f031c25d9bb7a2c7c42289`; runner will clone it into ignored `vendor/android-adb-automation-kit` and treat it as read-only reference.  
**Blocker:** None proven. Runner receipt/execution state is currently unverified from repository evidence.  
**Next automatic action:** Self-hosted runner syncs `ai/goal-current`, clones/refreshes the pinned upstream checkout, invokes Codex PM preplan, Claude preplan review, exactly one Codex Worker, Codex PM diff review, hard tests, and bounded fix loops if required.  
**User action required:** NO.  

## Workflow contract

- [x] Codex is the top-level PM/reviewer/test owner
- [x] Claude CLI is read-only review/advisory only
- [x] Exactly one Codex Worker performs implementation
- [x] Worker is forbidden from redesign, scope expansion, nested agents, or declaring DONE
- [x] Claude timeout/unavailable cannot freeze the pipeline
- [x] Failed source is not published; only failure evidence is returned
- [x] Upstream repository is pinned and reference-only
- [x] M2 task scope and acceptance criteria are bounded
- [x] Dispatch sequence 6 pushed
- [ ] Runner receipt/execution evidence observed
- [ ] Upstream local clone evidence observed
- [ ] Codex PM preplan PASS
- [ ] Claude preplan result recorded
- [ ] Single Worker implementation complete
- [ ] Codex PM code review PASS
- [ ] `compileall` PASS
- [ ] `pytest` PASS
- [ ] `adb devices` gate PASS
- [ ] `READY_FOR_USER_TEST`
