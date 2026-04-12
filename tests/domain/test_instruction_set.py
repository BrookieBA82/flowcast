import pytest
from datetime import date
from libs.domain.instruction_set import InstructionSet, _SeriesInstructionSet
from libs.domain.cashflow import CashFlowInstruction
from libs.domain.recurrence import MonthlyRecurrence


def make_instruction(series_id="s1", start=date(2024, 1, 1), end=None, amount=100, monthly_day=1):
    return CashFlowInstruction(
        id=f"{series_id}-{start}",
        series_id=series_id,
        amount=amount,
        recurrence=MonthlyRecurrence([monthly_day]),
        start_date=start,
        end_date=end,
    )


def test_effective_instructions_single_contained_instruction():
    series = _SeriesInstructionSet([])

    i1 = make_instruction(start=date(2024, 1, 15), end=date(2024, 3, 31), amount=100)

    series.add_instruction(i1)

    results = series.effective_instructions_between(
        date(2024, 1, 1),
        date(2024, 4, 15),
    )

    assert len(results) == 1

    assert results[0].instruction.amount == 100
    assert results[0].start_date == date(2024, 1, 15)
    assert results[0].end_date == date(2024, 3, 31)

def test_effective_instructions_empty_series_returns_no_intervals():
    series = _SeriesInstructionSet([])

    results = series.effective_instructions_between(date(2024, 1, 1), date(2024, 1, 2))

    assert results == []

def test_effective_instructions_boundary_edge_conditions():
    series = _SeriesInstructionSet([])

    i1 = make_instruction(start=date(2024, 1, 1), end=date(2024, 2, 1),amount=100)
    i2 = make_instruction(start=date(2024, 2, 1), end=date(2024, 3, 1), amount=200)
    i3 = make_instruction(start=date(2024, 3, 1), end=date(2024, 4, 1), amount=300)

    series.add_instruction(i1)
    series.add_instruction(i2)
    series.add_instruction(i3)

    results = series.effective_instructions_between(
        date(2024, 1, 1),
        date(2024, 3, 1),
    )

    assert len(results) == 2

    assert results[0].instruction.amount == 100
    assert results[0].start_date == date(2024, 1, 1)
    assert results[0].end_date == date(2024, 2, 1)

    assert results[1].instruction.amount == 200
    assert results[1].start_date == date(2024, 2, 1)
    assert results[1].end_date == date(2024, 3, 1)


def test_effective_instructions_boundaries_clamped_properly():
    series = _SeriesInstructionSet([])

    i1 = make_instruction(start=date(2024, 1, 1), amount=100)
    i2 = make_instruction(start=date(2024, 2, 1), amount=200)

    series.add_instruction(i1)
    series.add_instruction(i2)

    results = series.effective_instructions_between(
        date(2024, 1, 15),
        date(2024, 2, 15),
    )

    assert len(results) == 2

    assert results[0].instruction.amount == 100
    assert results[0].start_date == date(2024, 1, 15)
    assert results[0].end_date == date(2024, 2, 1)

    assert results[1].instruction.amount == 200
    assert results[1].start_date == date(2024, 2, 1)
    assert results[1].end_date == date(2024, 2, 15)


def test_effective_instructions_instruction_end_date_respected():
    series = _SeriesInstructionSet([])

    i1 = make_instruction(start=date(2024, 1, 1), end=date(2024, 1, 15), amount=100)
    i2 = make_instruction(start=date(2024, 2, 1), end=date(2024, 2, 10), amount=200)

    series.add_instruction(i1)
    series.add_instruction(i2)

    results = series.effective_instructions_between(
        date(2024, 1, 15),
        date(2024, 2, 15),
    )

    assert len(results) == 1

    assert results[0].instruction.amount == 200
    assert results[0].start_date == date(2024, 2, 1)
    assert results[0].end_date == date(2024, 2, 10)


def test_effective_instructions_terminate_active_instruction():
    series = _SeriesInstructionSet([])

    i1 = make_instruction(start=date(2024, 1, 1), amount=100)

    series.add_instruction(i1)
    series.terminate_series(date(2024, 3, 1))

    results = series.effective_instructions_between(
        date(2024, 2, 1),
        date(2024, 4, 1),
    )

    assert len(results) == 1

    r = results[0]
    assert r.instruction.amount == 100
    assert r.start_date == date(2024, 2, 1)
    assert r.end_date == date(2024, 3, 1)


