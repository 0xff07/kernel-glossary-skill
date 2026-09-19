"""The page as every check reads it, parsed once per run: the sections and their regions, the
fences and their excerpt units, the code spans, the paragraphs, the DETAILS subsections with their
block maps, the tables, the catalog, and the three views (prose, raw, spans-visible).

Region rules are stated once here: catalog is SPECIFICATIONS, COVERAGE, DOCUMENTATION and OTHER
SOURCES; section6 is the subsystem's reference section (REGISTERS, METHODS, PRIMITIVES or
INTERFACES); a non-C fence is a figure when a line carries a drawing character and a quotation
otherwise; everything else outside a heading, a blockquote or a fence is prose.
"""
import collections
import re

# ---- the constants the guidelines state once ----------------------------------------------------

CATALOG_SECTIONS = ("SPECIFICATIONS", "COVERAGE", "DOCUMENTATION", "OTHER SOURCES")
SECTION_SIX = ("REGISTERS", "METHODS", "PRIMITIVES", "INTERFACES")
DETAILS = "DETAILS"
SUMMARY = "SUMMARY"
# the box-drawing and block-element blocks, the arrows and the geometric shapes (figures.md [geometry])
BOX_DRAWING = re.compile("[\\u2500-\\u259f\\u2190-\\u21ff\\u25a0-\\u25ff]")
ELIXIR = re.compile(r"elixir\.bootlin\.com/linux/([^/\s)]+)/source/([^#)?]+)(?:\?[^#)]*)?(?:#L(\d+))?")
ELIXIR_VERSION = re.compile(r"elixir\.bootlin\.com/linux/([^/\s)]+)/source/")
CITED_SOURCE = re.compile(r"elixir\.bootlin\.com/linux/[^/\s)]+/source/([\w./-]+?)(?:#|\)|\s|$)")
LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
CODE_LINK = re.compile(r"\[`([^`]+)`\]\(([^)]+)\)")
CODE_LINK_ANY = re.compile(r"\[`[^`]+`\]\([^)]*\)")
BARE_SPAN = re.compile(r"`([^`\n]+)`")
CODE_SPAN = re.compile(r"`[^`]*`")
QUOTATION = re.compile(r'"[^"]*"')
PROVENANCE = re.compile(r"^/\* ([\w./-]+):(\d+)\b[^*]*\*/\s*$")
PROVENANCE_FILE = re.compile(r"/\* ([\w./-]+):\d+")
ELISION = "..."
CATALOG_SYMBOL = re.compile(r"\[`'\\<([^\\]+)\\>'(?::'[^']*')?`\]")
# the decoration a catalog name carries and a COMPLETENESS row does not: the tag, a pointer star, an
# array bound, a call's parentheses
NAME_DECORATION = re.compile(r"\(\)$|\[[^\]]*\]$")
CATALOG_ENTRY = re.compile(r"^- \[`(?:'\\<([^\\]+)\\>'(?::'[^']*')?|([^`'][^`]*))`\]"
                           r"\((https://elixir\.bootlin\.com/linux/[^/\s)]+/source/([^#)]+)(?:#L(\d+))?)\)")
PLAIN_ENTRY = re.compile(r"^- \[`([^`'][^`]*)`\]\(https://elixir\.bootlin\.com/")
TABLE_SEPARATOR = re.compile(r"^\|(?:\s*:?-{3,}:?\s*\|)+\s*$")
UNESCAPED_PIPE = re.compile(r"(?<!\\)\|")
ITEM = re.compile(r"^(\s*[-*]|\s*\d+\.)\s")
HEADING4 = re.compile(r"^#{4,6}\s")
RETURN_TYPE_LINE = re.compile(r"^(?!(?:return|else|do|goto|break|continue|case|default)\b)"
                              r"[A-Za-z_]\w*(?:\s+[A-Za-z_]\w*)*\s*\**\s*$")
