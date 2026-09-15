"""Examples, counterexamples and masks for style.verification-narration."""
import unittest
from checks.style_verification_narration import check
from tests.support import MINIMAL_PAGE, page

class Examples(unittest.TestCase):
    def test_example_0(self):
        found = list(check(page(''.join(MINIMAL_PAGE.splitlines(keepends=True)[:34] + ['The producer writes at the head and the consumer reads at the tail, and the difference between the two indexes is the number of stored values. [`struct kg_ring`](https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.h#L12) holds both indexes beside the slot array. Three callers exist, by a grep for the name across drivers/ at this tree.\n'] + MINIMAL_PAGE.splitlines(keepends=True)[35:])), None))
        for expected in [(35, 'FAIL', 'verification narration: …th indexes beside the slot array. Three callers exist, by a grep for the name across drivers/ at this tree.… (the fix: delete the method clause, keep the result and its scope)')]:
            self.assertIn(expected, [(f.line, f.severity, f.message) for f in found])

    def test_minimal_page_has_no_violations(self):
        self.assertFalse([f for f in check(page(MINIMAL_PAGE), None) if f.severity == 'FAIL'])

    def test_source_excerpt_is_not_prose(self):
        text = '# Title\n\n```c\n' + ' '.join(['— **bold** usually walks straightforward vtable']) + '\n```\n'
        self.assertFalse([f for f in check(page(text), None) if f.severity == 'FAIL'])


class TreeWide(unittest.TestCase):

    def test_a_tree_wide_search_is_narration_in_any_position(self):
        for text in ('A tree-wide search finds three callers of the helper.', 'Three callers reach it, by a search of the drivers.'):
            found = list(check(page(text), None))
            self.assertTrue(any(f.severity == 'FAIL' and 'verification narration' in f.message for f in found), text)
