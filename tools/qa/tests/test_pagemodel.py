"""pagemodel: fence classification and units, regions, the DETAILS block map, the views."""
import unittest

from tests.support import EXCERPT, FIGURE, LINKED, PROSE, page, skeleton


class Fences(unittest.TestCase):
    def test_kinds(self):
        p = page(skeleton(details=f"### A\n\n{PROSE}\n\n{EXCERPT}\n\n{PROSE}\n\n{FIGURE}\n\n{PROSE}\n\n"
                                  "```\nplain text with no drawing character\n```\n\n" + PROSE + "\n"))
        self.assertEqual([f.kind for f in p.fences], ["excerpt", "figure", "quotation"])
        self.assertEqual(len(p.excerpts), 1)
        self.assertEqual(len(p.figures), 1)
        self.assertEqual(len(p.quotations), 1)

    def test_units_split_on_interior_provenance(self):
        fence = ("```c\n/* drivers/kg/ring.c:10 */\nint a;\nint b;\n/* drivers/kg/ring.c:40 */\nint c;\n```")
        p = page(skeleton(details=f"### A\n\n{PROSE}\n\n{fence}\n\n{PROSE}\n"))
        self.assertEqual([(u.path, u.line, u.lines) for u in p.units],
                         [("drivers/kg/ring.c", 10, ["int a;", "int b;"]), ("drivers/kg/ring.c", 40, ["int c;"])])

    def test_unit_without_provenance(self):
        p = page(skeleton(details=f"### A\n\n{PROSE}\n\n```c\nint a;\n```\n\n{PROSE}\n"))
        self.assertIsNone(p.units[0].path)
        self.assertEqual(p.units[0].lines, ["int a;"])


class Regions(unittest.TestCase):
    def test_sections_and_regions(self):
        p = page(skeleton(registers="The status word holds the ring's state.",
                          details=f"### A\n\n{PROSE}\n\n{EXCERPT}\n\n{PROSE}\n"))
        lines = p.lines
        catalog = next(n for n, l in enumerate(lines, 1) if l.startswith("- [`'"))
        six = next(n for n, l in enumerate(lines, 1) if l.startswith("The status word"))
        prose = next(n for n, l in enumerate(lines, 1) if l.startswith("The producer writes"))
        self.assertEqual(p.region_of(1), "heading")
        self.assertEqual(p.region_of(3), "blockquote")
        self.assertEqual(p.region_of(catalog), "catalog")
        self.assertEqual(p.region_of(six), "section6")
        self.assertEqual(p.region_of(prose), "prose")
        self.assertEqual(p.region_of(p.excerpts[0].start + 1), "excerpt")
        self.assertEqual(p.h2_names, ["SUMMARY", "SPECIFICATIONS", "COVERAGE", "DOCUMENTATION",
                                      "OTHER SOURCES", "REGISTERS", "DETAILS"])
        self.assertEqual(p.section("REGISTERS").region, "section6")
        self.assertEqual(p.section("COVERAGE").region, "catalog")

    def test_lead_and_caution(self):
        p = page(skeleton())
        self.assertEqual(p.lead.start, 0)
        self.assertEqual(p.caution_block[0], "> CAUTION: AI-GENERATED CONTENT")
        self.assertTrue(p.h1.startswith("# "))


class BlockMap(unittest.TestCase):
    def test_map_letters(self):
        items = "\n".join(f"- item {k}" for k in range(6))
        details = (f"### A\n\n{PROSE}\n\n{EXCERPT}\n\n{PROSE}\n\n{FIGURE}\n\n{PROSE}\n\n"
                   f"| a | b |\n|---|---|\n| 1 | 2 |\n\n{PROSE}\n\n{items}\n\n{PROSE}\n\n- one\n- two\n\n"
                   f"#### Sub\n\n{PROSE}\n")
        p = page(skeleton(details=details))
        self.assertEqual(len(p.subsections), 1)
        # A list of any length is "l": never a block, never a recovery ([arrangement.units]).
        self.assertEqual(p.subsections[0]["map"], "P C P D P T P l P l H P")
        self.assertEqual(p.subsections[0]["figures"], 1)
        self.assertEqual(p.subsections[0]["title"], "A")

    def test_excerpt_size_excludes_provenance(self):
        p = page(skeleton(details=f"### A\n\n{PROSE}\n\n{EXCERPT}\n\n{PROSE}\n"))
        block = next(b for b in p.subsections[0]["blocks"] if b.kind == "C")
        self.assertEqual(block.size, 4)            # struct line, two members, the closing brace
        self.assertEqual(block.label, "drivers/kg/ring.h:12")

    def test_two_subsections(self):
        p = page(skeleton(details=f"### A\n\n{PROSE}\n\n### B\n\n{PROSE}\n\n{PROSE}\n"))
        self.assertEqual([s["title"] for s in p.subsections], ["A", "B"])
        self.assertEqual([len(s["paragraphs"]) for s in p.subsections], [1, 2])


