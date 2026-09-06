# Red team

**Opened before any result exists.** That is deliberate: attacks written after the fact are
selected for being survivable. Everything below is an attack on cyclegraph's own findings,
recorded now, to be answered with evidence later — and published unedited when the answer is
bad.

Sibling precedent sets the expectation. `assay` turned its instruments on itself and twelve
of its published claims broke. Expect breakage here.

**Status** is one of **LIVE** (a real weakness carried), **MITIGATED** (with the mechanism
named), or **OPEN** (not yet known). **Severity** is pre-committed: *fatal* invalidates the
headline; *major* forces a restatement; *minor* is a caveat.

`Outcome:` lines are appended after the relevant stage runs. They are never edited.

## A1. "Your ground truth is a judge that you know is wrong." · LIVE · major

`vernier` measured the same vendor's judge and found its 2-hands figure off by ~6pp against
the published value on two separate releases. cyclegraph's duty cycle is built on that
judge's manipulation label.

**Response.** The manipulation figure is the one that *did* reproduce within tolerance in
that project — 92.14% observed against 92.76% published. That is favourable and it is not
exoneration: reproducing a published number means the pipeline agrees with itself, not that
the label is correct. H1 tests whether duty cycle is stable across label sources, which
bounds the labeller's contribution without validating it. **The weakness is carried and
named**; nothing here converts an unvalidated label into a validated one.

*Landed if* H1's cross-source bound is exceeded.

## A2. "No ergonomist ever looked at this, so the numbers mean nothing." · LIVE · fatal to the strong claim

**Response.** Conceded, and the claim is downgraded rather than defended. v1 does not assert
that it measures HAL accurately; `README.md` says so above the fold and
`docs/COVERAGE.md` names it as the project's largest gap. What survives is the argument, the
instrument, the distribution, and internal consistency. If a reader concludes the project
cannot support an occupational-health finding, they have read it correctly.

*Landed already, by construction.* The response is scope, not rebuttal.

## A3. "Duty cycle is not the vendor's metric — you are equivocating on a word." · OPEN · fatal

The vendor's *active manipulation* is a per-frame binary about whether hands are working on
a workpiece. Duty cycle in the TLV is the fraction of a cycle spent in exertion. These may
not be the same construct: an exertion has a force component that "visibly manipulating"
does not, and idle grip is manipulation-shaped but not exertion.

**Response.** This is the sharpest attack on the project and it is unresolved. The rubric's
treatment of idle grip in the vendor's own prompt lineage is the place to look
(`../vernier/docs/RUBRIC.md` treats idle grip as `false`, which helps). But the mapping is
an argument, not a measurement, and if it fails the whole project fails.

*Landed if* S2 or S3 shows the TLV's duty cycle is defined in a way the vendor's label
cannot express.

## A4. "Your spectrum is finding the camera's motion, not the hands." · OPEN · major

Head-mounted cameras bob with gait and with the work itself. A dominant frequency in a
head-worn signal may be the body, not the hands.

**Response.** The negative control is aimed squarely at this: a non-repetitive egocentric
corpus has head motion too, so if the pipeline responds to head bob rather than hand
repetition, factory and kitchen medians will not separate by the pre-registered 1.0. That is
a real test and it is pre-registered.

*Landed if* the negative control fails.

## A5. "Excluding unresolvable clips is where your effect comes from." · OPEN · major

Clips with no dominant cycle are excluded. If non-repetitive work is systematically
excluded, the surviving distribution is repetitive by construction and any finding about
repetition is circular.

**Response.** The exclusion rate is a reported quantity, not a footnote — H2's second bound
requires ≥70% resolvable and would fail loudly if most clips dropped. The alternative
(assigning zero) is worse and `docs/RUBRIC.md` says why. **This remains a real
selection effect** and the reported distribution is conditional on resolvability, which
every statement of it must carry.

*Landed if* the resolvable fraction is below 70%, or if resolvability correlates with
factory.

## A6. "Aggregate-only reporting makes the work useless to the people it claims to protect." · LIVE · major

A site with a genuine exposure problem cannot be told it has one.

**Response.** Conceded and accepted as a cost, with the reason stated in `docs/ETHICS.md`
rather than left implicit. The trade is real: identifiability is the mechanism by which a
finding becomes actionable *and* the mechanism by which it becomes harmful to the people
recorded. Without site participation, this project takes the conservative side.

*Landed already.* Recorded so nobody has to discover it.

## A7. "You published a pre-registration and then chose thresholds you knew you would clear." · OPEN · major

**Response.** The thresholds are in git before any clip is decoded and the file is hashed.
That proves ordering, not disinterestedness — nothing prevents a threshold set
conservatively on the basis of intuition about what would pass. The honest containment is
that H2's second bound (≥70% resolvable) and the negative control are both set where failure
is genuinely plausible, and that a failed hypothesis is reported as failed.

*Landed if* every hypothesis passes comfortably, which would itself be evidence the
thresholds were slack.

## A8. "This is a surveillance tool with a paper attached." · LIVE · fatal to the framing

**Response.** The pipeline does compute a per-worker productivity signal; `docs/ETHICS.md`
names that in those words rather than waiting to be asked. The mitigation is that the
aggregation floor is enforced in the schema — `ExposureAggregate` has no field able to carry
an identifier — and that this repository publishes nothing at an identifiable unit. What it
cannot mitigate is that anyone with the corpus and this method can compute the per-worker
number themselves. That is stated, not hidden.

