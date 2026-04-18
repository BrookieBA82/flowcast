from datetime import date

import pytest

from libs.domain.balance import BalanceProjection, Account, AccountState
from libs.domain.cashflow import CashFlowEvent


def event(series_id="s1", account_id="a1", date_=date(2024, 1, 1), amount=100):
    return CashFlowEvent(
        series_id=series_id,
        account_id=account_id,
        instruction_id=f"{series_id}-{date_}",
        date=date_,
        amount=amount,
    )


def test_basic_accumulation_no_state():
    account = Account(id="a1", name="Checking", starting_balance=1000)

    events = [
        event(date_=date(2024, 1, 1), amount=100),
        event(date_=date(2024, 1, 2), amount=-50),
        event(date_=date(2024, 1, 3), amount=200),
    ]

    proj = BalanceProjection({"a1": account}, events)

    points = proj.balances_for_account("a1", date(2024, 1, 1), date(2024, 1, 10))

    assert [(p.date, p.balance) for p in points] == [
        (date(2024, 1, 1), 1100),
        (date(2024, 1, 2), 1050),
        (date(2024, 1, 3), 1250),
    ]


def test_same_day_balances_are_consolidated():
    account = Account(id="a1", name="Checking", starting_balance=1000)

    events = [
        event(date_=date(2024, 1, 1), amount=100),
        event(date_=date(2024, 1, 2), amount=-50),
        event(date_=date(2024, 1, 2), amount=200),
    ]

    proj = BalanceProjection({"a1": account}, events)

    points = proj.balances_for_account("a1", date(2024, 1, 1), date(2024, 1, 10))

    assert [(p.date, p.balance) for p in points] == [
        (date(2024, 1, 1), 1100),
        (date(2024, 1, 2), 1250),
    ]


def test_events_outside_window_are_excluded_without_state():
    account = Account(id="a1", name="Checking", starting_balance=1000)

    events = [
        event(date_=date(2023, 12, 31), amount=100),
        event(date_=date(2024, 1, 2), amount=50),
        event(date_=date(2024, 1, 10), amount=150),
    ]

    proj = BalanceProjection({"a1": account}, events)

    points = proj.balances_for_account("a1", date(2024, 1, 1), date(2024, 1, 10))

    assert [(p.date, p.balance) for p in points] == [
        (date(2024, 1, 2), 1050),
    ]


def test_events_outside_window_are_excluded_with_state():
    account = Account(id="a1", name="Checking", starting_balance=1000)

    state = AccountState(
        account_id="a1",
        as_of=date(2023, 12, 1),
        balance=2000,
    )

    events = [
        event(date_=date(2023, 12, 31), amount=100),
        event(date_=date(2024, 1, 2), amount=50),
        event(date_=date(2024, 1, 10), amount=150),
    ]

    proj = BalanceProjection({"a1": account}, events, states={"a1": state})

    points = proj.balances_for_account("a1", date(2024, 1, 1), date(2024, 1, 10))

    assert [(p.date, p.balance) for p in points] == [
        (date(2024, 1, 2), 2050),
    ]


def test_multiple_accounts_isolated_accumulation():
    a1 = Account(id="a1", name="Checking", starting_balance=1000)
    a2 = Account(id="a2", name="Savings", starting_balance=5000)

    events = [
        event(account_id="a1", date_=date(2024, 1, 1), amount=100),
        event(account_id="a2", date_=date(2024, 1, 2), amount=200),
        event(account_id="a1", date_=date(2024, 1, 3), amount=-50),
    ]

    proj = BalanceProjection({"a1": a1, "a2": a2}, events)

    p1 = proj.balances_for_account("a1", date(2024, 1, 1), date(2024, 1, 10))
    p2 = proj.balances_for_account("a2", date(2024, 1, 1), date(2024, 1, 10))

    assert [(p.date, p.balance) for p in p1] == [
        (date(2024, 1, 1), 1100),
        (date(2024, 1, 3), 1050),
    ]

    assert [(p.date, p.balance) for p in p2] == [
        (date(2024, 1, 2), 5200),
    ]


def test_state_overrides_starting_balance_and_effective_start():
    account = Account(id="a1", name="Checking", starting_balance=1000)

    state = AccountState(
        account_id="a1",
        as_of=date(2024, 1, 2),
        balance=2000,
    )

    events = [
        event(date_=date(2024, 1, 1), amount=100),
        event(date_=date(2024, 1, 2), amount=50),
        event(date_=date(2024, 1, 3), amount=25),
    ]

    proj = BalanceProjection({"a1": account}, events, states={"a1": state})

    points = proj.balances_for_account("a1", date(2024, 1, 1), date(2024, 1, 10))

    assert [(p.date, p.balance) for p in points] == [
        (date(2024, 1, 2), 2050),
        (date(2024, 1, 3), 2075),
    ]


def test_unknown_account_raises():
    proj = BalanceProjection({}, [])

    with pytest.raises(ValueError):
        proj.balances_for_account("missing", date(2024, 1, 1), date(2024, 1, 10))


def test_event_order_is_respected_even_if_unsorted_input():
    account = Account(id="a1", name="Checking", starting_balance=1000)

    events = [
        event(date_=date(2024, 1, 3), amount=200),
        event(date_=date(2024, 1, 1), amount=100),
        event(date_=date(2024, 1, 2), amount=-50),
    ]

    proj = BalanceProjection({"a1": account}, events)

    points = proj.balances_for_account("a1", date(2024, 1, 1), date(2024, 1, 10))

    assert [(p.date, p.balance) for p in points] == [
        (date(2024, 1, 1), 1100),
        (date(2024, 1, 2), 1050),
        (date(2024, 1, 3), 1250),
    ]
