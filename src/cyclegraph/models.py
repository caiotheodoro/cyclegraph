"""`CONTRACTS.md` (contracts/v1.1) as frozen pydantic models.

Every rule the contract states in prose is a validator here, so that a record which violates
the contract cannot be constructed rather than merely being frowned upon. The three rules:

1. Every record carries its provenance.
2. Absence is explicit: `null` with a sibling reason, never a silent zero.
3. Identifiers exist in records and never in aggregates — `ExposureAggregate` and
   `MeasurementCard` reject any string value anywhere in them that looks like one.

Changing a field is a `docs/DECISIONS.md` entry and a changelog row in `CONTRACTS.md`.
"""

from __future__ import annotations

import math
import re
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

CONTRACTS_REV = "contracts/v1.1"

# The corpus's own naming for the two things that must never reach a published number.
IDENTIFIER = re.compile(r"\b(factory_\d+|worker_\d+)\b")

# `docs/RUBRIC.md` "Hand speed" and `docs/PRE-REGISTRATION.md` H2c.
COVERAGE_FLOOR = 0.60
FLOW_NULL_CEILING = 0.10

# `docs/DECISIONS.md` D019.
K_FACTORIES_FLOOR = 5
K_WORKERS_FLOOR = 50
MAX_FACTORY_SHARE = 0.40

CI95 = Annotated[list[float], Field(min_length=2, max_length=2)]

LabelSource = Literal["judge", "probe", "human"]
Mapping = Literal["radwin-2015-freq-dc", "akkas-2015-speed-dc"]
Stratum = Literal["corpus", "size_tercile_1", "size_tercile_2", "size_tercile_3"]
ClaimStatus = Literal["UNTESTED", "HOLDS", "FAILED", "UNTESTED_ARM_B"]

_STRATUM_DEFINITION = re.compile(r"^docs/[A-Za-z0-9_./-]+\.md(#[a-z0-9-]+)?$")
_RESULTS_PATH = re.compile(r"^results/[A-Za-z0-9_./-]+$")


def _strings(obj: Any) -> list[str]:
    """Every string value reachable in a dumped record, for the identifier check."""
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        out: list[str] = []
        for v in obj.values():
            out.extend(_strings(v))
        return out
    if isinstance(obj, (list, tuple)):
        out = []
        for v in obj:
            out.extend(_strings(v))
        return out
    return []


def _ci_ok(ci: list[float]) -> bool:
    return ci[0] <= ci[1]


