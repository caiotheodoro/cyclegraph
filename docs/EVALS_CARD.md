# Evals card

What is evaluated, how, and what the evaluation cannot tell you. The structure is fixed at
W0 so results land in a decided shape; v1.1.0 added rows, none was removed.

## The evaluations

| Eval | What it measures | Ground truth | Runs at |
|---|---|---|---|
| H1a | Duty cycle across label sources | None — agreement between two unvalidated sources | W4 |
| H1b | Duty cycle across sampling rates | None — self-consistency | W4 |
| H2a | Spectral bout frequency vs. transition counting | None — two estimators on one signal | W5 |
| H2b | Spectral resolvable fraction | Definitional | W5 |
| H2c | Hand-box coverage and flow-null rate on the speed path | Definitional | W5 |
| NC-dc | Factory vs. Ego4D, duty-cycle gap and HAL gap | None — a contrast | W6 |
| NC-f | Factory vs. EPIC-KITCHENS-100, speed-path HAL gap | None — a contrast; the A4/A11 test | W6 |
| H3 | Median HAL inside [2.4, 6.2] | External, a cohort mean ± SD rather than a label | W7 |
| H4 | Variance decomposition | Definitional; `UNTESTED` under Arm B | W7 |
| H5 | Design effect ≥ 1.2 | Definitional; `UNTESTED` under Arm B | W7 |
| A14 | Rotation-only and translation-only synthetics, static hand | Synthetic, exact | W3 |

## Read the ground-truth column

**Eight of eleven evaluations have no ground truth.** They are consistency checks or
contrasts. An instrument can be perfectly self-consistent and perfectly wrong, and every one
of these would pass in that case.

The ones that reach outside are H3, which compares against a cohort distribution and is
plausibility rather than agreement; the two negative controls, which establish contrasts
rather than labels; and A14, which has an exact answer because it is synthetic.

This is the honest shape of an evaluation suite built without an expert anchor
(`docs/DECISIONS.md` D009), and it is stated here rather than inferred from the table.

## What would change it

One evaluation, not currently possible: a certified ergonomist scores a stratified sample of
whole clips on HAL, blind to the pipeline's output, on a sample drawn before any score is
seen. `docs/RUBRIC.md` fixes that protocol in advance precisely so the result would be
reportable whatever it said.

The best published third-person system reports a cross-domain RMSE of 0.74 HAL points
against observers (`docs/SURVEY.md` S2). That is the honest prior for how far this port
could be off, and nothing here measures it.

## Golden-case requirement

Every statistical unit ships at least one test with a hand-computable expected answer:

- the two HAL equations against Radwin 2015 Table 3 cells, within the paper's residual;
- the bootstrap against synthetic clustered data with a known design effect, within ±10%;
- the duty-cycle estimator against a series whose mean is known by construction;
- the spectral estimator against a synthetic signal of known frequency;
- the speed estimator against a rotation-only synthetic with a static hand (zero residual)
  and a translation-only synthetic whose residual is published as the path's floor.

`pytest` passing is not sufficient acceptance for these units on its own. `docs/WAVES.md`
carries the review rubric.
