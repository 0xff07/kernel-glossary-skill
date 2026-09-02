# page/

The page-mechanics rules: PAGE-01 (general page rules), PAGE-02 (self-contained kernel-source citation), PAGE-03 (code-block provenance comments), PAGE-04 (link anchoring and exhaustive span linking), PAGE-05 (OTHER SOURCES provenance), PAGE-06 (linked code in table cells). What a page is for, the rule every one of these protects, is `../WRITING.md`.

## Reference boundary

A rule file here states its own requirement and references no other rule and no shared file: not a sibling, not another directory, never `../routines/` and never `../WAIVERS.md`, which is harness that modifies how these rules apply and is routed to by the checking protocol. Rules are referenced from above (the routines and the passes), never the reverse. Grep-checkable from `guidelines/rules/`:

```
grep -rnE '(BAN|PAGE|FACT|PLOT|DIAG|ROUTINE)-[0-9]|WRITING|BANS|routines/|WAIVERS' page/PAGE-[0-9]*.md | awk -F: '$2+0 != 1'
```

must print nothing (line 1 is each file's own title).
