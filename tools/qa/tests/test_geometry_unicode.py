"""kind: rule — an emoji or pictograph in a figure fails; box-drawing, ASCII connectors, circled
digits and dingbats in text style all draw."""
import unittest
from checks.geometry_unicode import check
from tests.support import FIGURE, page


class Geometry(unittest.TestCase):
    def test_emoji_fail(self):
        for cell in ('│ 🚀 │ s1 │', '│ s0 │ ✅ │', '│ ⏰ s1 │', '│ ☕ │ s1 │', '│ ☺️ │ s1 │'):
            found = list(check(page(FIGURE.replace('│ s0 │ s1 │', cell)), None))
            self.assertTrue(any(f.severity == 'FAIL' and 'emoji' in f.message for f in found), cell)

    def test_any_other_character_draws(self):
        for cell in ('│  /  │', '| s0 | s1 |', '+--+--+', r'│ a \ b │', '│ ① ② │', '│ ✔ ✘ ★ ☐ │', '│ ──► ◉ │', '│ R/W  a|b │'):
            found = list(check(page(FIGURE.replace('│ s0 │ s1 │', cell)), None))
            self.assertFalse(any(f.severity == 'FAIL' for f in found), cell)

    def test_inventory_counts_emoji(self):
        found = list(check(page(FIGURE.replace('│ s0 │ s1 │', '│ 🚀 │ 🚀 │')), None))
        self.assertEqual(found[-1].data, {'figures': 1, 'emoji': 2})

    def test_width_and_loose_verticals_do_not_raise_unicode_findings(self):
        text = '```\n' + '─' * 121 + '\n\n│\n```'
        found = list(check(page(text), None))
        self.assertTrue(all(f.severity == 'note' for f in found))
if __name__ == '__main__':
    unittest.main()
