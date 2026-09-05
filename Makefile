# cyclegraph -- targets are the table of contents.
#
# Stages that are not written yet are targets that fail loudly. A stage that
# silently no-ops is how a pipeline comes to look finished before it is.

NOT_YET = @echo "not yet implemented -- see docs/HANDOFF.md for the wave that lands this" >&2 && exit 1

.PHONY: help validate privacy-gate check-placeholders check-claims test typecheck lock \
        survey manifest signal cycles hal estimate card

help:  ## This list.
	grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) | sed 's/:.*## /\t/'

# --- gates -------------------------------------------------------------------

validate: privacy-gate check-placeholders check-claims test typecheck  ## All gates. The exit condition for every wave.

privacy-gate:  ## Fail loudly if anything under docs/private/ is stageable.
	@if git add -A --dry-run 2>/dev/null | grep -q 'docs/private'; then \
		echo "REFUSING: docs/private/ is stageable. Fix .gitignore before committing."; \
		exit 1; \
	else \
		echo "privacy-gate: docs/private/ is not stageable."; \
	fi

check-placeholders:  ## No placeholder tokens in tracked files. Unknowns are named open questions with a resolving trigger.
	@# This Makefile and scripts/validate.py contain the token list by construction -- they are
	@# where it is defined. Excluding those two is not a loophole; a third exclusion would be,
	@# and keeping the list here is what makes that visible.
	@if git ls-files -z | xargs -0 grep -nE '\b(TBD|TODO|FIXME|XXX)\b' 2>/dev/null \
		| grep -vE '^(Makefile|scripts/validate\.py):'; then \
		echo "REFUSING: placeholder found. Name the open question and its resolving trigger instead."; \
		exit 1; \
	else \
		echo "check-placeholders: none."; \
	fi

check-claims:  ## Every cited path resolves, the spine is present, the pre-registration matches its hash.
	python3 scripts/validate.py

test:  ## Offline test suite. No network.
	python3 -m pytest tests -q

typecheck:  ## mypy --strict over tests and scripts, and over src once it exists.
	@# src/ is empty at W0 by design. mypy errors on a directory with no .py files, and here
	@# that error would mean the ordering rule is being followed -- not a failure.
	@if ls src/cyclegraph/*.py >/dev/null 2>&1; then \
		echo "typecheck: including src/"; \
		python3 -m mypy --strict src tests scripts; \
	else \
		echo "typecheck: src/ is empty (W0); checking tests and scripts"; \
		python3 -m mypy --strict tests scripts; \
	fi

lock:  ## Regenerate constraints from pyproject.
	uv pip compile --all-extras --universal --python-version 3.11 -o constraints.txt pyproject.toml

# --- stages, in the order docs/WAVES.md fixes ---------------------------------

survey:  ## docs/SURVEY.md -- the novelty gate. Ran 2026-09-05 and cleared, narrowly.
	@grep -q '^## Verdict:' docs/SURVEY.md \
		&& echo "survey: verdict recorded in docs/SURVEY.md (W1 cleared 2026-09-05)" \
		|| { echo "REFUSING: docs/SURVEY.md carries no verdict line." >&2; exit 1; }

manifest:  ## Clip manifest for one factory. Usage: make manifest FACTORY=factory_001
ifndef FACTORY
	$(error FACTORY is required, e.g. make manifest FACTORY=factory_001)
endif
	python3 scripts/build_clip_manifest.py --factory $(FACTORY)

signal:  ## Per-frame manipulation series and hand speed for each clip in the manifest.
	@# Refuses without the detector and labeller outputs; see docs/HANDOFF.md "the next three
	@# things". A stage that substituted a region prior for a detector would satisfy every
	@# schema and mean nothing.
	python3 scripts/build_signal.py \
		--detections results/pilot/detections.jsonl \
		--labels results/pilot/labels.jsonl

cycles:  ## Frequency axis: hand speed primary, spectral bout frequency and transition-counting as cross-checks.
	python3 scripts/estimate_frequency.py --labels results/pilot/labels.jsonl

hal:  ## Duty cycle and the Hand Activity Level axis, by the published equations (docs/DECISIONS.md D013).
	$(NOT_YET)

estimate:  ## Cluster bootstrap over factory_id/worker_id, with the design effect beside it.
	$(NOT_YET)

card:  ## Regenerate MEASUREMENT_CARD.json. Exits nonzero unless the verdict is VERIFIED.
	$(NOT_YET)
