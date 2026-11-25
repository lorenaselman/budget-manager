"""Boundary checks. Every entry point (CLI, CSV import) goes through here.

Nothing is silently corrected: bad input raises ValidationError with a
message saying which field is wrong and what is allowed.
"""

import math
from datetime import date

from .models import CATEGORIES, FIELDS, KINDS, Transaction


class ValidationError(ValueError):
    pass


def validate_transaction(raw, row=None):
    """Turn a dict of strings into a Transaction, or raise ValidationError."""
    prefix = f"Row {row}: " if row is not None else ""

    def fail(msg):
        raise ValidationError(prefix + msg)

    missing = [f for f in FIELDS if raw.get(f) is None or str(raw[f]).strip() == ""]
    if missing:
        fail(f"missing value for {', '.join(missing)}.")

    id_ = str(raw["id"]).strip()
    day = str(raw["date"]).strip()
    kind = str(raw["kind"]).strip().lower()
    category = str(raw["category"]).strip().lower()
    currency = str(raw["currency"]).strip()

    try:
        if len(day) != 10:
            raise ValueError
        date.fromisoformat(day)
    except ValueError:
        fail(f"date '{day}' must be a real date in YYYY-MM-DD format.")

    if kind not in KINDS:
        fail(f"kind '{kind}' must be one of: {', '.join(KINDS)}.")

    if category not in CATEGORIES:
        fail(f"unknown category '{category}'; allowed: {', '.join(CATEGORIES)}.")

    try:
        amount = float(str(raw["amount"]).strip())
    except ValueError:
        fail(f"amount '{raw['amount']}' is not a number.")
    if not math.isfinite(amount):
        fail("amount must be a finite number.")
    if amount <= 0:
        fail("amount must be > 0.")

    if not (len(currency) == 3 and currency.isascii() and currency.isalpha()
            and currency.isupper()):
        fail(f"currency '{currency}' must be a 3-letter uppercase ISO code, e.g. EUR.")

    return Transaction(id_, day, kind, category, round(amount, 2), currency)
