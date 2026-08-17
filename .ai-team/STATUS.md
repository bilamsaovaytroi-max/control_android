# CONTROL_ANDROID — Live Status

**Bridge readiness:** PASS  
**Project registration:** PASS  
**Claude CLI:** PASS  
**Codex CLI:** PASS  
**Tracked project:** `control_android`  
**Execution branch:** `ai/goal-current`  
**Active request:** Build ADB Device Discovery tool; stop after real Android device detection succeeds.  
**Current gate:** G00 foundation pre-plan review  
**Status:** IN_PROGRESS  
**Latest trigger:** `bb1c93621b3c4f5f5d01719bd97cac335a9a7827` (`ai-review-request: G00 gate before G01 device discovery`)  
**G00 worker draft:** `ai/g00-worker` — foundation code exists, not promoted yet.  
**G01 task:** `.ai/tasks/G01_ADB_DEVICE_DISCOVERY.md` — defined and blocked on G00 PASS.  
**G01 functional boundary:** resolve ADB, run `adb devices -l`, parse `serial/state/product/model/device/transport_id`, distinguish `device/offline/unauthorized/no-device`, expose human-readable and JSON scan output.  
**Out of scope until device detection passes:** screenshot, UIAutomator/XML, tap/swipe/input, WebView, OCR, Vision, workflow automation.  
**Next automatic action:** Claude pre-plan PASS → promote/test G00 → Claude audit/PM review → activate G01 pre-plan → one coding worker → Codex live ADB scan against attached device.  
**User action required:** NO. Keep Android device connected with USB debugging enabled when G01 reaches live-device test.

## Gate checklist

- [x] Bridge health PASS
- [x] User request captured
- [x] G01 ADB Device Discovery task defined
- [x] G00 dependency review re-triggered on healthy bridge
- [ ] G00 Claude pre-plan PASS
- [ ] G00 source promoted
- [ ] G00 Codex tests PASS
- [ ] G00 Claude audit + PM review PASS
- [ ] G01 Claude pre-plan PASS
- [ ] G01 code produced
- [ ] G01 unit tests PASS
- [ ] Real device detected through ADB
- [ ] READY_FOR_USER_TEST
