"""Run with: python3 -m unittest discover -s tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import datacheck  # noqa: E402


class FoodChecks(unittest.TestCase):
    def data(self, **over):
        d = {"groups": ["Bread", "Drinks"], "curated": [["White bread", "Bread", 42.1, "g", [["1 slice", 36]], "11-980"]],
             "cofid": [["11-981", "Bread, wholemeal", 0, 38.4, 0]]}
        d.update(over)
        return d

    def test_good_data_passes(self):
        self.assertEqual(datacheck.check_foods(self.data()), [])

    def test_out_of_range_carbs(self):
        bad = self.data(curated=[["White bread", "Bread", 142, "g", [["1 slice", 36]], "11-980"]])
        self.assertTrue(datacheck.check_foods(bad))

    def test_portion_too_large(self):
        bad = self.data(curated=[["White bread", "Bread", 42.1, "g", [["1 slice", 3600]], "11-980"]])
        self.assertTrue(datacheck.check_foods(bad))

    def test_repeated_name(self):
        row = ["White bread", "Bread", 42.1, "g", [], "11-980"]
        self.assertTrue(datacheck.check_foods(self.data(curated=[row, row[:5] + ["11-1"]])))

    def test_zero_carb_bread_is_flagged_for_review(self):
        warn = []
        datacheck.check_foods(self.data(cofid=[["11-1", "Bread, odd", 0, 0, 0]]), warn)
        self.assertEqual(len(warn), 1)


class ChainChecks(unittest.TestCase):
    def chain(self, items):
        return [{"chain": "Greggs", "source": "s", "url": "u", "date": "d", "items": items}]

    def test_good_chain_passes(self):
        self.assertEqual(datacheck.check_chains(self.chain([["Bakes", "Sausage roll", 23.0]])), [])

    def test_repeated_item(self):
        self.assertTrue(datacheck.check_chains(self.chain([["A", "Sausage roll", 23.0], ["B", "Sausage roll", 23.0]])))

    def test_implausible_carbs(self):
        self.assertTrue(datacheck.check_chains(self.chain([["Bakes", "Sausage roll", 2300.0]])))


class Generated(unittest.TestCase):
    def test_generated_files_pass(self):
        self.assertEqual(datacheck.main(), 0)


if __name__ == "__main__":
    unittest.main()
