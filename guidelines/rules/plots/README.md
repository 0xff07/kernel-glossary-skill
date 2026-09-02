# plots/

One rule: PLOT-04 (deriving from an existing page), read only when a page is rebuilt from prior material. The organization rules that used to share this directory (the domain model first, semantics tables for state sets, journey- or model-first DETAILS) are items 2 and 5 of `../WRITING.md`.

## Reference boundary

A rule file here references no other rule and no shared file; rules are referenced from above, never the reverse. Grep-checkable from `guidelines/rules/`:

```
grep -rnE '(BAN|PAGE|FACT|PLOT|DIAG|ROUTINE)-[0-9]|WRITING|BANS|routines/|WAIVERS' plots/PLOT-[0-9]*.md | awk -F: '$2+0 != 1'
```

must print nothing.
