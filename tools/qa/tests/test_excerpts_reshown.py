"""kind: rule — a location link whose lines the page reproduces only in another subsection is
listed for re-showing beside its paragraph; a unit that shows again more than about twelve lines
already shown is listed; links beside their code and links to lines never shown are only counted."""
import unittest
from checks import excerpts_reshown as rule
from tests.support import CAUTION, PROSE, page, TestInputs, observed
BASE = 'https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.c'
LINES = [f'\tline{n};' for n in range(1, 21)]

def fence(cited, count):
    return f'```c\n/* drivers/kg/ring.c:{cited} */\n' + '\n'.join(LINES[cited - 1:cited - 1 + count]) + '\n```'

def link(first, last=None):
    text = f'ring.c:{first}' + (f'-{last}' if last else '')
    return f'[`{text}`]({BASE}#L{first})'

def page_with(a, b):
    return page(f"# The kg ring\n\n{CAUTION}\n\nA ring hands values from a producer to a consumer.\n\n## SUMMARY\n\nThe model is one struct.\n\n"
                "## SPECIFICATIONS\n\nNone applies.\n\n## COVERAGE\n\n### Functions\n\n"
                f"- [`'\\<kg_ring_push\\>':'drivers/kg/ring.c'`]({BASE}#L1): the push\n\n## DOCUMENTATION\n\n## OTHER SOURCES\n\n## DETAILS\n\n"
                f"### The push\n\n{a}\n\n### The reset\n\n{b}\n")

class Reshown(unittest.TestCase):

    def run_on(self, a, b):
        return observed(rule.check(page_with(a, b), TestInputs()))

    def test_a_link_to_lines_shown_only_elsewhere_is_listed(self):
        found = self.run_on(f'{PROSE}\n\n{fence(1, 7)}\n\n{PROSE}', f'The head moves at {link(5)} and the reset follows.')
        self.assertEqual(len(found.rows), 1)
        self.assertIn('ring.c:5 shown only at page', found.rows[0].text)
        self.assertIn('[The push]; re-show the lines beside this paragraph or move it', found.rows[0].text)
        self.assertEqual(found.footer, 'location-links=1 beside=0 elsewhere=1 unreproduced=0 reshows-over-12=0')

    def test_a_link_beside_its_code_and_a_link_to_unshown_lines_are_only_counted(self):
        found = self.run_on(f'The head moves at {link(5)}.\n\n{fence(1, 7)}\n\n{PROSE}', f'The tail is at {link(15, 16)} and nothing shows it.')
        self.assertEqual(found.rows, [])
        self.assertEqual(found.footer, 'location-links=2 beside=1 elsewhere=0 unreproduced=1 reshows-over-12=0')

    def test_a_table_row_is_a_lookup_and_is_not_listed(self):
        table = f'| mode | chosen at |\n|---|---|\n| low | {link(5)} |'
        found = self.run_on(f'{PROSE}\n\n{fence(1, 7)}\n\n{PROSE}', f'{PROSE}\n\n{table}\n\n{PROSE}')
        self.assertEqual(found.rows, [])
        self.assertEqual(found.footer, 'location-links=0 beside=0 elsewhere=0 unreproduced=0 reshows-over-12=0')

    def test_a_long_re_show_is_listed_and_a_short_one_is_not(self):
        found = self.run_on(f'{PROSE}\n\n{fence(1, 20)}\n\n{PROSE}', f'{PROSE}\n\n{fence(3, 13)}\n\n{PROSE}')
        self.assertEqual(len(found.rows), 1)
        self.assertIn('ring.c:3 re-shows 13 lines shown earlier', found.rows[0].text)
        found = self.run_on(f'{PROSE}\n\n{fence(1, 20)}\n\n{PROSE}', f'{PROSE}\n\n{fence(3, 5)}\n\n{PROSE}')
        self.assertEqual(found.rows, [])
if __name__ == '__main__':
    unittest.main()
