from checks.links_table_machine_emitted import check
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
        self.worksheet_lines = ['## LINKS', links_table.HEADER, links_table.SEPARATOR] + rows + ['', '## PARITY']
        self.worksheet = '<worksheet>'
        self.tree, self.cache = (tree, {})

def rows_of(*rows):
    return [ROW.format(span=s, region=r, url=URL, reason=reason) for s, r, reason in rows]

class ReadBack(unittest.TestCase):

    def test_rows_and_refusals(self):
        rows = rows_of(('struct kg_ring', 'prose', 'symbol')) + ['| `short` | prose | 1 | 0 | | | |']
        found, refused = links_table.links_rows(FakeInputs(rows))
        self.assertEqual(list(found), ['struct kg_ring'])
        self.assertEqual(refused, ['short'])

    def test_emitted_diff(self):
        details = f'### A\n\nThe ring is [`struct kg_ring`]({URL}) and the count is `head`.\n'
        stale = observed(check(page(skeleton(details=details)), FakeInputs(rows_of(('gone', 'prose', 'symbol')))))
        messages = ' '.join((f.message for f in stale.findings))
        self.assertIn('`head` has no LINKS row', messages)
        self.assertIn('`gone` has no span on the page', messages)
if __name__ == '__main__':
    unittest.main()


class Dependencies(unittest.TestCase):
    def test_missing_required_input(self):
        from checks.links_table_machine_emitted import check
        from inputs import MissingInput
        from tests.support import TestInputs, page, skeleton
        with self.assertRaises(MissingInput):
            list(check(page(skeleton()), TestInputs()))
