from tests.support import observed
'selector: every listing runs on a page without inputs, and the flags the rules turn into\nfindings fire on the shapes they name.'
import unittest
from checks import arrangement_figure_placement, arrangement_units, excerpts_introduced, excerpts_members_named, excerpts_post_fence_subject, excerpts_sufficiency, facts_counts_serve_claims, facts_two_bases, facts_universal_claims, lead_summary_lead, lead_summary_summary, links_bare_spans, page_self_contained, purpose_openers, purpose_spine, style_headings, style_run_on_enumeration
from tests.support import EXCERPT, FIGURE, PROSE, URL, page, skeleton
LOCATION = 'https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.c#L{}'

class Flags(unittest.TestCase):

    def test_symbol_led_opener(self):
        listing = observed(purpose_openers.openers(page(skeleton(details=f'### A\n\n[`struct kg_ring`]({URL}) holds the indexes.\n')), None))
        self.assertEqual(listing.data['symbol'], 1)
        self.assertTrue(any(('symbol-led' in row.flags for row in listing.rows)))

    def test_bare_noun_heading(self):
        listing = observed(style_headings.details_headings(page(skeleton(details='### Ring\n\nThe producer writes at the head.\n')), None))
        self.assertEqual(listing.data['bare_noun'], 1)
        verb = observed(style_headings.details_headings(page(skeleton()), None))
        self.assertEqual(verb.data['bare_noun'], 0)

    def test_run_on_enumeration(self):
        sites = ', '.join((f'[drivers/kg/{n}.c:{k}]({LOCATION.format(k)})' for k, n in enumerate('abc', 1)))
        details = f'### A\n\nThe callers are {sites}, and [drivers/kg/d.c:4]({LOCATION.format(4)}).\n'
        listing = observed(style_run_on_enumeration.run_on_enumerations(page(skeleton(details=details)), None))
        self.assertEqual(listing.data['with_four_or_more_locations'], 1)
        self.assertTrue(any(('four-or-more-locations' in row.flags for row in listing.rows)))

    def test_pronoun_after_a_fence(self):
        details = f'### A\n\n{PROSE}\n\n{EXCERPT}\n\nIt records the head.\n'
        listing = observed(excerpts_post_fence_subject.first_sentence_after_fence(page(skeleton(details=details)), None))
        self.assertEqual(listing.data['pronoun_openers'], 1)

    def test_members_named_beside_a_definition(self):
        details = f'### A\n\n{PROSE}\n\n{EXCERPT}\n\nThe head advances on every write.\n'
        listing = observed(excerpts_members_named.members_named_beside_definition(page(skeleton(details=details)), None))
        self.assertEqual(listing.data['blocks'], 1)
        self.assertIn('2/2 named; unnamed: -', listing.rows[0].text)

    def test_bare_span_with_its_reason(self):
        listing = observed(links_bare_spans.bare_spans(page(skeleton(details='### A\n\nThe helper returns `-EINVAL` on a bad slot.\n')), None))
        self.assertEqual(len(listing.rows), 1)
        self.assertIn('error value', listing.rows[0].text)

    def test_facts_worklists(self):
        details = '### A\n\nOnly three callers reach the helper. The ring holds sixteen slots.\n'
        p = page(skeleton(summary='The model is a struct.', details=details))
        counts = observed(facts_two_bases.check(p, None))
        universals = observed(facts_universal_claims.check(p, None))
        self.assertEqual(counts.data['sentences'], 2)
        self.assertEqual(universals.data['sentences'], 1)

    def test_census_reads_word_numerals_and_count_columns(self):
        details = '### The ring keeps two indexes\n\nTwenty-six call sites reach the helper, and eleven references name the member.\n\n| member | reads | where they are |\n|---|---|---|\n| a | 9 | one file |\n| b | 3 | another |\n| c | 12 | a third |\n\n| field | bit | meaning |\n|---|---|---|\n| a | 0 | enable |\n| b | 1 | clear |\n| c | 2 | reset |\n\n| offset | read on |\n|---|---|\n| a | 28 lines |\n| b | 12 lines, all in one file |\n'
        listing = observed(facts_counts_serve_claims.census_sentences(page(skeleton(details=details)), None))
        self.assertEqual(listing.data['census'], 1)
        self.assertEqual(listing.data['count_columns'], 2)
        prepositional = '### The ring keeps two indexes\n\n| lock | acquisitions in this file | where |\n|---|---|---|\n| a | 14 | one place |\n| b | 5 | another |\n| c | 1 | a third |\n\n| constant | value | where |\n|---|---|---|\n| a | 100 ms | one place |\n| b | 1000 ms | another |\n'
        second = observed(facts_counts_serve_claims.census_sentences(page(skeleton(details=prepositional)), None))
        self.assertEqual(second.data['count_columns'], 1)
        self.assertNotIn('| bit |', ''.join((row.text for row in listing.rows)))

    def test_deflections_reads_all_three_shapes(self):
        details = "### The ring keeps two indexes\n\nThe arithmetic behind each of them is bandwidth/credits.md's.\n\nEvery register access happens inside a helper another page owns.\n\nThe chain is documented elsewhere.\n\n| helper | register and field | owning page |\n|---|---|---|\n| a | one bit | x/y.md |\n| b | another | x/z.md |\n\nThis page reaches the helper and says what it does.\n"
        listing = observed(page_self_contained.deflections(page(skeleton(details=details)), None))
        self.assertEqual(listing.data['named'], 1)
        self.assertEqual(listing.data['anonymous'], 2)
        self.assertEqual(listing.data['owning_columns'], 1)

    def test_lead_and_summary_sentences(self):
        p = page(skeleton())
        self.assertIn('sentences=1', observed(lead_summary_lead.lead_sentences(p, None)).footer)
        self.assertIn('sentences=1', observed(lead_summary_summary.summary_sentences(p, None)).footer)

