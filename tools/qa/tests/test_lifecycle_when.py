"""kind: rule — a cataloged struct with a field two or more functions write is listed as a
lifecycle candidate unless the worksheet records its Lifecycle table."""
import os
import shutil
import tempfile
import unittest
from checks import lifecycle_when as rule
from inputs import MissingInput
from tests.support import page, skeleton, TestInputs, observed, URL
RING_H = '\n' * 11 + 'struct kg_ring {\n\tunsigned int head;\n\tunsigned int tail;\n};\n'
RING_C = ['int kg_ring_push(struct kg_ring *ring, int v)', '{', '\tring->head++;', '\treturn 0;', '}', '',
          'void kg_ring_reset(struct kg_ring *ring)', '{', '\tring->head = 0;', '\tring->tail = 0;', '}']
DEVICE_H = '\n' * 3 + 'struct kg_device {\n\tstruct kg_device *parent;\n};\n'
CORE_C = ['void kg_dev_a(struct kg_device *dev)', '{', '\tdev->parent = NULL;', '}', '',
          'void kg_dev_b(struct kg_device *dev, struct kg_ring *ring)', '{', '\tdev->parent = dev;', '\tring->tail = 5;', '}']
FOREIGN = ("- [`'\\<struct kg_device\\>':'include/linux/kg_device.h'`](" + URL + "): a device\n"
           "- [`'\\<struct kg_device dev\\>':'drivers/kg/ring.h'`](" + URL + "): the ring's device\n")
CORE_FENCE = '```c\n/* include/linux/kg_device.h:4 */\nstruct kg_device {\n```\n\n```c\n/* drivers/base/kg_core.c:1 */\nvoid kg_dev_a(struct kg_device *dev)\n```\n'
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

    def foreign_page(self):
        text = skeleton(details='### The ring keeps two indexes\n\nThe producer writes at the head.\n\n' + CORE_FENCE)
        return page(text.replace('## DOCUMENTATION', FOREIGN + '\n## DOCUMENTATION'))

    def write_foreign(self):
        os.makedirs(os.path.join(self.root, 'include', 'linux'))
        os.makedirs(os.path.join(self.root, 'drivers', 'base'))
        open(os.path.join(self.root, 'include', 'linux', 'kg_device.h'), 'w', encoding='utf-8').write(DEVICE_H)
        open(os.path.join(self.root, 'drivers', 'base', 'kg_core.c'), 'w', encoding='utf-8').write('\n'.join(CORE_C) + '\n')

    def test_without_an_entry_the_cited_directories_are_read(self):
        self.write_foreign()
        found = observed(rule.check(self.foreign_page(), TestInputs(tree=self.root)))
        reviews = [f.message for f in found.all if f.severity == 'review']
        self.assertEqual(found.footer, 'objects=2 qualifying=2 recorded=0 excluded-files=0')
        self.assertTrue(any('struct kg_device has fields written by several functions, parent (2: kg_dev_a, kg_dev_b)' in r for r in reviews))
        self.assertTrue(any('tail (2: kg_dev_b, kg_ring_reset)' in r for r in reviews))

    def test_the_subsystem_entry_bounds_the_objects_and_the_census(self):
        self.write_foreign()
        entry = {'name': 'KG', 'dir': 'kg', 'kernel_paths': ['drivers/kg/']}
        found = observed(rule.check(self.foreign_page(), TestInputs(tree=self.root, subsystem=entry)))
        reviews = [f.message for f in found.all if f.severity == 'review']
        self.assertEqual(found.footer, 'objects=1 qualifying=1 recorded=0 excluded-files=0')
        self.assertEqual(len(reviews), 1)
        self.assertIn('head (2: kg_ring_push, kg_ring_reset)', reviews[0])
        self.assertNotIn('tail', reviews[0])
        notes = [f.message for f in found.all if f.severity == 'note']
        self.assertTrue(any('struct kg_device: defined outside the subsystem sources, not a candidate' in n for n in notes))
        self.assertFalse(any('kg_device dev' in n for n in notes))

    def test_a_missing_tree_is_reported(self):
        with self.assertRaises(MissingInput):
            list(rule.check(page(skeleton()), TestInputs(tree=None)))
if __name__ == '__main__':
    unittest.main()
