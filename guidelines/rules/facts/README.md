# Facts, code, and coverage

> Was: Facts, code, and coverage

What a page must prove and how it must prove it: excerpts, provenance, enumeration, claim verification. These are the classes the writer owns end to end and the exit suite checks.

## Reference boundary

**Reference direction is one-way, and it is enforced.** A rule file here states its own requirement and references no other rule and no shared file: nothing in this directory or in bans/, diagrams/, page/, plots/ — not by name, not by path, not even a sibling one file over — and never routines/ or pipelines/. Rules are referenced from above (the routines, and the passes over them), never the reverse. The directory's `FACT-WAIVERS.md` is harness, not a rule — its waivers and settled rulings modify how these rules apply, and the checking protocol routes adjudication to it: rules never cite it, and it may name this directory's rules only, never a foreign directory's.

The boundary is grep-checkable from `guidelines/rules/`:

```
grep -rnE '(BAN|PAGE|FACT|PLOT|DIAG|ROUTINE|PIPELINE)-[0-9]|routines/|pipelines/|WAIVERS' facts/FACT-[0-9]*.md | awk -F: '$2+0 != 1'
grep -rnE '(BAN|PAGE|PLOT|DIAG|ROUTINE|PIPELINE)-[0-9]|routines/|pipelines/' facts/FACT-WAIVERS.md
```

must print nothing (line 1 is each file's own title; the `[0-9]` glob keeps this README and the waivers file out of the rule sweep).
