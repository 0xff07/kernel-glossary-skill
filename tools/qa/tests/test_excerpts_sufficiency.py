from tests.support import observed
'kind: listing — the unreproduced-locations selector lists a location link whose line no excerpt\non the page reproduces, and passes over one the page shows.'
import unittest
from checks import arrangement_figure_placement, arrangement_units, excerpts_introduced, excerpts_members_named, excerpts_post_fence_subject, excerpts_sufficiency, facts_counts_serve_claims, facts_two_bases, facts_universal_claims, lead_summary_lead, lead_summary_summary, links_bare_spans, page_self_contained, purpose_openers, purpose_spine, style_headings, style_run_on_enumeration
from tests.support import EXCERPT, PROSE, TestInputs, page, skeleton
BASE = 'https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.h'

class UnreproducedLocations(unittest.TestCase):

    def test_lists_only_the_link_outside_every_excerpt(self):
        details = f'### The ring keeps two indexes\n\nThe head is declared at [drivers/kg/ring.h:13]({BASE}#L13) and the ring is freed at [`ring.h:99`]({BASE}#L99).\n\n{EXCERPT}\n\nThe producer writes at the head.\n'
        listing = observed(excerpts_sufficiency.unreproduced_locations(page(skeleton(details=details)), None))
        self.assertEqual(listing.footer, 'location-links=2 unreproduced=1')
        self.assertEqual(len(listing.rows), 1)
        self.assertTrue(listing.rows[0].text.startswith('ring.h:99 | '), listing.rows[0].text)
        self.assertIn('freed at [`ring.h:99`]', listing.rows[0].text)
class ThroughElisions(unittest.TestCase):
    RING_C = ['int kg_push(struct kg_ring *ring)', '{', '\tint ret;', '', '\tring->head++;', '\treturn 0;', '}']

    def test_a_line_after_an_elision_counts_as_reproduced_with_a_tree(self):
        import os, shutil, tempfile
        from measurements import reproduced_lines
        root = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(root, 'drivers', 'kg'))
            open(os.path.join(root, 'drivers', 'kg', 'ring.c'), 'w', encoding='utf-8').write('\n'.join(self.RING_C) + '\n')
            fence = '```c\n/* drivers/kg/ring.c:1 */\nint kg_push(struct kg_ring *ring)\n{\n...\n\tring->head++;\n\treturn 0;\n}\n```'
            details = f'### A\n\n{PROSE}\n\n{fence}\n\n{PROSE}\n'
            p = page(skeleton(details=details))
            self.assertEqual(reproduced_lines(p, TestInputs(tree=root))['drivers/kg/ring.c'], {1, 2, 5, 6, 7})
            self.assertEqual(reproduced_lines(p, None)['drivers/kg/ring.c'], {1, 2, 3, 4, 5, 6})
        finally:
            shutil.rmtree(root)

if __name__ == '__main__':
    unittest.main()


class Ranges(unittest.TestCase):

    def test_a_range_is_reproduced_only_when_every_line_is(self):
        details = f'### The ring keeps two indexes\n\nThe struct is declared at [`ring.h:12-15`]({BASE}#L12) and its neighbour at [`ring.h:12-16`]({BASE}#L12).\n\n{EXCERPT}\n\nThe producer writes at the head.\n'
        listing = observed(excerpts_sufficiency.unreproduced_locations(page(skeleton(details=details)), None))
        self.assertEqual(listing.footer, 'location-links=2 unreproduced=1')
        self.assertTrue(listing.rows[0].text.startswith('ring.h:12-16 | '), listing.rows[0].text)
