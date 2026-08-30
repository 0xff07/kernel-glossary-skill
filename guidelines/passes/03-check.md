# Pass 03: check

Purpose: confirm, independently and mechanically, that the writer's own checks were actually run and actually held. This pass does NOT redo the writer's work and does NOT read the page for style — it re-runs the writer's procedures against ground truth and compares the answers.
Inputs: the finished page (state WRITTEN); its dossier, whose EVIDENCE, LINKS, PARITY and sweep records (was the Gate A record) are the CLAIMS this pass tests; the kernel tree at the documented version, which is the only ground truth.
Outputs: the page's residual findings adjudicated and applied, and the check's outcome appended to the dossier's LINT section. Page state after this pass: LINTED.
Run by: **the orchestrator, inline, with shell tools.** It is not delegated. It costs on the order of ten thousand tokens, against the two hundred and ninety to four hundred and sixty thousand a full fresh-eyes sweep used to cost, because it runs procedures instead of reading prose.
Next: nothing, in-session. The page is LINTED and stays uncertified until a verify campaign (`guidelines/passes/04-verify.md`) runs it on a different tree, in a later session, or under a different model — which is where independent auditing actually belongs.

Rules are cited by stable ID; `guidelines/rules/INDEX.md` maps every ID to its file.

## Why this pass is not a second author

This pipeline used to hand a finished page to a fresh-context fixer that swept it for prose defects. That stage was retired, and the reasoning is worth keeping because it is easy to re-invent.

The premise was that a writer re-reading its own prose misses its own blind spots. **That premise is true — and irrelevant, because the checks are not a re-reading.** Measured on this corpus: a writer composed twenty label-colon violations, re-read its page twice, saw none of them, then ran the ROUTINE-01 prose view (was 3c) and fixed all twenty. A fresh fixer run afterwards found two items on a two-thousand-line page, against a five-to-fifty-five range on unswept pages, and reproduced every sweep class (was Gate A) at zero. Writer-blindness is a failure of PERCEPTION; the sweeps are PROCEDURE, and procedure survives self-application. The same asymmetry is why a writer's byte-comparison finds its own fabricated excerpts while a third re-reading never does.

So the writer sweeps its own prose now (`guidelines/passes/02-write.md`, exit-suite items 6 through 8), and what remains for this pass is the one thing a self-report cannot supply: **evidence that the self-report is true.** A writer that skipped its exit suite and reported "clean" is indistinguishable from one that ran it — unless somebody re-runs it. That is this pass, and it is the entire reason it exists.

## The check

Every step is a command whose answer is compared against the dossier's claim. A disagreement is a finding.

1. **Sweep reproduction (was Gate A).** Rebuild the prose view (ROUTINE-01) and re-run every candidate pattern (ROUTINE-04). Every class the writer reported fixed must reproduce at ZERO; every hit that remains must match a candidate the writer recorded as EXEMPT with its waiver ruling. A class the writer reported clean that fires here is a finding, and it means the writer did not run the sweep.
2. **Figure sweep.** Re-run ROUTINE-01's figure sweep over the non-` ```c ` fenced blocks. BAN-01 governs figure annotations and no prose-view pattern can see them; this class was invisible for the whole corpus until it was closed, and it immediately turned up a real defect in a page already signed off.
3. **Span closure.** RE-RUN THE SAME EXTRACTOR the writer used (`guidelines/passes/02-write.md`, exit-suite item 2) over the page, and diff its span set against the dossier's LINKS table. Because writer and checker derive the set from identical code, the diff cannot disagree on which spans exist — a discrepancy means the table was hand-edited or stale, which is itself a finding. Then the real check, which is judgment, not completeness: every `prose` row must carry a non-empty `kind / reason` cell, and you re-adjudicate a sample of them — is a `kind: symbol` row's disk line actually a definition, is a `reason` a real waiver or a bare span dressed up as one. A blank `prose` cell is an unlinked span or an unjudged anchor; `catalog` rows are out of closure scope for now. Do not take the writer's own closure count: two writers' self-closures reported zero while their tables were incomplete, which is the whole reason this pass re-derives from the script instead of trusting the prose.
4. **Excerpt and anchor spot-check.** Byte-compare a sample of fenced ` ```c ` units against the tree, and print the disk line behind a sample of anchors. The writer confirmed all of them; this establishes that it did. Sample sizes of roughly ten each have been sufficient to catch a systematically wrong procedure.
5. **Figure geometry.** Column-verify junction alignment and confirm the maximum width is under eighty. This is mechanical (extract the fence, measure the columns) and it has caught real defects that no pattern expresses: four leader lines landing two columns off their cells.
6. **Counts.** Re-derive two or three of the page's load-bearing counts on a basis shaped differently from BOTH bases the dossier's EVIDENCE section records. Every page so far has had a published number changed by a second basis; this is the cheapest audit of whether the writer's second basis was real.

## Findings

The orchestrator adjudicates every finding itself and never delegates it, because adjudication is where both writers and fixers have failed: writers rationalize their own prose, and fixers have over-exempted settled violations and over-escalated settled ones on the same page. Judge each finding against the waivers; a hit on an exempt construct is a false candidate, and rewording a compliant phrase to silence a pattern is itself a defect.

Applying a finding:

- A finding with an exactly-specified fix (a byte-proved anchor correction, a settled ROUTINE-05 recipe, a figure-geometry adjustment) is applied directly by the orchestrator and re-verified with the command that found it.
- Volume, or anything needing repeated judgement, goes to a fixer in FIX-LIST mode (`guidelines/passes/03-lint-fixlist.md`) — the fixer role survives only in this form: it applies an already-adjudicated list exactly as briefed, and never sweeps, never derives, and never extends. Derive the fix list from an EXHAUSTIVE grep of the offending construct, not from the sites a report happened to name; a fix list built from a report once missed an identical construct two hundred lines away, and the fixer correctly refused to improvise.
- A factual finding is never fixed here. It goes back to the writer, whose facts they are, while its transcript lives; otherwise it is recorded in the run log, surfaced to the user, and becomes repair-campaign catalog material.

Record the outcome in the dossier's LINT section and the page's state change in the run log (`progress/<campaign>/log.md`, WRITTEN → LINTED). If the check refuted a claim the campaign spec itself makes (a wrong anchor in a catalog row, a stale boundary), promote that correction into the spec as a dated amendment — the log does not travel.

## The standing hazard

Two classes have now shipped for pages at a time behind a pattern that structurally could not fire: the mid-paragraph label-colon behind a line-anchored grep, and the figure annotation behind a fence-stripping view. Both were clean runs of checks that could not reach the region they were meant to police.

So the check that matters most is the one this pass cannot script: **when a rule binds a region, confirm some mechanism actually reaches that region.** A clean run of a pattern that cannot fire is not evidence of anything, and it reads exactly like success.
