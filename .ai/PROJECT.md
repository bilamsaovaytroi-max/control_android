# Project contract

- Source of truth: `.ai/project_state.json` and test reports.
- Lifecycle: TODO -> IN_PROGRESS -> CODE_COMPLETE -> TESTING -> REVIEW -> DONE.
- Code work may move a task to `CODE_COMPLETE`; only the test gate may move it to `DONE`.
- Device tests are `PENDING` when no Android device is connected.
- Never use hard-coded coordinates as the primary selector.
- Every action follows precondition -> resolve -> act -> wait -> verify.
