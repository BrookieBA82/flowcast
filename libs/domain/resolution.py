from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Dict, Optional

from libs.domain.cashflow import CashFlowEvent
from libs.domain.balance import Account, AccountState, BalancePoint, BalanceProjection
from libs.domain.settlement import SettlementLog


@dataclass(frozen=True)
class ResolutionResult:
    account_states: Dict[str, AccountState]
    balance_points: Dict[str, List[BalancePoint]]


class EventResolver:
    def __init__(self, settlement_log: SettlementLog, start: date, end: date) -> None:
        self._settlement_log = settlement_log
        self._start = start
        self._end = end

    def normalize_before_start(self, events: List[CashFlowEvent]) -> List[CashFlowEvent]:
        uncleared_events: List[CashFlowEvent] = self._find_uncleared_events(events)
        for e in uncleared_events:
            self._settlement_log.defer(e.id, e.account_id, self._start)
        return [e.defer(self._start) for e in uncleared_events]

    def resolve(
        self,
        accounts: Dict[str, Account],
        events: List[CashFlowEvent],
        prior_states: Optional[Dict[str, AccountState]] = None) -> ResolutionResult:

        uncleared_events: List[CashFlowEvent] = self._find_uncleared_events(events)
        if uncleared_events:
            raise ValueError(f"Detected uncleared events prior to start date - must defer all before resolution")
        all_events: List[CashFlowEvent] = events
        return self._compute_resolution(accounts, all_events, prior_states)

    def normalize_and_resolve(
        self,
        accounts: Dict[str, Account],
        events: List[CashFlowEvent],
        prior_states: Optional[Dict[str, AccountState]] = None) -> ResolutionResult:

        deferred_events: List[CashFlowEvent] = self.normalize_before_start(events)
        updated_events = EventResolver._replace_deferred_events(events, deferred_events)
        return self.resolve(accounts, updated_events, prior_states)

    def _find_uncleared_events(self, events: List[CashFlowEvent]) -> List[CashFlowEvent]:
        return [e for e in events if self._before_start(e) and self._is_uncleared(e)]

    def _compute_resolution(
        self,
        accounts: Dict[str, Account],
        events: List[CashFlowEvent],
        prior_states: Optional[Dict[str, AccountState]] = None) -> ResolutionResult:

        prior_states = self._normalize_prior_states(prior_states)
        events_sorted = sorted(events, key=lambda e: (e.date, e.instruction_id))

        states: Dict[str, AccountState] = {}
        for account_id, account in accounts.items():
            states[account_id] = self._process_account_pre_start(
                account=account,
                events_sorted=events_sorted,
                state=prior_states.get(account_id))

        forward_events = [e for e in events_sorted if self._after_start(e)]
        projection_engine = BalanceProjection(accounts, forward_events, states)
        projections: Dict[str, List[BalancePoint]] = {
            account_id: projection_engine.balances_for_account(account_id, self._start, self._end)
            for account_id in accounts.keys() }

        return ResolutionResult(account_states=states, balance_points=projections)

    def _process_account_pre_start(
        self,
        account: Account,
        events_sorted: List[CashFlowEvent],
        state: Optional[AccountState]) -> AccountState:

        balance, anchor_date = (state.balance, state.as_of) if state else (account.starting_balance, None)
        pre_start_account_events = [
            e for e in events_sorted
            if e.account_id == account.id and self._is_post_anchor(e, anchor_date) and self._before_start(e)
        ]
        self._validate_account_events(pre_start_account_events, account.id)

        for e in pre_start_account_events:
            if not self._is_deferred(e):
                balance += self._effective_amount(e)

        new_start = self._start - timedelta(days=1)
        return AccountState(account_id=account.id, as_of=new_start, balance=balance)

    def _normalize_prior_states(self, priors: Optional[Dict[str, AccountState]]) -> Dict[str, AccountState]:
        priors = priors or {}
        for s in priors.values():
            if s.as_of >= self._start:
                raise ValueError("AccountState must be strictly before start")
        return priors

    def _validate_account_events(self, relevant: List[CashFlowEvent], account_id: str) -> None:
        unresolved = [e for e in relevant if self._is_uncleared(e) and not self._is_deferred(e)]
        if unresolved:
            raise ValueError(f"Unresolved events before start for account {account_id}")

    def _before_start(self, event: CashFlowEvent) -> bool:
        return event.date < self._start

    def _after_start(self, event: CashFlowEvent) -> bool:
        return event.date >= self._start

    def _is_uncleared(self, event: CashFlowEvent) -> bool:
        return not self._settlement_log.is_cleared(event.id)

    def _is_deferred(self, event: CashFlowEvent) -> bool:
        return self._settlement_log.is_deferred(event.id)

    def _effective_amount(self, event: CashFlowEvent) -> float:
        return self._settlement_log.effective_amount(event.id, event.amount)

    @staticmethod
    def _replace_deferred_events(
            original_events: List[CashFlowEvent],
            deferred_events: List[CashFlowEvent]) -> List[CashFlowEvent]:

        deferred_ids = { e.id for e in deferred_events }
        non_deferred_events = [e for e in original_events if e.id not in deferred_ids]
        return deferred_events + non_deferred_events

    @staticmethod
    def _is_post_anchor(event: CashFlowEvent, anchor_date: date) -> bool:
        return anchor_date is None or event.date >= anchor_date