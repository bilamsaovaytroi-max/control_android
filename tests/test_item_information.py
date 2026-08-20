from pathlib import Path

from control_android.item_information import (
    BLOCKED_PERCEPTION_ENGINE_REQUIRED,
    BUTTON_LABEL,
    Bounds,
    WORKFLOW_ID,
    item_information_workflow_definition,
    run_item_information_workflow,
    safe_gallery_tap_point,
)


class FakeDeviceManager:
    def screenshot(self, serial: str, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"fake-png")
        return destination

    def ui_xml(self, serial: str, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("<hierarchy />", encoding="utf-8")
        return destination


def test_workflow_identity_and_button_label():
    definition = item_information_workflow_definition()
    assert definition["id"] == WORKFLOW_ID
    assert definition["label"] == BUTTON_LABEL
    assert BUTTON_LABEL == "Item Information"


def test_workflow_contains_open_scroll_close_restore_sequence():
    steps = [step["id"] for step in item_information_workflow_definition()["steps"]]
    assert steps.index("find_gallery_area") < steps.index("open_gallery")
    assert steps.index("open_gallery") < steps.index("verify_gallery_open")
    assert steps.index("verify_gallery_open") < steps.index("scroll_gallery_down")
    assert steps.index("scroll_gallery_down") < steps.index("close_gallery")
    assert steps.index("close_gallery") < steps.index("verify_item_page_restored")


def test_workflow_has_bounded_scroll_until_found():
    find_step = next(
        step for step in item_information_workflow_definition()["steps"] if step["id"] == "find_gallery_area"
    )
    assert find_step["action"] == "scroll_until_found"
    assert find_step["direction"] == "up"
    assert find_step["max_scrolls"] == 8
    assert find_step["downward_retry_scrolls"] == 2


def test_workflow_forbids_primary_coordinates():
    definition = item_information_workflow_definition()
    assert definition["primary_coordinates_allowed"] is False
    assert "structured_unresolved" in definition["strategy_order"]


def test_gallery_close_has_accessible_hints_and_safe_fallback():
    close_step = next(
        step for step in item_information_workflow_definition()["steps"] if step["id"] == "close_gallery"
    )
    hints = close_step["target"]["hints"]
    assert close_step["target"]["role"] == "gallery_close"
    assert "Close" in hints["content_desc"]
    assert "Close gallery" in hints["aria_label"]
    assert close_step["safe_fallback"] == "android_back_once_with_evidence"


def test_safe_tap_avoids_favorite_overlay_when_center_overlaps():
    image = Bounds(0, 0, 300, 300)
    overlay = Bounds(120, 120, 80, 80)
    point = safe_gallery_tap_point(image, overlay)
    assert image.contains(point)
    assert not overlay.contains(point)


def test_run_without_engine_returns_structured_blocker(tmp_path):
    result = run_item_information_workflow(
        "serial-1",
        device_manager=FakeDeviceManager(),
        evidence_root=tmp_path,
    )
    assert result.workflow_id == WORKFLOW_ID
    assert result.status == BLOCKED_PERCEPTION_ENGINE_REQUIRED
    evidence_dir = Path(result.evidence_dir)
    assert (evidence_dir / "workflow_definition.json").exists()
    assert (evidence_dir / "workflow_result.json").exists()
    assert (evidence_dir / "item_information_initial.png").exists()
    assert (evidence_dir / "item_information_initial.xml").exists()
