"""Behavior and boundaries for style run on enumeration."""
import unittest
from checks.style_run_on_enumeration import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_reading_candidates_and_location_flags(self):
        text = 'The callers are a.c:1, b.c:2, c.c:3, and d.c:4.'
        found = list(check(page(text), None))
        self.assertTrue(any(f.severity == 'review' and f.data and 'four-or-more-locations' in f.data.get('flags', []) for f in found))
        self.assertFalse(any(f.severity == 'review' for f in check(page('The ring advances and wraps.'), None)))
