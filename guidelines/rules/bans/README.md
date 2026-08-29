# Forbidden phrases checklist

> Was: 7c. Forbidden phrases checklist

The sweep list for the classes above and the two ban classes that live here. Scan every body paragraph for these before writing on, and rewrite hits as plain declarative sentences; quote comments with "According to the comment <quote>, ..." or "The comment reads <quote>." instead of label-colon framing.

## Reference boundary

**Reference direction is one-way, and it is enforced.** A rule file here states its own requirement and references no other rule: nothing in this directory or in diagrams/, facts/, page/, plots/ — not by name, not by path, not even a sibling one file over — and never routines/ or pipelines/. The one allowed shared reference is the settled adjudications registry, `../7r-adjudications.md`. Rules are referenced from above (routines/ and pipelines/), never the reverse.

The boundary is grep-checkable from `guidelines/rules/`:

```
grep -rnE '(BAN|PAGE|FACT|PLOT|DIAG|ROUTINE|PIPELINE)-[0-9]|routines/|pipelines/' bans/BAN-*.md | awk -F: '$2+0 != 1'
```

must print nothing (line 1 is each file's own title; the glob keeps this README out of the sweep).
