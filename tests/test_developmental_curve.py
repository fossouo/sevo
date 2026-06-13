"""Developmental curve naïf → CP → CE1 → CE2.

Freezes the answer to the CE2 research question: a CE1-appris brain accelerates
CE2 arithmetic *more* than CP accelerated CE1 — because the `carry` bottleneck,
new at CE1, is mastered by CE2 and completes the prerequisite chain.
"""
import importlib.util
import json
import os

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "developmental_curve",
    os.path.join(os.path.dirname(__file__), "..", "scripts", "developmental_curve.py"))
curve_mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(curve_mod)


@pytest.fixture(scope="module")
def curve(tmp_path_factory):
    out = tmp_path_factory.mktemp("curve_art")
    rep = tmp_path_factory.mktemp("curve_rep")
    return curve_mod.run(str(out), str(rep)), str(out), str(rep)


def test_bottleneck_unlocks_along_the_curve(curve):
    c, _, _ = curve
    cp = c["steps"]["CP->CE1"]["spotlight"]
    ce = c["steps"]["CE1->CE2"]["spotlight"]
    assert c["bottleneck_unlocked"]
    # CE1→CE2 arithmetic transfers more than CP→CE1 did (carry now known)
    assert ce["transfer"] > cp["transfer"]
    assert ce["transfer"] >= 0.5 and cp["transfer"] < 0.2


def test_ce1_to_ce2_arithmetic_is_faster(curve):
    c, _, _ = curve
    ce = c["steps"]["CE1->CE2"]["spotlight"]
    assert ce["trials_dev"] < ce["trials_naive"]    # CE1-appris learns CE2 add faster


def test_curve_artifacts_and_report(curve):
    _, out, rep = curve
    path = os.path.join(out, "curve.json")
    assert os.path.exists(path)
    json.load(open(path, encoding="utf-8"))
    assert os.path.exists(os.path.join(rep, "DEVELOPMENTAL_CURVE.md"))


def test_curve_is_deterministic(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    curve_mod.run(str(a), str(a))
    curve_mod.run(str(b), str(b))
    assert (a / "curve.json").read_text(encoding="utf-8") == (b / "curve.json").read_text(encoding="utf-8")
