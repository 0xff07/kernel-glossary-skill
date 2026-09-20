"""kind: rule — a register grid keeps its cell boundaries on the bit grid and its dividers at the boundaries of the rows beside them."""
import unittest
from checks import registers_ruler as rule
from tests.support import page, skeleton, observed
RULER = ("    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1\n"
         "           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0\n")
TOPB = "          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐\n"
GOOD = ("```\n    A word\n    ──────\n\n" + RULER + TOPB +
        "    DW0   │       device_id (31:16)       │       vendor_id (15:0)        │\n"
        "          ├───────────────┬───────────────┴───────────────────────────────┤\n"
        "    DW1   │   revision    │                     rest (23:0)               │\n"
        "          └───────────────┴───────────────────────────────────────────────┘\n```")
PER_BIT = ("```\n    A word\n    ──────\n\n" + RULER + TOPB +
        "    DW0   │       device_id (31:16)       │       vendor_id (15:0)        │\n"
        "          ├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤\n"
        "    DW1   │   revision    │                     rest (23:0)               │\n"
        "          └───────────────┴───────────────────────────────────────────────┘\n```")
OFF_GRID = ("```\n    A word\n    ──────\n\n" + RULER + TOPB +
        "    DW0   │      device_id (31:16)       │        vendor_id (15:0)        │\n"
        "          └──────────────────────────────┴────────────────────────────────┘\n```")

def run(fig):
    return observed(rule.check(page(skeleton(details=f'### A\n\nThe word is drawn.\n\n{fig}\n\nA sentence after.\n')), None))

class Ruler(unittest.TestCase):
    def test_a_grid_with_matching_dividers_passes(self):
        found = run(GOOD)
        self.assertEqual(found.findings, [])
        self.assertEqual(found.footer, 'grids=1 off-grid=0 bad-dividers=0')

    def test_a_per_bit_divider_fails(self):
        found = run(PER_BIT)
        self.assertEqual([f.severity for f in found.findings], ['FAIL'])
        self.assertIn('divider has', found.findings[0].message)

    def test_a_boundary_off_the_bit_grid_fails(self):
        found = run(OFF_GRID)
        self.assertEqual([f.severity for f in found.findings], ['FAIL'])
        self.assertIn('off the bit grid', found.findings[0].message)

    def test_a_figure_without_a_ruler_is_not_read(self):
        found = run("```\n    ┌────┐\n    │ s0 │\n    └────┘\n```")
        self.assertEqual(found.footer, 'grids=0 off-grid=0 bad-dividers=0')

if __name__ == '__main__':
    unittest.main()
