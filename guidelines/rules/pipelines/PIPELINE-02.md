# PIPELINE-02: The one-pass pipeline

> Companion to PIPELINE-01: where PIPELINE-01 is the checking walkthrough (and re-runs its mechanical steps after any edit), PIPELINE-02 is the build-and-fix order. It visits every rule exactly once, and it is scheduled so that every stage's fixes land only on surface that later stages check, never on a guarantee already issued. A page built or repaired in this order needs no stage revisited because of the pipeline's own fixes. ROUTINE-01's independence contract is untouched: the checker still re-verifies the finished page; re-verification of an unchanged page is not a re-run forced by a fix.

## The one-pass contract

1. **Creators before constrainers.** A rule whose fixes create or move content (sections, blocks, figures, tables) runs before every rule that constrains wording or verifies items: new content is raw material for later stages and poison for earlier ones.
2. **Fixes are born compliant, built from verified material.** A stage's fix may only produce text that already satisfies every earlier stage. The recipes make this possible: a hedge fix lifts its exact condition from the already-byte-verified adjacent excerpt; a superlative fix names the mechanic already shown in the adjacent block; a claim restatement keeps exact constants in a plain declarative. Locally applying an earlier rule's recipe while writing new text is not a re-run of that rule.
3. **Guarantees are per item.** Deleting an item, or adding a sibling, never invalidates the records issued for other items; only an in-place rewrite of an already-checked item could, and clause 2 forbids producing a non-compliant one.

Three cross-stage constraints the recipes must honor:

1. The figure roster is frozen at Step 2; no later stage adds a figure.
2. A Step 12 redraw stays within the pattern and style named at Steps 10-11; the escape hatch is deletion to prose, which is per-item safe.
3. Figure-annotation rewording at Step 15 preserves the geometry verified at Step 13 (line width and junction alignment).

## Step 1: PLOT-04 (settle the content set)

1. Derived pages only; a fresh page records "not derived" and moves on.
2. Run PLOT-04's criteria: the inventory, a disposition for every item, cuts reported with catalog and scope shrunk together.
3. Fixes may: restore or draft whole sections, in the raw.
4. Nothing precedes this stage, so nothing can be disturbed.

## Step 2: FACT-01 (complete the coverage; freeze the figure roster)

1. Run FACT-01's criteria: enumerate and record every behavior's sites; add the missing structs, helpers, lifecycle and asynchronous coverage, and hard-coded limits.
2. Decide here which relationships earn figures (the justification test consumed as a design input); the roster is frozen from this point.
3. Fixes may: create any content, since everything after this stage checks it.
4. Step 1 survives because additions realize its dispositions.

## Step 3: FACT-02 (driver examples)

1. Run FACT-02's criteria: recency evidence per driver, each described from its own source.
2. Fixes may: replace a stale driver's example content wholesale.
3. Earlier stages survive because substitution is content the later stages have not yet checked.

## Step 4: PAGE-05 (OTHER SOURCES)

1. Run PAGE-05's criteria: every entry traced byte-exactly to its Link: trailer or dig output, including entries the commits added at Step 2 now warrant.
2. Fixes may: add, replace, or drop entries in the one section nothing earlier reads.

## Step 5: PLOT-01 (the model)

1. Run PLOT-01's criteria: the model stated in the lead and SUMMARY before DETAILS, spec-mapped or a disclosed synthesis naming its materials; sources recorded.
2. Fixes may: write model prose and SPECIFICATIONS entries; every claim in them is verified at Step 20, every span linked at Step 22.

## Step 6: PLOT-02 (semantics tables)

1. Run PLOT-02's criteria against the Step 5 model: one member-meaning-construct table per fixed set, transitions shown, taxonomies with their axis named.
2. Fixes may: convert bare lists into tables and add transition tables; a transition figure joins the frozen roster's drawing queue.

## Step 7: PLOT-03 (the spine)

1. All content now exists, so re-homing happens exactly once. Run PLOT-03's criteria: DETAILS organized as a journey or model, every cataloged symbol inside its phase or facet, headings drafted as declarative claims.
2. Fixes may: move sections and rewrite headings; moves change no sentence, and the new headings are verified as claims at Step 20.

## Step 8: PAGE-02 (definition and usage blocks)

1. Run PAGE-02's criteria: the parity table with a definition and a usage block per catalog symbol, both directions, the shown-versus-enumerated split, the sufficiency test.
2. Fixes may: add fenced C blocks inside the settled sections; fences are invisible to every guarantee issued so far.

## Step 9: PAGE-03 (provenance and byte-verification)

1. Run PAGE-03's criteria: the provenance line on every block, every unit byte-compared at its cited line.
2. Fixes may: touch only fence-internal first lines and cited line numbers; nothing outside a fence changes.

## Step 10: DIAG-04 (pattern figures)

