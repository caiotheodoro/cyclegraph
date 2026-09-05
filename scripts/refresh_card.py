#!/usr/bin/env python3
"""Regenerate `MEASUREMENT_CARD.json` from `results/`. `docs/METHOD.md` E9.

**Exits nonzero unless the verdict is `VERIFIED`, and in v1 the verdict cannot be `VERIFIED`.**
`docs/COVERAGE.md` lists inputs that are unobservable from video -- peak force above all -- and
the card's verdict is a consequence of that list rather than a setting. So a nonzero exit here
is the stage working. Anyone who "fixes" it has removed the only mechanism that stops the card
claiming more than the project has.

No value is passed in. Every claim names a file under `results/` and its verdict is read from
that file; a claim whose file does not exist is `UNTESTED`, which is what it is.

Usage:
    python3 scripts/refresh_card.py
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cyclegraph.card.build import ClaimSource, build_card  # noqa: E402

PILOT_REV = "3e5f87c88c54ce8343865d8e2a8c171f18385a05"

CLAIMS: tuple[ClaimSource, ...] = (
    ClaimSource("H1", "duty cycle is a property of the clip, not of the labeller",
                "results/pilot/h1.json"),
    ClaimSource("H1a", "duty cycle agrees across label sources", "results/pilot/h1a.json"),
    ClaimSource("H1b", "duty cycle agrees across sampling rates", "results/pilot/h1b.json"),
    ClaimSource("H2", "exertion frequency is recoverable without segmenting exertions",
                "results/pilot/h2.json"),
    ClaimSource("H2a", "spectral and transition-counting frequency agree",
                "results/pilot/h2a.json"),
    ClaimSource("H2b", "enough clips carry a resolvable dominant cycle",
                "results/pilot/h2b.json"),
    ClaimSource("H2c", "detector coverage and flow-null rate clear their bounds",
                "results/pilot/h2c.json"),
    ClaimSource("H3", "the corpus median HAL is plausible against the pooled cohort",
                "results/h3_plausibility.json"),
    ClaimSource("H4", "exposure structure is between sites, not between people",
                "results/h4_variance.json"),
    ClaimSource("H5", "clip observations are not independent", "results/h5_design_effect.json"),
    ClaimSource("NC-dc", "the pipeline separates factory work from non-factory work on duty "
                         "cycle", "results/nc_duty_cycle.json"),
    ClaimSource("NC-f", "the pipeline separates factory work from kitchen work on the speed "
                        "path", "results/nc_frequency.json"),
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="MEASUREMENT_CARD.json")
    parser.add_argument("--corpus-rev", default=PILOT_REV)
    parser.add_argument("--arm", default=None, choices=["A", "B"])
    args = parser.parse_args(argv)

    card = build_card(
        CLAIMS,
        results_root=ROOT / "results",
        coverage_md=ROOT / "docs" / "COVERAGE.md",
        corpus_rev=args.corpus_rev,
        generated=datetime.now(timezone.utc),
        arm=args.arm,
    )
    (ROOT / args.out).write_text(card.model_dump_json(indent=2) + "\n")

    print(f"wrote {args.out}")
    print(f"  verdict: {card.verdict}")
    untested = [c.id for c in card.claims if c.status in ("UNTESTED", "UNTESTED_ARM_B")]
    print(f"  claims: {len(card.claims)} ({len(untested)} untested)")
    print(f"  known gaps: {len(card.known_gaps)}")
    for gap in card.known_gaps:
        print(f"    - {gap}")
    if card.verdict != "VERIFIED":
        print(
            "\nExiting nonzero because the verdict is not VERIFIED. This is the stage "
            "working:\ndocs/COVERAGE.md lists inputs that cannot be observed from video, so "
            "in v1 the verdict\nis NOT_VERIFIED by construction. Do not 'fix' this.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
