from abc import ABC, abstractmethod
from typing import Dict, List
import json
from pathlib import Path

from libs.domain.balance import Account
from libs.domain.cashflow import CashFlowInstruction, CashFlowEvent, CashFlowSeries
from libs.domain.settlement import SettlementLog


class Repository(ABC):
    @abstractmethod
    def load_accounts(self) -> Dict[str, Account]: ...
    @abstractmethod
    def save_accounts(self, accounts: Dict[str, Account]) -> None: ...

    @abstractmethod
    def load_instructions(self) -> Dict[str, CashFlowInstruction]: ...
    @abstractmethod
    def save_instructions(self, instructions: Dict[str, CashFlowInstruction]) -> None: ...

    @abstractmethod
    def load_series(self) -> Dict[str, CashFlowSeries]: ...
    @abstractmethod
    def save_series(self, series: Dict[str, CashFlowSeries]) -> None: ...

    @abstractmethod
    def load_events(self) -> List[CashFlowEvent]: ...
    @abstractmethod
    def save_events(self, events: List[CashFlowEvent]) -> None: ...

    @abstractmethod
    def load_settlement_log(self) -> SettlementLog: ...
    @abstractmethod
    def save_settlement_log(self, log: SettlementLog) -> None: ...


class JsonRepository:
    def __init__(self, base_path: str):
        self.base = Path(base_path)
        self.base.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        return self.base / f"{name}.json"

    def _load(self, name: str, default):
        path = self._path(name)
        if not path.exists():
            return default
        return json.loads(path.read_text())

    def _save(self, name: str, data):
        self._path(name).write_text(json.dumps(data, indent=2))