# ROUTINE-01: The checking protocol

> Was: the cross-cutting protocol of the gates 3a (Gate A), 3b (Gate B), and 3c (mechanical checks), rules.md:542-715; the per-rule checks themselves now live in each rule file's PASS CRITERIA.

A page passes when every PASS CRITERIA in every rule file under `../bans/`, `../page/`, `../facts/`, and `../plots/` passes. This page carries only what belongs to no single rule: who runs the criteria, when, how the mechanical sweeps execute, and the completeness discipline that keeps a clean run meaningful.

## Ownership and independence (was rules.md:567-571)

1. Verify each criterion by performing its named action and recording the evidence, a count or a list, not "looks fine"; reading the page is not sufficient.
2. The writer runs every criterion on its own work first, the mechanical sweeps on its own prose included. An earlier split that forbade self-sweeping was withdrawn, because the sweeps are procedure rather than perception and survive self-application; the reasoning is recorded in `../../passes/03-check.md`.
3. The orchestrator then re-runs every mechanical check independently and compares the answers; it adjudicates every residual itself and never delegates adjudication.

## Re-run trigger and terminal condition (was rules.md:544, 563, 571, 611)

1. Re-run the mechanical criteria after every edit, your own hand-edits included.
2. A page is final only at zero unadjudicated findings across every rule file.
3. There is no checker script to run, maintain, or trust: a script's regexes age into false positives and its passes into false confidence, so the criteria are executed by hand with an editor and standard shell tools, and a check that cannot fail is not a check.

## The batched sweep and the prose view (was rules.md:636-679)

1. Run the mechanical sweeps of BAN-01, BAN-02, BAN-04, BAN-06, and BAN-07 as one batched pass, per ROUTINE-04's watch list and execution audit, against a prose view of the page, never the raw file.
2. Only the checks their criteria mark as raw-file runs go against the raw file (BAN-01's heading and boldface greps, PAGE-01's internal-link greps, PAGE-06's table-cell span inventory — the prose view tags table rows `[C]` and rewrites their links away, so it cannot see them; PAGE-07's explanation generator, which counts the members inside the fences the view drops; PAGE-08's opener generator, which needs the headings the view drops to find each section's first paragraph; and BAN-02's fence-introducing-colon adjudication, which needs the fence the view drops).
3. The patterns generate candidates; they are not the gate. Judge every hit against the rule's own exemptions and its directory's waivers file (each rule directory carries one, `<PREFIX>-WAIVERS.md`; for this batched sweep that is `../bans/BAN-WAIVERS.md`) before editing, and never reword an exempt construct to silence a pattern.
4. BAN-07's criteria carry the full hedge token list for the batched sweep.

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
    tag = ""                                               # [C] = label-colon exempt (waiver) ONLY;
    if cat or l.startswith("|") or l.lstrip().startswith(("- ", "* ")):
        tag = "[C] "                                       #   every OTHER ban still binds here
    l = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", l)         # [text](url) -> text; kills URL colons
    l = re.sub(r"`[^`]*`", "§", l)                      # inline code -> placeholder
    l = re.sub(r'"[^"]*"', "§", l)                      # double-quoted verbatim (waiver)
    l = re.sub(r"\b[\w/.-]+\.(c|h|rst|S):\d+", "§", l)  # file:line citations
    l = re.sub(r"::|\d+:\d+", "§", l)                   # scope form, ratios
    print(f"{n}:{tag}{l}")
EOF
```

### Rows tagged `[C]`

1. `[C]` rows are catalog bullets, list items, and table cells. `../bans/BAN-WAIVERS.md` exempts the label-colon shape there and nothing else: skip BAN-02 candidates on `[C]` rows and adjudicate every other pattern on them exactly as on flowing prose.
2. SPECIFICATIONS entries are list bullets whose `<spec name>, section <N.N>: <section title>` format is mandated by `../../passes/01-research.md`; rewording them to silence a pattern breaks a format another guideline requires (was rules.md:667-673).

## The figure sweep (was rules.md:699-705)

1. The prose view discards every fenced block, so figure annotations are invisible to every pattern above, yet they are still governed: the diagram rules lift only the phrase classes inside a figure (BAN-02, BAN-04, and the ROUTINE-04/BAN-06/BAN-07 sweeps), and BAN-01's bans (anthropomorphic verbs, em dashes, negative constructions) still bind figure text.
2. Close the region explicitly:

```
awk '/^```/{f=!f; lang=(f? substr($0,4) : ""); next} f && lang!="c"' page.md
```

After it prints:

1. Adjudicate the output against BAN-01 and against the banned figure shapes of `../diagrams/DIAG-02.md` (was 7v; the four diagram rules are split verbatim into `../diagrams/DIAG-01.md` through `../diagrams/DIAG-04.md`, each carrying its own PASS CRITERIA; the original was retired to its git pin).
2. A ` ```c ` block is a source excerpt and is never swept; a fenced block reproducing a verbatim quotation (a commit message, a kernel comment) is exempt like any other verbatim text.
3. Judge the geometry mechanically rather than by eye, and repair what it rejects per `ROUTINE-07.md`.

## Regions times rules (was rules.md:709-715)

1. A grep is a candidate generator, never the gate.
2. Four classes shipped behind a pattern that structurally could not see them:
   1. the mid-paragraph label-colon (BAN-02) behind a line-anchored grep;
   2. the figure annotation behind the fence-stripping view;
   3. the heading behind a prose view that dropped every `#` line even though BAN-01, BAN-04, and FACT-03 bind headings;
   4. the whole catalog region behind a blanket exemption that generalized one registry carve-out into a total blind spot.
3. The discipline is therefore: enumerate the page's regions (prose, headings, figures, catalog bullets, table cells, fenced excerpts) and, for every rule that binds a region, name the mechanism that reaches it.
4. A region no mechanism reaches is not clean; it is unexamined, and it reads exactly like clean.

## What no pattern reaches

1. These classes stay a read-through:
   1. BAN-03's prose-list shapes;
   2. BAN-08's enumerating sentences, counted by member rather than matched by pattern;
   3. BAN-04's superlatives judged in context;
   4. FACT-03's heading truth and full claim audit;
   5. PAGE-02's parity table;
   6. PAGE-06's table-cell spans, inventoried from the raw file;
   7. PAGE-07's shape-only paragraphs beside excerpts (its generator counts the members a paragraph names; whether the paragraph explains them or merely counts and places them is read);
   8. FACT-01's coverage enumerations;
   9. figure geometry;
   10. PAGE-08's leading paragraphs (its generator tags a count or an ordinal in a first sentence; whether the paragraph opens on purpose is read, tagged or not).
2. Every finding is fixed or surfaced for the owning rule's directory waivers file with reasoning (the user alone folds a ruling in), never silenced.

**PASS CRITERIA:**

1. Every PASS CRITERIA in every rule file under `../bans/`, `../page/`, `../facts/`, and `../plots/` was executed twice: once by the writer before reporting done, once independently by the checker, with the two answer sets compared and every residual adjudicated by the orchestrator itself, never delegated.
2. The evidence for each criterion is recorded as a count or a list, and the mechanical criteria were re-run after every subsequent edit, hand-edits included.
3. The regions-times-rules confirmation is on record: for each region of the page, the mechanism that reached it is named, and no region a rule binds was left unexamined.
4. Zero unadjudicated findings remain across every rule file; every finding was fixed or surfaced for the owning rule's directory waivers file with reasoning.