COMMENT_STARTS = ("/*", " *", "*/", "//", "}")
TAGS = ("struct", "enum", "union")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
# the block map's letters: prose (P), excerpt (C), figure (D), table (T), other fence (Q), list (l) and heading (H); DENSE are the blocks
DENSE = set("CDTQ")
LABEL_CLIP = 60
FIGURE_CLIP = 70
BRIDGE_CLIP = 110
# the view's masks (checking.md [sweeps]); links, spans and quotes use the regexes above
VIEW_LOCATION = re.compile(r"\b[\w/.-]+\.(c|h|rst|S):\d+(?:-\d+)?")
VIEW_COLON = re.compile(r"::|\d+:\d+")
# the constructs a C unit's first code line defines, named as prose names them (a tool convention)
CONSTRUCT_TAGGED = re.compile(r"^(?:static\s+|extern\s+|const\s+)*(?:struct|enum|union)\s+(\w+)\s*\{")
CONSTRUCT_MACRO = re.compile(r"^#define\s+(\w+)")
# every qualifier and type word is one token, so the pattern never backtracks across them
CONSTRUCT_FUNCTION = re.compile(r"^(?:[\w*]+\s+)+\*?(\w+)\s*\([^;]*$")
CONSTRUCT_NAME_LINE = re.compile(r"^([A-Za-z_]\w*)\s*\(")
# a unit of prototypes defines nothing, so the construct prose can name is the first one declared
CONSTRUCT_PROTOTYPE = re.compile(r"^(?:[\w*]+\s+)+\*?(\w+)\s*\([^;]*\)\s*;\s*$")

Fence = collections.namedtuple("Fence", "start end lang kind body units")
Unit = collections.namedtuple("Unit", "fence path line lines start")
SpanOccurrence = collections.namedtuple("SpanOccurrence", "text line col region linked url")
Block = collections.namedtuple("Block", "kind line size label text stats")
ViewRow = collections.namedtuple("ViewRow", "line tag text region in_catalog")
Section = collections.namedtuple("Section", "name start end region")
TableRow = collections.namedtuple("TableRow", "line cells")
Table = collections.namedtuple("Table", "line header rows region")


class SpanSummary:
    """One code span of the page, with how often it is linked, how often bare, and where."""

    def __init__(self, text, region):
        self.text = text
        self.region = region
        self.linked = 0
        self.bare = 0
        self.at = []
        self.urls = []


def split_cells(line):
    """The cells of a table row, an escaped pipe kept inside its cell."""
    cells = UNESCAPED_PIPE.split(line.strip())
    if cells and not cells[0].strip():
        cells = cells[1:]
    if cells and not cells[-1].strip():
        cells = cells[:-1]
    return [cell.strip() for cell in cells]


def is_code_line(text):
    """A body line that can carry a definition: not blank, a comment, a brace or an elision."""
    if not text:
        return False
    if text.startswith(COMMENT_STARTS):
        return False
    return text.strip() != ELISION


def prose_text(text):
    """A line as a reader reads it: links reduced to their text, code spans to X."""
    return CODE_SPAN.sub("X", LINK.sub(r"\1", text))


def sentences_of(text):
    """The sentences of one paragraph."""
    return [s for s in SENTENCE_END.split(prose_text(text).strip()) if re.search(r"\w", s)]


def word_count(text):
    """The words of one paragraph: every whitespace-separated token carrying a word character."""
    return sum(1 for word in prose_text(text).split() if re.search(r"\w", word))


def prose_stats(text):
    """(words, sentences, the length in words of each sentence) of one paragraph."""
    found = sentences_of(text)
    return word_count(text), len(found), [len(s.split()) for s in found]


def catalog_name(key):
    """The symbol a catalog entry names, as a COMPLETENESS row and the prose spell it: the last word of
    the entry, without its pointer star, array bound or parentheses."""
    return NAME_DECORATION.sub("", key.split()[-1]).strip("*&")


