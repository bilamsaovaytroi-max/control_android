from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
import time
from typing import Any, Protocol

from .device import DeviceManager


WORKFLOW_ID = "item_information"
BUTTON_LABEL = "Item Information"

PASS = "PASS"
BLOCKED_NOT_ITEM_PAGE = "BLOCKED_NOT_ITEM_PAGE"
BLOCKED_PERCEPTION_ENGINE_REQUIRED = "BLOCKED_PERCEPTION_ENGINE_REQUIRED"
UNRESOLVED_GALLERY_NOT_FOUND = "UNRESOLVED_GALLERY_NOT_FOUND"
UNRESOLVED_GALLERY_CLOSE_NOT_FOUND = "UNRESOLVED_GALLERY_CLOSE_NOT_FOUND"


@dataclass(frozen=True)
class Bounds:
    """Screen-space rectangle returned by a locator candidate."""

    x: int
    y: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    @property
    def center(self) -> tuple[int, int]:
        return self.x + self.width // 2, self.y + self.height // 2

    def contains(self, point: tuple[int, int]) -> bool:
        px, py = point
        return self.x <= px <= self.right and self.y <= py <= self.bottom


@dataclass(frozen=True)
class Candidate:
    """Resolved UI target with evidence from SmartLocator/perception."""

    role: str
    method: str
    bounds: Bounds
    confidence: float
    label: str = ""
    evidence: dict[str, Any] | None = None


@dataclass(frozen=True)
class WorkflowRunResult:
    workflow_id: str
    status: str
    message: str
    evidence_dir: str
    evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class WorkflowEngine(Protocol):
    """Future SmartLocator workflow engine contract.

    The engine owns perception/action execution. This module owns the bounded
    workflow contract, evidence wrapper, and desktop button dispatch.
    """

    def execute_workflow(self, definition: dict[str, Any], serial: str, evidence_dir: Path) -> WorkflowRunResult:
        ...


def item_information_workflow_definition() -> dict[str, Any]:
    """Return the deterministic workflow contract for item gallery inspection."""

    return {
        "id": WORKFLOW_ID,
        "label": BUTTON_LABEL,
        "primary_coordinates_allowed": False,
        "strategy_order": [
            "uiautomator_resource_id",
            "accessibility_content_desc",
            "exact_text",
            "contains_text_or_hierarchy",
            "webview_dom_role_aria_text_bounds",
            "opencv_grouping",
            "local_ocr",
            "optional_cloud_ocr",
            "structured_unresolved",
        ],
        "steps": [
            {
                "id": "ensure_item_page",
                "action": "ensure_state",
                "success_status": "ITEM_PAGE_DETECTED",
                "failure_status": BLOCKED_NOT_ITEM_PAGE,
                "signals": [
                    "Buy It Now",
                    "Add to cart",
                    "Watch",
                    "price_visible",
                    "product_title_visible",
                    "product_image_area_visible",
                ],
            },
            {
                "id": "find_gallery_area",
                "action": "scroll_until_found",
                "direction": "up",
                "max_scrolls": 8,
                "downward_retry_scrolls": 2,
                "target": {
                    "role": "product_gallery",
                    "hints": {
                        "text": ["Gallery"],
                        "content_desc": ["Image", "Gallery", "Product image"],
                        "aria_label": ["Image", "Gallery", "Product image"],
                    },
                },
                "failure_status": UNRESOLVED_GALLERY_NOT_FOUND,
            },
            {
                "id": "open_gallery",
                "action": "tap",
                "target_from": "find_gallery_area",
                "tap_area": {
                    "prefer": ["image_center", "safe_image_bounds"],
                    "avoid": ["favorite_heart", "navigation", "buy_button"],
                },
            },
            {
                "id": "verify_gallery_open",
                "action": "wait_state",
                "timeout_seconds": 10,
                "signals": ["Gallery", "close_button_visible", "thumbnail_grid_visible", "large_image_modal_visible"],
            },
            {
                "id": "scroll_gallery_down",
                "action": "scroll",
                "direction": "down",
                "container_role": "gallery_content",
                "times": 1,
                "wait_until": "screen_changes",
                "timeout_seconds": 5,
            },
            {
                "id": "close_gallery",
                "action": "tap",
                "target": {
                    "role": "gallery_close",
                    "hints": {
                        "text": ["X", "Close"],
                        "content_desc": ["Close", "Close gallery"],
                        "aria_label": ["Close", "Close gallery"],
                    },
                },
                "strategy_order": ["accessibility", "webview_dom", "exact_text", "local_ocr", "opencv_template"],
                "safe_fallback": "android_back_once_with_evidence",
                "failure_status": UNRESOLVED_GALLERY_CLOSE_NOT_FOUND,
            },
            {
                "id": "verify_item_page_restored",
                "action": "wait_state",
                "timeout_seconds": 10,
                "signals": ["Buy It Now", "Add to cart", "Watch", "price_visible", "product_title_visible", "item_url_or_state_restored"],
            },
            {
                "id": "capture_final_evidence",
                "action": "evidence",
                "save": [
                    "screenshot",
                    "ui_xml",
                    "selected_candidate_json",
                    "gallery_close_candidate_json",
                    "workflow_result_json",
                ],
            },
        ],
    }


