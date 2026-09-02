# Pass 02: write

Purpose: compose the complete page, then verify it, facts and prose, with the mechanical exit suite before reporting done.
Inputs: the dossier (pass 01) and the resolved parameters (pass 00); every dossier fact is re-verified on disk before it lands, because the tree at the documented version is the only ground truth.
Outputs: the page at `docs/<dir>/<topic-slug>.md`, and the dossier with its PARITY table closed and its LINKS, EVIDENCE and LINT sections written. Page state after this pass: WRITTEN.
Run by: single-agent mode inline; in a campaign a dispatched writer agent (brief at the end of this file), on the strongest available model.
Next: pass 03 (`guidelines/passes/03-check.md`), the orchestrator's independent re-run of the same checks.

Rules are cited by stable ID; `guidelines/rules/INDEX.md` maps every ID to its file.

## Reading list, before composing

1. `guidelines/rules/WRITING.md`: what a page is for. Read it first and compose under it from the first sentence.
2. `guidelines/rules/BANS.md`: what is trimmed from every sentence, with each ban's fix and exemptions.
3. The page and fact rules: `guidelines/rules/page/PAGE-01.md` through `PAGE-06.md` and `guidelines/rules/facts/FACT-01.md` through `FACT-04.md`; `guidelines/rules/plots/PLOT-04.md` only when the page derives from existing material.
4. `guidelines/reference/TEMPLATE-FULL.md`, the page's entry in `guidelines/reference/subsystems.md`, and the one or two `docs/sound/` exemplar pages pass 00 chose (`guidelines/passes/00-prep.md`; form only, never facts).
5. `guidelines/reference/measured-criteria.md`: the depth rules, the coverage tripwires and the excerpt criteria.
6. The figure rules under `guidelines/rules/diagrams/`, only when the page will carry a figure: DIAG-01 and DIAG-02 always govern one, DIAG-03 and DIAG-04 are the catalogs.
7. `guidelines/reference/rewriters.md`: the table only, unless it says a rewriter is ON.

The checking harness (`guidelines/rules/routines/`, `guidelines/rules/WAIVERS.md`, `guidelines/passes/dossier.md`) is read at the exit suite below, not before composing.

## Generate the page

Follow the template exactly. The page contains these sections in order:

