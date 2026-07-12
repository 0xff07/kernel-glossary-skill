# 3c. Mechanical checks (by hand)

Rule IDs (3a-3c, 7, 7a-7r) resolve via `guidelines/rules/INDEX.md`.

The mechanical layer of the gates is executed with an editor and standard shell tools. There is no checker script to run, maintain, or trust; a script's regexes age into false positives and its passes into false confidence, so the checks below are the procedure itself. Work page by page.

1. Link targets. List every cited location, then open each one and confirm what the link claims:

```
grep -oE 'source/[^)#[:space:]]+#L[0-9]+' page.md | sed 's|source/||; s|#L| |' | sort -u |
while read f l; do echo "== $f:$l"; sed -n "${l}p" "/path/to/tree/$f"; done
```

Judge each printed line: a symbol-name link must land on the symbol's definition line itself (7m), and a file:line location link must land on the exact site the prose describes. When link and code disagree, fix the anchor by re-finding the symbol on disk.

2. Excerpt verbatimness. For every fenced ` ```c ` block, open the provenance file at the cited line and compare unit by unit (an interior `/* path:line */` delimiter starts a new unit; a standalone `...` line marks a declared elision):

```
sed -n 'START,ENDp' path/from/provenance.c
```

Each unit must begin at its cited line and match byte for byte, tabs included. Content that matches elsewhere in the file with a wrong claimed line number is a finding (7l, 7o).

3. Gate A candidates. Run the candidate greps below fence-aware, then judge EVERY hit against the rule's exemptions and the settled adjudications registry (7r) before touching the page. A hit on an exempt construct is a false candidate, and rewording a compliant phrase to silence a pattern is itself an error: a writer once reworded a correct "32-bit Arm" purely to quiet an arm-word pattern, and that rewording was the only defect introduced. Fix confirmed hits with the 7q recipes.

- `grep -n '—' page.md` — em-dashes; no exemption outside fenced blocks.
- `grep -nE '^[A-Z][^:]{2,80}: [a-z]' page.md` — label-colon candidates; exempt inside double-quoted verbatim text, in catalog bullets, in table rows, and in H3/H4 catalog labels (7a).
- `grep -niE '(usually|typically|generally|normally|commonly|mostly|often|in practice|tends to)' page.md` — hedges; hyphenated compounds ("read-mostly") and verbatim quotes are exempt.
- `grep -niE '(^|[^a-z])arms?([^a-z]|$)' page.md` — the branch-metaphor ban; capitalized CPU-architecture names (Arm, ARM64, arm64) and verbatim quotes are exempt.
- `grep -niE '(contract|tall(y|ies|ied)|canonical|vtable)' page.md` — banned words; verbatim quotes exempt.
- `grep -nE ', not [a-z]+[.,]' page.md` — negative constructions.
- `grep -n '](.*\.md)' page.md` — internal cross-link candidates; only non-URL .md targets are violations.
- `grep -nE '^#{2,4} (Why|How|Where|What)|^#{2,4} .*\?$' page.md` — banned heading shapes.
- `grep -n '\*\*' page.md` — boldface candidates; `/**` kerneldoc openers inside fenced code are exempt.

What no grep can express stays a read-through: 7b prose-list shapes, 7d superlatives judged in context, heading truth (Gate B item 4, 7o), definition-plus-usage parity (Gate B item 1; `guidelines/rules/3b-gate-b.md`), coverage (item 6), figure geometry (item 8), and the whole 7o behavioral-claim audit. Every finding is fixed or recorded as a 7r adjudication with reasoning, never silenced.
