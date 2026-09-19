"""kg retro: the first-pass tables and EXEMPT lines of a campaign's worksheets, summed per rule."""
import tempfile
import unittest
from pathlib import Path

import retro

RECORDED = '''# Worksheet

## LINT

### First pass
One run before any fix.

| rule | FAIL | review |
|---|---|---|
| `excerpts.verbatim` | 4 | 0 |
| style.superlatives | 1 | 3 |
| TOTAL | 5 | 3 |

EXEMPT style.superlatives "x": ruling
EXEMPT old.rule "y": ruling

LINTED 2026-09-18 page sha256: 0 qa sha256: 1
'''
BARE = '# Worksheet\n\n## LINT\n\nEXEMPT style.walk "z": ruling\n'
WALKER = ('## LINT\n### First pass\n| rule | FAIL | review |\n|---|---|---|\n| style.walk | 0 | 2 |\n\n'
          'EXEMPT style.walk "w": ruling\nEXEMPT style.walk "v": ruling\n')


def campaign(root, extra=0):
    base = Path(root) / 'usb4' / 'acpi'
    base.mkdir(parents=True)
    (base / 'a.worksheet.md').write_text(RECORDED, encoding='utf-8')
    (base / 'b.worksheet.md').write_text(BARE, encoding='utf-8')
    for n in range(extra):
        (base / f'p{n:02}.worksheet.md').write_text(WALKER, encoding='utf-8')
    return Path(root)


class Retro(unittest.TestCase):

    def test_pages_rows_and_listing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = campaign(tmp)
            pages = retro.gather(root)
            self.assertEqual([page['page'] for page in pages], ['usb4/acpi/a', 'usb4/acpi/b'])
            self.assertEqual(pages[0]['first'], {'excerpts.verbatim': (4, 0), 'style.superlatives': (1, 3)})
            self.assertIsNone(pages[1]['first'])
            rows = {row['rule']: row for row in retro.summarize(pages, ['excerpts.verbatim', 'style.superlatives', 'style.walk'])}
            self.assertEqual(list(rows), ['excerpts.verbatim', 'style.superlatives', 'style.walk', 'old.rule'])
            verbatim = rows['excerpts.verbatim']
            self.assertEqual((verbatim['fail'], verbatim['review'], verbatim['hit_pages'], verbatim['pages']), (4, 0, 1, 1))
            self.assertEqual((rows['style.superlatives']['exempt'], rows['style.superlatives']['share']), (1, 0.25))
            self.assertEqual(rows['style.superlatives']['last']['date'], '2026-09-18')
            self.assertEqual((rows['style.walk']['hit_pages'], rows['style.walk']['exempt'], rows['style.walk']['exempt_all'], rows['style.walk']['note']), (0, 0, 1, ''))
            self.assertEqual(rows['old.rule']['note'], 'not a rule now')
            text = '\n'.join(retro.render(root, pages, list(rows.values())))
            self.assertTrue(text.startswith(f'retrospective over 1 page in {root} (1 worksheet without a first-pass record)'), text)
            self.assertIn('usb4/acpi/a 2026-09-18', text)
            listing = '\n'.join(retro.render(root, pages, [rows['style.superlatives']], rule='style.superlatives'))
            self.assertIn('usb4/acpi/a', listing)
            self.assertIn('2026-09-18', listing)
            self.assertNotIn('usb4/acpi/b', listing)

    def test_guard_and_noise_notes_need_enough_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = campaign(tmp, extra=20)
            rows = {row['rule']: row for row in retro.summarize(retro.gather(root), ['excerpts.verbatim', 'style.walk', 'style.lists'])}
            self.assertEqual(rows['style.lists']['note'], 'no hit in 21 pages')
            self.assertEqual((rows['style.walk']['exempt'], rows['style.walk']['exempt_all'], rows['style.walk']['note']), (40, 41, '100% exempt'))
            self.assertEqual(rows['excerpts.verbatim']['note'], '')

    def test_a_worksheet_without_the_heading_records_nothing(self):
        lines = ['## LINT', 'The first pass found nothing worth a table.', '| rule | FAIL | review |', '|---|---|---|', '| style.walk | 0 | 1 |']
        self.assertIsNone(retro.first_pass_table(lines))
        self.assertEqual(retro.first_pass_table(['**First pass**', '', '| rule | FAIL | review |', '|---|---|---|', '| style.walk | 0 | 1 |']), {'style.walk': (0, 1)})


if __name__ == '__main__':
    unittest.main()
