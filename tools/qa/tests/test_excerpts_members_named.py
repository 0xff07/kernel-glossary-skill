"""Behavior and boundaries for excerpts members named."""
import unittest
from checks.excerpts_members_named import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_members_not_named_and_named_in_prose(self):
        bad = list(check(page(skeleton(details=EXCERPT+'\n\nThe device starts.')), None))
        self.assertTrue(any(f.severity == 'review' and f.data and 'none-named' in f.data.get('flags', []) for f in bad))
        good = list(check(page(skeleton(details=EXCERPT+'\n\nThe head and tail advance.')), None))
        self.assertTrue(any('2/2 named' in f.message for f in good))
        self.assertFalse(any(f.data and f.data.get('flags') for f in good))
