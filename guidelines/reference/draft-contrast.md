# Draft-versus-page contrast

Rule IDs (7, 7a-7r) resolve via `guidelines/rules/INDEX.md`; 7g-7i live under `guidelines/diagrams/`.

`guidelines/samples/draft-original-vma-overview.md` is an earlier-generation draft of the same topic as `guidelines/samples/page-enhanced-vma-overview.md`; the sample page was rebuilt from it. The pair is kept in `guidelines/samples/` so the gap between a plausible draft and a page meeting this standard stays concrete and measurable:

| measure | draft | page |
|---|---|---|
| lines | 1,161 | 2,922 |
| fenced c blocks | 43 | 107 |
| provenance comments | 43 (one per block; single-excerpt blocks only) | 127 (stitched blocks with interior 7l delimiters) |
| Elixir links | 409 | 634 |
| mechanical checks | 1 non-verbatim code block, 1 Gate A hit | zero findings |

The differences that matter are not the raw sizes but what produced them:

- Verification versus plausibility. The draft states facts that read correctly and are wrong at the tree. It claims the VMA's `vm_mm` back-pointer "is set once, at allocation, and never changes"; the sample page shows the second writer (the fork path, where `vm_area_init_from()` copies the parent's pointer and `dup_mmap()` then redirects the clone at the child address space) with both excerpts inline. It claims the anonymous-VMA `vm_pgoff` "holds the starting PFN of the range"; the sample page reproduces the on-disk code showing `vma->vm_pgoff = vma->vm_start >> PAGE_SHIFT` (a virtual page index) together with the kernel's own comment. It claims `vma_set_range()` has "seven call sites in mm/vma.c" and that "every path that resizes a VMA goes through it"; the sample page enumerates all seven sites with location links (six in `mm/vma.c` plus one in `mm/mmap.c`) and shows the split path that adjusts the fields directly. Every draft claim was re-verified symbol by symbol before it survived into the sample page.
- Definition-plus-usage depth. The draft's `vm_lock_seq` section is one paragraph (4 lines); the sample page's runs 88 lines with the field definition, the writer-side stamping code, and the reader-side comparison code. Section for section, the sample page carries the caller excerpt the draft only alludes to.
- Enumeration with location links. The draft asserts counts in prose; the sample page links each site individually, so every count is checkable one click deep.
- Source-of-truth links in OTHER SOURCES. The draft hand-built `git.kernel.org/.../commit/?id=` URLs; the sample page carries byte-exact `Link:` trailer URLs from `git log` (7n).
- Mechanical cleanliness. The draft fails the checks (one stitched excerpt does not match the tree verbatim; one label-colon idiom in prose); the sample page has zero findings.
- Coverage. The sample page adds whole sections absent from the draft (the per-VMA lock state catalog, the lifecycle-driver catalog, the mapping-path orchestration walk, the newer preparation-descriptor struct) because the coverage rules in 7j demanded them.

When drafts of any prior generation exist for a topic (next section), this contrast is the acceptance test: reusing a draft is legitimate only when the result is indistinguishable from a fresh page written to this standard.

The audit does not stop at a sample. A later enhancement pass over this same sample page corrected an off-by-one call-site count (a written 119 for the 118 on disk) and a provenance comment two lines off its excerpt, and a 7o audit after that found a false universal claim both passes had missed: the page asserted a helper "is invoked from exactly one place" while the tree holds four callers (the plain store helper, its gfp variant, the fork-path bulk store, and an error-path rollback). Sample pages calibrate form and depth; correctness is established only by re-running the 7o actions against the tree, on every page, however clean its history.
