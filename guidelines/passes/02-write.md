# Pass 02: write

Purpose: compose the complete page following every writing rule, then verify it — facts AND prose — with the mechanical exit suite before reporting done.
Inputs: the dossier (pass 01) and the resolved parameters (pass 00); every dossier fact is re-verified on disk before it lands, because the tree at the documented version is the only ground truth.
Outputs: the draft page at `docs/<dir>/<topic-slug>.md`, and the dossier updated — its PARITY table closed and its EVIDENCE section written, plus any research entry the disk disagreed with corrected. Page state after this pass: WRITTEN.
Run by: single-agent mode inline; in a campaign a dispatched writer agent (brief at the end of this file), on the strongest available model.
Next: pass 03 (`guidelines/passes/03-check.md`), the orchestrator's independent mechanical check. The writer owns the page end to end — facts and prose — and closes the PARITY table, runs the full exit suite below (which now includes the Gate A sweeps), and persists its evidence before reporting. Page state after this pass: WRITTEN. It stays uncertified until a verify campaign signs it off (`guidelines/passes/04-verify.md`).

Rules are cited by stable ID; `guidelines/rules/INDEX.md` maps every ID to its file.

## Reading list (mandatory, in order)

This pass owns the writer's reading list; the writer brief points here instead of restating rules.

1. `guidelines/rules/7r-adjudications.md`, the settled adjudications registry, then `guidelines/rules/rules.md`, which carries every writing rule and every gate in one file (7p applies additionally whenever the page derives from existing material).
2. `guidelines/rules/diagrams.md`, but only when the page will carry a figure: 7g's principles always govern one, and 7h and 7i hold the figure catalogs (choose the shape from 7i's use-case index). A page with no figure needs none of it.
3. `guidelines/reference/measured-criteria.md`: the depth rules and tripwires that define what "in-depth, fine-grained" measures as.
4. The sample pages chosen in pass 00 (`guidelines/passes/00-prep.md`), under its doctrine that samples calibrate form only, never facts.
5. The page's subsystem entry in `guidelines/reference/subsystems.md`.
6. `guidelines/rules/rules.md`, the gates. The writer satisfies Gate B's factual items (3b) by construction and by the mechanical exit suite below, AND runs Gate A (3a) itself per 3c's procedure — the prose view, the candidate patterns, and the figure sweep. Read 3c closely: its patterns are deliberately unanchored, and re-anchoring them reintroduces the blind spot that let a whole class ship for eight pages. The orchestrator re-runs the mechanical checks independently in pass 03 (`guidelines/passes/03-check.md`), and a verify campaign re-runs the whole gate later on a different tree or a different model (`guidelines/passes/04-verify.md`).

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

