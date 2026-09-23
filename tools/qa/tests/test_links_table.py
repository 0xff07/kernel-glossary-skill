"""plugins.links_table: the worksheet's LINKS rows read back, the closure of their kind / reason
cells, and the table `kg table` writes into the worksheet, or prints without one."""
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
        self.assertIn('the table is printed, not written', err.getvalue())
        self.assertIn('carried 1 kind / reason cells', out.getvalue())
        self.assertIn('added row(s) to fill:', out.getvalue())
        self.assertIn('`head`', out.getvalue())

    def test_the_table_is_written_into_the_worksheet_on_disk(self):
        details = f'### A\n\nThe ring is [`struct kg_ring`]({URL}) and the count is `head`.\n'
        worksheet = os.path.join(self.root, 'ring.worksheet.md')
        template = ['# Worksheet', '', '## LINKS', 'WRITTEN by `kg table`, one row per span:', '',
                    '| span | region | linked | bare | bare at | anchor URL | disk line | kind / reason |', '',
                    "The first seven columns are the script's.", '', '## COMPLETENESS', 'nothing yet']
        open(worksheet, 'w', encoding='utf-8').write('\n'.join(template) + '\n')
        inputs = FakeInputs([], tree=self.root)
        inputs.worksheet, inputs.worksheet_lines = worksheet, template
        out, err = (io.StringIO(), io.StringIO())
        self.assertEqual(links_table.emit_table(page(skeleton(details=details)), inputs, out=out, err=err), 0)
        written = open(worksheet, encoding='utf-8').read().split('\n')
        self.assertIn(f'LINKS table written to {worksheet}:', out.getvalue())
        self.assertIn('added row(s) to fill', out.getvalue())
        self.assertIn('`head`', out.getvalue())
        self.assertEqual(written[:5], template[:5])
        self.assertEqual(written[5], links_table.HEADER)
        self.assertEqual(written[6], links_table.SEPARATOR)
        rows = [k for k in range(7, len(written)) if written[k].startswith('|')]
        after = rows[-1] + 1
        self.assertTrue(any(written[k].startswith('| `head` | prose | 0 | 1 |') for k in rows), written[7:after])
        self.assertTrue(any(written[k].startswith('| `struct kg_ring` | prose | 1 | 0 |') for k in rows), written[7:after])
        self.assertEqual(written[after:after + 5], template[6:11])
        # a second write keeps the cell a person filled in, and replaces the whole table
        head = next(k for k in rows if written[k].startswith('| `head`'))
        written[head] = written[head].rsplit('|', 2)[0] + '| a settled bare span |'
        open(worksheet, 'w', encoding='utf-8').write('\n'.join(written) + '\n')
        inputs.worksheet_lines = written
        self.assertEqual(links_table.emit_table(page(skeleton(details=details)), inputs, out=io.StringIO(), err=err), 0)
        again = open(worksheet, encoding='utf-8').read().split('\n')
        self.assertTrue(again[head].endswith('| a settled bare span |'), again[head])
        self.assertEqual(len(again), len(written))

    def test_a_section_without_a_table_and_a_worksheet_without_the_section(self):
        table = [links_table.HEADER, links_table.SEPARATOR, '| `x` | prose | 1 | 0 |  |  |  | symbol |']
        self.assertEqual(links_table.with_table(['## LINKS', 'text', '', '## COMPLETENESS'], table),
                         ['## LINKS', 'text', ''] + table + ['', '## COMPLETENESS'])
        self.assertEqual(links_table.with_table(['# Worksheet', ''], table), ['# Worksheet', '', '', '## LINKS', ''] + table)
if __name__ == '__main__':
    unittest.main()


class Kinds(unittest.TestCase):

    def test_a_range_span_is_a_location(self):
        base = 'https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.h'
        p = page(skeleton(details=f'### A\n\nThe ring is declared at [`drivers/kg/ring.h:12-14`]({base}#L12) and its file is [`ring.h`]({base}).\n'))
        self.assertEqual(links_table.linked_kind('drivers/kg/ring.h:12-14', p.spans['drivers/kg/ring.h:12-14']), 'location')
        self.assertEqual(links_table.linked_kind('ring.h', p.spans['ring.h']), 'file')
