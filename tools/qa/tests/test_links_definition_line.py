from span_utils import classify
"""plugins.anchors: every link opened under a temporary tree: a symbol link lands on a line naming
it, a location link on its own line, a file link and a DOCUMENTATION entry on a file the tree
holds."""
import os
import shutil
import tempfile
import unittest
from checks import links_definition_line as anchors
from tests.support import URL, page, skeleton, TestInputs, observed
BASE = 'https://elixir.bootlin.com/linux/v0.1/source/'

class Anchors(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp()
        path = os.path.join(self.root, 'drivers', 'kg', 'ring.h')
        os.makedirs(os.path.dirname(path))
        lines = [f'/* line {n} */' for n in range(1, 12)] + ['struct kg_ring {', '\tunsigned int head;', '};']
        open(path, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
        self.inputs = TestInputs(self.root)

    def tearDown(self):
        shutil.rmtree(self.root)

    def check(self, details, text=None):
        return observed(anchors.check(page(text or skeleton(details=details)), self.inputs))

    def test_symbol_link_on_its_definition_line(self):
        result = self.check(f'### A\n\nThe ring is [`struct kg_ring`]({URL}).\n')
        self.assertEqual(result.data['anchor_misses'], 0)
        self.assertEqual([f for f in result.findings if f.severity == 'FAIL'], [])

    def test_symbol_link_on_a_line_not_naming_it(self):
        result = self.check(f'### A\n\nThe ring is [`struct kg_ring`]({BASE}drivers/kg/ring.h#L2).\n')
        self.assertEqual(result.data['anchor_misses'], 1)
        self.assertIn('does not name it', result.findings[0].message)

    def test_location_link(self):
        clean = self.check(f'### A\n\nThe head is declared at [`drivers/kg/ring.h:13`]({BASE}drivers/kg/ring.h#L13).\n')
        self.assertEqual(clean.data['anchor_misses'], 0)
        wrong = self.check(f'### A\n\nThe head is declared at [`drivers/kg/ring.h:13`]({BASE}drivers/kg/ring.h#L12).\n')
        self.assertEqual(wrong.data['anchor_misses'], 1)
        self.assertIn('location span', wrong.findings[0].message)

    def test_file_link_is_opened(self):
        held = self.check(f'### A\n\nThe header is [`ring.h`]({BASE}drivers/kg/ring.h).\n')
        self.assertEqual(held.data['anchor_misses'], 0)
        missing = self.check(f'### A\n\nThe header is [`nosuch.h`]({BASE}drivers/kg/nosuch.h).\n')
        self.assertEqual(missing.data['anchor_misses'], 1)
        self.assertIn('a path the tree does not hold', missing.findings[0].message)
        directory = self.check(f'### A\n\nThe driver is under [`drivers/kg/`]({BASE}drivers/kg/).\n')
        self.assertEqual(directory.data['anchor_misses'], 0)
        for escape in ('../../etc/passwd', '/etc/passwd', 'drivers/kg/../../../etc/passwd'):
            outside = self.check(f'### A\n\nSee [`passwd`]({BASE}{escape}).\n')
            self.assertEqual(outside.data['anchor_misses'], 1, escape)

    def test_beyond_the_file(self):
        result = self.check(f'### A\n\nThe ring is [`struct kg_ring`]({BASE}drivers/kg/ring.h#L400).\n')
        self.assertIn('beyond the file', result.findings[0].message)

    def test_documentation_entry_names_a_file_the_tree_holds(self):
        text = skeleton().replace('## DOCUMENTATION\n\n', f"## DOCUMENTATION\n\n- [`Documentation/kg/ring.rst`]({BASE}Documentation/kg/ring.rst): the ring's ABI\n\n")
        result = self.check(None, text)
        self.assertEqual(result.data['anchor_misses'], 1)
        self.assertEqual(sum(('Documentation/kg/ring.rst' in f.message for f in result.findings)), 1)
        self.assertEqual(result.data['catalog_misses'], 0)

    def test_catalog_entry_line_names_its_symbol(self):
        result = self.check('### A\n\nThe producer writes at the head.\n')
        self.assertEqual(result.data['catalog_misses'], 0)
        self.assertEqual(result.data['catalog_entries'], 1)

    def test_location_range(self):
        clean = self.check(f'### A\n\nThe ring is declared at [`drivers/kg/ring.h:12-14`]({BASE}drivers/kg/ring.h#L12).\n')
        self.assertEqual(clean.data['anchor_misses'], 0)
        self.assertEqual((clean.data['location_ranges'], clean.data['location_single']), (1, 0))
        inside = self.check(f'### A\n\nThe ring is declared at [`drivers/kg/ring.h:12-14`]({BASE}drivers/kg/ring.h#L13).\n')
        self.assertIn('not its first line', inside.findings[0].message)
        beyond = self.check(f'### A\n\nThe ring is declared at [`drivers/kg/ring.h:12-400`]({BASE}drivers/kg/ring.h#L12).\n')
        self.assertIn('beyond the file', beyond.findings[0].message)
        backwards = self.check(f'### A\n\nThe ring is declared at [`drivers/kg/ring.h:14-12`]({BASE}drivers/kg/ring.h#L14).\n')
        self.assertIn('before its first line', backwards.findings[0].message)

    def test_bare_span_classes(self):
        self.assertIn('error value', classify('-EINVAL'))
        self.assertIn('literal value', classify('0x10'))
        self.assertIn('path string', classify('/sys/bus/thunderbolt'))
        self.assertEqual(classify('tb_switch_alloc'), '')
        self.assertEqual(classify('CONFIG_USB4'), '')
        self.assertEqual(classify('grep -rn tb_switch drivers/'), '')
if __name__ == '__main__':
    unittest.main()


class Dependencies(unittest.TestCase):
    def test_missing_required_input(self):
        from checks.links_definition_line import check
        from inputs import MissingInput
        from tests.support import TestInputs, page, skeleton
        with self.assertRaises(MissingInput):
            list(check(page(skeleton()), TestInputs()))
