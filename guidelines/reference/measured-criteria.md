# Samples and measured criteria

Rules are cited by stable ID; `guidelines/rules/INDEX.md` maps every ID to its file.

The sample pages were produced by this workflow and verified link-by-link and excerpt-by-excerpt against their kernel tree with zero findings. Their measured shape is descriptive calibration for what "in-depth, fine-grained" turned out to measure as — context for a writer's expectations, never a criterion:

| sample | lines | c blocks | Elixir links | figures |
|---|---|---|---|---|
| `guidelines/reference/samples/page-overview-mm-struct.md` | 2,940 | 98 | 861 | 1 |
| `guidelines/reference/samples/page-lifecycle-mm-refcount.md` | 1,743 | 59 | 591 | 1 |
| `guidelines/reference/samples/page-encoding-pgtable-entries.md` | 3,024 | 141 | 718 | 3 |
| `guidelines/reference/samples/page-enhanced-vma-overview.md` | 2,922 | 107 | 634 | 1 |

Across the thirteen pages of the campaign that produced them, the per-page ranges were 1,468 to 3,270 lines, 46 to 141 code blocks, and 357 to 861 Elixir links. These numbers are outcomes, not targets, and no size number is a criterion in either direction: a page ends when coverage is complete, and a conforming page on a genuinely narrow mechanism can measure below every range above.

The criteria are coverage-shaped. Three tripwires convert the depth rules below into checks that work for any subsystem:

- Blocks per catalog entry below 1.0: fewer fenced ` ```c ` blocks than LINUX KERNEL catalog entries means unpaired symbols, because every symbol needs a definition and a usage excerpt (conforming pages measure 1.03 to 1.47 blocks per entry; a deficient derived page measured 0.73).
- Catalog coverage of scope (fill-or-descope): every anchor symbol in the page's catalog-row scope statement and every symbol recorded in the dossier's SYMBOLS section is either cataloged or explicitly de-scoped in the writer's report, with the reason. This is the wire the ratio cannot trip: a writer who catalogs twelve symbols on a topic whose scope holds forty scores a clean ratio on a thin page, and only the scope comparison catches it.
- A catalog that shrank across a rewrite without reported cuts (PLOT-04).

Any tripped wire forces the parity audit (PAGE-02; was Gate B item 1) and, for a derived page, the PLOT-04 disposition list before the page can be called done. The fix for a tripped page is completing coverage per FACT-01 and PAGE-02's criteria, or cutting scope explicitly per PLOT-04 and fill-or-descope; it is never padding prose and never silent thinning.

The depth rules that produce those numbers:

- Definition plus usage, per symbol. Every symbol in the LINUX KERNEL catalog gets both its definition excerpt and at least one real caller or usage excerpt in DETAILS (PAGE-02; was Gate B item 1). A page of definitions alone reads like a header file; the usage excerpt is what makes each symbol's role concrete.
- Full site enumeration with counts. When prose says a helper is used at N sites, N is a verified count (semcode `find_callers` plus grep, re-checked on disk) and the sites are enumerated with per-site file-location links (PAGE-04), or a representative spread is cited with the total stated.
- Every hard-coded limit named with its value and its defining file and line (FACT-01).
- Lifecycle and state transitions in full: allocation, initialization, teardown order, the serializing locks, reference counting, and every state a tracked field moves through with the transition drivers cited (FACT-01).
