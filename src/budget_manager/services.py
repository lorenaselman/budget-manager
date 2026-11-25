"""Business logic. No printing, no prompting, no file access."""

from collections import defaultdict

from .validation import ValidationError, validate_transaction


class BudgetService:
    def __init__(self, transactions=()):
        self._items = list(transactions)

    @property
    def transactions(self):
        return list(self._items)

    def _next_id(self):
        nums = [int(t.id[1:]) for t in self._items
                if t.id[:1] == "T" and t.id[1:].isdigit()]
        return f"T{max(nums, default=0) + 1:03d}"

    def add(self, date, kind, category, amount, currency):
        raw = {"id": self._next_id(), "date": date, "kind": kind,
               "category": category, "amount": amount, "currency": currency}
        tx = validate_transaction(raw)
        self._items.append(tx)
        return tx

    def filter(self, kind=None, category=None):
        return [t for t in self._items
                if (kind is None or t.kind == kind)
                and (category is None or t.category == category.lower())]

    def undo(self):
        """Remove and return the most recent transaction."""
        if not self._items:
            raise ValidationError("nothing to undo.")
        return self._items.pop()

    def summary(self):
        """Per-currency totals. Currencies are never mixed (no FX rates)."""
        out = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
        for t in self._items:
            out[t.currency][t.kind] += t.amount
        return {cur: {"income": round(v["income"], 2),
                      "expense": round(v["expense"], 2),
                      "balance": round(v["income"] - v["expense"], 2)}
                for cur, v in sorted(out.items())}
