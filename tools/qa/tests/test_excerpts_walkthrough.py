"""kind: rule — a function the catalog names is read whole: one excerpt, or consecutive pieces
in page order from the signature to the closing brace; missing lines fail, a piece shown before
the walk reaches it is a review row, lines shown again are counted."""
import os
import shutil
import tempfile
import unittest
from checks import excerpts_walkthrough as rule
from inputs import MissingInput
from tests.support import CAUTION, PROSE, page, skeleton, TestInputs, observed
RING_C = ['int kg_ring_push(struct kg_ring *ring, int v)', '{', '\tif (ring->head == 3)', '\t\treturn -ENOSPC;',
          '\tring->head++;', '\treturn 0;', '}', '', 'static void kg_ring_reset(struct kg_ring *ring)', '{',
          '\tring->head = 0;', '\tring->tail = 0;', '}']
BASE = 'https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/'

def fence(cited, *lines):
    return f'```c\n/* drivers/kg/ring.c:{cited} */\n' + '\n'.join(lines) + '\n```'

def catalog(*entries):
    return '\n'.join(f"- [`'\\<{name}\\>':'drivers/kg/ring.c'`]({BASE}ring.c#L{line}): {name}" for name, line in entries)

def page_with(entries, *details):
    body = '\n\n'.join(f'{PROSE}\n\n{d}' for d in details)
    text = (f"# The kg ring\n\n{CAUTION}\n\nA ring hands values from a producer to a consumer.\n\n## SUMMARY\n\nThe model is one struct.\n\n"
            "## SPECIFICATIONS\n\nNone applies.\n\n## COVERAGE\n\n### Functions\n\n" + catalog(*entries) +
            f"\n\n## DOCUMENTATION\n\n## OTHER SOURCES\n\n## DETAILS\n\n### A\n\n{body}\n\n{PROSE}\n")
    return page(text)

class Walkthrough(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, 'drivers', 'kg'))
        open(os.path.join(self.root, 'drivers', 'kg', 'ring.c'), 'w', encoding='utf-8').write('\n'.join(RING_C) + '\n')

    def tearDown(self):
        shutil.rmtree(self.root)

    def run_on(self, entries, *details):
        return observed(rule.check(page_with(entries, *details), TestInputs(tree=self.root)))

    def severities(self, found, severity):
        return [f.message for f in found.all if f.severity == severity]

    def test_a_function_read_whole_in_one_excerpt(self):
        found = self.run_on([('kg_ring_push', 1)], fence(1, *RING_C[:7]))
        self.assertEqual(self.severities(found, 'FAIL'), [])
        self.assertEqual(found.footer, 'functions=1 whole=1 walked=0 incomplete=0 previewed=0 pieces=1 reshown-lines=0')

    def test_consecutive_pieces_walk_the_function_through(self):
        found = self.run_on([('kg_ring_push', 1)], fence(1, *RING_C[:4]), fence(5, *RING_C[4:7]))
        self.assertEqual(self.severities(found, 'FAIL'), [])
        self.assertIn('walked=1', found.footer)
        self.assertIn('pieces=2', found.footer)

    def test_lines_never_shown_fail_and_are_named(self):
        found = self.run_on([('kg_ring_push', 1)], fence(1, *RING_C[:4]))
        fails = self.severities(found, 'FAIL')
        self.assertEqual(len(fails), 1)
        self.assertIn('kg_ring_push() (ring.c:1-7, 7 lines) is not read whole: lines 5-7 are never shown', fails[0])
        self.assertIn('incomplete=1', found.footer)

    def test_a_piece_shown_before_the_walk_reaches_it_is_a_review_row(self):
        found = self.run_on([('kg_ring_push', 1)], fence(5, *RING_C[4:7]), fence(1, *RING_C[:4]))
        self.assertEqual(self.severities(found, 'FAIL'), [])
        reviews = self.severities(found, 'review')
        self.assertEqual(len(reviews), 1)
        self.assertIn('kg_ring_push() is shown out of order: page', reviews[0])
        self.assertIn('shows 5-7 before the walk reaches those lines', reviews[0])

    def test_lines_shown_again_are_counted_and_do_not_break_the_walk(self):
        found = self.run_on([('kg_ring_push', 1)], fence(1, *RING_C[:7]), fence(5, *RING_C[4:6]))
        self.assertEqual(self.severities(found, 'FAIL'), [])
        self.assertIn('whole=1', found.footer)
        self.assertIn('reshown-lines=2', found.footer)

    def test_an_anchor_inside_the_body_still_names_the_function_and_a_struct_is_ignored(self):
        found = self.run_on([('kg_ring_push', 5), ('kg_ring_reset', 9)], fence(1, *RING_C[:7]))
        self.assertIn('functions=2', found.footer)
        self.assertIn('kg_ring_reset() (ring.c:9-13, 5 lines) is not read whole: lines 9-13 are never shown', self.severities(found, 'FAIL')[0])
        found = observed(rule.check(page(skeleton(details=f'### A\n\n{PROSE}\n')), TestInputs(tree=self.root)))
        self.assertIn('functions=0', found.footer)

    def test_a_missing_tree_is_reported(self):
        with self.assertRaises(MissingInput):
            list(rule.check(page(skeleton()), TestInputs(tree=None)))
if __name__ == '__main__':
    unittest.main()
