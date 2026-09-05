"""`CONTRACTS.md` in code: every prose rule is a validator, and these tests are the proof.

Offline, no network, fixtures only.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from cyclegraph import models
from tests import fixtures

RECORDS: dict[str, type[BaseModel]] = {
    "ClipRef": models.ClipRef,
    "FrameSignal": models.FrameSignal,
    "ExertionSegment": models.ExertionSegment,
    "DutyCycleEstimate": models.DutyCycleEstimate,
    "FrequencyEstimate": models.FrequencyEstimate,
    "HandSpeedEstimate": models.HandSpeedEstimate,
    "HALScore": models.HALScore,
    "ExposureAggregate": models.ExposureAggregate,
    "MeasurementCard": models.MeasurementCard,
}


def _valid_cases() -> list[tuple[str, dict[str, Any]]]:
    return [(name, fx) for name, fxs in fixtures.VALID.items() for fx in fxs]


def _invalid_cases() -> list[tuple[str, str, dict[str, Any]]]:
    return [(name, why, fx) for name, cases in fixtures.INVALID.items() for why, fx in cases]


def test_every_record_in_the_contract_has_a_model_and_a_fixture() -> None:
    assert set(RECORDS) == set(fixtures.VALID) == set(fixtures.INVALID)


@pytest.mark.parametrize(("name", "fx"), _valid_cases())
def test_valid_fixture_constructs_and_round_trips(name: str, fx: dict[str, Any]) -> None:
    model = RECORDS[name]
    rec = model.model_validate(fx)
    again = model.model_validate_json(rec.model_dump_json())
    assert again == rec


@pytest.mark.parametrize(("name", "why", "fx"), _invalid_cases(), ids=lambda v: v if isinstance(v, str) else "")
def test_invalid_fixture_is_rejected(name: str, why: str, fx: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        RECORDS[name].model_validate(fx)


@pytest.mark.parametrize(("name", "fx"), _valid_cases())
def test_records_are_frozen(name: str, fx: dict[str, Any]) -> None:
    rec = RECORDS[name].model_validate(fx)
    first = next(iter(fx))
    with pytest.raises(ValidationError):
        setattr(rec, first, getattr(rec, first))


@pytest.mark.parametrize(("name", "fx"), _valid_cases())
def test_unknown_fields_are_a_contract_violation(name: str, fx: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        RECORDS[name].model_validate({**fx, "unexpected": 1})


def test_no_aggregate_field_can_carry_an_identifier() -> None:
    """Rule 3 by reflection: the schema has no field whose name could hold one."""
    for field in models.ExposureAggregate.model_fields:
        assert "factory_id" not in field and "worker_id" not in field, field
    for field in models.MeasurementCard.model_fields:
        assert "factory_id" not in field and "worker_id" not in field, field


def test_no_aggregate_string_can_carry_an_identifier() -> None:
    """Rule 3 by value: every string-typed field is tried with an identifier and rejected."""
    base = fixtures.AGGREGATE
    string_fields = [k for k, v in base.items() if isinstance(v, str)]
    assert string_fields, "the fixture should have string fields to test"
    for k in string_fields:
        with pytest.raises(ValidationError):
            models.ExposureAggregate.model_validate({**base, k: f"{base[k]} factory_042"})


def test_the_force_axis_cannot_be_populated_by_any_route() -> None:
    for value in (0.0, 3.0, "3", True):
        with pytest.raises(ValidationError):
            models.HALScore.model_validate({**fixtures.HAL_AKKAS, "force_axis": value})
    with pytest.raises(ValidationError):
        models.HALScore.model_validate({**fixtures.HAL_AKKAS, "tlv_evaluable": True})


def test_unresolvable_frequency_is_a_value_not_zero() -> None:
    rec = models.FrequencyEstimate.model_validate(fixtures.FREQUENCY_NO_PEAK)
    assert rec.hz is None and rec.status == "no_peak" and not rec.resolvable


def test_speed_floors_match_the_rubric() -> None:
    assert models.COVERAGE_FLOOR == 0.60
    assert models.FLOW_NULL_CEILING == 0.10
    assert models.K_FACTORIES_FLOOR == 5
    assert models.K_WORKERS_FLOOR == 50
    assert models.MAX_FACTORY_SHARE == 0.40


def test_identifier_pattern_matches_the_corpus_naming_and_not_the_cluster_unit() -> None:
    assert models.IDENTIFIER.search("factory_007") is not None
    assert models.IDENTIFIER.search("worker_001") is not None
    assert models.IDENTIFIER.search("factory_id/worker_id") is None
