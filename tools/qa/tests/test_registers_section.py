"""kind: rule — REGISTERS draws its registers: a table under REGISTERS is listed, and so is a REGISTERS that links register definitions and draws none; a page without the section reports nothing."""
import unittest
from checks import registers_section as rule
from tests.support import FIGURE, page, skeleton, observed
REG = 'https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/kg_regs.h'
HELPER = 'https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.c'

def run(registers):
    return observed(rule.check(page(skeleton(registers=registers)), None))

class RegistersSection(unittest.TestCase):
    def test_a_drawn_register_passes(self):
        found = run(f'[`KG_RING_CS_0`]({REG}#L4) holds the enable bit the probe sets.\n\n{FIGURE}\n\nBit 0 is the enable.')
        self.assertEqual(found.rows, [])
        self.assertEqual(found.footer, 'tables=0 register-links=1 figures=1')

    def test_a_table_under_registers_is_listed(self):
        found = run(f'| register | helper |\n|---|---|\n| [`KG_RING_CS_0`]({REG}#L4) | [`kg_ring_push()`]({HELPER}#L1) |\n\n{FIGURE}')
        self.assertEqual(len(found.rows), 1)
        self.assertIn('table of 1 rows under REGISTERS', found.rows[0].text)
        self.assertEqual(found.footer, 'tables=1 register-links=1 figures=1')

    def test_register_links_without_a_figure_are_listed(self):
        found = run(f'[`KG_RING_CS_0`]({REG}#L4) holds the enable bit the probe sets.')
        self.assertEqual(len(found.rows), 1)
        self.assertIn('links 1 register definitions and draws none', found.rows[0].text)
        self.assertEqual(found.footer, 'tables=0 register-links=1 figures=0')

    def test_a_page_without_the_section_reports_nothing(self):
        found = observed(rule.check(page(skeleton()), None))
        self.assertEqual(found.rows, [])
        self.assertEqual(found.footer, 'no REGISTERS section')

if __name__ == '__main__':
    unittest.main()
