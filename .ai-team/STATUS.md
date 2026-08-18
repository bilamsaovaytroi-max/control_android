# CONTROL_ANDROID — Live Status

**Bridge readiness:** RECHECKING  
**Project registration:** PASS  
**Claude CLI:** previously PASS  
**Codex CLI:** previously PASS  
**Tracked project:** `control_android`  
**Execution branch:** `ai/goal-current`  
**Current milestone:** Gate recovery before M2  
**Current gate:** Runtime + workspace revalidation  
**Status:** RECHECK_REQUESTED  
**Last observable progress:** M0/M1 source and device-core evidence exist, but the latest execution report failed because the Bridge executor used Python 3.9.5 and Claude could not verify the executor working directory as a Git repository.  
**Blocker:** Environment gate must be re-run on Python 3.11+ from a valid Git checkout before M2 is activated.  
**Next automatic action:** Bridge/Codex re-runs compileall, pytest, health and source-integrity checks; Claude post-test audit follows. If all pass, PM activates M2 Perception.  
**User action required:** NO during this recheck. If the Bridge still reports Python <3.11 or a non-Git workspace, PM will surface the exact machine fix.

## Gate checklist

- [x] M0/M1 implementation present on `ai/goal-current`
- [x] Unit tests previously passed (`7 passed`)
- [x] ADB/device-core functionality previously produced device evidence
- [ ] Executor runtime reports Python 3.11+
- [ ] Executor workspace verified as Git checkout
- [ ] `python -m compileall src` PASS
- [ ] `pytest -q` PASS
- [ ] `python -m control_android.health` PASS
- [ ] Claude post-test audit PASS
- [ ] PM final gate PASS
- [ ] Activate M2 Perception
