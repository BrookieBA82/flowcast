from datetime import date
from libs.domain.cashflow import CashFlowSeries, CashFlowInstruction
from libs.domain.recurrence import MonthlyRecurrence,OneTimeRecurrence


def test_effective_range_basic():
    instr = CashFlowInstruction(
        id="i1",
        series_id="s1",
        account_id="a1",
        amount=100,
        recurrence=OneTimeRecurrence(date(2026, 1, 10)),
        start_date=date(2026, 1, 1),
        end_date=None,
    )

    result = instr.effective_range(date(2026, 1, 5), date(2026, 1, 20))
    assert result == (date(2026, 1, 5), date(2026, 1, 20))


def test_effective_range_no_overlap():
    instr = CashFlowInstruction(
        id="i1",
        series_id="s1",
        account_id="a1",
        amount=100,
        recurrence=OneTimeRecurrence(date(2026, 1, 10)),
        start_date=date(2026, 2, 1),
        end_date=None,
    )

    assert instr.effective_range(date(2026, 1, 1), date(2026, 1, 31)) is None


def test_events_respect_start_date():
    instr = CashFlowInstruction(
        id="i1",
        series_id="s1",
        account_id="a1",
        amount=100,
        recurrence=MonthlyRecurrence([1]),
        start_date=date(2026, 2, 1),
        end_date=None,
    )

    events = instr.events_between(date(2026, 1, 1), date(2026, 3, 31))

    assert [e.date for e in events] == [
        date(2026, 2, 1),
        date(2026, 3, 1),
    ]


def test_events_respect_end_date():
    instr = CashFlowInstruction(
        id="i1",
        series_id="s1",
        account_id="a1",
        amount=100,
        recurrence=MonthlyRecurrence([1]),
        start_date=date(2026, 1, 1),
        end_date=date(2026, 2, 15),
    )

    events = instr.events_between(date(2026, 1, 1), date(2026, 3, 31))

    assert [e.date for e in events] == [
        date(2026, 1, 1),
        date(2026, 2, 1),
    ]


def test_one_time_event_generation():
    instr = CashFlowInstruction(
        id="i1",
        series_id="s1",
        account_id="a1",
        amount=500,
        recurrence=OneTimeRecurrence(date(2026, 1, 10)),
        start_date=date(2026, 1, 1),
        end_date=None,
    )

    events = instr.events_between(date(2026, 1, 1), date(2026, 1, 31))

    assert len(events) == 1
    assert events[0].amount == 500


def test_series_filters_by_series_id():
    series = CashFlowSeries(id="s1", name="Test")

    instr1 = CashFlowInstruction(
        id="i1",
        series_id="s1",
        account_id="a1",
        amount=100,
        recurrence=MonthlyRecurrence([1]),
        start_date=date(2026, 1, 1),
        end_date=None,
    )

    instr2 = CashFlowInstruction(
        id="i2",
        series_id="s2",
        account_id="a1",
        amount=200,
        recurrence=MonthlyRecurrence([1]),
        start_date=date(2026, 1, 1),
        end_date=None,
    )

    events = series.events_for_series(
        [instr1, instr2],
        date(2026, 1, 1),
        date(2026, 1, 31),
    )

    assert all(e.series_id == "s1" for e in events)
    assert len(events) == 1


def test_series_sorts_events():
    series = CashFlowSeries(id="s1", name="Test")

    instr = CashFlowInstruction(
        id="i1",
        series_id="s1",
        account_id="a1",
        amount=100,
        recurrence=MonthlyRecurrence([15, 1]),
        start_date=date(2026, 1, 1),
        end_date=None,
    )

    events = series.events_for_series(
        [instr],
        date(2026, 1, 1),
        date(2026, 1, 31),
    )

    assert [e.date for e in events] == [
        date(2026, 1, 1),
        date(2026, 1, 15),
    ]


def test_instruction_versions_split_correctly():
    series = CashFlowSeries(id="s1", name="Paycheck")

    instr_old = CashFlowInstruction(
        id="i1",
        series_id="s1",
        account_id="a1",
        amount=1000,
        recurrence=MonthlyRecurrence([1]),
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 1),
    )

    instr_new = CashFlowInstruction(
        id="i2",
        series_id="s1",
        account_id="a1",
        amount=1200,
        recurrence=MonthlyRecurrence([1]),
        start_date=date(2026, 3, 1),
        end_date=None,
    )

    events = series.events_for_series(
        [instr_old, instr_new],
        date(2026, 1, 1),
        date(2026, 4, 30),
    )

    assert [(e.date, e.amount) for e in events] == [
        (date(2026, 1, 1), 1000),
        (date(2026, 2, 1), 1000),
        (date(2026, 3, 1), 1200),
        (date(2026, 4, 1), 1200),
    ]
