# Samples and measured criteria

Rule IDs (7, 7a-7r) resolve via `guidelines/rules/INDEX.md`; 7g-7i live under `guidelines/diagrams/`.

The sample pages were produced by this workflow and verified link-by-link and excerpt-by-excerpt against their kernel tree with zero findings. Their measured shape defines concretely what "in-depth, fine-grained" means for this knowledge base:

| sample | lines | c blocks | Elixir links | figures |
|---|---|---|---|---|
| `guidelines/samples/page-overview-mm-struct.md` | 2,940 | 98 | 861 | 1 |
| `guidelines/samples/page-lifecycle-mm-refcount.md` | 1,743 | 59 | 591 | 1 |
| `guidelines/samples/page-encoding-pgtable-entries.md` | 3,024 | 141 | 718 | 3 |
| `guidelines/samples/page-enhanced-vma-overview.md` | 2,922 | 107 | 634 | 1 |

Across the thirteen pages of the campaign that produced them, the per-page ranges were 1,468 to 3,270 lines, 46 to 141 code blocks, and 357 to 861 Elixir links. These numbers are outcomes, not targets: they fall out of the depth rules below when applied to a fine-grained topic. Three tripwires convert them into checks that work for any subsystem: a finished fine-grained page below the smallest sample page (1,468 lines); a page with fewer fenced ` ```c ` blocks than LINUX KERNEL catalog entries (conforming pages measure 1.03 to 1.47 blocks per entry, because every symbol needs a definition and a usage excerpt; a deficient derived page measured 0.73); and a catalog that shrank across a rewrite without reported cuts. Any tripped wire forces the Gate B parity audit (item 1; `guidelines/gates/gate-b.md`) and, for a derived page, the 7p disposition list before the page can be called done. The fix for a tripped page is completing coverage per 7j and Gate B, or cutting scope explicitly per 7p; it is never padding prose and never silent thinning. There is no length ceiling; a page ends when coverage is complete, not at a line count.

The depth rules that produce those numbers:

- Definition plus usage, per symbol. Every symbol in the LINUX KERNEL catalog gets both its definition excerpt and at least one real caller or usage excerpt in DETAILS (Gate B item 1). A page of definitions alone reads like a header file; the usage excerpt is what makes each symbol's role concrete.
- Full site enumeration with counts. When prose says a helper is used at N sites, N is a verified count (semcode `find_callers` plus grep, re-checked on disk) and the sites are enumerated with per-site file-location links (7m), or a representative spread is cited with the total stated.
- Every hard-coded limit named with its value and its defining file and line (7j).
- Lifecycle and state transitions in full: allocation, initialization, teardown order, the serializing locks, reference counting, and every state a tracked field moves through with the transition drivers cited (7j).
