from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
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
    account_id: str
    instruction_id: str
    date: date
    amount: float
    orig_date: date = field(default=None)
    id: str = field(init=False)

    def __post_init__(self):
        orig = self.orig_date or self.date
        object.__setattr__(self, "orig_date", orig)
        object.__setattr__(
            self,
            "id",
            CashFlowEvent._generate_id(
                self.series_id,
                self.instruction_id,
                orig.isoformat(),   # 🔑 stable across deferrals
            )
        )

    def defer(self, deferral_date: date) -> "CashFlowEvent":
        return CashFlowEvent(
            series_id=self.series_id,
            account_id=self.account_id,
            instruction_id=self.instruction_id,
            date=deferral_date,
            amount=self.amount,
            orig_date=self.orig_date)

    @staticmethod
    def _generate_id(series_id: str, instruction_id: str, orig_date: str) -> str:
        return f"{series_id}:{instruction_id}:{orig_date}"


@dataclass(frozen=True)
class CashFlowInstruction:
    id: str
    series_id: str
    account_id: str
    amount: float
    recurrence: Recurrence
    start_date: date
    end_date: Optional[date]

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
        return CashFlowEvent(
            series_id=self.series_id,
            account_id=self.account_id,
            instruction_id=self.id,
            date=d,
            amount=self.amount)
