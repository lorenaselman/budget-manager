"""File persistence (CSV). No business rules beyond calling validation."""

import csv
import os
import tempfile
from pathlib import Path

from .models import FIELDS
from .validation import ValidationError, validate_transaction


def load(path):
    """Return (transactions, errors). A missing file is an empty ledger.

    Invalid rows are reported with their row number, never fixed or hidden.
    """
    path = Path(path)
    if not path.exists():
        return [], []
    good, errors, seen = [], [], set()
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None or set(FIELDS) - set(reader.fieldnames):
            return [], [f"File header must contain: {', '.join(FIELDS)}."]
        for n, raw in enumerate(reader, start=2):  # row 1 is the header
            try:
                tx = validate_transaction(raw, row=n)
                if tx.id in seen:
                    raise ValidationError(f"Row {n}: duplicate id '{tx.id}'.")
            except ValidationError as err:
                errors.append(str(err))
                continue
            seen.add(tx.id)
            good.append(tx)
    return good, errors


def save(path, transactions):
    """Atomic write: the file is either the old state or the new one."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=FIELDS)
            writer.writeheader()
            for t in transactions:
                writer.writerow(t.to_row())
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