1. Draw and verify the non-bit-layout figures from the frozen roster, each per a named catalog pattern, with the four banned shapes applied as design constraints while drawing.
2. Fixes may: create figure fences and their annotations; annotations are swept at Steps 14-19.

## Step 11: DIAG-03 (bit-layout figures)

1. Draw and verify the bit-layout figures (a disjoint set from Step 10): style by the register-versus-structure test, geometry, legend, scale choice; queue every bit range, constant, and macro for Step 20's claim audit.
2. Fixes may: create figure fences and annotations, as at Step 10.

## Step 12: DIAG-02 (the strip test)

1. Run DIAG-02's criteria on every drawn figure: strip the labels, record what the skeleton asserts, confirm none of the four banned shapes.
2. Fixes may: delete a failed figure with its content folded into surrounding prose (per-item safe; the folded prose is still ahead of the sweeps), or redraw within the Step 10/11 pattern (constraint 2).

## Step 13: DIAG-01 (per-figure final)

1. Run DIAG-01's criteria: justification confirmed against the Step 2 roster (no additions here, per constraint 1), geometry, sub-diagram titles, and the prose paragraph above every opening fence.
2. Fixes may: adjust figure geometry and add those paragraphs; the paragraphs precede the sweeps.

## Step 14: BAN-03 (fold the lists)

1. Run BAN-03's criteria: every exposition list in DETAILS, SUMMARY, and the lead folded into flowing prose.
2. This is the one ban whose fix writes new sentences, so it runs before the other sweeps see them.

## Step 15: BAN-01 (core bans)

1. Run BAN-01's criteria over prose, headings, and figure annotations.
2. Fixes may: reword sentences and annotations per the recipes; annotation rewording preserves Step 13's geometry (constraint 3).

## Step 16: BAN-02 (label-colons)

1. Run BAN-02's criteria over the prose view; fix per the recipes.

## Step 17: BAN-04 (superlatives)

1. Run BAN-04's criteria; each fix names the mechanic already shown in the adjacent verified block (clause 2), so it introduces no unverifiable claim.

## Step 18: BAN-06 (banned words)

1. Run BAN-06's criteria; fixes swap tokens for the concrete rule, count, helper, or branch word.

## Step 19: BAN-07 (hedges)

1. Run BAN-07's criteria; each fix lifts the exact condition from the adjacent verified excerpt (clause 2).
2. The recipes' target forms satisfy all five bans at once, so Steps 15-19 cannot disturb one another; their new wording is claim-audited at Step 20 and span-linked at Step 22.

## Step 20: FACT-03 (the claim audit)

1. Wording is now final. Run FACT-03's criteria in full: every quantifier, count, per-member claim, restated guard, and invariant re-derived and recorded, lead and SUMMARY included; every heading (Step 7's included) true of its section; prose against its adjacent excerpts; the Step 11 bit claims; every provenance line number from Step 9 confirmed.
2. Fixes may: weaken or restate claims as plain declaratives with exact constants, born compliant with Steps 14-19; a new search-basis sentence is drafted the same way.

## Step 21: PAGE-01 (the skeleton)

1. Run PAGE-01's criteria: topic-name H1, the caution blockquote diffed byte-for-byte, Documentation references placed, one unwrapped line per paragraph, tab indentation, OTHER SOURCES entry format, walkthrough presence evidenced by Step 8's parity table.
2. Fixes may: join lines, move entries, and fix formats; layout edits add no words, so no sweep or audit result changes.

## Step 22: PAGE-04 (exhaustive linking)

1. The terminal node, because its fixes have zero footprint: link syntax is invisible to the prose view, touches no fence, and changes no geometry.
2. Run PAGE-04's criteria on the final text: one Elixir version, every span linked exactly once (the spans Steps 15-20 legitimately introduced included), symbol links on definition lines, location links per enumerated site, every anchor opened and confirmed.

## Every rule exactly once

| stage | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rule | PLOT-04 | FACT-01 | FACT-02 | PAGE-05 | PLOT-01 | PLOT-02 | PLOT-03 | PAGE-02 | PAGE-03 | DIAG-04 | DIAG-03 | DIAG-02 | DIAG-01 | BAN-03 | BAN-01 | BAN-02 | BAN-04 | BAN-06 | BAN-07 | FACT-03 | PAGE-01 | PAGE-04 |

## The limit

The pipeline is re-run-free under the contract, and the contract's weak point is discovery, not fixing: a missing call site surfacing in Step 20's counterexample search is a Step 2 coverage failure arriving late, and no ordering rescues a pass whose early stage did wrong work. What the ordering eliminates is the churn PIPELINE-01 tolerates by design: every pipeline fix lands on not-yet-checked surface, so the re-run-after-every-edit trigger remains necessary only for hand-edits made outside this order.
