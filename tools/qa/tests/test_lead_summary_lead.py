"""Behavior and boundaries for lead summary lead."""
import unittest
from checks.lead_summary_lead import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_word_limit_and_sentence_inventory(self):
        text = skeleton(lead=' '.join(['word'] * 220))
        self.assertFalse([f for f in check(page(text), None) if f.severity == 'FAIL'])
        found = list(check(page(skeleton(lead=' '.join(['word'] * 221))), None))
        self.assertTrue(any(f.severity == 'FAIL' and 'words=' in f.message for f in found))
        self.assertTrue(any(f.severity == 'review' and '[ ]' in f.message for f in found))

    def test_structured_blocks(self):
        found = list(check(page(skeleton(lead=PROSE+'\n\n'+EXCERPT)), None))
        self.assertTrue(any(f.severity == 'FAIL' and 'source excerpt' in f.message for f in found))
        self.assertFalse([f for f in check(page(skeleton()), None) if f.severity == 'FAIL'])


class Lists(unittest.TestCase):

    def test_a_numbered_list_in_the_lead_is_a_list(self):
        found = list(check(page(skeleton(lead=PROSE + '\n\n1. The first item.\n2. The second item.\n\n' + PROSE)), None))
        self.assertTrue(any(f.severity == 'FAIL' and f.message == 'lead: a list' for f in found), [f.message for f in found])
