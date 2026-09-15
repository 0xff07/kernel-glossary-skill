"""Examples, counterexamples and masks for style.label-colon."""
import unittest
from checks.style_label_colon import check
from tests.support import MINIMAL_PAGE, page

class Examples(unittest.TestCase):
    def test_example_0(self):
        found = list(check(page(''.join(MINIMAL_PAGE.splitlines(keepends=True)[:34] + ['The producer writes at the head and the consumer reads at the tail, and the difference between the two indexes is the number of stored values. [`struct kg_ring`](https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.h#L12) holds both indexes beside the slot array. One rule: the host answers first.\n'] + MINIMAL_PAGE.splitlines(keepends=True)[35:])), None))
        for expected in [(35, 'review', 'label colon: …f stored values. § holds both indexes beside the slot array. One rule: the host answers first.…')]:
            self.assertIn(expected, [(f.line, f.severity, f.message) for f in found])

    def test_minimal_page_has_no_violations(self):
        self.assertFalse([f for f in check(page(MINIMAL_PAGE), None) if f.severity == 'FAIL'])

    def test_source_excerpt_is_not_prose(self):
        text = '# Title\n\n```c\n' + ' '.join(['— **bold** usually walks straightforward vtable']) + '\n```\n'
        self.assertFalse([f for f in check(page(text), None) if f.severity == 'FAIL'])


class SectionSix(unittest.TestCase):

    def test_an_entry_bullet_of_section_six_is_a_catalog_bullet(self):
        from tests.support import skeleton
        text = skeleton(registers='- [`KG_CTRL`](https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.h#L3): The control register\n\nOne rule: the host answers first.')
        found = [f for f in check(page(text), None) if f.severity == 'review' and 'label colon' in f.message]
        self.assertEqual(len(found), 1)
        self.assertIn('One rule: the host answers first', found[0].message)
