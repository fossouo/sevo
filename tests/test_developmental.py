"""Developmental progression CP → CE1 — measurable, honest transfer.

Asserts the research result: a CP-appris brain starts CE1 with a real transfer
advantage, strongest where skills are shared (arithmetic). We assert the robust
signals (transfer pretest, the arithmetic head-start, artifacts, determinism),
not the marginal global-speed number.
"""
import importlib.util
import json
import os

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "developmental", os.path.join(os.path.dirname(__file__), "..", "scripts", "developmental.py"))
developmental = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(developmental)

ARTIFACTS = ("brain_after_cp.json", "brain_after_ce1.json",
             "cp_to_ce1_diff.json", "developmental_comparison.json")


@pytest.fixture(scope="module")
def study(tmp_path_factory):
    out = tmp_path_factory.mktemp("dev_art")
    rep = tmp_path_factory.mktemp("dev_rep")
    return developmental.run(str(out), str(rep)), str(out), str(rep)


def test_cp_appris_brain_transfers_to_ce1(study):
    result, _, _ = study
    tp = result["comparison"]["aggregate"]["transfer_pretest"]
    assert tp["developmental"] > tp["isolated"]      # measurable CP→CE1 transfer


def test_transfer_is_strongest_on_shared_arithmetic(study):
    """Place value + number facts learned at CP carry into CE1 arithmetic."""
    result, _, _ = study
    add = result["comparison"]["per_node"]["math.CE1.add_within_100_nocarry"]
    assert add["developmental"]["pretest"] > add["isolated"]["pretest"]
    assert add["developmental"]["pretest"] >= 0.5    # near-mastery at pretest from CP


def test_artifacts_and_report_produced(study):
    _, out, rep = study
    for name in ARTIFACTS:
        path = os.path.join(out, name)
        assert os.path.exists(path)
        json.load(open(path, encoding="utf-8"))
    assert os.path.exists(os.path.join(rep, "DEVELOPMENTAL_REPORT.md"))


def test_cp_to_ce1_diff_shows_added_competences(study):
    _, out, _ = study
    diff = json.load(open(os.path.join(out, "cp_to_ce1_diff.json"), encoding="utf-8"))
    assert diff["semantic_concepts_added"]           # CE1 adds concepts on top of CP


def test_developmental_artifacts_deterministic(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    developmental.run(str(a), str(a))
    developmental.run(str(b), str(b))
    for name in ARTIFACTS:
        assert (a / name).read_text(encoding="utf-8") == (b / name).read_text(encoding="utf-8")
