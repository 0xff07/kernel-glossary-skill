"""kind: rule — a cataloged struct with a field two or more functions write is listed as a
lifecycle candidate unless the worksheet records its Lifecycle table."""
import os
import shutil
import tempfile
import unittest
from checks import lifecycle_when as rule
from inputs import MissingInput
from tests.support import page, skeleton, TestInputs, observed
RING_H = '\n' * 11 + 'struct kg_ring {\n\tunsigned int head;\n\tunsigned int tail;\n};\n'
RING_C = ['int kg_ring_push(struct kg_ring *ring, int v)', '{', '\tring->head++;', '\treturn 0;', '}', '',
          'void kg_ring_reset(struct kg_ring *ring)', '{', '\tring->head = 0;', '\tring->tail = 0;', '}']
TABLE = '## EVIDENCE\n### Lifecycle\n| object | field | mark | writer | site | event | value |\n|---|---|---|---|---|---|---|\n| `struct kg_ring` | head | ① | kg_ring_push | ring.c:3 | push | +1 |\n'

class When(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, 'drivers', 'kg'))
        open(os.path.join(self.root, 'drivers', 'kg', 'ring.h'), 'w', encoding='utf-8').write(RING_H)
        open(os.path.join(self.root, 'drivers', 'kg', 'ring.c'), 'w', encoding='utf-8').write('\n'.join(RING_C) + '\n')
        open(os.path.join(self.root, 'drivers', 'kg', 'ring_test.c'), 'w', encoding='utf-8').write('void t(struct kg_ring *ring)\n{\n\tring->tail = 1;\n}\n')

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_a_field_with_two_writers_is_a_candidate_until_recorded(self):
        found = observed(rule.check(page(skeleton()), TestInputs(tree=self.root)))
        reviews = [f.message for f in found.all if f.severity == 'review']
        self.assertEqual(len(reviews), 1)
        self.assertIn('struct kg_ring has fields written by several functions, head (2: kg_ring_push, kg_ring_reset)', reviews[0])
        self.assertNotIn('tail', reviews[0])
        self.assertEqual(found.footer, 'objects=1 qualifying=1 recorded=0 excluded-files=0')
        found = observed(rule.check(page(skeleton()), TestInputs(tree=self.root, worksheet='## EVIDENCE\n### Lifecycle\nexcluded: ring.c (out of scope)\n')))
        self.assertEqual(found.footer, 'objects=1 qualifying=0 recorded=0 excluded-files=1')
        found = observed(rule.check(page(skeleton()), TestInputs(tree=self.root, worksheet=TABLE)))
        self.assertEqual([f for f in found.all if f.severity == 'review'], [])
        self.assertEqual(found.footer, 'objects=1 qualifying=1 recorded=1 excluded-files=0')

    def test_a_missing_tree_is_reported(self):
        with self.assertRaises(MissingInput):
            list(rule.check(page(skeleton()), TestInputs(tree=None)))
if __name__ == '__main__':
    unittest.main()
