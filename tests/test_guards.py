"""The guards added under D064-D066, each exercised rather than asserted in prose.

Three fresh-context reviews found defects in fixes, and the fourth observed that five of the
six behaviours the third round claimed were shipped with no test. Two of its four SERIOUS
findings were in exactly those untested paths. This file is that gap closed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_signal  # noqa: E402
import run_labeller  # noqa: E402

from cyclegraph.signal.frames import contradiction_reason  # noqa: E402
from cyclegraph.signal.ports import FrameLabel  # noqa: E402

REV = "3e5f87c88c54ce8343865d8e2a8c171f18385a05"


def _manifest(path: Path) -> None:
    path.write_text(json.dumps({
        "factory_id": "factory_001", "worker_id": "worker_001", "clip_index": 0,
        "shard": "f/w/p.tar", "byte_start": 1, "byte_end": 2, "duration_s": 180.0,
        "fps": 30.0, "width": 1920, "height": 1080, "codec": "h264",
    }) + "\n")


def test_the_placeholder_writer_is_idempotent_but_will_not_overwrite_a_measurement(
        tmp_path: Path) -> None:
    """Size alone made the flag refuse its own output, and the remedy it printed was wrong:
    `results/pilot` is where the card reads, so "use a different --out-dir" is not available.
    What must be protected is a measurement, not a byte count (D066)."""
    manifest = tmp_path / "m.jsonl"
    _manifest(manifest)
    out = tmp_path / "out"
    args = ["--manifest", str(manifest), "--detections", "/dev/null", "--labels", "/dev/null",
            "--record-not-attempted", "--out-dir", str(out), "--corpus-rev", REV]
    assert build_signal.main(args) == 0
    assert build_signal.main(args) == 0          # its own placeholders: overwriting is fine

    # A record from a stage that ran must stop it.
    speeds = out / "hand_speed.jsonl"
    rows = speeds.read_text().splitlines()
    measured = json.loads(rows[0])
    measured.update(status="ok", n_with_box=10, coverage=1.0, flow_null_rate=0.0,
                    rms_speed_mm_s=100.0, median_box_width_px=190.0, mask_source="egohos",
                    n_samples=10, n_flow_null=0)
    speeds.write_text(json.dumps(measured) + "\n")
    assert build_signal.main(args) == 2
    assert speeds.read_text().strip()            # untouched


def test_the_rate_guard_is_exact_at_rates_whose_period_does_not_terminate(
        tmp_path: Path) -> None:
    """Rounding the gap made `1/round(1/fps, 6)` disagree with `fps`: 6 Hz inferred as
    5.999988, 3 Hz as 3.000003. The guard then refused a resume of a file the run itself
    wrote. Exact at 4 and 8 Hz, which is the only reason it went unnoticed (D066)."""
    for fps in (3.0, 4.0, 6.0, 8.0, 12.0, 30.0):
        path = tmp_path / f"{fps}.jsonl"
        path.write_text("".join(json.dumps({
            "clip_id": "factory_001/worker_001/000000", "t_s": i / fps,
            "label_source": "probe", "manipulation": True, "hands_visible": 2,
        }) + "\n" for i in range(12)))
        assert run_labeller.rate_of(path) == fps, f"{fps} Hz inferred wrongly"


def test_the_two_reasons_a_box_is_dropped_are_not_the_same_reason() -> None:
    """`docs/BENCHMARK.md` gives them separate rows so a reader need not guess which happened.
    The first version used `box_is_contradicted`, true for an unreadable frame as well, and
    attributed a statement to the labeller it never made (D065)."""
    no_hand = contradiction_reason(FrameLabel(manipulation=False, hands_visible=0))
    unreadable = contradiction_reason(
        FrameLabel(manipulation=None, hands_visible=None, unreadable_reason="decode failed"))
    kept = contradiction_reason(FrameLabel(manipulation=True, hands_visible=2))

    assert no_hand is not None and "no visible hand" in no_hand
    assert unreadable is not None and "could not read" in unreadable
    assert no_hand != unreadable
    assert kept is None


def test_a_clip_this_manifest_does_not_name_is_left_alone(tmp_path: Path) -> None:
    """Resume deletes rows for clips it judges partial. A clip another shard wrote into a
    shared output is not this run's to judge, and `expected.get(cid)` returning None made it
    look partial every time (D065)."""
    path = tmp_path / "labels.jsonl"
    mine, foreign = "factory_001/worker_001/000000", "factory_002/worker_009/000004"
    path.write_text("".join(json.dumps({
        "clip_id": cid, "t_s": i * 0.25, "label_source": "probe",
        "manipulation": True, "hands_visible": 2,
    }) + "\n" for cid in (mine, foreign) for i in range(4)))

    have = run_labeller.rows_per_clip(path)
    expected = {mine: 4}                          # only this manifest's clip
    complete = {cid for cid, n in have.items() if n == expected.get(cid)}
    partial = {cid for cid in have if cid in expected and cid not in complete}
    assert complete == {mine}
    assert partial == set()                       # the foreign clip is not deleted
    assert foreign in have


def test_a_falsified_part_falsifies_the_conjunction_even_with_a_part_unmeasured(
        tmp_path: Path) -> None:
    """`docs/PRE-REGISTRATION.md` states H1 as "falsified if *either* bound is exceeded". The
    first roll-up returned UNTESTED whenever any part was, which would have reported H1 as open
    on a corpus that had already falsified it -- and H1's failure is what selects Arm B.

    Fixed before H1b's result existed; adjusting it afterwards would have been the post-hoc
    move this project refuses (D067)."""
    import roll_up_claims

    def verdicts(h1a: str, h1b: str) -> str:
        for name, status in (("h1a", h1a), ("h1b", h1b)):
            (tmp_path / f"{name}.json").write_text(json.dumps({"status": status}))
        roll_up_claims.main(["--dir", str(tmp_path)])
        return str(json.loads((tmp_path / "h1.json").read_text())["status"])

    assert verdicts("UNTESTED", "FAILED") == "FAILED"    # one bound exceeded is enough
    assert verdicts("FAILED", "UNTESTED") == "FAILED"
    assert verdicts("UNTESTED", "HOLDS") == "UNTESTED"   # holding needs the whole set
    assert verdicts("HOLDS", "HOLDS") == "HOLDS"
    assert verdicts("HOLDS", "FAILED") == "FAILED"
