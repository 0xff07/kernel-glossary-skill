"""kg retro: the first-pass records and the EXEMPT lines of a workspace, summed per rule."""
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

import retro

RECORD = {"kg": 3, "page": "docs/usb4/acpi/a.md", "date": "2026-09-18", "page_digest": "0" * 64, "qa_digest": "1" * 64,
          "rules": {"excerpts.verbatim": {"FAIL": 4, "review": 0, "complete": True},
                    "style.superlatives": {"FAIL": 1, "review": 3, "complete": True},
                    "style.walk": {"FAIL": 0, "review": 0, "complete": True}}}
CONVERTED = {"kg": 3, "page": "docs/usb4/acpi/c.md", "date": "2026-09-10", "page_digest": None, "qa_digest": None,
             "converted": "from the First pass table of c.worksheet.md", "rules": {"style.walk": {"FAIL": 0, "review": 2}}}
A = '# Worksheet\n\n## LINT\n\nEXEMPT style.superlatives "x": ruling\nEXEMPT old.rule "y": ruling\n\nLINTED 2026-09-18 page sha256: 0 qa sha256: 1\n'
B = '# Worksheet\n\n## LINT\n\nEXEMPT style.walk "z": ruling\n'


def workspace(root):
    base = Path(root) / 'usb4' / 'acpi'
    base.mkdir(parents=True)
    (base / 'a.first-pass.json').write_text(json.dumps(RECORD), encoding='utf-8')
    (base / 'c.first-pass.json').write_text(json.dumps(CONVERTED), encoding='utf-8')
    (base / 'a.worksheet.md').write_text(A, encoding='utf-8')
    (base / 'b.worksheet.md').write_text(B, encoding='utf-8')
    return Path(root)


class Retro(unittest.TestCase):

    def test_records_rows_and_listing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = workspace(tmp)
            records, exemptions = retro.gather(root)
            self.assertEqual([r['page'] for r in records], ['usb4/acpi/a', 'usb4/acpi/c'])
            self.assertEqual(records[0]['rules'], {'excerpts.verbatim': (4, 0), 'style.superlatives': (1, 3), 'style.walk': (0, 0)})
            self.assertEqual((records[0]['converted'], records[1]['converted']), (False, True))
            self.assertEqual(exemptions, {'usb4/acpi/a': Counter({'style.superlatives': 1, 'old.rule': 1}),
                                          'usb4/acpi/b': Counter({'style.walk': 1})})
            rows = {row['rule']: row for row in retro.summarize(records, exemptions, ['excerpts.verbatim', 'style.superlatives', 'style.walk', 'style.lists'])}
            self.assertEqual(list(rows), ['excerpts.verbatim', 'style.superlatives', 'style.walk', 'style.lists', 'old.rule'])
            verbatim = rows['excerpts.verbatim']
            self.assertEqual((verbatim['pages'], verbatim['hit_pages'], verbatim['fail'], verbatim['review'], verbatim['exempt']), (1, 1, 4, 0, 0))
            self.assertEqual((rows['style.superlatives']['fail'], rows['style.superlatives']['review'], rows['style.superlatives']['exempt']), (1, 3, 1))
            # the converted record names style.walk, so both records are its sample; one hit
            self.assertEqual((rows['style.walk']['pages'], rows['style.walk']['hit_pages'], rows['style.walk']['review'], rows['style.walk']['exempt']), (2, 1, 2, 1))
            self.assertEqual((rows['style.lists']['pages'], rows['style.lists']['hit_pages']), (0, 0))
            self.assertEqual((rows['old.rule']['known'], rows['old.rule']['exempt']), (False, 1))
            text = retro.render(root, records, exemptions, list(rows.values()))
            self.assertTrue(text[0].startswith(f'retrospective over 2 first-pass records and 2 worksheets in {root} (1 record converted'), text[0])
            self.assertIn('rules the records or the worksheets name that the skill no longer carries:', text)
            self.assertTrue(text[-1].startswith('old.rule'))
            listing = retro.render(root, records, exemptions, [rows['style.walk']], rule='style.walk')
            self.assertEqual(len(listing), 5)
            self.assertIn('usb4/acpi/a', listing[2])
            self.assertIn('no first-pass record naming the rule', next(l for l in listing if 'usb4/acpi/b' in l))
            self.assertIn('2026-09-10', next(l for l in listing if 'usb4/acpi/c' in l))

    def test_a_record_naming_no_valid_rule_is_an_empty_sample(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / 'x'
            base.mkdir()
            (base / 'p.first-pass.json').write_text(json.dumps({'kg': 3, 'rules': {'TOTAL': {'FAIL': 5, 'review': 3}}}), encoding='utf-8')
            records, exemptions = retro.gather(tmp)
            self.assertEqual((records[0]['rules'], exemptions), ({}, {}))
            self.assertEqual(retro.summarize(records, exemptions, ['style.walk'])[0]['pages'], 0)


if __name__ == '__main__':
    unittest.main()
