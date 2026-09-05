"""Dense optical flow by Farneback. One implementation of `FlowEstimator`.

`opencv-python-headless` is already declared in the `signal` extra, so this adapter costs no
new dependency -- which is a real input to the estimator choice `docs/DECISIONS.md` D024 fixes,
because RAFT-small would need torch and torch is not declared anywhere.

The failure contract is the one that matters. Farneback does not raise on a hopeless pair; it
returns a field, and on a blurred or dark pair that field decays toward zero. Returning it
would make a flow failure read as a hand that was not moving, which is `docs/RED-TEAM.md` A15
and the flattering direction. So this returns `None` for the cases it can detect -- mismatched
shapes, empty input, a field that is identically zero -- and the caller nulls the sample.

What it cannot detect is stated rather than implied: a *nearly* zero field from motion blur
comes back as a small speed, and `docs/DECISIONS.md` D023 records that the reported null rate
is therefore a lower bound on flow failure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import numpy as np
import numpy.typing as npt

from cyclegraph.signal.ports import Flow

FLOW_METHOD: Final[str] = "farneback-cv2"


@dataclass(frozen=True, slots=True)
class FarnebackFlow:
    """OpenCV's defaults, named rather than positional so the record can carry them."""

    pyr_scale: float = 0.5
    levels: int = 3
    winsize: int = 15
    iterations: int = 3
    poly_n: int = 5
    poly_sigma: float = 1.2

    @property
    def flow_method(self) -> str:
        return FLOW_METHOD

    def flow(self, first: npt.NDArray[np.uint8], second: npt.NDArray[np.uint8]) -> Flow | None:
        import cv2

        if first.shape != second.shape or first.ndim != 2 or first.size == 0:
            return None
        field = cv2.calcOpticalFlowFarneback(
            first, second, None, self.pyr_scale, self.levels, self.winsize,
            self.iterations, self.poly_n, self.poly_sigma, 0,
        )
        if not np.isfinite(field).all():
            return None
        if not field.any():
            return None  # an identically zero field is a dead estimate, not a still hand
        out: Flow = field.astype(np.float32)
        return out
