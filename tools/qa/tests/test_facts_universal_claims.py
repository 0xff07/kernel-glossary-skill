"""Behavior and boundaries for facts universal claims."""
import unittest
from checks.facts_universal_claims import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_candidate_and_similar_non_candidate(self):
        found = list(check(page('Only the helper releases the ring.'), TestInputs()))
        self.assertTrue(any(f.line == 1 and f.severity == 'review' and 'UNIVERSAL' in f.message for f in found))
        self.assertFalse(any(f.severity == 'review' for f in check(page('The ring holds values.'), TestInputs())))

    def test_fence_and_catalog_are_excluded(self):
        text = '```c\n'+'Only the helper releases the ring.'+'\n```\n\n## COVERAGE\n\n'+'Only the helper releases the ring.'
        self.assertFalse(any(f.severity == 'review' for f in check(page(text), TestInputs())))

    def test_baseline_tag_is_preserved(self):
        found = list(check(page('Only the helper releases the ring.'), TestInputs(baseline='Only the helper releases the ring.')))
        self.assertTrue(any('[carried]' in f.message for f in found))

    def test_count_only_sentence_is_not_a_universal_claim(self):
        found = list(check(page('Three callers allocate it. Only three callers free it.'), TestInputs()))
        reviews = [f for f in found if f.severity == 'review']
        self.assertEqual(len(reviews), 1)
        self.assertIn('UNIVERSAL [n/a]', reviews[0].message)
        self.assertNotIn('COUNT', reviews[0].message)

    def test_link_text_matches_the_normalized_baseline(self):
        found = list(check(page('[Every](https://example.org) caller releases it.'),
                           TestInputs(baseline='Every caller releases it.')))
        self.assertEqual(found[-1].data, {'sentences': 1, 'new_since_commit': 0})
        self.assertTrue(any('[carried]' in f.message for f in found))


class TriggerWords(unittest.TestCase):

    def test_the_single_and_once_select_a_sentence(self):
        for text in ('The single caller of the helper frees the ring.', 'The helper runs once per probe.'):
            found = list(check(page(text), TestInputs()))
            self.assertTrue(any(f.severity == 'review' and 'UNIVERSAL' in f.message for f in found), text)
