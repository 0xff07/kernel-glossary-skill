"""plugins.links_table: the worksheet's LINKS rows read back, the closure of their kind / reason
cells, and the table `kg table` emits."""
import io
import os
import shutil
import tempfile
import unittest
from inputs import Inputs
import links_table
from tests.support import URL, page, skeleton, TestInputs, observed
ROW = '| `{span}` | {region} | 1 | 0 |  | {url} | struct kg_ring {{ | {reason} |'

class FakeInputs(TestInputs):
    worksheet_section = Inputs.worksheet_section

    def __init__(self, rows, tree=None):
        super().__init__()
        self.worksheet_lines = ['## LINKS', links_table.HEADER, links_table.SEPARATOR] + rows + ['', '## COMPLETENESS']
        self.worksheet = '<worksheet>'
        self.tree, self.cache = (tree, {})

def rows_of(*rows):
    return [ROW.format(span=s, region=r, url=URL, reason=reason) for s, r, reason in rows]

class Emit(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp()
        path = os.path.join(self.root, 'drivers', 'kg', 'ring.h')
        os.makedirs(os.path.dirname(path))
        open(path, 'w', encoding='utf-8').write('\n' * 11 + 'struct kg_ring {\n};\n')

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_no_tree_no_table(self):
        err = io.StringIO()
        inputs = FakeInputs([])
        inputs.worksheet_lines = None
        self.assertEqual(links_table.emit_table(page(skeleton()), inputs, out=io.StringIO(), err=err), 2)
        self.assertIn('no kernel tree', err.getvalue())

    def test_table_carries_the_reason_already_recorded(self):
        details = f'### A\n\nThe ring is [`struct kg_ring`]({URL}) and the count is `head`.\n'
        inputs = FakeInputs(rows_of(('struct kg_ring', 'prose', 'symbol, confirmed')), tree=self.root)
        out, err = (io.StringIO(), io.StringIO())
        self.assertEqual(links_table.emit_table(page(skeleton(details=details)), inputs, out=out, err=err), 0)
        lines = out.getvalue().split('\n')
        self.assertEqual(lines[0], links_table.HEADER)
        ring = next((l for l in lines if l.startswith('| `struct kg_ring`')))
        self.assertTrue(ring.endswith('| struct kg_ring { | symbol, confirmed |'), ring)
        self.assertTrue(any((l.startswith('| `head` | prose | 0 | 1 |') for l in lines)))
        self.assertIn('carried 1 kind / reason cells', err.getvalue())
        self.assertIn('added row(s) to fill:', err.getvalue())
        self.assertIn('`head`', err.getvalue())
if __name__ == '__main__':
    unittest.main()


class Kinds(unittest.TestCase):

    def test_a_range_span_is_a_location(self):
        base = 'https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.h'
        p = page(skeleton(details=f'### A\n\nThe ring is declared at [`drivers/kg/ring.h:12-14`]({base}#L12) and its file is [`ring.h`]({base}).\n'))
        self.assertEqual(links_table.linked_kind('drivers/kg/ring.h:12-14', p.spans['drivers/kg/ring.h:12-14']), 'location')
        self.assertEqual(links_table.linked_kind('ring.h', p.spans['ring.h']), 'file')
