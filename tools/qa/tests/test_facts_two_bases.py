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
        self.assertEqual(found[-1].data, {'sentences': 1, 'with_basis': 0, 'without_basis': 1, 'new_since_commit': 1, 'stale_bases': 0})

    def test_a_recorded_basis_turns_the_row_into_a_note_and_a_stale_row_is_reported(self):
        dossier = ('## EVIDENCE\n### Bases\n| line | claim | basis 1 | basis 2 | result |\n|---|---|---|---|---|\n'
                   '| 1 | Three callers reach | find_callers | git grep -n | agrees |\n'
                   '| 1 | Nine callers | git grep | read | agrees |\n| 7 | anything | x | y | z |\n\npage sha256: ' + 'a' * 64 + '\n')
        found = list(check(page('Three callers reach the helper. Four callers free it.'), TestInputs(dossier=dossier)))
        reviews = [f for f in found if f.severity == 'review']
        self.assertEqual(len(reviews), 1)
        self.assertIn('Four callers free it.', reviews[0].message)
        self.assertTrue(any(f.severity == 'note' and 'Three callers reach the helper.' in f.message and 'basis recorded' in f.message for f in found))
        self.assertEqual(sum(1 for f in found if 'names no sentence there' in f.message), 2)
        self.assertEqual(found[-1].data, {'sentences': 2, 'with_basis': 1, 'without_basis': 1, 'new_since_commit': None, 'stale_bases': 2})
