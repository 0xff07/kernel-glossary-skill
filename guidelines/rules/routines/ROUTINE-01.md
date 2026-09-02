# ROUTINE-01: The checking protocol

> Was: the cross-cutting protocol of the gates 3a, 3b and 3c; the per-rule checks live in each rule's PASS CRITERIA. Harness, not a rule: a page cannot violate this file.

A page passes when every PASS CRITERIA in `../WRITING.md`, `../BANS.md` and every rule under `../page/`, `../facts/` and `../plots/` passes, plus `../diagrams/` when the page carries a figure. This file carries what belongs to no single rule: who runs the criteria, how the sweeps execute, and the completeness discipline that keeps a clean run meaningful.

## Ownership and independence

1. Verify each criterion by performing its named action and recording the evidence, a count or a list, never "looks fine".
2. The writer runs every criterion on its own work first, the sweeps on its own prose included: the sweeps are procedure, not perception, and survive self-application.
3. The orchestrator re-runs every mechanical check independently, compares the answers, and adjudicates every residual itself; adjudication is never delegated.
4. Re-run the mechanical criteria after every edit, your own hand-edits included. A page is final only at zero unadjudicated findings.
5. No checker script is trusted: a script's regexes age into false positives and its passes into false confidence. Scripts generate candidates; the criteria are executed by hand with an editor and standard shell tools, and a helper script is believed only after it has been shown to fail on an injected defect and its headline count cross-checked against a one-line grep.

## The batched sweep and the prose view

1. Run every `../BANS.md` pattern as one batched pass against a prose view of the page, never the raw file, case-insensitively and never anchored to line start (a paragraph is one line, and an anchored pattern sees only its first clause).
2. Only the checks marked as raw-file runs go against the raw file: BANS' boldface and heading greps, PAGE-01's internal-link greps, PAGE-06's table-cell inventory, ROUTINE-04's generators, and BANS' fence-introducing-colon adjudication.
3. Patterns generate candidates. Judge every hit against BANS' exemptions and `../WAIVERS.md` before editing, write the verdict down first, and never reword an exempt construct to silence a pattern.

The view builder:

```
python3 - page.md <<'EOF'
import re, sys
CAT = ("## LINUX KERNEL", "## KERNEL DOCUMENTATION", "## OTHER SOURCES", "## SPECIFICATIONS")
fence = cat = False
for n, l in enumerate(open(sys.argv[1], encoding="utf-8"), 1):
    l = l.rstrip("\n")
    if l.startswith("```"): fence = not fence; continue
    if fence: continue
    if l.startswith("## "): cat = l.strip() in CAT; continue
    if l.startswith("#"):
        print(f"{n}:[H] {l.lstrip('#').strip()}"); continue
    if l.startswith(">"): continue
    tag = ""
    if cat or l.startswith("|") or l.lstrip().startswith(("- ", "* ")):
        tag = "[C] "
    l = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", l)
    l = re.sub(r"`[^`]*`", "§", l)
    l = re.sub(r'"[^"]*"', "§", l)
    l = re.sub(r"\b[\w/.-]+\.(c|h|rst|S):\d+", "§", l)
    l = re.sub(r"::|\d+:\d+", "§", l)
    print(f"{n}:{tag}{l}")
EOF
```

Rows tagged `[C]` are catalog bullets, list items and table cells: the label-colon shape is exempt there and nothing else, and SPECIFICATIONS entries keep their mandated `<spec name>, section <N.N>: <section title>` form.

## The figure sweep

The prose view discards every fenced block, so figure text is invisible to the patterns above and is swept separately:

```
awk '/^```/{f=!f; lang=(f? substr($0,4) : ""); next} f && lang!="c"' page.md
```

Adjudicate what it prints against the three bans that reach figures (the em dash, the negative construction, the placement verbs) and against `../diagrams/DIAG-02.md`'s banned shapes. A ` ```c ` block is a source excerpt and is never swept; a fenced verbatim quotation is exempt like any other quoted text. Judge geometry mechanically per `ROUTINE-07.md`.

## Regions times rules

A grep is a candidate generator, never the gate. Enumerate the page's regions (prose, headings, figures, catalog bullets, table cells, fenced excerpts) and, for every rule that binds a region, name the mechanism that reaches it. A region no mechanism reaches is not clean; it is unexamined, and it reads exactly like clean. `guidelines/LESSONS.md` records the classes that shipped behind patterns that could not fire.

## What no pattern reaches

These stay a read-through: BANS' list shapes and run-on enumerations (ROUTINE-04 ranks the candidates); superlatives judged in context; heading truth and the full claim audit (FACT-03); the parity table (PAGE-02); table-cell spans (PAGE-06); WRITING's leading paragraphs, excerpt paragraphs, DETAILS spine and SUMMARY shape (ROUTINE-04 prints the candidates); coverage enumerations (FACT-01); figure geometry (ROUTINE-07). Every finding is fixed or surfaced for `../WAIVERS.md` with reasoning, never silenced.

**PASS CRITERIA:**

1. Every PASS CRITERIA in WRITING, BANS and every rule file was executed twice: by the writer before reporting done, and independently by the checker, with the answer sets compared and every residual adjudicated by the orchestrator.
2. The evidence for each criterion is a count or a list, and the mechanical criteria were re-run after every subsequent edit.
3. The regions-times-rules confirmation is on record: for each region, the mechanism that reached it.
4. Zero unadjudicated findings remain; every finding was fixed or surfaced with reasoning.
