import json

from control_android.logging_utils import JsonlLogger


def test_jsonl_logger_emits_parseable_record(tmp_path) -> None:
    path = tmp_path / "run.jsonl"
    logger = JsonlLogger(path)
    record = logger.emit("info", "startup", jobId="G00")

    assert record["level"] == "INFO"
    assert record["event"] == "startup"
    assert "timestamp" in record

    saved = json.loads(path.read_text(encoding="utf-8").strip())
    assert saved["context"]["jobId"] == "G00"