class Views(unittest.TestCase):
    def test_prose_view_masks_and_drops(self):
        details = (f"### A\n\nThe helper {LINKED} reads \"a quoted phrase\" at ring.c:12 and `a span`.\n\n"
                   f"{EXCERPT}\n\n{PROSE}\n")
        p = page(skeleton(details=details))
        rows = p.prose_view()
        texts = [r.text for r in rows]
        self.assertTrue(any("The helper § reads § at § and §." == t for t in texts), texts)   # a linked span is still a span
        self.assertFalse(any("struct kg_ring {" in t for t in texts))
        self.assertTrue(any(r.tag == "[H] " and r.text == "A" for r in rows))
        self.assertTrue(any(r.tag == "[C] " and r.in_catalog for r in rows))

    def test_spans_visible(self):
        p = page(skeleton(details="### A\n\nRun `grep foo` here.\n"))
        masked = next(r.text for r in p.prose_view() if r.text.startswith("Run"))
        visible = next(r.text for r in p.prose_view(spans_visible=True) if r.text.startswith("Run"))
        self.assertEqual(masked, "Run § here.")
        self.assertEqual(visible, "Run `grep foo` here.")

    def test_section_six_bullets_are_catalog_bullets_and_other_list_items_are_prose(self):
        text = skeleton(details="### A\n\n- a list item under DETAILS\n\nThe head is at ring.c:12-20 and ring.h:3.\n",
                        registers="- [`KG_CTRL`](https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.h#L3): the control register")
        rows = {r.text: r for r in page(text).prose_view()}
        item = rows["- a list item under DETAILS"]
        self.assertEqual((item.tag, item.region), ("", "prose"))
        six = next(r for r in rows.values() if r.region == "section6" and r.text.startswith("- "))
        self.assertEqual((six.tag, six.in_catalog), ("[C] ", False))
        self.assertIn("The head is at § and §.", rows)

    def test_raw_view_drops_fences_keeps_headings(self):
        p = page(skeleton(details=f"### A\n\n{PROSE}\n\n{EXCERPT}\n\n{PROSE}\n"))
        texts = [t for _n, t in p.raw_view()]
        self.assertIn("### A", texts)
        self.assertFalse(any(t.startswith("struct kg_ring {") for t in texts))

    def test_counted_lines(self):
        self.assertEqual(page("# T\n\na\n").counted_lines(), 3)
        self.assertEqual(page("# T\n\na").counted_lines(), 3)



class Tables(unittest.TestCase):
    def test_negative_values_are_data_rows_with_original_locations(self):
        p = page('| offset | reads |\n|---|---|\n| -1 | 9 |\n| -2 | 3 |')
        self.assertEqual(len(p.tables), 1)
        table, = p.tables
        self.assertEqual(table.header, ['offset', 'reads'])
        self.assertEqual([(r.line, r.cells) for r in table.rows],
                         [(3, ['-1', '9']), (4, ['-2', '3'])])

    def test_split_cells_keeps_an_escaped_pipe(self):
        from pagemodel import split_cells
        self.assertEqual(split_cells("| a \\| b | c |"), ["a \\| b", "c"])
        self.assertEqual(split_cells("| a | | c |"), ["a", "", "c"])
        self.assertEqual(split_cells("| a | b | |"), ["a", "b", ""])

    def test_summary_table_shapes(self):
        p = page(skeleton(summary=f"{PROSE}\n\n| a | b |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n\n{PROSE}"))
        self.assertEqual([b for b in p.summary_blocks() if b[0] == "T"], [("T", (2, 2))])
        p = page(skeleton(summary=f"{PROSE}\n\n|---|---|\n\n{PROSE}"))
        self.assertEqual([b for b in p.summary_blocks() if b[0] == "T"], [("T", (0, 0))])

class Constructs(unittest.TestCase):
    def test_construct_of_names_a_prototype_unit(self):
        from pagemodel import construct_of
        self.assertEqual(construct_of(["int kg_push(struct kg_ring *r, int v);"]), "kg_push()")
        self.assertEqual(construct_of(["\tint ret;"]), "")
        self.assertEqual(construct_of(["int (*fn)(void);"]), "")


class CatalogNames(unittest.TestCase):
    def test_a_name_drops_what_a_parity_row_drops(self):
        from pagemodel import catalog_name
        self.assertEqual(catalog_name("struct tb_nhi *nhi"), "nhi")
        self.assertEqual(catalog_name("unsigned long privdata[]"), "privdata")
        self.assertEqual(catalog_name("tb_domain_add()"), "tb_domain_add")
        self.assertEqual(catalog_name("struct tb"), "tb")
        self.assertEqual(catalog_name("TB_AUTOSUSPEND_DELAY"), "TB_AUTOSUSPEND_DELAY")

    def test_the_page_reports_the_undecorated_names(self):
        entry = ("- [`'\\<struct tb_nhi *nhi\\>':'include/linux/thunderbolt.h'`]"
                 "(https://elixir.bootlin.com/linux/v0.1/source/include/linux/thunderbolt.h#L85): the host interface")
        text = skeleton().replace("## DOCUMENTATION", entry + "\n\n## DOCUMENTATION")
        self.assertIn("nhi", page(text).catalog_names)
        self.assertNotIn("*nhi", page(text).catalog_names)


if __name__ == "__main__":
    unittest.main()