Maintain the catalog-to-DETAILS parity checklist as the page is composed: one row per LINUX KERNEL catalog symbol, recording where DETAILS reproduces its definition as a fenced ` ```c ` block and where it shows a concrete caller or usage as code — the two evidence columns of Gate B item 1. The table lives in the dossier's PARITY section (`guidelines/passes/dossier.md`); close it before reporting the page written. It is not a file of its own. Catalog a symbol only when both of its cells can be filled; a symbol the page will not excerpt is mentioned and linked in prose without a catalog bullet. At exit every row is filled or its symbol has been de-cataloged (fill-or-decatalog): there is no deliberately-empty state, and each de-cataloging is named in the writer's final report.

This is construction bookkeeping — tracking coverage forward while writing, the same duty class as the 7o enumerations — not a style sweep. The verify pass audits the table independently against the page; a checklist entry is a hint, never evidence (the same relationship the dossier has). The checklist exists because parity holes that survive the writer cost a follow-up round-trip an order of magnitude more expensive than the missing excerpts themselves.

## Mechanical exit suite (run before reporting done)

After the page is complete, the writer verifies its own work with the procedures below and fixes what they find before reporting. **They cover the facts AND the prose**, and they are reliable in the writer's own hands for one reason: they are mechanical. They never ask the writer to NOTICE anything — they ask it to run a procedure and dispose of what the procedure returns.

That distinction is the whole basis of this pass, and it was measured. A writer on this pipeline composed twenty label-colon violations while believing it was writing under 7a, re-read its own page twice, and saw none of them — then ran the 3c prose view and fixed all twenty. Its own account: "writer-blindness is real and total. The sweep worked on my own prose, but only because it is mechanical, not because I got better at seeing." The same asymmetry is why a writer's byte-comparison finds its own fabricated excerpts while a third re-reading never does. **Perception fails on your own work; procedure does not.** So the writer runs the sweeps, and an earlier rule forbidding it from doing so is withdrawn.

1. Excerpts: byte-compare every fenced ` ```c ` unit against its provenance file at the cited line (tabs included; an interior `/* path:line */` delimiter starts a new unit, a standalone `...` line is a declared elision). Every unit begins at its cited line.
2. Anchors: **do not hand-build the anchor table — emit it.** Run the extractor below over the finished page; it produces the dossier's LINKS table mechanically, one row per distinct inline span, with the URL and the disk line at that URL already fetched, and each span tagged `prose` (the lead paragraph, SUMMARY, and DETAILS — the closure region of item 6) or `catalog` (the reference sections). The reason this step is a script and not a transcription: every LINKS-table defect in this corpus was a completeness failure — a dropped row, an omitted half of the table, a whole table never written — and a script cannot drop a row it is emitting. You then JUDGE, you do not TRANSCRIBE: for each linked row confirm the printed disk line is the right target (a symbol link on its definition line, a location link on the exact site the prose describes; 7m, and the 7r rulings for `CONFIG_*`, generic primitives, and ops-struct members) and fill its `kind` (symbol / location / config / generated / file); item 6 fills the `reason` for the bare rows. This owns the same split as everything mechanical here — the script owns which-spans-exist, you own is-each-anchor-right.

    ```
    python3 - <output-path> <tree-root> <<'EOF'
    import re, sys, subprocess
    page, tree = sys.argv[1], sys.argv[2]
    CATALOG = ("## SPECIFICATIONS", "## LINUX KERNEL",
               "## KERNEL DOCUMENTATION", "## OTHER SOURCES")
    region, fence, spans = "prose", False, {}   # before the first ## is H1 + caution + lead = prose
    def note(span, region, url=None):
        cur = spans.get(span)
        if cur is None: spans[span] = {"region": region, "url": url}; return
        if region == "prose": cur["region"] = "prose"      # prose is the stricter obligation
        if url and not cur.get("url"): cur["url"] = url
    for line in open(page, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("```"): fence = not fence; continue
        if fence: continue
        if line.startswith("## "):
            region = "catalog" if line.strip() in CATALOG else "prose"; continue
        for m in re.finditer(r"\[`([^`]+)`\]\(([^)]+)\)", line):    # linked spans
            note(m.group(1), region, m.group(2))
        for m in re.finditer(r"`([^`\n]+)`", re.sub(r"\[`[^`]+`\]\([^)]*\)", " ", line)):  # bare
            note(m.group(1), region, None)
    print("| span | region | linked | anchor URL | disk line | kind / reason |")
    print("|---|---|---|---|---|---|")
    for span in sorted(spans, key=str.lower):
        r = spans[span]; url = r.get("url"); disk = ""
        if url:
            mm = re.search(r"/source/([^#]+)#L(\d+)", url)
            if mm:
                out = subprocess.run(["sed", "-n", f"{mm.group(2)}p", f"{tree}/{mm.group(1)}"],
                                     capture_output=True, text=True).stdout.strip()
                disk = (out[:48] + "…") if len(out) > 48 else out
        print(f"| `{span.replace('|', chr(92)+'|')}` | {r['region']} | "
              f"{'yes' if url else 'no'} | {url or ''} | {disk} | |")
    EOF
    ```
3. Parity closure: confirm every catalog symbol appears in at least one fenced block and the dossier's PARITY table has zero empty rows (fill-or-decatalog above). Check every CELL, not the ratio: pages have cleared the 1.0 blocks-per-entry floor comfortably and still carried empty definition cells.
4. Counts: re-derive every count and every "only"/"never"/"always"/"exactly" enumeration with a search basis shaped differently from the one used during research — a repeated identical grep repeats the same miss — and reconcile, or fix the sentence to what the enumeration shows (7o). This has changed a published number on every page it has been run against.
5. Cited examples: for each driver or consumer file cited as an example, confirm a substantive commit within roughly three years (`git log -1` on the file).
6. **Span closure (7m), over the prose region.** The extractor in item 2 already emitted one row per span, so the inventory is complete by construction — there is no "did I list every span" step to get wrong. What remains is judgment, and it has a defined scope: **every `prose` row must resolve.** A `prose | yes` (linked) row resolves by its `kind`, filled in item 2. A `prose | no` (bare) row resolves only when you fill its `reason` with the 7r exemption that licenses leaving it unlinked (literal, path string, Kconfig fragment, commit hash, local/parameter/goto label quoted from an excerpt, symbol verified ABSENT from the tree, or a value/expression span whose constituents are each linked elsewhere) — or, if none applies, it is a real bare-span defect and you link it, which moves it to a `yes` row on the next extract. **A `prose` row with an empty `kind / reason` cell is the defect this check exists to surface**, and it is the biggest single class in this corpus (a fresh-eyes stage once linked ninety-one bare spans across five pages). `catalog` rows are out of closure scope for now — the reference sections carry their own coverage through the PARITY table, and extending closure to them is a later step. Anchor confirmation from item 2 stays page-wide regardless: a wrong URL in a catalog row is still a defect.
7. **Gate A prose sweep (3c).** Build the prose view, run every candidate pattern against it, and adjudicate each hit against 7r BEFORE touching anything — a hit on an exempt construct is a false candidate, and rewording a compliant phrase to silence a pattern is itself a defect. Fix the settled classes with the 7q recipes; escalate anything unsettled rather than deciding it yourself. Then run 3c's figure sweep over the non-` ```c ` fenced blocks, which the prose view cannot see and which rule 7 still governs. Then the classes no pattern expresses: 7b list shapes, 7d superlatives judged in context, heading shape, and figure geometry.
8. **Re-run after fixing.** Your own fixes introduce defects. A writer on this pipeline introduced two wrong anchors DURING its fix round and caught them only by re-running; another silently scrambled four paragraphs with an automated link substitution. After any fix, re-run items 1, 2 and 7 over every paragraph you touched.
9. Persist the evidence: append the suite's outcomes to the dossier's EVIDENCE section (`guidelines/passes/dossier.md`) — every count and universal claim with its two derivation bases and reconciled result, the excerpt-unit and anchor-confirmation tallies, the span-closure result, and the Gate A candidate counts per class with their dispositions — so the check pass and any later verify pass re-derive from recorded bases instead of reconstructing them.

