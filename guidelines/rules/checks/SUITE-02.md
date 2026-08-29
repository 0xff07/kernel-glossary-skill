# SUITE-02: Rule wiring

> Extracted from: the cross-references formerly embedded in the rule files. A rule file states its own requirement and nothing else; every dependency, carve-out, pairing, precedence, and fix route between rules lives here, and references run in one direction only, from the harness into the rules.

## Fix routing

Every confirmed hit from a ban sweep is fixed with the matching SUITE-05 recipe, never by ad-hoc rephrasing. The recipe rows map to their rules:

| recipe row | rule |
|---|---|
| em-dash | BAN-01 |
| negative construction ("X, not Y") | BAN-01 |
| placement verbs (lives / sits / wants); "walk" for a scalar | BAN-01 |
| question headings; "vtable" | BAN-01 |
| label-colon prose; colon-introduced quotes and lists | BAN-02 |
| intro sentence + explanatory list | BAN-03 |
| hollow superlatives; "X matters"; "the key ..." | BAN-04 |
| "contract"; "tally"; "canonical"; "arm"/"arms" | BAN-06 |
| hedges | BAN-07 |
| bare kernel-symbol span (Elixir link anchored at the definition line) | PAGE-04 |

- A fix must not introduce another rule's banned shape: swapping a label-colon for "X matters because Y" or "X is what makes Y" trades a BAN-02 hit for a BAN-04 hit.

## Sweep aggregation

- SUITE-04's batched sweep also carries BAN-03's intro-sentence-plus-list shape and the colon-introduced list on the same pass.
- SUITE-04's scan patterns are the grep-shaped tells of BAN-02 and BAN-04.
- The one-unwrapped-line paragraph shape that makes line-anchored patterns blind to mid-paragraph hits is PAGE-01's no-hard-wrapping rule.
- The batched execution, the prose view, and the figure sweep are SUITE-01's.
- Adjudication for every sweep goes against the rule's own exemptions and `../7r-adjudications.md`.

## Evidence chain: code, links, and provenance

- PAGE-04 extends PAGE-01's every-symbol-linked rule with URL construction, anchor selection, and exhaustiveness.
- PAGE-01's DETAILS-walkthrough requirement is evidenced by PAGE-02's parity table.
- PAGE-02 establishes that every fenced C block is real and located; PAGE-03 then byte-compares each block at its cited line.
- PAGE-03's "verbatim between delimiters" requirement is PAGE-02's verbatimness rule applied to stitched blocks.
- FACT-03's "provenance line numbers are claims too" audit executes on PAGE-03's provenance comments.
- FACT-01's breadth mandate ("as mandatory as the prose and citation rules") resolves to BAN-01 through BAN-07 (the SUITE-04/BAN-06/BAN-07 sweep classes included), PAGE-01, and PAGE-02.

## Model and organization

- PLOT-01 and PLOT-03 are a pair: PLOT-01 puts the model at the top of the page, PLOT-03 organizes the body around it.
- FACT-03's one licensed exception (prose stating more than a single excerpt witnesses) is exactly PLOT-01's disclosed synthesis.
- The prose bans bind that synthesis in full: BAN-02's label-colon ban, BAN-04's superlative and importance bans, and the SUITE-04/BAN-06/BAN-07 sweep classes.
- Under the synthesis every fact keeps its own citation, per PAGE-02's excerpt rules and PAGE-04's linking rules; anything the named materials do not support is weakened or scoped per FACT-03.
- PLOT-03's reorganizations preserve coverage; the evidence is PAGE-02's parity table.
- PLOT-04's derived-page audit is that same PAGE-02 parity audit.
- A coverage cut permitted by FACT-01 is a scope decision governed by PLOT-04.
- PLOT-02's meaning column states what a member is in PLOT-01's model; its construct column links the defining code per PAGE-04.
- PLOT-02's semantics tables stay Markdown; where a state set's transitions earn a figure, that figure falls under the diagram rules below.

## Figure governance and precedence

- FACT-01's draw-the-structure mandate executes under the four diagram rules: DIAG-01 (justification, restraint, and geometry), DIAG-02 (banned shapes), DIAG-03 (bit layouts), DIAG-04 (the pattern catalog).
- DIAG-02 outranks DIAG-03 and DIAG-04: a catalog pattern that lands in one of the four banned shapes is not followed. DIAG-04's retired input-grid and event-grid forms are the recorded precedent.
- DIAG-03 sits on top of DIAG-01's general rules.
- DIAG-03's bit ranges, constants, and macros are behavioral claims audited under FACT-03.
- Material that fails DIAG-02's strip-the-labels test routes to a Markdown semantics table under PLOT-02 or into the surrounding prose.
- A catalog in visual form is banned twice over: PLOT-03 bans it in words, DIAG-02 in shape.
- Inside a figure fence the phrase classes (BAN-02, BAN-04, and the SUITE-04/BAN-06/BAN-07 sweeps) are lifted; BAN-01's bans (anthropomorphic verbs, em dashes, negative constructions) still bind figure text. SUITE-01's figure sweep is the mechanism that reaches it.
- DIAG-01's under-80-columns rule has one exception: DIAG-03's single-row L-connector register.
- Per-figure sign-off names the DIAG-03 or DIAG-04 pattern the figure follows.
- PLOT-03's journey-or-model spine and DIAG-01's figure spine are the same spine: a figure depicts the page's journey or model, and the primary figure shows it whole.
- DIAG-01 already rejects the bare call chain as a figure; DIAG-02 extends that rejection to any figure whose entire semantic content is call order.
- DIAG-01's under-drawing case (the operation that reshapes a data structure) maps to DIAG-04's before/after transformation and data-dependency patterns.
- DIAG-02's verbatim-quotation exemption covers the plain fences PAGE-02 mandates for reproduced commit-message tables and figures.
- DIAG-04's register/address-offset-map pattern (addressing across a block) is distinct from DIAG-03's bit layouts (the bits of one register).

## Legacy ID map

The canonical originals (`../rules.md`, `../diagrams.md`) cite rules by their old stable IDs. They resolve here as:

| old ID | resolves to |
|---|---|
| 7 | BAN-01 |
| 7a | BAN-02 |
| 7b | BAN-03 |
| 7c | the bans sweep set (`../bans/README.md` + SUITE-04/BAN-06/BAN-07) |
| 7d | BAN-04 |
| 7e | PAGE-02 |
| 7f | PAGE-01 |
| 7g | DIAG-01 |
| 7h | DIAG-03 |
| 7i | DIAG-04 |
| 7j | FACT-01 |
| 7k | FACT-02 |
| 7l | PAGE-03 |
| 7m | PAGE-04 |
| 7n | PAGE-05 |
| 7o | FACT-03 |
| 7p | PLOT-04 |
| 7q | SUITE-05 |
| 7r | `../7r-adjudications.md` (unchanged) |
| 7s | PLOT-01 |
| 7t | PLOT-02 |
| 7u | PLOT-03 |
| 7v | DIAG-02 |
| 3a, 3b, 3c | SUITE-01 |

- Range phrases in the originals expand in ID order: "7 through 7d" is 7, 7a, 7b, 7c, 7d, and "7 through 7f" adds 7e and 7f.
