from control_android.adb import AdbError
from control_android.desktop import DeviceConnectionModel


class FakeTransport:
    def __init__(self, devices=None, error=None):
        self._devices = list(devices or [])
        self.error = error

    def devices(self):
        if self.error:
            raise self.error
        return list(self._devices)


def test_refresh_one_device():
    model = DeviceConnectionModel(FakeTransport([("abc", "device")]))
    devices = model.refresh()
    assert [(item.serial, item.state) for item in devices] == [("abc", "device")]
    assert model.adb_ready is True
    assert model.status == "Not connected"


def test_refresh_no_devices():
    model = DeviceConnectionModel(FakeTransport())
    assert model.refresh() == []
    assert model.status == "No Android device detected"


def test_single_usable_device_connects_automatically():
    model = DeviceConnectionModel(FakeTransport([("abc", "device")]))
    model.refresh()
    connected = model.connect()
    assert connected is not None
    assert connected.serial == "abc"
    assert model.status == "Connected"


def test_multiple_devices_require_selection():
    model = DeviceConnectionModel(FakeTransport([("one", "device"), ("two", "device")]))
    model.refresh()
    assert model.connect() is None
    assert model.status == "Select a usable device"
    assert model.connect("two").serial == "two"


def test_offline_device_cannot_connect():
    model = DeviceConnectionModel(FakeTransport([("abc", "offline")]))
    model.refresh()
    assert model.connect("abc") is None
    assert model.status == "Offline"
    assert model.connected is None


def test_unauthorized_device_cannot_connect():
    model = DeviceConnectionModel(FakeTransport([("abc", "unauthorized")]))
    model.refresh()
    assert model.connect("abc") is None
    assert model.status == "Unauthorized"
    assert model.connected is None


def test_adb_error_is_reported_without_crash():
    model = DeviceConnectionModel(FakeTransport(error=AdbError("adb missing")))
    assert model.refresh() == []
    assert model.adb_ready is False
    assert model.status == "ADB error"
    assert model.last_error == "adb missing"


def test_refresh_drops_connection_when_device_goes_offline():
    transport = FakeTransport([("abc", "device")])
    model = DeviceConnectionModel(transport)
    model.refresh()
    model.connect("abc")
    transport._devices = [("abc", "offline")]
    model.refresh()
    assert model.connected is None
    assert model.status == "No usable Android device"


def test_selected_offline_device_is_rejected_with_multiple_devices():
    model = DeviceConnectionModel(
        FakeTransport([("good", "device"), ("other", "device"), ("bad", "offline")])
    )
    model.refresh()
    assert model.connect("bad") is None
    assert model.status == "Offline"
