"""Behavior and boundaries for excerpts catalog parity."""
import unittest
from checks.excerpts_catalog_parity import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_missing_and_reproduced_catalog_symbol(self):
        found = list(check(page(skeleton()), None))
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].severity, 'FAIL')
        self.assertIn('kg_ring', found[0].message)
        self.assertEqual(list(check(page(skeleton(details=EXCERPT)), None)), [])
