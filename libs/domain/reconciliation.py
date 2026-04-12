from dataclasses import dataclass
from datetime import date
from typing import List
from libs.domain.cashflow import CashFlowEvent
from libs.domain.instruction_set import InstructionSet


@dataclass(frozen=True)
class ReconciledEvent:
    event: CashFlowEvent
    cleared: bool


@dataclass(frozen=True)
class ReconciliationView:
    instruction_set: InstructionSet

    def events_between(self, start: date, end: date) -> List[ReconciledEvent]:
        events = self.instruction_set.events_between(start, end)
        return [ReconciledEvent(event=e, cleared=False) for e in events]
