# Decisions

Append-only. Each entry: the decision, its reason, and what would reverse it. Entries are
never edited; a change is a later entry naming what it supersedes.

Seeded 2026-09-05 from the scoping session that created this repository.

## D001 — Documentation before code

`docs/PRE-REGISTRATION.md`, `docs/RUBRIC.md` and `CONTRACTS.md` freeze before `src/` exists.
The project's argument is that a measurement was published without a stated protocol.
Improvising this one would be self-refuting, and git history is the only evidence of
ordering that cannot be reconstructed after the fact.

**Reverses if:** nothing.

## D002 — Repository named `cyclegraph`

Frank Gilbreth's c.1913 instrument: a small lamp fixed to a worker's hand, photographed at
long exposure, the developed plate showing the path of one work cycle. This is the same
measurement from the hand's own point of view, a century later and at 10,000 hours.
Consistent with the sibling naming line — `vernier`, `assay`, `plumb`, `titer`, `sonar` —
where the name is the instrument the project is.

**Reverses if:** nothing.

## D003 — HAL is the index; RULA and REBA are not

**Decision.** The Hand Activity Level axis of the ACGIH TLV is the index. RULA and REBA are
not used.

**Rationale.** RULA and REBA score trunk, neck, legs and upper arm. A head-mounted camera
never sees a trunk. Every published video-ergonomics system is third-person for this reason,
and building on RULA/REBA from an egocentric viewpoint would be building on an ill-posed
foundation. HAL, the Strain Index and OCRA are hand-and-wrist instruments designed for
repetitive manufacturing work and score what this viewpoint does see.

**Evidence.** `docs/COVERAGE.md` maps every input of the TLV and of the Strain Index against
what is observable here. `docs/SURVEY.md` records the third-person finding; it is `[S]` and
gates the project until opened.

**Alternatives rejected.** RULA/REBA on the observable distal subset — a partial score
against a whole-body scale is not interpretable. A new video-native index — invites "why
should I believe your index" and forfeits decades of occupational-health validation.

**Reverses if:** egocentric whole-body pose estimation becomes reliable enough on fisheye
imagery that the proximal segments RULA/REBA need are recoverable. The camera motion carries
some trunk information in principle; nothing here depends on that.

## D004 — Unobservable inputs are reported absent, never estimated

Peak force cannot be read from video. It is recorded `null` with a reason string, and the
TLV is never evaluated.

An imputed force would look plausible, propagate into every downstream number, and be wrong
by an offset no internal check could detect — while converting a gap a reader can see into
an error they cannot.

**Reverses if:** nothing. An instrumented subset with measured force would be a different
study, not an amendment to this one.

## D005 — Spectral frequency is primary; transition-counting is the cross-check

**Decision.** Exertion frequency is estimated spectrally from the manipulation series.
Transition-counting runs on the same clips as a cross-check and is the subject of H2.

**Rationale.** Counting exertions requires deciding where one ends and the next begins,
which is where label noise concentrates and where an arbitrary debounce threshold silently
sets the answer. Spectral estimation never locates a boundary. Cyclic work has a dominant
frequency; recovering it is a well-posed signal problem rather than an annotation problem.

**Evidence.** `docs/RUBRIC.md` fixes the debounce at 0.5 s and records it on every segment,
precisely because the count is a function of it.

**Alternatives rejected.** A learned temporal segmenter — needs labels this project does not
have. Duty cycle only, no frequency — HAL needs both, and duty cycle alone cannot
distinguish slow heavy work from fast light work.

**Reverses if:** H2 fails and the disagreement traces to the spectral side.

## D006 — Corpus-level reporting only; worker *and* factory are variance units

Both identifiers are load-bearing for interval estimation and appear in no published number.
This goes further than `../vernier/docs/ETHICS.md`, which protects individuals but reports
nothing at site level either way.

Factory-level aggregation would expose sites: a finding about an identifiable workplace
whose operators never participated, where the people carrying the consequences are the
workers there. 85 sites with published client sectors are not meaningfully anonymous.

