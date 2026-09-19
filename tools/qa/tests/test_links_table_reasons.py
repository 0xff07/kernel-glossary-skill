from checks.links_table_reasons import check
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

class Reasons(unittest.TestCase):

    def test_blank_reason_on_a_prose_row(self):
        details = f'### A\n\nThe ring is [`struct kg_ring`]({URL}).\n'
        blank = observed(check(page(skeleton(details=details)), FakeInputs(rows_of(('struct kg_ring', 'prose', '')))))
        self.assertEqual([f.severity for f in blank.findings], ['FAIL'])
        self.assertIn('empty kind / reason cell', blank.findings[0].message)
        filled = observed(check(page(skeleton(details=details)), FakeInputs(rows_of(('struct kg_ring', 'prose', 'symbol')))))
        self.assertEqual(filled.findings, [])

    def test_a_catalog_entry_needs_no_reason(self):
        entry = "'\\<struct kg_ring\\>':'drivers/kg/ring.h'"
        result = observed(check(page(skeleton()), FakeInputs(rows_of((entry, 'catalog', '')))))
        self.assertEqual(result.data['links_blank_reasons'], 0)
if __name__ == '__main__':
    unittest.main()


class Dependencies(unittest.TestCase):
    def test_missing_required_input(self):
        from checks.links_table_reasons import check
        from inputs import MissingInput
        from tests.support import TestInputs, page, skeleton
        with self.assertRaises(MissingInput):
            list(check(page(skeleton()), TestInputs()))
