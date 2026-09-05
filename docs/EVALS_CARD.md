# Evals card

What is evaluated, how, and what the evaluation cannot tell you.

**No evaluation has run.** The structure is fixed at W0 so results land in a decided shape.

## The evaluations

| Eval | What it measures | Ground truth | Runs at |
|---|---|---|---|
| H1a | Duty cycle across label sources | None — agreement between two unvalidated sources | W4 |
| H1b | Duty cycle across sampling rates | None — self-consistency | W4 |
| H2a | Spectral vs. transition frequency | None — agreement between two estimators on the same signal | W5 |
| H2b | Resolvable fraction | Definitional | W5 |
| NC | Factory vs. non-repetitive corpus | None — a contrast, not a label | W6 |
| H3 | Distribution vs. published HAL | External, but a range rather than a label | W7 |
| H4 | Variance decomposition | Definitional | W7 |
| H5 | Design effect | Definitional | W7 |

## Read the ground-truth column

**Six of eight evaluations have no ground truth.** They are consistency checks. An instrument
can be perfectly self-consistent and perfectly wrong, and every one of these would pass in
that case.

The two that reach outside are H3, which compares against a published range and is
plausibility rather than agreement, and the negative control, which establishes a contrast
rather than a label.

This is the honest shape of an evaluation suite built without an expert anchor
(`docs/DECISIONS.md` D009), and it is stated here rather than inferred from the table.

## What would change it

One evaluation, not currently possible: a certified ergonomist scores a stratified sample of
whole clips on HAL, blind to the pipeline's output, on a sample drawn before any score is
seen. `docs/RUBRIC.md` fixes that protocol in advance precisely so the result would be
reportable whatever it said.

Until it runs, no number in this project is validated against the construct it claims to
measure.

## Golden-case requirement

Every statistical unit ships at least one test with a hand-computable expected answer: the
spectral estimator against a synthetic signal of known frequency; the bootstrap against
synthetic clustered data with a known design effect; the duty-cycle estimator against a
series whose mean is known by construction. `pytest` passing is not sufficient acceptance
for these units on its own. `docs/WAVES.md` carries the review rubric.
