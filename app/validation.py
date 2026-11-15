import re
from typing import Optional
from fastapi import HTTPException

MIN_YEAR = 2000
MAX_YEAR = 2100

# DECIMAL(9, 2) in the transactions table
MAX_AMOUNT = 9_999_999.99

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}$")

# "#rgb", "#rrggbb" (color inputs) or a plain css color name such as "white"
COLOR_RE = re.compile(r"^(#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6}|[a-zA-Z]{3,20})$")

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


def clean (value: str) -> str:
    return value.strip() if isinstance(value, str) else value

def period_filters (month: Optional[str] = None, year: Optional[str] = None):
    """Validates the month/year query params shared by the dashboard endpoints.
    Returns ("", "") / ("", "2026") / ("6", "2026") as the queries expect."""
    month = (month or "").strip()
    year = (year or "").strip()

    if month and not year:
        raise HTTPException(status_code=400, detail="Can not filter only to month.")

    if year:
        if not year.isdigit() or len(year) != 4 or not (MIN_YEAR <= int(year) <= MAX_YEAR):
            raise HTTPException(status_code=400, detail=f"Year must be between {MIN_YEAR} and {MAX_YEAR}.")
        year = str(int(year))

    if month:
        if not month.isdigit() or not (1 <= int(month) <= 12):
            raise HTTPException(status_code=400, detail="Month must be between 1 and 12.")
        month = str(int(month))

    return month, year
