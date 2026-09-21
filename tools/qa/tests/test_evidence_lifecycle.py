"""kind: rule — every row of the worksheet's Lifecycle table is an assignment to the named field
inside the named writer at a cited site, its mark stands in a figure legend, and every writer of a
drawn field the tree holds has a row."""
import os
import shutil
import tempfile
import unittest
from checks import evidence_lifecycle as rule
from inputs import MissingInput
from tests.support import PROSE, page, skeleton, TestInputs, observed
RING_H = '\n' * 11 + 'struct kg_ring {\n\tunsigned int head;\n\tunsigned int tail;\n};\n'
RING_C = ['int kg_ring_push(struct kg_ring *ring, int v)', '{', '\tring->head++;', '\treturn 0;', '}', '',
          'void kg_ring_reset(struct kg_ring *ring)', '{', '\tring->head = 0;', '\tring->tail = 0;', '}']
FIGURE = '```\n    ┌──────┐  ①  ┌──────┐\n    │ push │ ──► │ head │ ②\n    └──────┘     └──────┘\n    ① kg_ring_push ring.c:3  head advances by one\n    ② kg_ring_reset :9  head returns to zero\n```'
EXCERPTS = '```c\n/* drivers/kg/ring.c:1 */\n' + '\n'.join(RING_C) + '\n```'
HEADER = '## EVIDENCE\n### Lifecycle\n| object | field | mark | writer | site | event | value |\n|---|---|---|---|---|---|---|\n'

def table(*rows):
    return HEADER + '\n'.join(rows) + '\n'

class Lifecycle(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, 'drivers', 'kg'))
        open(os.path.join(self.root, 'drivers', 'kg', 'ring.h'), 'w', encoding='utf-8').write(RING_H)
        open(os.path.join(self.root, 'drivers', 'kg', 'ring.c'), 'w', encoding='utf-8').write('\n'.join(RING_C) + '\n')

    def tearDown(self):
        shutil.rmtree(self.root)

    def run_on(self, worksheet):
        details = f'### A\n\n{PROSE}\n\n{EXCERPTS}\n\n{PROSE}\n\n{FIGURE}\n\n{PROSE}\n'
        return observed(rule.check(page(skeleton(details=details)), TestInputs(tree=self.root, worksheet=worksheet)))

    def by(self, found, severity):
        return [f.message for f in found.all if f.severity == severity]

    def test_complete_rows_verify(self):
        found = self.run_on(table('| `struct kg_ring` | head | ① | kg_ring_push | ring.c:3 | push | +1 |',
                                  '| `struct kg_ring` | head | ② | kg_ring_reset | ring.c:9 | reset | 0 |'))
        self.assertEqual(self.by(found, 'FAIL'), [])
        self.assertEqual(self.by(found, 'review'), [])
        self.assertEqual(found.footer, 'rows=2 objects=1 verified=2 uncorroborated=0 missing-writers=0 excluded-files=0 findings=0')

    def test_a_missing_writer_and_an_unmarked_row_are_review_rows(self):
        found = self.run_on(table('| `struct kg_ring` | head | ① | kg_ring_push | ring.c:3 | push | +1 |'))
        self.assertEqual(self.by(found, 'FAIL'), [])
        self.assertIn('struct kg_ring.head: kg_ring_reset() also writes it (ring.c:9) and has no row', self.by(found, 'review')[0])
        found = self.run_on(table('| `struct kg_ring` | head | ① | kg_ring_push | ring.c:3 | push | +1 |') + 'excluded: ring.c (the reset path is another page\'s)\n')
        self.assertEqual([r for r in self.by(found, 'review') if 'also writes' in r], [])
        found = self.run_on(table('| `struct kg_ring` | tail | ③ | kg_ring_reset | ring.c:10 | reset | 0 |'))
        self.assertIn('no figure legend on the page carries this mark with this writer', self.by(found, 'review')[0])
        found = self.run_on(table('| `struct kg_ring` | tail | ② | kg_ring_reset | ring.c:10 | reset | 0 |'))
        self.assertIn('the legend phrase does not name tail', self.by(found, 'review')[0])

    def test_wrong_rows_fail(self):
        found = self.run_on(table('| `struct kg_ring` | head | ① | kg_ring_push | ring.c:4 | push | +1 |'))
        self.assertIn('ring.c:4 does not assign head', self.by(found, 'FAIL')[0])
        found = self.run_on(table('| `struct kg_ring` | head | ① | kg_ring_reset | ring.c:3 | push | +1 |'))
        self.assertIn('ring.c:3 lies in kg_ring_push(), not in kg_ring_reset()', self.by(found, 'FAIL')[0])
        found = self.run_on(table('| `struct kg_ring` | depth | ① | kg_ring_push | ring.c:3 | push | +1 |'))
        self.assertIn('depth is not a member of the struct', self.by(found, 'FAIL')[0])
        found = self.run_on(table('| `struct kg_other` | head | ① | kg_ring_push | ring.c:3 | push | +1 |'))
        self.assertIn('struct kg_other is defined in no file the page cites', self.by(found, 'FAIL')[0])

    def test_no_table_and_missing_inputs(self):
        found = self.run_on('## EVIDENCE\n')
        self.assertEqual(found.footer, 'lifecycle rows=0')
        with self.assertRaises(MissingInput):
            list(rule.check(page(skeleton()), TestInputs(tree=self.root)))
if __name__ == '__main__':
    unittest.main()


class Corroboration(Lifecycle):
    def test_an_assignment_to_another_structs_field_is_not_corroborated(self):
        src = ['struct kg_alpha {', '\tint state;', '};', 'struct kg_beta {', '\tint state;', '};', '',
               'void kg_update_beta(struct kg_beta *b)', '{', '\tb->state = 1;', '}', '',
               'void kg_update_alpha(struct kg_alpha *a)', '{', '\ta->state = 1;', '}']
        open(os.path.join(self.root, 'drivers', 'kg', 'alpha.c'), 'w', encoding='utf-8').write('\n'.join(src) + '\n')
        excerpt = '```c\n/* drivers/kg/alpha.c:1 */\n' + '\n'.join(src) + '\n```'
        fig = '```\n    ┌───┐  ①  ┌───┐\n    │ a │ ──► │ s │\n    └───┘     └───┘\n    ① kg_update_beta alpha.c:10  state is set\n```'
        details = f'### A\n\n{PROSE}\n\n{excerpt}\n\n{PROSE}\n\n{fig}\n\n{PROSE}\n'
        worksheet = table('| `struct kg_alpha` | state | ① | kg_update_beta | alpha.c:10 | update | 1 |')
        found = observed(rule.check(page(skeleton(details=details)), TestInputs(tree=self.root, worksheet=worksheet)))
        self.assertEqual(self.by(found, 'FAIL'), [])
        self.assertTrue(any('does not list this site' in r for r in self.by(found, 'review')), self.by(found, 'review'))
        self.assertIn('verified=0 uncorroborated=1', found.footer)
