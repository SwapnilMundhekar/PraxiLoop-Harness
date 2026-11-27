"""Strict, versioned JSON codec for process-local workflow checkpoint records.

This is a persistence *format*, not durable storage or a trusted audit record.
Import verifies internal state/event consistency, not approval authenticity.
"""

import json
import re

from praxiloop.workflow_integrity import JournalIntegrityError, validate_record
from praxiloop.workflow_journal import WorkflowRecord
from praxiloop.workflow_state import WorkflowEvent, WorkflowSnapshot, WorkflowState

_SCHEMA_VERSION = 1
_FIELDS = frozenset({"schema_version", "workflow_id", "state", "revision", "events"})
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


class InvalidCheckpoint(ValueError):
    """Untrusted checkpoint does not conform to this versioned contract."""


def _limits(max_events: int, max_bytes: int) -> None:
    if type(max_events) is not int or max_events < 1:
        raise ValueError("max_events must be a positive integer")
    if type(max_bytes) is not int or max_bytes < 1:
        raise ValueError("max_bytes must be a positive integer")


def _workflow_id(value: object) -> str:
    if type(value) is not str or _ID.fullmatch(value) is None:
        raise InvalidCheckpoint("invalid workflow_id")
    return value


def _unique_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for name, value in pairs:
        if name in result:
            raise InvalidCheckpoint("duplicate JSON key")
        result[name] = value
    return result


def _reject_constant(_value: str) -> None:
    raise InvalidCheckpoint("non-standard JSON constant")


def dump_checkpoint(
    workflow_id: str,
    record: WorkflowRecord,
    *,
    max_events: int = 16,
    max_bytes: int = 4096,
) -> str:
    """Serialize a consistent record in canonical, ASCII-only JSON."""
    _limits(max_events, max_bytes)
    name = _workflow_id(workflow_id)
    if type(record) is not WorkflowRecord:
        raise InvalidCheckpoint("record must be a WorkflowRecord")
    if type(record.events) is not tuple or len(record.events) > max_events:
        raise InvalidCheckpoint("invalid or oversized event sequence")
    try:
        validate_record(record)
    except (JournalIntegrityError, TypeError, ValueError):
        raise InvalidCheckpoint("record failed internal consistency check") from None
    result = json.dumps(
        {
            "schema_version": _SCHEMA_VERSION,
            "workflow_id": name,
            "state": record.snapshot.state.value,
            "revision": record.snapshot.revision,
            "events": [event.value for event in record.events],
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    if len(result.encode("utf-8")) > max_bytes:
        raise InvalidCheckpoint("checkpoint exceeds byte limit")
    return result


def load_checkpoint(
    document: str,
    *,
    max_events: int = 16,
    max_bytes: int = 4096,
) -> tuple[str, WorkflowRecord]:
    """Decode and independently replay untrusted version-1 JSON data."""
    _limits(max_events, max_bytes)
    if type(document) is not str:
        raise InvalidCheckpoint("checkpoint must be a JSON string")
    if len(document.encode("utf-8", errors="surrogatepass")) > max_bytes:
        raise InvalidCheckpoint("checkpoint exceeds byte limit")
    try:
        data = json.loads(
            document, object_pairs_hook=_unique_keys, parse_constant=_reject_constant
        )
    except (ValueError, TypeError, OverflowError, RecursionError):
        raise InvalidCheckpoint("checkpoint is not valid JSON") from None
    if type(data) is not dict or data.keys() != _FIELDS:
        raise InvalidCheckpoint("unexpected checkpoint fields")
    if type(data["schema_version"]) is not int or data["schema_version"] != _SCHEMA_VERSION:
        raise InvalidCheckpoint("unsupported checkpoint schema")
    workflow_id = _workflow_id(data["workflow_id"])
    if type(data["events"]) is not list or len(data["events"]) > max_events:
        raise InvalidCheckpoint("invalid or oversized event sequence")
    if type(data["revision"]) is not int or data["revision"] < 0:
        raise InvalidCheckpoint("invalid revision")
    if type(data["state"]) is not str or any(type(v) is not str for v in data["events"]):
        raise InvalidCheckpoint("state and events must be strings")
    try:
        record = WorkflowRecord(
            snapshot=WorkflowSnapshot(
                state=WorkflowState(data["state"]), revision=data["revision"]
            ),
            events=tuple(WorkflowEvent(value) for value in data["events"]),
        )
        validate_record(record)
    except (ValueError, TypeError):
        raise InvalidCheckpoint("invalid workflow state or event history") from None
    return workflow_id, record
