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

## Tally

Attacks recorded: 9. Landed: 3 (A2, A6, A8 — all by construction, all disclosed in the
README). Open: 5. Mitigated: 1.
