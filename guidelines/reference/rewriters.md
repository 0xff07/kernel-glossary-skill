# Rewriter skills

A rewriter is an EXTERNAL skill that governs prose style. This file is the registry: which
rewriters exist, which are switched on, and what each one governs. A writer reads the entries
that are ON and nothing else.

Rules are cited by stable ID; `guidelines/rules/INDEX.md` maps every ID to its file.

## Switchboard

| rewriter | sibling skill | default | governs |
|---|---|---|---|
| humanizer | `humanizer` | ON  | AI-writing patterns: inflated claims, filler, qualifier stacking, repeated openings, punctuation habits |
| asd-ste100 | `asd-ste100` | OFF | controlled-language shape: sentence length, active voice, one instruction per sentence, noun clusters |

A rewriter is ON only when this table says ON and its sibling skill is present. The switch is
whole-skill: there is no per-pattern disable, and an entry is either read in full or not read at all.

**This table is the only switch.** The setting is global and applies to every page the skill writes.
A campaign spec never carries one: a spec fixes SCOPE — what gets documented, at what version, with
what boundaries — and wording is not scope. Neither does a slice invocation. Changing which
rewriters are ON is an edit to this table, and it takes effect on the next page written.

## Precedence

**An ON rewriter governs prose style, and outranks the style rules under `guidelines/rules/bans/`
where the two disagree.** Those bans were written against this corpus; a rewriter is a maintained
external standard, and the user has ruled that the standard wins on style.

The bans do not disappear. They keep everything a rewriter does not speak to, and every ban with no
counterpart in an ON rewriter binds unchanged (BAN-01's placement verbs and "vtable", BAN-02's
label-colon, BAN-06's banned words).

**A rewriter governs style and nothing else.** It has no authority over:

1. Facts. Every claim, count, limit, and behavioral statement stays exactly as researched, and no
   rewriter licenses a claim the tree does not witness (FACT-01, FACT-03).
2. Excerpts. Fenced ` ```c ` blocks are byte-exact copies of the tree with provenance comments
   (PAGE-03). A rewriter never reaches inside a fence, and a sentence-length rule does not apply to
   a verbatim kernel comment.
3. Citations. Link anchors, span linking, and the documented version in every URL (PAGE-04).
4. Page structure. Section order, the catalog sections and their mandated bullet form (PAGE-05),
   and the template (`guidelines/reference/TEMPLATE-FULL.md`).
5. Figures. ASCII figure geometry and annotation content (the DIAG rules).

That list is the region contract: a rewriter's rules apply to body prose and headings, which is the
same region ROUTINE-01's prose view computes. Everything the prose view strips is out of reach.

Where an ON rewriter contradicts a FACT, PAGE, PLOT, or DIAG rule rather than a ban, the house rule
governs and the writer records the conflict in its report. Those rules are about the kernel and
about the page, not about prose.

## Adding a rewriter

An external skill qualifies when it meets four conditions:

1. It rewrites without inventing. Its own text must promise that every claim survives and no fact is
   added. Both entries below carry that promise; a skill that "improves" prose by supplying causes
   or mechanisms is disqualified outright.
2. It preserves modality. A hedge is content, and a rewriter that upgrades "may have failed" to
   "failed" changes the claim.
3. It is readable as rules, not as a service. The writer reads it at compose time, so the skill has
   to state its patterns; a skill that only accepts text and returns text cannot be used this way.
4. It has a fixed, citable source, so a page's style is reproducible later.

Add the entry here, set its default, and list every ban it displaces under Conflicts. Nothing else
in the skill changes: `guidelines/passes/02-write.md` reads whatever this table says is ON.

## humanizer

Source: the sibling skill `humanizer`, installed unmodified 2026-08-31 from
<https://github.com/blader/humanizer> at commit e2e92e7, version 2.11.2, MIT. Its 35 patterns derive
from Wikipedia's ["Signs of AI writing"](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing),
maintained by WikiProject AI Cleanup.

It is installed rather than vendored, because the upstream is maintained and a frozen copy would
drift. Re-pull it when you want a newer version, and re-read this entry's conflict list against the
patterns that changed.

Governs: inflated claims and sales language (1, 4), name-dropping (2), -ing pseudo-analysis (3),
vague sources (5), overused AI vocabulary (7), "not X but Y" (9), forced triples (10), repeated
sentence openings (11), passive voice (13), em and en dashes (14), boldface density (15),
bold mini-headings in lists (16), filler and qualifier stacking (23, 24), announcing the next point
(28), a heading restated in the opening sentence (29), and dramatic fragments (31).

Conflicts, resolved in the rewriter's favor:

- BAN-01 item 6 requires a declarative what-does-what heading; pattern 29 forbids the opening
  sentence from restating that heading. Under this rewriter, the heading form stands and the
  opening sentence must say something the heading does not.
- BAN-01 item 2 bans boldface in prose outright; pattern 15 makes it a density rule. The absolute
  ban stands, because it is stricter and the two point the same way.

Where it agrees with the house rules, nothing changes: pattern 14 and BAN-01 item 1 both ban the em
dash, pattern 9 and BAN-01 item 3 both ban the negative construction, patterns 1 and 4 and BAN-04
all ban the hollow superlative, pattern 24 and BAN-07 both ban qualifier stacking.

## asd-ste100

Source: the sibling skill `asd-ste100`, installed unmodified 2026-08-20 from
<https://github.com/danyuchn/asd-ste100-skill>, version 0.4.0. It encodes the rule categories of
ASD-STE100 Issue 9 (January 2025) and reproduces no part of ASD's approved dictionary, so its
lexical rules are a direction of travel and its structural rules are the enforceable part.

Mode: use **STE-flavored**, not Strict. Strict mode is for procedures and error strings; these pages
are explanatory prose, and the skill's own text says a strict rewrite of prose reads as a
personality transplant.

Governs: active voice, one instruction per sentence, sentence length caps, noun clusters of at most
three words, no phrasal verbs, no semicolons, no ellipsis, one topic per paragraph, and simple
tenses.

Conflicts, resolved in the rewriter's favor:

- BAN-03 bans the intro sentence followed by an explanatory list; STE requires a list for three or
  more steps or conditions. Under this rewriter a genuine sequence is a list, and BAN-03 keeps only
  what it was aimed at, which is a list standing in for a sentence that should flow.
- BAN-07 bans hedges; STE requires modality to survive a rewrite. A hedge that names the exact
  condition the code tests is content and stays. BAN-07 keeps the hedge that names no condition.

One conflict resolved AGAINST the rewriter, because it is not a style question:

- STE permits the em dash. BAN-01 bans it, and that ban is a house typographic convention across
  491 pages rather than a claim about clarity. The em dash stays banned.

Its sentence-length caps apply to body prose only. Catalog bullets, table cells, and figure
annotations are outside the region contract.
