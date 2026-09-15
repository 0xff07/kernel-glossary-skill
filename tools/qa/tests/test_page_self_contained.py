"""Behavior and boundaries for page self contained."""
import unittest
from checks.page_self_contained import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_local_link_and_external_url(self):
        bad = list(check(page('See [the sibling](../other.md).'), None))
        self.assertTrue(any(f.line == 1 and f.severity == 'FAIL' and 'link target' in f.message for f in bad))
        good = list(check(page('See [the notes](https://example.org/notes.md).'), None))
        self.assertFalse(any(f.severity == 'FAIL' for f in good))

    def test_anonymous_handoffs_and_named_reference_deduplication(self):
        for text in ('The chain is documented elsewhere.', 'A helper another page owns.'):
            found = list(check(page(text), None))
            self.assertTrue(any(f.severity == 'review' and 'ANONYMOUS HANDOFF' in f.message for f in found))
        found = list(check(page('The arithmetic is bandwidth/credits.md\'s.'), None))
        self.assertEqual(len([f for f in found if f.severity == 'review']), 1)

    def test_owning_column_accounts_for_its_cells_and_escaped_pipes(self):
        text = '| helper | role | owning page |\n|---|---|---|\n| a | x \\| y | a/b.md |\n| b | role | a/c.md |'
        found = list(check(page(text), None))
        candidates = [f for f in found if f.severity != 'note']
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].line, 1)
        self.assertIn('OWNING-PAGE COLUMN', candidates[0].message)

    def test_code_quotes_and_named_source_marker(self):
        for text in ('`TODO x.md`', 'the FIXME in the switch above', '```c\nTODO x.md\n```'):
            self.assertFalse([f for f in check(page(text), None) if f.severity != 'note'], text)
        self.assertTrue(any(f.severity == 'FAIL' for f in check(page('TODO finish'), None)))
