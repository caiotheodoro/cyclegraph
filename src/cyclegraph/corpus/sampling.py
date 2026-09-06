"""The 4 Hz sample plan: which instants a clip is read at, and as what pairs.

`docs/DECISIONS.md` D010 fixes the analysis rate at 4 Hz, which puts Nyquist at 2 Hz -- 120
exertions per minute, above any sustained hand cycle the TLV contemplates. Each sample is a
**pair** `(t, t + 1/fps_clip)` so the speed path has a flow baseline, where `fps_clip` is the
clip's own frame rate and **not** the analysis rate (`docs/DECISIONS.md` D045, pre-registration
v1.5.0). Read as the analysis rate the two frames were 0.25 s apart, and at that baseline
neither flow estimator recovers a working hand's motion -- both report the background inside
the hand box, which the rubric then subtracts (D044). The pair therefore doubles frames
*decoded* and leaves frames *written* unchanged: the second frame of a pair is never labelled.

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


def pair_offset_s(fps_clip: float) -> float:
    """The gap between the two frames of a speed pair: one frame of the source video.

    Takes the **clip's** frame rate, and has no default on purpose. The default it used to
    carry was the analysis rate, which is how a 0.25 s flow baseline got into the pipeline
    without anyone choosing it (`docs/DECISIONS.md` D045). A caller now has to say which rate
    it means.
    """
    if fps_clip <= 0:
        raise ValueError("a frame rate is positive")
    return 1.0 / fps_clip


def nyquist_hz(fps_sampled: float = ANALYSIS_HZ) -> float:
    """The highest frequency the rate can resolve. Above it, `status: "aliased"`."""
    return fps_sampled / 2.0


def n_samples(duration_s: float, *, fps_sampled: float = ANALYSIS_HZ) -> int:
    """How many samples fit, leaving room for the last one's pair inside the clip.

    Samples sit at `t = i/fps`, and the margin reserved for the pair is one **analysis**
    period, so `i < duration*fps - 1`. The count is the number of non-negative integers
    satisfying that, which is `ceil(duration*fps - 1)` -- and **not**
    `floor((duration - 1/fps) * fps) + 1`, which is one too many whenever `duration*fps` is an
    integer, exactly the case where the last pair lands on the final frame rather than before
    it.

    **The margin is deliberately larger than the pair now needs.** Since D045 the pair spans
    one frame of the source video, about 0.033 s, not the 0.25 s this reserves. Shrinking the
    margin to match would gain at most one sample per clip and would change `n_samples` for
    every clip in the corpus, including `CONTRACTS.md`'s worked 187.4 s example, which is
    pinned at 749 and tested. A conservative decode margin is worth more than one sample, and
    keeping it stated here is the difference between a decision and an oversight.
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
    """The first frame of every pair, in seconds from the clip's start.

    The spacing is the analysis grid, `1/fps_sampled`. It is not the pair offset and has not
    been since D045; the two were the same number under the old reading, which is why one
    call site could stand for both.
    """
    if fps_sampled <= 0:
        raise ValueError("the analysis rate is positive")
    step = 1.0 / fps_sampled
    return [i * step for i in range(n_samples(duration_s, fps_sampled=fps_sampled))]


def plan_pairs(clip: ClipRef, *, fps_sampled: float = ANALYSIS_HZ) -> list[tuple[float, float]]:
    """Every `(t, t + 1/fps_clip)` pair for a clip. A clip under the rubric's floor plans none.

    The instants come from the analysis grid; the offset to the second frame comes from the
    clip's own frame rate (D045).
    """
    if clip.duration_s < MIN_CLIP_S:
        return []
    step = pair_offset_s(clip.fps)
    return [(t, t + step) for t in sample_times(clip.duration_s, fps_sampled=fps_sampled)]
