"""CP protocol freeze — non-regression guard for the founder demo socle.

The CP-appris brain MUST stay: GENUINE, save/reload exact, audit clean, replay
deterministic, and free of item leakage. This runs the actual founder demo and
asserts those five invariants + that the six proof artifacts are produced. If a
future change breaks any of them, it is a protocol break (see docs/CP_PROTOCOL.md).
"""
import importlib.util
import json
import os

import pytest

from sevo.curriculum.factory import teaching_bank
from sevo.eval import ItemLeakageError
from sevo.runtime import BrainService

# Load the demo script (lives under scripts/, not an installed package).
_SPEC = importlib.util.spec_from_file_location(
    "demo_cp", os.path.join(os.path.dirname(__file__), "..", "scripts", "demo_cp.py"))
demo_cp = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(demo_cp)

NODE = "fr.CP.lecture_mots_reguliers"
ARTIFACTS = ("brain_before.json", "brain_after.json", "brain_diff.json",
             "assessment_report.json", "emma_session_journal.json", "audit_report.json")


@pytest.fixture(scope="module")
def demo(tmp_path_factory):
    out = tmp_path_factory.mktemp("demo")
    return demo_cp.run(str(out)), str(out)


def test_demo_verdict_is_genuine(demo):
    result, _ = demo
    assert result["verdict"] == "GENUINE" and result["genuine"]


def test_demo_save_reload_exact(demo):
    result, _ = demo
    assert result["reload_exact"]


def test_demo_audit_clean_no_leakage(demo):
    result, _ = demo
    assert result["audit_clean"] and result["leakage_clean"]


def test_demo_replay_deterministic(demo):
    result, _ = demo
    assert result["replay_deterministic"]


def test_demo_produces_all_proof_artifacts(demo):
    _, out = demo
    for name in ARTIFACTS:
        path = os.path.join(out, name)
        assert os.path.exists(path), f"missing artifact {name}"
        with open(path, encoding="utf-8") as f:
            json.load(f)                         # valid JSON


def test_assessment_report_records_independent_verdict(demo):
    _, out = demo
    with open(os.path.join(out, "assessment_report.json"), encoding="utf-8") as f:
        report = json.load(f)
    assert report["verdict"]["verdict"] == "GENUINE"
    assert report["reload_exact"]


def test_evaluate_still_refuses_taught_items():
    """The anti-leakage guard is part of the frozen protocol."""
    svc = BrainService(seed=0)
    seen = teaching_bank(NODE, 0)[0].word
    with pytest.raises(ItemLeakageError):
        svc.evaluate(NODE, items=[seen])
