"""One valid and several invalid fixtures per record in `CONTRACTS.md`.

Every invalid fixture names the rule it breaks. Tests assert that each valid fixture
constructs and each invalid one raises; a record that could be built from an invalid fixture
would mean a contract rule is prose only.

HAL values are computed from the mappings, not typed in, so the fixture cannot carry a
transcribed number that the equations disagree with (AGENTS.md rule 2).
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any

from cyclegraph.exposure.hal import SCALE_REV, hal_akkas_2015, hal_radwin_2015

GENERATED = datetime(2026, 9, 5, tzinfo=timezone.utc)
REV = "3e5f87c8"

Fixture = dict[str, Any]
Broken = tuple[str, Fixture]


def _with(base: Fixture, **changes: Any) -> Fixture:
    out = deepcopy(base)
    out.update(changes)
    return out


CLIP_REF: Fixture = {
    "clip_id": "factory_001/worker_001/000123",
    "factory_id": "factory_001",
    "worker_id": "worker_001",
    "clip_index": 123,
    "shard": "factory_001/worker_001/shard-00007.tar",
    "byte_start": 512,
    "byte_end": 8419328,
    "duration_s": 187.4,
    "fps": 30.0,
    "width": 1920,
    "height": 1080,
    "codec": "h265",
    "corpus_rev": REV,
}

CLIP_REF_BROKEN: list[Broken] = [
    ("clip_id is not the composite", _with(CLIP_REF, clip_id="factory_001/worker_002/000123")),
    ("byte range inverted", _with(CLIP_REF, byte_end=100)),
    ("empty corpus_rev", _with(CLIP_REF, corpus_rev="")),
    ("unknown field", _with(CLIP_REF, sector="automotive")),
]

FRAME_SIGNAL: Fixture = {
    "clip_id": "factory_001/worker_001/000123",
    "corpus_rev": REV,
    "fps_sampled": 4.0,
    "n_frames": 12,
    "manipulation": [True, True, False, None, True, True, True, False, True, True, True, True],
    "hands_visible": [2, 2, 1, None, 2, 2, 1, 0, 2, 2, 2, 1],
    "hand_box_width_px": [212.0, 208.5, None, None, 210.0, 211.0, 205.0, None, 209.0, 208.0, 207.0, 206.0],
    "hand_mask_source": "100doh",
    "flow_method": "farneback",
    "label_source": "judge",
    "label_rev": "qwen3vl@abc",
    "prompt_variant": "P0b",
    "status": "ok",
    "n_unreadable": 1,
}

FRAME_SIGNAL_NOT_ATTEMPTED: Fixture = {
    "clip_id": "factory_001/worker_001/000123",
    "corpus_rev": REV,
    "fps_sampled": 4.0,
    "n_frames": 4,
    "manipulation": [None, None, None, None],
    "hands_visible": [None, None, None, None],
    "hand_box_width_px": [None, None, None, None],
    "hand_mask_source": "none",
    "flow_method": "none",
    "label_source": None,
    "label_rev": None,
    "prompt_variant": None,
    "status": "not_attempted",
    "n_unreadable": 4,
}

FRAME_SIGNAL_BROKEN: list[Broken] = [
    ("n_unreadable does not count the nulls", _with(FRAME_SIGNAL, n_unreadable=0)),
    ("series lengths disagree", _with(FRAME_SIGNAL, hands_visible=FRAME_SIGNAL["hands_visible"][:-1])),
    ("manipulation null without hands_visible null",
     _with(FRAME_SIGNAL, hands_visible=[2, 2, 1, 0, 2, 2, 1, 0, 2, 2, 2, 1])),
    ("manipulation with no visible hand",
     _with(FRAME_SIGNAL, hands_visible=[0, 2, 1, None, 2, 2, 1, 0, 2, 2, 2, 1])),
    ("a box where no hand is visible",
     _with(FRAME_SIGNAL, hand_box_width_px=[212.0, 208.5, None, None, 210.0, 211.0, 205.0, 200.0, 209.0, 208.0, 207.0, 206.0])),
    ("mask source none with a box width", _with(FRAME_SIGNAL, hand_mask_source="none")),
    ("label_source defaulted to an unknown value", _with(FRAME_SIGNAL, label_source="default")),
    ("not_attempted carrying label provenance",
     _with(FRAME_SIGNAL_NOT_ATTEMPTED, label_source="judge", label_rev="r", prompt_variant="p")),
    ("not_attempted with a scored instant",
     _with(FRAME_SIGNAL_NOT_ATTEMPTED, manipulation=[True, None, None, None],
           hands_visible=[2, None, None, None], n_unreadable=3)),
    ("not_attempted naming a detector", _with(FRAME_SIGNAL_NOT_ATTEMPTED, hand_mask_source="100doh")),
    ("null provenance without not_attempted",
     _with(FRAME_SIGNAL, label_source=None, label_rev=None, prompt_variant=None)),
    ("ok with more than 10% unreadable",
     _with(FRAME_SIGNAL, manipulation=[None, None, False, None, True, True, True, False, True, True, True, True],
           hands_visible=[None, None, 1, None, 2, 2, 1, 0, 2, 2, 2, 1],
           hand_box_width_px=[None, None, None, None, 210.0, 211.0, 205.0, None, 209.0, 208.0, 207.0, 206.0],
           n_unreadable=3)),
]

EXERTION_SEGMENT: Fixture = {
    "clip_id": "factory_001/worker_001/000123",
    "corpus_rev": REV,
    "start_s": 12.5,
    "end_s": 14.0,
    "method": "transitions",
    "min_duration_s": 0.5,
    "label_source": "judge",
}

EXERTION_SEGMENT_BROKEN: list[Broken] = [
    ("end before start", _with(EXERTION_SEGMENT, end_s=12.0)),
    ("primary path never segments", _with(EXERTION_SEGMENT, method="spectral")),
    ("debounce not the pre-registered 0.5 s", _with(EXERTION_SEGMENT, min_duration_s=0.25)),
    ("segment shorter than the debounce", _with(EXERTION_SEGMENT, end_s=12.75)),
]

DUTY_CYCLE: Fixture = {
    "clip_id": "factory_001/worker_001/000123",
    "corpus_rev": REV,
    "duty_cycle": 254 / 374,
    "n_frames_scored": 374,
    "n_frames_exerting": 254,
    "n_frames_excluded": 1,
    "label_source": "judge",
    "status": "ok",
}

DUTY_CYCLE_BROKEN: list[Broken] = [
    ("ratio does not match counts", _with(DUTY_CYCLE, duty_cycle=0.5)),
    ("null with status ok", _with(DUTY_CYCLE, duty_cycle=None)),
    ("value with status too_short", _with(DUTY_CYCLE, status="too_short")),
    ("exerting exceeds scored", _with(DUTY_CYCLE, n_frames_exerting=400, duty_cycle=400 / 374)),
    ("ok with more than 10% excluded", _with(DUTY_CYCLE, n_frames_excluded=80)),
]

FREQUENCY: Fixture = {
    "clip_id": "factory_001/worker_001/000123",
    "corpus_rev": REV,
    "label_source": "judge",
    "hz": 0.42,
    "method": "spectral",
    "peak_power_ratio": 6.1,
    "resolvable": True,
    "hz_ci95": [0.38, 0.47],
    "nyquist_hz": 2.0,
    "status": "ok",
}

FREQUENCY_NO_PEAK: Fixture = _with(
    FREQUENCY, hz=None, peak_power_ratio=2.1, resolvable=False, hz_ci95=None, status="no_peak"
)

FREQUENCY_BROKEN: list[Broken] = [
    ("zero assigned to an unresolvable clip", _with(FREQUENCY, hz=0.0, resolvable=False, hz_ci95=None)),
    ("at Nyquist but status ok", _with(FREQUENCY, hz=2.0, hz_ci95=None)),
    ("no_peak but resolvable", _with(FREQUENCY_NO_PEAK, resolvable=True)),
    ("no_peak with a peak above the floor", _with(FREQUENCY_NO_PEAK, peak_power_ratio=7.0)),
    ("ok with a spectral peak below the 6x floor", _with(FREQUENCY, peak_power_ratio=2.0)),
    ("ok with no peak ratio at all", _with(FREQUENCY, peak_power_ratio=None)),
    ("interval does not contain the estimate", _with(FREQUENCY, hz_ci95=[0.5, 0.6])),
    ("null hz with status ok", _with(FREQUENCY, hz=None, hz_ci95=None)),
    ("aliased but carrying a value", _with(FREQUENCY, hz=2.5, status="aliased", hz_ci95=None)),
]

HAND_SPEED: Fixture = {
    "clip_id": "factory_001/worker_001/000123",
    "corpus_rev": REV,
    "rms_speed_mm_s": 612.4,
    "n_samples": 749,
    "n_with_box": 688,
    "n_flow_null": 9,
    "coverage": 688 / 749,
    "flow_null_rate": 9 / 688,
    "hand_breadth_mm": 85.0,
    "median_box_width_px": 209.0,
    "mask_source": "100doh",
    "flow_method": "farneback",
    "ego_motion": "mask_complement_median",
    "status": "ok",
    "status_reason": None,
}

HAND_SPEED_LOW_COVERAGE: Fixture = _with(
    HAND_SPEED,
    rms_speed_mm_s=None,
    n_with_box=300,
    n_flow_null=3,
    coverage=300 / 749,
    flow_null_rate=3 / 300,
    status="low_coverage",
    status_reason="detector coverage 0.40 below the 0.60 floor",
)

HAND_SPEED_NO_DETECTOR: Fixture = _with(
    HAND_SPEED,
    rms_speed_mm_s=None, n_with_box=0, n_flow_null=0, coverage=0.0, flow_null_rate=0.0,
    median_box_width_px=None, mask_source=None, status="no_detector",
    status_reason="no detector ran on this clip",
)

HAND_SPEED_BROKEN: list[Broken] = [
    ("zero speed for a failed flow", _with(HAND_SPEED, n_flow_null=200, flow_null_rate=200 / 688, rms_speed_mm_s=0.0)),
    ("zero speed with status ok", _with(HAND_SPEED, rms_speed_mm_s=0.0)),
    ("ok below the coverage floor", _with(HAND_SPEED, n_with_box=300, n_flow_null=3, coverage=300 / 749, flow_null_rate=3 / 300)),
    ("coverage not the ratio", _with(HAND_SPEED, coverage=0.99)),
    ("region prior as a mask source", _with(HAND_SPEED, mask_source="region")),
    ("no_detector naming a detector", _with(HAND_SPEED_NO_DETECTOR, mask_source="100doh")),
    ("null mask source with a detector status", _with(HAND_SPEED, mask_source=None)),
    ("reason present with status ok", _with(HAND_SPEED, status_reason="fine")),
    ("no reason with a failure status", _with(HAND_SPEED_LOW_COVERAGE, status_reason=None)),
]

_D = 0.68
HAL_AKKAS: Fixture = {
    "clip_id": "factory_001/worker_001/000123",
    "corpus_rev": REV,
    "label_source": "judge",
    "hal": round(hal_akkas_2015(612.4, 100 * _D), 1),
    "mapping": "akkas-2015-speed-dc",
    "scale_rev": SCALE_REV["akkas-2015-speed-dc"],
    "duty_cycle": _D,
    "hz": None,
    "rms_speed_mm_s": 612.4,
    "out_of_range": False,
    "force_axis": None,
    "force_axis_reason": "peak force is not observable from video (docs/COVERAGE.md)",
    "tlv_evaluable": False,
    "status": "ok",
}

HAL_RADWIN: Fixture = _with(
    HAL_AKKAS, mapping="radwin-2015-freq-dc", scale_rev=SCALE_REV["radwin-2015-freq-dc"],
    hz=0.42, rms_speed_mm_s=None, hal=round(hal_radwin_2015(0.42, 100 * _D), 1),
)

HAL_OUT_OF_RANGE: Fixture = _with(
    HAL_RADWIN, hz=1.9, hal=round(hal_radwin_2015(1.9, 100 * _D), 1), out_of_range=True,
)

HAL_ZERO_DC: Fixture = _with(
    HAL_AKKAS, hal=None, duty_cycle=0.0, status="zero_duty_cycle",
)

HAL_BROKEN: list[Broken] = [
    ("akkas mapping without a speed", _with(HAL_AKKAS, rms_speed_mm_s=None)),
    ("radwin mapping without a frequency", _with(HAL_RADWIN, hz=None)),
    ("hal is not the mapping of its inputs", _with(HAL_AKKAS, hal=6.1)),
    ("out_of_range not derived", _with(HAL_RADWIN, hz=1.9, hal=round(hal_radwin_2015(1.9, 100 * _D), 1))),
    ("scale_rev for the other mapping", _with(HAL_AKKAS, scale_rev=SCALE_REV["radwin-2015-freq-dc"])),
    ("free-text scale_rev", _with(HAL_AKKAS, scale_rev="x")),
    ("zero speed mapped", _with(HAL_AKKAS, rms_speed_mm_s=0.0)),
    ("zero frequency mapped", _with(HAL_RADWIN, hz=0.0)),
    ("duty cycle zero with status ok", _with(HAL_AKKAS, duty_cycle=0.0)),
    ("force axis populated", _with(HAL_AKKAS, force_axis=3.0)),
    ("tlv marked evaluable", _with(HAL_AKKAS, tlv_evaluable=True)),
    ("unknown mapping", _with(HAL_AKKAS, mapping="cyclegraph-approx")),
    ("no label source", {k: v for k, v in HAL_AKKAS.items() if k != "label_source"}),
]

_MEAN = 4.11
_W_CLUSTER = 0.34
_DE = 1.44
_W_IID = _W_CLUSTER / (_DE**0.5)
AGGREGATE: Fixture = {
    "aggregate_id": "corpus-v1",
    "stratum": "corpus",
    "stratum_definition": "docs/DECISIONS.md#d019",
    "n_clips": 41230,
    "n_workers": 2144,
    "n_factories": 85,
    "max_factory_share_workers": 0.04,
    "max_factory_share_clips": 0.05,
    "mapping": "akkas-2015-speed-dc",
    "label_source": "probe",
    "hal_mean": _MEAN,
    "hal_ci95": [_MEAN - _W_CLUSTER / 2, _MEAN + _W_CLUSTER / 2],
    "hal_quantiles": {"p10": 2.1, "p50": 4.0, "p90": 6.7},
    "cluster_unit": "factory_id/worker_id",
    "weighting": "clip",
    "design_effect": _DE,
    "design_effect_width_ratio": _DE**0.5,
    "design_effect_mc_band": 0.05,
    "bootstrap_b": 10000,
    "seed": 777,
    "iid_ci95_for_contrast": [_MEAN - _W_IID / 2, _MEAN + _W_IID / 2],
    "aggregation_reason": "corpus-level; docs/ETHICS.md forbids any unit below the floor",
    "corpus_rev": REV,
    "generated": GENERATED,
}

AGGREGATE_STRATUM: Fixture = _with(
    AGGREGATE, aggregate_id="size-tercile-2-v1", stratum="size_tercile_2",
    n_clips=12000, n_workers=700, n_factories=28,
    max_factory_share_workers=0.11, max_factory_share_clips=0.14, weighting="worker",
)

AGGREGATE_BROKEN: list[Broken] = [
    ("factory_id field", _with(AGGREGATE, factory_id="factory_001")),
    ("worker_id field", _with(AGGREGATE, worker_id="worker_001")),
    ("identifier smuggled in the reason", _with(AGGREGATE, aggregation_reason="factory_007 only")),
    ("identifier smuggled in the id", _with(AGGREGATE, aggregate_id="worker_012")),
    ("identifier as a quantile key", _with(AGGREGATE, hal_quantiles={"factory_007": 4.0})),
    ("shard-style identifier", _with(AGGREGATE, aggregation_reason="from factory001_worker001_part00.tar")),
    ("capitalised identifier", _with(AGGREGATE, aggregation_reason="Factory_007")),
    ("identifier in the definition anchor", _with(AGGREGATE, stratum_definition="docs/DECISIONS.md#factory-007")),
    ("path traversal in the definition", _with(AGGREGATE, stratum_definition="docs/../results/x.md")),
    ("free-text stratum definition", _with(AGGREGATE_STRATUM, stratum_definition="the big ones")),
    ("stratum below the factory floor", _with(AGGREGATE_STRATUM, n_factories=4)),
    ("stratum below the worker floor", _with(AGGREGATE_STRATUM, n_workers=49)),
    ("one factory dominates by workers", _with(AGGREGATE_STRATUM, max_factory_share_workers=0.55)),
    ("one factory dominates by clips", _with(AGGREGATE_STRATUM, max_factory_share_clips=0.55)),
    ("stratum clip-weighted", _with(AGGREGATE_STRATUM, weighting="clip")),
    ("bare worker_id as cluster unit", _with(AGGREGATE, cluster_unit="worker_id")),
    ("width ratio not the square root", _with(AGGREGATE, design_effect_width_ratio=1.44)),
    ("design effect not its own intervals", _with(AGGREGATE, design_effect=3.5, design_effect_width_ratio=3.5**0.5)),
    ("interval does not contain the mean", _with(AGGREGATE, hal_ci95=[4.5, 4.8])),
    ("iid interval does not contain the mean", _with(AGGREGATE, iid_ci95_for_contrast=[4.5, 4.6])),
    ("bootstrap B not the pre-registered 10,000", _with(AGGREGATE, bootstrap_b=1)),
    ("naive timestamp", _with(AGGREGATE, generated=datetime(2026, 9, 5))),
    ("non-UTC timestamp", _with(AGGREGATE, generated=datetime(2026, 9, 5, tzinfo=timezone(timedelta(hours=5))))),
    ("no aggregation reason", _with(AGGREGATE, aggregation_reason="")),
    ("no label source", {k: v for k, v in AGGREGATE.items() if k != "label_source"}),
]

CLAIM: Fixture = {
    "id": "H3",
    "statement": "the corpus median HAL is plausible against the pooled cohort",
    "status": "UNTESTED",
    "source": "results/h3_plausibility.json",
    "interval": None,
    "pilot_gate": False,
}

PILOT_CLAIM: Fixture = {
    "id": "H1",
    "statement": "duty cycle is a property of the clip, not of the labeller",
    "status": "UNTESTED",
    "source": "results/pilot/h1.json",
    "interval": None,
    "pilot_gate": True,
}

CARD: Fixture = {
    "verdict": "NOT_VERIFIED",
    "generated": GENERATED,
    "corpus_rev": REV,
    "arm": None,
    "claims": [CLAIM, PILOT_CLAIM],
    "known_gaps": ["no expert agreement statistic", "peak force unobservable"],
}

CARD_BROKEN: list[Broken] = [
    ("verified with an untested claim", _with(CARD, verdict="VERIFIED", known_gaps=[])),
    ("verified with an open gap", _with(CARD, verdict="VERIFIED", claims=[_with(CLAIM, status="HOLDS"), _with(PILOT_CLAIM, status="HOLDS")])),
    ("pilot value reaching the card", _with(CARD, claims=[CLAIM, _with(PILOT_CLAIM, status="HOLDS", interval=[0.03, 0.04])])),
    ("pilot claim not gated", _with(CARD, claims=[CLAIM, _with(PILOT_CLAIM, pilot_gate=False)])),
    ("non-pilot claim gated", _with(CARD, claims=[_with(CLAIM, pilot_gate=True), PILOT_CLAIM])),
    ("source outside results/", _with(CARD, claims=[_with(CLAIM, source="docs/BENCHMARK.md"), PILOT_CLAIM])),
    ("identifier in a statement", _with(CARD, claims=[_with(CLAIM, statement="factory_003 is high"), PILOT_CLAIM])),
    ("duplicate claim ids", _with(CARD, claims=[CLAIM, CLAIM])),
    ("unknown status", _with(CARD, claims=[_with(CLAIM, status="PASSED"), PILOT_CLAIM])),
]

VALID: dict[str, list[Fixture]] = {
    "ClipRef": [CLIP_REF],
    "FrameSignal": [FRAME_SIGNAL, FRAME_SIGNAL_NOT_ATTEMPTED],
    "ExertionSegment": [EXERTION_SEGMENT],
    "DutyCycleEstimate": [DUTY_CYCLE, _with(DUTY_CYCLE, duty_cycle=None, status="too_short")],
    "FrequencyEstimate": [FREQUENCY, FREQUENCY_NO_PEAK],
    "HandSpeedEstimate": [HAND_SPEED, HAND_SPEED_LOW_COVERAGE, HAND_SPEED_NO_DETECTOR],
    "HALScore": [HAL_AKKAS, HAL_RADWIN, HAL_OUT_OF_RANGE, HAL_ZERO_DC],
    "ExposureAggregate": [AGGREGATE, AGGREGATE_STRATUM],
    "MeasurementCard": [CARD],
}

INVALID: dict[str, list[Broken]] = {
    "ClipRef": CLIP_REF_BROKEN,
    "FrameSignal": FRAME_SIGNAL_BROKEN,
    "ExertionSegment": EXERTION_SEGMENT_BROKEN,
    "DutyCycleEstimate": DUTY_CYCLE_BROKEN,
    "FrequencyEstimate": FREQUENCY_BROKEN,
    "HandSpeedEstimate": HAND_SPEED_BROKEN,
    "HALScore": HAL_BROKEN,
    "ExposureAggregate": AGGREGATE_BROKEN,
    "MeasurementCard": CARD_BROKEN,
}
