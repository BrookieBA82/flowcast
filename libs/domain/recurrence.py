import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum, auto
from typing import List

class RecurrenceType(Enum):
    ONE_TIME = auto()
    MONTHLY = auto()
    ANNUAL = auto()


class Recurrence:
    def occurrences_between(self, start: date, end: date) -> List[date]:
        raise NotImplementedError


def last_day_of_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


@dataclass(frozen=True)
class OneTimeRecurrence(Recurrence):
    run_date: date

    def occurrences_between(self, start: date, end: date) -> List[date]:
        if start <= self.run_date <= end:
            return [self.run_date]
        return []


@dataclass(frozen=True)
class MonthlyRecurrence(Recurrence):
    days: List[int]

    def occurrences_between(self, start: date, end: date) -> List[date]:
        results: List[date] = []

        year = start.year
        month = start.month

        while (year < end.year) or (year == end.year and month <= end.month):
            max_day = last_day_of_month(year, month)

            for day in self.days:
                actual_day = min(day, max_day)
                occurrence = date(year, month, actual_day)
                if start <= occurrence < end:
                    results.append(occurrence)

            if month == 12:
                year += 1
                month = 1
            else:
                month += 1

        return sorted(results)


@dataclass(frozen=True)
class AnnualRecurrence(Recurrence):
    month: int
    day: int

    def occurrences_between(self, start: date, end: date) -> List[date]:
        results: List[date] = []

        for year in range(start.year, end.year + 1):
            max_day = last_day_of_month(year, self.month)
            actual_day = min(self.day, max_day)

            occurrence = date(year, self.month, actual_day)

            if start <= occurrence < end:
                results.append(occurrence)

        return results