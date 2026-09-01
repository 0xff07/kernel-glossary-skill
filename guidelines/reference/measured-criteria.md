# Samples and measured criteria

Rules are cited by stable ID; `guidelines/rules/INDEX.md` maps every ID to its file.

The sample pages were produced by this workflow and verified link-by-link and excerpt-by-excerpt against their kernel tree with zero findings. Their measured shape is descriptive calibration for what "in-depth, fine-grained" turned out to measure as — context for a writer's expectations, never a criterion:

| sample | c blocks | Elixir links | figures |
|---|---|---|---|
| `guidelines/reference/samples/page-overview-mm-struct.md` | 98 | 861 | 1 |
| `guidelines/reference/samples/page-lifecycle-mm-refcount.md` | 59 | 591 | 1 |
| `guidelines/reference/samples/page-encoding-pgtable-entries.md` | 141 | 718 | 3 |
| `guidelines/reference/samples/page-enhanced-vma-overview.md` | 107 | 634 | 1 |

Across the thirteen pages of the campaign that produced them, the per-page ranges were 46 to 141 code blocks and 357 to 861 Elixir links. These numbers are outcomes, not targets, and no size number is a criterion in either direction: a page ends when coverage is complete, and a conforming page on a genuinely narrow mechanism can measure below every range above.

**A page's line count is not recorded here and is not a measure of anything.** It was withdrawn deliberately: it correlates with nothing a reader cares about, it moves with excerpt depth and figure count rather than with coverage, and quoting it invites a writer to aim at it. What a page owes is coverage of its scope, and the measures that speak to that are the ones above plus the excerpt criterion below. Report a page's length if it is useful for a run log; do not treat it as evidence about the page.

The criteria are coverage-shaped. Three tripwires convert the depth rules below into checks that work for any subsystem:

- Blocks per catalog entry below 1.0: fewer fenced ` ```c ` blocks than LINUX KERNEL catalog entries means unpaired symbols, because every symbol needs a definition and a usage excerpt (conforming pages measure 1.03 to 1.47 blocks per entry; a deficient derived page measured 0.73).
- Catalog coverage of scope (fill-or-descope): every anchor symbol in the page's catalog-row scope statement and every symbol recorded in the dossier's SYMBOLS section is either cataloged or explicitly de-scoped in the writer's report, with the reason. This is the wire the ratio cannot trip: a writer who catalogs twelve symbols on a topic whose scope holds forty scores a clean ratio on a thin page, and only the scope comparison catches it.
- A catalog that shrank across a rewrite without reported cuts (PLOT-04).

Any tripped wire forces the parity audit (PAGE-02; was Gate B item 1) and, for a derived page, the PLOT-04 disposition list before the page can be called done. The fix for a tripped page is completing coverage per FACT-01 and PAGE-02's criteria, or cutting scope explicitly per PLOT-04 and fill-or-descope; it is never padding prose and never silent thinning.

**An excerpt shows enough of the construct to carry the point the prose makes about it.** This is a
criterion rather than an outcome, because a byte-exact excerpt can still be useless: a fenced block
holding a function's signature and its opening brace proves the provenance line and teaches nothing.

Measured across the corpora at v7.0, an excerpt unit runs a median of 15 lines in `docs/acpi/`
(mean 19.5, 1,789 units) and 14 lines in the sound corpus (mean 17.2, 1,378 units in a 40-page
sample). Units of five lines or fewer are 14.1% and 11.8% of the total respectively. That residue is
real and legitimate: a one-line `#define`, a single struct field, a prototype in a header. It is not
a budget for truncating bodies.

The check is per unit, never per page. For every unit that opens a function, struct, enum, or union,
the block continues far enough to show the behavior the surrounding prose asserts; where that runs
long, cut from the middle with the house `...` elision marker rather than stopping at the brace. A
page whose five-line-or-fewer units run far above the corpus rate has usually truncated bodies
rather than cited many macros, and the two are told apart by reading the thin units, never by the
percentage alone. A page measured at 34.2% against a 14.1% corpus rate is how this criterion was
found.

The depth rules that produce those numbers:

- Definition plus usage, per symbol. Every symbol in the LINUX KERNEL catalog gets both its definition excerpt and at least one real caller or usage excerpt in DETAILS (PAGE-02; was Gate B item 1). A page of definitions alone reads like a header file; the usage excerpt is what makes each symbol's role concrete.
- Full site enumeration with counts. When prose says a helper is used at N sites, N is a verified count (semcode `find_callers` plus grep, re-checked on disk) and the sites are enumerated with per-site file-location links (PAGE-04), or a representative spread is cited with the total stated.
- Every hard-coded limit named with its value and its defining file and line (FACT-01).
- Lifecycle and state transitions in full: allocation, initialization, teardown order, the serializing locks, reference counting, and every state a tracked field moves through with the transition drivers cited (FACT-01).
