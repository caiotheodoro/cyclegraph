"""`HALScore` from a duty cycle and one frequency-axis input. `docs/METHOD.md` E6.

The mapping names its input (`docs/ARCHITECTURE.md`): `akkas-2015-speed-dc` takes RMS hand
speed and `radwin-2015-freq-dc` takes bout frequency, and a record carrying the wrong one is
invalid rather than quietly mapped from the other. This module never chooses between them --
the caller says which path it is scoring, because the two paths have different meanings and
`docs/DECISIONS.md` D014 makes only one of them primary.

**No approximation of this project's own, ever.** The two functions in `exposure/hal.py` are
peer-reviewed fits with published residuals, and an approximation would produce numbers that
look like HAL, compare against published HAL in H3, and be wrong by an offset H3 could not
detect (`docs/RUBRIC.md`).

**The force axis is structurally absent.** `force_axis` is `null` and `tlv_evaluable` is
`false` on every record this module can produce; there is no code path that could populate
either, which is the point of `docs/COVERAGE.md`'s "unobservable, full stop".
"""

from __future__ import annotations

from typing import Final

from cyclegraph.exposure.hal import (
    SCALE_REV,
    Mapping,
    hal_akkas_2015,
    hal_radwin_2015,
    in_fitted_range,
)
from cyclegraph.models import DutyCycleEstimate, FrequencyEstimate, HALScore, HandSpeedEstimate

FORCE_AXIS_REASON: Final[str] = (
    "peak force is not observable from video (docs/COVERAGE.md); it is never imputed"
)

HAL_DECIMALS: Final[int] = 1
"""`docs/RUBRIC.md`: reported to one decimal, as Radwin 2015 recommends."""


def _score(
    duty: DutyCycleEstimate, *, mapping: Mapping, hz: float | None, speed: float | None,
) -> HALScore:
    def build(hal: float | None, duty_cycle: float, out_of_range: bool,
              status: str) -> HALScore:
        return HALScore(
            clip_id=duty.clip_id,
            corpus_rev=duty.corpus_rev,
            label_source=duty.label_source,
            hal=hal,
            mapping=mapping,
            scale_rev=SCALE_REV[mapping],
            duty_cycle=duty_cycle,
            hz=hz,
            rms_speed_mm_s=speed,
            out_of_range=out_of_range,
            force_axis=None,
            force_axis_reason=FORCE_AXIS_REASON,
            tlv_evaluable=False,
            status=status,  # type: ignore[arg-type]
        )

    x = hz if mapping == "radwin-2015-freq-dc" else speed
    if duty.status != "ok" or duty.duty_cycle is None or x is None:
        return build(None, duty.duty_cycle or 0.0, False, "no_input")
    if duty.duty_cycle == 0.0:
        # Both equations take ln D, so a zero duty cycle has no image. It is a value with a
        # status, not a HAL of zero: a worker whose hands never engaged is not at
        # hand-activity level zero, they are outside the instrument's domain.
        return build(None, 0.0, False, "zero_duty_cycle")
    d_pct = 100.0 * duty.duty_cycle
    raw = (hal_radwin_2015(x, d_pct) if mapping == "radwin-2015-freq-dc"
           else hal_akkas_2015(x, d_pct))
    return build(
        round(min(max(raw, 0.0), 10.0), HAL_DECIMALS),
        duty.duty_cycle,
        not in_fitted_range(mapping, x, d_pct),
        "ok",
    )


def score_speed_path(duty: DutyCycleEstimate, speed: HandSpeedEstimate) -> HALScore:
    """The primary path (D014): `akkas-2015-speed-dc` from RMS hand speed."""
    if speed.clip_id != duty.clip_id:
        raise ValueError("a HAL score joins one clip's duty cycle and its own speed")
    return _score(duty, mapping="akkas-2015-speed-dc", hz=None,
                  speed=speed.rms_speed_mm_s if speed.status == "ok" else None)


def score_spectral_path(duty: DutyCycleEstimate, frequency: FrequencyEstimate) -> HALScore:
    """The cross-check path: `radwin-2015-freq-dc` from **bout** frequency, which is a lower
    bound on exertion frequency, so the HAL it produces is a lower bound too (D014, A10)."""
    if frequency.clip_id != duty.clip_id:
        raise ValueError("a HAL score joins one clip's duty cycle and its own frequency")
    return _score(duty, mapping="radwin-2015-freq-dc",
                  hz=frequency.hz if frequency.status == "ok" else None, speed=None)
