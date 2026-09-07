"""`ExposureAggregate`: the published unit, and the only one. `docs/METHOD.md` E8.

`docs/ARCHITECTURE.md` calls the aggregation floor *"the seam that matters most in this
repository"*, and the reason it is a seam and not a habit is that the same pipeline that
flags injury risk also yields per-worker productivity surveillance. The floor is what
separates them.

The schema does most of the enforcing: `ExposureAggregate` has no field that can carry an
identifier, its validator rejects any string that looks like one anywhere in the record, and
`n_factories`, `n_workers` and the two dominance shares are required with no default. What
this module adds is the part a schema cannot do -- **computing the shares honestly and
refusing to build a record when they fail**, returning a suppression reason instead.

A stratum below the floor is **printed as suppressed, never omitted** (`docs/DECISIONS.md`
D019). An omitted row is indistinguishable from a row that was never computed; a suppressed
one tells a reader that a number exists and is being withheld, which is the honest shape of
this constraint.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Final, Literal

from cyclegraph.estimation.bootstrap import (
    BOOTSTRAP_B,
    BOOTSTRAP_SEED,
    cluster_bootstrap_ci,
    cluster_bootstrap_means,
    composite_cluster_ids,
    design_effect,
    iid_bootstrap_ci,
)
from cyclegraph.models import (
    K_FACTORIES_FLOOR,
    K_WORKERS_FLOOR,
    MAX_FACTORY_SHARE,
    ExposureAggregate,
    LabelSource,
    Mapping,
    Stratum,
)

DESIGN_EFFECT_MC_BAND: Final[float] = 0.05
"""The design effect is computed from the two intervals it is compared against, so it agrees
with them exactly; this band is the Monte Carlo slack a reader should allow at B = 10,000, not
a tolerance this module needs."""

QUANTILES: Final[tuple[int, ...]] = (10, 50, 90)


@dataclass(frozen=True, slots=True)
class ClipObservation:
    """One clip's HAL and the two identifiers that make it non-independent."""

    factory_id: str
    worker_id: str
    hal: float


@dataclass(frozen=True, slots=True)
class VarianceComponents:
    """H4: is exposure set by how a site is organised, or by the individual?"""

    between_factory: float
    between_worker_within_factory: float
    n_factories: int
    n_workers: int
    n_factories_with_two_workers: int = 0
    """How many factories contributed any within-factory information at all. Zero means the
    denominator of H4's ratio was never measured, only defaulted."""

    @property
    def ratio(self) -> float:
        if self.between_worker_within_factory <= 0:
            return float("inf")
        return self.between_factory / self.between_worker_within_factory

    @property
    def evaluable(self) -> bool:
        """Whether H4's comparison was made against anything.

        It compares two variances as a **ratio**, so what has to exist is the *denominator*.
        Two ways it can be absent, and only the second was caught at first:

        - No factory contributed two workers, so `within` is an empty list and its mean
          defaults to 0.0. Nothing was measured.
        - Every factory that did contribute two workers found no variation between them, so
          `within` is a measured 0.0.

        Either way `ratio` short-circuits to infinity and H4 would be **confirmed by a zero
        denominator**. The first guard tested `between_factory > 0` instead -- the numerator --
        which let the second case through and, worse, reported a measured between-factory
        variance of zero as NOT EVALUABLE when it is a clean falsification: ratio 0.0 is at or
        below 1 and H4 is falsified, which the record should say (D064).
        """
        return (self.n_factories_with_two_workers > 0
                and self.between_worker_within_factory > 0.0)

    @property
    def holds(self) -> bool:
        """H4 is falsified if the ratio is at or below 1, and unsupported if never evaluated."""
        return self.evaluable and self.ratio > 1.0


def variance_components(observations: Sequence[ClipObservation]) -> VarianceComponents:
    """Between-factory variance against between-worker-within-factory variance.

    Computed over *worker* means rather than clips, so a worker with many clips does not
    weight the within-factory component by how much they were recorded -- which is a property
    of the corpus's sampling, not of the workforce.
    """
    by_factory: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for obs in observations:
        by_factory[obs.factory_id][obs.worker_id].append(obs.hal)
    if len(by_factory) < 2:
        raise ValueError("a between-factory component needs at least two factories")

    worker_means: dict[str, list[float]] = {
        factory: [statistics.fmean(v) for v in workers.values()]
        for factory, workers in by_factory.items()
    }
    factory_means = [statistics.fmean(means) for means in worker_means.values()]
    within = [statistics.variance(means) for means in worker_means.values() if len(means) > 1]
    return VarianceComponents(
        between_factory=statistics.variance(factory_means),
        between_worker_within_factory=statistics.fmean(within) if within else 0.0,
        n_factories=len(by_factory),
        n_workers=sum(len(w) for w in by_factory.values()),
        n_factories_with_two_workers=len(within),
    )


@dataclass(frozen=True, slots=True)
class FloorCheck:
    """What D019 asks of a stratum before it may be published."""

    n_clips: int
    n_factories: int
    n_workers: int
    max_factory_share_workers: float
    max_factory_share_clips: float

    @property
    def failures(self) -> tuple[str, ...]:
        out: list[str] = []
        if self.n_factories < K_FACTORIES_FLOOR:
            out.append(f"{self.n_factories} factories, floor is {K_FACTORIES_FLOOR}")
        if self.n_workers < K_WORKERS_FLOOR:
            out.append(f"{self.n_workers} workers, floor is {K_WORKERS_FLOOR}")
        if self.max_factory_share_workers > MAX_FACTORY_SHARE:
            out.append(f"one factory holds {self.max_factory_share_workers:.0%} of workers")
        if self.max_factory_share_clips > MAX_FACTORY_SHARE:
            out.append(f"one factory holds {self.max_factory_share_clips:.0%} of clips")
        return tuple(out)

    @property
    def clears(self) -> bool:
        return not self.failures


