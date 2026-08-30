# plots/

The page-structure rules: PLOT-01 (domain-model layer), PLOT-02 (semantics tables for state sets and taxonomies), PLOT-03 (journey- or model-first organization), PLOT-04 (deriving from an existing page).

## Reference boundary

**Reference direction is one-way, and it is enforced.** A rule file here states its own requirement and references no other rule and no shared file: nothing in this directory or in bans/, diagrams/, facts/, page/ — not by name, not by path, not even a sibling one file over — and never routines/ or pipelines/. Rules are referenced from above (the routines, and the passes over them), never the reverse. The directory's `PLOT-WAIVERS.md` is harness, not a rule — its waivers and settled rulings modify how these rules apply, and the checking protocol routes adjudication to it: rules never cite it, and it may name this directory's rules only, never a foreign directory's.

The boundary is grep-checkable from `guidelines/rules/`:

```
grep -rnE '(BAN|PAGE|FACT|PLOT|DIAG|ROUTINE|PIPELINE)-[0-9]|routines/|pipelines/|WAIVERS' plots/PLOT-[0-9]*.md | awk -F: '$2+0 != 1'
grep -rnE '(BAN|PAGE|FACT|DIAG|ROUTINE|PIPELINE)-[0-9]|routines/|pipelines/' plots/PLOT-WAIVERS.md
```

must print nothing (line 1 is each file's own title; the `[0-9]` glob keeps this README and the waivers file out of the rule sweep).
