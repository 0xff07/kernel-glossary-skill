"""plugins.worksheet: the identity verdicts, the scope-closure and catalog tables of PARITY, the
acceptance lines and the evidence digest, and the LINT record that evidences LINTED."""
import unittest
from inputs import Inputs
from checks import parity_closed as worksheet
from tests.support import page, skeleton, TestInputs, observed
DIGEST = 'a' * 64
OTHER = 'b' * 64
ACCEPTANCE = '- scoped behaviors covered: done\n- claims supported nearby: done\n- guards preserved: done\n- invariants searched: done\n- activation delta: not applicable, nothing switches on\n- modes told apart: not applicable\n- constructs and limits covered: done\n'

class FakeInputs(TestInputs):
    worksheet_section = Inputs.worksheet_section

    def __init__(self, text, how='convention', rejected=(), digest=DIGEST):
        super().__init__()
        self.worksheet_lines = text.split('\n') if text is not None else None
        self.worksheet = '<worksheet>' if text is not None else None
        self.worksheet_how = how
        self.worksheet_rejected = list(rejected)
        self.page_digest = digest

def check(name, text, **fields):
    return observed(worksheet.check(page(skeleton()), FakeInputs(text, **fields)))

class Parity(unittest.TestCase):
    SCOPE = '| anchors | location on the page |\n|---|---|\n| `kg_ring` | DETAILS, the first subsection |\n\n'
    ROWS = '| symbol | DEFINITION | USAGE |\n|---|---|---|\n| `struct kg_ring` | C@66 | C@80 |\n'

    def test_catalog_rows_closed(self):
        self.assertEqual(check('parity', '## PARITY\n' + self.SCOPE + self.ROWS).findings, [])

    def test_empty_cell_and_missing_row(self):
        empty = check('parity', '## PARITY\n' + self.SCOPE + self.ROWS.replace('C@80', ''))
        self.assertEqual([f.severity for f in empty.findings], ['FAIL'])
        missing = check('parity', '## PARITY\n' + self.SCOPE + '| symbol | DEFINITION | USAGE |\n|---|---|---|\n| `other` | C@1 | C@2 |\n')
        self.assertTrue(any(('no PARITY row naming them' in f.message for f in missing.findings)))

    def test_no_parity_section(self):
        self.assertIn('no PARITY section', check('parity', '## LINT\n').findings[0].message)
if __name__ == '__main__':
    unittest.main()


class Dependencies(unittest.TestCase):
    def test_missing_required_input(self):
        from checks.parity_closed import check
        from inputs import MissingInput
        from tests.support import TestInputs, page, skeleton
        with self.assertRaises(MissingInput):
            list(check(page(skeleton()), TestInputs()))
