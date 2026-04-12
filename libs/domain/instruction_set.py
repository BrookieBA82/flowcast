from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional

from libs.domain.cashflow import CashFlowInstruction, CashFlowEvent


@dataclass
class InstructionSet:
    _instructions_by_series: dict[str, _SeriesInstructionSet]

    def effective_instruction(self, series_id: str, at: date) -> Optional[CashFlowInstruction]:
        if series_id not in self._instructions_by_series:
            raise ValueError(f"Series {series_id} does not exist")

        series = self._instructions_by_series[series_id]
        results = series.effective_instructions_between(at, at + timedelta(days=1))

        return results[0].instruction if results else None

    def events_between(self, start: date, end: date) -> List[CashFlowEvent]:
        events: List[CashFlowEvent] = []

        for series in self._instructions_by_series.values():
            for eff in series.effective_instructions_between(start, end):
                instr = eff.instruction

                clamped_start = max(eff.start_date, instr.start_date)
                clamped_end = eff.end_date
                if instr.end_date is not None:
                    clamped_end = min(clamped_end, instr.end_date)

                if clamped_start < clamped_end:
                    events.extend(instr.events_between(clamped_start, clamped_end))

        return sorted(events, key=lambda e: (e.date, e.instruction_id))

    def create_series(self, series_id: str, instruction: CashFlowInstruction):
        if series_id in self._instructions_by_series:
            raise ValueError(f"Series {series_id} already exists")

        series_instructions = _SeriesInstructionSet([])
        series_instructions.add_instruction(instruction)
        self._instructions_by_series[series_id] = series_instructions

    def update_series_from(self, series_id: str, new_instruction: CashFlowInstruction):
        if series_id not in self._instructions_by_series:
            raise ValueError(f"Series {series_id} does not exist")

        self._instructions_by_series[series_id].add_instruction(new_instruction)

    def terminate_series(self, series_id: str, end_date: date):
        if series_id not in self._instructions_by_series:
            raise ValueError(f"Series {series_id} does not exist")

        self._instructions_by_series[series_id].terminate_series(end_date)


@dataclass
class _SeriesInstructionSet:
    _boundaries: list[tuple[date, Optional[CashFlowInstruction]]]

    def add_instruction(self, instruction: CashFlowInstruction):
        if self._is_terminated:
            raise ValueError("Cannot add instruction after termination")

        max_date = self._max_date
        if max_date and instruction.start_date <= max_date:
            raise ValueError("Overlapping instructions detected")

        self._boundaries.append((instruction.start_date, instruction))

    def terminate_series(self, end_date: date):
        if self._is_terminated:
            raise ValueError("Cannot terminate multiple times")

        max_date = self._max_date
        if max_date and end_date <= max_date:
            raise ValueError("Cannot terminate series before max date")

        self._boundaries.append((end_date, None))

    def effective_instructions_between(self, start: date, end: date) -> List[_EffectiveInstruction]:
        if not self._boundaries or start >= end:
            return []

        boundaries = self._boundaries
        dates = [b[0] for b in boundaries]

        results: List[_EffectiveInstruction] = []

        idx = bisect_right(dates, start) - 1

        if idx >= 0:
            _, instr = boundaries[idx]

            if instr is not None:
                next_boundary = boundaries[idx + 1] if idx + 1 < len(boundaries) else None
                next_date = next_boundary[0] if next_boundary else end

                effective_start = max(start, instr.start_date)
                effective_end = min(next_date, end, instr.end_date) if instr.end_date else min(next_date, end)

                if effective_start < effective_end:
                    results.append(_EffectiveInstruction(instr, effective_start, effective_end))

        for i in range(idx + 1, len(boundaries)):
            boundary_date, instr = boundaries[i]

            if boundary_date >= end:
                break

            if instr is None:
                break

            next_boundary = boundaries[i + 1] if i + 1 < len(boundaries) else None
            next_date = next_boundary[0] if next_boundary else end

            effective_start = max(boundary_date, start, instr.start_date)
            effective_end = min(next_date, end, instr.end_date) if instr.end_date else min(next_date, end)

            if effective_start >= effective_end:
                continue

            results.append(_EffectiveInstruction(instr, effective_start, effective_end))

        return results

    @property
    def _max_date(self) -> Optional[date]:
        return self._boundaries[-1][0] if self._boundaries else None

    @property
    def _is_terminated(self) -> bool:
        return bool(self._boundaries) and self._boundaries[-1][1] is None


@dataclass(frozen=True)
class _EffectiveInstruction:
    instruction: CashFlowInstruction
    start_date: date
    end_date: date
