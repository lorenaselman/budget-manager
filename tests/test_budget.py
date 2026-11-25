import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from budget_manager import storage  # noqa: E402
from budget_manager.cli import build_parser, run  # noqa: E402
from budget_manager.services import BudgetService  # noqa: E402
from budget_manager.validation import ValidationError  # noqa: E402


class NormalCase(unittest.TestCase):
    def test_add_and_summary(self):
        s = BudgetService()
        s.add("2026-09-01", "income", "salary", "2000", "EUR")
        s.add("2026-09-04", "expense", "food", "18.50", "EUR")
        self.assertEqual(s.summary(),
                         {"EUR": {"income": 2000.0, "expense": 18.5, "balance": 1981.5}})
        self.assertEqual([t.id for t in s.transactions], ["T001", "T002"])


class BoundaryCases(unittest.TestCase):
    def test_amount_zero_and_negative_rejected(self):
        s = BudgetService()
        for bad in ("0", "-5", "nan", "inf", "abc"):
            with self.assertRaises(ValidationError, msg=bad):
                s.add("2026-09-01", "expense", "food", bad, "EUR")
        self.assertEqual(s.transactions, [])

    def test_unknown_category_and_bad_date_rejected(self):
        s = BudgetService()
        with self.assertRaisesRegex(ValidationError, "unknown category 'gadgets'"):
            s.add("2026-09-01", "expense", "gadgets", "5", "EUR")
        for bad in ("2026-13-01", "20260901", "2026-02-30"):
            with self.assertRaises(ValidationError, msg=bad):
                s.add(bad, "expense", "food", "5", "EUR")

    def test_smallest_valid_amount_accepted(self):
        s = BudgetService()
        self.assertEqual(s.add("2026-09-01", "expense", "food", "0.01", "EUR").amount, 0.01)

    def test_sample_file_reports_each_bad_row(self):
        good, errors = storage.load(ROOT / "data" / "sample_transactions.csv")
        self.assertEqual(len(good), 4)
        self.assertEqual(len(errors), 8)
        self.assertIn("Row 6: amount must be > 0.", errors)
        self.assertTrue(any("duplicate id 'T002'" in e for e in errors))


class Persistence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "t.csv"

    def tearDown(self):
        self.tmp.cleanup()

    def cli(self, *argv):
        return run(build_parser().parse_args(["--data", str(self.path), *argv]),
                   out=lambda *_: None)

    def test_round_trip(self):
        s = BudgetService()
        s.add("2026-09-04", "expense", "food", "18.5", "EUR")
        storage.save(self.path, s.transactions)
        loaded, errors = storage.load(self.path)
        self.assertEqual((loaded, errors), (s.transactions, []))

    def test_undo_is_persisted_and_survives_reload(self):
        self.cli("add", "2026-09-01", "income", "salary", "100", "EUR")
        self.cli("add", "2026-09-02", "expense", "food", "10", "EUR")
        self.assertEqual(self.cli("undo"), 0)
        loaded, _ = storage.load(self.path)          # simulates crash + restart
        self.assertEqual([t.id for t in loaded], ["T001"])
        self.cli("add", "2026-09-03", "expense", "food", "7", "EUR")
        loaded, _ = storage.load(self.path)
        self.assertEqual([t.id for t in loaded], ["T001", "T002"])

    def test_undo_on_empty_ledger_fails_cleanly(self):
        self.assertEqual(self.cli("undo"), 1)

    def test_add_refused_when_file_has_bad_rows(self):
        self.path.write_text("id,date,kind,category,amount,currency\n"
                             "T001,2026-09-01,expense,food,-1,EUR\n")
        before = self.path.read_text()
        self.assertEqual(self.cli("add", "2026-09-02", "expense", "food", "5", "EUR"), 1)
        self.assertEqual(self.path.read_text(), before)


if __name__ == "__main__":
    unittest.main()
