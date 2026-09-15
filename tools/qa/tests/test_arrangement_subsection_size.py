"""Behavior and boundaries for arrangement subsection size."""
import unittest
from checks.arrangement_subsection_size import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_thresholds_and_boundary(self):
        for words in (400,600):
            found = list(check(page(skeleton(details='### A\n\n'+' '.join(['word']*words))), None))
            self.assertFalse(any(f.severity == 'review' for f in found))
        found = list(check(page(skeleton(details='### A\n\n'+' '.join(['word']*601))), None))
        self.assertTrue(any(f.severity == 'review' and 'words=601' in f.message for f in found))
        found = list(check(page(skeleton(details='### A\n\n'+'\n\n'.join(['A sentence.']*9))), None))
        self.assertTrue(any(f.severity == 'review' and 'paragraphs=9' in f.message for f in found))