1. H1: the topic name (just the name, no extra text)
2. The AI-generated-content caution blockquote, immediately below the H1
3. The lead, with an ASCII figure if the material earns one
4. `## SUMMARY`
5. `## SPECIFICATIONS`
6. `## LINUX KERNEL`
7. `## KERNEL DOCUMENTATION`
8. `## OTHER SOURCES`
9. `## <section6_heading>` (from the subsystem's entry; omit entirely if set to "none")
10. `## DETAILS`

## Parity bookkeeping while composing

Keep the catalog-to-DETAILS checklist as you compose: one row per LINUX KERNEL catalog symbol, two cells, where DETAILS reproduces its definition as a fenced ` ```c ` block and where it shows a concrete usage as code (PAGE-02). It lives in the dossier's PARITY section. Catalog a symbol only when both cells can be filled; a symbol the page will not excerpt is mentioned and linked in prose without a catalog bullet. At exit every row is filled or its symbol is de-cataloged, and each de-cataloging is named in the final report; there is no deliberately-empty state.

## Mechanical exit suite (run before reporting done)

Read the harness now: `guidelines/rules/routines/ROUTINE-01.md` (protocol, prose view, figure sweep), `ROUTINE-04.md` (candidate generators), `ROUTINE-07.md` (figure geometry), `guidelines/rules/WAIVERS.md`, and `guidelines/passes/dossier.md`. The suite covers facts and prose, and it works in your own hands because it is procedure, not perception: you run each item and dispose of what it returns. Validate every helper script before believing a clean result from it, by injecting a known defect and confirming it is reported, and by cross-checking its headline count against a one-line grep. Name every scratch file for this page's slug; the session scratchpad is shared with other writers.

1. Excerpts. Byte-compare every fenced ` ```c ` unit against its provenance file at the cited line, tabs included; an interior `/* path:line */` delimiter starts a new unit and a standalone `...` line is a declared elision. Every unit begins at its cited line. Where a `...` resynchronizes on a line that occurs more than once in the file, split the block into two provenance-delimited units instead.
2. Anchors. Do not hand-build the anchor table; emit it with the extractor below, one row per distinct inline span with its URL and the disk line at that URL, each span tagged `prose` or `catalog`. Then judge, row by row: a symbol link lands on its definition line, a location link on the site the prose describes (PAGE-04, WAIVERS.md), and the `kind / reason` column is filled as you go, `kind` for a linked row (symbol, location, config, generated, file) and `reason` for a bare one. Persist the filled table into the dossier's LINKS section.

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
    ```

    The `linked` and `bare` columns are occurrence counts: a span linked once and bare four times later is four defects, and every `prose` row with a bare count needs each occurrence resolved, linked or covered by a WAIVERS.md exemption. A dense reference table is linked in every row (settled 2026-09-01). A bare span in flowing prose is linked.
3. Parity closure. Every catalog symbol appears in at least one fenced block and the PARITY table has zero empty rows; check every cell, not the ratio.
4. Counts. Re-derive every count and every "only", "never", "always", "exactly" enumeration with a search basis shaped differently from the one used during research, and reconcile or fix the sentence to what the enumeration shows (FACT-03).
5. Cited examples. Each driver or consumer file cited as an example carries a substantive commit within roughly three years (`git log -1`).
6. Span closure (PAGE-04). Every `prose` row of the LINKS table carries a non-empty `kind / reason` cell; a bare occurrence resolves only by a WAIVERS.md exemption or by linking it. `catalog` rows are covered by PARITY and are out of closure scope; anchor confirmation stays page-wide.
7. The sweeps. Build the prose view (ROUTINE-01), run every BANS pattern, and adjudicate each candidate against BANS' exemptions and WAIVERS.md before touching anything, writing the verdict down first; fix with BANS' fix column and escalate what you are unsure of. Then the figure sweep over the non-C fences, the raw-file greps for boldface and headings, and the read-throughs: list shapes, enumerations (ROUTINE-04 ranks the candidates), superlatives in context, heading shape, figure geometry (ROUTINE-07).
8. WRITING. Run ROUTINE-04's opener and member generators over the raw file and read every row they print: every leading paragraph for rule 1, the paragraph beside every excerpt for rule 3, function excerpts included. Read the DETAILS headings for the journey or model spine (rule 2). Count SUMMARY's tables and figures (rule 5).
9. Re-run after fixing. Your own fixes introduce defects; after any fix, re-run items 1, 2, 7 and 8 over every paragraph you touched.
10. Persist the evidence into the dossier's EVIDENCE and LINT sections: every count and universal claim with its two bases and reconciled result, the excerpt-unit and anchor tallies, the span-closure result, the WRITING lists (leading paragraphs with verdicts, per-excerpt members shown and named, the spine, the SUMMARY counts), and the sweep candidates per class with their dispositions.

Claims that are not disk-settleable (intent, motivation, anything the tree at the documented version cannot witness) are never left as bare assertions: scope them out, weaken them to what the evidence shows (FACT-03), or state them with their basis disclosed (PAGE-03, PAGE-05). The final report lists this class explicitly; "could not verify" is reserved for it, and a disk-settleable claim is settled or dropped.

## Dispatching a writer (campaign brief)

Role: researches, writes and verifies one complete page (passes 01 and 02), owning everything disk-settleable on it: parity, excerpt verbatimness, anchors, counts, behavioral claims, and the prose under WRITING and BANS. A page is not reported written until the PARITY table has zero empty rows and the exit suite has run clean with its evidence persisted. The orchestrator re-runs every mechanical check in pass 03 and applies every residual itself. Model tier: the strongest available. On death, resume the same agent first ("do not redo the research; write the page now from what you have"); if repeated resumes fail, a fresh agent starts from the dossier plus the campaign spec.

Fill the brackets from the campaign spec; the brief carries absolute paths composed at dispatch time.

```
Write the page <output path> for the <subsystem> knowledge base.

SKILL_DIR: <absolute path to the kernel-glossary-skill checkout>
WORKSPACE: <SKILL_DIR>/progress/<campaign>/
YOUR DOSSIER: <SKILL_DIR>/progress/<campaign>/<slug>.dossier.md
YOUR SCRATCH: <session scratchpad>/<slug>/ (the scratchpad is shared; write only here)

MANDATORY READING, in order, before any research or writing:
1. <SKILL_DIR>/guidelines/rules/WRITING.md, what a page is for. Compose under it from the first sentence.
2. <SKILL_DIR>/guidelines/rules/BANS.md, what is trimmed from every sentence.
3. <SKILL_DIR>/guidelines/passes/00-prep.md, the template and the docs/sound exemplar doctrine; read the one or two exemplar pages it names for this page's archetype, in full (form only, never facts).
4. <SKILL_DIR>/guidelines/passes/01-research.md and dossier.md, the research procedure and the dossier you keep.
5. <SKILL_DIR>/guidelines/passes/02-write.md, this file: the rest of the reading list, the parity bookkeeping, and the exit suite you run before reporting done. Read everything the list names.
6. <SKILL_DIR>/guidelines/reference/subsystems.md, the page's subsystem entry only.

MISSION. <Scope statement from the catalog row, naming the anchor symbols with file:line hints.> <The boundary rules for this page's cluster: what this page owns, what each sibling owns, the seam symbols, which sibling pages exist on disk.> Line numbers are hints; the disk is ground truth, and a hint you cannot reproduce is reported, never written around.

CAMPAIGN FACTS:
- Documented tree: <path>, version <tag>, commit <sha>. Architecture scope: <arch>. CONFIG assumptions to state where behavior depends on them: <list>.
- Section 6 heading: <value or "omit">.
- Exemplar pages for this archetype, from 00-prep.md: <one or two docs/sound/ paths>.
- Project-specific bans and amendments from the campaign spec: <list, or "none">.
- <Derivation source and known defects, if an existing page feeds this one; PLOT-04 applies. Otherwise omit.>

DIRECTIVES.
- Run the research pass yourself, keeping the dossier current; it is the recovery point.
- The only files you write are the page and your dossier. Nowhere else in progress/, never in guidelines/ or campaigns/. No git operation that changes state.
- If the output path exists when you are about to write, stop and report.
- Enumerate call-site populations before any prose that counts or characterizes them (FACT-03).
- Keep the parity checklist as you compose; fill or de-catalog every row.
- Run the exit suite after the page is complete and fix what it finds before reporting; persist the LINKS table with every kind / reason cell filled, and the EVIDENCE and LINT sections, into the dossier.
- Final message: the lead verbatim; sections written; catalog count and parity outcome (de-catalogings with reasons); exit-suite results (units verified, anchors confirmed, counts with second bases, the ROUTINE-04 footers, SUMMARY counts, sweep candidates per class with dispositions); the exemptions applied; any hint that did not reproduce; any claim that is not disk-settleable and how the page scopes it. Not the page text beyond the lead.
```
