import pytest
from datetime import date

from libs.domain.cashflow import CashFlowEvent
from libs.domain.balance import Account, BalancePoint
from libs.domain.settlement import SettlementLog
from libs.domain.resolution import EventResolver


def make_event(eid, account_id="a1", d=date(2024, 1, 1), amount=100):
    return CashFlowEvent(
        series_id="s1",
        account_id=account_id,
        instruction_id=eid,
        date=d,
        amount=amount)


def make_account_map():
    return {
        "a1": Account("a1", "Checking", 1000),
        "a2": Account("a2", "Savings", 5000),
    }


def test_resolve_detects_uncleared_past_events():
    log = SettlementLog()

    e1, e2 = [
        make_event("e1", d=date(2024, 1, 1)),
        make_event("e2", d=date(2024, 1, 2)),
    ]

    log.clear(e1.id, "a1", date(2024, 1, 3), 100)

    resolver = EventResolver(log, start=date(2024, 1, 5), end=date(2024, 2, 5))
    with pytest.raises(ValueError):
        resolver.resolve(make_account_map(), [e1, e2])


def test_normalize_and_resolve_defers_uncleared_past_events():
    log = SettlementLog()

    e1, e2 = [
        make_event("e1", d=date(2024, 1, 1), amount=100),
        make_event("e2", d=date(2024, 1, 2), amount=200),
    ]

    log.clear(e1.id, "a1", date(2024, 1, 3), 100)

    resolver = EventResolver(log, start=date(2024, 1, 5), end=date(2024, 2, 5))
    resolved = resolver.normalize_and_resolve(make_account_map(), [e1, e2])

    account_state = resolved.account_states["a1"]
    balance_points = resolved.balance_points["a1"]

    assert account_state.balance == 1100
    assert account_state.as_of == date(2024, 1, 4)
    assert balance_points == [BalancePoint(date(2024, 1, 5), 1300)]


def test_resolve_computes_account_state_from_cleared_events():
    accounts = {
        "a1": Account("a1", "Checking", 1000),
    }

    e1, e2 = [
        make_event("e1", d=date(2024, 1, 1), amount=100),
        make_event("e2", d=date(2024, 1, 2), amount=-50),
    ]

    log = SettlementLog()
    log.clear(e1.id, "a1", date(2024, 1, 3), 100)
    log.clear(e2.id, "a1", date(2024, 1, 3), -50)

    resolver = EventResolver(log, start=date(2024, 2, 1), end=date(2024, 3, 1))
    resolved = resolver.resolve(accounts, [e1, e2])

    account_state = resolved.account_states["a1"]

    assert account_state.balance == 1050
    assert account_state.as_of == date(2024, 1, 31)


def test_resolve_projects_future_events_with_clearing():
    accounts = {
        "a1": Account("a1", "Checking", 1000),
    }

    e1, e2 = [
        make_event("e1", d=date(2024, 1, 1), amount=100),
        make_event("e2", d=date(2024, 2, 1), amount=200),
    ]

    log = SettlementLog()
    log.clear(e1.id, "a1", date(2024, 1, 2), 100)

    resolver = EventResolver(log, start=date(2024, 2, 1), end=date(2024, 3, 1))
    resolved = resolver.resolve(accounts, [e1, e2])

    balance_points = resolved.balance_points["a1"]

    assert len(balance_points) == 1
    assert balance_points[0].date == date(2024, 2, 1)
    assert balance_points[0].balance == 1300


def test_normalize_and_resolve_handles_multiple_accounts_independently():
    accounts = {
        "a1": Account("a1", "Checking", 1000),
        "a2": Account("a2", "Savings", 5000),
    }

    e1, e2, e3, e4, e5, e6 = [
        make_event("e1", account_id="a1", d=date(2024, 1, 1), amount=100),
        make_event("e2", account_id="a2", d=date(2024, 1, 1), amount=200),
        make_event("e3", account_id="a1", d=date(2024, 1, 15), amount=100),
        make_event("e4", account_id="a2", d=date(2024, 1, 15), amount=200),
        make_event("e5", account_id="a1", d=date(2024, 2, 15), amount=100),
        make_event("e6", account_id="a2", d=date(2024, 2, 15), amount=200),
    ]

    log = SettlementLog()
    log.clear(e1.id, "a1", date(2024, 1, 2), 100)
    log.clear(e2.id, "a2", date(2024, 1, 2), 200)

    resolver = EventResolver(log, start=date(2024, 2, 1), end=date(2024, 3, 1))
    resolved = resolver.normalize_and_resolve(accounts, [e1, e2, e3, e4, e5, e6])

    assert resolved.account_states["a1"].balance == 1100
    assert resolved.account_states["a1"].as_of == date(2024, 1, 31)
    assert resolved.account_states["a2"].balance == 5200
    assert resolved.account_states["a2"].as_of == date(2024, 1, 31)

    bp_1_1, bp_1_2 = resolved.balance_points["a1"]
    bp_2_1, bp_2_2 = resolved.balance_points["a2"]

    assert bp_1_1.date == date(2024, 2, 1)
    assert bp_1_1.balance == 1200

    assert bp_1_2.date == date(2024, 2, 15)
    assert bp_1_2.balance == 1300

    assert bp_2_1.date == date(2024, 2, 1)
    assert bp_2_1.balance == 5400

    assert bp_2_2.date == date(2024, 2, 15)
    assert bp_2_2.balance == 5600


def test_normalize_before_start_defers_uncleared_past_events():
    log = SettlementLog()

    e1, e2, e3 = [
        make_event("e1", d=date(2024, 1, 1)),
        make_event("e2", d=date(2024, 1, 2)),
        make_event("e3", d=date(2024, 1, 5)),
    ]

    log.clear(e1.id, "a1", date(2024, 1, 3), 100)

    resolver = EventResolver(log, start=date(2024, 1, 5), end=date(2024, 2, 5))
    deferred = resolver.normalize_before_start([e1, e2, e3])

    assert len(deferred) == 1
    assert deferred[0].date == date(2024, 1, 5)
    assert deferred[0].orig_date == date(2024, 1, 2)

