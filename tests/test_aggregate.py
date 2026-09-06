"""Tests for `src/cyclegraph/estimation/aggregate.py`.

The aggregation floor is the seam `docs/ARCHITECTURE.md` calls the one that would cause real
harm, so most of this file is about refusing to build a record rather than about building one.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cyclegraph.estimation.aggregate import (
    ClipObservation,
    build_aggregate,
    floor_check,
    replicate_means,
    size_terciles,
    variance_components,
)
from cyclegraph.models import K_FACTORIES_FLOOR, K_WORKERS_FLOOR, MAX_FACTORY_SHARE

GENERATED = datetime(2026, 9, 5, tzinfo=timezone.utc)
DEFINITION = "docs/DECISIONS.md#d019"


def _corpus(n_factories: int = 10, workers_per: int = 8, clips_per: int = 3,
            hal: float = 4.0) -> list[ClipObservation]:
    return [
        ClipObservation(factory_id=f"factory_{f:03d}", worker_id=f"worker_{w:03d}",
                        hal=hal + 0.1 * ((f + w) % 5))
        for f in range(1, n_factories + 1)
        for w in range(1, workers_per + 1)
        for _ in range(clips_per)
    ]


def _build(obs: list[ClipObservation], **kw: object):  # type: ignore[no-untyped-def]
    return build_aggregate(obs, stratum="corpus", stratum_definition=DEFINITION,
                           mapping="akkas-2015-speed-dc", label_source="probe",
                           corpus_rev="3e5f87c8", generated=GENERATED, **kw)  # type: ignore[arg-type]


def test_a_stratum_clearing_the_floor_produces_a_record() -> None:
    outcome = _build(_corpus())
    assert not outcome.suppressed and outcome.aggregate is not None
    agg = outcome.aggregate
    assert agg.n_factories == 10 and agg.n_workers == 80
    assert agg.cluster_unit == "factory_id/worker_id"
    assert agg.hal_ci95[0] <= agg.hal_mean <= agg.hal_ci95[1]


def test_too_few_factories_is_suppressed_with_a_reason_not_omitted() -> None:
    """An omitted row is indistinguishable from one nobody computed."""
    outcome = _build(_corpus(n_factories=4, workers_per=20))
    assert outcome.suppressed and outcome.aggregate is None
    assert outcome.suppressed_reason is not None
    assert "4 factories" in outcome.suppressed_reason


def test_too_few_workers_is_suppressed() -> None:
    outcome = _build(_corpus(n_factories=10, workers_per=4))
    assert outcome.suppressed
    assert outcome.suppressed_reason is not None and "workers" in outcome.suppressed_reason


def test_a_dominant_factory_is_suppressed_even_when_the_counts_clear() -> None:
    """A13. A stratum one site dominates is re-identifiable even at ten factories and a
    hundred workers, which is why the shares are a separate condition."""
    obs = _corpus(n_factories=10, workers_per=8)
    obs += [ClipObservation("factory_001", f"worker_{w:03d}", 4.0) for w in range(100, 200)]
    check = floor_check(obs)
    assert check.n_factories >= K_FACTORIES_FLOOR and check.n_workers >= K_WORKERS_FLOOR
    assert check.max_factory_share_workers > MAX_FACTORY_SHARE
    outcome = _build(obs)
    assert outcome.suppressed
    assert outcome.suppressed_reason is not None
    assert "of workers" in outcome.suppressed_reason


def test_the_design_effect_is_the_squared_width_ratio_of_its_own_intervals() -> None:
    """The record's validator recomputes it, so a value that disagreed with the intervals it
    is printed beside could not be constructed."""
    agg = _build(_corpus()).aggregate
    assert agg is not None
    implied = ((agg.hal_ci95[1] - agg.hal_ci95[0])
               / (agg.iid_ci95_for_contrast[1] - agg.iid_ci95_for_contrast[0])) ** 2
    assert agg.design_effect == pytest.approx(implied, rel=1e-9)
    assert agg.design_effect_width_ratio == pytest.approx(agg.design_effect**0.5)


def test_clustering_widens_the_interval_relative_to_iid() -> None:
    """The whole reason H5 exists: clips from one worker are not independent observations."""
    obs = [ClipObservation(f"factory_{f:03d}", f"worker_{w:03d}", hal=4.0 + f * 0.5)
           for f in range(1, 11) for w in range(1, 9) for _ in range(5)]
    agg = _build(obs).aggregate
    assert agg is not None
    assert agg.design_effect > 1.0


def test_the_pre_registered_b_cannot_be_changed_through_the_back_door() -> None:
    with pytest.raises(ValueError, match="pre-registered"):
        _build(_corpus(), b=100)


def test_variance_components_separate_sites_from_people() -> None:
    """H4's statistic. A corpus where factories differ and workers within them do not must
    give a ratio above 1; the reverse must give one below."""
    sites = [ClipObservation(f"factory_{f:03d}", f"worker_{w:03d}", hal=float(f))
             for f in range(1, 11) for w in range(1, 9)]
    people = [ClipObservation(f"factory_{f:03d}", f"worker_{w:03d}", hal=float(w))
              for f in range(1, 11) for w in range(1, 9)]
    assert variance_components(sites).holds
    assert not variance_components(people).holds


def test_variance_components_use_worker_means_not_clip_counts() -> None:
    """A worker recorded more often must not weight the within-factory component; how much
    someone was filmed is a property of the corpus, not of the workforce."""
    balanced = [ClipObservation(f"factory_{f:03d}", f"worker_{w:03d}", hal=float(w))
                for f in range(1, 11) for w in range(1, 9)]
    skewed = list(balanced) + [ClipObservation("factory_001", "worker_001", 1.0)] * 50
    assert variance_components(balanced).between_worker_within_factory == pytest.approx(
        variance_components(skewed).between_worker_within_factory, rel=1e-9)


def test_a_single_factory_cannot_yield_a_between_factory_component() -> None:
    with pytest.raises(ValueError, match="at least two factories"):
        variance_components([ClipObservation("factory_001", "worker_001", 4.0)])


def test_size_terciles_split_factories_by_worker_count() -> None:
    obs: list[ClipObservation] = []
    for f in range(1, 10):
        for w in range(1, f + 1):
            obs.append(ClipObservation(f"factory_{f:03d}", f"worker_{w:03d}", 4.0))
    terciles = size_terciles(obs)
    assert terciles["factory_001"] == "size_tercile_1"
    assert terciles["factory_009"] == "size_tercile_3"
    assert set(terciles.values()) == {"size_tercile_1", "size_tercile_2", "size_tercile_3"}


def test_replicate_means_make_an_interval_reproducible_without_a_grouping_key() -> None:
    """`docs/DATASET_CARD.md` ships these instead of worker ids, so a reader can reproduce a
    clustered interval without being handed the thing that would let them de-aggregate."""
    obs = _corpus()
    means = replicate_means(obs)
    assert len(means) == 10_000
    agg = _build(obs).aggregate
    assert agg is not None
    lo = sorted(means)[int(0.025 * len(means))]
    assert lo == pytest.approx(agg.hal_ci95[0], abs=0.02)


def test_an_aggregate_carries_no_identifier_anywhere() -> None:
    """The schema rejects one in any string or key; this asserts the assembler does not try."""
    agg = _build(_corpus()).aggregate
    assert agg is not None
    dumped = agg.model_dump_json()
    assert "factory_0" not in dumped and "worker_0" not in dumped


def test_h4_is_not_confirmed_by_a_corpus_with_no_within_factory_information() -> None:
    """H4 asks whether exposure is set by the site or the individual. Answering it needs both
    variances, and a corpus where no factory contributed two workers has measured only one.

    `within` is then empty, its mean defaults to 0.0, `ratio` short-circuits to infinity and
    `holds` was True -- the hypothesis confirmed by data that cannot bear on it, which is the
    defect `docs/DECISIONS.md` D034 corrected for H2b, one hypothesis over (D053)."""
    singletons = [ClipObservation(f"factory_{i}", f"worker_{i}", 4.0 + i) for i in range(3)]
    components = variance_components(singletons)
    assert components.n_factories_with_two_workers == 0
    assert components.between_worker_within_factory == 0.0
    assert components.ratio == float("inf")
    assert not components.evaluable
    assert not components.holds


def test_a_corpus_with_no_variance_at_all_does_not_confirm_h4_either() -> None:
    """Identical HAL everywhere: nothing varies between sites or within them. An infinite ratio
    out of 0/0 is not evidence of anything."""
    flat = [ClipObservation(f"factory_{i}", f"worker_{j}", 4.0)
            for i in range(3) for j in range(2)]
    components = variance_components(flat)
    assert components.n_factories_with_two_workers == 3   # the data exists
    assert components.between_factory == 0.0              # but nothing varies
    assert not components.evaluable
    assert not components.holds


def test_h4_still_evaluates_when_the_data_can_answer_it() -> None:
    """The guard must not swallow the real case."""
    real = [ClipObservation("factory_1", "worker_1", 3.0),
            ClipObservation("factory_1", "worker_2", 3.1),
            ClipObservation("factory_2", "worker_3", 7.0),
            ClipObservation("factory_2", "worker_4", 7.1)]
    components = variance_components(real)
    assert components.evaluable and components.holds and components.ratio > 1.0
