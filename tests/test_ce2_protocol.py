"""CE2 respects the frozen CP protocol — extension, not a rewrite."""
import importlib.util
import os

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "demo_cp", os.path.join(os.path.dirname(__file__), "..", "scripts", "demo_cp.py"))
demo_cp = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(demo_cp)


@pytest.fixture(scope="module")
def ce2(tmp_path_factory):
    return demo_cp.run(str(tmp_path_factory.mktemp("ce2")), grade="CE2")


def test_ce2_genuine_under_frozen_protocol(ce2):
    assert ce2["grade"] == "CE2" and ce2["verdict"] == "GENUINE" and ce2["genuine"]
    assert ce2["audit_clean"] and ce2["leakage_clean"] and ce2["replay_deterministic"]


def test_ce2_after_ce1_chain_is_genuine(tmp_path):
    r = demo_cp.run(str(tmp_path), grade="CE2", prior_grade="CP,CE1")
    assert r["mode"] == "after_cp_ce1" and r["verdict"] == "GENUINE"
    assert r["reload_exact"] and r["audit_clean"]


def test_ce2_artifacts_deterministic(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    demo_cp.run(str(a), grade="CE2")
    demo_cp.run(str(b), grade="CE2")
    for name in ("brain_before.json", "brain_after.json", "brain_diff.json",
                 "assessment_report.json", "audit_report.json"):
        assert (a / name).read_text(encoding="utf-8") == (b / name).read_text(encoding="utf-8")
