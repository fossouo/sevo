"""Runtime persistence envelope + schema migrations.

A saved *runtime* is more than the brain's cognitive state: it also carries the
service counters and the session history. To keep ``Brain.export_state`` pure
(cognitive only, schema ``0.4``), the runtime wraps it in an **envelope** with
its own ``runtime_schema_version`` and a migration chain.

Why migrations matter: the brain will evolve quickly. A state saved under one
version must never be silently reinterpreted under a newer structure — it is
either migrated forward explicitly, or rejected with a clear error.

    0.4  (bare ``Brain.export_state`` saved directly — PR #3)
    0.5  (envelope: brain + counters + sessions — PR #4)
"""
from __future__ import annotations

RUNTIME_SCHEMA_VERSION = "0.5"
SUPPORTED_RUNTIME_SCHEMAS = {"0.5"}
MIGRATABLE_FROM = {"0.4"}

DEFAULT_COUNTERS = {"perceptions": 0, "actions": 0, "feedbacks": 0, "consolidations": 0}


class EnvelopeSchemaError(ValueError):
    pass


def make_envelope(brain_state: dict, counters: dict, sessions: dict) -> dict:
    return {
        "runtime_schema_version": RUNTIME_SCHEMA_VERSION,
        "brain": brain_state,
        "counters": {**DEFAULT_COUNTERS, **counters},
        "sessions": sessions,
    }


def _looks_like_bare_brain(env: dict) -> bool:
    return "procedural_skills" in env and "brain" not in env


def _migrate_0_4_to_0_5(env: dict) -> dict:
    env = dict(env)
    env["counters"] = {**DEFAULT_COUNTERS, **env.get("counters", {})}
    env.setdefault("sessions", {})
    env["runtime_schema_version"] = "0.5"
    return env


_MIGRATIONS = {"0.4": _migrate_0_4_to_0_5}


def migrate_envelope(env: dict) -> dict:
    """Bring any supported or migratable envelope up to the current version, or
    raise EnvelopeSchemaError. A bare brain export (PR #3 save) is treated as a
    legacy 0.4 envelope and wrapped."""
    if "runtime_schema_version" not in env:
        if _looks_like_bare_brain(env):
            env = {"runtime_schema_version": "0.4", "brain": env,
                   "counters": {}, "sessions": {}}
        else:
            raise EnvelopeSchemaError(
                "state has no 'runtime_schema_version' and is not a recognisable "
                "bare brain export — refusing to load."
            )
    version = env["runtime_schema_version"]
    while version in MIGRATABLE_FROM and version not in SUPPORTED_RUNTIME_SCHEMAS:
        env = _MIGRATIONS[version](env)
        version = env["runtime_schema_version"]
    if version not in SUPPORTED_RUNTIME_SCHEMAS:
        raise EnvelopeSchemaError(
            f"unsupported runtime_schema_version {version!r}; this build supports "
            f"{sorted(SUPPORTED_RUNTIME_SCHEMAS)} (migratable from {sorted(MIGRATABLE_FROM)})."
        )
    return env
