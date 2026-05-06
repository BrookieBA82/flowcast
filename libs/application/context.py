from dataclasses import dataclass
from typing import Dict, List

from libs.domain.balance import Account
from libs.domain.cashflow import CashFlowInstruction, CashFlowEvent, CashFlowSeries
from libs.domain.settlement import SettlementLog
from libs.persistence.repository import Repository


@dataclass
class AppContext:
    accounts: Dict[str, Account]
    instructions: Dict[str, CashFlowInstruction]
    series: Dict[str, CashFlowSeries]
    events: List[CashFlowEvent]
    settlement_log: SettlementLog
    repo: Repository