"""kind: rule — nothing inside a function is elided; a long definition drops one run of members
behind a numbered marker, every run after it at least three lines or the closing line alone; a
`...` that ends a unit, or stands between two units, is a truncation."""
import os
import shutil
import tempfile
import unittest
from checks import excerpts_contiguity as rule
from tests.support import PROSE, page, skeleton, TestInputs, observed
RING_H = ['struct kg_ring {', '\tint a;', '\tint b;', '\tint c;', '\tint d;', '\tint e;', '\tint f;', '};', '',
          'static inline int kg_ring_full(struct kg_ring *ring)', '{', '\tint x = 1;', '\tint y = 2;', '\tint z = 3;',
          '\treturn x + y + z;', '}']

class Contiguity(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, 'drivers', 'kg'))
        open(os.path.join(self.root, 'drivers', 'kg', 'ring.h'), 'w', encoding='utf-8').write('\n'.join(RING_H) + '\n')

    def tearDown(self):
        shutil.rmtree(self.root)

    def run_on(self, cited, *lines, tree=True):
        fence = f'```c\n/* drivers/kg/ring.h:{cited} */\n' + '\n'.join(lines) + '\n```'
        inputs = TestInputs(tree=self.root) if tree else TestInputs()
        found = observed(rule.check(page(skeleton(details=f'### A\n\n{PROSE}\n\n{fence}\n\n{PROSE}\n')), inputs))
        return [f.message for f in found.all if f.severity == 'FAIL'], found.footer

    def test_a_definition_drops_one_run_behind_a_numbered_marker(self):
        fails, footer = self.run_on(1, 'struct kg_ring {', '\tint a;', '... /* 3 lines, to :6 */', '\tint e;', '\tint f;', '};')
        self.assertEqual(fails, [])
        self.assertEqual(footer, 'units=1 elisions=1 elided=1 in-functions=0 findings=0')
        fails, _ = self.run_on(1, 'struct kg_ring {', '... /* 6 lines, to :8 */', '};')
        self.assertEqual(fails, [])

    def test_two_elisions_in_a_definition_fail(self):
        fails, _ = self.run_on(1, 'struct kg_ring {', '...', '\tint c;', '\tint d;', '\tint e;', '...', '};')
        self.assertEqual(len(fails), 1)
        self.assertIn('2 elisions, at most one', fails[0])

    def test_a_short_run_after_the_elision_fails_unless_it_closes(self):
        fails, _ = self.run_on(1, 'struct kg_ring {', '...', '\tint f;', '};')
        self.assertEqual(len(fails), 1)
        self.assertIn("a run of 2 after an elision ('int f; / };'), at least 3 lines", fails[0])

    def test_an_elision_inside_a_function_fails(self):
        fails, footer = self.run_on(10, 'static inline int kg_ring_full(struct kg_ring *ring)', '{', '...', '\treturn x + y + z;', '}')
        self.assertEqual(len(fails), 1)
        self.assertIn('elides inside kg_ring_full(): nothing inside a function is elided', fails[0])
        self.assertIn('in-functions=1', footer)

    def test_a_trailing_or_stitching_elision_is_a_truncation(self):
        fails, _ = self.run_on(1, 'struct kg_ring {', '\tint a;', '\tint b;', '...')
        self.assertEqual(len(fails), 1)
        self.assertIn('ends on an elision, which truncates the construct', fails[0])
        fails, footer = self.run_on(1, 'struct kg_ring {', '\tint a;', '\tint b;', '...', '/* drivers/kg/ring.h:10 */', 'static inline int kg_ring_full(struct kg_ring *ring)', '{')
        self.assertEqual(len(fails), 1)
        self.assertIn("before the next unit's provenance comment; the comment marks the jump, so drop the `...`", fails[0])
        self.assertEqual(footer, 'units=2 elisions=1 elided=1 in-functions=0 findings=1')

    def test_an_unelided_unit_is_not_counted_and_no_tree_still_counts_runs(self):
        fails, footer = self.run_on(1, 'struct kg_ring {', '\tint a;', '};')
        self.assertEqual(fails, [])
        self.assertEqual(footer, 'units=1 elisions=0 elided=0 in-functions=0 findings=0')
        fails, _ = self.run_on(1, 'struct kg_ring {', '...', '\tint f;', '};', tree=False)
        self.assertEqual(len(fails), 1)
if __name__ == '__main__':
    unittest.main()
