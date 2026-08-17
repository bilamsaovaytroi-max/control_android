# control_android

Android automation platform foundation for Windows + Android devices.

## Goal 0 — Project Foundation

This branch currently contains only the project foundation. Android device automation is intentionally deferred to later goals.

### Requirements

- Python 3.11+
- `pip install -e .[dev]`

### Validate

```bat
python -m compileall src
pytest -q
python -m control_android.health
```

`control_android.health` treats Python 3.11+ as required. Android-side tools such as ADB, scrcpy and Tesseract are reported as optional warnings during Goal 0 because their runtime integrations are implemented in later goals.

### Configuration

Copy or reference `config/appsettings.example.yaml`. Sample configuration must not contain secrets.

### Project governance

- `.ai/project_state.json` tracks development state.
- `.ai-team/` is owned by the AI Team Bridge V6.1 execution loop.
- Coding workers do not mark a goal DONE without executor tests and review evidence.
