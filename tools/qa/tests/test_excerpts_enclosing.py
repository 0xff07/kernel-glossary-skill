'kind: rule — a unit that shows lines from inside a construct reproduces the construct\'s opening line\n(the signature, the struct line, the #define, the kerneldoc\'s "/**" and title), or continues a construct\nan earlier unit of the same fence opened; a top-level line needs nothing.'
import os
import shutil
import tempfile
import unittest
from checks import excerpts_enclosing as rule
from inputs import MissingInput
from tests.support import PROSE, page, skeleton, TestInputs, observed
RING_H = ['/**', ' * struct kg_ring - a ring', ' * @head: the head', ' * @tail: the tail', ' */', 'struct kg_ring {',
          '\tunsigned int head;', '\tunsigned int tail;', '};', '', '#define KG_RING_MAX 16', '#define KG_RING_CHECK(r) \\',
          '\t((r)->head >= (r)->tail)', '', 'static inline int kg_ring_full(struct kg_ring *ring)', '{',
          '\treturn ring->head - ring->tail == KG_RING_MAX;', '}', '', 'int kg_ring_push(struct kg_ring *ring, int v);']
RING_C = ['static int kg_ring_push(struct kg_ring *ring,', '\t\t\tint v)', '{', '\tint ret;', '',
          '\tif (ring->head == 3)', '\t\treturn -ENOSPC;', '\tring->head++;', '\treturn 0;', '}', '',
          'static const struct kg_ops kg_ring_ops = {', '\t.push = kg_ring_push,', '};']

def fence(*parts):
    return '```c\n' + '\n'.join(parts) + '\n```'

