"""CE1 respects the FROZEN CP protocol — extension, not a rewrite.

The CE1 demo must produce the same six artifacts as CP, with the same
guarantees: GENUINE, save/reload exact, audit clean, replay deterministic, no
item leakage, deterministic artifacts. Nothing about GENUINE, teacher/oracle
separation or anti-leakage is allowed to change.
"""
import importlib.util
import json
import os

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "demo_cp", os.path.join(os.path.dirname(__file__), "..", "scripts", "demo_cp.py"))
demo_cp = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(demo_cp)

ARTIFACTS = ("brain_before.json", "brain_after.json", "brain_diff.json",
             "assessment_report.json", "emma_session_journal.json", "audit_report.json")


@pytest.fixture(scope="module")
def ce1(tmp_path_factory):
    out = tmp_path_factory.mktemp("ce1")
    return demo_cp.run(str(out), grade="CE1"), str(out)


def test_ce1_is_genuine_under_the_frozen_protocol(ce1):
    result, _ = ce1
    assert result["grade"] == "CE1"
    assert result["verdict"] == "GENUINE" and result["genuine"]


def test_ce1_save_reload_audit_replay(ce1):
    result, _ = ce1
    assert result["reload_exact"]
    assert result["audit_clean"] and result["leakage_clean"]
    assert result["replay_deterministic"]


def test_ce1_artifacts_comparable_to_cp(ce1):
    """Same six proof files, same shapes — a CE1 report comparable to CP."""
    _, out = ce1
    for name in ARTIFACTS:
        path = os.path.join(out, name)
        assert os.path.exists(path)
        json.load(open(path, encoding="utf-8"))
    diff = json.load(open(os.path.join(out, "brain_diff.json"), encoding="utf-8"))
    assert diff["semantic_concepts_added"]              # CE1 concepts acquired
    assess = json.load(open(os.path.join(out, "assessment_report.json"), encoding="utf-8"))
    assert assess["verdict"]["verdict"] == "GENUINE" and assess["reload_exact"]


def test_ce1_artifacts_are_deterministic(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    demo_cp.run(str(a), grade="CE1")
    demo_cp.run(str(b), grade="CE1")
    for name in ARTIFACTS:
        assert (a / name).read_text(encoding="utf-8") == (b / name).read_text(encoding="utf-8")
