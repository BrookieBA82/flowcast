from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum, auto
from typing import Dict, Optional


class _SettlementStatus(Enum):
    CLEARED = auto()
    DEFERRED = auto()


@dataclass(frozen=True)
class _SettlementEvent:
    event_id: str
    account_id: str
    date: date
    status: _SettlementStatus
    settled_amount: Optional[float] = None


class SettlementLog:
    def __init__(self):
        self._by_event_id: Dict[str, _SettlementEvent] = { }

    def clear(self, event_id: str, account_id: str, date_: date, settled_amount: float) -> None:
        if self._is_event_cleared(event_id):
            raise ValueError(f"Event {event_id} has already been cleared")
        settlement = _SettlementEvent(event_id, account_id, date_, _SettlementStatus.CLEARED, settled_amount)
        self._by_event_id[settlement.event_id] = settlement

    def defer(self, event_id: str, account_id: str, date_: date) -> None:
        if self._is_event_cleared(event_id):
            raise ValueError(f"Event {event_id} has already been cleared")
        previous_deferral_date = self._get_deferral_date(event_id)
        if previous_deferral_date and previous_deferral_date >= date_:
            raise ValueError(f"Event {event_id} has already been deferred to later date {previous_deferral_date}")
        settlement = _SettlementEvent(event_id, account_id, date_, _SettlementStatus.DEFERRED)
        self._by_event_id[settlement.event_id] = settlement

    def is_cleared(self, event_id: str) -> bool:
        s = self._by_event_id.get(event_id)
        return s is not None and s.status == _SettlementStatus.CLEARED

    def is_deferred(self, event_id: str) -> bool:
        s = self._by_event_id.get(event_id)
        return s is not None and s.status == _SettlementStatus.DEFERRED

    def effective_amount(self, event_id: str, original_amount: float) -> float:
        s = self._by_event_id.get(event_id)
        if not s or s.status == _SettlementStatus.DEFERRED:
            return original_amount

        return s.settled_amount

    def _is_event_cleared(self, event_id: str) -> bool:
        return event_id in self._by_event_id and self._by_event_id[event_id].status == _SettlementStatus.CLEARED

    def _get_deferral_date(self, event_id: str) -> Optional[date]:
        event = self._by_event_id.get(event_id)
        return event.date if event else None