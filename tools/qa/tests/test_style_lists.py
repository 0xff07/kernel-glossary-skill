"""Behavior and boundaries for style lists: a list under DETAILS or SUMMARY fails, once per list."""
import unittest
from checks.style_lists import check
from tests.support import PROSE, page, skeleton

LIST = '- the first item\n- the second item\n  which continues here\n- the third item'


class Lists(unittest.TestCase):

    def test_each_list_under_details_fails_once(self):
        text = skeleton(details=f'### A\n\n{PROSE}\n\n{LIST}\n\n{PROSE}\n\n1. one\n2. two\n\n{PROSE}\n')
        found = list(check(page(text), None))
        self.assertEqual([f.severity for f in found], ['FAIL', 'FAIL'])
        lines = text.split('\n')
        self.assertEqual([f.line for f in found], [lines.index('- the first item') + 1, lines.index('1. one') + 1])
        self.assertIn('a list under DETAILS', found[0].message)

    def test_a_list_in_summary_fails(self):
        found = list(check(page(skeleton(summary=f'The model is one struct.\n\n{LIST}')), None))
        self.assertEqual([f.severity for f in found], ['FAIL'])
        self.assertIn('a list under SUMMARY', found[0].message)

    def test_the_lead_the_catalog_and_section_six_are_not_this_rules(self):
        text = skeleton(lead=f'{PROSE}\n\n- a lead list item',
                        registers='- [`KG_CTRL`](https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.h#L3): the control register')
        self.assertEqual(list(check(page(text), None)), [])

    def test_a_list_inside_a_fence_is_not_a_list(self):
        text = skeleton(details=f'### A\n\n{PROSE}\n\n```\n- not a list\n- reproduced text\n```\n\n{PROSE}\n')
        self.assertEqual(list(check(page(text), None)), [])


if __name__ == '__main__':
    unittest.main()
