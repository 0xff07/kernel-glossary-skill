"""Behavior and boundaries for arrangement units."""
import unittest
from checks.arrangement_units import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_inventory_and_optional_baseline(self):
        now = skeleton(details=f'### A\n\n{PROSE}\n\n{EXCERPT}\n\n{PROSE}')
        found = list(check(page(now), TestInputs()))
        self.assertTrue(any(f.data and f.data.get('maps') == ['P C P'] for f in found))
        self.assertTrue(any(f.data and f.data.get('inventory') for f in found))
        self.assertTrue(any('no committed baseline' in f.message for f in found))
        changed = list(check(page(now), TestInputs(baseline=skeleton())))
        self.assertTrue(any(f.data and f.data.get('added') == 1 for f in changed))
        self.assertTrue(any('structured block added' in f.message for f in changed))
