# Pass 02: write

Purpose: compose the complete page following every writing rule, then verify it — facts AND prose — with the mechanical exit suite before reporting done.
Inputs: the dossier (pass 01) and the resolved parameters (pass 00); every dossier fact is re-verified on disk before it lands, because the tree at the documented version is the only ground truth.
Outputs: the draft page at `docs/<dir>/<topic-slug>.md`, and the dossier updated — its PARITY table closed and its EVIDENCE section written, plus any research entry the disk disagreed with corrected. Page state after this pass: WRITTEN.
Run by: single-agent mode inline; in a campaign a dispatched writer agent (brief at the end of this file), on the strongest available model.
Next: pass 03 (`guidelines/passes/03-check.md`), the orchestrator's independent mechanical check. The writer owns the page end to end — facts and prose — and closes the PARITY table, runs the full exit suite below (which now includes the ROUTINE-01 sweeps), and persists its evidence before reporting. Page state after this pass: WRITTEN.

Rules are cited by stable ID; `guidelines/rules/INDEX.md` maps every ID to its file.

## Reading list (mandatory, in order)

This pass owns the writer's reading list; the writer brief points here instead of restating rules.

1. The waivers files — `guidelines/rules/bans/BAN-WAIVERS.md`, `page/PAGE-WAIVERS.md`, `facts/FACT-WAIVERS.md`, `plots/PLOT-WAIVERS.md`, `diagrams/DIAG-WAIVERS.md` — the settled waivers and rulings, all five first; then the rule corpus under `guidelines/rules/` — `INDEX.md` first (the map), then every rule under `bans/`, `page/`, `facts/`, and `plots/` (PLOT-04 applies additionally whenever the page derives from existing material).
2. `guidelines/reference/rewriters.md`: the rewriter switchboard. Read the switchboard, then read in full the SKILL.md of every rewriter it lists as ON, and nothing of the ones it lists as OFF. An ON rewriter governs prose style and outranks the bans under `guidelines/rules/bans/` where the two disagree; that file names each displacement. It governs style only — facts, excerpts, citations, page structure, and figures stay with the house rules. Compose under the ON rewriters from the first sentence; this is not a rewriting step after the draft.
3. The figure rules under `guidelines/rules/diagrams/`, but only when the page will carry a figure: DIAG-01's principles and DIAG-02's banned shapes always govern one, and DIAG-03 and DIAG-04 hold the figure catalogs (choose the shape from DIAG-04's use-case index). A page with no figure needs none of it.
4. `guidelines/reference/measured-criteria.md`: the depth rules and tripwires that define what "in-depth, fine-grained" measures as.
5. The exemplar pages under `docs/sound/` chosen in pass 00 (`guidelines/passes/00-prep.md`), read in full, under its doctrine that exemplars calibrate form only, never facts.
6. The page's subsystem entry in `guidelines/reference/subsystems.md`.
7. The checking harness under `guidelines/rules/routines/` (ROUTINE-01, with ROUTINE-04's patterns and ROUTINE-05's recipes). The writer satisfies the factual PASS CRITERIA by construction and by the mechanical exit suite below, AND runs the mechanical sweeps (was Gate A) itself per ROUTINE-01's procedure — the prose view, the candidate patterns, and the figure sweep. Read ROUTINE-04 closely: its patterns are deliberately unanchored, and re-anchoring them reintroduces the blind spot that let a whole class ship for eight pages. A pattern belonging to a ban that an ON rewriter displaces still generates candidates; adjudicate those against the rewriter, and record them as EXEMPT naming it. The orchestrator re-runs the mechanical checks independently in pass 03 (`guidelines/passes/03-check.md`).

## Generate the page

Follow the template structure exactly. The page must contain these sections in order:

1. H1: the topic name (just the name, no extra text)
2. The AI-generated-content caution blockquote, immediately below the H1
3. A short summary paragraph with an ASCII diagram if appropriate
4. `## SUMMARY`
5. `## SPECIFICATIONS`
6. `## LINUX KERNEL`
7. `## KERNEL DOCUMENTATION`
8. `## OTHER SOURCES`
9. `## <section6_heading>` (from the subsystem's entry in `guidelines/reference/subsystems.md`; omit entirely if set to "none")
10. `## DETAILS`

## Parity bookkeeping while composing

Maintain the catalog-to-DETAILS parity checklist as the page is composed: one row per LINUX KERNEL catalog symbol, recording where DETAILS reproduces its definition as a fenced ` ```c ` block and where it shows a concrete caller or usage as code — the two evidence columns of the parity criteria (PAGE-02; was Gate B item 1). The table lives in the dossier's PARITY section (`guidelines/passes/dossier.md`); close it before reporting the page written. It is not a file of its own. Catalog a symbol only when both of its cells can be filled; a symbol the page will not excerpt is mentioned and linked in prose without a catalog bullet. At exit every row is filled or its symbol has been de-cataloged (fill-or-decatalog): there is no deliberately-empty state, and each de-cataloging is named in the writer's final report.

This is construction bookkeeping — tracking coverage forward while writing, the same duty class as the FACT-03 enumerations — not a style sweep. The check pass audits the table independently against the page; a checklist entry is a hint, never evidence (the same relationship the dossier has). The checklist exists because parity holes that survive the writer cost a follow-up round-trip an order of magnitude more expensive than the missing excerpts themselves.

## Mechanical exit suite (run before reporting done)

After the page is complete, the writer verifies its own work with the procedures below and fixes what they find before reporting. **They cover the facts AND the prose**, and they are reliable in the writer's own hands for one reason: they are mechanical. They never ask the writer to NOTICE anything — they ask it to run a procedure and dispose of what the procedure returns.

That distinction is the whole basis of this pass, and it was measured. A writer on this pipeline composed twenty label-colon violations while believing it was writing under BAN-02 (was 7a), re-read its own page twice, and saw none of them — then ran the ROUTINE-01 prose view and fixed all twenty. Its own account: "writer-blindness is real and total. The sweep worked on my own prose, but only because it is mechanical, not because I got better at seeing." The same asymmetry is why a writer's byte-comparison finds its own fabricated excerpts while a third re-reading never does. **Perception fails on your own work; procedure does not.** So the writer runs the sweeps, and an earlier rule forbidding it from doing so is withdrawn.

**Validate every helper script before you believe a clean result from it.** A zero-defect report is only as good as the tool that produced it, and two independent failure modes have already produced false clean runs on this pipeline. First, negative-control it: inject a known defect (flip a character in an excerpt, shift a provenance line by one) and confirm the checker reports it — several writers caught real fabrications this way only after proving their checker could fail. Second, cross-check the script's headline count against a trivially independent one (`grep -c '^```c'`, an `awk` tally) before trusting a zero. A writer's excerpt verifier was silently OVERWRITTEN by a sibling's script in the shared scratchpad and reported 75 blocks / 81 units against a true 71 / 77; the counts disagreeing with a one-line `grep` is what exposed it. A tool that cannot be shown to fail, and whose totals nobody cross-checked, has not verified anything.

1. Excerpts: byte-compare every fenced ` ```c ` unit against its provenance file at the cited line (tabs included; an interior `/* path:line */` delimiter starts a new unit, a standalone `...` line is a declared elision). Every unit begins at its cited line. Watch for AMBIGUOUS ELISIONS: a `...` resynchronizes on the next literal line, so if that line occurs more than once in the source file the unit can silently re-anchor at the wrong place. Where that is possible, split the block into two provenance-delimited units instead of relying on the elision to land.
2. Anchors: **do not hand-build the anchor table — emit it.** Run the extractor below over the finished page; it produces the dossier's LINKS table mechanically, one row per distinct inline span, with the URL and the disk line at that URL already fetched, and each span tagged `prose` (the lead paragraph, SUMMARY, and DETAILS — the closure region of item 6) or `catalog` (the reference sections). The reason this step is a script and not a transcription: every LINKS-table defect in this corpus was a completeness failure — a dropped row, an omitted half of the table, a whole table never written — and a script cannot drop a row it is emitting. You then JUDGE, you do not TRANSCRIBE: for each linked row confirm the printed disk line is the right target (a symbol link on its definition line, a location link on the exact site the prose describes; PAGE-04, and PAGE-WAIVERS' rulings for `CONFIG_*`, generic primitives, and ops-struct members) and fill its `kind` (symbol / location / config / generated / file); item 6 fills the `reason` for the bare rows. This owns the same split as everything mechanical here — the script owns which-spans-exist, you own is-each-anchor-right.

    ```
    python3 - <output-path> <tree-root> <<'EOF'
    import re, sys, subprocess
    page, tree = sys.argv[1], sys.argv[2]
    CATALOG = ("## SPECIFICATIONS", "## LINUX KERNEL",
               "## KERNEL DOCUMENTATION", "## OTHER SOURCES")
    region, fence, spans, lineno = "prose", False, {}, 0   # before the first ## is H1 + caution + lead = prose
    def note(span, region, url=None, at=0):
        cur = spans.setdefault(span, {"region": region, "url": None,
                                      "n_linked": 0, "n_bare": 0, "bare_at": []})
        if region == "prose": cur["region"] = "prose"      # prose is the stricter obligation
        if url:
            cur["n_linked"] += 1
            if not cur["url"]: cur["url"] = url
        else:
            cur["n_bare"] += 1
            if region == "prose" and len(cur["bare_at"]) < 6: cur["bare_at"].append(at)
    for line in open(page, encoding="utf-8"):
        line = line.rstrip("\n"); lineno += 1
        if line.startswith("```"): fence = not fence; continue
        if fence: continue
        if line.startswith("## "):
            region = "catalog" if line.strip() in CATALOG else "prose"; continue
        for m in re.finditer(r"\[`([^`]+)`\]\(([^)]+)\)", line):    # linked spans
            note(m.group(1), region, m.group(2), lineno)
        for m in re.finditer(r"`([^`\n]+)`", re.sub(r"\[`[^`]+`\]\([^)]*\)", " ", line)):  # bare
            note(m.group(1), region, None, lineno)
    print("| span | region | linked | bare | bare at | anchor URL | disk line | kind / reason |")
    print("|---|---|---|---|---|---|---|---|")
    for span in sorted(spans, key=str.lower):
        r = spans[span]; url = r.get("url"); disk = ""
        if url:
            mm = re.search(r"/source/([^#]+)#L(\d+)", url)
            if mm:
                out = subprocess.run(["sed", "-n", f"{mm.group(2)}p", f"{tree}/{mm.group(1)}"],
                                     capture_output=True, text=True).stdout.strip()
                disk = (out[:48] + "…") if len(out) > 48 else out
        at = " ".join(str(n) for n in r["bare_at"])
        print(f"| `{span.replace('|', chr(92)+'|')}` | {r['region']} | "
              f"{r['n_linked']} | {r['n_bare']} | {at} | {url or ''} | {disk} | |")
    EOF

    The `linked` and `bare` columns are OCCURRENCE COUNTS, not a yes/no, and
    `bare at` gives the prose line numbers of the bare ones. This matters: a span
    linked once and left bare five times later is a real PAGE-04 defect, and an earlier
    version of this extractor keyed its table by span text alone, so those repeats
    collapsed into a single "linked: yes" row and became structurally invisible.
    Three writers on one batch each hit it, each hand-rolled a per-occurrence scan
    to work around it, and between them those scans found 25 defects this table
    could not show. Any row with a non-zero `bare` count in the `prose` region
    needs its bare occurrences resolved — linked, or covered by a waiver —
    even when the same span is linked elsewhere on the page.

    Judge these rows; do not mass-link them. The commonest shape by far is a
    DENSE REFERENCE TABLE — a census or semantics table whose first column is a
    bare symbol name, with that symbol linked in the prose that introduces the
    table. On one measured page 72 of these appeared and the large majority were
    that shape. That shape is NO LONGER an open adjudication: it was settled on
    2026-09-01 against exemption, and the ruling is in the page directory's
    waivers file. Every occurrence in such a table is linked, exactly as in
    flowing prose, because this corpus carries no cross-page links and an
    unlinked symbol in a table is a dead end for a reader who landed mid-table.
    Density is the accepted cost. A bare occurrence in flowing prose is, as
    before, a plain PAGE-04 defect and gets linked.
    ```
3. Parity closure: confirm every catalog symbol appears in at least one fenced block and the dossier's PARITY table has zero empty rows (fill-or-decatalog above). Check every CELL, not the ratio: pages have cleared the 1.0 blocks-per-entry floor comfortably and still carried empty definition cells.
4. Counts: re-derive every count and every "only"/"never"/"always"/"exactly" enumeration with a search basis shaped differently from the one used during research — a repeated identical grep repeats the same miss — and reconcile, or fix the sentence to what the enumeration shows (FACT-03). This has changed a published number on every page it has been run against.
5. Cited examples: for each driver or consumer file cited as an example, confirm a substantive commit within roughly three years (`git log -1` on the file).
6. **Span closure (PAGE-04), over the prose region.** The extractor in item 2 emits one row per distinct span WITH per-occurrence counts, so the inventory is complete at the occurrence level — but only because of those counts. Read the row's `bare` column, never its existence: a span linked once and bare four times later is four defects behind a row that would otherwise read as resolved, and that is exactly the class an earlier deduped version of this table hid. What remains is judgment, and it has a defined scope: **every `prose` row must resolve, and a row with a non-zero `bare` count is not resolved until each of those occurrences is.** A row whose occurrences are all linked resolves by its `kind`, filled in item 2. A bare occurrence resolves only when you fill the `reason` with the waiver that licenses leaving it unlinked (literal, path string, Kconfig fragment, commit hash, local/parameter/goto label quoted from an excerpt, symbol verified ABSENT from the tree, or a value/expression span whose constituents are each linked elsewhere) — or, if none applies, it is a real bare-span defect and you link it, which moves it to a `yes` row on the next extract. **A `prose` row with an empty `kind / reason` cell is the defect this check exists to surface**, and it is the biggest single class in this corpus (a fresh-eyes stage once linked ninety-one bare spans across five pages). `catalog` rows are out of closure scope for now — the reference sections carry their own coverage through the PARITY table, and extending closure to them is a later step. Anchor confirmation from item 2 stays page-wide regardless: a wrong URL in a catalog row is still a defect.
7. **The prose sweep (ROUTINE-01; was Gate A).** Build the prose view, run every candidate pattern against it, and adjudicate each hit against the waivers BEFORE touching anything — a hit on an exempt construct is a false candidate, and rewording a compliant phrase to silence a pattern is itself a defect. Fix the settled classes with the ROUTINE-05 recipes; escalate anything unsettled rather than deciding it yourself. Then run ROUTINE-01's figure sweep over the non-` ```c ` fenced blocks, which the prose view cannot see and which BAN-01 still governs. Then the classes no pattern expresses: BAN-03 list shapes, BAN-04 superlatives judged in context, heading shape, and figure geometry.
8. **Excerpt explanation (PAGE-07).** Run PAGE-07's generator over the raw file. It prints, per definition excerpt, the members the two adjacent paragraphs name and the ones they do not; a block with zero members named is a defect, an unnamed member is covered only by a group phrase the paragraph takes from the excerpt's own comments, and a paragraph that names the members but only counts or places them ("the first five fields", "adjacent fields", "a few fields further down") is a defect the generator cannot see, so read the paragraph beside every excerpt for it. The fix is never a shorter excerpt that hides the members: write the member sentences from the research you already hold (the dossier's SYMBOLS and USAGE rows, the field table if the page carries one), or elide the excerpt to the members the paragraph explains and say what the elision drops. This class was invisible to the suite until 2026-09-02, and two batches shipped with half their definition excerpts unexplained; the field purposes were on those pages, in tables in another section, and the paragraph beside each excerpt said how many fields the construction pass writes.
9. **Re-run after fixing.** Your own fixes introduce defects. A writer on this pipeline introduced two wrong anchors DURING its fix round and caught them only by re-running; another silently scrambled four paragraphs with an automated link substitution. After any fix, re-run items 1, 2, 7 and 8 over every paragraph you touched.
10. Persist the evidence: append the suite's outcomes to the dossier's EVIDENCE section (`guidelines/passes/dossier.md`) — every count and universal claim with its two derivation bases and reconciled result, the excerpt-unit and anchor-confirmation tallies, the span-closure result, the excerpt-explanation list (per definition block, members shown, members named, and the group phrase covering each unnamed member), and the sweep candidate counts per class with their dispositions (was the Gate A record) — so the check pass re-derives from recorded bases instead of reconstructing them.

When you adjudicate a candidate in your own prose you will want to defend it. Write the verdict down before you act on it: the sweep does not stop a writer wanting to defend its prose, it stops the defence from being silent, and "it reads well" is visibly not a waiver ruling once it is on the page next to one.

Claims that are not disk-settleable (intent, motivation, anything the tree at the documented version cannot witness) are never left as bare assertions: scope them out, weaken them to what the evidence shows (FACT-03), or state them with their basis disclosed (PAGE-03, PAGE-05). The writer's report lists this class explicitly; "could not verify" is reserved for it — a disk-settleable claim is settled or dropped, never reported unverified.

## Composing stance

The exemplar pages under `docs/sound/` are the worked examples. The one or two read in the prep pass (`guidelines/passes/00-prep.md`) set the standard for the lead, the journey or model organization of DETAILS, the figures, and above all the paragraph beside each excerpt; match them there, and match the rules wherever a sound page predates one (`00-prep.md` names the three known gaps). The examples in the rule files use ACPI, mm, and sound symbols; they illustrate the rule mechanic, which applies unchanged to every subsystem. Write the paragraph beside each excerpt as the explanation of that excerpt (PAGE-07): what each member it shows holds and who writes or reads it, what the shown lines of a function do. A sentence that names what the excerpt is about to show may end in the colon that introduces it; a paragraph that counts the members or says where they sit explains nothing. Where the members are many, cut the excerpt into several and explain each. All generated content must follow the rules as it is composed; the ROUTINE-05 recipes (`guidelines/rules/routines/ROUTINE-05.md`) exist so compliant phrasing never has to be re-derived per hit, and the waivers files settle the boundary cases in advance.

## Dispatching a writer (campaign brief)

Role: researches, writes, and fact-verifies one complete page (passes 01 and 02). The writer owns everything disk-settleable on its page — catalog-to-DETAILS parity, excerpt verbatimness, link-anchor correctness, counts, and behavioral claims — and leaves no substantive holes: a page is not reported written until the parity table has zero empty rows (fill-or-decatalog) and the mechanical exit suite above has run clean with its evidence persisted. The writer runs the ROUTINE-01 sweeps on its own prose as part of the exit suite (item 7) — the sweeps are procedure, not perception, and survive self-application (the measurement is in `guidelines/passes/03-check.md`); the orchestrator re-runs every mechanical check independently in pass 03 and applies every residual itself. Model tier: the strongest available model; page writing needs research judgment, prose discipline, and figure quality. On death, resume the same agent first ("do not redo the research; write the page now from what you have"); if repeated resumes fail, a fresh agent starts from the page's dossier, its parity table, and the campaign spec.

Fill the brackets from the campaign spec (the spec is machine-portable; the absolute paths below are composed at dispatch time from the local environment). The brief names the files that carry every house rule, as absolute paths; a writer must never have to guess where a rule lives.

```
Write the page <output path> for the <subsystem> knowledge base.

SKILL_DIR: <absolute path to the kernel-glossary-skill checkout>

MANDATORY READING, in order, before any research or writing. Every house
rule lives in these files and nothing is pasted into this brief, so a
skipped read is a skipped rule set.
1. The five waivers files — <SKILL_DIR>/guidelines/rules/bans/BAN-WAIVERS.md,
   page/PAGE-WAIVERS.md, facts/FACT-WAIVERS.md, plots/PLOT-WAIVERS.md,
   diagrams/DIAG-WAIVERS.md — the settled waivers and rulings. First
   action, all five. Apply them as written; never reword an exempt
   construct.
2. <SKILL_DIR>/guidelines/passes/00-prep.md — template and exemplar
   doctrine. Read the one or two docs/sound/ pages it names for this
   page's archetype, in full, before writing (exemplars calibrate form
   only, never facts; the rules govern where a sound page predates one).
3. <SKILL_DIR>/guidelines/passes/01-research.md and
   <SKILL_DIR>/guidelines/passes/dossier.md — the research procedure and
   the dossier you keep at <SKILL_DIR>/progress/<campaign>/<slug>.dossier.md.
4. <SKILL_DIR>/guidelines/passes/02-write.md — the composition procedure,
   the full writer reading list (the rules via
   <SKILL_DIR>/guidelines/rules/INDEX.md, the diagram rules DIAG-01 through
   DIAG-04 among them, the depth rules in
   <SKILL_DIR>/guidelines/reference/measured-criteria.md), the parity
   bookkeeping, and the mechanical exit suite you run before reporting
   done. Read everything that list names.
5. The rule corpus under <SKILL_DIR>/guidelines/rules/ — you own
   satisfying the factual PASS CRITERIA by construction and by the exit
   suite (PAGE-02 parity and grounded code, PAGE-04 links, FACT-01
   coverage, FACT-02 driver recency, FACT-03 behavioral claims), and a
   factual defect that survives you costs a follow-up round. You also run the
   ROUTINE-01 sweeps on your own prose — exit-suite item 7; the
   orchestrator re-runs every mechanical check independently after you
   report.
6. <SKILL_DIR>/guidelines/reference/subsystems.md — read only the page's
   subsystem entry.

MISSION. <Scope statement from the catalog row, naming the anchor symbols
with file:line hints.> <The boundary rules for this page's cluster: what
this page owns, what each sibling page owns, the seam symbols. Recap of
sibling territory is limited to one short paragraph.>

CAMPAIGN FACTS (carried by this brief because no guideline file can):
- Documented tree: <path>, version <tag>, commit <sha>. Every fact, line
  number, and excerpt is verified against the on-disk tree before it
  lands; semcode results and the dossier are hints, the disk is ground
  truth. Architecture scope: <arch>. State CONFIG assumptions in the page
  where behavior depends on them: <list>.
- Section 6 heading for this subsystem: <value or "omit">.
- Exemplar pages for this page's archetype, from 00-prep.md: <one or two
  docs/sound/ paths>. Read them in full before writing; form only, never
  facts.
- Project-specific bans and amendments from the campaign spec: <list, or
  "none">.
- <If an existing draft or prior page feeds this one: the source file(s)
  and sections to mine, the known source defects from the reuse map;
  PLOT-04 applies (inventory the source, give every item a kept/merged/cut
  disposition, report every cut and shrink the catalog and scope
  statement with it). Otherwise omit this bullet.>

DIRECTIVES.
- Run the research pass yourself (pass 01), keeping the dossier current
  as you research; it is the recovery point if you die mid-page.
- The ONLY file you write besides the page is your dossier at
  <SKILL_DIR>/progress/<campaign>/<slug>.dossier.md. The parity table and
  your exit-suite evidence are SECTIONS OF IT, not files beside it. Write
  nowhere else in progress/, which belongs to other runs too; helper
  scripts and scratch go in your scratchpad directory, under a
  subdirectory named for this page's slug. The session scratchpad is
  SHARED with the other writers dispatched alongside you: a generically
  named file is overwritten or read back merged with a sibling's data,
  which has already caused one writer to run its anchor review against a
  contaminated LINKS table. Namespace every file you write there.
- Enumerate call-site populations before writing any prose that counts or
  characterizes them (FACT-03).
- Keep the parity checklist as you compose and close it before you
  finish: one row per LINUX KERNEL catalog symbol, two cells — where
  DETAILS shows its definition excerpt, where it shows a concrete usage
  excerpt. At exit every row is filled or its symbol is de-cataloged to a
  prose mention with a link (fill-or-decatalog; there is no
  deliberately-empty state). The table is the dossier's PARITY section.
- Run the mechanical exit suite (02-write.md) after the page is complete
  and fix what it finds before reporting: byte-compare every excerpt
  unit against the tree; print and confirm the disk line behind every
  link anchor; confirm every catalog symbol appears in at least one
  fenced block and the parity table has zero empty rows; re-derive every
  count with a search basis shaped differently from the one used while
  researching; confirm cited example files carry a recent substantive
  commit; persist the evidence into the dossier's EVIDENCE section.
- RUN the ROUTINE-01 sweeps on your own prose (exit-suite item 7). This
  is new: an earlier version of this pass forbade it. The ban was wrong
  for the mechanical classes — measured, a writer using the ROUTINE-01
  prose view fixed
  32 of 35 prose defects in its own draft, including 20 label-colons it
  had re-read twice without seeing. Adjudicate every candidate against
  the waivers and WRITE THE VERDICT DOWN before acting; escalate what
  you are unsure of rather than deciding it yourself.
- Close the span inventory against your LINKS table (exit-suite item 6).
  Every inline code span in prose is either linked from the table or has
  an `exempt` row with its waiver reason. There is no third state.
- Write the file to <output path>. Your final message is a short
  evidence report: sections written; catalog symbol count and the
  parity-table outcome (rows filled, symbols de-cataloged with one-line
  reasons); exit-suite results (excerpt units verified, anchors
  confirmed, counts re-derived with their second bases); the waiver
  ruling count you applied as proof of the waivers read; and any claim that is
  not disk-settleable, stated with how the page scopes, weakens, or
  discloses it ("could not verify" is reserved for that class — a
  disk-settleable claim is settled or dropped, never reported
  unverified). Not the page text.
```