def test_effective_instructions_enforces_monotonic_order():
    series = _SeriesInstructionSet([])

    series.add_instruction(make_instruction(start=date(2024, 1, 10)))

    with pytest.raises(ValueError):
        series.add_instruction(make_instruction(start=date(2024, 1, 5)))


def test_effective_instructions_terminate_must_follow_last_boundary():
    series = _SeriesInstructionSet([])

    series.add_instruction(make_instruction(start=date(2024, 1, 10)))

    with pytest.raises(ValueError):
        series.terminate_series(date(2024, 1, 5))


def test_events_between_produces_expected_events():
    i1 = make_instruction(series_id="s1", start=date(2024, 1, 1), amount=100)
    i2 = make_instruction(series_id="s1", start=date(2024, 2, 1), amount=200)

    inst_set = InstructionSet({})
    inst_set.create_series(series_id="s1", instruction=i1)
    inst_set.update_series_from(series_id="s1", new_instruction=i2)

    events = inst_set.events_between(date(2024, 1, 1), date(2024, 2, 2))

    assert len(events) == 2

    e1, e2 = events

    assert e1.date == date(2024, 1, 1)
    assert e1.amount == 100
    assert e1.series_id == "s1"

    assert e2.date == date(2024, 2, 1)
    assert e2.amount == 200
    assert e2.series_id == "s1"


def test_events_between_multiple_series_are_combined_correctly():
    i1 = make_instruction(series_id="s1", start=date(2024, 1, 1), amount=100)
    i2 = make_instruction(series_id="s2", start=date(2024, 1, 1), monthly_day=2, amount=200)

    inst_set = InstructionSet({})
    inst_set.create_series(series_id="s1", instruction=i1)
    inst_set.create_series(series_id="s2", instruction=i2)

    events = inst_set.events_between(date(2024, 1, 1), date(2024, 2, 3))

    assert len(events) == 4

    e1, e2, e3, e4 = events

    assert e1.date == date(2024, 1, 1)
    assert e1.amount == 100
    assert e1.series_id == "s1"

    assert e2.date == date(2024, 1, 2)
    assert e2.amount == 200
    assert e2.series_id == "s2"

    assert e3.date == date(2024, 2, 1)
    assert e3.amount == 100
    assert e3.series_id == "s1"

    assert e4.date == date(2024, 2, 2)
    assert e4.amount == 200
    assert e4.series_id == "s2"


def test_events_between_respects_termination():
    i1 = make_instruction(series_id="s1", start=date(2024, 1, 1), amount=100)

    inst_set = InstructionSet({})
    inst_set.create_series(series_id="s1", instruction=i1)
    inst_set.terminate_series(series_id="s1", end_date=date(2024, 3, 1))

    events = inst_set.events_between(date(2024, 1, 1), date(2024, 6, 1))

    assert len(events) == 2

    e1, e2 = events

    assert e1.date == date(2024, 1, 1)
    assert e1.amount == 100
    assert e1.series_id == "s1"

    assert e2.date == date(2024, 2, 1)
    assert e2.amount == 100


def test_effective_instruction_at_single_series():
    i1 = make_instruction(series_id="s1", start=date(2024, 1, 1), end=date(2024, 1, 15), amount=100)
    i2 = make_instruction(series_id="s1", start=date(2024, 2, 1), amount=200)

    inst_set = InstructionSet({})
    inst_set.create_series(series_id="s1", instruction=i1)
    inst_set.update_series_from(series_id="s1", new_instruction=i2)
    inst_set.terminate_series(series_id="s1", end_date=date(2024, 3, 1))

    before_start = inst_set.effective_instruction(series_id="s1", at=date(2023, 12, 1))
    assert before_start is None

    first_range = inst_set.effective_instruction(series_id="s1", at=date(2024, 1, 1))
    assert first_range.series_id == "s1"
    assert first_range.amount == 100

    within_gap = inst_set.effective_instruction(series_id="s1", at=date(2024, 1, 15))
    assert within_gap is None

    second_range = inst_set.effective_instruction(series_id="s1", at=date(2024, 2, 1))
    assert second_range.series_id == "s1"
    assert second_range.amount == 200

    upon_termination = inst_set.effective_instruction(series_id="s1", at=date(2024, 3, 1))
    assert upon_termination is None
