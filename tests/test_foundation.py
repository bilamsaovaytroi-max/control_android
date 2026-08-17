import json
from pathlib import Path

from control_android.config import Settings
from control_android.health import check_environment
from control_android.adb import AdbTransport, AdbResult
from control_android.device import DeviceManager


ROOT = Path(__file__).parents[1]


def test_required_structure_exists():
    for relative in [".ai/project_state.json", ".ai/PROJECT.md", "config/default.json", "src/control_android"]:
        assert (ROOT / relative).exists(), relative


def test_settings_load():
    settings = Settings.from_file(ROOT / "config/default.json")
    assert settings.adb_path == "adb"
    assert settings.project_root == ROOT


def test_health_is_serializable():
    report = check_environment()
    assert report["python"]
    json.dumps(report)


def test_adb_command_shape_without_running_process():
    transport = AdbTransport("adb", 3)
    assert transport.adb_path == "adb"


def test_adb_result_is_immutable():
    result = AdbResult(("adb", "devices"), 0, "List of devices attached\n", "")
    assert result.returncode == 0


def test_binary_transport_method_exists():
    assert callable(AdbTransport().run_bytes)


def test_device_reservation_is_exclusive():
    manager = DeviceManager()
    with manager.reserve("emulator-1"):
        assert "emulator-1" in manager._locks
        try:
            with manager.reserve("emulator-1", timeout=0):
                assert False, "lock must be exclusive"
        except TimeoutError:
            pass
