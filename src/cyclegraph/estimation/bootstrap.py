"""Cluster bootstrap intervals and the design effect, in both readings.

Ported from `../vernier/src/vernier/estimation/bootstrap.py` (`docs/LINEAGE.md`), with two
changes the pre-registration requires: the cluster id is the composite `factory_id/worker_id`
and a bare id is refused (`docs/DECISIONS.md` D015), and the design effect is returned as the
variance ratio *and* the width ratio because the two readings have been confused before
(`docs/PRE-REGISTRATION.md` H5).

The replicate means are exposed so the release can ship them
(`docs/DATASET_CARD.md` `bootstrap_replicates`) and every interval is reproducible without a
grouping key.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, NamedTuple

import numpy as np
from numpy.typing import NDArray

BOOTSTRAP_B = 10_000
BOOTSTRAP_SEED = 777
_COMPOSITE_SEP = "/"


class BootstrapCI(NamedTuple):
    lo: float
    hi: float
    method: Literal["cluster-bootstrap", "iid"]
    clusters: int | None
    B: int
    seed: int

    @property
    def width(self) -> float:
        return self.hi - self.lo


class DesignEffect(NamedTuple):
    """`variance_ratio` is the design effect; `width_ratio` is its square root."""

    variance_ratio: float
    width_ratio: float


def composite_cluster_ids(factory_ids: Sequence[str], worker_ids: Sequence[str]) -> list[str]:
    """`factory_id/worker_id` for every record. The only cluster id the estimator accepts."""
    if len(factory_ids) != len(worker_ids):
        raise ValueError("factory_ids and worker_ids must align")
    return [f"{f}{_COMPOSITE_SEP}{w}" for f, w in zip(factory_ids, worker_ids, strict=True)]


def _check_composite(cluster_ids: Sequence[str]) -> None:
    bad = [c for c in cluster_ids if _COMPOSITE_SEP not in c]
    if bad:
        raise ValueError(
            "cluster ids must be the composite factory_id/worker_id; worker_id alone is "
            f"numbered within factory and would pool people across sites (D015): {bad[0]!r}"
        )


def cluster_bootstrap_means(
    values: Sequence[float],
    cluster_ids: Sequence[str],
    *,
    B: int = BOOTSTRAP_B,
    seed: int = BOOTSTRAP_SEED,
) -> NDArray[np.float64]:
    """The B replicate means from resampling whole clusters with replacement."""
    if len(values) != len(cluster_ids):
        raise ValueError("values and cluster_ids must align")
    if B <= 0:
        raise ValueError("B must be positive")
    _check_composite(cluster_ids)
    arr = np.asarray(values, dtype=np.float64)
    ids = np.asarray(cluster_ids)
    unique, inverse = np.unique(ids, return_inverse=True)
    n_clusters = unique.shape[0]
    if n_clusters < 2:
        raise ValueError("a cluster bootstrap needs at least two clusters")
    sums = np.bincount(inverse, weights=arr, minlength=n_clusters)
    counts = np.bincount(inverse, minlength=n_clusters).astype(np.float64)
    rng = np.random.default_rng(seed)
    picks = rng.integers(0, n_clusters, size=(B, n_clusters))
    # Resampled mean = sum of picked cluster sums / sum of picked cluster sizes.
    means: NDArray[np.float64] = sums[picks].sum(axis=1) / counts[picks].sum(axis=1)
    return means


def cluster_bootstrap_ci(
    values: Sequence[float],
    cluster_ids: Sequence[str],
    *,
    B: int = BOOTSTRAP_B,
    seed: int = BOOTSTRAP_SEED,
) -> BootstrapCI:
    """Percentile 95% interval for the mean, clustering over `factory_id/worker_id`."""
    means = cluster_bootstrap_means(values, cluster_ids, B=B, seed=seed)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return BootstrapCI(
        lo=float(lo),
        hi=float(hi),
        method="cluster-bootstrap",
        clusters=int(np.unique(np.asarray(cluster_ids)).shape[0]),
        B=B,
        seed=seed,
    )


def iid_bootstrap_ci(
    values: Sequence[float], *, B: int = BOOTSTRAP_B, seed: int = BOOTSTRAP_SEED
) -> BootstrapCI:
    """The iid interval. Never reported alone: it sits beside the clustered one, labelled,
    to exhibit the design effect (`docs/PRE-REGISTRATION.md` "Clustering")."""
    arr = np.asarray(values, dtype=np.float64)
    n = arr.shape[0]
    if n < 2 or B <= 0:
        raise ValueError("need at least two values and a positive B")
    rng = np.random.default_rng(seed)
    picks = rng.integers(0, n, size=(B, n))
    means = arr[picks].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return BootstrapCI(lo=float(lo), hi=float(hi), method="iid", clusters=None, B=B, seed=seed)


def design_effect(cluster_ci: BootstrapCI, iid_ci: BootstrapCI) -> DesignEffect:
    """Both readings of the same number. H5's threshold is on `variance_ratio`."""
    if cluster_ci.method != "cluster-bootstrap" or iid_ci.method != "iid":
        raise ValueError("design_effect takes one clustered and one iid interval, in that order")
    if iid_ci.width <= 0:
        raise ValueError("iid interval has no width")
    width_ratio = cluster_ci.width / iid_ci.width
    return DesignEffect(variance_ratio=width_ratio * width_ratio, width_ratio=width_ratio)


def expected_design_effect(cluster_size: float, icc: float) -> float:
    """Kish: 1 + (m − 1) ρ for equal clusters. Used by the golden test, exposed for reports."""
    if cluster_size < 1 or not 0 <= icc <= 1:
        raise ValueError("cluster_size >= 1 and 0 <= icc <= 1")
    return 1.0 + (cluster_size - 1.0) * icc

