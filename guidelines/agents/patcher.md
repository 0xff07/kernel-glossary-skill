# Patch agent

Role: applies the adjudicated stylistic fix list to one finished page — the style-lint findings the orchestrator confirmed (prose rewordings per the 7q recipes, banned-word replacements, span-form fixes with their briefed link targets), each item stated exactly in the brief. It performs no research, makes no judgment calls, and touches nothing the brief does not name. Hard boundary: the patcher never fixes substance — no excerpt additions or extensions, no coverage or parity closure, no fact, count, or claim edits, no anchor re-derivation. A substantive defect discovered at any stage is the writer's to fix (resume the writer; `guidelines/campaign/pipeline.md`), never the patcher's. An item that turns out to need a decision is returned in the report, never improvised.
Model tier: the style-lint tier (a cheaper model); the work is applying already-adjudicated rewordings.
Mandatory reading: carried inside the brief below, as absolute paths.
Report: a short final message listing, per briefed item, what was applied or why it was returned unapplied.
Death/resume: re-dispatch fresh from the same brief; the agent holds no state worth resuming.

## Patch brief template

Fill the brackets. The fix list is the orchestrator-reviewed output of the style-lint pass; the brief is the complete scope.

```
Apply the stylistic fix list below to <page path>.

SKILL_DIR: <absolute path to the kernel-glossary-skill checkout>

MANDATORY READING, in order, before touching the page:
1. <SKILL_DIR>/guidelines/rules/7r-adjudications.md — never reword an
   exempt construct beyond what the fix list states.
2. <SKILL_DIR>/guidelines/rules/7q-rephrase-recipes.md and
   <SKILL_DIR>/guidelines/rules/7m-linking.md — the rewording recipes and
   the link form for any span-form fix.
3. The page itself, in full, before the first edit.

FIX LIST. <One numbered item per confirmed finding: the current text
(exact), the replacement (exact, or the 7q recipe to apply), and its
location by section heading. Span-form fixes name the exact link target
URL. Nothing else is in scope.>

CONSTRAINTS.
- Apply each item exactly as briefed; preserve all surrounding text,
  links, excerpts, and figures byte-for-byte.
- Never add, extend, or modify a fenced excerpt; never change a fact, a
  count, a claim, or a link anchor the fix list does not name. Substance
  is out of scope by role; if an item would require it, return the item.
- If an item cannot be applied exactly as briefed (the current text is
  not found, the placement is ambiguous, the fix needs a decision), skip
  it and return it in your report with what you found; never improvise.
- Re-run the Gate A candidate greps over the paragraphs you touched
  (fence-aware) to confirm your edits introduced no new candidates.
- Anything you persist goes under <SKILL_DIR>/progress/<campaign>/ with a
  unique <slug>.-prefixed name; write nowhere else in progress/, which
  belongs to other runs too.

REPORT. Per item: applied (with the resulting sentence) or returned
(reason). Confirm the touched paragraphs re-grep clean and that no
fenced block changed.
```
