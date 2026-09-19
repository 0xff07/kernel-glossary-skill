"""kind: rule — a subsection with two or more blocks opens by naming the constructs its blocks show or counting its parts."""
import unittest
from checks import purpose_schema as rule
from tests.support import EXCERPT, FIGURE, LINKED, PROSE, page, skeleton, observed

def run(opener):
    text = skeleton(details=f'### A\n\n{opener}\n\n{EXCERPT}\n\n{PROSE}\n\n{FIGURE}\n\n{PROSE}\n')
    return observed(rule.check(page(text), None))

class Schema(unittest.TestCase):
    def test_an_opener_naming_the_construct_or_counting_the_parts_passes(self):
        found = run(f'The ring is {LINKED}, shown first, then the two indexes drawn on the array.')
        self.assertEqual(found.findings, [])
        self.assertEqual(found.footer, 'multi-block-subsections=1 schema-named=1')
        found = run('Two things happen here, in two parts: the definition and the picture of it.')
        self.assertEqual(found.findings, [])

    def test_an_opener_naming_nothing_is_reviewed(self):
        found = run('Rings are a common structure and this one is no exception.')
        self.assertEqual(len(found.findings), 1)
        self.assertIn('names none of the constructs they show (kg_ring)', found.findings[0].message)

    def test_a_single_block_subsection_is_not_counted(self):
        text = skeleton(details=f'### A\n\n{PROSE}\n\n{EXCERPT}\n\n{PROSE}\n')
        found = observed(rule.check(page(text), None))
        self.assertEqual(found.footer, 'multi-block-subsections=0 schema-named=0')
if __name__ == '__main__':
    unittest.main()
