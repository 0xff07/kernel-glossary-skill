# Pass 03: check

Purpose: confirm, independently and mechanically, that the writer's own checks were run and held. This pass re-runs the writer's procedures against ground truth and compares the answers; it does not redo the writer's work and does not read the page for style. Its reach into prose content is bounded to what ROUTINE-04's generators print.
Inputs: the finished page (state WRITTEN); its dossier, whose EVIDENCE, LINKS, PARITY and LINT sections are the claims this pass tests; the kernel tree at the documented version.
Outputs: the page's residual findings adjudicated and applied, and the check's outcome appended to the dossier's LINT section. Page state after this pass: LINTED, the terminal state.
Run by: the orchestrator, inline, with shell tools; never delegated. It costs on the order of ten thousand tokens.

Rules are cited by stable ID; `guidelines/rules/INDEX.md` maps every ID to its file.

The pass exists for the one thing a self-report cannot supply: evidence that the self-report is true. A writer that skipped its exit suite and reported "clean" is indistinguishable from one that ran it unless somebody re-runs it. (The fresh-eyes prose sweep this pipeline once ran was retired; `guidelines/LESSONS.md` records the measurement.)

## The check

Every step is a command whose answer is compared against the dossier's claim. A disagreement is a finding.

1. Sweep reproduction. Rebuild the prose view (ROUTINE-01) and re-run every BANS pattern. Every class the writer reported fixed must reproduce at zero; every hit that remains must match a candidate the writer recorded as exempt with its exemption. A class the writer reported clean that fires here means the writer did not run the sweep.
2. Figure sweep. Re-run ROUTINE-01's figure sweep over the non-C fences for the three bans that reach figures, and read each figure against DIAG-02's banned shapes.
3. Span closure. Re-run the same extractor the writer used (02-write.md, item 2) and diff its span set against the dossier's LINKS table; a discrepancy means the table was hand-edited or stale. Then judge: every `prose` row carries a non-empty `kind / reason` cell, and a sample of them is re-adjudicated (is a symbol row's disk line a definition, is a reason a real exemption). Do not take the writer's closure count on trust.
4. Excerpt and anchor spot-check. Byte-compare a sample of fenced units against the tree and print the disk line behind a sample of anchors; roughly ten each has been enough to catch a systematically wrong procedure.
5. Figure geometry. Column-verify junctions and confirm every line is under eighty columns (ROUTINE-07); the L-connector trunks of a register figure and the lanes of a swimlane meet their reference shapes and are cleared, not repaired.
6. Counts. Re-derive two or three load-bearing counts on a basis shaped differently from both bases the dossier records.
7. WRITING. Re-run ROUTINE-04's opener and member generators and compare with the dossier's lists; read every first sentence for rule 1 and a sample of excerpt paragraphs for rule 3; read the DETAILS headings for the spine; count SUMMARY's tables and figures. A count-led opener, an unexplained excerpt, a catalog-order spine or a SUMMARY carrying a member table is a finding.

## Findings

The orchestrator adjudicates every finding itself. A finding with an exactly specified fix (a byte-proved anchor, a BANS fix, a geometry repair, a rewritten first sentence) is applied by the orchestrator and re-verified with the command that found it; a fix set at volume is derived from an exhaustive grep of the construct, never from the sites a report happened to name. A factual finding is never fixed here: it goes back to the writer while its transcript lives, otherwise into the run log and to the user as repair material.

Record the outcome in the dossier's LINT section and the state change in the run log. A refuted spec claim is promoted into the campaign spec as a dated amendment; a durable lesson goes to `guidelines/LESSONS.md`; a settled boundary is surfaced to the user for `guidelines/rules/WAIVERS.md`.

## The standing hazard

Classes have shipped for pages at a time behind a pattern that structurally could not fire on the region it was meant to police, and a clean run of such a pattern reads exactly like success. When a rule binds a region, confirm some mechanism reaches that region.
