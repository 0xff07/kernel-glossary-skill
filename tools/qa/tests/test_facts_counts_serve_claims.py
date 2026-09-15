"""Behavior and boundaries for facts counts serve claims."""
import unittest
from checks.facts_counts_serve_claims import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_census_is_a_work_item_not_a_verdict(self):
        found = list(check(page('Only three callers reach the helper.'), None))
        self.assertTrue(any(f.line == 1 and f.severity == 'review' and 'CONTAINS UNIVERSAL WORD' in f.message for f in found))
        self.assertFalse(any('SERVES-A-CLAIM' in f.message for f in found))
        self.assertFalse(any(f.severity == 'review' for f in check(page('The ring holds sixteen slots.'), None)))

    def test_count_columns_and_escaped_pipes(self):
        text = '| member | role | reads |\n|---|---|---|\n| a | x \\| y | 9 |\n| b | clear | 3 |\n\n| field | bit |\n|---|---|\n| a | 0 |\n| b | 1 |'
        found = list(check(page(text), None))
        candidates = [f for f in found if f.severity == 'review']
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].line, 1)
        self.assertIn('| reads |', candidates[0].message)

    def test_hyphenated_numeral_and_fence_mask(self):
        text = 'Twenty-six call sites reach the helper.'
        self.assertTrue(any(f.severity == 'review' for f in check(page(text), None)))
        self.assertFalse(any(f.severity == 'review' for f in check(page('```c\n'+text+'\n```'), None)))


class TriggerWords(unittest.TestCase):

    def test_the_single_and_once_carry_a_universal_word(self):
        for text in ('The single owner has three call sites in probe.', 'Once armed, three call sites reach the helper.'):
            found = list(check(page(text), None))
            self.assertTrue(any(f.severity == 'review' and 'CONTAINS UNIVERSAL WORD' in f.message for f in found), text)