def safe_gallery_tap_point(image_bounds: Bounds, overlay_bounds: Bounds | None = None) -> tuple[int, int]:
    """Choose a point inside the image while avoiding a favorite/heart overlay.

    eBay mobile often places the favorite heart near the lower-right of the
    product image. If the normal center intersects an overlay, tap left-center.
    """

    center = image_bounds.center
    if overlay_bounds is None or not overlay_bounds.contains(center):
        return center

    candidates = [
        (image_bounds.x + image_bounds.width // 3, image_bounds.y + image_bounds.height // 2),
        (image_bounds.x + image_bounds.width // 2, image_bounds.y + image_bounds.height // 3),
        (image_bounds.x + image_bounds.width // 4, image_bounds.y + image_bounds.height // 3),
    ]
    for point in candidates:
        if image_bounds.contains(point) and not overlay_bounds.contains(point):
            return point
    return center


def _new_evidence_dir(root: Path, workflow_id: str) -> Path:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    path = root / workflow_id / stamp
    path.mkdir(parents=True, exist_ok=True)
    return path


def run_item_information_workflow(
    serial: str,
    *,
    engine: WorkflowEngine | None = None,
    device_manager: DeviceManager | None = None,
    evidence_root: Path | str = Path(".ai") / "evidence",
) -> WorkflowRunResult:
    """Run or dispatch the Item Information workflow for one Android device.

    If a SmartLocator workflow engine is not yet available, this function still
    captures baseline evidence and returns a structured blocker instead of
    attempting blind coordinate taps.
    """

    root = Path(evidence_root)
    evidence_dir = _new_evidence_dir(root, WORKFLOW_ID)
    definition = item_information_workflow_definition()
    (evidence_dir / "workflow_definition.json").write_text(
        json.dumps(definition, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    manager = device_manager or DeviceManager()
    evidence: dict[str, Any] = {"workflow_definition": "workflow_definition.json"}

    try:
        manager.screenshot(serial, evidence_dir / "item_information_initial.png")
        evidence["initial_screenshot"] = "item_information_initial.png"
    except Exception as exc:  # evidence path must survive ADB/device failures
        evidence["initial_screenshot_error"] = repr(exc)

    try:
        manager.ui_xml(serial, evidence_dir / "item_information_initial.xml")
        evidence["initial_ui_xml"] = "item_information_initial.xml"
    except Exception as exc:
        evidence["initial_ui_xml_error"] = repr(exc)

    if engine is None:
        result = WorkflowRunResult(
            workflow_id=WORKFLOW_ID,
            status=BLOCKED_PERCEPTION_ENGINE_REQUIRED,
            message="Item Information workflow is registered, but no SmartLocator workflow engine is attached yet.",
            evidence_dir=str(evidence_dir),
            evidence=evidence,
        )
    else:
        result = engine.execute_workflow(definition, serial, evidence_dir)

    (evidence_dir / "workflow_result.json").write_text(
        json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return result
