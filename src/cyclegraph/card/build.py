"""Assemble `MeasurementCard` from what is on disk. `docs/METHOD.md` E9.

Three rules, all of which exist because a card is the one artifact a reader is likely to take
at face value:

**Generated, never written.** Every claim cites a path under `results/` and this module reads
it; there is no parameter through which a value can be supplied by hand.

**The verdict is a consequence, not a setting.** `VERIFIED` requires that no claim is untested
*and* that `docs/COVERAGE.md` lists no open gap. In v1 the second is false by construction --
the force axis is unobservable -- so the verdict is `NOT_VERIFIED` and `make card` exits
nonzero. **That nonzero exit is the wave succeeding**, and anyone who "fixes" it has broken
the only mechanism preventing the card from claiming more than the project has.

**Pilot-gated claims publish pass or fail and never a value.** The pilot factory is nameable,
so an H1 mean absolute difference or an H2 agreement figure is a per-factory number (D018).
The schema enforces it; this module does not try to work around it.

The known gaps are parsed out of `docs/COVERAGE.md` rather than restated here, so a gap that
closes in the coverage table closes on the card, and one that opens there opens here.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Final

from cyclegraph.models import PILOT_GATED_CLAIMS, ClaimStatus, MeasurementCard, MeasurementClaim

_GAP_ROW = re.compile(r"^\|\s*\*\*(?P<name>[^|*]+?)\*\*\s*\|\s*\*\*(?P<status>[^|]*?)\*\*\s*\|")
_UNOBSERVABLE: Final[str] = "Unobservable"


def known_gaps(coverage_md: Path) -> list[str]:
    """Every input `docs/COVERAGE.md` marks unobservable, in the coverage table's own words.

    Parsed rather than restated: a gap that closes in the table closes on the card, and one
    that opens there opens here. A card whose gap list was a literal in this file would drift
    from the document it claims to summarise, which is the transcription problem one level up.
    """
    gaps: list[str] = []
    for line in coverage_md.read_text().splitlines():
        match = _GAP_ROW.match(line)
        if match and _UNOBSERVABLE in match.group("status"):
            gaps.append(match.group("name").strip())
    if not gaps:
        raise ValueError(
            "no unobservable input found in the coverage table; either the table changed "
            "shape or the parse is wrong, and a card with an empty gap list would read as a "
            "project with nothing missing"
        )
    return gaps


@dataclass(frozen=True, slots=True)
class ClaimSource:
    """A claim and the file that decides it. The value is never passed in."""

    id: str
    statement: str
    source: str


def read_claim(claim: ClaimSource, results_root: Path) -> MeasurementClaim:
    """Read one claim's verdict from its own result file.

    A missing file is `UNTESTED`, which is the truth: nothing has produced that number. It is
    not an error, because most of this card is untested for most of the project's life.
    """
    pilot_gated = claim.id in PILOT_GATED_CLAIMS
    path = results_root / Path(claim.source).relative_to("results")
    status: ClaimStatus = "UNTESTED"
    interval: list[float] | None = None
    if path.exists():
        payload = json.loads(path.read_text())
        raw = str(payload.get("status", "UNTESTED"))
        if raw not in ("UNTESTED", "HOLDS", "FAILED", "UNTESTED_ARM_B"):
            raise ValueError(f"{claim.source} carries an unknown claim status {raw!r}")
        status = raw  # type: ignore[assignment]
        if not pilot_gated and isinstance(payload.get("interval"), list):
            interval = [float(v) for v in payload["interval"]]
    return MeasurementClaim(
        id=claim.id, statement=claim.statement, status=status,
        source=claim.source, interval=interval, pilot_gate=pilot_gated,
    )


def build_card(
    claims: Sequence[ClaimSource], *, results_root: Path, coverage_md: Path,
    corpus_rev: str, generated: datetime, arm: str | None = None,
) -> MeasurementCard:
    """The card. The verdict follows from the claims and the gaps; it is not an argument."""
    read = [read_claim(c, results_root) for c in claims]
    gaps = known_gaps(coverage_md)
    untested = [c.id for c in read if c.status in ("UNTESTED", "UNTESTED_ARM_B")]
    return MeasurementCard(
        verdict="VERIFIED" if not untested and not gaps else "NOT_VERIFIED",
        generated=generated,
        corpus_rev=corpus_rev,
        arm=arm,  # type: ignore[arg-type]
        claims=read,
        known_gaps=gaps,
    )
