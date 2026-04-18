from dataclasses import dataclass
from datetime import date
from typing import List, Dict, Optional
from libs.domain.cashflow import CashFlowEvent


@dataclass(frozen=True)
class Account:
    id: str
    name: str
    starting_balance: float


@dataclass(frozen=True)
class AccountState:
    account_id: str
    as_of: date
    balance: float


@dataclass(frozen=True)
class BalancePoint:
    date: date
    balance: float


class BalanceProjection:
    def __init__(
            self,
            accounts: Dict[str, Account],
            events: List[CashFlowEvent],
            states: Optional[Dict[str, AccountState]] = None):

        self._accounts = accounts
        self._events = sorted(events, key=lambda e: (e.date, e.instruction_id))
        self._states = states or {}

    def balances_for_account(self, account_id: str, start: date, end: date) -> List[BalancePoint]:
        account = self._accounts.get(account_id)
        if not account:
            raise ValueError(f"Unknown account {account_id}")

        state = self._states.get(account_id)

        if state:
            balance = state.balance
            effective_start = max(start, state.as_of)
        else:
            balance = account.starting_balance
            effective_start = start

        points: List[BalancePoint] = []
        last_date: Optional[date] = None

        for event in self._events:
            if event.account_id != account_id:
                continue

            if event.date < effective_start:
                continue

            if event.date >= end:
                break

            if last_date and last_date == event.date:
                points.pop(len(points) - 1)
            balance += event.amount
            points.append(BalancePoint(event.date, balance))
            last_date = event.date

        return points
