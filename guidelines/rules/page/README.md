# page/

The page-mechanics rules: PAGE-01 (general page rules), PAGE-02 (self-contained kernel-source citation), PAGE-03 (code-block provenance comments), PAGE-04 (link anchoring and exhaustive span linking), PAGE-05 (OTHER SOURCES provenance).

## Reference boundary

**Reference direction is one-way, and it is enforced.** A rule file here states its own requirement and references no other rule: nothing in this directory or in bans/, diagrams/, facts/, plots/ — not by name, not by path, not even a sibling one file over — and never routines/ or pipelines/. The one allowed shared reference is the settled adjudications registry, `../7r-adjudications.md`. Rules are referenced from above (routines/ and pipelines/), never the reverse.

The boundary is grep-checkable from `guidelines/rules/`:

```
grep -rnE '(BAN|PAGE|FACT|PLOT|DIAG|ROUTINE|PIPELINE)-[0-9]|routines/|pipelines/' page/PAGE-*.md | awk -F: '$2+0 != 1'
```

must print nothing (line 1 is each file's own title; the glob keeps this README out of the sweep).
