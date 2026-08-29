# SUITE-03: The walkthrough

> Companion to SUITE-01 (the protocol) and SUITE-02 (the wiring): the order in which an agent walks a page through every rule. Each step names the SUITE-02 wiring it exercises, and the appendices map the old gates (rules.md 3a/3b/3c) and every SUITE-02 section onto the steps, so the three pages stay isomorphic.

## Step 1: Load the harness and take your role

1. Read SUITE-01, SUITE-02, `../7r-adjudications.md`, and the PASS CRITERIA of every rule file under `../bans/`, `../page/`, `../facts/`, `../plots/`, and `../diagrams/`.
2. Know your role: the writer runs Steps 2 through 13 on its own work first; the checker later re-runs them independently and compares answers; the orchestrator adjudicates every residual and never delegates adjudication; a verify campaign re-runs everything later on a newer tree or model.
3. There is no checker script; the steps run by hand, and a check that cannot fail is not a check.
4. Work page by page; record evidence at every step (a count or a list, never "looks fine"); reading the page is not sufficient.
5. Material citing old rule IDs resolves through SUITE-02's Legacy ID map.

*Wiring: Legacy ID map; SUITE-01's ownership, independence, and no-checker-script protocol.*

## Step 2: Build the prose view

1. Run SUITE-01's view builder over the page.
2. Confirm the `[C]` tagging of catalog bullets, list items, and table cells: only the label-colon shape is exempt on `[C]` rows, and every other ban still binds there.
3. SPECIFICATIONS entries are list bullets in a mandated format; never reword them to silence a pattern.
4. Sweep nothing against the raw file except what Step 5 lists.

