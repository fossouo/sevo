"""Developmental evidence — non-regression guards for the frozen CP→CE1 result.

These protect the *scientific* finding, not just the code:
  * arithmetic transfer (shared structure) must stay positive/confirmed;
  * French transfer (unshared) must NOT be artificially forced;
  * transfer must stay LOCALIZED — any future PR that "improves everything
    everywhere" is suspect and should fail here.
"""
import importlib.util
import json
import os

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "developmental_evidence",
    os.path.join(os.path.dirname(__file__), "..", "scripts", "developmental_evidence.py"))
ev = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(ev)

ARTIFACTS = ("naive_to_ce1.json", "cp_to_ce1.json", "transfer_matrix.json",
             "developmental_delta.json")
FRENCH = ("fr.CE1.pluriel_reguliers", "fr.CE1.pluriel_en_al", "fr.CE1.present_verbes_er")


@pytest.fixture(scope="module")
def evidence(tmp_path_factory):
    out = tmp_path_factory.mktemp("ev_art")
    docs = tmp_path_factory.mktemp("ev_docs")
    reps = tmp_path_factory.mktemp("ev_rep")
    return ev.run(str(out), str(docs), str(reps)), str(out), str(docs)


def test_arithmetic_transfer_stays_confirmed(evidence):
    result, _, _ = evidence
    add = result["matrix"]["by_node"]["math.CE1.add_within_100_nocarry"]
    assert add["verdict"] == "confirmed" and add["observed_transfer"] > 0


def test_transfer_stays_localized_not_global(evidence):
    """Not everything transfers — at least one CE1 node must be 'absent'. A PR
    that makes every node confirmed is suspect (forced/global improvement)."""
    result, _, _ = evidence
    verdicts = [v["verdict"] for v in result["matrix"]["by_node"].values()]
    assert result["n_confirmed"] < result["n_nodes"]
    assert "absent" in verdicts


def test_french_transfer_is_not_artificially_forced(evidence):
    """French nodes share only a low-weight skill with CP — none may be
    'confirmed' (that would mean transfer was forced, not real)."""
    result, _, _ = evidence
    bn = result["matrix"]["by_node"]
    for n in FRENCH:
        assert bn[n]["verdict"] in ("weak", "absent")


def test_evidence_artifacts_and_report(evidence):
    _, out, docs = evidence
    for name in ARTIFACTS:
        path = os.path.join(out, name)
        assert os.path.exists(path)
        json.load(open(path, encoding="utf-8"))
    assert os.path.exists(os.path.join(docs, "DEVELOPMENTAL_EVIDENCE.md"))


def test_transfer_matrix_records_the_bottleneck_finding(evidence):
    """The key result: addition WITHOUT carry transfers from CP, addition WITH
    carry does not — because `carry` is new at CE1 (transfer gated by the
    missing bottleneck skill)."""
    result, _, _ = evidence
    bn = result["matrix"]["by_node"]
    assert "carry" in bn["math.CE1.add_within_100_carry"]["new_skills_at_ce1"]
    assert bn["math.CE1.add_within_100_nocarry"]["observed_transfer"] > \
        bn["math.CE1.add_within_100_carry"]["observed_transfer"]


def test_evidence_is_deterministic(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    ev.run(str(a), str(a), str(a))
    ev.run(str(b), str(b), str(b))
    for name in ARTIFACTS:
        assert (a / name).read_text(encoding="utf-8") == (b / name).read_text(encoding="utf-8")
