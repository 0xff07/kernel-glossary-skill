"""plugins.excerpts: the byte-compare of one unit against its source, resynchronising only after
a declared elision and never onto a line the file holds twice."""
import unittest
from checks import excerpts_introduced as excerpts
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

class Definitions(unittest.TestCase):

    def test_defined_name(self):
        self.assertEqual(excerpts.defined_name('struct kg_ring {'), 'kg_ring')
        self.assertEqual(excerpts.defined_name('#define KG_SLOTS 16'), 'KG_SLOTS')
        self.assertEqual(excerpts.defined_name('static int kg_ring_push(struct kg_ring *ring, int v)'), 'kg_ring_push')
        self.assertIsNone(excerpts.defined_name('\treturn 0;'))

    def test_shown_names_a_tagless_enum_by_its_first_enumerator(self):
        self.assertEqual(excerpts.shown(['enum {', '\tKG_INIT,', '\tKG_READY,', '};']), ('KG_INIT', 'definition', 1))
        self.assertEqual(excerpts.shown(['enum {', '\tKG_INIT = 1,', '};']), ('KG_INIT', 'definition', 1))
        self.assertEqual(excerpts.shown(['enum {', '\t/* the first step */', '\tKG_INIT,', '};']), ('KG_INIT', 'definition', 2))
        self.assertEqual(excerpts.shown(['enum kg_state {', '\tKG_INIT,', '};']), ('kg_state', 'definition', 0))
        self.assertEqual(excerpts.shown(['enum {', '};']), (None, 'body', 0))

    def test_shown_passes_over_a_leading_include(self):
        self.assertEqual(excerpts.shown(['#include "kg.h"', '', '#define KG_SLOTS 16']), ('KG_SLOTS', 'definition', 2))
        self.assertEqual(excerpts.shown(['#include <linux/errno.h>']), (None, 'body', 0))
        self.assertEqual(excerpts.shown(['#if IS_ENABLED(CONFIG_KG)', '', '#define KG_MAX 6']), ('KG_MAX', 'definition', 2))
        self.assertEqual(excerpts.shown(['#ifdef CONFIG_KG', '#define KG_MAX 6']), ('KG_MAX', 'definition', 1))
        self.assertEqual(excerpts.shown(['#define KG_MAX 6']), ('KG_MAX', 'definition', 0))

    def test_shown_names_a_prototype_unit_by_its_first_declaration(self):
        self.assertEqual(excerpts.shown(['int kg_push(struct kg_ring *r, int v);']), ('kg_push', 'definition', 0))
        self.assertEqual(excerpts.shown(['\tint ret;']), (None, 'body', 0))
        self.assertEqual(excerpts.shown(['int (*fn)(void);']), (None, 'body', 0))
        self.assertEqual(excerpts.shown(['\tring->head++;']), (None, 'body', 0))

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

    def test_enclosing_and_hint_target(self):
        cache = {}
        self.assertEqual(excerpts.enclosing(self.root, 'drivers/kg/ring.c', 6, cache), ('kg_ring_push', 4))
        self.assertEqual(excerpts.enclosing(self.root, 'drivers/kg/ring.c', 2, cache), ('kg_ring_push', 4))
        self.assertEqual(excerpts.hint_target(self.root, 'drivers/kg/ring.c', 10, cache), ('drivers/kg/ring.h', 12))
        self.assertEqual(excerpts.hint_target(self.root, 'drivers/kg/ring.c', 4, cache), ('drivers/kg/ring.c', 4))

class Introductions(unittest.TestCase):
    BODY = ['struct kg_ring {', '\tunsigned int head;', '};']

    def state(self, intro):
        from tests.support import URL, TestInputs, observed
        return excerpts.introduction_state(intro.replace('URL', URL), 'kg_ring', 'drivers/kg/ring.h', 12, self.BODY)[0]

    def test_states(self):
        self.assertEqual(self.state('The ring is [`struct kg_ring`](URL).'), 'linked')
        self.assertEqual(self.state('The ring is `kg_ring`.'), 'BARE mention')
        self.assertEqual(self.state('See [`drivers/kg/ring.h:12`](URL).'), 'LOCATION LINK ONLY')
        self.assertEqual(self.state('See [`drivers/kg/ring.h:12-14`](URL).'), 'LOCATION LINK ONLY')
        self.assertEqual(self.state('Nothing names it.'), 'ABSENT')

    def test_rows_and_findings_over_a_page(self):
        from tests.support import URL, TestInputs, observed
        linked = page(skeleton(details=f'### A\n\nThe ring is [`struct kg_ring`]({URL}).\n\n{EXCERPT}\n\n{PROSE}\n'))
        rows, states, details = excerpts.introduction_rows(linked, None)
        self.assertEqual((len(rows), states, len(details)), (1, ['linked'], 1))
        self.assertEqual(observed(excerpts.check(linked, TestInputs(tree='/unused'))).findings, [])
        absent = page(skeleton(details=f'### A\n\n{PROSE}\n\n{EXCERPT}\n\n{PROSE}\n'))
        found = observed(excerpts.check(absent, TestInputs(tree='/unused'))).findings
        self.assertEqual(len(found), 1)
        self.assertIn('ABSENT in the prose above the fence', found[0].message)

    def test_the_function_regex_does_not_backtrack(self):
        import time
        from pagemodel import CONSTRUCT_FUNCTION
        start = time.perf_counter()
        self.assertIsNone(CONSTRUCT_FUNCTION.match('static ' * 40 + 'x'))
        self.assertIsNone(excerpts.ENCLOSING_FUNCTION.match('static ' * 40 + 'x'))
        self.assertLess(time.perf_counter() - start, 0.05)
        self.assertEqual(CONSTRUCT_FUNCTION.match('static struct tb_switch *tb_switch_alloc(struct tb *tb,').group(1), 'tb_switch_alloc')
if __name__ == '__main__':
    unittest.main()


class Dependencies(unittest.TestCase):
    def test_missing_required_input(self):
        from checks.excerpts_introduced import check
        from inputs import MissingInput
        from tests.support import TestInputs, page, skeleton
        with self.assertRaises(MissingInput):
            list(check(page(skeleton(details=EXCERPT)), TestInputs()))

    def test_page_only_introduction_survives_missing_or_invalid_source(self):
        import kg
        from unittest.mock import patch
        from tests.test_runner import binding
        text = page(skeleton(details=f'### A\n\n{PROSE}\n\n{EXCERPT}'))
        for inputs in (TestInputs(), TestInputs(tree='/wrong/tree', source_problems=['wrong version'])):
            with patch.object(excerpts, 'source_lines', side_effect=AssertionError('unvalidated read')):
                result, = kg.run_rules(text, inputs, [binding(excerpts.check, excerpts.RULE)])
            self.assertIsNotNone(result.skipped)
            self.assertTrue(any(f.severity == 'review' and 'ABSENT in the prose' in f.message
                                for f in result.findings))

    def test_body_slice_without_source_does_not_guess_the_construct(self):
        import kg
        from tests.test_runner import binding
        excerpt = '```c\n/* drivers/kg/ring.c:6 */\n\tring->head++;\n```'
        result, = kg.run_rules(page(skeleton(details=excerpt)), TestInputs(),
                              [binding(excerpts.check, excerpts.RULE)])
        self.assertIsNotNone(result.skipped)
        self.assertFalse(any(f.severity == 'review' for f in result.findings))
