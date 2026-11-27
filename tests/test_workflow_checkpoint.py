"""Versioned checkpoint contract and malicious input regression tests."""

import json

import pytest

from praxiloop.workflow_checkpoint import InvalidCheckpoint, dump_checkpoint, load_checkpoint
from praxiloop.workflow_journal import InMemoryWorkflowJournal, WorkflowRecord
from praxiloop.workflow_state import WorkflowEvent as E, WorkflowSnapshot, WorkflowState as S


PATHS = [
    (),
    (E.START_INVESTIGATION,),
    (E.START_INVESTIGATION, E.INVESTIGATION_FAILED),
    (E.START_INVESTIGATION, E.INVESTIGATION_COMPLETE, E.DENY),
    (
        E.START_INVESTIGATION, E.INVESTIGATION_COMPLETE, E.APPROVE,
        E.START_EXECUTION, E.EXECUTION_COMPLETE, E.VERIFICATION_PASSED,
    ),
]


def journal_record(events):
    journal = InMemoryWorkflowJournal()
    for index, event in enumerate(events):
        journal.append("wf-1", event, expected_revision=index, idempotency_key=f"cmd-{index}")
    return journal.read_record("wf-1")


@pytest.mark.parametrize("events", PATHS)
def test_round_trip_through_versioned_format(events):
    record = journal_record(events)
    encoded = dump_checkpoint("wf-1", record)
    workflow_id, restored = load_checkpoint(encoded)
    assert workflow_id == "wf-1"
    assert restored == record
    assert json.loads(encoded)["schema_version"] == 1
    assert encoded == dump_checkpoint("wf-1", restored)


def test_checkpoint_does_not_change_original_record():
    original = journal_record((E.START_INVESTIGATION,))
    dump_checkpoint("wf", original)
    assert original.snapshot.revision == 1
    assert original.events == (E.START_INVESTIGATION,)


def test_encoding_is_canonical_without_whitespace():
    a = dump_checkpoint("wf-1", journal_record(()))
    b = dump_checkpoint("wf-1", journal_record(()))
    assert a == b
    assert "\n" not in a
    assert " " not in a


@pytest.mark.parametrize("bad", ["", " ", "../abc", "\u00e9", "x" * 129, None, True, 1])
def test_reject_invalid_workflow_ids(bad):
    with pytest.raises(InvalidCheckpoint):
        dump_checkpoint(bad, journal_record(()))


@pytest.mark.parametrize("bad", [0, -1, True, 1.5, "1", None])
def test_reject_invalid_event_limits(bad):
    with pytest.raises(ValueError, match="max_events"):
        load_checkpoint("{}", max_events=bad)
    with pytest.raises(ValueError, match="max_events"):
        dump_checkpoint("wf", journal_record(()), max_events=bad)


@pytest.mark.parametrize("bad", [0, -1, True, 1.5, "4096", None])
def test_reject_invalid_byte_limits(bad):
    with pytest.raises(ValueError, match="max_bytes"):
        load_checkpoint("{}", max_bytes=bad)
    with pytest.raises(ValueError, match="max_bytes"):
        dump_checkpoint("wf", journal_record(()), max_bytes=bad)


def test_reject_record_not_matching_event_history():
    tampered = WorkflowRecord(snapshot=WorkflowSnapshot(state=S.SUCCEEDED, revision=1), events=(E.START_INVESTIGATION,))
    with pytest.raises(InvalidCheckpoint):
        dump_checkpoint("wf", tampered)


def test_reject_invalid_record_type():
    with pytest.raises(InvalidCheckpoint):
        dump_checkpoint("wf", "wrong")


def test_reject_event_limit_before_export_or_import():
    record = journal_record((E.START_INVESTIGATION, E.INVESTIGATION_COMPLETE))
    with pytest.raises(InvalidCheckpoint):
        dump_checkpoint("wf", record, max_events=1)
    with pytest.raises(InvalidCheckpoint):
        load_checkpoint(dump_checkpoint("wf", record), max_events=1)


def test_reject_byte_limit_for_both_directions():
    encoded = dump_checkpoint("wf", journal_record(()))
    with pytest.raises(InvalidCheckpoint):
        dump_checkpoint("wf", journal_record(()), max_bytes=10)
    with pytest.raises(InvalidCheckpoint):
        load_checkpoint(encoded, max_bytes=10)


def valid_document():
    return json.loads(dump_checkpoint("wf", journal_record((E.START_INVESTIGATION,))))


@pytest.mark.parametrize("field,invalid", [
    ("schema_version", 2),
    ("schema_version", True),
    ("workflow_id", "../unsafe"),
    ("workflow_id", 4),
    ("state", "UNKNOWN"),
    ("state", True),
    ("revision", True),
    ("revision", -1),
    ("revision", "1"),
    ("events", "START_INVESTIGATION"),
    ("events", ["APPROVE"]),
    ("events", [1]),
    ("events", ["START_INVESTIGATION", "START_INVESTIGATION"]),
])
def test_reject_invalid_values(field, invalid):
    payload = valid_document()
    payload[field] = invalid
    with pytest.raises(InvalidCheckpoint):
        load_checkpoint(json.dumps(payload))


@pytest.mark.parametrize("field", ["schema_version", "workflow_id", "state", "revision", "events"])
def test_reject_missing_required_fields(field):
    payload = valid_document()
    del payload[field]
    with pytest.raises(InvalidCheckpoint):
        load_checkpoint(json.dumps(payload))


def test_reject_unknown_fields():
    payload = valid_document()
    payload["approved_by"] = "injected"
    with pytest.raises(InvalidCheckpoint):
        load_checkpoint(json.dumps(payload))


def test_reject_duplicate_json_keys():
    valid = dump_checkpoint("wf", journal_record(()))
    duplicated = valid.replace('"schema_version":1', '"schema_version":1,"schema_version":1')
    with pytest.raises(InvalidCheckpoint):
        load_checkpoint(duplicated)


@pytest.mark.parametrize("bad", ['{', 'null', '[]', '"string"', 'NaN', 'Infinity', ''])
def test_reject_malformed_or_non_object_json(bad):
    with pytest.raises(InvalidCheckpoint):
        load_checkpoint(bad)


def test_reject_revision_mismatch_even_with_legal_events():
    payload = valid_document()
    payload["revision"] = 2
    with pytest.raises(InvalidCheckpoint):
        load_checkpoint(json.dumps(payload))


def test_reject_state_mismatch_even_with_legal_events():
    payload = valid_document()
    payload["state"] = S.SUCCEEDED.value
    with pytest.raises(InvalidCheckpoint):
        load_checkpoint(json.dumps(payload))


def test_import_has_no_side_effects_on_journal():
    journal = InMemoryWorkflowJournal()
    record = journal.read_record("wf")
    restored_id, restored = load_checkpoint(dump_checkpoint("wf", record))
    assert restored_id == "wf"
    assert restored == record
    assert journal.events_for("wf") == ()
