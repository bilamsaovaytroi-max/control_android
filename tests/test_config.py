from pathlib import Path

import pytest

from control_android.config import AppConfig, load_config


def test_sample_config_loads() -> None:
    cfg = load_config(Path("config/appsettings.example.yaml"))
    assert cfg.adb_timeout == 10
    assert cfg.retry_limit == 3
    assert 0 <= cfg.vision_min_confidence <= 1


def test_invalid_numeric_value_fails() -> None:
    with pytest.raises(ValueError):
        AppConfig.from_mapping({"adb_timeout": 0})


def test_invalid_confidence_fails() -> None:
    with pytest.raises(ValueError):
        AppConfig.from_mapping({"vision_min_confidence": 1.1})
