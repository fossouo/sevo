"""Runtime state schema migrations — never misread an old save silently."""
import pytest

from sevo.brain import Brain
from sevo.persistence import (
    RUNTIME_SCHEMA_VERSION,
    EnvelopeSchemaError,
    make_envelope,
    migrate_envelope,
)


def test_bare_brain_state_is_wrapped_and_migrated():
    bare = Brain(seed=1).export_state()           # a PR#3-style bare save
    env = migrate_envelope(bare)
    assert env["runtime_schema_version"] == RUNTIME_SCHEMA_VERSION
    assert env["brain"] == bare
    assert "counters" in env and "sessions" in env


def test_explicit_0_4_envelope_migrates_and_backfills_counters():
    bare = Brain(seed=1).export_state()
    env04 = {"runtime_schema_version": "0.4", "brain": bare,
             "counters": {"feedbacks": 3}, "sessions": {}}
    env = migrate_envelope(env04)
    assert env["runtime_schema_version"] == "0.5"
    assert env["counters"]["feedbacks"] == 3       # preserved
    assert env["counters"]["perceptions"] == 0     # backfilled
    assert env["baseline_snapshot"] is None        # legacy had none
    assert env["seed"] == 0                         # backfilled default


def test_current_envelope_passes_through():
    env = make_envelope(Brain(seed=1).export_state(), {}, {})
    assert migrate_envelope(env)["runtime_schema_version"] == RUNTIME_SCHEMA_VERSION


def test_unsupported_or_unrecognised_is_rejected():
    with pytest.raises(EnvelopeSchemaError):
        migrate_envelope({"runtime_schema_version": "9.9", "brain": {}})
    with pytest.raises(EnvelopeSchemaError):
        migrate_envelope({"foo": "bar"})           # neither versioned nor a bare brain
