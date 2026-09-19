"""kind: rule — the writes a lifecycle figure numbers are shown in DETAILS in the order of their marks."""
import os
import shutil
import tempfile
import unittest
from checks import lifecycle_order as rule
from inputs import MissingInput
from tests.support import PROSE, page, skeleton, TestInputs, observed
RING_C = ['int kg_ring_push(struct kg_ring *ring, int v)', '{', '\tring->head++;', '\treturn 0;', '}', '',
          'void kg_ring_reset(struct kg_ring *ring)', '{', '\tring->head = 0;', '\tring->tail = 0;', '}']
TABLE = ('## EVIDENCE\n### Lifecycle\n| object | field | mark | writer | site | event | value |\n|---|---|---|---|---|---|---|\n'
         '| `struct kg_ring` | head | ① | kg_ring_push | ring.c:3 | push | +1 |\n| `struct kg_ring` | head | ② | kg_ring_reset | ring.c:9 | reset | 0 |\n')

def fence(cited, *lines):
    return f'```c\n/* drivers/kg/ring.c:{cited} */\n' + '\n'.join(lines) + '\n```'

class Order(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, 'drivers', 'kg'))
        open(os.path.join(self.root, 'drivers', 'kg', 'ring.c'), 'w', encoding='utf-8').write('\n'.join(RING_C) + '\n')

    def tearDown(self):
        shutil.rmtree(self.root)

    def run_on(self, *fences):
        details = '### A\n\n' + '\n\n'.join(f'{PROSE}\n\n{f}' for f in fences) + f'\n\n{PROSE}\n'
        return observed(rule.check(page(skeleton(details=details)), TestInputs(tree=self.root, worksheet=TABLE)))

    def test_marks_shown_in_order_pass_and_an_inversion_is_reviewed(self):
        found = self.run_on(fence(1, *RING_C[:5]), fence(7, *RING_C[6:11]))
        self.assertEqual(found.findings, [])
        self.assertEqual(found.footer, 'marks=2 shown=2 inversions=0')
        found = self.run_on(fence(7, *RING_C[6:11]), fence(1, *RING_C[:5]))
        self.assertEqual(len(found.findings), 1)
        self.assertIn('the walk shows ② kg_ring_reset() at page', found.findings[0].message)
        self.assertIn('before ① kg_ring_push()', found.findings[0].message)

    def test_missing_inputs_are_reported(self):
        with self.assertRaises(MissingInput):
            list(rule.check(page(skeleton()), TestInputs(tree=self.root)))
if __name__ == '__main__':
    unittest.main()
