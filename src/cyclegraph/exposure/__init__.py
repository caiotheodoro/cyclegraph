"""`exposure` — duty cycle and the Hand Activity Level axis. `docs/ARCHITECTURE.md`."""

from cyclegraph.exposure.hal import (
    AKKAS_2015_RANGE,
    RADWIN_2015_RANGE,
    SCALE_REV,
    hal_akkas_2015,
    hal_radwin_2015,
    in_fitted_range,
)

__all__ = [
    "AKKAS_2015_RANGE",
    "RADWIN_2015_RANGE",
    "SCALE_REV",
    "hal_akkas_2015",
    "hal_radwin_2015",
    "in_fitted_range",
]
