from dataclasses import dataclass
from libs.domain.recurrence import Recurrence


@dataclass(frozen=True)
class CashFlowInstruction:
    name: str
    amount: float
    recurrence: Recurrence