def floor_check(observations: Sequence[ClipObservation]) -> FloorCheck:
    """The dominance shares are computed here rather than asserted, because a stratum that
    one site dominates is re-identifiable even when the counts clear (D019, A13)."""
    if not observations:
        raise ValueError("a floor check over no clips is not a result")
    clips_by_factory: dict[str, int] = defaultdict(int)
    workers_by_factory: dict[str, set[str]] = defaultdict(set)
    for obs in observations:
        clips_by_factory[obs.factory_id] += 1
        workers_by_factory[obs.factory_id].add(obs.worker_id)
    n_workers = sum(len(w) for w in workers_by_factory.values())
    return FloorCheck(
        n_clips=len(observations),
        n_factories=len(clips_by_factory),
        n_workers=n_workers,
        max_factory_share_workers=max(len(w) for w in workers_by_factory.values()) / n_workers,
        max_factory_share_clips=max(clips_by_factory.values()) / len(observations),
    )


@dataclass(frozen=True, slots=True)
class StratumOutcome:
    """Either a publishable aggregate, or the reason there is not one.

    `suppressed_reason` is printed rather than the row being dropped: an omitted row is
    indistinguishable from one nobody computed.
    """

    stratum: Stratum
    aggregate: ExposureAggregate | None
    suppressed_reason: str | None

    @property
    def suppressed(self) -> bool:
        return self.aggregate is None


def build_aggregate(
    observations: Sequence[ClipObservation],
    *,
    stratum: Stratum,
    stratum_definition: str,
    mapping: Mapping,
    label_source: LabelSource,
    corpus_rev: str,
    generated: datetime,
    weighting: Literal["worker", "clip"] = "clip",
    aggregate_id: str | None = None,
    seed: int = BOOTSTRAP_SEED,
    b: int = BOOTSTRAP_B,
) -> StratumOutcome:
    """Assemble one publishable row, or suppress it and say why."""
    if b != BOOTSTRAP_B:
        raise ValueError(
            f"B is pre-registered at {BOOTSTRAP_B} and the record's schema fixes it there; "
            f"a different B is a different pre-registration"
        )
    check = floor_check(observations)
    if not check.clears:
        return StratumOutcome(stratum=stratum, aggregate=None,
                              suppressed_reason="; ".join(check.failures))

    values = [o.hal for o in observations]
    clusters = composite_cluster_ids([o.factory_id for o in observations],
                                     [o.worker_id for o in observations])
    clustered = cluster_bootstrap_ci(values, clusters, B=b, seed=seed)
    iid = iid_bootstrap_ci(values, B=b, seed=seed)
    effect = design_effect(clustered, iid)
    mean = statistics.fmean(values)

    return StratumOutcome(
        stratum=stratum,
        suppressed_reason=None,
        aggregate=ExposureAggregate(
            aggregate_id=aggregate_id or f"{stratum.replace('_', '-')}-v1",
            stratum=stratum,
            stratum_definition=stratum_definition,
            n_clips=check.n_clips,
            n_workers=check.n_workers,
            n_factories=check.n_factories,
            max_factory_share_workers=check.max_factory_share_workers,
            max_factory_share_clips=check.max_factory_share_clips,
            mapping=mapping,
            label_source=label_source,
            hal_mean=mean,
            hal_ci95=[clustered.lo, clustered.hi],
            hal_quantiles={f"p{q}": _percentile(values, q) for q in QUANTILES},
            cluster_unit="factory_id/worker_id",
            weighting=weighting,
            design_effect=effect.variance_ratio,
            design_effect_width_ratio=effect.width_ratio,
            design_effect_mc_band=DESIGN_EFFECT_MC_BAND,
            bootstrap_b=10_000,
            seed=seed,
            iid_ci95_for_contrast=[iid.lo, iid.hi],
            aggregation_reason=(
                f"stratum clears the D019 floor: {check.n_factories} factories, "
                f"{check.n_workers} workers, no site above {MAX_FACTORY_SHARE:.0%}"
            ),
            corpus_rev=corpus_rev,
            generated=generated,
        ),
    )


def _percentile(values: Sequence[float], q: int) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (q / 100.0) * (len(ordered) - 1)
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def size_terciles(observations: Sequence[ClipObservation]) -> dict[str, Stratum]:
    """Factory-size terciles by worker count -- the only strata v1 defines (D019).

    Sector strata are deliberately absent: the release carries no sector field, and a sector
    with five public clients would name five companies.
    """
    workers: dict[str, set[str]] = defaultdict(set)
    for obs in observations:
        workers[obs.factory_id].add(obs.worker_id)
    ordered = sorted(workers, key=lambda f: (len(workers[f]), f))
    third = max(len(ordered) // 3, 1)
    out: dict[str, Stratum] = {}
    for i, factory in enumerate(ordered):
        if i < third:
            out[factory] = "size_tercile_1"
        elif i < 2 * third:
            out[factory] = "size_tercile_2"
        else:
            out[factory] = "size_tercile_3"
    return out


def replicate_means(observations: Sequence[ClipObservation], *, seed: int = BOOTSTRAP_SEED,
                    b: int = BOOTSTRAP_B) -> list[float]:
    """The B replicate means, so every published interval is reproducible from the release
    without shipping a grouping key (`docs/DATASET_CARD.md`)."""
    clusters = composite_cluster_ids([o.factory_id for o in observations],
                                     [o.worker_id for o in observations])
    return [float(m) for m in cluster_bootstrap_means([o.hal for o in observations],
                                                      clusters, B=b, seed=seed)]
