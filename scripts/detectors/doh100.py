"""100DOH: hand detection from Shan et al., CVPR 2020. `docs/METHOD.md` E3.

`docs/SURVEY.md` records this as `[V]` from the repository `github.com/ddshan/hand_object_detector`,
MIT licence, trained on 100K YouTube frames plus egocentric EPIC-KITCHENS/EGTEA/CharadesEgo --
which is why it is the contract's primary detector rather than a general-purpose hand model.

**Install, on the instance, not here.** Verified on a `g5.xlarge` (A10G, driver 580) running
the Deep Learning OSS Nvidia Driver AMI GPU PyTorch 2.7 (Ubuntu 22.04), `ami-012ba162b9cd2729c`,
with torch 2.7.0+cu128 and CUDA 12.8 (`docs/DECISIONS.md` D035):

    git clone https://github.com/ddshan/hand_object_detector
    cd hand_object_detector
    python3 /path/to/cyclegraph/scripts/detectors/patch_doh100.py .
    pip install scipy opencv-python-headless
    cd lib && TORCH_CUDA_ARCH_LIST="8.6" python setup.py build_ext --inplace

`patch_doh100.py` makes the custom CUDA ops compile against torch 2.x, across eight files: `Tensor.type()` returned a `DeprecatedTypeProperties`, and torch 2 wants
`scalar_type()` for dispatch and `is_cuda()` directly on the tensor. Without it the build fails
at `AT_DISPATCH_FLOATING_TYPES` with "cannot convert const at::DeprecatedTypeProperties to
c10::ScalarType". The patch touches no model logic and changes no numerics.

Point `DOH100_ROOT` at that clone and `DOH100_CHECKPOINT` at the weights.

**The weights are the open blocker, not the build.** The checkpoint
`faster_rcnn_1_8_132028.pth` is published only through a Google Drive link that now refuses
automated download, and no mirror was found on Hugging Face. `docs/METHOD.md` names EgoHOS as
the fallback if coverage fails H2c; it is not a fallback for a file that will not download.

Run `scripts/run_detector.py --smoke` before buying the full pilot: it measures the real frame
rate, which `docs/METHOD.md` E3 has only ever estimated.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Final

import numpy as np

from cyclegraph.signal.ports import HandBox, MaskSource

SCORE_THRESHOLD: Final[float] = 0.5
"""The paper's own operating point for hand detection. Not tuned here: a threshold chosen to
make coverage clear H2c would be choosing the answer, and H2c is a pre-registered gate."""

HAND_CLASS: Final[int] = 1
"""100DOH's class order is (background, targetobject, hand). Only hands are read."""


class Doh100Detector:
    """Loads once, detects per frame. Raises loudly rather than degrading."""

    def __init__(self, root: str | None = None, checkpoint: str | None = None,
                 device: str = "cuda") -> None:
        self._root = Path(root or os.environ.get("DOH100_ROOT", ""))
        self._checkpoint = Path(checkpoint or os.environ.get("DOH100_CHECKPOINT", ""))
        if not self._root.exists():
            raise RuntimeError(
                "DOH100_ROOT is unset or missing. This module does not fall back to another "
                "detector: CONTRACTS.md's mask_source is a closed enum and a box from "
                "anything else is a contract violation, not a substitution."
            )
        if not self._checkpoint.exists():
            raise RuntimeError(f"DOH100_CHECKPOINT not found at {self._checkpoint}")
        self._device = device
        self._model: Any = None

    @property
    def mask_source(self) -> MaskSource:
        return "100doh"

    def _load(self) -> Any:
        if self._model is not None:
            return self._model
        sys.path.insert(0, str(self._root / "lib"))
        import torch
        from model.faster_rcnn.resnet import resnet  # type: ignore[import-not-found]

        classes = ["__background__", "targetobject", "hand"]
        net = resnet(classes, 101, pretrained=False, class_agnostic=False)
        net.create_architecture()
        state = torch.load(self._checkpoint, map_location="cpu")
        net.load_state_dict(state["model"])
        net.to(self._device).eval()
        self._model = net
        return net

    def boxes(self, frame: np.ndarray) -> list[HandBox]:
        """Hand boxes for one greyscale frame, in that frame's own pixel coordinates.

        The caller scales them to native clip pixels; this returns what the model saw.
        """
        import torch

        net = self._load()
        rgb = np.repeat(frame[:, :, None], 3, axis=2).astype(np.float32)
        rgb -= np.array([102.9801, 115.9465, 122.7717], dtype=np.float32)  # the repo's means
        tensor = torch.from_numpy(rgb).permute(2, 0, 1).unsqueeze(0).to(self._device)
        info = torch.tensor([[frame.shape[0], frame.shape[1], 1.0]], device=self._device)
        empty = torch.zeros((1, 1, 5), device=self._device)
        with torch.no_grad():
            scores, boxes = net(tensor, info, empty, torch.zeros(1, device=self._device))[:2]
        scores_np = scores.squeeze(0).cpu().numpy()
        boxes_np = boxes.squeeze(0).cpu().numpy()
        out: list[HandBox] = []
        for i in range(scores_np.shape[0]):
            score = float(scores_np[i, HAND_CLASS])
            if score < SCORE_THRESHOLD:
                continue
            x1, y1, x2, y2 = (float(v) for v in boxes_np[i, HAND_CLASS * 4:(HAND_CLASS + 1) * 4])
            if x2 <= x1 or y2 <= y1:
                continue
            out.append(HandBox(x=x1, y=y1, width=x2 - x1, height=y2 - y1,
                               score=min(score, 1.0)))
        return out