class Structure(unittest.TestCase):

    def test_block_map_and_figure_distribution(self):
        details = f'### The ring keeps two indexes\n\n{PROSE}\n\n{EXCERPT}\n\n{PROSE}\n\n### The ring wraps at the end\n\n{PROSE}\n\n{FIGURE}\n\n{PROSE}\n'
        p = page(skeleton(details=details))
        block_map = observed(arrangement_units.block_map(p, None))
        self.assertEqual(block_map.data['maps'], ['P C P', 'P D P'])
        self.assertEqual(block_map.data['subsections'], 2)
        distribution = observed(arrangement_figure_placement.figure_distribution(p, None))
        self.assertEqual(distribution.data, {'figures': 1, 'subsections_with_figures': 1})

    def test_spine(self):
        p = page(skeleton(details=f'### The ring keeps two indexes\n\n[`struct kg_ring`]({URL}) holds both indexes.\n'))
        listing = observed(purpose_spine.subsection_first_symbol(p, None))
        self.assertEqual(listing.data['with_catalog_symbol'], 1)
        self.assertTrue(listing.rows[0].text.rstrip().endswith('-> kg_ring'), listing.rows[0].text)

    def test_against_the_baseline(self):
        now = skeleton(details=f'### A\n\n{PROSE}\n\n{EXCERPT}\n\n{PROSE}\n\n{PROSE}\n')
        before = skeleton(details=f'### A\n\n{PROSE}\n')
        inputs = type('Inputs', (), {'baseline': before})()
        inventory = observed(arrangement_units.baseline_inventory(page(now), inputs))
        self.assertEqual((inventory.data['added'], inventory.data['removed'], inventory.data['changed']), (1, 0, 1))
        reuse = observed(arrangement_units.reuse(page(now), inputs))
        self.assertTrue(any(('repeated on the page' in row.text for row in reuse.rows)))
if __name__ == '__main__':
    unittest.main()
