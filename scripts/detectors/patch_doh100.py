#!/usr/bin/env python3
"""Make 100DOH's custom CUDA ops compile against torch 2.x. `docs/DECISIONS.md` D035.

Run once inside a `hand_object_detector` clone, before `setup.py build_ext`:

    python3 patch_doh100.py ~/hand_object_detector

The change is entirely one deprecation. `Tensor.type()` used to return a
`DeprecatedTypeProperties`, which could be handed to `AT_DISPATCH_FLOATING_TYPES` and asked
`.is_cuda()`. Torch 2 wants `scalar_type()` for the dispatch and `is_cuda()` on the tensor
itself, so the build otherwise stops at::

    error: cannot convert 'const at::DeprecatedTypeProperties' to 'c10::ScalarType'

**No model logic and no numerics change.** That matters more than the convenience: a port that
altered the detector would make `mask_source: "100doh"` a claim about a model nobody published.

This is a substitution script rather than a committed `.diff` on purpose. A diff carries line
numbers and context, so it rots the moment upstream moves a line; these two replacements are
mechanical and version-independent. It is also idempotent -- running it twice changes nothing
the second time -- so a half-finished instance setup can simply be re-run.

Verified on `ami-012ba162b9cd2729c` (Deep Learning OSS Nvidia Driver AMI GPU PyTorch 2.7,
Ubuntu 22.04) with torch 2.7.0+cu128, CUDA 12.8, on an A10G.
"""

from __future__ import annotations

import sys
from pathlib import Path

SUBSTITUTIONS: tuple[tuple[str, str], ...] = (
    (".type().is_cuda()", ".is_cuda()"),
    (".type() ==", ".scalar_type() =="),
    (".type(), \"", ".scalar_type(), \""),
)

SOURCE_SUFFIXES = frozenset({".h", ".cpp", ".cu", ".cuh"})


def patch_tree(root: Path) -> list[str]:
    """Apply the substitutions under `lib/model/csrc`. Returns the files changed."""
    csrc = root / "lib" / "model" / "csrc"
    if not csrc.is_dir():
        raise SystemExit(f"not a hand_object_detector clone: {csrc} does not exist")
    changed: list[str] = []
    for path in sorted(csrc.rglob("*")):
        if path.suffix not in SOURCE_SUFFIXES:
            continue
        before = path.read_text()
        after = before
        for old, new in SUBSTITUTIONS:
            after = after.replace(old, new)
        if after != before:
            path.write_text(after)
            changed.append(str(path.relative_to(root)))
    return changed


def main(argv: list[str] | None = None) -> int:
    args = list(argv) if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print(__doc__)
        return 2
    changed = patch_tree(Path(args[0]).expanduser())
    if changed:
        print(f"patched {len(changed)} files for torch 2.x:")
        for name in changed:
            print(f"  {name}")
    else:
        print("nothing to patch; already applied, or upstream has fixed it")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
