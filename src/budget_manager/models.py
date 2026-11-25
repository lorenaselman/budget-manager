"""Domain model: the Transaction record and its allowed values."""

from dataclasses import dataclass

KINDS = ("expense", "income")
CATEGORIES = ("food", "rent", "transport", "utilities", "health",
              "entertainment", "salary", "other")
FIELDS = ("id", "date", "kind", "category", "amount", "currency")


@dataclass(frozen=True)
class Transaction:
    """One validated record. All six fields are always present."""

    id: str
    date: str        # ISO format YYYY-MM-DD
    kind: str        # "expense" | "income"
    category: str    # one of CATEGORIES
    amount: float    # always > 0; the sign comes from `kind`
    currency: str    # 3 uppercase letters, e.g. EUR

    def to_row(self):
        return {"id": self.id, "date": self.date, "kind": self.kind,
                "category": self.category, "amount": f"{self.amount:.2f}",
                "currency": self.currency}
