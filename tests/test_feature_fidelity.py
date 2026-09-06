"""The regression tests for `docs/DECISIONS.md` D040.

A feature distribution is not a schema, so no contract or validator in this repository could
have caught a head being applied to features it was not fitted to. These are the checks that
would have.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from run_labeller import DECODE_PIX_FMT, DinoFeatures  # noqa: E402

from cyclegraph.corpus.decode import ffmpeg_clip_argv  # noqa: E402
from cyclegraph.models import ClipRef  # noqa: E402
from tests import fixtures  # noqa: E402


def _clip() -> ClipRef:
    return ClipRef.model_validate(fixtures.CLIP_REF)


def test_the_labeller_decodes_colour_not_grey() -> None:
    """D040 defect 2. Grey frames replicated across three channels moved the duty cycle by
    0.033 against H1a's bound of 0.05 -- a preprocessing choice consuming two thirds of the
    tolerance of the hypothesis it feeds."""
    assert DECODE_PIX_FMT == "rgb24"
    argv = ffmpeg_clip_argv("https://x/y", _clip(), fps_sampled=4.0, width=960, height=540,
                            pix_fmt=DECODE_PIX_FMT)
    assert argv[argv.index("-pix_fmt") + 1] == "rgb24"


def test_the_flow_path_still_decodes_grey_by_default() -> None:
    """The default is unchanged: the speed path is luminance-only and grey is a third of the
    bytes. What changed is that the format is a parameter rather than an assumption."""
    argv = ffmpeg_clip_argv("https://x/y", _clip(), fps_sampled=4.0, width=480, height=270)
    assert argv[argv.index("-pix_fmt") + 1] == "gray"


def test_preprocess_refuses_a_greyscale_frame() -> None:
    """The failure that silently produced 462,437 wrong labels is now loud."""
    grey = np.zeros((540, 960), dtype=np.uint8)
    with pytest.raises(ValueError, match="colour frames"):
        DinoFeatures.preprocess(grey)
    replicated = np.repeat(grey[:, :, None], 3, axis=2)
    assert DinoFeatures.preprocess(replicated).shape == (3, 224, 224)  # shape alone cannot tell


def test_pooling_includes_the_cls_token() -> None:
    """D040 defect 1. Vernier's code means over every token; its docstring says patch tokens
    and this project reproduced the docstring. Measured impact was nil, but the head is only
    meaningful over the features it was fitted to, so the check is on the code path."""
    source = (ROOT / "scripts" / "run_labeller.py").read_text()
    assert "last_hidden_state.mean(dim=1)" in source
    assert "last_hidden_state[:, 1:, :]" not in source


def test_preprocess_matches_the_pipeline_the_head_was_fitted_to() -> None:
    """Shortest edge to 256 bicubic, centre-crop 224, rescale, ImageNet normalise. Verified
    end to end against vernier's stored vectors at cosine 1.000000 (D040); this pins the
    shape and the normalisation so a later edit cannot drift them unnoticed."""
    frame = np.full((1080, 1920, 3), 128, dtype=np.uint8)
    out = DinoFeatures.preprocess(frame)
    assert out.shape == (3, 224, 224)
    assert out.dtype == np.float32
    # 128/255 normalised by ImageNet mean/std, per channel.
    expected = [(128 / 255 - m) / s for m, s in
                zip((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))]
    for channel, value in enumerate(expected):
        assert out[channel].mean() == pytest.approx(value, abs=1e-4)
