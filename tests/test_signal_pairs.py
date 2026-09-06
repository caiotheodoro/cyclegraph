"""Tests for `scripts/build_signal.py`'s pair streaming.

`docs/DECISIONS.md` D045 made the speed pair two **consecutive frames of the source video**,
not two 4 Hz instants. That turns the decode into an index problem, and an off-by-one here does
not raise: it pairs each instant with a frame from somewhere else in the clip and reports a
speed for it. The whole clip would be wrong and every record would still validate.

The decoder is stubbed, so this runs offline against a frame sequence whose every element
announces its own index.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_signal  # noqa: E402

from cyclegraph.corpus.sampling import sample_times  # noqa: E402
from cyclegraph.models import ClipRef  # noqa: E402
from tests import fixtures  # noqa: E402

FPS = 30.0
DURATION_S = 61.0


def _clip() -> ClipRef:
    return ClipRef.model_validate(
        {**fixtures.CLIP_REF, "duration_s": DURATION_S, "fps": FPS})


def _install_stub(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Frames whose single pixel is their own native index, so a mispaired frame is visible."""
    seen: dict[str, Any] = {}

    def fake_argv(url: str, clip: ClipRef, **kw: Any) -> list[str]:
        seen.update(kw)
        return ["ffmpeg"]

    def fake_decode(argv: list[str], width: int, height: int, **kw: Any) -> Iterator[Any]:
        for n in range(int(seen["max_frames"])):
            yield np.full((2, 2), n % 251, dtype=np.uint8)

    class FakeReader:
        def __init__(self, *a: Any, **k: Any) -> None: ...
        def _resolve(self) -> str: return "url"

    monkeypatch.setattr(build_signal, "ffmpeg_clip_argv", fake_argv)
    monkeypatch.setattr(build_signal, "decode_gray_frames", fake_decode)
    monkeypatch.setattr(build_signal, "ShardReader", FakeReader)
    return seen


def test_the_two_frames_are_consecutive_frames_of_the_source(
        monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _install_stub(monkeypatch)
    clip = _clip()
    pairs = list(build_signal.stream_pairs(clip, None, width=2, height=2))
    times = sample_times(DURATION_S)

    assert seen["fps_sampled"] == FPS  # decoded at the clip's rate, not the analysis rate
    assert len(pairs) == len(times)
    for k, t_s, first, second in pairs:
        expected = int(round(t_s * FPS))
        assert int(first[0, 0]) == expected % 251
        assert int(second[0, 0]) == (expected + 1) % 251
        assert t_s == times[k]


def test_the_instants_are_the_analysis_grid_and_arrive_in_order(
        monkeypatch: pytest.MonkeyPatch) -> None:
    _install_stub(monkeypatch)
    pairs = list(build_signal.stream_pairs(_clip(), None, width=2, height=2))
    assert [k for k, _, _, _ in pairs] == sorted(k for k, _, _, _ in pairs)
    assert [t for _, t, _, _ in pairs] == sample_times(DURATION_S)


def test_an_instant_whose_pair_is_not_decoded_is_absent_rather_than_invented(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """The caller records those with a reason. Yielding a pair built from whatever frame
    happened to be last would put a speed on an instant that was never measured."""
    seen = _install_stub(monkeypatch)

    def short_decode(argv: list[str], width: int, height: int, **kw: Any) -> Iterator[Any]:
        for n in range(100):  # far fewer than the plan needs
            yield np.full((2, 2), n % 251, dtype=np.uint8)

    monkeypatch.setattr(build_signal, "decode_gray_frames", short_decode)
    pairs = list(build_signal.stream_pairs(_clip(), None, width=2, height=2))
    assert 0 < len(pairs) < len(sample_times(DURATION_S))
    assert all(int(second[0, 0]) == (int(first[0, 0]) + 1) % 251
               for _, _, first, second in pairs)
    assert seen  # the stub was used


def test_a_clip_that_plans_no_instants_streams_nothing(
        monkeypatch: pytest.MonkeyPatch) -> None:
    _install_stub(monkeypatch)
    tiny = ClipRef.model_validate({**fixtures.CLIP_REF, "duration_s": 60.0, "fps": FPS})
    assert isinstance(list(build_signal.stream_pairs(tiny, None, width=2, height=2)), list)
