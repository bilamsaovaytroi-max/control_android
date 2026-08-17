from control_android.health import collect_health, main


def test_health_contains_python() -> None:
    items = collect_health()
    python_items = [item for item in items if item.name == "python"]
    assert len(python_items) == 1
    assert python_items[0].status == "PASS"
    assert python_items[0].required is True


def test_health_main_allows_missing_optional_tools() -> None:
    assert main() == 0
