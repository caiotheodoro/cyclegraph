"""The detector must not hold a clip in memory. `docs/DECISIONS.md` D043 and D049.

This is a regression test for a defect that has now happened twice, in two scripts, for the
same reason: a decode helper returned a list, colour frames are 1.55 MB each, and a 1200 s clip
at 4 Hz is 7.4 GB. There is no output to assert on -- the run produces correct rows right up
until the machine swaps -- so what is pinned is the shape of the code that avoids it.

Following `tests/test_feature_fidelity.py`, which pins D040 the same way and for the same
reason: some defects are only visible as resource use, and a test that cannot see them can
still stop them being reintroduced.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import run_detector  # noqa: E402


def test_the_streaming_decode_is_a_generator_not_a_list() -> None:
    """A function that returns a list has already paid the memory before its caller sees it."""
    assert inspect.isgeneratorfunction(run_detector.stream_clip)


def test_the_pilot_loop_streams_and_the_smoke_path_is_the_only_caller_of_decode_clip() -> None:
    """`decode_clip` still exists and is still correct; it is bounded by `--smoke`. What must
    not come back is the pilot loop calling it, which is what filled the box."""
    source = inspect.getsource(run_detector.main)
    pilot = source.split("if args.smoke:")[1].split("return 0")[1]
    assert "stream_clip(" in pilot
    assert "decode_clip(" not in pilot


def test_the_frame_that_reaches_the_detector_carries_its_own_instant() -> None:
    """Streaming pairs each frame with its `t_s` rather than zipping two lists afterwards. A
    frame written at the wrong instant is a silent misalignment of the whole clip, which is the
    failure `zip(strict=True)` caught once already."""
    signature = inspect.signature(run_detector.stream_clip)
    assert list(signature.parameters) == ["clip", "token"]
    annotation = str(signature.return_annotation)
    assert "tuple" in annotation and "float" in annotation
