import pytest
from datetime import date
from libs.domain.settlement import SettlementLog


def test_cleared_event_is_recognized():
    log = SettlementLog()

    log.clear(event_id="e1", account_id="a1", date_=date(2024, 1, 1), settled_amount=100.0)

    assert log.is_cleared("e1")
    assert not log.is_deferred("e1")
    assert log.effective_amount("e1", 100) == 100.0


def test_deferred_event_keeps_original_balance():
    log = SettlementLog()

    log.defer(event_id="e1", account_id="a1", date_=date(2024, 1, 1))

    assert not log.is_cleared("e1")
    assert log.is_deferred("e1")
    assert log.effective_amount("e1", 100) == 100.0


def test_cleared_event_after_multiple_deferrals():
    log = SettlementLog()

    log.defer(event_id="e1", account_id="a1", date_=date(2024, 1, 1))
    log.defer(event_id="e1", account_id="a1", date_=date(2024, 1, 2))
    log.clear(event_id="e1", account_id="a1", date_=date(2024, 1, 3), settled_amount=100.0)

    assert log.is_cleared("e1")
    assert not log.is_deferred("e1")
    assert log.effective_amount("e1", 100) == 100.0


def test_cannot_clear_same_event_twice():
    log = SettlementLog()

    log.clear(event_id="e1", account_id="a1", date_=date(2024, 1, 1), settled_amount=80.0)

    with pytest.raises(ValueError):
        log.clear(event_id="e1", account_id="a1", date_=date(2024, 1, 1), settled_amount=80.0)


def test_cannot_defer_cleared_event():
    log = SettlementLog()

    log.clear(event_id="e1", account_id="a1", date_=date(2024, 1, 3), settled_amount=100.0)

    with pytest.raises(ValueError):
        log.defer(event_id="e1", account_id="a1", date_=date(2024, 1, 3))


def test_cannot_defer_event_already_deferred_to_later_date():
    log = SettlementLog()

    log.defer(event_id="e1", account_id="a1", date_=date(2024, 1, 5))

    with pytest.raises(ValueError):
        log.defer(event_id="e1", account_id="a1", date_=date(2024, 1, 3))


def test_missing_settlement_defaults_to_original():
    log = SettlementLog()

    assert log.effective_amount("e1", 100) == 100


def test_cleared_amount_overrides_original():
    log = SettlementLog()

    log.clear(event_id="e1", account_id="a1", date_=date(2024, 1, 1), settled_amount=80.0)

    assert log.effective_amount("e1", 100) == 80


def test_multiple_events_independent():
    log = SettlementLog()

    log.clear(event_id="e1", account_id="a1", date_=date(2024, 1, 1), settled_amount=50.0)

    log.defer(event_id="e2", account_id="a1", date_=date(2024, 1, 2))

    assert log.effective_amount("e1", 100) == 50.0
    assert log.effective_amount("e2", 100) == 100.0