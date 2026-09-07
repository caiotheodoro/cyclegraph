"""H1 and H2 are conjunctions of their parts; this writes them from the parts' verdicts.

`docs/PRE-REGISTRATION.md` states H1 as two bounds and H2 as three, and a parent holds only if
every part does. That is a fact about the hypothesis and not a measurement, so it is derived
here rather than in `card/build.py` -- the card reads verdicts from `results/` and must not
compute any, or the artifact it generates would depend on logic that no measurement produced.

A parent whose parts are not all present is **UNTESTED**, never `HOLDS`: a conjunction over an
incomplete set is not satisfied, it is unevaluated. That is the same rule D052 and D053 arrived
at for gates over absent data.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PARENTS: dict[str, tuple[str, ...]] = {
    "h1": ("h1a", "h1b"),
    "h2": ("h2a", "h2b", "h2c"),
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", default="results/pilot")
    args = parser.parse_args(argv)
    out_dir = ROOT / args.dir

    for parent, parts in PARENTS.items():
        statuses: dict[str, str] = {}
        for part in parts:
            path = out_dir / f"{part}.json"
            if path.exists():
                statuses[part] = str(json.loads(path.read_text()).get("status", "UNTESTED"))
            else:
                statuses[part] = "UNTESTED"
        if any(s == "UNTESTED" for s in statuses.values()):
            status = "UNTESTED"
        elif all(s == "HOLDS" for s in statuses.values()):
            status = "HOLDS"
        else:
            status = "FAILED"
        (out_dir / f"{parent}.json").write_text(json.dumps({
            "claim": parent.upper(), "status": status, "parts": statuses,
            "note": ("a conjunction: the parent holds only if every part does, and is UNTESTED "
                     "while any part is, because a conjunction over an incomplete set is "
                     "unevaluated rather than satisfied"),
        }, indent=2) + "\n")
        print(f"  {parent.upper()}: {status}  from {statuses}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
