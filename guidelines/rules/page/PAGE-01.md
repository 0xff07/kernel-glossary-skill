# PAGE-01: General page rules

> Was: 7f. General page rules

**INPUT:** The whole raw page: the H1, the caution blockquote and its template, section placement, paragraph line structure, every inline code span outside fences, the indentation of cited code, and the OTHER SOURCES entries.

**OUTPUT:** A page with the mandated skeleton: topic-name H1, byte-exact caution blockquote, Documentation references in KERNEL DOCUMENTATION, one unwrapped line per paragraph, every kernel-symbol span an Elixir link with the struct/enum keyword kept, zero internal cross-links, tab-preserved excerpts, link-formatted OTHER SOURCES, and DETAILS carrying code walkthroughs; delivered with the bare-span fix record at zero remaining.

Page-shape requirements that apply to every page regardless of subsystem.

**Rule:** H1 is always the topic name only. Immediately below the H1, before the summary paragraph, every generated page carries this exact AI-generated-content caution blockquote, reproduced verbatim (including the repeated final line):

```
> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.
```

**Rule:** `Documentation/` references go in KERNEL DOCUMENTATION, never in OTHER SOURCES. When an existing page has `Documentation/` links in OTHER SOURCES (or `docs.kernel.org` / `kernel.org/doc` URLs), move them to KERNEL DOCUMENTATION; do not convert the existing URLs, add a new Elixir cross referencer reference entry pointing to the same in-tree kernel doc file.

**Rule:** No hard line wrapping in prose. Each paragraph is a single long line, with line breaks only between paragraphs, at no column width. Code blocks (between ` ``` ` markers), ASCII diagrams (indented lines), list items, and table rows are exempt.

**Rule:** Every mention of a kernel symbol (function, macro, struct, enum, typedef) is an Elixir cross referencer link. No exceptions. This covers every inline code span (`` ` `` ... `` ` ``) in every section — SUMMARY, LINUX KERNEL, INTERFACES, DETAILS, and prose paragraphs — including inline code with arguments such as `` `func(arg1, arg2)` `` in INTERFACES sections.

- Write [`function_name()`](https://elixir.bootlin.com/linux/v7.0/source/path/to/file.c#L123) instead of bare `function_name()`.
- Write [`func(arg1, arg2)`](https://elixir.bootlin.com/linux/v7.0/source/path/to/file.c#L123) instead of bare `func(arg1, arg2)`.
- Write [`struct foo`](https://elixir.bootlin.com/linux/v7.0/source/path/to/file.h#L45) instead of bare `struct foo`.
- Write [`MACRO_NAME`](https://elixir.bootlin.com/linux/v7.0/source/path/to/file.h#L78) instead of bare `MACRO_NAME`.

The only place bare symbol names are acceptable is inside fenced code blocks (` ``` `) that show code snippets or struct definitions. A symbol appearing several times on the same page is linked at every occurrence outside code blocks (repeat the link). A symbol whose file and line cannot be determined is looked up before it is written; a name that truly is not in the kernel source (a spec-defined ACPI method like `_PS0`, a hardware register like `SLP_EN`) may stay unlinked with a comment noting it is a spec/hardware name.

**Rule:** A struct or enum type always carries its `struct` or `enum` keyword (`struct acpi_gpe_event_info`, `enum ec_command`) unless the type is a typedef. This applies everywhere: LINUX KERNEL entries, SUMMARY, INTERFACES, DETAILS, and inline prose. In the LINUX KERNEL `'\<...\>'` entry format the keyword goes inside the angle brackets: `'\<struct acpi_gpe_register_info\>'`, `'\<enum ec_command\>'`.

**Rule:** No internal cross-links. Do not link to other pages in the knowledge base (`[Page Title](other-page.md)`); each page is self-contained.

**Rule:** Kernel source cited in Markdown code blocks keeps the exact indentation of the kernel source: tabs (8-space width), never converted to spaces — function bodies, switch/case statements, and multi-line expressions alike.

**Rule:** Every OTHER SOURCES entry uses the markdown link format `[Title](URL)`; no bare URLs, no `Title — URL` style.

**Rule:** The DETAILS section includes detailed kernel code walkthroughs: step-by-step traces through function call chains, real driver API usage examples, and lifecycle coverage for key objects. Every function/struct/enum in the LINUX KERNEL section gets at least one concrete driver usage shown in DETAILS. Kernel code paths are cited as fenced ` ```c ` blocks, then explained — never described in prose alone.

**PASS CRITERIA:**

- The H1 is the topic name only, and the caution blockquote sits immediately below it, byte-identical to the template above, repeated final line included: diff it against the template, do not eyeball it.
- Zero `Documentation/` references (and zero `docs.kernel.org` / `kernel.org/doc` URLs) in OTHER SOURCES; each lives in KERNEL DOCUMENTATION as an Elixir reference entry.
- Every prose paragraph is a single unwrapped line; only fences, ASCII diagrams, list items, and table rows break lines. Check for mid-paragraph line breaks.
- Scan every inline code span outside fences and confirm every kernel-symbol mention (function, macro, struct, enum, typedef, argument forms included) is an Elixir link, repeats included; only a verified spec or hardware name stays bare, with a comment saying so. Record bare spans found and fixed; sign off at zero remaining.
- Every struct and enum keeps its `struct`/`enum` keyword everywhere, the `'\<...\>'` catalog form included.
- Zero internal cross-links: `](.*\.md)` on the raw file finds no non-URL `.md` target, and no page path or other non-symbol span carries any link target at all (a resolving source anchor on a page path passes every mechanical check and is caught only by reading).
- Cited code keeps tab indentation exactly; spot-compare at least one block against the source file.
- Every OTHER SOURCES entry is `[Title](URL)`; zero bare URLs or "Title, URL" forms.
- DETAILS carries the walkthroughs: every LINUX KERNEL symbol shows at least one concrete driver usage, cited as fenced C blocks and then explained, never prose alone.
