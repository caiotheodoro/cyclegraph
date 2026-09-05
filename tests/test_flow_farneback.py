"""Tests for `src/cyclegraph/signal/flow_farneback.py`."""

from __future__ import annotations

import numpy as np
import pytest

from cyclegraph.signal.flow_farneback import FLOW_METHOD, FarnebackFlow

# Farneback resolves sub-pixel displacement to a fraction of a pixel at its finest pyramid
# level. A synthetic shift of 3 px must come back as 3 px; 0.3 px is a tenth of the signal and
# is the estimator's documented working precision, not a value tuned until this passed.
DISPLACEMENT_TOLERANCE_PX = 0.3


def _textured(height: int = 96, width: int = 128, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.integers(0, 255, size=(height, width), dtype=np.uint8)


def test_a_known_translation_comes_back_as_that_translation() -> None:
    """The golden case: shift a textured frame by exactly 3 px and recover 3 px."""
    first = _textured()
    second = np.roll(first, 3, axis=1)
    field = FarnebackFlow().flow(first, second)
    assert field is not None
    interior = field[10:-10, 10:-10]  # the wrapped edge is not a translation
    assert float(np.median(interior[..., 0])) == pytest.approx(3.0, abs=DISPLACEMENT_TOLERANCE_PX)
    assert float(np.median(interior[..., 1])) == pytest.approx(0.0, abs=DISPLACEMENT_TOLERANCE_PX)


def test_a_featureless_pair_gives_no_field_rather_than_a_field_of_zeros() -> None:
    """A15 at the adapter. The real failure -- darkness, blown highlights -- leaves nothing to
    track, and Farneback returns an identically zero field. Returning it would make a dead
    estimate indistinguishable from a hand that was not moving."""
    flat = np.full((64, 64), 128, dtype=np.uint8)
    assert FarnebackFlow().flow(flat, flat.copy()) is None


def test_a_static_but_textured_pair_leaks_a_small_field_and_that_is_the_A15_limit() -> None:
    """What the `== 0.0` rule cannot catch, measured rather than asserted in prose.

    Two identical textured frames are a dead pair in every sense that matters, but Farneback
    returns a few hundredths of a pixel of noise rather than zeros, so the null detector does
    not fire and the sample passes through as a real speed. The magnitude bounds the harm:
    0.08 px per 0.25 s interval scaled by 85 mm over a 193 px box is about 0.14 mm/s, against
    hand speeds in the hundreds. The bias is negligible; the under-count of the null rate is
    the thing `docs/DECISIONS.md` D023 says to read as a lower bound.
    """
    first = _textured(270, 480, seed=3)
    field = FarnebackFlow().flow(first, first.copy())
    assert field is not None
    assert float(np.sqrt((field**2).sum(axis=-1)).max()) < 0.1


def test_a_mismatched_pair_returns_none_rather_than_raising() -> None:
    assert FarnebackFlow().flow(_textured(96, 128), _textured(64, 64)) is None


def test_an_empty_frame_returns_none() -> None:
    empty = np.zeros((0, 0), dtype=np.uint8)
    assert FarnebackFlow().flow(empty, empty) is None


def test_the_method_name_reaches_the_record_verbatim() -> None:
    assert FarnebackFlow().flow_method == FLOW_METHOD == "farneback-cv2"


def test_the_parameters_are_named_so_a_record_can_carry_them() -> None:
    estimator = FarnebackFlow(winsize=21)
    assert estimator.winsize == 21 and estimator.levels == 3
