# Pass 03 (application channel): the fix-list fixer

Rules are cited by stable ID; `guidelines/rules/INDEX.md` maps every ID to its file.

The full fresh-eyes lint sweep is RETIRED. The writer now runs the mechanical sweeps (ROUTINE-01; was Gate A) on its own
prose (`guidelines/passes/02-write.md`, exit-suite items 6-8), and the orchestrator re-runs them
mechanically in the check pass (`guidelines/passes/03-check.md`). The reasoning is recorded in
03-check.md and is not repeated here.

What survives is this: a fixer in FIX-LIST MODE, the application channel for findings the
orchestrator has ALREADY adjudicated. Use it when a check turns up volume, or repeated work that
would otherwise be applied by hand. It sweeps nothing, derives nothing, and decides nothing.

Model tier: a cheap model. The work is exact substitution against an explicit list.

Two rules govern the list itself, both learned the hard way:

- Derive it from an EXHAUSTIVE grep of the offending construct, never from the sites a report
  happened to name. A fix list built from a lint report once named one occurrence of a construct
  and missed an identical one two hundred lines earlier; the fixer applied exactly what it was
  briefed and correctly refused to improvise.
- Never put a factual finding on it. Facts belong to the writer, and a fixer that edits a fact is
  outside its lane.

## Brief

```
Lint-fix the finished page <path>.
[FIX-LIST MODE: apply the reviewed fix list below to <path>; skip the
sweeps entirely; every constraint still applies.]

SKILL_DIR: <absolute path to the kernel-glossary-skill checkout>

MANDATORY READING, in order, before touching the page:
1. <SKILL_DIR>/guidelines/rules/7r-adjudications.md — first action. Judge
   every candidate against it BEFORE fixing or proposing; a hit on an
   exempt construct is a false candidate, and rewording a compliant
   phrase to silence a pattern is itself a defect.
2. The rule corpus under <SKILL_DIR>/guidelines/rules/ — one rule per
   file; INDEX.md maps every ID. This pass exercises the prose rules
   (BAN-01, BAN-02, BAN-03, BAN-04, BAN-06, BAN-07, and PAGE-01),
   PAGE-04's span form, the ROUTINE-05 fix recipes, ROUTINE-04's
   candidate patterns, and ROUTINE-01's link-target and excerpt
   procedures (the preconditions for span-link and line-drift fixes).
3. The frozen samples for catalog-form questions:
   <SKILL_DIR>/guidelines/reference/samples/page-encoding-pgtable-entries.md and
   <SKILL_DIR>/guidelines/reference/samples/page-overview-mm-struct.md — the LINUX
   KERNEL bullet display form they use is the house convention, not
   corruption (form only, never facts).

FACTS. Documented tree: <path>, version <tag>, commit <sha> (the disk is
ground truth for every byte-match precondition).
PROJECT-SPECIFIC BANS carried from the campaign spec: <list, or "none">.
[FIX LIST. <One numbered item per reviewed finding: the current text
(exact), the replacement (exact, or the ROUTINE-05 recipe to apply), and its
location by section heading. Span-form fixes name the exact link target
URL. Nothing else is in scope.>]

CONSTRAINTS.
- Fix ONLY the listed items, exactly as briefed; escalate everything
  unsettled. Never fix
  facts: no excerpt additions or extensions, no coverage or parity
  closure, no fact, count, or claim edits. Fenced blocks stay
  byte-for-byte except the provenance line of a byte-proved drift fix.
- An item that cannot be applied exactly as briefed (text not found,
  ambiguous placement, needs a decision) is returned in the report with
  what you found; never improvise.
- Re-run the ROUTINE-04 candidate greps over the paragraphs you touched
  (fence-aware) to confirm no new candidates.
- Anything you persist goes under <SKILL_DIR>/progress/<campaign>/ with a
  unique <slug>.-prefixed name; write nowhere else in progress/, which
  belongs to other runs too.

REPORT. Write the dossier's LINT section and summarize it as your
final message: FIXED by class with counts and before/after, ESCALATED
with proposed fixes, EXEMPT with the 7r ruling count applied, SUBSTANCE
NOTES, and confirmation that touched paragraphs re-grep clean and no
fenced block changed (beyond declared drift fixes).
```
