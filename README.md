# Personal Budget Manager — Release 1

A small command-line budget manager: add, list and summarize transactions,
saved to a CSV file, with validation at every entry point and an undo.
Python 3.9+ standard library only — nothing to install.

## Run

From this folder:

```bash
export PYTHONPATH=src
python3 -m budget_manager add 2026-09-04 expense food 18.50 EUR
python3 -m budget_manager list [--kind expense] [--category food]
python3 -m budget_manager summary
python3 -m budget_manager undo
python3 -m budget_manager validate --data data/sample_transactions.csv
python3 -m budget_manager            # interactive menu
```

Data is stored in `data/transactions.csv` (change with `--data FILE`).

Example:

```
$ python3 -m budget_manager add 2026-09-04 expense food -5 EUR
ERROR: amount must be > 0.
$ python3 -m budget_manager summary
EUR: income 2000.00  expense 18.50  balance 1981.50
```

## Test

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

9 tests: a normal case, boundaries (0, negative, NaN, bad dates, unknown
category, 0.01), the sample file (4 valid + 8 invalid rows with exact
messages), save/load round-trip, and undo surviving a reload.

## Rules (acceptance criteria)

| Field | Rule |
|---|---|
| id | auto-assigned `T001`, `T002`, … unique |
| date | real date, `YYYY-MM-DD` |
| kind | `expense` or `income` |
| category | one of: food, rent, transport, utilities, health, entertainment, salary, other — unknown categories are **rejected** |
| amount | finite number > 0 (sign comes from `kind`) |
| currency | 3 uppercase letters (e.g. EUR) |

## Known limitations

- Currencies are never converted; the summary reports one line per currency.
- Undo only removes the last transaction (no redo, no multi-step history).
- Whole-file rewrite on each change; fine for hundreds of rows, not millions.
- If the data file contains invalid rows, `add`/`undo` refuse to run (so rows
  are never silently dropped); fix the file, using `validate` to find them.
- No edit/delete of arbitrary transactions.
