from abc import ABC, abstractmethod
from dataclasses import asdict
from datetime import date
from pathlib import Path
import json

from libs.application.context import AppContext
from libs.domain.balance import Account
from libs.domain.cashflow import CashFlowInstruction, CashFlowEvent, CashFlowSeries
from libs.domain.recurrence import MonthlyRecurrence
from libs.domain.settlement import SettlementLog


class Repository(ABC):
    @abstractmethod
    def load(self) -> AppContext:
        pass

    @abstractmethod
    def save(self, ctx: AppContext) -> None:
        pass


class JsonRepository(Repository):
    def __init__(self, path: str):
        self._path = Path(path)

    def load(self) -> AppContext:
        if not self._path.exists():
            return AppContext(
                accounts={},
                instructions={},
                series={},
                events=[],
                settlement_log=SettlementLog(),
            )

        raw = json.loads(self._path.read_text())

        accounts = {
            k: Account(**v)
            for k, v in raw["accounts"].items()
        }

        series = {
            k: CashFlowSeries(**v)
            for k, v in raw["series"].items()
        }

        instructions = {}
        for k, v in raw["instructions"].items():
            instructions[k] = CashFlowInstruction(
                id=v["id"],
                series_id=v["series_id"],
                account_id=v["account_id"],
                amount=v["amount"],
                recurrence=MonthlyRecurrence(**v["recurrence"]),
                start_date=date.fromisoformat(v["start_date"]),
                end_date=date.fromisoformat(v["end_date"]) if v["end_date"] else None,
            )

        events = [
            CashFlowEvent(
                series_id=e["series_id"],
                account_id=e["account_id"],
                instruction_id=e["instruction_id"],
                date=date.fromisoformat(e["date"]),
                amount=e["amount"],
                orig_date=date.fromisoformat(e["orig_date"]),
            )
            for e in raw["events"]
        ]

        settlement_log = SettlementLog()

        for event_id, s in raw["settlements"].items():
            if s["status"] == "CLEARED":
                settlement_log.clear(
                    event_id=event_id,
                    account_id=s["account_id"],
                    date_=date.fromisoformat(s["date"]),
                    settled_amount=s["settled_amount"],
                )
            else:
                settlement_log.defer(
                    event_id=event_id,
                    account_id=s["account_id"],
                    date_=date.fromisoformat(s["date"]),
                )

        return AppContext(
            accounts=accounts,
            instructions=instructions,
            series=series,
            events=events,
            settlement_log=settlement_log,
        )

    def save(self, ctx: AppContext) -> None:
        settlements = {}

        for event_id, s in ctx.settlement_log._by_event_id.items():
            settlements[event_id] = {
                "account_id": s.account_id,
                "date": s.date.isoformat(),
                "status": s.status.name,
                "settled_amount": s.settled_amount,
            }

        data = {
            "accounts": {
                k: asdict(v)
                for k, v in ctx.accounts.items()
            },
            "series": {
                k: asdict(v)
                for k, v in ctx.series.items()
            },
            "instructions": {
                k: {
                    "id": v.id,
                    "series_id": v.series_id,
                    "account_id": v.account_id,
                    "amount": v.amount,
                    "start_date": v.start_date.isoformat(),
                    "end_date": v.end_date.isoformat() if v.end_date else None,
                    "recurrence": asdict(v.recurrence),
                }
                for k, v in ctx.instructions.items()
            },
            "events": [
                {
                    "series_id": e.series_id,
                    "account_id": e.account_id,
                    "instruction_id": e.instruction_id,
                    "date": e.date.isoformat(),
                    "amount": e.amount,
                    "orig_date": e.orig_date.isoformat(),
                }
                for e in ctx.events
            ],
            "settlements": settlements,
        }

        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2))