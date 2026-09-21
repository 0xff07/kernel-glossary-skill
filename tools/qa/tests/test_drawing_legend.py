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
          'void kg_ring_reset(struct kg_ring *ring)', '{', '\tring->head = 0;', '\tring->tail = 0;', '}', '',
          'void kg_ring_drain(struct kg_ring *ring)', '{', '\tkg_ring_reset(ring);', '}']
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
        found = self.run_on(figure('① kg_ring_push ring.c:3  advances the head', '② kg_ring_push :4  returns success to the caller'))
        self.assertEqual(self.fails(found), [])
        self.assertEqual(found.footer, 'figures=1 with-legend=1 marks=2 entries=2 phrased=2 findings=0 unresolved=0')
        found = self.run_on(figure('① kg_ring_push ring.c:3   ② kg_ring_push :4'))
        self.assertTrue(all('carries no phrase' in f for f in self.fails(found)))
        self.assertEqual(len(self.fails(found)), 2)

    def test_a_mark_without_a_legend_entry_and_an_entry_marking_nothing_fail(self):
        found = self.run_on(figure('① kg_ring_push ring.c:3  advances the head'))
        self.assertIn('marks ② in the drawing have no legend entry with a site', self.fails(found)[0])
        found = self.run_on(figure('① kg_ring_push ring.c:3  advances the head', '② kg_ring_push :4  returns success to the caller', '③ kg_ring_reset :9  clears the head'))
        self.assertTrue(any('legend entries ③ mark nothing' in f for f in self.fails(found)))

    def test_a_site_outside_the_named_function_or_not_reproduced_fails(self):
        found = self.run_on(figure('① kg_ring_push ring.c:3  advances the head', '② kg_ring_push :9  clears the head'))
        self.assertIn('does not lie in kg_ring_push(): kg_ring_reset() holds that line', self.fails(found)[0])
        found = self.run_on(figure('① kg_ring_push ring.c:3  advances the head', '② kg_ring_reset :9  clears the head'))
        self.assertIn('is a line no excerpt on the page reproduces', self.fails(found)[0])
        found = self.run_on(figure('① kg_ring_push ring.c:3  advances the head', '② kg_ring_push other.c:4  returns success to the caller'))
        self.assertIn('matches no file the page cites', self.fails(found)[0])

    def test_a_figure_without_marks_is_left_alone_and_a_missing_tree_is_reported(self):
        found = self.run_on('```\n    ┌──┐\n    │ a│\n    └──┘\n```')
        self.assertEqual(found.footer, 'figures=1 with-legend=0 marks=0 entries=0 phrased=0 findings=0 unresolved=0')
        with self.assertRaises(MissingInput):
            list(rule.check(page(skeleton()), TestInputs(tree=None)))
if __name__ == '__main__':
    unittest.main()


class Containment(Legend):
    def test_a_call_site_is_not_the_named_function(self):
        text = skeleton(details=f'### A\n\n{PROSE}\n\n{EXCERPT}\n\n' + figure('① kg_ring_push ring.c:3  head advances', '② kg_ring_reset ring.c:15  reset is called') + f'\n\n{PROSE}\n')
        found = observed(rule.check(page(text), TestInputs(tree=self.root)))
        fails = [f.message for f in found.findings if f.severity == 'FAIL']
        self.assertTrue(any('does not lie in kg_ring_reset(): kg_ring_drain' in m for m in fails), fails)

    def test_a_line_outside_any_construct_is_unresolved(self):
        text = skeleton(details=f'### A\n\n{PROSE}\n\n{EXCERPT}\n\n' + figure('① kg_ring_push ring.c:3  head advances', '② kg_ring_reset ring.c:6  between the functions') + f'\n\n{PROSE}\n')
        found = observed(rule.check(page(text), TestInputs(tree=self.root)))
        self.assertTrue(any('unresolved' in f.message and f.severity == 'review' for f in found.findings))
        self.assertIn('unresolved=1', found.footer)
