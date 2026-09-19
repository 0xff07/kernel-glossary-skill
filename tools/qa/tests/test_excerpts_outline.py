"""kind: rule — a function walked in pieces has an outline table above its first piece whose rows are the pieces, and each piece's introduction carries its mark."""
import os
import shutil
import tempfile
import unittest
from checks import excerpts_outline as rule
from inputs import MissingInput
from tests.support import CAUTION, PROSE, page, TestInputs, observed
RING_C = ['int kg_ring_push(struct kg_ring *ring, int v)', '{', '\tif (ring->head == 3)', '\t\treturn -ENOSPC;',
          '\tring->head++;', '\treturn 0;', '}']
BASE = 'https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.c'
LINK = f'[`kg_ring_push()`]({BASE}#L1)'

def fence(cited, *lines):
    return f'```c\n/* drivers/kg/ring.c:{cited} */\n' + '\n'.join(lines) + '\n```'

def page_with(*details):
    body = '\n\n'.join(details)
    return page(f"# The kg ring\n\n{CAUTION}\n\nA ring hands values from a producer to a consumer.\n\n## SUMMARY\n\nThe model is one struct.\n\n"
                f"## SPECIFICATIONS\n\nNone applies.\n\n## COVERAGE\n\n### Functions\n\n- [`'\\<kg_ring_push\\>':'drivers/kg/ring.c'`]({BASE}#L1): the push\n\n"
                f"## DOCUMENTATION\n\n## OTHER SOURCES\n\n## DETAILS\n\n### A\n\n{body}\n\n{PROSE}\n")
OUTLINE = '| piece | lines | stage |\n|---|---|---|\n| ① | ring.c:1-4 | the guard |\n| ② | ring.c:5-7 | the advance |'

class Outline(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, 'drivers', 'kg'))
        open(os.path.join(self.root, 'drivers', 'kg', 'ring.c'), 'w', encoding='utf-8').write('\n'.join(RING_C) + '\n')

    def tearDown(self):
        shutil.rmtree(self.root)

    def run_on(self, *details):
        return observed(rule.check(page_with(*details), TestInputs(tree=self.root)))

    def fails(self, found):
        return [f.message for f in found.all if f.severity == 'FAIL']

    def test_an_outlined_walk_with_marked_pieces_passes(self):
        found = self.run_on(PROSE, OUTLINE, f'Piece ① of {LINK} guards the push.', fence(1, *RING_C[:4]), f'Piece ② of {LINK} advances the head.', fence(5, *RING_C[4:7]))
        self.assertEqual(self.fails(found), [])
        self.assertEqual(found.footer, 'walked=1 outlined=1 pieces=2 marked=2')

    def test_no_outline_wrong_rows_and_an_unmarked_piece_fail(self):
        found = self.run_on(f'{LINK} guards the push.', fence(1, *RING_C[:4]), f'{LINK} advances the head.', fence(5, *RING_C[4:7]))
        self.assertIn('is walked in 2 pieces with no outline table', self.fails(found)[0])
        wrong = OUTLINE.replace('ring.c:5-7', 'ring.c:5-6')
        found = self.run_on(PROSE, wrong, f'Piece ① of {LINK}.', fence(1, *RING_C[:4]), f'Piece ② of {LINK}.', fence(5, *RING_C[4:7]))
        self.assertTrue(any('do not match the pieces shown' in f for f in self.fails(found)))
        found = self.run_on(PROSE, OUTLINE, f'Piece ① of {LINK}.', fence(1, *RING_C[:4]), f'{LINK} advances the head.', fence(5, *RING_C[4:7]))
        self.assertTrue(any('piece 2 (ring.c:5-7) is not introduced with its mark ②' in f for f in self.fails(found)))

    def test_a_function_shown_whole_needs_no_outline_and_a_missing_tree_is_reported(self):
        found = self.run_on(f'{LINK} whole.', fence(1, *RING_C))
        self.assertEqual(found.footer, 'walked=0 outlined=0 pieces=0 marked=0')
        with self.assertRaises(MissingInput):
            list(rule.check(page_with(PROSE), TestInputs(tree=None)))
if __name__ == '__main__':
    unittest.main()
