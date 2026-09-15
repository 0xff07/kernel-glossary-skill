from tests.support import observed
'kind: rule — a paragraph whose location links reach two files no excerpt reproduces is a file jump\nand fails; a compact census that states its total is listed for reading; a stated total with a clause\nper member is still a jump; one file, a reproduced line or a table row is not counted.'
import unittest
from checks import excerpts_cited_shown
from tests.support import EXCERPT, page, skeleton
H = 'https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.h'
C = 'https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.c'
P = 'https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/probe.c'
RING_C = '```c\n/* drivers/kg/ring.c:38 */\nstatic void kg_ring_free(struct kg_ring *ring)\n{\n\tkfree(ring->slots);\n}\n```'

def run(details):
    return observed(excerpts_cited_shown.check(page(skeleton(details=details)), None))

class FileJumps(unittest.TestCase):

    def test_two_unreproduced_files_in_one_paragraph_fail(self):
        details = (f'### The ring keeps two indexes\n\nThe head is declared at [ring.h:13]({H}#L13) and the ring '
                   f'is freed by [`kg_ring_free()`]({C}#L38) at [`ring.c:40`]({C}#L40).\n')
        found = run(details)
        fails = [f for f in found.all if f.severity == 'FAIL']
        self.assertEqual(len(fails), 1)
        self.assertTrue(fails[0].message.startswith('file jump: ring.h:13, ring.c:40 in 2 files'), fails[0].message)
        self.assertEqual(fails[0].data['files'], ['drivers/kg/ring.c', 'drivers/kg/ring.h'])
        self.assertEqual(found.footer, 'paragraphs=3 file-jumps=1 censuses=0')

    def test_reproduced_lines_do_not_count(self):
        details = (f'### The ring keeps two indexes\n\nThe head is declared at [ring.h:13]({H}#L13) and the ring '
                   f'is freed at [`ring.c:40`]({C}#L40).\n\n{EXCERPT}\n\nThe slots go with the ring.\n\n{RING_C}\n\n'
                   'The free releases the slots.\n')
        found = run(details)
        self.assertEqual([f for f in found.all if f.severity == 'FAIL'], [])
        self.assertEqual(found.footer, 'paragraphs=5 file-jumps=0 censuses=0')

    def test_one_file_is_not_a_jump(self):
        details = f'### The ring keeps two indexes\n\nThe head is declared at [ring.h:13]({H}#L13) and freed at [ring.h:99]({H}#L99).\n'
        found = run(details)
        self.assertEqual([f for f in found.all if f.severity == 'FAIL'], [])
        self.assertEqual(found.rows, [])

    def test_a_census_with_its_total_is_listed_for_reading(self):
        details = (f'### The ring keeps two indexes\n\nThree readers take the head: [ring.h:13]({H}#L13), '
                   f'[ring.c:40]({C}#L40) and [probe.c:9]({P}#L9).\n')
        found = run(details)
        self.assertEqual([f for f in found.all if f.severity == 'FAIL'], [])
        self.assertEqual(len(found.rows), 1)
        self.assertTrue(found.rows[0].text.startswith('census across 3 files: ring.h:13, ring.c:40, probe.c:9 | '), found.rows[0].text)
        self.assertEqual(found.rows[0].flags, {'census'})
        self.assertEqual(found.footer, 'paragraphs=3 file-jumps=0 censuses=1')

    def test_a_quantified_census_is_listed_for_reading(self):
        details = (f'### The ring keeps two indexes\n\nEvery reader takes the cached copy: [ring.h:13]({H}#L13), '
                   f'[ring.c:40]({C}#L40) and [probe.c:9]({P}#L9).\n')
        found = run(details)
        self.assertEqual([f for f in found.all if f.severity == 'FAIL'], [])
        self.assertEqual(len(found.rows), 1)
        self.assertEqual(found.footer, 'paragraphs=3 file-jumps=0 censuses=1')

    def test_a_total_with_a_clause_per_member_is_an_explanation(self):
        details = (f'### The ring keeps two indexes\n\nThe head is read by [`kg_probe()`]({P}#L5) as the size of the array it '
                   f'allocates at [probe.c:9]({P}#L9), and by [`kg_ring_free()`]({C}#L38) as the count of slots it drops at '
                   f'[ring.c:40]({C}#L40). Both readers take the cached copy.\n')
        found = run(details)
        fails = [f for f in found.all if f.severity == 'FAIL']
        self.assertEqual(len(fails), 1)
        self.assertEqual(found.rows, [])
        self.assertEqual(found.footer, 'paragraphs=3 file-jumps=1 censuses=0')

    def test_table_rows_and_list_items(self):
        details = (f'### The ring keeps two indexes\n\nThe producer writes at the head.\n\n| member | writer |\n|---|---|\n'
                   f'| head | [ring.h:13]({H}#L13) and [ring.c:40]({C}#L40) |\n\n'
                   f'- the head at [ring.h:13]({H}#L13) and the free at [ring.c:40]({C}#L40)\n')
        found = run(details)
        fails = [f for f in found.all if f.severity == 'FAIL']
        self.assertEqual(len(fails), 1)
        self.assertEqual(fails[0].line, page(skeleton(details=details)).lines.index(f'- the head at [ring.h:13]({H}#L13) and the free at [ring.c:40]({C}#L40)') + 1)
if __name__ == '__main__':
    unittest.main()


class Ranges(unittest.TestCase):

    def test_a_partly_reproduced_range_is_unshown(self):
        details = (f'### The ring keeps two indexes\n\nThe struct spans [`ring.h:12-16`]({H}#L12) and the ring is freed at [`ring.c:40`]({C}#L40).\n\n{EXCERPT}\n\nThe producer writes at the head.\n')
        found = run(details)
        fails = [f for f in found.all if f.severity == 'FAIL']
        self.assertEqual(len(fails), 1)
        self.assertTrue(fails[0].message.startswith('file jump: ring.h:12-16, ring.c:40 in 2 files'), fails[0].message)
        shown = run(details.replace('ring.h:12-16', 'ring.h:12-15'))
        self.assertEqual([f for f in shown.all if f.severity == 'FAIL'], [])
