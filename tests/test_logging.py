import json
import logging

from aria.logging_setup import MASK, JsonFormatter, SecretMasker, trace_id_var


def _format(record_message: str, secrets: list[str], **extra) -> dict:
    formatter = JsonFormatter(SecretMasker(secrets))
    record = logging.LogRecord("aria.test", logging.INFO, __file__, 1, record_message, None, None)
    for key, value in extra.items():
        setattr(record, key, value)
    return json.loads(formatter.format(record))


def test_log_lines_are_json_with_extra_fields():
    entry = _format("tool finished", [], step="tool_calling", duration_ms=12)
    assert entry["msg"] == "tool finished"
    assert entry["level"] == "INFO"
    assert entry["step"] == "tool_calling"
    assert entry["duration_ms"] == 12


def test_secrets_are_masked_in_messages_and_fields():
    entry = _format("calling with key abc123secret", ["abc123secret"], header="Bearer abc123secret")
    assert "abc123secret" not in json.dumps(entry)
    assert entry["msg"].endswith(MASK)


def test_longer_secrets_are_masked_whole():
    masker = SecretMasker(["abc", "abcdef"])
    assert masker.mask("token=abcdef") == f"token={MASK}"


def test_trace_id_is_attached_when_set():
    token = trace_id_var.set("trace-1")
    try:
        entry = _format("step", [])
    finally:
        trace_id_var.reset(token)
    assert entry["trace_id"] == "trace-1"
