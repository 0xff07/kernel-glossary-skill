"""kind: rule — a figure names functions through circled marks resolved by a legend beneath the
drawing; the marks and the legend match, every legend site is reproduced by an excerpt on the
page and lies in the named function."""
import os
import shutil
import tempfile
import unittest
from checks import drawing_legend as rule
from inputs import MissingInput
from tests.support import PROSE, page, skeleton, TestInputs, observed
RING_C = ['int kg_ring_push(struct kg_ring *ring, int v)', '{', '\tring->head++;', '\treturn 0;', '}', '',
          'void kg_ring_reset(struct kg_ring *ring)', '{', '\tring->head = 0;', '\tring->tail = 0;', '}']
EXCERPT = '```c\n/* drivers/kg/ring.c:1 */\n' + '\n'.join(RING_C[:5]) + '\n```'

def figure(*legend):
    body = ['    Two writers of the head', '    ───────────────────────', '    ┌──────┐  ①  ┌──────┐', '    │ push │ ──► │ head │', '    └──────┘  ②  └──────┘']
    return '```\n' + '\n'.join(body + ['    ' + l for l in legend]) + '\n```'

class Legend(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, 'drivers', 'kg'))
        open(os.path.join(self.root, 'drivers', 'kg', 'ring.c'), 'w', encoding='utf-8').write('\n'.join(RING_C) + '\n')
        open(os.path.join(self.root, 'drivers', 'kg', 'ring.h'), 'w', encoding='utf-8').write('\n' * 11 + 'struct kg_ring {\n\tunsigned int head;\n};\n')

    def tearDown(self):
        shutil.rmtree(self.root)

    def run_on(self, fig, excerpt=EXCERPT):
        details = f'### A\n\n{PROSE}\n\n{excerpt}\n\n{PROSE}\n\n{fig}\n\n{PROSE}\n'
        return observed(rule.check(page(skeleton(details=details)), TestInputs(tree=self.root)))

    def fails(self, found):
        return [f.message for f in found.all if f.severity == 'FAIL']

    def test_marks_resolved_by_reproduced_sites_pass(self):
        found = self.run_on(figure('① kg_ring_push ring.c:3   ② kg_ring_push :4'))
        self.assertEqual(self.fails(found), [])
        self.assertEqual(found.footer, 'figures=1 with-legend=1 marks=2 entries=2 findings=0')

    def test_a_mark_without_a_legend_entry_and_an_entry_marking_nothing_fail(self):
        found = self.run_on(figure('① kg_ring_push ring.c:3'))
        self.assertIn('marks ② in the drawing have no legend entry with a site', self.fails(found)[0])
        found = self.run_on(figure('① kg_ring_push ring.c:3  ② kg_ring_push :4  ③ kg_ring_reset :9'))
        self.assertTrue(any('legend entries ③ mark nothing' in f for f in self.fails(found)))

    def test_a_site_outside_the_named_function_or_not_reproduced_fails(self):
        found = self.run_on(figure('① kg_ring_push ring.c:3   ② kg_ring_push :9'))
        self.assertIn('does not lie in kg_ring_push(): kg_ring_reset() holds that line', self.fails(found)[0])
        found = self.run_on(figure('① kg_ring_push ring.c:3   ② kg_ring_reset :9'))
        self.assertIn('is a line no excerpt on the page reproduces', self.fails(found)[0])
        found = self.run_on(figure('① kg_ring_push ring.c:3   ② kg_ring_push other.c:4'))
        self.assertIn('matches no file the page cites', self.fails(found)[0])

    def test_a_figure_without_marks_is_left_alone_and_a_missing_tree_is_reported(self):
        found = self.run_on('```\n    ┌──┐\n    │ a│\n    └──┘\n```')
        self.assertEqual(found.footer, 'figures=1 with-legend=0 marks=0 entries=0 findings=0')
        with self.assertRaises(MissingInput):
            list(rule.check(page(skeleton()), TestInputs(tree=None)))
if __name__ == '__main__':
    unittest.main()
