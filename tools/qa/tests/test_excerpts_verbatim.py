"""plugins.excerpts: the byte-compare of one unit against its source, resynchronising only after
a declared elision and never onto a line the file holds twice."""
import unittest
from checks import excerpts_verbatim as excerpts
from tests.support import EXCERPT, PROSE, page, skeleton, TestInputs, observed
SOURCE = ['int a;', 'int b;', 'int c;', 'int d;', 'int e;', 'int f;']
DUPLICATED = ['int a;', 'int b;', 'int c;', 'int x;', 'int d;', 'int x;']

def unit_of(cited, *body):
    fence = '```c\n/* drivers/kg/ring.c:%d */\n%s\n```' % (cited, '\n'.join(body))
    return page(skeleton(details=f'### A\n\n{PROSE}\n\n{fence}\n\n{PROSE}\n')).units[0]

def compare(unit, source):
    findings, counts = ([], {'elisions': 0, 'resyncs': 0, 'bad': 0})
    excerpts.compare_unit(unit, source, findings, counts)
    return (findings, counts)

class CompareUnit(unittest.TestCase):

    def test_verbatim_at_the_cited_line(self):
        findings, counts = compare(unit_of(2, 'int b;', 'int c;'), SOURCE)
        self.assertEqual(findings, [])
        self.assertEqual(counts['bad'], 0)

    def test_content_elsewhere_than_the_cited_line(self):
        findings, counts = compare(unit_of(3, 'int b;', 'int c;'), SOURCE)
        self.assertEqual(counts['bad'], 1)
        self.assertIn('does not begin at the cited line', findings[0].message)

    def test_mismatch_without_an_elision(self):
        findings, counts = compare(unit_of(2, 'int b;', 'int zzz;'), SOURCE)
        self.assertEqual(counts['bad'], 1)
        self.assertIn('mismatch at source line 3', findings[0].message)

    def test_declared_elision_resynchronises(self):
        findings, counts = compare(unit_of(2, 'int b;', '...', 'int e;', 'int f;'), SOURCE)
        self.assertEqual(findings, [])
        self.assertEqual((counts['elisions'], counts['resyncs'], counts['bad']), (1, 1, 0))

    def test_resync_onto_a_duplicated_line_is_refused(self):
        findings, counts = compare(unit_of(2, 'int b;', '...', 'int x;'), DUPLICATED)
        self.assertEqual(counts['bad'], 1)
        self.assertIn('occurs 2 times', findings[0].message)

    def test_an_elision_may_end_on_the_closing_brace(self):
        source = ['struct a {', '\tint x;', '};', 'struct b {', '\tint y;', '};']
        findings, counts = compare(unit_of(1, 'struct a {', '...', '};'), source)
        self.assertEqual(findings, [])
        self.assertEqual((counts['resyncs'], counts['bad']), (1, 0))
        findings, counts = compare(unit_of(1, 'struct a {', '...', '\tint y;'), source)
        self.assertEqual(counts['bad'], 0)
        self.assertEqual(compare(unit_of(4, 'struct b {', '...', '};'), source)[1]['bad'], 0)

    def test_tabs_are_compared_byte_for_byte(self):
        source = ['\tint a;', '        int b;']
        self.assertEqual(compare(unit_of(1, '\tint a;'), source)[1]['bad'], 0)
        self.assertEqual(compare(unit_of(1, '        int a;'), source)[1]['bad'], 1)

class AgainstATree(unittest.TestCase):
    RING_C = ['/**', ' * kg_ring_push - push one value', ' */', 'int kg_ring_push(struct kg_ring *ring, int v)', '{', '\tring->head++;', '\treturn 0;', '}', '', 'struct kg_ring;', 'int b;', 'int c;']

    def setUp(self):
        import os, tempfile
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, 'drivers', 'kg'))
        open(os.path.join(self.root, 'drivers', 'kg', 'ring.c'), 'w', encoding='utf-8').write('\n'.join(self.RING_C) + '\n')
        open(os.path.join(self.root, 'drivers', 'kg', 'ring.h'), 'w', encoding='utf-8').write('\n' * 11 + 'struct kg_ring {\n\tunsigned int head;\n};\n')

    def tearDown(self):
        import shutil
        shutil.rmtree(self.root)

    def verbatim(self, fence):
        from tests.support import TestInputs, observed
        return observed(excerpts.check(page(skeleton(details=f'### A\n\n{PROSE}\n\n{fence}\n\n{PROSE}\n')), TestInputs(self.root)))

    def test_run_verbatim(self):
        clean = self.verbatim('```c\n/* drivers/kg/ring.c:11 */\nint b;\nint c;\n```')
        self.assertEqual(clean.findings, [])
        self.assertEqual((clean.data['units'], clean.data['bad']), (1, 0))
        missing = self.verbatim('```c\n/* drivers/kg/nosuch.c:1 */\nint b;\n```')
        self.assertIn('cannot be opened under the tree', missing.findings[0].message)
        zero = self.verbatim('```c\n/* drivers/kg/ring.c:0 */\nint b;\n```')
        self.assertIn('cites no line of the file', zero.findings[0].message)
        self.assertEqual(zero.data['bad'], 1)
if __name__ == '__main__':
    unittest.main()


class Dependencies(unittest.TestCase):
    def test_missing_required_input(self):
        from checks.excerpts_verbatim import check
        from inputs import MissingInput
        from tests.support import TestInputs, page, skeleton
        with self.assertRaises(MissingInput):
            list(check(page(skeleton()), TestInputs()))
