"""Dominant bout frequency, read spectrally. The path that never segments an exertion.

`docs/RUBRIC.md`: the primary frequency estimate *"reads the dominant frequency out of the
manipulation series spectrally, which is why no boundary rule is needed for it"*, and a
`FrequencyEstimate` is `resolvable` when its peak exceeds **6x the median power of the rest of
the spectrum**.

**Why Lomb-Scargle and not an FFT.** The manipulation series has holes: a frame nobody could
label is `null`, and the rubric forbids filling it. An FFT needs an evenly sampled vector, so
using one would mean imputing the gaps -- the exact gap-filling the duty-cycle rule refuses,
smuggled in one module over. Lomb-Scargle is the standard periodogram for unevenly sampled
data and takes the scored samples at their true instants, so a clip with dropouts is analysed
as what it is rather than as a repaired version of itself.

The grid is the natural periodogram resolution, `k / T` up to Nyquist. A denser grid would
spread each peak over many bins and inflate the median it is compared against, which would
make the 6x floor easier to clear the finer you sampled -- a threshold that moved with an
implementation detail rather than with the signal.

A clip with no dominant cycle is `status: "no_peak"` with `hz: null`, **counted and excluded,
never zero**: treating "no detectable cycle" as "no repetition" is the single most
consequential way this pipeline could understate exposure.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

import numpy as np

from cyclegraph.models import (
    PEAK_POWER_FLOOR,
    UNREADABLE_CEILING,
    ClipRef,
    FrequencyEstimate,
    LabelSource,
)

Label = bool | None

MIN_SCORED_SAMPLES: Final[int] = 8
"""Below this a periodogram is not a measurement of anything. Any clip clearing the rubric's
60 s floor at 4 Hz has hundreds, so this only ever fires on synthetic or truncated input."""

H2B_RESOLVABLE_FRACTION: Final[float] = 0.70
"""`docs/PRE-REGISTRATION.md` H2b: at least this share of pilot clips must be resolvable."""


def _periodogram(times: np.ndarray, values: np.ndarray, freqs: np.ndarray) -> np.ndarray:
    from scipy.signal import lombscargle

    centred = values - values.mean()
    if not np.any(centred):
        return np.zeros_like(freqs)
    power: np.ndarray = lombscargle(times, centred, 2.0 * np.pi * freqs, normalize=True)
    return power


def spectral_frequency(
    clip: ClipRef, series: Sequence[Label], *, fps: float, label_source: LabelSource,
) -> FrequencyEstimate:
    """The dominant bout frequency of one clip's manipulation series."""
    if fps <= 0:
        raise ValueError("the analysis rate is positive")
    nyquist = fps / 2.0
    scored = [(i / fps, float(v)) for i, v in enumerate(series) if v is not None]
    n_total = len(series)
    n_excluded = n_total - len(scored)

    def absent(status: str, ratio: float | None = None) -> FrequencyEstimate:
        return FrequencyEstimate(
            clip_id=clip.clip_id, corpus_rev=clip.corpus_rev, label_source=label_source,
            hz=None, method="spectral", peak_power_ratio=ratio, resolvable=False,
            hz_ci95=None, nyquist_hz=nyquist,
            status=status,  # type: ignore[arg-type]
        )

    if clip.duration_s < 60.0:
        return absent("too_short")
    if n_total == 0 or n_excluded / n_total > UNREADABLE_CEILING:
        return absent("no_labels")
    if len(scored) < MIN_SCORED_SAMPLES:
        return absent("no_labels")

    times = np.asarray([t for t, _ in scored], dtype=np.float64)
    values = np.asarray([v for _, v in scored], dtype=np.float64)
    span = float(times[-1] - times[0])
    if span <= 0:
        return absent("no_labels")

    n_bins = int(np.floor(span * nyquist))
    if n_bins < 2:
        return absent("no_peak")
    freqs = np.arange(1, n_bins + 1, dtype=np.float64) / span

    power = _periodogram(times, values, freqs)
    if not np.any(power):
        return absent("no_peak")  # a constant series has no dominant cycle

    peak = int(np.argmax(power))
    rest = np.delete(power, peak)
    median_rest = float(np.median(rest)) if rest.size else 0.0
    ratio = float(power[peak] / median_rest) if median_rest > 0 else float("inf")
    hz = float(freqs[peak])

    if ratio < PEAK_POWER_FLOOR:
        return absent("no_peak", ratio)
    if hz >= nyquist:
        return absent("aliased", ratio)

    return FrequencyEstimate(
        clip_id=clip.clip_id, corpus_rev=clip.corpus_rev, label_source=label_source,
        hz=hz, method="spectral", peak_power_ratio=ratio, resolvable=True,
        hz_ci95=None, nyquist_hz=nyquist, status="ok",
    )


def resolvable_fraction(estimates: Sequence[FrequencyEstimate]) -> float:
    """H2b's statistic: the share of clips with a dominant cycle. Denominator is every clip
    the estimator ran on, because excluding the unresolvable ones is what H2b measures."""
    if not estimates:
        raise ValueError("a resolvable fraction over no clips is not a result")
    return sum(1 for e in estimates if e.resolvable) / len(estimates)
