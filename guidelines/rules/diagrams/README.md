# diagrams/

The figure rules, read only when a page will carry a figure: DIAG-01 (general ASCII diagram principles), DIAG-02 (banned figure shapes, which outrank the catalogs), DIAG-03 (register and bitfield figures), DIAG-04 (the pattern catalog).

## Reference boundary

A rule file here references no other rule and no shared file; rules are referenced from above, never the reverse. Settled rulings live in `../WAIVERS.md`, which rules never cite. Grep-checkable from `guidelines/rules/`:

```
grep -rnE '(BAN|PAGE|FACT|PLOT|DIAG|ROUTINE)-[0-9]|WRITING|BANS|routines/|WAIVERS' diagrams/DIAG-[0-9]*.md | awk -F: '$2+0 != 1'
```

must print nothing.