class Enclosing(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, 'drivers', 'kg'))
        for name, lines in (('ring.h', RING_H), ('ring.c', RING_C)):
            open(os.path.join(self.root, 'drivers', 'kg', name), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')

    def tearDown(self):
        shutil.rmtree(self.root)

    def run_on(self, *fences):
        details = '### A\n\n' + '\n\n'.join(f'{PROSE}\n\n{f}' for f in fences) + f'\n\n{PROSE}\n'
        return observed(rule.check(page(skeleton(details=details)), TestInputs(tree=self.root)))

    def fails(self, found):
        return [f.message for f in found.all if f.severity == 'FAIL']

    def test_the_constructs_of_a_file(self):
        got = [(c.start, c.end, c.kind, c.name) for c in rule.constructs_of(RING_H)]
        self.assertEqual(got, [(1, 5, 'kerneldoc', 'struct kg_ring'), (6, 9, 'struct', 'kg_ring'), (12, 13, 'macro', 'KG_RING_CHECK'),
                               (15, 18, 'function', 'kg_ring_full')])
        got = [(c.start, c.end, c.kind, c.name) for c in rule.constructs_of(RING_C)]
        self.assertEqual(got, [(1, 10, 'function', 'kg_ring_push'), (12, 14, 'initializer', 'kg_ring_ops')])

    def test_a_member_alone_fails_and_the_opened_definition_passes(self):
        found = self.run_on(fence('/* drivers/kg/ring.h:7 */', '\tunsigned int head;'))
        self.assertEqual(len(self.fails(found)), 1)
        self.assertIn('shows lines of struct kg_ring (ring.h:6-9) without its opening line; begin the unit at ring.h:6', self.fails(found)[0])
        found = self.run_on(fence('/* drivers/kg/ring.h:6 */', 'struct kg_ring {', '...', '\tunsigned int tail;', '};'))
        self.assertEqual(self.fails(found), [])
        self.assertEqual(found.footer, 'units=1 openers-shown=1 continued=0 named-above=0 top-level-lines=0 unmapped=0 findings=0')

    def test_a_function_fragment_needs_its_signature_or_a_sentence_naming_it(self):
        found = self.run_on(fence('/* drivers/kg/ring.c:8 */', '\tring->head++;'))
        self.assertIn('shows lines of kg_ring_push() (ring.c:1-10) without its signature, and no sentence above the fence links kg_ring_push()', self.fails(found)[0])
        intro = 'The push advances the head, as [`kg_ring_push()`](https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.c#L1) shows.'
        details = '### A\n\n' + intro + '\n\n' + fence('/* drivers/kg/ring.c:8 */', '\tring->head++;') + f'\n\n{PROSE}\n'
        found = observed(rule.check(page(skeleton(details=details)), TestInputs(tree=self.root)))
        self.assertEqual(self.fails(found), [])
        self.assertIn('named-above=1', found.footer)
        found = self.run_on(fence('/* drivers/kg/ring.c:2 */', '\t\t\tint v)', '{', '\tint ret;'))
        self.assertIn('begin the unit at ring.c:1', self.fails(found)[0])
        found = self.run_on(fence('/* drivers/kg/ring.c:1 */', 'static int kg_ring_push(struct kg_ring *ring,', '\t\t\tint v)', '{', '...', '\tring->head++;', '\treturn 0;', '}'))
        self.assertEqual(self.fails(found), [])

    def test_a_later_unit_continues_the_construct_an_earlier_unit_opened(self):
        opener = ('/* drivers/kg/ring.c:1 */', 'static int kg_ring_push(struct kg_ring *ring,', '\t\t\tint v)', '{')
        found = self.run_on(fence(*opener, '...', '/* drivers/kg/ring.c:8 */', '\tring->head++;'))
        self.assertEqual(self.fails(found), [])
        self.assertIn('continued=1', found.footer)
        found = self.run_on(fence('/* drivers/kg/ring.c:8 */', '\tring->head++;', '...', *opener))
        self.assertEqual(len(self.fails(found)), 1)
        found = self.run_on(fence(*opener), fence('/* drivers/kg/ring.c:8 */', '\tring->head++;'))
        self.assertEqual(len(self.fails(found)), 1)

    def test_a_kerneldoc_fragment_keeps_its_opening_and_title(self):
        found = self.run_on(fence('/* drivers/kg/ring.h:3 */', ' * @head: the head'))
        self.assertIn('the kerneldoc of struct kg_ring (ring.h:1-5) without its "/**" line and the title line beneath it', self.fails(found)[0])
        found = self.run_on(fence('/* drivers/kg/ring.h:1 */', '/**', '...', ' * @tail: the tail', ' */'))
        self.assertEqual(len(self.fails(found)), 1)
        found = self.run_on(fence('/* drivers/kg/ring.h:1 */', '/**', ' * struct kg_ring - a ring', '...', ' * @tail: the tail', ' */'))
        self.assertEqual(self.fails(found), [])

    def test_macros_initializers_and_top_level_lines(self):
        found = self.run_on(fence('/* drivers/kg/ring.h:11 */', '#define KG_RING_MAX 16'), fence('/* drivers/kg/ring.h:20 */', 'int kg_ring_push(struct kg_ring *ring, int v);'))
        self.assertEqual(self.fails(found), [])
        self.assertIn('top-level-lines=2', found.footer)
        found = self.run_on(fence('/* drivers/kg/ring.h:13 */', '\t((r)->head >= (r)->tail)'))
        self.assertIn('the macro KG_RING_CHECK (ring.h:12-13)', self.fails(found)[0])
        found = self.run_on(fence('/* drivers/kg/ring.c:13 */', '\t.push = kg_ring_push,'))
        self.assertIn('the initializer of kg_ring_ops (ring.c:12-14)', self.fails(found)[0])
        found = self.run_on(fence('/* drivers/kg/ring.c:12 */', 'static const struct kg_ops kg_ring_ops = {', '\t.push = kg_ring_push,', '};'))
        self.assertEqual(self.fails(found), [])

    def test_an_unmapped_unit_is_a_review_row_and_a_missing_tree_is_reported(self):
        found = self.run_on(fence('/* drivers/kg/ring.c:8 */', '\tring->tail++;'))
        self.assertEqual(self.fails(found), [])
        self.assertIn('unmapped=1', found.footer)
        with self.assertRaises(MissingInput):
            list(rule.check(page(skeleton()), TestInputs(tree=None)))
if __name__ == '__main__':
    unittest.main()
