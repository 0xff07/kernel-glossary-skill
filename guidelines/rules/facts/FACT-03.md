# FACT-03: Behavioral-claim verification

> Was: 7o. Behavioral-claim verification

**INPUT:** Every quantified, universal, per-member, restated-guard, and lifecycle-invariant claim on the page (lead and SUMMARY included), the excerpts adjacent to each, and the enumeration tooling to re-derive every count and mapping.

**OUTPUT:** Every claim re-verified against a recorded search or derivation, every heading true of its section, prose agreeing with its adjacent excerpts, and every provenance line number confirmed; delivered as the claim list with per-claim evidence.

**Problem:**

1. A page is a set of claims about kernel behavior, and the class of error that reads correctly, links correctly, and survives every mechanical check is the unverified claim.
2. Each claim class below has a named audit action: perform them while writing, and re-perform them when reviewing, enhancing, or reusing a page.

**Rule:**

1. Universal quantifiers are enumerations.
2. A sentence containing "only", "never", "always", "all", "every", "exactly N", "the single", or "once" asserts the size or uniformity of a set: enumerate that set first (semcode `find_callers` plus a tree-wide grep that includes headers), then cite every member with location links or weaken the sentence to what the enumeration shows.

**Rule:**

1. A per-member claim is as many claims as the family has members.
2. "Each X ..." / "every X ..." over a family ("each wrapper forwards to exactly one underlying primitive", "every callback runs under the lock", "each descriptor slot maps to one register") is verified by building the member-to-property mapping first; one exception falsifies the sentence.
3. When an exception exists, restate to what the mapping shows, restrict the family explicitly ("every read-side helper ..."), or name the classifier and what falls outside it ("one primary primitive, plus cursor-bookkeeping helpers") — an unstated classifier is how a strictly-false claim reads as true.

**Rule:**

1. Lead and SUMMARY compression gets no precision waiver.
2. Quantified, universal, and per-member claims there are audited exactly like DETAILS claims and must agree with the DETAILS evidence on the same page; cross-check every lead and SUMMARY quantifier against the page's own tables and enumerations at sign-off.
3. Compression may drop detail, never trade accuracy for sweep.

**Rule:**

1. Every enumeration states its search basis inline — directories searched, headers included or not, definition sites excluded, architecture and CONFIG filter: "a grep across mm/, fs/, kernel/, drivers/, arch/x86/, and include/ at this tree finds 118 call sites of ... outside their definitions".
2. A count without its basis cannot be re-verified and does not qualify; a count that holds only under the page's CONFIG assumptions (a caller compiled out without `CONFIG_MMU`) says so at the claim.
3. Counts are re-derived at every review, never trusted — a re-count on a live page corrected a written 119 to the 118 on disk.

**Rule:** A restated condition is derived, not paraphrased. Prose restating a guard or threshold ("requires map_count + 2 < sysctl_max_map_count - 3") is derived from the reproduced code by exact negation of its operator, keeps the exact constants, and shows the guard as a code block beside the sentence so the reader can repeat the derivation.

**Rule:**

1. Headings are claims.
2. A DETAILS heading must be true of everything in its section, and a heading edit is a claim edit; verify each heading against its section's excerpts after writing and after every rewording.

**Rule:**

1. Prose does not outrun its excerpt.
2. Read each behavioral sentence against the adjacent code line by line.
3. Semantics carried by a primitive's own name are behavior and are stated: an ordering suffix (`refcount_set_release()` orders the preceding field writes before the count becomes visible to an acquiring reader), a `_locked`/`_unlocked` variant, an RCU flavor, saturation semantics.
4. The one licensed exception is the disclosed domain-model synthesis — assembled from named on-disk materials with every fact under it still individually cited; it never licenses an undisclosed, unsourced, or guessed assertion.

**Rule:**

1. Invariant claims get a counterexample search.
2. Before asserting "set once and never changes", "always called under lock L", or "freed only through F", search explicitly: every assignment site, every lock-less caller, every free path.
3. Cite the kernel's own enforcement where it exists (`lockdep_assert_held()`, `VM_WARN_ON()`, a `const` qualifier) — an assertion line is stronger evidence than a grep that found nothing.
4. Provenance line numbers are claims too: content matching does not validate them; open the file and confirm the excerpt begins at the cited line.

**PASS CRITERIA:**

1. List every universal quantifier ("only", "never", "always", "all", "every", "exactly N", "the single", "once"), every count, every per-member "each/every X" claim, every restated guard or threshold, and every lifecycle invariant on the page, lead and SUMMARY included; compression earns no waiver there.
2. For each quantifier and count, re-run the enumeration and record the search performed and its result; confirm the count states its search basis inline (directories, headers, exclusions, CONFIG assumptions) and matches the re-derived number. Counts are never carried over from a previous pass on trust.
3. For each per-member claim, rebuild the member-to-property mapping and confirm every member, or confirm the sentence restricts the family or names its classifier and boundary; one unhandled exception falsifies the claim.
4. For each restated guard, re-derive it from the reproduced code by exact negation of its operator with the exact constants, and confirm the guard appears as a code block beside the sentence.
5. Confirm every DETAILS heading is true of everything in its section, re-checking after any rewording, and read every behavioral sentence against its adjacent excerpt line by line, including the semantics a primitive's own name carries (ordering suffixes, `_locked`/`_unlocked` variants, RCU flavor, saturation). The disclosed model synthesis is the only licensed exception and never covers an undisclosed or unsourced assertion.
6. For each invariant, run the counterexample search (every assignment site, every lock-less caller, every free path) and cite the kernel's own enforcement where it exists; confirm every provenance line number by opening the file at that line.
7. Sign off with the claim list and its per-claim evidence; zero claims may remain without a recorded re-verification.
