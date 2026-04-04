from datetime import date
from libs.domain.recurrence import MonthlyRecurrence, AnnualRecurrence


def test_monthly_single_day():
    r = MonthlyRecurrence(days=[1])

    results = r.occurrences_between(
        date(2026, 1, 1),
        date(2026, 4, 1)
    )

    assert results == [
        date(2026, 1, 1),
        date(2026, 2, 1),
        date(2026, 3, 1),
    ]


def test_monthly_multiple_days():
    r = MonthlyRecurrence(days=[1, 15])

    results = r.occurrences_between(
        date(2026, 1, 1),
        date(2026, 1, 31)
    )

    assert results == [
        date(2026, 1, 1),
        date(2026, 1, 15),
    ]


def test_monthly_31_clamps():
    r = MonthlyRecurrence(days=[31])

    results = r.occurrences_between(
        date(2026, 2, 1),
        date(2026, 3, 1)
    )

    assert results == [
        date(2026, 2, 28),  # clamped
    ]


def test_annual_basic():
    r = AnnualRecurrence(month=4, day=15)

    results = r.occurrences_between(
        date(2025, 1, 1),
        date(2027, 12, 31)
    )

    assert results == [
        date(2025, 4, 15),
        date(2026, 4, 15),
        date(2027, 4, 15),
    ]


def test_annual_feb_29_clamps():
    r = AnnualRecurrence(month=2, day=29)

    results = r.occurrences_between(
        date(2025, 1, 1),
        date(2026, 12, 31)
    )

    assert results == [
        date(2025, 2, 28),
        date(2026, 2, 28),
    ]


def test_annual_feb_29_valid():
    r = AnnualRecurrence(month=2, day=29)

    results = r.occurrences_between(
        date(2024, 1, 1),
        date(2024, 12, 31)
    )

    assert results == [
        date(2024, 2, 29),
    ]
