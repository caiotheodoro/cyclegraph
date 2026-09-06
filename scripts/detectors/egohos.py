"""EgoHOS: egocentric hand-object segmentation (Zhang et al., ECCV 2022). `docs/METHOD.md` E3.

Adopted in place of 100DOH because 100DOH's published weights cannot be downloaded from either
link its authors give and no mirror exists (`docs/DECISIONS.md` D037, re-probed 2026-09-06 with
EgoHOS as a live control). That is a different reason from the one `docs/METHOD.md` anticipated
when it named EgoHOS the fallback "if 100DOH's coverage fails H2c" -- coverage has never been
measured -- and `docs/DECISIONS.md` D047 records the switch and what it costs.

**It is a segmenter, so a box has to be defined.** `docs/RUBRIC.md` v1.4.0: a hand box from a
mask is the axis-aligned bounding box of that hand's mask pixels, and "largest detected hand
box" then selects among those by area. Only the two hand classes are read; an object a hand is
holding is not part of the hand.

**Install, on the instance, not here.** EgoHOS is built on mmsegmentation 0.x and its
`requirements.txt` pins `torch==1.11.0`, which the current Deep Learning AMI does not ship.
mmcv-full must match the torch and CUDA actually installed or the ops fail at import rather
than at build:

    git clone https://github.com/owenzlz/EgoHOS
    cd EgoHOS/mmsegmentation
    pip install -U openmim && mim install "mmcv-full==1.7.1"
    pip install -e . scikit-image
    gdown 1DEJBeQ3cR1q7cjjzwDUIQVSoptT-y9U7 && unzip work_dirs.zip

Point `EGOHOS_ROOT` at `EgoHOS/mmsegmentation`. `--smoke` measures the real frame rate on a
handful of clips before the full pilot is bought; `docs/METHOD.md` E3's detector estimate has
never been measured and the labeller's estimate turned out to be wrong by a factor of four.

**Verify before trusting.** `mmcv-full` that does not match the installed torch imports and
then produces silently wrong output on some ops. The smoke run prints the fraction of frames
with any hand pixel at all; a value near zero means the install is broken, not that the corpus
has no hands.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Final

import numpy as np

from cyclegraph.signal.ports import HandBox, MaskSource

CONFIG_REL: Final[str] = "work_dirs/seg_twohands_ccda/seg_twohands_ccda.py"
CHECKPOINT_REL: Final[str] = "work_dirs/seg_twohands_ccda/best_mIoU_iter_56000.pth"

HAND_CLASSES: Final[tuple[int, int]] = (1, 2)
"""EgoHOS's `seg_twohands` label map is (0 background, 1 left hand, 2 right hand). The
object-interaction models add further classes and are not loaded: an object a hand is holding
is not part of the hand (`docs/RUBRIC.md` v1.4.0)."""

MIN_MASK_PIXELS: Final[int] = 64
"""A hand smaller than this at 960x540 is a few speckles, and its bounding box would be noise
scaled by `hand_breadth_mm / box_width_px` into a very large mm/s. Not a confidence threshold --
the segmenter emits no per-hand score -- but a floor on what counts as a region at all. 64 px
is an 8x8 block, about 0.01% of the frame."""


def boxes_from_labels(labels: np.ndarray) -> list[HandBox]:
    """A box per hand class present in one label map. `docs/RUBRIC.md` v1.5.0's definition.

    Pure, so it is testable without mmsegmentation installed -- which matters because this is
    the half of the adapter that decides a number the whole speed axis is scaled by, and the
    half that would otherwise only ever run on a rented GPU.

    **The box bounds the largest connected component, not every pixel of the class.** A
    segmenter emits scattered false positives, and a bounding box over a disconnected mask
    spans the specks rather than the hand: measured on real frames it produced boxes up to
    676 px wide at 960x540, against a hand of about 96 px there. That is not a small error --
    `hand_breadth_mm / box_width_px` is a *divisor*, so an inflated box deflates every speed on
    the clip, in the flattering direction (`docs/DECISIONS.md` D048).
    """
    from scipy import ndimage

    out: list[HandBox] = []
    for klass in HAND_CLASSES:
        components, found = ndimage.label(labels == klass)
        if found == 0:
            continue
        sizes = np.bincount(components.ravel())
        sizes[0] = 0  # background of this class's component map
        largest = int(sizes.argmax())
        mask = components == largest
        if int(sizes[largest]) < MIN_MASK_PIXELS:
            continue
        ys, xs = np.nonzero(mask)
        x0, x1 = int(xs.min()), int(xs.max())
        y0, y1 = int(ys.min()), int(ys.max())
        # +1 because the bounding box spans inclusive pixel indices: a mask one pixel wide has
        # width 1, not 0, and HandBox refuses a zero-width box.
        out.append(HandBox(x=float(x0), y=float(y0), width=float(x1 - x0 + 1),
                           height=float(y1 - y0 + 1), score=1.0))
    return out


class EgoHosDetector:
    """Loads once, segments per frame. Raises loudly rather than degrading."""

    def __init__(self, root: str | None = None, config: str | None = None,
                 checkpoint: str | None = None, device: str = "cuda:0") -> None:
        self._root = Path(root or os.environ.get("EGOHOS_ROOT", ""))
        self._config = Path(config or self._root / CONFIG_REL)
        self._checkpoint = Path(checkpoint or self._root / CHECKPOINT_REL)
        if not self._root.exists():
            raise RuntimeError(
                "EGOHOS_ROOT is unset or missing. It points at the `mmsegmentation` directory "
                "of a clone of github.com/owenzlz/EgoHOS; see this module's docstring."
            )
        for path, what in ((self._config, "config"), (self._checkpoint, "checkpoint")):
            if not path.exists():
                raise RuntimeError(
                    f"EgoHOS {what} not found at {path}. `work_dirs.zip` must be downloaded "
                    f"and unzipped inside EGOHOS_ROOT."
                )
        self._device = device
        self._model: Any = None

    @property
    def mask_source(self) -> MaskSource:
        return "egohos"

    def _load(self) -> Any:
        if self._model is not None:
            return self._model
        from mmseg.apis import init_segmentor

        self._model = init_segmentor(str(self._config), str(self._checkpoint),
                                     device=self._device)
        return self._model

    def segment(self, frame: np.ndarray) -> np.ndarray:
        """The raw label map for one colour frame. Separated so a smoke run can inspect it."""
        # Checked before the import, so a grey frame is refused on any machine rather than only
        # on one with mmsegmentation installed.
        if frame.ndim != 3 or frame.shape[2] != 3:
            raise ValueError(
                "EgoHOS was fitted on colour frames; pass an (H, W, 3) RGB frame. "
                "docs/DECISIONS.md D040 measured what a grey frame costs a colour model."
            )
        from mmseg.apis import inference_segmentor

        # mmseg reads images in BGR, as OpenCV hands them over; an RGB frame is reversed here
        # rather than anywhere else so the one channel-order conversion is next to the call
        # that needs it.
        result = inference_segmentor(self._load(), frame[:, :, ::-1].copy())[0]
        return np.asarray(result)

    def boxes(self, frame: np.ndarray) -> list[HandBox]:
        """A box per hand, in the frame's own pixel coordinates.

        The score is 1.0 and means "this hand was segmented", not a confidence: the model emits
        a label map and no per-region probability. Writing a fabricated confidence would put a
        number on the record that nothing measured.
        """
        return boxes_from_labels(self.segment(frame))
