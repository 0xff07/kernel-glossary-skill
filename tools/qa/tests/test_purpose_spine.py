"""Behavior and boundaries for purpose spine."""
import unittest
from checks.purpose_spine import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_symbol_inventory_and_catalog_order_run(self):
        text = skeleton(details=f'### A\n\n[`struct kg_ring`]({URL}) holds both indexes.')
        found = list(check(page(text), None))
        self.assertTrue(any('-> kg_ring' in f.message and f.severity == 'review' for f in found))
        self.assertFalse(any(f.data and 'catalog-order-run' in f.data.get('flags', []) for f in found))
        entries = '\n'.join(f'- [`\'\\<{name}\\>\':\'f.h\'`]({URL}): role' for name in ('aa', 'bb', 'cc'))
        text = '## COVERAGE\n'+entries+'\n\n## DETAILS\n'+''.join(f'\n### The `{n}` handles values\n\nThe `{n}` handles a value.\n' for n in ('aa','bb','cc'))
        found = list(check(page(text), None))
        self.assertTrue(any(f.data and 'catalog-order-run' in f.data.get('flags', []) for f in found))
