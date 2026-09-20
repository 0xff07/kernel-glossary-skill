# The plan-review brief

The plan-review brief, dispatched to a fresh strong agent after the catalog and boundaries exist; it returns amendments and never rewrites the plan:

```
Adversarially review this documentation-campaign plan for <subsystem
area>. You are attacking the catalog, not the prose. Input: the campaign spec
at <path> (context, inventory digests, catalog, boundary rules, batch
order). Tree for spot checks: <path>, version <tag>.

Hunt for, and propose concrete fixes with one-line justifications:
1. Coverage gaps: topics in the digests or the request absent from both
   the catalog and the fold-in list.
2. Duplicated ownership: sibling pages whose scope statements would force
   the same walkthrough twice; propose the boundary statement and seam
   symbol, or a merge.
3. Wrong granularity: rows whose scope exceeds one page (propose the split
   line) and rows too thin to stand alone (propose the merge target).
4. Ordering defects: pages batched before the pages that explain their
   prerequisites.
5. Anchor errors: scope-statement symbols that do not exist at the
   documented version.

Return a numbered amendment list (merge / split / rescope / reorder /
fold-in), each naming the affected rows. Do not rewrite the plan yourself.
```