def on_page_pattern(key):
    """A tagged catalog key is searched with its tag and a plain name without one."""
    words = key.split()
    if len(words) == 2 and words[0] in TAGS:
        return r"(?<![\w])" + words[0] + r"\s+" + re.escape(words[1]) + r"(?![\w])"
    return r"(?<![\w])(?<!struct )(?<!enum )(?<!union )" + re.escape(key) + r"(?![\w])"


def construct_of(body):
    """The construct a unit's first code line defines, as prose would name it, or ''."""
    for line in body:
        text = line.rstrip()
        if not is_code_line(text):
            continue
        match = CONSTRUCT_TAGGED.match(text)
        if match:
            return match.group(1)
        match = CONSTRUCT_MACRO.match(text)
        if match:
            return match.group(1)
        match = CONSTRUCT_FUNCTION.match(text)
        if match:
            return match.group(1) + "()"
        match = CONSTRUCT_PROTOTYPE.match(text)
        if match:
            return match.group(1) + "()"
        match = CONSTRUCT_NAME_LINE.match(text)
        if match and not text.endswith(";"):
            return match.group(1) + "()"
        return ""
    return ""


class Page:
    """One page, parsed once."""

    def __init__(self, path, text=None):
        self.path = path
        if text is None:
            text = open(path, encoding="utf-8").read()
        self.raw = text
        self.lines = text.split("\n")
        self._parse_fences()
        self._parse_headings()
        self._parse_regions()
        self._parse_spans()
        self._parse_catalog()
        self._parse_tables()
        self._parse_paragraphs()
        self._parse_subsections()

    # ---- fences and units ----

    def _parse_fences(self):
        self.fences = []
        lines = self.lines
        i = 0
        while i < len(lines):
            if not lines[i].startswith("```"):
                i += 1
                continue
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            lang = lines[i][3:].strip()
            body = lines[i + 1:j]
            if lang == "c":
                kind = "excerpt"
            elif any(BOX_DRAWING.search(line) for line in body):
                kind = "figure"
            else:
                kind = "quotation"
            fence = Fence(i + 1, j + 1, lang, kind, body, [])
            if kind == "excerpt":
                fence.units.extend(self._units_of(fence))
            self.fences.append(fence)
            i = j + 1
        self.units = [unit for fence in self.fences for unit in fence.units]

    @staticmethod
    def _units_of(fence):
        out = []
        current = None
        for k, line in enumerate(fence.body):
            match = PROVENANCE.match(line.strip())
            if match:
                if current:
                    out.append(current)
                current = Unit(fence, match.group(1), int(match.group(2)), [], fence.start + 1 + k)
            elif current is None:
                current = Unit(fence, None, None, [line], fence.start + 1 + k)
            else:
                current.lines.append(line)
        if current:
            out.append(current)
        return out

    def in_fence(self, n):
        """True when the 1-based line n lies inside a fence, markers included."""
        return self._fence_at(n) is not None

    def _fence_at(self, n):
        for fence in self.fences:
            if fence.start <= n <= fence.end:
                return fence
        return None

    @property
    def excerpts(self):
        return [f for f in self.fences if f.kind == "excerpt"]

    @property
    def figures(self):
        return [f for f in self.fences if f.kind == "figure"]

    @property
    def quotations(self):
        return [f for f in self.fences if f.kind == "quotation"]

    def excerpted_code(self):
        """Every line of every C fence, joined."""
        return "\n".join(line for fence in self.excerpts for line in fence.body)

    # ---- headings, sections, regions ----

    def _parse_headings(self):
        self.headings = []                        # (line, text) outside fences
        for n, line in enumerate(self.lines, 1):
            if line.startswith("#") and not self.in_fence(n):
                self.headings.append((n, line))
        self.h1 = self.lines[0] if self.lines and self.lines[0].startswith("# ") else None
        self.caution_block = self.lines[2:5] if len(self.lines) >= 5 else []
        h2 = [(n, line.strip()[3:].strip()) for n, line in self.headings if line.startswith("## ")]
        self.sections = []
        for k, (n, name) in enumerate(h2):
            end = h2[k + 1][0] - 1 if k + 1 < len(h2) else len(self.lines)
            if name in CATALOG_SECTIONS:
                region = "catalog"
            elif name in SECTION_SIX:
                region = "section6"
            else:
                region = "prose"
            self.sections.append(Section(name, n, end, region))
        self.h2_names = [s.name for s in self.sections]
        first = h2[0][0] if h2 else len(self.lines) + 1
        self.lead = Section("lead", 0, first - 1, "prose")

    def section(self, name):
        for s in self.sections:
            if s.name == name:
                return s
        return None

    def _parse_regions(self):
        self.regions = []
        current = "prose"
        for n, line in enumerate(self.lines, 1):
            fence = self._fence_at(n)
            if fence is not None:
                self.regions.append(fence.kind)
                continue
            if line.startswith("## "):
                name = line.strip()[3:].strip()
                current = "catalog" if name in CATALOG_SECTIONS else \
                    "section6" if name in SECTION_SIX else "prose"
                self.regions.append("heading")
                continue
            if line.startswith("#"):
                self.regions.append("heading")
                continue
            if not line.strip():
                self.regions.append("blank")
                continue
            if line.startswith(">"):
                self.regions.append("blockquote")
                continue
            self.regions.append(current)

    def region_of(self, n):
        """The region of the 1-based line n."""
        return self.regions[n - 1] if 0 < n <= len(self.regions) else "blank"

    def section_of(self, n):
        """The H2 section the 1-based line n sits under, or the lead."""
        for s in self.sections:
            if s.start <= n <= s.end:
                return s
        return self.lead

    # ---- code spans ----

    def _parse_spans(self):
        self.span_occurrences = []
        summaries = {}
        for n, line in enumerate(self.lines, 1):
            region = self.region_of(n)
            if region in ("excerpt", "figure", "quotation", "blank", "blockquote"):
                continue
            if line.startswith("## "):
                continue
            span_region = "catalog" if region == "catalog" else "prose"
            for match in CODE_LINK.finditer(line):
                self.span_occurrences.append(SpanOccurrence(match.group(1), n, match.start(),
                                                            span_region, True, match.group(2)))
                summary = summaries.setdefault(match.group(1), SpanSummary(match.group(1), span_region))
                if span_region == "prose":
                    summary.region = "prose"
                summary.linked += 1
                if match.group(2) not in summary.urls:
                    summary.urls.append(match.group(2))
            for match in BARE_SPAN.finditer(CODE_LINK_ANY.sub(" ", line)):
                self.span_occurrences.append(SpanOccurrence(match.group(1), n, match.start(),
                                                            span_region, False, None))
                summary = summaries.setdefault(match.group(1), SpanSummary(match.group(1), span_region))
                if span_region == "prose":
                    summary.region = "prose"
                summary.bare += 1
                if span_region == "prose":
                    summary.at.append(n)
        self.spans = summaries

    def linked_spans(self):
        return [s for s in self.spans.values() if s.linked]

    def bare_only_spans(self, region):
        return [s for s in self.spans.values() if s.region == region and s.bare and not s.linked]

    def bare_occurrences(self):
        return sum(s.bare for s in self.spans.values())

    def versions(self):
        """Every kernel version the page's Elixir links pin, with its count."""
        return collections.Counter(ELIXIR_VERSION.findall(self.raw))

    def version(self):
        found = self.versions()
        return next(iter(found)) if len(found) == 1 else None

    def cited_files(self):
        """Every tree file the page cites, from its provenance comments and its Elixir links."""
        return sorted(set(PROVENANCE_FILE.findall(self.raw)) | set(CITED_SOURCE.findall(self.raw)))

    # ---- the catalog ----

    def _parse_catalog(self):
        keys = []
        for match in CATALOG_SYMBOL.finditer(self.raw):
            key = " ".join(match.group(1).split())
            if key not in keys:
                keys.append(key)
        coverage = self.section("COVERAGE")
        body = self.lines[coverage.start:coverage.end] if coverage else []
        for line in body:
            match = PLAIN_ENTRY.match(line)
            if match:
                key = " ".join(match.group(1).split())
                if key not in keys:
                    keys.append(key)
        self.catalog_keys = keys
        self.catalog_names = [catalog_name(key) for key in keys]
        self.catalog_entries = []                 # (key, path, line, page line) over every catalog section
        for n, line in enumerate(self.lines, 1):
            if self.region_of(n) != "catalog":
                continue
            match = CATALOG_ENTRY.match(line)
            if match:
                key = " ".join((match.group(1) or match.group(2)).split())
                self.catalog_entries.append((key, match.group(4), int(match.group(5)) if match.group(5) else None, n))

    def _parse_tables(self):
        """Tables with a header separator, escaped pipes and original row locations."""
        self.tables = []
        for n, line in enumerate(self.lines, 1):
            if self.in_fence(n) or not line.startswith('|') or n >= len(self.lines):
                continue
            if not TABLE_SEPARATOR.match(self.lines[n]):
                continue
            rows = []
            for at in range(n + 2, len(self.lines) + 1):
                text = self.lines[at - 1]
                if not text.startswith('|'):
                    break
                if not TABLE_SEPARATOR.match(text):
                    rows.append(TableRow(at, split_cells(text)))
            self.tables.append(Table(n, split_cells(line), rows, self.region_of(n)))

    # ---- paragraphs ----

    def _parse_paragraphs(self):
        """Every line of running prose outside the catalog sections: one paragraph per line."""
        self.paragraphs = []
        for n, line in enumerate(self.lines, 1):
            region = self.region_of(n)
            if region not in ("prose", "section6"):
                continue
            if line.startswith("|") or ITEM.match(line) or line.startswith(("    ", "\t")):
                continue
            words, count, lengths = prose_stats(line)
            self.paragraphs.append(Block("P", n, words, "", line, (words, count, lengths)))

    def is_prose_line(self, n):
        """Running prose at the 1-based line n: not blank, heading, table row, blockquote, list
        item, fence or indented block."""
        line = self.lines[n - 1]
        if self.region_of(n) in ("blank", "heading", "blockquote", "excerpt", "figure", "quotation"):
            return False
        if line.startswith("|") or ITEM.match(line) or line.startswith(("    ", "\t")):
            return False
        return True

    # ---- the block reader (arrangement) ----

    def _read_fence(self, numbered, i):
        n, line = numbered[i]
        lang = line[3:].strip()
        j = i + 1
        while j < len(numbered) and not numbered[j][1].startswith("```"):
            j += 1
        body = [text for _m, text in numbered[i + 1:j] if text.strip()]
        raw_body = [text for _m, text in numbered[i + 1:j]]
        if lang == "c":
            marks = [f"{m.group(1)}:{m.group(2)}" for m in
                     (PROVENANCE.match(t.strip()) for t in body) if m]
            label = " + ".join(marks) if marks else (body[0].strip()[:LABEL_CLIP] if body else "")
            size = sum(1 for t in body if not PROVENANCE.match(t.strip()) and t.strip() != ELISION)
            construct = construct_of(raw_body)
            return Block("C", n, size, label, construct, {"body": raw_body}), j + 1
        kind = "D" if any(BOX_DRAWING.search(t) for t in body) else "Q"
        label = body[0].strip()[:FIGURE_CLIP] if body else ""
        return Block(kind, n, len(body), label, "", {}), j + 1

    def _read_table(self, numbered, i):
        n, line = numbered[i]
        j = i
        while j < len(numbered) and numbered[j][1].startswith("|"):
            j += 1
        return Block("T", n, j - i, line.strip()[:FIGURE_CLIP], "", {}), j

    def _read_list(self, numbered, i):
        n, line = numbered[i]
        j = i
        while j < len(numbered) and (ITEM.match(numbered[j][1]) or numbered[j][1].startswith(" ")):
            j += 1
        items = sum(1 for _m, text in numbered[i:j] if ITEM.match(text))
        # A list is never a block ([arrangement.units]); it is neither prose nor a recovery.
        return Block("l", n, items, line.strip()[:FIGURE_CLIP], "", {}), j

    def _read_heading(self, numbered, i):
        n, line = numbered[i]
        return Block("H", n, len(line.lstrip("#").split()), line.strip()[:FIGURE_CLIP], "", {}), i + 1

    def _read_paragraph(self, numbered, i):
        n, _line = numbered[i]
        j = i
        while j < len(numbered) and numbered[j][1].strip() and not numbered[j][1].startswith(("```", "|")) \
                and not HEADING4.match(numbered[j][1]):
            j += 1
        if j == i:
            j = i + 1
        text = " ".join(t for _m, t in numbered[i:j])
        words, count, lengths = prose_stats(text)
        quoted = " ".join(LINK.sub(r"\1", text).split())[:BRIDGE_CLIP]
        return Block("P", n, words, "", quoted, (words, count, lengths)), j

    def blocks_of(self, numbered):
        """[(Block)] for a run of numbered lines: the block map of a subsection or a page."""
        out = []
        i = 0
        while i < len(numbered):
            _n, line = numbered[i]
            if not line.strip():
                i += 1
                continue
            if line.startswith("```"):
                block, i = self._read_fence(numbered, i)
            elif line.startswith("|"):
                block, i = self._read_table(numbered, i)
            elif ITEM.match(line):
                block, i = self._read_list(numbered, i)
            elif HEADING4.match(line):
                block, i = self._read_heading(numbered, i)
            else:
                block, i = self._read_paragraph(numbered, i)
            out.append(block)
        return out

    def _parse_subsections(self):
        """Every ### subsection under DETAILS with its block map."""
        self.subsections = []
        details = self.section(DETAILS)
        if details is None:
            return
        current = None
        in_fence = False
        for n in range(details.start + 1, details.end + 1):
            line = self.lines[n - 1]
            if line.startswith("```"):
                in_fence = not in_fence
            elif not in_fence and line.startswith("## "):
                break
            elif not in_fence and line.startswith("### "):
                current = {"line": n, "title": line[4:].strip(), "numbered": []}
                self.subsections.append(current)
                continue
            if current is not None:
                current["numbered"].append((n, line))
        for sub in self.subsections:
            blocks = self.blocks_of(sub["numbered"])
            sub["blocks"] = blocks
            sub["kinds"] = [b.kind for b in blocks]
            sub["map"] = " ".join(sub["kinds"])
            sub["paragraphs"] = [b for b in blocks if b.kind == "P"]
            sub["words"] = sum(b.size for b in sub["paragraphs"])
            sub["dense"] = sum(1 for b in blocks if b.kind in DENSE)
            sub["figures"] = sum(1 for b in blocks if b.kind == "D")
            sub["source"] = sum(b.size for b in blocks if b.kind == "C")
            sub["end"] = sub["numbered"][-1][0] if sub["numbered"] else sub["line"]

    # ---- the lead and the SUMMARY ----

    def lead_blocks(self):
        """The lead's blocks as (kind, value): P carries its text, the rest their size."""
        lines = self.lines
        end = self.lead.end
        out = []
        i = 0
        while i < end:
            line = lines[i]
            if not line.strip() or line.startswith(("#", ">")):
                i += 1
                continue
            if line.startswith("```"):
                lang = line[3:].strip()
                j = i + 1
                while j < end and not lines[j].startswith("```"):
                    j += 1
                visible = [t for t in lines[i + 1:j] if t.strip()]
                out.append((self._fence_letter(lang, visible), len(visible)))
                i = j + 1
                continue
            if line.startswith("|") or ITEM.match(line):
                j = i
                while j < end and lines[j].strip() and not lines[j].startswith("```"):
                    j += 1
                out.append(("T" if line.startswith("|") else "L", j - i))
                i = j
                continue
            j = i
            while j < end and lines[j].strip() and not lines[j].startswith(("```", "|", ">", "#")):
                j += 1
            out.append(("P", " ".join(lines[i:j])))
            i = j
        return out

    def summary_blocks(self):
        """The SUMMARY's blocks as (kind, value); a table carries (body rows, columns)."""
        section = self.section(SUMMARY)
        if section is None:
            return None
        lines = self.lines
        i, end = section.start, section.end
        out = []
        while i < end:
            line = lines[i]
            if not line.strip():
                i += 1
                continue
            if line.startswith("```"):
                lang = line[3:].strip()
                j = i + 1
                while j < end and not lines[j].startswith("```"):
                    j += 1
                visible = [t for t in lines[i + 1:j] if t.strip()]
                out.append((self._fence_letter(lang, visible), len(visible)))
                i = j + 1
                continue
            if line.startswith("|"):
                j = i
                while j < end and lines[j].startswith("|"):
                    j += 1
                rows = [split_cells(t) for t in lines[i:j] if not TABLE_SEPARATOR.match(t)]
                widest = max((len(r) for r in rows), default=0)
                out.append(("T", (max(len(rows) - 1, 0), widest)))
                i = j
                continue
            j = i
            while j < end and lines[j].strip() and not lines[j].startswith(("```", "|")):
                j += 1
            out.append(("P", " ".join(lines[i:j])))
            i = j
        return out

    @staticmethod
    def _fence_letter(lang, visible):
        if lang == "c":
            return "C"
        return "D" if any(BOX_DRAWING.search(t) for t in visible) else "Q"

    # ---- the views ----

    def prose_view(self, spans_visible=False):
        """The prose view of checking.md [sweeps]: fences dropped, links resolved to their text,
        code spans, double-quoted text, file.c:LINE citations and N:M pairs masked, headings tagged
        [H], catalog bullets, the entry bullets of section six and table cells tagged [C]; any other
        list item outside the catalog sections is swept as prose. Every row carries its page line,
        its tag, its masked text, its region and whether it lies in a catalog section."""
        rows = []
        fence = cat = False
        for n, line in enumerate(self.lines[:self.counted_lines()], 1):
            if line.startswith("```"):
                fence = not fence
                continue
            if fence:
                continue
            if line.startswith("## "):
                cat = line.strip()[3:].strip() in CATALOG_SECTIONS
                continue
            if line.startswith("#"):
                rows.append(ViewRow(n, "[H] ", line.lstrip("#").strip(), "heading", cat))
                continue
            if line.startswith(">"):
                continue
            six = self.section_of(n).region == "section6"
            tag = "[C] " if cat or line.startswith("|") or (six and ITEM.match(line)) else ""
            text = LINK.sub(r"\1", line)
            if not spans_visible:
                text = CODE_SPAN.sub("§", text)
            text = QUOTATION.sub("§", text)
            text = VIEW_LOCATION.sub("§", text)
            text = VIEW_COLON.sub("§", text)
            region = self.region_of(n)
            if region == "blank":
                region = "catalog" if cat else self.section_of(n).region
            rows.append(ViewRow(n, tag, text, region, cat))
        return rows

    @staticmethod
    def printed(row):
        """A view row as the snippet in checking.md prints it."""
        return f"{row.line}:{row.tag}{row.text}"

    def raw_view(self):
        """The raw file with every fence dropped and headings kept: (line, text) rows."""
        rows = []
        fence = False
        for n, line in enumerate(self.lines[:self.counted_lines()], 1):
            if line.startswith("```"):
                fence = not fence
                continue
            if fence:
                continue
            rows.append((n, line))
        return rows

    def counted_lines(self):
        """The page's line count as wc -l counts it."""
        if self.lines and self.lines[-1] == "":
            return len(self.lines) - 1
        return len(self.lines)