Enforced in `CONTRACTS.md` — `ExposureAggregate` has no field able to carry an identifier —
rather than by convention, because a rule enforced by intention survives as long as
attention does.

**Reverses if:** nothing, at this consent basis. A study run with the participation of the
sites concerned would be a different study with a different document.

## D007 — A new ethics basis, not an extension of `vernier`'s

`../vernier/docs/ETHICS.md` explicitly disclaims claims about labour practice. cyclegraph
makes one. Widening that document to cover this work would damage the credibility of both;
`docs/ETHICS.md` states its own basis and is narrower in what it permits.

**Reverses if:** nothing.

## D008 — Self-documented ethics, no external review, and that is a disclosed weakness

**Decision.** The ethics basis is self-documented. No IRB or equivalent review is sought
before v1.

**Rationale.** No institutional affiliation is available to route a review through, and the
alternative — proceeding while claiming review is forthcoming — would be worse than
proceeding while saying plainly that there is none.

**Evidence.** The aggregation floor is enforced schema-side rather than by policy, which is
the strongest mitigation available without a reviewer.

**Alternatives rejected.** Seeking review first — weeks, and it needs an affiliation.
Proceeding silently — the failure mode this repository exists to criticise.

**Reverses if:** an affiliation becomes available, or any finding moves toward a
site-identifiable claim. The second is a hard trigger, not a preference.

## D009 — No expert anchor, and the claim is downgraded to match

**Decision.** No certified ergonomist scores a sample. v1 does not claim to measure HAL
accurately.

**Rationale.** None is available. The honest consequence is a downgrade, not a
reinterpretation of what the remaining evidence shows: internal consistency and literature
plausibility are not validation, and the README says so above the fold rather than in a
limitations section.

**Evidence.** H3 is labelled a plausibility check wherever it appears. `docs/COVERAGE.md`
names the missing agreement statistic as the project's largest gap.

**Alternatives rejected.** Treating agreement with the vendor's own labels as validation —
that measures agreement with a judge whose 2-hands figure `vernier` found off by ~6pp.
Self-rating by the author — not an independent context, and not a qualification.

**Reverses if:** an ergonomist becomes available. `docs/RUBRIC.md` fixes the protocol in
advance so the result would be reportable whatever it said.

## D010 — Analysis rate is 4 Hz

Nyquist is then 2 Hz, or 120 exertions per minute, spanning the range the HAL scale is
defined over. A lower rate would alias fast repetitive work into a plausible slow frequency,
and the aliasing would bias exposure *downward* — the direction that flatters the corpus,
which is the direction an unforced error should never run.

**Reverses if:** H1's sampling-rate bound fails between 4 Hz and 8 Hz, which would mean 4 Hz
is already too coarse for duty cycle, not only for frequency.

## D011 — The raw release only; the evaluation release cannot support this

`builddotai/Egocentric-10K-Evaluation`'s `frame_id` is a bare UUID carrying no factory,
worker, clip or timestamp (`../vernier/docs/UPSTREAM-FINDINGS.md`). No clip can be
reconstructed from it and no duty cycle computed. The raw corpus is 19,495 h265 WebDataset
shards, reachable a frame at a time over HTTP range requests via ffmpeg's `subfile`
protocol, established in `../vernier/docs/DECISIONS.md`.

**Reverses if:** a release ships clip-linked frame identifiers.

## D012 — One factory end to end before any stratified draw

The pilot is every clip in a single factory, fixed as the first in the pinned revision's
sorted manifest rather than chosen after inspection. It exercises decode, labelling, duty
cycle, spectral frequency and aggregation at a scale that can be inspected by eye. The
stratified draw follows only if the pilot's gates pass.

**Reverses if:** the pilot factory turns out to be degenerate — a single task, or too few
workers to estimate a design effect. That would be a documented re-draw with the reason, not
a silent one.