When you adjudicate a candidate in your own prose you will want to defend it. Write the verdict down before you act on it: the sweep does not stop a writer wanting to defend its prose, it stops the defence from being silent, and "it reads well" is visibly not a 7r ruling once it is on the page next to one.

Claims that are not disk-settleable (intent, motivation, anything the tree at the documented version cannot witness) are never left as bare assertions: scope them out, weaken them to what the evidence shows (7o), or state them with their basis disclosed (7l, 7n). The writer's report lists this class explicitly; "could not verify" is reserved for it — a disk-settleable claim is settled or dropped, never reported unverified.

## Composing stance

The sample pages under `guidelines/reference/samples/` embody every rule. The closest-matching sample read in the prep pass (`guidelines/passes/00-prep.md`) is the worked example; match its structure, diagram style, code-citation density, and depth. The examples in the rule files use ACPI and mm symbols; they illustrate the rule mechanic, which applies unchanged to every subsystem. All generated content must follow the rules as it is composed; the 7q recipes (`guidelines/rules/rules.md` (7q)) exist so compliant phrasing never has to be re-derived per hit, and the 7r registry settles the boundary cases in advance.

## Dispatching a writer (campaign brief)

Role: researches, writes, and fact-verifies one complete page (passes 01 and 02). The writer owns everything disk-settleable on its page — catalog-to-DETAILS parity, excerpt verbatimness, link-anchor correctness, counts, and behavioral claims — and leaves no substantive holes: a page is not reported written until the parity table has zero empty rows (fill-or-decatalog) and the mechanical exit suite above has run clean with its evidence persisted. What the writer does not run are the style sweeps; the lint-fix stage with fresh context does those better. Model tier: the strongest available model; page writing needs research judgment, prose discipline, and figure quality. On death, resume the same agent first ("do not redo the research; write the page now from what you have"); if repeated resumes fail, a fresh agent starts from the page's dossier, its parity table, and the plan file.

