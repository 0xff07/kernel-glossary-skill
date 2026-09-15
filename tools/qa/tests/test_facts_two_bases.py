"""Behavior and boundaries for facts two bases."""
import unittest
from checks.facts_two_bases import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_candidate_and_similar_non_candidate(self):
        found = list(check(page('Three callers reach the helper.'), TestInputs()))
        self.assertTrue(any(f.line == 1 and f.severity == 'review' and 'COUNT' in f.message for f in found))
        self.assertFalse(any(f.severity == 'review' for f in check(page('The ring holds values.'), TestInputs())))

    def test_fence_and_catalog_are_excluded(self):
        text = '```c\n'+'Three callers reach the helper.'+'\n```\n\n## COVERAGE\n\n'+'Three callers reach the helper.'
        self.assertFalse(any(f.severity == 'review' for f in check(page(text), TestInputs())))

    def test_baseline_tag_is_preserved(self):
        found = list(check(page('Three callers reach the helper.'), TestInputs(baseline='Three callers reach the helper.')))
        self.assertTrue(any('[carried]' in f.message for f in found))

    def test_ordinal_scope_and_rule_owned_label(self):
        found = list(check(page('The first caller allocates it. Only three callers free it.'), TestInputs()))
        reviews = [f for f in found if f.severity == 'review']
        self.assertEqual(len(reviews), 2)
        self.assertTrue(all('COUNT [n/a]' in f.message for f in reviews))
        self.assertFalse(any('UNIVERSAL' in f.message for f in reviews))

    def test_code_and_link_normalization_preserve_new_counts(self):
        text = '`three` callers use [the ring](https://example.org/42). Four callers free it.'
        found = list(check(page(text), TestInputs(baseline='Two callers free it.')))
        reviews = [f for f in found if f.severity == 'review']
        self.assertEqual(len(reviews), 1)
        self.assertIn('Four callers free it.', reviews[0].message)
        self.assertEqual(found[-1].data, {'sentences': 1, 'new_since_commit': 1})
