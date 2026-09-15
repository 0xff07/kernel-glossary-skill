"""Behavior and boundaries for excerpts post fence subject."""
import unittest
from checks.excerpts_post_fence_subject import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_pronoun_and_linked_symbol(self):
        bad = list(check(page(skeleton(details=EXCERPT+'\n\nIt records the head.')), None))
        self.assertTrue(any(f.severity == 'review' and f.data and 'opens-on-pronoun-or-no-symbol' in f.data.get('flags', []) for f in bad))
        good = list(check(page(skeleton(details=EXCERPT+f'\n\n[`struct kg_ring`]({URL}) records the head.')), None))
        self.assertFalse(any(f.data and f.data.get('flags') for f in good))
        self.assertTrue(any(f.severity == 'review' for f in good))
