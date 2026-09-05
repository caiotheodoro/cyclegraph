"""The 4 Hz sample plan: which instants a clip is read at, and as what pairs.

`docs/DECISIONS.md` D010 fixes the analysis rate at 4 Hz, which puts Nyquist at 2 Hz -- 120
exertions per minute, above any sustained hand cycle the TLV contemplates. Each sample is a
**pair** `(t, t + 1/fps)` so the speed path has a flow baseline; decode is sequential either
way, so the pair roughly doubles frames written rather than frames decoded.

**These instants do not exist in the corpus.** The release ships `duration_sec` and `fps` per
clip and nothing per frame (`../vernier/docs/DECISIONS.md` D065), so every timestamp here is
cyclegraph's construction and is disclosed as one wherever it reaches a record.

The rule that decides the count: the **second** frame of the last pair must fall strictly
inside the clip. A plan whose final pair reaches past the end produces a decode failure that
looks like corpus corruption, and `docs/METHOD.md` E2's sub-1% gate would absorb it.
"""

from __future__ import annotations

import math
from typing import Final

from cyclegraph.models import MIN_CLIP_S, ClipRef

ANALYSIS_HZ: Final[float] = 4.0


def pair_offset_s(fps_sampled: float = ANALYSIS_HZ) -> float:
    """The gap between the two frames of a pair, `1/fps`."""
    if fps_sampled <= 0:
        raise ValueError("the analysis rate is positive")
    return 1.0 / fps_sampled


def nyquist_hz(fps_sampled: float = ANALYSIS_HZ) -> float:
    """The highest frequency the rate can resolve. Above it, `status: "aliased"`."""
    return fps_sampled / 2.0


def n_samples(duration_s: float, *, fps_sampled: float = ANALYSIS_HZ) -> int:
    """How many pairs fit, with the second frame of the last one strictly inside the clip.

    Samples sit at `t = i/fps`, and the pair at `i` needs `t + 1/fps < duration`, so
    `i < duration*fps - 1`. The count is the number of non-negative integers satisfying that,
    which is `ceil(duration*fps - 1)` -- and **not** `floor((duration - 1/fps) * fps) + 1`,
    which is one too many whenever `duration*fps` is an integer, exactly the case where the
    last pair lands on the final frame rather than before it.
    """
    if duration_s <= 0:
        raise ValueError("a clip has positive duration")
    if fps_sampled <= 0:
        raise ValueError("the analysis rate is positive")
    limit = duration_s * fps_sampled - 1.0
    if limit <= 0:
        return 0
    count = math.ceil(limit)
    # `ceil` of an exact integer is that integer, which is the count we want; of a fractional
    # value it rounds up, also what we want. The guard is for float error near an integer.
    if math.isclose(limit, round(limit), rel_tol=0.0, abs_tol=1e-9):
        count = int(round(limit))
    return max(count, 0)


def sample_times(duration_s: float, *, fps_sampled: float = ANALYSIS_HZ) -> list[float]:
    """The first frame of every pair, in seconds from the clip's start."""
    step = pair_offset_s(fps_sampled)
    return [i * step for i in range(n_samples(duration_s, fps_sampled=fps_sampled))]


def plan_pairs(clip: ClipRef, *, fps_sampled: float = ANALYSIS_HZ) -> list[tuple[float, float]]:
    """Every `(t, t + 1/fps)` pair for a clip. A clip under the rubric's floor plans none."""
    if clip.duration_s < MIN_CLIP_S:
        return []
    step = pair_offset_s(fps_sampled)
    return [(t, t + step) for t in sample_times(clip.duration_s, fps_sampled=fps_sampled)]
