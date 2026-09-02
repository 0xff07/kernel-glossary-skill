# ROUTINE-05: Rephrase recipes (quick reference)

> Was: 7q. Rephrase recipes (quick reference); then bans/BAN-QUICKFIX.md. Harness, not a rule: a page cannot violate this file; it is the fix lookup the sweeps route confirmed hits through.

Every ban has a one-line recipe; apply the recipe instead of re-deriving compliant phrasing per hit. Each ban's own rule carries the full statement and worked examples; this table is the lookup, and its last column names the rule that owns each class (was the fix-routing table of the retired walkthrough).

| banned | recipe | rule |
|---|---|---|
| em-dash | parentheses, or two sentences | BAN-01 |
| label-colon prose ("X: Y", "The fix: Y") | one plain declarative sentence; introduce quotes with "According to the comment ..." | BAN-02 |
| shape-only paragraph beside an excerpt ("the first five fields", "adjacent fields", "has three branches") | name each member the excerpt shows, say what it holds and which path writes or reads it, or elide the excerpt to the members the paragraph explains; a colon-terminated sentence naming what the excerpt shows may introduce it | PAGE-07 |
| intro sentence + explanatory list | fold the items into one flowing sentence | BAN-03 |
| hedge (usually, typically, often, in practice, ...) | name the exact condition the code tests | BAN-07 |
| hollow superlative, "X matters", "the key ..." | name the mechanic in the same clause and drop the ranking | BAN-04 |
| "contract" | state the precondition, guarantee, or invariant it stands for | BAN-06 |
| "tally" | "count" | BAN-06 |
| "canonical X" | "the X that performs it", named plainly | BAN-06 |
| "arm"/"arms" for a branch or union case | "branch", "case", "side", "leg", or the symbol name | BAN-06 |
| "X, not Y" | state X plainly; drop the contrast | BAN-01 |
| lives / sits / wants for code placement | "is defined in", "is held in", "is stored in" | BAN-01 |
| "walk" for a scalar changing value | "transitions through", "advances through" | BAN-01 |
| Why/How/Where or question headings | declarative subject-verb-object heading | BAN-01 |
| "vtable" | "function pointer struct" or the concrete type name | BAN-01 |
| bare kernel-symbol span | Elixir link anchored at the definition line | PAGE-04 |

**PASS CRITERIA:** This table imposes no page-level check of its own; a page cannot fail it directly. It passes through use: every confirmed hit from the ban sweeps is fixed with the matching recipe above instead of ad-hoc rephrasing, and no fix introduces another banned shape (swapping a label-colon for "X matters because Y" trades a BAN-02 hit for a BAN-04 hit). When reviewing a finished page, spot-confirm that applied fixes match the recipes' target forms.