*Wiring: Sweep aggregation (the batched execution and prose view are SUITE-01's).*

## Step 3: Run the batched ban sweeps

1. One pass over the prose view executes the mechanical criteria of:
   1. BAN-01: negative constructions, the anthropomorphic lemma sets, em dashes, "vtable";
   2. BAN-02: the unanchored label-colon pattern;
   3. BAN-04: the words-to-watch list and the cleft frames;
   4. BAN-06: the banned words and the letter-delimited arm pattern;
   5. BAN-07: the hedge tokens.
2. Sweep case-insensitively and fence-aware; use case as evidence when judging.
3. Judge negative and anthropomorphic candidates by reading each in context, never by the grep alone.
4. SUITE-04's criteria audit this step itself: the sweep ran over the view, unanchored, and carried BAN-03's intro-sentence-plus-list shape and the colon-introduced list on the same pass.
5. SUITE-04's scan patterns are the grep-shaped tells of BAN-02 and BAN-04; the one-unwrapped-line paragraph shape that blinds anchored patterns is PAGE-01's no-hard-wrapping rule.

*Wiring: Sweep aggregation (all bullets).*

## Step 4: Adjudicate and fix

1. Judge every candidate from Steps 3, 5, and 6 against the owning rule's exemptions and `../7r-adjudications.md`.
2. Never reword an exempt construct to silence a pattern.
3. Fix each confirmed hit with the matching SUITE-05 recipe per SUITE-02's Fix routing table.
4. Confirm no fix introduced another banned shape: swapping a label-colon for "X matters because Y" trades a BAN-02 hit for a BAN-04 hit.
5. Every finding ends fixed or recorded as a registry adjudication with reasoning, never silenced.

*Wiring: Fix routing (the table and both bullets); Sweep aggregation (the adjudication bullet).*

## Step 5: Run the raw-file checks

1. BAN-01's raw-file greps: question headings, trailing-`?` headings, and `**` boldface (kerneldoc openers inside fences exempt).
2. PAGE-01's internal-link checks: no non-URL `.md` target, and no page path or other non-symbol span carrying any link target (the class only reading catches).
3. Read every DETAILS, SUMMARY, and body H3/H4 for BAN-01's bare-noun ban.

*Wiring: Sweep aggregation (the raw-file carve-out named in the rules' criteria).*

## Step 6: Sweep and judge the figures

1. Run SUITE-01's figure sweep (the awk over non-C fences).
2. Adjudicate the annotations: the phrase classes (BAN-02, BAN-04, and the SUITE-04/BAN-06/BAN-07 sweeps) are lifted inside a figure fence; BAN-01's bans still bind the text.
3. Per figure, in precedence order:
   1. DIAG-01's criteria: justification in both directions, geometry, and the prose paragraph above the opening fence;
   2. DIAG-02's criteria: strip-the-labels and the four banned shapes; DIAG-02 outranks the catalogs, with DIAG-04's retired input-grid and event-grid forms as the precedent; the exempt fences include the verbatim-quote blocks PAGE-02 mandates;
   3. DIAG-03's criteria for bit layouts, on top of DIAG-01's general rules; queue its bit ranges, constants, and macros for Step 10's claim audit;
   4. DIAG-04's criteria: the pattern chosen from the use-case index and named at sign-off.
4. Confirm the figure spine is the page's spine: PLOT-03's journey or model, shown whole by the primary figure.
5. Confirm reshaping operations carry DIAG-04's before/after or data-dependency figures.
6. Confirm call-order-only figures were rejected: DIAG-01 rejects the bare chain, DIAG-02 the rest.
7. Confirm material failing the strip test routed to a PLOT-02 Markdown table or into prose.
8. A catalog in visual form is banned twice over (PLOT-03 in words, DIAG-02 in shape); the offset-map pattern stays distinct from DIAG-03's bit layouts.

*Wiring: Figure governance and precedence (all bullets).*

## Step 7: Verify every link

1. Run PAGE-04's criteria:
   1. one Elixir version per page;
   2. extract every cited location and open each target line;
   3. symbol-text links land on definition lines; non-definition references are path:line location links, one per enumerated call site;
   4. the exhaustiveness classes (CONFIG_* options, generic primitives, field paths, ops members) are linked;
   5. the settled bare spans are cleared without rewording; in-family precedent never overrides.
2. Run PAGE-01's span scan: every kernel-symbol span outside fences linked, repeats included, struct/enum keyword kept everywhere.
3. PAGE-04 extends PAGE-01's every-symbol-linked rule.
4. Record bare spans found and fixed; sign off at zero.

*Wiring: Evidence chain (PAGE-04 extends PAGE-01).*

## Step 8: Verify every code block

1. Run PAGE-02's criteria:
   1. build the catalog-to-DETAILS parity table, one definition column and one usage column per catalog symbol;
   2. check the fewer-blocks-than-entries tripwire; pass only at zero empty cells;
   3. check the reverse direction: a symbol that carries its own DETAILS section belongs in the catalog;
   4. where the page names several distinct users of one symbol, each appears as an excerpt or a per-site location link, with the shown-versus-enumerated split stated;
   5. apply the sufficiency test to the main documented path.
2. Run PAGE-03's criteria:
   1. the provenance-comment form on every fenced C block;
   2. byte-compare every unit at its cited line, tabs included;
   3. content matching elsewhere under a wrong claimed line is a finding;
   4. a comparator that resynchronizes on mismatch is worse than none.
3. PAGE-02 establishes each block is real and located; PAGE-03 byte-compares it; PAGE-03's verbatim-between-delimiters requirement is PAGE-02's verbatimness rule on stitched blocks.
4. Record the block count with every block confirmed.

*Wiring: Evidence chain (the parity evidence; the PAGE-02/PAGE-03 division; verbatim-between-delimiters).*

## Step 9: Verify coverage, drivers, and sources

1. Run FACT-01's criteria:
   1. re-run and record every behavior enumeration;
   2. confirm structs and helpers, lifecycle and asynchronous behavior, and every hard-coded limit with its value and defining line;
   3. check done-ness against the catalog and scope statement; every cut is a reported scope decision governed by PLOT-04;
   4. FACT-01's breadth mandate ranks with the prose and citation rules (BAN-01 through BAN-07, PAGE-01, PAGE-02); its figure mandate was executed in Step 6.
2. Run FACT-02's criteria: recency evidence per cited driver, each described from its own source.
3. Run PAGE-05's criteria: every OTHER SOURCES entry traced byte-exactly to its Link: trailer or dig output.
4. When the page derives from existing material, run PLOT-04's criteria: the inventory, per-item dispositions, reported cuts, and the derived page's own parity audit, the same audit Step 8 ran.

*Wiring: Evidence chain (the breadth resolution); Model and organization (cuts governed by PLOT-04; PLOT-04's audit is PAGE-02's parity audit).*

## Step 10: Audit the claims

1. Run FACT-03's criteria in full:
   1. list every universal quantifier, count, per-member claim, restated guard, and lifecycle invariant, lead and SUMMARY included with no compression waiver;
   2. re-run each enumeration and derivation with the search recorded;
   3. rebuild the member-to-property mappings;
   4. confirm every heading is true of its section and every behavioral sentence agrees with its adjacent excerpt;
   5. run the counterexample searches;
   6. confirm every provenance line number (this executes on PAGE-03's provenance comments).
2. Include the bit ranges, constants, and macros queued from Step 6's DIAG-03 figures.
3. The one licensed exception to prose outrunning its excerpt is PLOT-01's disclosed synthesis, checked in Step 11.
4. Sign off with the claim list and per-claim evidence.

*Wiring: Evidence chain (FACT-03's provenance audit on PAGE-03); Model and organization (the licensed exception); Figure governance (DIAG-03 claims under FACT-03).*

## Step 11: Check the model and the organization

1. Run PLOT-01's criteria:
   1. the model stated in the lead and SUMMARY before DETAILS, spec-mapped or a disclosed synthesis naming its materials;
   2. the prose bans bind the synthesis in full: BAN-02's label-colon ban, BAN-04's superlative and importance bans, and the SUITE-04/BAN-06/BAN-07 classes;
   3. every fact under the synthesis keeps its own citation per PAGE-02's excerpt rules and PAGE-04's linking rules; anything unsupported is weakened or scoped per FACT-03;
   4. record the model's sources.
2. Run PLOT-02's criteria:
   1. every fixed state set or taxonomy as a member-meaning-construct table;
   2. the meaning column states what a member is in PLOT-01's model; the construct column links per PAGE-04;
   3. transitions shown; tables stay Markdown, with any transition figure already judged in Step 6.
3. Run PLOT-03's criteria:
   1. the DETAILS headings trace a journey or model (PLOT-01 and PLOT-03 are a pair);
   2. coverage preserved through reorganization, with Step 8's parity table as the evidence;
   3. sign off with the heading count and the spine.

*Wiring: Model and organization (all bullets).*

## Step 12: Check the page skeleton

1. Run PAGE-01's remaining criteria:
   1. the H1 is the topic name only;
   2. the caution blockquote diffed against the template byte for byte;
   3. Documentation references placed in KERNEL DOCUMENTATION;
   4. every prose paragraph one unwrapped line (the shape Step 3's unanchored patterns depend on);
   5. cited code keeps tab indentation;
   6. OTHER SOURCES entries in link format;
   7. the DETAILS walkthroughs present, evidenced by Step 8's parity table.

*Wiring: Sweep aggregation (the one-unwrapped-line dependency); Evidence chain (walkthroughs evidenced by parity).*

## Step 13: Close the regions

1. Enumerate the page's regions: prose, headings, figures, catalog bullets, table cells, fenced excerpts.
2. For every rule that binds a region, name the step and mechanism that reached it; a region no mechanism reached is unexamined and reads exactly like clean.
3. Confirm the read-throughs no pattern expresses were actually read: BAN-03's list shapes, BAN-04's superlatives in context, negative and anthropomorphic candidates in context, heading truth, the parity table, the coverage enumerations, figure geometry, and the whole claim audit.

*Wiring: SUITE-01's blind-spot doctrine; the read-through halves of Sweep aggregation and Figure governance.*

## Step 14: Sign off, hand off, and re-run

1. The page is final only at zero unadjudicated findings across every rule file.
2. Every finding is fixed or recorded in `../7r-adjudications.md` with reasoning, and the evidence for every criterion is on record.
3. After any subsequent edit, your own hand-edits included, re-run the mechanical steps.
4. Writer done: the independent checker re-runs Steps 2 through 13 and compares answers; the orchestrator adjudicates every residual itself.
5. A verify campaign repeats the walkthrough later, on a newer tree or under a different model.

*Wiring: SUITE-01's terminal condition, re-run trigger, and independence contract.*

## Appendix A: the old gates map onto the steps

| gate (rules.md) | step |
|---|---|
| 3a re-run after every edit (544) | 14 |
| 3a em-dashes, label-colon, superlatives, banned words, hedges, vtable, arm (546-553) | 3, 4 |
| 3a boldface, internal `.md` links, question headings (547, 554-555) | 5 |
| 3a fence-aware hand run, judge against exemptions and the registry, never reword (557) | 2, 4 |
| 3a case doctrine and the `\b` underscore trap (559-561) | 3 |
| 3a final at zero unadjudicated findings (563) | 14 |
| 3b evidence discipline and ownership/independence (567-571) | 1, 14 |
| 3b item 1 parity, reverse direction, shown-versus-enumerated (573-575) | 8 |
| 3b item 2 grounded code (577) | 8 |
| 3b item 3 every symbol linked, keyword kept (581) | 7 |
| 3b item 4 declarative headings, journey- or model-first (585) | 5, 11 |
| 3b item 5 negative constructions, anthropomorphic verbs, judged by reading (589) | 3, 13 |
| 3b item 6 coverage, model, semantics tables (593) | 9, 11 |
| 3b item 7 driver recency (597) | 9 |
| 3b item 8 figures (601-603) | 6 |
| 3b item 9 behavioral-claim audit (605) | 10 |
| 3c no-checker-script doctrine (611) | 1 |
| 3c link targets procedure (613-622) | 7 |
| 3c excerpt verbatimness procedure (624-632) | 8 |
| 3c prose view first, `[C]` rows, SPECIFICATIONS ruling (638-673) | 2 |
| 3c candidate patterns over the view (675-689) | 3 |
| 3c raw-file patterns: `.md` links, the stricter companion, headings, boldface (691-697) | 5 |
| 3c figure sweep (699-705) | 6 |
| 3c read-through list (707) | 13 |
| 3c blind spots: regions times rules (709-713) | 13 |
| 3c permissive-checker warning (715) | 1, 8 |

## Appendix B: SUITE-02 maps onto the steps

| SUITE-02 section | steps |
|---|---|
| Fix routing | 4 |
| Sweep aggregation | 2, 3, 5, 12 |
| Evidence chain: code, links, and provenance | 7, 8, 9, 10, 12 |
| Model and organization | 9, 10, 11 |
| Figure governance and precedence | 6, 10 |
| Legacy ID map | 1 |
