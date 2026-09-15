"""Behavior and boundaries for purpose openers."""
import unittest
from checks.purpose_openers import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_every_opener_is_a_reading_item_with_observed_flags(self):
        found = list(check(page(skeleton(details=f'### A\n\n[`struct kg_ring`]({URL}) holds the indexes.')), None))
        flagged = [f for f in found if f.data and 'symbol-led' in f.data.get('flags', [])]
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged[0].severity, 'review')
        self.assertTrue(any(f.severity == 'review' and f.data == {'flags': []} for f in found))
        self.assertFalse(any(f.data and 'symbol-led' in f.data.get('flags', []) for f in check(page(skeleton()), None)))
