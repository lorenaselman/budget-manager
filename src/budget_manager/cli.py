"""Command-line interface: parse input, call the service, print results."""

import argparse
import sys

from . import storage
from .models import CATEGORIES, KINDS
from .services import BudgetService
from .validation import ValidationError

DEFAULT_DATA = "data/transactions.csv"


def build_parser():
    p = argparse.ArgumentParser(prog="budget_manager",
                                description="Personal budget manager")
    p.add_argument("--data", default=DEFAULT_DATA, help="CSV file to use")
    sub = p.add_subparsers(dest="command")
    a = sub.add_parser("add", help="add a transaction")
    a.add_argument("date", help="YYYY-MM-DD")
    a.add_argument("kind", help="|".join(KINDS))
    a.add_argument("category", help="|".join(CATEGORIES))
    a.add_argument("amount", help="positive number")
    a.add_argument("currency", help="e.g. EUR")
    ls = sub.add_parser("list", help="list transactions")
    ls.add_argument("--kind")
    ls.add_argument("--category")
    sub.add_parser("summary", help="income, expenses and balance per currency")
    sub.add_parser("undo", help="remove the last transaction")
    sub.add_parser("validate", help="check the data file and report bad rows")
    sub.add_parser("menu", help="interactive menu")
    return p


def _fmt(t):
    return (f"{t.id}  {t.date}  {t.kind:<7}  {t.category:<13}"
            f"{t.amount:>10.2f} {t.currency}")


def run(args, out=print):
    """Execute one command. Returns an exit code."""
    transactions, errors = storage.load(args.data)
    for e in errors:
        print(f"WARNING: {e}", file=sys.stderr)
    cmd = args.command
    if cmd == "validate":
        out(f"{len(transactions)} valid row(s), {len(errors)} invalid.")
        return 1 if errors else 0
    if errors and cmd in ("add", "undo"):
        # Saving would silently drop the bad rows, so refuse to modify.
        print("ERROR: fix the invalid rows above before changing the file.",
              file=sys.stderr)
        return 1

    service = BudgetService(transactions)
    try:
        if cmd == "add":
            tx = service.add(args.date, args.kind, args.category,
                             args.amount, args.currency)
            storage.save(args.data, service.transactions)
            out(f"Added {_fmt(tx)}")
        elif cmd == "list":
            rows = service.filter(args.kind, args.category)
            for t in rows:
                out(_fmt(t))
            if not rows:
                out("No transactions.")
        elif cmd == "summary":
            totals = service.summary()
            for cur, v in totals.items():
                out(f"{cur}: income {v['income']:.2f}  "
                    f"expense {v['expense']:.2f}  balance {v['balance']:.2f}")
            if not totals:
                out("No transactions.")
        elif cmd == "undo":
            tx = service.undo()
            storage.save(args.data, service.transactions)  # disk follows memory
            out(f"Undid {_fmt(tx)}")
    except ValidationError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 1
    return 0


def menu(args, input_fn=input):
    """Simple interactive loop that reuses run()."""
    while True:
        choice = input_fn("\n[a]dd  [l]ist  [s]ummary  [u]ndo  [q]uit > ").strip().lower()
        if choice == "q":
            return 0
        if choice == "a":
            args.command = "add"
            args.date = input_fn("Date (YYYY-MM-DD): ")
            args.kind = input_fn(f"Kind ({'/'.join(KINDS)}): ")
            args.category = input_fn(f"Category ({'/'.join(CATEGORIES)}): ")
            args.amount = input_fn("Amount: ")
            args.currency = input_fn("Currency (e.g. EUR): ")
        elif choice in ("l", "s", "u"):
            args.command = {"l": "list", "s": "summary", "u": "undo"}[choice]
            args.kind = args.category = None
        else:
            print("Unknown choice.")
            continue
        run(args)


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command in (None, "menu"):
        return menu(args)
    return run(args)