def _close(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol


class Record(BaseModel):
    """Frozen, closed, and strict. An unknown field is a contract violation, not a warning."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class ClipRef(Record):
    """One clip in the raw corpus. `clip_id` is the join key everywhere."""

    clip_id: str
    factory_id: str
    worker_id: str
    clip_index: int = Field(ge=0)
    shard: str
    byte_start: int = Field(ge=0)
    byte_end: int = Field(gt=0)
    duration_s: float = Field(gt=0)
    fps: float = Field(gt=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    codec: str = Field(min_length=1)
    corpus_rev: str = Field(min_length=1)

    @model_validator(mode="after")
    def _clip_id_is_the_composite(self) -> ClipRef:
        expected = f"{self.factory_id}/{self.worker_id}/{self.clip_index:06d}"
        if self.clip_id != expected:
            raise ValueError(f"clip_id must be {expected!r}, got {self.clip_id!r}")
        if self.byte_end <= self.byte_start:
            raise ValueError("byte_end must exceed byte_start")
        return self


class FrameSignal(Record):
    """The per-frame series for one clip at the analysis rate."""

    clip_id: str
    fps_sampled: float = Field(gt=0)
    n_frames: int = Field(ge=0)
    manipulation: list[bool | None]
    hands_visible: list[Literal[0, 1, 2] | None]
    hand_box_width_px: list[float | None]
    hand_mask_source: Literal["100doh", "egohos", "none"]
    flow_method: str = Field(min_length=1)
    label_source: LabelSource
    label_rev: str = Field(min_length=1)
    prompt_variant: str = Field(min_length=1)
    status: Literal["ok", "too_short", "no_labels", "decode_failed"]
    n_unreadable: int = Field(ge=0)

    @model_validator(mode="after")
    def _series_are_aligned_and_absence_is_counted(self) -> FrameSignal:
        n = self.n_frames
        if not (len(self.manipulation) == len(self.hands_visible) == len(self.hand_box_width_px) == n):
            raise ValueError("every series must have exactly n_frames entries")
        for m, h in zip(self.manipulation, self.hands_visible, strict=True):
            if (m is None) != (h is None):
                raise ValueError("manipulation and hands_visible are null together or not at all")
        unreadable = sum(1 for m in self.manipulation if m is None)
        if unreadable != self.n_unreadable:
            raise ValueError(f"n_unreadable is {self.n_unreadable} but {unreadable} frames are null")
        if self.hand_mask_source == "none" and any(w is not None for w in self.hand_box_width_px):
            raise ValueError("hand_mask_source 'none' cannot carry a box width")
        for w in self.hand_box_width_px:
            if w is not None and w <= 0:
                raise ValueError("a box width is positive or null")
        return self


class ExertionSegment(Record):
    """One bounded exertion. Produced only by the cross-check path."""

    clip_id: str
    start_s: float = Field(ge=0)
    end_s: float = Field(gt=0)
    method: Literal["transitions", "segmenter"]
    min_duration_s: float = Field(gt=0)
    label_source: LabelSource

    @model_validator(mode="after")
    def _ordered(self) -> ExertionSegment:
        if self.end_s <= self.start_s:
            raise ValueError("end_s must exceed start_s")
        return self


class DutyCycleEstimate(Record):
    """Fraction of scored frames labelled as exerting, one clip."""

    clip_id: str
    duty_cycle: float | None
    n_frames_scored: int = Field(ge=0)
    n_frames_exerting: int = Field(ge=0)
    n_frames_excluded: int = Field(ge=0)
    label_source: LabelSource
    status: Literal["ok", "too_short", "no_labels", "decode_failed"]

    @model_validator(mode="after")
    def _null_iff_not_ok_and_the_ratio_is_the_ratio(self) -> DutyCycleEstimate:
        if (self.duty_cycle is None) != (self.status != "ok"):
            raise ValueError("duty_cycle is null exactly when status is not 'ok'")
        if self.status == "ok":
            if self.n_frames_scored == 0:
                raise ValueError("status 'ok' needs scored frames")
            if self.n_frames_exerting > self.n_frames_scored:
                raise ValueError("n_frames_exerting cannot exceed n_frames_scored")
            assert self.duty_cycle is not None
            if not _close(self.duty_cycle, self.n_frames_exerting / self.n_frames_scored):
                raise ValueError("duty_cycle must equal n_frames_exerting / n_frames_scored")
        return self


class FrequencyEstimate(Record):
    """Manipulation-bout frequency, one clip, spectral path. `hz` is a lower bound on exertion
    frequency (`docs/DECISIONS.md` D014) and every consumer labels it so."""

    clip_id: str
    hz: float | None
    method: Literal["spectral", "transitions"]
    peak_power_ratio: float | None
    resolvable: bool
    hz_ci95: CI95 | None
    nyquist_hz: float = Field(gt=0)
    status: Literal["ok", "no_peak", "aliased", "too_short", "no_labels"]

    @model_validator(mode="after")
    def _unresolvable_is_a_value(self) -> FrequencyEstimate:
        if (self.hz is None) != (self.status != "ok"):
            raise ValueError("hz is null exactly when status is not 'ok'")
        if self.status == "ok":
            assert self.hz is not None
            if not self.resolvable:
                raise ValueError("status 'ok' requires resolvable")
            if self.hz <= 0:
                raise ValueError("hz must be positive")
            if self.hz >= self.nyquist_hz:
                raise ValueError("an estimate at or above Nyquist is status 'aliased', not 'ok'")
            if self.hz_ci95 is not None and not (
                _ci_ok(self.hz_ci95) and self.hz_ci95[0] <= self.hz <= self.hz_ci95[1]
            ):
                raise ValueError("hz_ci95 must be ordered and contain hz")
        if self.status == "no_peak" and self.resolvable:
            raise ValueError("status 'no_peak' means not resolvable")
        if self.hz is None and self.hz_ci95 is not None:
            raise ValueError("no interval without an estimate")
        return self


class HandSpeedEstimate(Record):
    """RMS residual hand speed, one clip, speed path. Never from a region prior."""

    clip_id: str
    rms_speed_mm_s: float | None
    n_samples: int = Field(gt=0)
    n_with_box: int = Field(ge=0)
    n_flow_null: int = Field(ge=0)
    coverage: float = Field(ge=0, le=1)
    flow_null_rate: float = Field(ge=0, le=1)
    hand_breadth_mm: float = Field(gt=0)
    median_box_width_px: float | None
    mask_source: Literal["100doh", "egohos"]
    flow_method: str = Field(min_length=1)
    ego_motion: Literal["mask_complement_median"]
    status: Literal["ok", "low_coverage", "no_detector", "flow_failed", "too_short"]
    status_reason: str | None

    @model_validator(mode="after")
    def _rates_are_the_rates_and_status_follows_them(self) -> HandSpeedEstimate:
        if (self.rms_speed_mm_s is None) != (self.status != "ok"):
            raise ValueError("rms_speed_mm_s is null exactly when status is not 'ok'")
        if (self.status_reason is None) != (self.status == "ok"):
            raise ValueError("status_reason is present exactly when status is not 'ok'")
        if self.n_with_box > self.n_samples or self.n_flow_null > self.n_with_box:
            raise ValueError("counts must nest: n_flow_null <= n_with_box <= n_samples")
        if not _close(self.coverage, self.n_with_box / self.n_samples):
            raise ValueError("coverage must equal n_with_box / n_samples")
        expected_null = self.n_flow_null / self.n_with_box if self.n_with_box else 0.0
        if not _close(self.flow_null_rate, expected_null):
            raise ValueError("flow_null_rate must equal n_flow_null / n_with_box")
        if self.status == "ok":
            assert self.rms_speed_mm_s is not None
            if self.rms_speed_mm_s < 0:
                raise ValueError("speed is non-negative")
            if self.coverage < COVERAGE_FLOOR:
                raise ValueError(f"coverage below {COVERAGE_FLOOR} is status 'low_coverage'")
            if self.flow_null_rate > FLOW_NULL_CEILING:
                raise ValueError(f"flow-null rate above {FLOW_NULL_CEILING} is status 'flow_failed'")
            if self.median_box_width_px is None or self.median_box_width_px <= 0:
                raise ValueError("status 'ok' needs a positive median box width for the scale")
        if self.status == "low_coverage" and self.coverage >= COVERAGE_FLOOR:
            raise ValueError("status 'low_coverage' contradicts coverage")
        if self.status == "flow_failed" and self.flow_null_rate <= FLOW_NULL_CEILING:
            raise ValueError("status 'flow_failed' contradicts flow_null_rate")
        return self


class HALScore(Record):
    """The Hand Activity Level axis, one clip. The force axis is structurally absent."""

    clip_id: str
    hal: float | None
    mapping: Mapping
    scale_rev: str = Field(min_length=1)
    duty_cycle: float = Field(ge=0, le=1)
    hz: float | None
    rms_speed_mm_s: float | None
    out_of_range: bool
    force_axis: None = None
    force_axis_reason: str = Field(min_length=1)
    tlv_evaluable: Literal[False] = False
    status: Literal["ok", "no_input"]

    @model_validator(mode="after")
    def _the_mapping_names_its_input(self) -> HALScore:
        if (self.hal is None) != (self.status != "ok"):
            raise ValueError("hal is null exactly when status is not 'ok'")
        if self.status == "ok":
            assert self.hal is not None
            if not 0 <= self.hal <= 10:
                raise ValueError("hal is on the 0-10 scale")
            if self.mapping == "radwin-2015-freq-dc" and self.hz is None:
                raise ValueError("mapping radwin-2015-freq-dc requires hz")
            if self.mapping == "akkas-2015-speed-dc" and self.rms_speed_mm_s is None:
                raise ValueError("mapping akkas-2015-speed-dc requires rms_speed_mm_s")
        return self


class ExposureAggregate(Record):
    """The published unit. No identifier field, and no identifier in any string."""

    aggregate_id: str = Field(min_length=1)
    stratum: Stratum
    stratum_definition: str
    n_clips: int = Field(gt=0)
    n_workers: int = Field(gt=0)
    n_factories: int = Field(gt=0)
    k_factories: int = Field(ge=K_FACTORIES_FLOOR)
    k_workers: int = Field(ge=K_WORKERS_FLOOR)
    max_factory_share: float = Field(ge=0, le=MAX_FACTORY_SHARE)
    mapping: Mapping
    hal_mean: float = Field(ge=0, le=10)
    hal_ci95: CI95
    hal_quantiles: dict[str, float]
    cluster_unit: Literal["factory_id/worker_id"]
    weighting: Literal["worker", "clip"]
    design_effect: float = Field(gt=0)
    design_effect_width_ratio: float = Field(gt=0)
    design_effect_mc_band: float = Field(ge=0)
    bootstrap_b: int = Field(gt=0)
    seed: int
    iid_ci95_for_contrast: CI95
    aggregation_reason: str = Field(min_length=1)
    corpus_rev: str = Field(min_length=1)
    generated: datetime

    @model_validator(mode="after")
    def _the_floor_is_in_the_schema(self) -> ExposureAggregate:
        if not _STRATUM_DEFINITION.match(self.stratum_definition):
            raise ValueError("stratum_definition must be a path under docs/, not free text")
        if self.k_factories != self.n_factories or self.k_workers != self.n_workers:
            raise ValueError("k_factories/k_workers must equal n_factories/n_workers")
        if self.stratum != "corpus" and self.weighting != "worker":
            raise ValueError("strata are worker-weighted")
        if not _ci_ok(self.hal_ci95) or not (self.hal_ci95[0] <= self.hal_mean <= self.hal_ci95[1]):
            raise ValueError("hal_ci95 must be ordered and contain hal_mean")
        if not _ci_ok(self.iid_ci95_for_contrast):
            raise ValueError("iid_ci95_for_contrast must be ordered")
        if not _close(self.design_effect_width_ratio, math.sqrt(self.design_effect), tol=1e-6):
            raise ValueError("design_effect_width_ratio must be sqrt(design_effect)")
        if self.generated.tzinfo is None:
            raise ValueError("generated must be timezone-aware UTC")
        for s in _strings(self.model_dump()):
            if IDENTIFIER.search(s):
                raise ValueError(f"an aggregate cannot carry an identifier: {s!r}")
        return self


class MeasurementClaim(Record):
    id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    status: ClaimStatus
    source: str
    interval: CI95 | None

    @model_validator(mode="after")
    def _source_is_under_results(self) -> MeasurementClaim:
        if not _RESULTS_PATH.match(self.source):
            raise ValueError("source must be a path under results/")
        if self.interval is not None and not _ci_ok(self.interval):
            raise ValueError("interval must be ordered")
        return self


class MeasurementCard(Record):
    """Generated, never written. `VERIFIED` only when nothing is untested and no gap is open."""

    verdict: Literal["NOT_VERIFIED", "VERIFIED"]
    generated: datetime
    corpus_rev: str = Field(min_length=1)
    arm: Literal["A", "B"] | None
    claims: list[MeasurementClaim]
    known_gaps: list[str]

    @model_validator(mode="after")
    def _verified_means_verified(self) -> MeasurementCard:
        open_claims = [c.id for c in self.claims if c.status in ("UNTESTED", "UNTESTED_ARM_B")]
        if self.verdict == "VERIFIED" and (open_claims or self.known_gaps):
            raise ValueError("VERIFIED requires no untested claim and no known gap")
        if self.generated.tzinfo is None:
            raise ValueError("generated must be timezone-aware UTC")
        ids = [c.id for c in self.claims]
        if len(ids) != len(set(ids)):
            raise ValueError("claim ids must be unique")
        for s in _strings(self.model_dump()):
            if IDENTIFIER.search(s):
                raise ValueError(f"a card cannot carry an identifier: {s!r}")
        return self
