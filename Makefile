PYTHON ?= python3
export PYTHONPATH := src

.PHONY: test demo-cp demo-ce1 demo-ce1-after-cp demo-ce2 demo-ce2-after-ce1 demo-cm1 \
        demo-developmental demo-developmental-evidence demo-developmental-curve report demo-docker

test:
	$(PYTHON) -m pytest -q

# One-command founder proof: Brain naïf -> Emma -> Brain appris -> diff ->
# independent eval -> GENUINE -> save/reload -> re-eval. Same protocol per grade.
demo-cp:
	$(PYTHON) scripts/demo_cp.py CP

demo-ce1:                       # naïve: a fresh brain learns CE1 in isolation
	$(PYTHON) scripts/demo_cp.py CE1

demo-ce1-after-cp:              # developmental: a CP-appris brain then learns CE1
	$(PYTHON) scripts/demo_cp.py CE1 CP

demo-ce2:                       # naïve: a fresh brain learns CE2 in isolation
	$(PYTHON) scripts/demo_cp.py CE2

demo-ce2-after-ce1:             # developmental: naïf → CP → CE1 → CE2
	$(PYTHON) scripts/demo_cp.py CE2 CP,CE1

demo-cm1:                       # CM1 (introduces multiplication — a new bottleneck)
	$(PYTHON) scripts/demo_cp.py CM1

# Research study: does CP-appris help learn CE1? (developmental vs isolated)
demo-developmental:
	$(PYTHON) scripts/developmental.py

# Freeze the CP->CE1 finding as evidence: skill-level transfer matrix + report.
demo-developmental-evidence:
	$(PYTHON) scripts/developmental_evidence.py

# Developmental curve naïf→CP→CE1→CE2: does each class unlock the next?
demo-developmental-curve:
	$(PYTHON) scripts/developmental_curve.py

# Regenerate the reproducible experiment reports (maths / FR / conjugation / CP).
report:
	PYTHONPATH=src:experiments $(PYTHON) experiments/generate_report.py

# Run the brain as a container service and smoke-test it over HTTP.
demo-docker:
	docker compose up --build -d
	@echo "waiting for health..."; sleep 5
	./scripts/smoke_test.sh
