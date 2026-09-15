"""Behavior and boundaries for arrangement paragraphs."""
import unittest
from checks.arrangement_paragraphs import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_word_threshold_and_consecutive_paragraphs(self):
        paragraph = ' '.join(['word'] * 121) + '.'
        found = list(check(page(skeleton(details='### A\n\n'+paragraph)), None))
        self.assertTrue(any(f.severity == 'review' and 'words=121' in f.message for f in found))
        text = skeleton(details='### A\n\nA first sentence.\n\nA second sentence.')
        found = list(check(page(text), None))
        self.assertTrue(any(f.severity == 'review' and '2 consecutive paragraphs' in f.message for f in found))
        separated = text.replace('\n\nA second', '\n\n'+EXCERPT+'\n\nA second')
        self.assertFalse(any('2 consecutive paragraphs' in f.message for f in check(page(separated), None)))

    def test_three_long_sentences(self):
        text = ' '.join([' '.join(['word'] * 36)+'.'] * 3)
        self.assertTrue(any('3 consecutive sentences' in f.message for f in check(page(skeleton(details='### A\n\n'+text)), None)))
