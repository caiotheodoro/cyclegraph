"""Golden cases for the cluster bootstrap: synthetic clustered data with a known design effect.

Kish's formula gives the design effect for equal clusters of size m and intraclass
correlation ρ as 1 + (m − 1)ρ. The estimator must recover it, and must recover ≈1 when ρ = 0.
"""

from __future__ import annotations

import numpy as np
import pytest

from cyclegraph.estimation import bootstrap as bs

N_CLUSTERS = 400
CLUSTER_SIZE = 10
B = 2000


def _clustered(icc: float, seed: int) -> tuple[list[float], list[str]]:
    """Random-intercept data: y = u_cluster + e, var(u) = icc, var(e) = 1 − icc."""
    rng = np.random.default_rng(seed)
    u = rng.normal(0.0, np.sqrt(icc), size=N_CLUSTERS)
    e = rng.normal(0.0, np.sqrt(1.0 - icc), size=(N_CLUSTERS, CLUSTER_SIZE))
    y = (u[:, None] + e).ravel()
    ids = [f"factory_{c // 20:03d}/worker_{c % 20:03d}" for c in range(N_CLUSTERS) for _ in range(CLUSTER_SIZE)]
    return y.tolist(), ids


@pytest.mark.parametrize("icc", [0.3, 0.6])
def test_recovers_a_known_design_effect(icc: float) -> None:
    values, ids = _clustered(icc, seed=11)
    cl = bs.cluster_bootstrap_ci(values, ids, B=B, seed=1)
    iid = bs.iid_bootstrap_ci(values, B=B, seed=1)
    de = bs.design_effect(cl, iid)
    expected = bs.expected_design_effect(CLUSTER_SIZE, icc)
    assert de.variance_ratio == pytest.approx(expected, rel=0.12)
    assert de.width_ratio == pytest.approx(np.sqrt(de.variance_ratio))


def test_independent_data_has_a_design_effect_near_one() -> None:
    values, ids = _clustered(0.0, seed=5)
    cl = bs.cluster_bootstrap_ci(values, ids, B=B, seed=2)
    iid = bs.iid_bootstrap_ci(values, B=B, seed=2)
    assert bs.design_effect(cl, iid).variance_ratio == pytest.approx(1.0, abs=0.12)


def test_clustered_interval_is_wider_and_contains_the_mean() -> None:
    values, ids = _clustered(0.5, seed=3)
    cl = bs.cluster_bootstrap_ci(values, ids, B=B, seed=3)
    iid = bs.iid_bootstrap_ci(values, B=B, seed=3)
    assert cl.width > iid.width
    m = float(np.mean(values))
    assert cl.lo <= m <= cl.hi


def test_bare_worker_id_is_refused_as_a_cluster() -> None:
    """D015: worker_001 exists in every factory."""
    values = [1.0, 2.0, 3.0, 4.0]
    with pytest.raises(ValueError, match="composite"):
        bs.cluster_bootstrap_ci(values, ["worker_001", "worker_001", "worker_002", "worker_002"], B=10)


def test_composite_ids_are_built_from_both_parts() -> None:
    ids = bs.composite_cluster_ids(["factory_001", "factory_002"], ["worker_001", "worker_001"])
    assert ids == ["factory_001/worker_001", "factory_002/worker_001"]
    assert len(set(ids)) == 2


def test_replicates_are_seeded_and_reproducible() -> None:
    values, ids = _clustered(0.2, seed=7)
    a = bs.cluster_bootstrap_means(values, ids, B=50, seed=9)
    b = bs.cluster_bootstrap_means(values, ids, B=50, seed=9)
    c = bs.cluster_bootstrap_means(values, ids, B=50, seed=10)
    assert np.array_equal(a, b)
    assert not np.array_equal(a, c)
    assert a.shape == (50,)


def test_design_effect_demands_the_right_pair() -> None:
    values, ids = _clustered(0.2, seed=8)
    cl = bs.cluster_bootstrap_ci(values, ids, B=20)
    iid = bs.iid_bootstrap_ci(values, B=20)
    with pytest.raises(ValueError):
        bs.design_effect(iid, cl)


def test_defaults_are_the_pre_registered_ones() -> None:
    assert bs.BOOTSTRAP_B == 10_000
