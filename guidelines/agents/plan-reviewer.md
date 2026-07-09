# Plan-review agent

Role: adversarial review of a finished campaign catalog before the user checkpoint (`guidelines/campaign/planning.md`, step 6). A fresh agent that took no part in writing the plan attacks it: coverage gaps, duplicated ownership, wrong granularity, ordering defects, anchor errors. A catalog nobody attacked ships its blind spots.
Model tier: strong; this is judgment work over the whole catalog.
Mandatory reading: the plan file under review (path carried in the brief); spot checks run against the documented tree. The writing rules are not needed, because the target is the catalog, not the prose.
Report: a numbered amendment list (merge / split / rescope / reorder / fold-in), each naming the affected rows; the reviewer never rewrites the plan itself. The orchestrator applies the amendments it accepts and records the outcome in the plan file.
Death/resume: resume the same agent and ask for the amendments found so far; spawn a fresh agent only after resuming fails twice.

## Plan review brief template

Dispatch after the catalog and boundary rules exist, to a fresh agent that took no part in writing them.

```
Adversarially review this documentation-campaign plan for <subsystem
area>. You are attacking the catalog, not the prose. Input: the plan file
at <path> (context, inventory digests, catalog, boundary rules, batch
order). Tree for spot checks: <path>, version <tag>.

Hunt for, and propose concrete fixes with one-line justifications:
1. Coverage gaps: topics present in the inventory digests or the user
   request but absent from both the catalog and the fold-in list.
2. Duplicated ownership: sibling pages whose scope statements would force
   the same walkthrough twice; propose the boundary statement and seam
   symbol, or a merge.
3. Wrong granularity: rows whose scope exceeds one page's material
   (propose the split line) and rows too thin to stand alone (propose the
   merge target).
4. Ordering defects: pages batched before the pages that explain their
   prerequisites.
5. Anchor errors: scope-statement symbols that do not exist at the
   documented version (spot-check against the tree).

Return a numbered amendment list (merge / split / rescope / reorder /
fold-in), each naming the affected rows. Do not rewrite the plan yourself.
```
