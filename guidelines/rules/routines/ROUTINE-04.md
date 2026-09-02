# ROUTINE-04: Candidate generators

> Was: the scan-pattern watch list (7c, then bans/BAN-05.md) and the generators that PAGE-07 and PAGE-08 carried. Harness, not a rule: a page cannot violate this file. The sweep patterns live in BANS.md beside their fixes and exemptions; this file holds the scripts that generate candidates no pattern expresses. Every generator prints candidates and none is the gate: what it prints is read, and the owning rule decides.

## Openers (WRITING rule 1)

Run over the RAW file, because the headings that mark each leading paragraph are what the prose view drops. It prints the first sentence of the lead and of every section, tagged `COUNT` when that sentence carries a number word, a digit or an ordinal. An incidental number ("USB 2.0", "bit 9", "in one word") is cleared on reading; a first sentence that opens on layout or sequence with no purpose stated is a hit the tag cannot see; so every printed sentence is read.

```
python3 - page.md <<'EOF'
import re, sys
L = open(sys.argv[1], encoding="utf-8").read().split("\n")
NUM = re.compile(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|\d+)\b"
                 r"|\b(first|second|third|fourth|fifth|remaining|other)\b", re.I)
fence = False; sec = "lead"; lead = True
for n, l in enumerate(L, 1):
    if l.startswith("```"): fence = not fence; continue
    if fence: continue
    if l.startswith("#"): sec = l.lstrip("#").strip()[:60]; lead = True; continue
    if not l.strip() or l.startswith(("|", "- ", ">")): continue
    if lead:
        s = re.split(r"(?<=[.;:])\s", re.sub(r"\]\(https?://[^)]*\)", "]", l), maxsplit=1)[0]
        print(f"{n} [{sec}]{' COUNT' if NUM.search(s) else ''}: {s[:160]}")
    lead = False
EOF
```

## Members named beside a definition excerpt (WRITING rule 3)

Run over the RAW file, because the members it counts are inside the fences the prose view drops. It prints, per fenced C block that shows two or more struct, union or enum members, how many of those members the two adjacent paragraphs name and which they do not. A block with zero members named is a defect outright; an unnamed member is covered only by a group phrase the paragraph takes from the excerpt's own comment; a paragraph that names every member and only counts or places them is a hit the generator cannot see. So the paragraph beside every excerpt is read, function excerpts included, which the generator never scores.

```
python3 - page.md <<'EOF'
import re, sys
lines = open(sys.argv[1], encoding="utf-8").read().split("\n")
MEMBER = re.compile(r"^\t[^\t/*#}].*?\b(\w+)\s*(?:\[[^\]]*\])?\s*(?::\s*\d+)?\s*;")
ENUMV  = re.compile(r"^\t([A-Z][A-Z0-9_]*)\s*(?:=[^,/]*)?,?\s*(?:/\*.*)?$")
def para(i, step):
    j = i + step
    while 0 <= j < len(lines) and not lines[j].strip(): j += step
    if not (0 <= j < len(lines)) or lines[j].startswith(("```", "#")): return ""
    k = j
    while 0 <= k + step < len(lines) and lines[k + step].strip() and not lines[k + step].startswith("```"): k += step
    a, b = sorted((j, k))
    return " ".join(lines[a:b + 1])
i = 0; blocks = 0; zero = 0; fr = []
while i < len(lines):
    if lines[i].rstrip() != "```c": i += 1; continue
    j = i + 1
    while j < len(lines) and not lines[j].startswith("```"): j += 1
    body = lines[i + 1:j]; kind = None; mem = []
    for l in body:
        if re.search(r"\b(struct|union) \w*\s*\{|\bunion\s*\{", l): kind = "struct"
        elif re.search(r"\benum \w*\s*\{", l): kind = "enum"
        elif l.startswith("}"): kind = None
        m = (MEMBER if kind == "struct" else ENUMV if kind == "enum" else None)
        m = m and m.match(l)
        if m and m.group(1) not in mem: mem.append(m.group(1))
    if len(mem) >= 2:
        prose = re.sub(r"\(https?://[^)]*\)", "", para(i, -1) + " " + para(j, +1))
        named = [m for m in mem if re.search(r"\b" + re.escape(m) + r"\b", prose)]
        blocks += 1; fr.append(len(named) / len(mem)); zero += not named
        print(f"{i + 1}: {len(named)}/{len(mem)} named; unnamed: {' '.join(m for m in mem if m not in named) or '-'}")
    i = j + 1
print(f"definition blocks={blocks} zero-named={zero} mean-fraction-named={sum(fr) / max(len(fr), 1):.2f}")
EOF
```

## Enumerations (BANS, run-on enumeration)

No pattern expresses the shape. Generate candidates as the sentences that carry three or more commas together with " and ", split on semicolons as well as full stops, and rank them by the number of DISTINCT file:line locations each carries: a sentence with four locations is almost always a real hit and a sentence with one almost never is, because a set large enough to need a table needs a location per member. Then read: the steps of one operation are prose, the members of one set are a table.

## SUMMARY shape (WRITING rule 5)

```
awk '/^## SUMMARY/{f=1} /^## SPECIFICATIONS/{f=0} f && /^\|---/{t++} f && /^```/{c++} END{print "tables", t+0, "figures", c/2}' page.md
```

**PASS CRITERIA:** Each generator was run over the raw file of the finished page, every row it printed was read against the owning rule, and the rows with their verdicts are recorded in the dossier's EVIDENCE section. A generator's clean footer is never the pass; the reading is.
