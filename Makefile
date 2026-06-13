PYTHON ?= python3
export PYTHONPATH := src

.PHONY: test demo-cp report demo-docker

test:
	$(PYTHON) -m pytest -q

# One-command founder proof: Brain CP-naïf -> Emma -> Brain CP-appris ->
# diff -> independent eval -> GENUINE -> save/reload -> re-eval.
demo-cp:
	$(PYTHON) scripts/demo_cp.py

# Regenerate the reproducible experiment reports (maths / FR / conjugation / CP).
report:
	PYTHONPATH=src:experiments $(PYTHON) experiments/generate_report.py

# Run the brain as a container service and smoke-test it over HTTP.
demo-docker:
	docker compose up --build -d
	@echo "waiting for health..."; sleep 5
	./scripts/smoke_test.sh
