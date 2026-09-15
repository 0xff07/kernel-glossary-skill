"""Behavior and boundaries for arrangement headings."""
import unittest
from checks.arrangement_headings import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_ten_words_is_within_the_band(self):
        for count in (10,11):
            found = list(check(page(skeleton(details='### '+' '.join(['word']*count)+'\n\n'+PROSE)), None))
            reviews = [f for f in found if f.severity == 'review']
            self.assertEqual(len(reviews), int(count == 11))
            if reviews:
                self.assertIn('words=11', reviews[0].message)
