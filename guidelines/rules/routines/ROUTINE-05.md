# ROUTINE-05: Rephrase recipes (quick reference)

> Was: 7q. Rephrase recipes (quick reference); then bans/BAN-QUICKFIX.md. Harness, not a rule: a page cannot violate this file; it is the fix lookup the sweeps route confirmed hits through.

Every ban has a one-line recipe; apply the recipe instead of re-deriving compliant phrasing per hit. Each ban's own rule carries the full statement and worked examples; this table is the lookup.

| banned | recipe |
|---|---|
| em-dash | parentheses, or two sentences |
| label-colon prose ("X: Y", "The fix: Y") | one plain declarative sentence; introduce quotes with "According to the comment ..." |
| intro sentence + explanatory list | fold the items into one flowing sentence |
| hedge (usually, typically, often, in practice, ...) | name the exact condition the code tests |
| hollow superlative, "X matters", "the key ..." | name the mechanic in the same clause and drop the ranking |
| "contract" | state the precondition, guarantee, or invariant it stands for |
| "tally" | "count" |
| "canonical X" | "the X that performs it", named plainly |
| "arm"/"arms" for a branch or union case | "branch", "case", "side", "leg", or the symbol name |
| "X, not Y" | state X plainly; drop the contrast |
| lives / sits / wants for code placement | "is defined in", "is held in", "is stored in" |
| "walk" for a scalar changing value | "transitions through", "advances through" |
| Why/How/Where or question headings | declarative subject-verb-object heading |
| "vtable" | "function pointer struct" or the concrete type name |
| bare kernel-symbol span | Elixir link anchored at the definition line |

**PASS CRITERIA:** This table imposes no page-level check of its own; a page cannot fail it directly. It passes through use: every confirmed hit from the ban sweeps is fixed with the matching recipe above instead of ad-hoc rephrasing, and no fix introduces another banned shape (swapping a label-colon for "X matters because Y" trades a BAN-02 hit for a BAN-04 hit). When reviewing a finished page, spot-confirm that applied fixes match the recipes' target forms.
