# What is blocked, by what, and what it costs

Written 2026-09-07, after the pilot closed. `docs/HANDOFF.md` says what to do next; this says
what stops it, in the only three categories that matter: **money**, **a human step**, and
**nothing will ever unblock this**. Conflating them is how a project talks itself into believing
it is one grant away from a result it can never have.

Every cost below is derived from a rate this project measured, and the derivation is shown so a
reader can disagree with it. Where a figure is an estimate rather than a measurement it says so.

## The short version

| | Blocked by | Cost | Who unblocks it |
|---|---|---|---|
| **H1a** — duty cycle across label sources | money, and a design question | ~$5 reduced, ~$9 as specified | you, with a caveat below |
| **Ego4D control** (NC-dc) | **a licence acceptance, not money** | ~$8, est. | **you, in a browser, today** |
| **EPIC control** (NC-f) | an institutional email address | — | nobody here |
| **H3, H4, H5** | the main draw, below | — | follows the draw |
| **Main draw, Arm A** | money | **~$2,800** | out of reach |
| **Main draw, Arm B** | money | **~$82** | a modest top-up |
| **Expert validation** | nothing will unblock it | — | nobody |

## What is *not* blocked, stated first because it is the thing most easily missed

**The Ego4D negative control needs a licence acceptance, not a budget.** `docs/METHOD.md` E7
puts its cost at "small", no sample size is pre-registered for it, and the labeller runs free on
a laptop (`docs/DECISIONS.md` D061's measured 45–67 frames/s on MPS). The detector and flow
stages are the only paid parts, and at the pilot's measured rates a control of the pilot's own
size is **roughly $8** — 4.4 GPU-hours for the detector at the measured 30 frames/s across three
workers, plus about an hour of CPU for the flow. *Estimate, not a measurement: no Ego4D clip has
been decoded.*

`docs/WAVES.md` requires the negative control **before H3**, so this is not optional work that
was deferred — it is the next gate in sequence, and it is the cheapest remaining thing that
answers a pre-registered question. It is blocked on a human accepting Ego4D's terms.

## Blocked on money

### The main draw — the real wall

H1a's outcome selects the arm; both are priced from this pilot's measured rates.

**Arm A** (H1a holds): 40,000 clips, probe labels. At the pilot's 4,767 samples per clip that is
~190M frames.
- Detector: 190M ÷ 30 frames/s = ~1,765 GPU-hours × $1.212 ≈ **$2,140**
- Flow/signal: 190M × 0.84 usable ÷ 90 pairs/s = ~492 CPU-hours × $1.428 ≈ **$700**
- Labeller: free, but ~40 days of laptop wall-clock at the measured rate
- **≈ $2,840**

**Arm B** (H1a fails): 200 clips, judge-only, ≈953k frames.
- Judge: ≈**$68** at the sibling's paid rate (`docs/METHOD.md` E3, a real invoice)
- Detector ≈ 8.8 GPU-hours ≈ $11; signal ≈ 2.5 hours ≈ $4
- **≈ $82**

The asymmetry is the point: **failing H1a is 35× cheaper to act on than passing it.** That is
not a reason to want it to fail, and the pre-registration fixed both targets before either was
measurable precisely so that this asymmetry could not influence anything.

### H1a itself — and why cheap may be worse than nothing

The judge is a second, independent label source. The probe's own fidelity is **0.6933 against a
pre-registered ≥0.90**, and H1 exists because a labeller can be stable and wrong — H1b holding
(D069) shows duty cycle is stable across sampling rates and says nothing about whether it is
right.

At the full 4 Hz rate, $5 buys about **two clips**, and a mean absolute difference over two
pairs is not a result. The design that fits is ~30 stratified clips with **both** sources scored
on the *same* subsampled instants, which removes the rate confound entirely.

**The caveat that money does not fix.** H1a assumes the judge is the better source. Weaken it
enough to fit a budget and agreement means "two weak labellers are wrong in similar ways", while
disagreement diagnoses nothing. A cheap H1a can consume the budget and leave H1 exactly as open
as it is now, having also spent the one chance to ask the question cleanly.

`docs/REPRODUCTION.md` permits any OpenAI-compatible endpoint, so a self-hosted VLM on AWS is a
stronger judge for money already allocated. That is the option this document recommends
considering before the API one.

## Blocked on a human step, not money

- **Ego4D** — accept the licence. Then it is ~$8 and it is the next pre-registered gate.
- **EPIC-KITCHENS-100** — requires an institutional email address, recorded unmet in
  `../vernier/docs/COVERAGE.md`. If it stays unmet the frequency control is reported `UNTESTED`
  **in those words**, and `docs/RED-TEAM.md` A4 and A11 stay OPEN. This is a disclosure, not a
  workaround.

## Blocked permanently — no budget changes these

These are in `docs/COVERAGE.md` and are repeated here so that a reader costing the project does
not mistake them for line items.

- **No ergonomist has scored anything.** There is no agreement statistic against a human expert,
  and everything this project reports is internal consistency or literature comparison. COVERAGE
  calls this the largest gap and it is not a funding problem.
- **Peak force is unobservable from video**, so the TLV is never evaluable and `force_axis` is
  structurally absent from every record.
- **The box-convention offset against the pre-registered detector cannot be measured**, because
  100DOH's weights cannot be obtained by anyone (D037). It is bounded to about ±6% by the
  hand-breadth sensitivity rows and no further (D047).
- **The speed path collapses above ~900 mm/s** against an equation fitted to 1288 mm/s, for both
  estimators, at four decode resolutions and five parameter settings (D044, D050, D059). This is
  a property of dense optical flow with a smoothness prior, not a tuning failure.

## What the pilot already settled, so it is not re-bought

H2a **FAILED**, H2b and H2c **HOLD**, H1b **HOLDS**, H2 **FAILED** as their conjunction. The
corpus aggregate is **SUPPRESSED** by D019's k-anonymity floor — one factory against a floor of
five — which is why H3, H4 and H5 are not answerable here at any price and are listed above under
the draw rather than under money.
