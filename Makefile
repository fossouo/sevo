PYTHON ?= python3
export PYTHONPATH := src

.PHONY: test demo-cp demo-ce1 demo-ce1-after-cp report demo-docker

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

# Regenerate the reproducible experiment reports (maths / FR / conjugation / CP).
report:
	PYTHONPATH=src:experiments $(PYTHON) experiments/generate_report.py

# Run the brain as a container service and smoke-test it over HTTP.
demo-docker:
	docker compose up --build -d
	@echo "waiting for health..."; sleep 5
	./scripts/smoke_test.sh
