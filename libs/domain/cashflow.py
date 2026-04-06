from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional
from libs.domain.recurrence import Recurrence


@dataclass(frozen=True)
class CashFlowSeries:
    id: str
    name: str

    def events_for_series(self, instructions: List[CashFlowInstruction], start: date, end: date) -> List[CashFlowEvent]:
        events: List[CashFlowEvent] = []
        for instruction in instructions:
            if instruction.series_id != self.id:
                continue
            events.extend(instruction.events_between(start, end))

        return sorted(events, key=lambda e: (e.date, e.instruction_id))


@dataclass(frozen=True)
class CashFlowEvent:
    series_id: str
    instruction_id: str
    date: date
    amount: float


@dataclass(frozen=True)
class CashFlowInstruction:
    id: str
    series_id: str
    amount: float
    recurrence: Recurrence
    start_date: date
    end_date: Optional[date]
    created_on: datetime

    def __post_init__(self):
        if self.end_date and self.start_date >= self.end_date:
            raise ValueError("start_date must be < end_date")

    def effective_range(self, query_start: date, query_end: date) -> Optional[tuple[date, date]]:
        effective_start = max(query_start, self.start_date)
        effective_end = min(query_end, self.end_date) if self.end_date else query_end
        if effective_start > effective_end:
            return None

        return effective_start, effective_end

    def events_between(self, start: date, end: date) -> List[CashFlowEvent]:
        effective = self.effective_range(start, end)

        if not effective:
            return []

        effective_start, effective_end = effective
        dates = sorted(self.recurrence.occurrences_between(effective_start, effective_end))
        return [self._event_for_date(d) for d in dates]

    def _event_for_date(self, d: date) -> CashFlowEvent:
        return CashFlowEvent(series_id=self.series_id, instruction_id=self.id, date=d, amount=self.amount)