*Landed if* any published artifact carries a worker or factory identifier.

## A9. "The conflict of interest shaped the finding." · MITIGATED · minor

The author has an interest in this work being noticed.

**Response.** Hypotheses, thresholds and stopping rules freeze before any data is seen, and
the freeze is hashed. Containment is structural rather than dispositional. Its limit: the
choice of *which* hypotheses to pre-register is itself a judgement made in advance of, and
in anticipation of, publication — pre-registration bounds analytic flexibility, not framing.

## A10. "Your frequency is bout frequency, not exertion frequency." · MITIGATED · fatal to the spectral axis

The manipulation series goes `true` when hands are working on a workpiece and stays `true`
across consecutive exertions. Ten screw turns are one bout and ten TLV exertions. A spectral
peak over that series recovers bouts, and HAL from bout frequency is a systematic
under-statement — in the direction that flatters the corpus.

**Response.** Conceded before any data. `docs/DECISIONS.md` D014 demotes the spectral path
to a cross-check reported as a lower bound and makes the speed–duty-cycle path primary,
which is the input the ACGIH table's own authors chose when they automated HAL. Every
`FrequencyEstimate` says what `hz` is. What the mitigation does not do is make bout
frequency into exertion frequency; nothing can, without exertion-level labels.

*Landed if* the speed path fails its pre-registered coverage or control (D014) and the
spectral path becomes primary — at which point every HAL is a lower bound and is published
as one.

## A11. "Hand speed in image space is camera speed." · OPEN · major

A head-mounted camera moves. Flow inside the hand box is hand motion plus camera motion.

**Response.** Ego-motion is estimated from the complement of the hand mask and subtracted
(`CONTRACTS.md` `HandSpeedEstimate.ego_motion`). The EPIC-KITCHENS frequency control (D016)
is the test: kitchens have head motion too, and if the speed path cannot separate factory
from kitchen by 0.5 HAL, it is measuring the head.

*Landed if* the frequency control fails on the speed path.

## A12. "A 92%-saturated binary series has no spectral peak; H2b fails by construction." · OPEN · major

At ~0.92 manipulation prevalence the series is almost all ones with short gaps. Its
spectrum is dominated by low-frequency content and the `6×` peak floor may rarely clear.

**Response.** That is what H2b measures, and it is why the speed path does not depend on
resolvability at all (D014). If H2b fails, the spectral cross-check is reported as failed
and the speed path carries HAL alone, with A10's lower-bound cross-check unavailable — a
real loss, stated.

*Landed if* spectral resolvability is below 70% on the pilot.

## A13. "A stratum with five factories re-identifies a site." · MITIGATED · major

**Response.** D019: ≥ 5 factories, ≥ 50 workers, no factory above 40% of the stratum's
workers or clips, worker-weighted estimates, one `corpus_rev` per release with prior strata
withdrawn on re-pin so no two published aggregates differ by fewer than the floor, and
pilot values never published because the pilot factory is nameable. Only size terciles are
defined; sector strata were dropped because the metadata carries no sector and a sector of
five public clients names five companies. What the mitigation cannot do: anyone with the
corpus can compute the per-factory number themselves. That is A8, restated.

*Landed if* any published aggregate can be shown to bound a single factory's value to
within the corpus interquartile range.

## A14. "Parallax and radial rotational flow on a fisheye leave residual where the hands sit." · OPEN · major

Camera rotation on a wide lens produces flow that is not uniform across the image; camera
translation produces more flow on near objects — the hands — than on the background the
ego-motion estimate is taken from. A scalar subtraction leaves a residual that reads as
hand speed. Rolling shutter adds to it.

**Response.** The synthetic golden test in `docs/WAVES.md`'s checklist, widened by D021 to
both mechanisms: a rotation-only sequence under the corpus's own fisheye leaves residual that
a scalar ego-motion estimate cannot cancel, and is measured; a translation-only sequence with
a static hand at typical working distance is measured too. The floor is the pair, not the
translation term alone. If the floor is a material fraction
of observed factory speeds, the speed path is reported with that floor subtracted and the
subtraction disclosed.

*Landed if* the residual floor exceeds **0.25 HAL** at the corpus median RMS speed
(`docs/PRE-REGISTRATION.md` v1.3.0, `docs/DECISIONS.md` D021; the earlier 20%-of-speed
bound was ~5x looser and is superseded).

## A15. "Flow failure reads as zero speed — the flattering direction." · MITIGATED · major

Motion blur, low light and rolling shutter make dense flow fail quietly toward zero.

**Response.** A flow failure is `null` with a reason, never zero; the null rate is a
reported quantity on every `HandSpeedEstimate`, and above 10% the clip is
`status: "flow_failed"` and contributes no speed (`CONTRACTS.md`). H2c pre-registers the
10% bound.

*Landed if* the corpus null rate exceeds 10%, in which case the speed path is conditional on
flow success and every statement of it must carry that.

## Tally

Attacks recorded: 15. Landed: 3 (A2, A6, A8 — all by construction, all disclosed in the
README). Open: 7 (A3, A4, A5, A7, A11, A12, A14). Mitigated: 5 (A9, A10, A13, A15, and A3
partially — the TLV's own definition of exertion is "handling an object", which is the
vendor's construct; A3 stays OPEN until the pilot's labels are read against that sentence).
