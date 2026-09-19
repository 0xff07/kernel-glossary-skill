"""kind: rule — a page with eight or more catalog symbols opens DETAILS with an actor table of linked symbols and roles."""
import unittest
from checks import arrangement_actors as rule
from tests.support import CAUTION, PROSE, URL, page, skeleton, observed
BASE = 'https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.h'

def big_catalog(n):
    entries = [f"- [`'\\<kg_fn{i}\\>':'drivers/kg/ring.c'`]({BASE}#L{i + 20}): fn {i}" for i in range(n)]
    return (f"# The kg ring\n\n{CAUTION}\n\nA ring hands values from a producer to a consumer.\n\n## SUMMARY\n\nThe model is one struct.\n\n"
            "## SPECIFICATIONS\n\nNone applies.\n\n## COVERAGE\n\n### Structures\n\n"
            f"- [`'\\<struct kg_ring\\>':'drivers/kg/ring.h'`]({URL}): the ring\n" + '\n'.join(entries) +
            "\n\n## DOCUMENTATION\n\n## OTHER SOURCES\n\n## DETAILS\n\n")
TABLE = f"| actor | role |\n|---|---|\n| [`struct kg_ring`]({URL}) | the ring |\n| [`kg_fn0()`]({BASE}#L20) | pushes |\n| [`kg_fn1()`]({BASE}#L21) | pops |\n"

def run(text):
    return observed(rule.check(page(text), None))

class Actors(unittest.TestCase):
    def test_a_big_catalog_needs_the_table_and_a_small_one_does_not(self):
        found = run(big_catalog(8) + f'{PROSE}\n\n### A\n\n{PROSE}\n')
        self.assertEqual(found.findings[0].severity, 'FAIL')
        self.assertIn('9 catalog symbols and no actor table', found.findings[0].message)
        found = run(skeleton())
        self.assertEqual(found.findings, [])
        self.assertEqual(found.footer, 'catalog=1 actors=absent')

    def test_the_table_is_read_and_its_gaps_reviewed(self):
        found = run(big_catalog(8) + f'{PROSE}\n\n{TABLE}\n### A\n\n{PROSE}\n')
        self.assertEqual(found.findings, [])
        self.assertEqual(found.footer, 'catalog=9 actors=3 structs-covered=1/1')
        bare = TABLE.replace(f'[`struct kg_ring`]({URL})', '`struct kg_ring`')
        found = run(big_catalog(8) + f'{PROSE}\n\n{bare}\n### A\n\n{PROSE}\n')
        self.assertTrue(any('without a linked symbol' in f.message for f in found.findings))
        self.assertTrue(any('cataloged objects absent from the actor table: struct kg_ring' in f.message for f in found.findings))
if __name__ == '__main__':
    unittest.main()
