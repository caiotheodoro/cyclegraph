"""The two published HAL mappings, transcribed from their papers. `docs/DECISIONS.md` D013.

Both are regression fits to the ACGIH 2001 Hand Activity Level look-up table, made by the
group that automated HAL from video. Neither is this project's own; `docs/RUBRIC.md` says
why an approximation of our own is refused. Constants are the papers' constants to the
precision the papers print them. `tests/test_hal_mapping.py` holds each function to the
paper's table cells.

Radwin RG, Azari DP, Lindstrom MJ, Ulin SS, Armstrong TJ, Rempel D. A frequency–duty cycle
equation for the ACGIH hand activity level. Ergonomics 2015;58(2):173–183. Eq. (3).

Akkas O, Azari DP, Chen C-HE, Hu YH, Ulin SS, Armstrong TJ, Rempel D, Radwin RG. A hand
speed–duty cycle equation for estimating the ACGIH hand activity level rating. Ergonomics
2015;58(2):184–194.

Neither function clips to the 0–10 scale or rounds. The caller decides how to report an
input outside the fitted range (`in_fitted_range`), and `HALScore.out_of_range` carries that
decision on the record rather than hiding it in a clamp.
"""

from __future__ import annotations

import math
from typing import Literal, NamedTuple

Mapping = Literal["radwin-2015-freq-dc", "akkas-2015-speed-dc"]

# `HALScore.scale_rev` for each mapping: the table edition the fit was made to, and the fit.
SCALE_REV: dict[Mapping, str] = {
    "radwin-2015-freq-dc": "acgih-2001-table/radwin-2015-fit",
    "akkas-2015-speed-dc": "acgih-2001-table/akkas-2015-fit",
}


class FittedRange(NamedTuple):
    """The range of the data each equation was fitted on. Outside it is extrapolation."""

    x_lo: float
    x_hi: float
    duty_cycle_pct_lo: float
    duty_cycle_pct_hi: float


# Radwin 2015 Table 2: F 0.125–1.67 exertions/s, D 11–100 %.
RADWIN_2015_RANGE = FittedRange(0.125, 1.67, 11.0, 100.0)
# Akkas 2015 Table 1: S 255.3–1288.0 mm/s, D 11–100 %.
AKKAS_2015_RANGE = FittedRange(255.3, 1288.0, 11.0, 100.0)

# Radwin 2015 eq. (3): HAL = 6.56 ln D [ F^1.31 / (1 + 3.18 F^1.31) ]
_R_A = 6.56
_R_P = 1.31
_R_K = 3.18

# Akkas 2015: HAL = 10 σ(−15.87 + 0.02 D + 2.25 ln S), S in mm/s
_A_B0 = -15.87
_A_BD = 0.02
_A_BS = 2.25


def hal_radwin_2015(frequency_hz: float, duty_cycle_pct: float) -> float:
    """HAL from exertion frequency (exertions/s) and duty cycle (percent).

    On the spectral path the frequency handed in is manipulation-*bout* frequency, a lower
    bound on exertion frequency (`docs/DECISIONS.md` D014); the result is then a lower bound
    too, and the caller labels it so.
    """
    if frequency_hz <= 0:
        raise ValueError("frequency must be positive; an unresolvable clip is null, not zero")
    if duty_cycle_pct <= 0 or duty_cycle_pct > 100:
        raise ValueError("duty cycle is a percentage in (0, 100]")
    f = math.pow(frequency_hz, _R_P)
    return _R_A * math.log(duty_cycle_pct) * (f / (1.0 + _R_K * f))


def hal_akkas_2015(rms_speed_mm_s: float, duty_cycle_pct: float) -> float:
    """HAL from RMS hand speed (mm/s, hand-breadth scaled) and duty cycle (percent)."""
    if rms_speed_mm_s <= 0:
        raise ValueError("speed must be positive; a failed flow is null, not zero")
    if duty_cycle_pct <= 0 or duty_cycle_pct > 100:
        raise ValueError("duty cycle is a percentage in (0, 100]")
    z = _A_B0 + _A_BD * duty_cycle_pct + _A_BS * math.log(rms_speed_mm_s)
    return 10.0 / (1.0 + math.exp(-z))


def in_fitted_range(mapping: Mapping, x: float, duty_cycle_pct: float) -> bool:
    """Whether (x, D) lies inside the data the mapping was fitted on."""
    r = RADWIN_2015_RANGE if mapping == "radwin-2015-freq-dc" else AKKAS_2015_RANGE
    return r.x_lo <= x <= r.x_hi and r.duty_cycle_pct_lo <= duty_cycle_pct <= r.duty_cycle_pct_hi
