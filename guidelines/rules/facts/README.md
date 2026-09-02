# facts/

What a page must prove and how: coverage (FACT-01), driver examples (FACT-02), behavioral-claim verification (FACT-03), the activation delta (FACT-04). These are the classes the writer owns end to end and the exit suite checks.

## Reference boundary

A rule file here references no other rule and no shared file; rules are referenced from above, never the reverse. Settled rulings live in `../WAIVERS.md`, which rules never cite. Grep-checkable from `guidelines/rules/`:

```
grep -rnE '(BAN|PAGE|FACT|PLOT|DIAG|ROUTINE)-[0-9]|WRITING|BANS|routines/|WAIVERS' facts/FACT-[0-9]*.md | awk -F: '$2+0 != 1'
```

must print nothing.