Fill the brackets from the plan file. The brief names the files that carry every house rule, as absolute paths; a writer must never have to guess where a rule lives.

```
Write the page <output path> for the <subsystem> knowledge base.

SKILL_DIR: <absolute path to the kernel-glossary-skill checkout>

MANDATORY READING, in order, before any research or writing. Every house
rule lives in these files and nothing is pasted into this brief, so a
skipped read is a skipped rule set.
1. <SKILL_DIR>/guidelines/rules/7r-adjudications.md — the settled
   adjudications registry. First action. Apply it as written; never
   reword an exempt construct.
2. <SKILL_DIR>/guidelines/passes/00-prep.md — template and samples
   doctrine (samples calibrate form only, never facts).
3. <SKILL_DIR>/guidelines/passes/01-research.md and
   <SKILL_DIR>/guidelines/passes/dossier.md — the research procedure and
   the dossier you keep at <SKILL_DIR>/progress/<campaign>/<slug>.dossier.md.
4. <SKILL_DIR>/guidelines/passes/02-write.md — the composition procedure,
   the full writer reading list (the rules via
   <SKILL_DIR>/guidelines/rules/INDEX.md, the diagram rules 7g-7i among
   them, the depth rules in
   <SKILL_DIR>/guidelines/reference/measured-criteria.md), the parity
   bookkeeping, and the mechanical exit suite you run before reporting
   done. Read everything that list names.
5. <SKILL_DIR>/guidelines/rules/rules.md — you own satisfying its
   factual items by construction and by the exit suite (1 parity,
   2 grounded code, 3 links, 6 coverage, 7 driver recency, 9 behavioral
   claims); a verify campaign re-runs the whole gate later, and a
   factual defect found there costs a follow-up round. Gate A and the
   style items stay with the lint-fix stage: do not run style sweeps on
   your own prose.
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
- Project-specific bans and amendments from the plan file: <list, or
  "none">.
- <If an existing draft or prior page feeds this one: the source file(s)
  and sections to mine, the known source defects from the reuse map; rule
  7p applies (inventory the source, give every item a kept/merged/cut
  disposition, report every cut and shrink the catalog and scope
  statement with it). Otherwise omit this bullet.>

DIRECTIVES.
- Run the research pass yourself (pass 01), keeping the dossier current
  as you research; it is the recovery point if you die mid-page.
- The ONLY file you write besides the page is your dossier at
  <SKILL_DIR>/progress/<campaign>/<slug>.dossier.md. The parity table and
  your exit-suite evidence are SECTIONS OF IT, not files beside it. Write
  nowhere else in progress/, which belongs to other runs too; helper
  scripts and scratch go in your own scratchpad directory.
- Enumerate call-site populations before writing any prose that counts or
  characterizes them (7o).
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
- RUN the Gate A sweeps on your own prose (exit-suite item 7). This is
  new: an earlier version of this pass forbade it. The ban was wrong for
  the mechanical classes — measured, a writer using 3c's prose view fixed
  32 of 35 prose defects in its own draft, including 20 label-colons it
  had re-read twice without seeing. Adjudicate every candidate against 7r
  and WRITE THE VERDICT DOWN before acting; escalate what you are unsure
  of rather than deciding it yourself.
- Close the span inventory against your LINKS table (exit-suite item 6).
  Every inline code span in prose is either linked from the table or has
  an `exempt` row with its 7r reason. There is no third state.
- Write the file to <output path>. Your final message is a short
  evidence report: sections written; catalog symbol count and the
  parity-table outcome (rows filled, symbols de-cataloged with one-line
  reasons); exit-suite results (excerpt units verified, anchors
  confirmed, counts re-derived with their second bases); the 7r ruling
  count you applied as proof of the registry read; and any claim that is
  not disk-settleable, stated with how the page scopes, weakens, or
  discloses it ("could not verify" is reserved for that class — a
  disk-settleable claim is settled or dropped, never reported
  unverified). Not the page text.
```
