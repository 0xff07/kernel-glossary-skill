# Facts, code, and coverage

> Was: Facts, code, and coverage

What a page must prove and how it must prove it: excerpts, provenance, enumeration, claim verification. These are the classes the writer owns end to end and the exit suite checks.

## Reference boundary

**Reference direction is one-way, and it is enforced.** A rule file here states its own requirement and references no other rule: nothing in this directory or in bans/, diagrams/, page/, plots/ — not by name, not by path, not even a sibling one file over — and never routines/ or pipelines/. The one allowed shared reference is the settled adjudications registry, `../7r-adjudications.md`. Rules are referenced from above (routines/ and pipelines/), never the reverse.

The boundary is grep-checkable from `guidelines/rules/`:

```
grep -rnE '(BAN|PAGE|FACT|PLOT|DIAG|ROUTINE|PIPELINE)-[0-9]|routines/|pipelines/' facts/FACT-*.md | awk -F: '$2+0 != 1'
```

must print nothing (line 1 is each file's own title; the glob keeps this README out of the sweep).
