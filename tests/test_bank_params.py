"""Contract test: teaching/held-out bank split parameters are pinned.

The committed developmental curve (reports/DEVELOPMENTAL_CURVE.md and the
numeric fixture tests/test_curve_numeric_fixture.py) depends on the exact
teaching/held-out split used to build every bank. Those tests pin the *trial
counts* and *transfer deltas* that result from the split, but nothing names the
split parameters themselves as a contract — so a silent change to a default
(e.g. ``frac_teach=0.55`` → ``0.6``) would shift every number and be diagnosed
only indirectly, after a full curve re-run.

This test pins the parameters *as named constants*, so an accidental change to
a ``build_bank*`` default fails immediately and points at the cause, not the
symptom.

These are PROTOCOL constants: changing them is a protocol break that requires
regenerating every committed demo artifact and updating the numeric fixture
(see docs/CP_PROTOCOL.md, docs/DEVELOPMENTAL_CURVE.md).
"""
import inspect
import unittest

from sevo.curriculum import (
    cm1_maths,
    cp_ce1_math,
    cp_maths_numeration,
    fr_conjugation,
    fr_cp_ce1,
    fr_lecture_cp,
)

# Pinned protocol values (must match the curriculum module defaults).
FRAC_TEACH = 0.55
N_TEACH = 24
N_HELDOUT = 24

# (module, function_name) for every bank builder that takes ``frac_teach``.
_FRAC_TEACH_BUILDERS = [
    (fr_lecture_cp, "build_bank_lecture"),
    (fr_cp_ce1, "build_bank_fr"),
    (cp_maths_numeration, "build_bank_num"),
    (cm1_maths, "build_bank_cm1"),
    (fr_conjugation, "build_bank_conj"),
]


def _default(func, param):
    return inspect.signature(func).parameters[param].default


class TestBankSplitParametersPinned(unittest.TestCase):
    def test_frac_teach_default_is_pinned_everywhere(self):
        for mod, name in _FRAC_TEACH_BUILDERS:
            func = getattr(mod, name)
            self.assertEqual(
                _default(func, "frac_teach"),
                FRAC_TEACH,
                f"{mod.__name__}.{name} frac_teach default drifted "
                f"(expected {FRAC_TEACH}). This is a protocol break — "
                f"regenerate artifacts + numeric fixture if intended.",
            )

    def test_count_based_builder_defaults_are_pinned(self):
        func = cp_ce1_math.build_bank
        self.assertEqual(_default(func, "n_teach"), N_TEACH,
                         "cp_ce1_math.build_bank n_teach default drifted")
        self.assertEqual(_default(func, "n_heldout"), N_HELDOUT,
                         "cp_ce1_math.build_bank n_heldout default drifted")

    def test_every_frac_teach_builder_actually_exposes_the_param(self):
        # Guards against a refactor that renames/removes the knob silently.
        for mod, name in _FRAC_TEACH_BUILDERS:
            params = inspect.signature(getattr(mod, name)).parameters
            self.assertIn(
                "frac_teach", params,
                f"{mod.__name__}.{name} no longer exposes frac_teach",
            )


if __name__ == "__main__":
    unittest.main()
