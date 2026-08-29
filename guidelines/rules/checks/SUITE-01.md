# SUITE-01: The checking protocol

> Was: the cross-cutting protocol of the gates 3a (Gate A), 3b (Gate B), and 3c (mechanical checks), rules.md:542-715; the per-rule checks themselves now live in each rule file's PASS CRITERIA.

A page passes when every PASS CRITERIA in every rule file under `../bans/`, `../page/`, `../facts/`, and `../plots/` passes. This page carries only what belongs to no single rule: who runs the criteria, when, how the mechanical sweeps execute, and the completeness discipline that keeps a clean run meaningful.

**Ownership and independence** (was rules.md:567-571). Verify each criterion by performing its named action and recording the evidence, a count or a list, not "looks fine"; reading the page is not sufficient. The writer runs every criterion on its own work first, the mechanical sweeps on its own prose included (an earlier split that forbade self-sweeping was withdrawn, because the sweeps are procedure rather than perception and survive self-application; the reasoning is recorded in `../../passes/03-check.md`). The orchestrator then re-runs every mechanical check independently and compares the answers; it adjudicates every residual itself and never delegates adjudication. A verify campaign re-runs everything later, on a newer tree or under a different model.

**Re-run trigger and terminal condition** (was rules.md:544, 563, 571, 611). Re-run the mechanical criteria after every edit, your own hand-edits included. A page is final only at zero unadjudicated findings across every rule file. There is no checker script to run, maintain, or trust: a script's regexes age into false positives and its passes into false confidence, so the criteria are executed by hand with an editor and standard shell tools, and a check that cannot fail is not a check.

**The batched sweep and the prose view** (was rules.md:636-679). Run the mechanical sweeps of BAN-01, BAN-02, BAN-04, BAN-06, and BAN-07 as one batched pass, per BAN-05's procedure, against a prose view of the page, never the raw file; only the checks their criteria mark as raw-file runs go against the raw file (BAN-01's heading and boldface greps, PAGE-01's internal-link greps). The patterns generate candidates; they are not the gate. Judge every hit against the rule's own exemptions and the settled adjudications registry (`../7r-adjudications.md`) before editing, and never reword an exempt construct to silence a pattern. BAN-07's criteria carry the full hedge token list for the batched sweep.

The view builder (was rules.md:640-664; the canonical copy's output line, rules.md:661, drops the computed `[C]` tag it just built, a defect corrected here):

```
python3 - page.md <<'EOF'
import re, sys
CAT = ("## LINUX KERNEL", "## KERNEL DOCUMENTATION", "## OTHER SOURCES", "## SPECIFICATIONS")
fence = cat = False
for n, l in enumerate(open(sys.argv[1], encoding="utf-8"), 1):
    l = l.rstrip("\n")
    if l.startswith("```"): fence = not fence; continue    # fenced blocks exempt (PAGE-01)
    if fence: continue
    if l.startswith("## "): cat = l.strip() in CAT; continue
    if l.startswith("#"):                                  # headings are GOVERNED (BAN-01, BAN-04, FACT-03):
        print(f"{n}:[H] {l.lstrip('#').strip()}"); continue #   emit them, do not drop them
    if l.startswith(">"): continue                          # caution blockquote
    tag = ""                                               # [C] = label-colon exempt (7r) ONLY;
    if cat or l.startswith("|") or l.lstrip().startswith(("- ", "* ")):
        tag = "[C] "                                       #   every OTHER ban still binds here
    l = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", l)         # [text](url) -> text; kills URL colons
    l = re.sub(r"`[^`]*`", "§", l)                      # inline code -> placeholder
    l = re.sub(r'"[^"]*"', "§", l)                      # double-quoted verbatim (7r)
    l = re.sub(r"\b[\w/.-]+\.(c|h|rst|S):\d+", "§", l)  # file:line citations
    l = re.sub(r"::|\d+:\d+", "§", l)                   # scope form, ratios
    print(f"{n}:{tag}{l}")
EOF
```

Rows tagged `[C]` are catalog bullets, list items, and table cells. The registry exempts the label-colon shape there and nothing else: skip BAN-02 candidates on `[C]` rows and adjudicate every other pattern on them exactly as on flowing prose. SPECIFICATIONS entries are list bullets whose `<spec name>, section <N.N>: <section title>` format is mandated by `../../passes/01-research.md`; rewording them to silence a pattern breaks a format another guideline requires (was rules.md:667-673).

**The figure sweep** (was rules.md:699-705). The prose view discards every fenced block, so figure annotations are invisible to every pattern above, yet they are still governed: the diagram rules lift only the phrase classes inside a figure (BAN-02, BAN-04, and the BAN-05/BAN-06/BAN-07 sweeps), and BAN-01's bans (anthropomorphic verbs, em dashes, negative constructions) still bind figure text. Close the region explicitly:

```
awk '/^```/{f=!f; lang=(f? substr($0,4) : ""); next} f && lang!="c"' page.md
```

Adjudicate what it prints against BAN-01 and against the banned figure shapes of `../diagrams/DIAG-02.md` (was 7v; the four diagram rules are split verbatim into `../diagrams/DIAG-01.md` through `../diagrams/DIAG-04.md`, each carrying its own PASS CRITERIA; `../diagrams.md` remains canonical). A ` ```c ` block is a source excerpt and is never swept; a fenced block reproducing a verbatim quotation (a commit message, a kernel comment) is exempt like any other verbatim text.

**Regions times rules** (was rules.md:709-715). A grep is a candidate generator, never the gate. Four classes shipped behind a pattern that structurally could not see them: the mid-paragraph label-colon (BAN-02) behind a line-anchored grep; the figure annotation behind the fence-stripping view; the heading behind a prose view that dropped every `#` line even though BAN-01, BAN-04, and FACT-03 bind headings; and the whole catalog region behind a blanket exemption that generalized one registry carve-out into a total blind spot. The discipline is therefore: enumerate the page's regions (prose, headings, figures, catalog bullets, table cells, fenced excerpts) and, for every rule that binds a region, name the mechanism that reaches it. A region no mechanism reaches is not clean; it is unexamined, and it reads exactly like clean.

What no pattern reaches stays a read-through: BAN-03's prose-list shapes, BAN-04's superlatives judged in context, FACT-03's heading truth and full claim audit, PAGE-02's parity table, FACT-01's coverage enumerations, and figure geometry. Every finding is fixed or recorded as an adjudication in `../7r-adjudications.md` with reasoning, never silenced.

**PASS CRITERIA:**

- Every PASS CRITERIA in every rule file under `../bans/`, `../page/`, `../facts/`, and `../plots/` was executed twice: once by the writer before reporting done, once independently by the checker, with the two answer sets compared and every residual adjudicated by the orchestrator itself, never delegated.
- The evidence for each criterion is recorded as a count or a list, and the mechanical criteria were re-run after every subsequent edit, hand-edits included.
- The regions-times-rules confirmation is on record: for each region of the page, the mechanism that reached it is named, and no region a rule binds was left unexamined.
- Zero unadjudicated findings remain across every rule file; every finding was fixed or recorded in `../7r-adjudications.md` with reasoning.
