# Checking a kernel-glossary page

A page is a set of claims, and the unverified claim is the error that reads well and survives every pattern. The writer runs every check on its own work, the orchestrator re-runs the mechanical ones and compares the answers, and the evidence lives in the dossier so a later pass starts from it. Scripts print candidates; reading decides.

## Before the first check [setup]

1. [setup.read-at-qa] Read this file and `guidelines/dossier.md` at QA time, after composing.
2. [setup.runner] `python3 tools/qa/kg.py check docs/<dir>/<group>/<slug>.md` runs all `qa` requirements in guideline order. Each rule reports its guideline location, FAIL violations, review work items and informational notes, including inventories and measurements. `--json` retains all findings and structured data; `--checklist` includes manual and unexecuted requirements. Zero findings is not a guideline PASS. `--only <rule-id>` selects checks and settles no page state; `kg where <slug>` locates the guideline, check and tests. `kg view` exposes `--prose`, `--raw`, `--spans-visible` and `--regions`; `kg table <page>` emits LINKS. The tree, dossier, baseline and campaign spec resolve by convention or `--tree`, `--dossier`, `--campaign` and `--spec`: the tree is the checkout three directories above the skill (`<tree>/.claude/skills/kernel-glossary-skill`); the dossier is found under `progress/*/` at the page's mirrored path and accepted by its HEADER; the baseline is the committed page at `HEAD` when it differs from the working copy, which the facts and arrangement rules compare against; the campaign spec is `campaigns/<dir>.md` for the page's top directory, so a campaign whose short name differs from that directory passes `--spec campaigns/<campaign>.md` at every check, the writer's QA runs and the check pass alike. The resolver checks the source version and cited-file cleanliness, meaning that the tree has no uncommitted change in a file the page cites and every cited path is tracked at the commit, and validates dossier identity. Missing required input makes the rule INCOMPLETE while preserving earlier findings; an engine error is reported separately. Exit 1 means a FAIL or engine/input error, 2 missing input without another failure, and 0 complete execution without FAIL; review work remains. A full run reports WRITTEN or LINTED from the current page and QA digests in LINT.
3. [setup.selftest] After changing a guideline or its check, run `python3 tools/qa/kg.py selftest --rule <id>` to execute that rule's test module, then `python3 tools/qa/kg.py selftest` for all bindings, rule tests, shared engine tests and reference figures. Missing or empty test modules, broken bindings and unknown IDs fail. Tests use inline pages and temporary source trees or dossiers, so no external kernel checkout or dossier is required. A page's findings still require reading, and a headline count is cross-checked against a one-line grep.
4. [setup.scratch-names] Keep every scratch file under the page's own subdirectory of the scratchpad, `<dir>/<group>/<slug>/`; the scratchpad is shared, and two groups of one subsystem may share a slug.

## The mechanical steps [steps]

1. [steps.excerpts] Excerpts. Byte-compare every fenced C unit against its provenance file at the cited line, tabs included. An interior provenance comment starts a new unit, a standalone `...` is a declared elision, and every unit begins at its cited line; content that matches elsewhere under a wrong line number is a finding, and a procedure that resynchronizes after a mismatch is worse than none. A declared elision resynchronizes on its next line: where that line occurs twice in the file, split the block into two units; an elision may end on the construct's closing brace, `}` or `};` at column 0, which resynchronizes on the first such line that follows. An elision also hides a line dropped beside it, which no check can see, so keep elisions few and never next to the lines a claim rests on.
2. [steps.anchors] Anchors. Emit the LINKS table with the script, never by hand. Judge every row: a symbol link lands on its definition line, a location link on the site the prose describes. Fill the kind cell (symbol, location, config, generated, file) for a linked row or the reason for a bare one as you go; the linked and bare columns are occurrence counts, and a bare prose occurrence resolves only by linking or by a settled exemption. Persist the table into the dossier.
3. [steps.scope-parity] Scope and parity. Every anchor symbol and behavior the catalog row (or the request) names has a location on the page or a scope reduction recorded with its reason above the PARITY table; PARITY starts from the catalog and cannot supply this, and removing a catalog entry never discharges the obligation (the coverage rule of kernel.md [coverage] prints the scoped symbols the page never names). Then every catalog symbol appears in at least one fenced block and the PARITY table has no empty row; check every cell, and de-catalog a symbol that cannot be paired, with a reason named in the report. Block and unit counts are measurements and settle nothing, because one fence can hold several definitions and one caller excerpt can serve several usages; the table's cells decide.
4. [steps.counts] Counts. Re-derive every count and every only, never, always or exactly claim on a differently shaped basis; persist both bases and the reconciled result. The published sentence states the result and its scope and never the search.
5. [steps.sources] Cited sources. An example driver has a substantive commit within the window kernel.md [coverage] states; the recency rule prints the newest commit and substance is read from `git log`. Every OTHER SOURCES entry matches its `Link:` trailer or `dig` output byte for byte.
6. [steps.span-closure] Span closure. Every prose row of LINKS carries a kind or reason, and so does every catalog row whose span is not one of the catalog's own entries, the bare spans in a bullet's descriptive text; the entry rows are covered by PARITY, and anchor confirmation is page-wide.
7. [steps.sweeps] Sweeps. Build the prose view, run every ban pattern over it, adjudicate each hit against the exempt column before touching anything, and write the verdict first; fix with the fix column and escalate what you are unsure of. Then sweep the figure fences for the three bans that reach them, grep the raw file for boldface, sweep the headings in the prose view, and read for list shapes, run-on enumerations, superlatives in context, heading shape and figure geometry.
8. [steps.writing] Writing. Run the opener, spine, member and post-fence generators and read every row: every leading paragraph for purpose before mechanism, the paragraph beside every excerpt for its explanation, function excerpts included, and the first sentence after every excerpt for its subject; read the DETAILS headings for the journey or model spine. Run the lead and SUMMARY generators, tag every lead sentence purpose, position or promise and every SUMMARY sentence M, J, I or B in the dossier, move a sentence with no role to its owning section, and keep a claim the lead already makes only where it adds a relationship, phase or constraint.
9. [steps.rhythm] Rhythm. Run the block-map generator and read the passage behind every line: opening and closing blocks, blocks with no prose between them, the one-sentence bridges it quotes, oversized excerpts, paragraphs and figures, the fences it could not classify, and the figure distribution. Confirm each excerpt's function, situation and premises are identifiable where it stands; enlarge, combine, split or revise, or record why the unit stays whole. Never add or remove a block to satisfy a number, and re-run the sweep over every paragraph the revisions touched.
10. [steps.introductions] Introductions. Every excerpt unit's construct is named and linked in the prose above its fence; a `BARE mention`, `LOCATION LINK ONLY` or `ABSENT` verdict is fixed there, and a construct the heuristics misname is adjudicated by hand and recorded.
11. [steps.rerun] Re-run after fixing. Your own fixes introduce defects, and a result recorded before an edit describes a page that no longer exists. After any edit, re-run `kg check` whole, then repeat by hand the steps the edit reaches: a changed sentence or paragraph reaches steps 7, 8 and 9 over what it touched; a new, changed or moved link or span reaches 2 and 6; a new or changed claim, count or universal word reaches 4; a changed excerpt, provenance line or elision reaches 1, 3 and 10; a catalog change reaches 3 and 6 and the coverage rule; a changed figure reaches 7 and the geometry check; a changed DOCUMENTATION or OTHER SOURCES entry reaches 5; a moved, split or merged subsection reaches 8, 9 and 10. Then refresh the LINKS rows, PARITY cells, counts, block maps and adjudications the edit invalidated, and record the final page's digest with the results (step 12).
12. [steps.persist] Persist the evidence, ending EVIDENCE with `page sha256: <digest>` of the page it describes.

## The prose view and the sweeps [sweeps]

1. [sweeps.prose-view] The view drops fences, resolves links to their text, masks code spans, double-quoted text, `file.c:LINE` citations and `N:M` pairs, tags headings `[H]` and tags catalog bullets, the entry bullets of section six and table cells `[C]`, where the label-colon shape is exempt and nothing else; any other list item outside the catalog sections is swept as prose. SPECIFICATIONS entries keep their mandated form. The verification-narration row alone is swept a second time with code spans visible, because a page writes a command inside a span.

```
python3 - page.md <<'VIEW'
import re, sys
CAT = ("## COVERAGE", "## DOCUMENTATION", "## OTHER SOURCES", "## SPECIFICATIONS")
SIX = ("## REGISTERS", "## METHODS", "## PRIMITIVES", "## INTERFACES")
fence = cat = six = False
for n, l in enumerate(open(sys.argv[1], encoding="utf-8"), 1):
    l = l.rstrip("\n")
    if l.startswith("```"): fence = not fence; continue
    if fence: continue
    if l.startswith("## "): cat = l.strip() in CAT; six = l.strip() in SIX; continue
    if l.startswith("#"):
        print(f"{n}:[H] {l.lstrip('#').strip()}"); continue
    if l.startswith(">"): continue
    tag = ""
    if cat or l.startswith("|") or (six and l.lstrip().startswith(("- ", "* "))):
        tag = "[C] "
    l = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", l)
    l = re.sub(r"`[^`]*`", "§", l)
    l = re.sub(r'"[^"]*"', "§", l)
    l = re.sub(r"\b[\w/.-]+\.(c|h|rst|S):\d+(?:-\d+)?", "§", l)
    l = re.sub(r"::|\d+:\d+", "§", l)
    print(f"{n}:{tag}{l}")
VIEW
```

2. [sweeps.raw-file] Only these run on the raw file: the boldface grep, the internal-link grep (a `](` target ending in `.md` that is not a URL), the table-cell inventory, the generators, and the paragraph-final colon that introduces the next fence, one verdict per colon-ending line:

```
awk '/^```/{f=!f} p && NF{ print p, (/^```/ ? "ok" : "DANGLING"); p=0 } !f && /:$/{p=NR}' page.md
```

3. [sweeps.figures] The figure sweep prints every non-C fence; a fence with no drawing character is a quotation or listing, exempt like any other quoted text, and the rest are read against the three bans that reach figures and the banned shapes.

```
awk '/^```/{f=!f; lang=(f? substr($0,4) : ""); next} f && lang!="c"' page.md
```

4. [sweeps.regions] Enumerate the page's regions (prose, headings, figures, catalog bullets, table cells, fences) and name the mechanism that reaches each; a region no mechanism reaches is unexamined, and it reads exactly like clean. Four classes once shipped behind patterns that could not fire on their region.
5. [sweeps.generators] Reading inventories are findings from their owning guideline modules. Use `kg check <page> --only <rule-id> --json`: `purpose.openers` for openers, `purpose.spine` for the subsection spine, `excerpts.members-named` for members, `excerpts.post-fence-subject` for post-fence sentences, `style.run-on-enumeration` for enumerations, `lead-summary.lead` and `lead-summary.summary` for sentence roles, `arrangement.units` for block maps and baseline comparisons, `arrangement.figure-placement` for figure distribution, `excerpts.introduced` for introductions, `facts.two-bases` and `facts.universal-claims` for claims, `facts.counts-serve-claims` for census candidates, `links.bare-spans` for bare spans, `excerpts.sufficiency` for unreproduced locations, `excerpts.cited-shown` for censuses across files, and `style.headings` for headings. Review rows require reading even when they carry no heuristic flag. The measurements are summary notes.

## What no script decides [judgement]

1. [judgement.candidates] A check emits violations, reading candidates and measurements. The check pass adjudicates candidates against the owning guideline; zero findings proves only that the check detected none of the shapes it recognizes.
2. [judgement.no-rewording] Never reword an exempt construct to silence a pattern. A hit the exempt column covers is recorded in the dossier's LINT as `EXEMPT <rule-id> "<a fragment of the flagged text>": <the ruling applied>` (a page line may follow the fragment as a hint, a double quote inside the fragment is written `\"`, and the ruling runs to the end of the line), which `kg check` reads and prints as a note; a new exemption or ruling lands only through the user, and an agent that settles a boundary during a run records it in the run log and surfaces it.
3. [judgement.unwitnessed] A claim the tree cannot witness is handled as [facts.unwitnessed] says: scoped out, weakened, or stated with its basis disclosed.
4. [judgement.strip-test] Every figure passes the strip test and none of the four banned shapes; each is signed off with the relationship it conveys and the pattern it follows.
5. [judgement.read-not-measured] Whether nearby source supports an explanation, whether an excerpt keeps the context needed to read it, whether a bridge connects its surroundings, and whether a figure serves its passage are read, never measured.
6. [judgement.scope-covered] Scoped behaviors covered: every behavior the catalog row names has a location on the page, or a recorded scope reduction.
7. [judgement.claims-nearby] Claims supported nearby: every behavioral sentence has the source that supports it beside it on the page.
8. [judgement.guards] Guards preserved: every restated guard or threshold keeps the code's operators and constants.
9. [judgement.invariants] Invariants searched: every lifecycle invariant has had its counterexample search, recorded with its basis.
10. [judgement.activation-delta] Activation delta answered: every activatable mechanism answers the four questions of [facts.activation-delta].
11. [judgement.modes] Modes told apart: where a mechanism has several active modes, each difference is explained, or the construct that makes the modes identical is named.
12. [judgement.constructs] Constructs and limits covered: every state-holding construct, lifecycle stage, helper and hard-coded limit that kernel.md [coverage.constructs] demands has its excerpt or citation on the page, or its absence is stated with the reason.

The seven lines from [judgement.scope-covered] to [judgement.constructs] are recorded in the dossier's EVIDENCE, one line each, as done or as not applicable with the reason (dossier.md [evidence]); the check pass reads the seven lines and spot-checks one.

## Figure geometry [figure-check]

Under `kg check`, the geometry checks of figures.md [geometry] run steps 1 to 3 and the loose-vertical part of step 5 (a `│` with no drawn character, junction or arrowhead in the row above and none in the row below); steps 4 and 6 and the trunk ends of step 5 are read, and the writer repairs every class by step 7.

1. [figure-check.extract] Extract every fenced block and drop the source excerpts and the quotation fences.
2. [figure-check.width] Flag any line over the width figures.md [geometry] sets, except a register drawn as a single row with L-connectors.
3. [figure-check.ascii] Flag ASCII `\`, `/` and `|` used as a side, corner, junction, connector or extent marker, leaving a word separator (`R/W`, `put / get`, a path such as `/sys/bus/`), `a|b`, `||`, a comment and reproduced source alone; a spaced C expression such as `a | b` is flagged and read (figures.md [geometry.unicode]).
4. [figure-check.boxes] Group the rows of one box and check it against itself: its border columns and every interior `│` meet a border or junction character (`┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼ │`, or `═ ║ ╔ ╗ ╚ ╝ ╤ ╧` on a double border) in the rows above and below.
5. [figure-check.trunks] Follow every vertical trunk to both ends; it terminates on a junction, an arrowhead or a labelled elbow.
6. [figure-check.bars] A measurement bar spans exactly the columns of what it measures; a span bar on a time or value axis is a datum and is measured against nothing.
7. [figure-check.repair] Repair by class: replace an ASCII extent marker with `├───┤` sized to the box, with the label beneath when it no longer fits; re-anchor a trunk on `┬`, `┴` or `┼` (`╤` or `╧` on a double border) or move it to a junction column; delete a trunk hanging in blank space and redraw the relationship as a straight arrow between facing borders with its label in the gutter above; re-pad a box's rows to one width, leaving annotations outside it alone. Re-run after every repair, because a moved column breaks the next junction.
8. [figure-check.not-breakage] Not breakage: an annotation running past a box's right border, two boxes at different indents, a `│` above `▼` or below `▲`, a C expression in annotation text, a dashed `╎ ┆ ╏` guide, barrier or second class of path, and a span bar with no box above it. Record these as cleared, never as fixed.

## The report [report]

The dossier's sections and what each must hold are dossier.md, whose own rules check the HEADER, the LINKS table, PARITY, EVIDENCE and the LINT record.

1. [report.final] The final report gives the lead verbatim, the sections written, the catalog count and parity outcome with de-catalogings, the QA results (units verified, anchors confirmed, counts with second bases, the generator measurements, the lead and SUMMARY roles, sweep candidates per class with dispositions, the rhythm outliers with dispositions, the introduction summary), the exemptions applied, every hint that did not reproduce, and every claim the tree cannot settle; never the page text beyond the lead.

## The check pass [check-pass]

1. [check-pass.inline] The orchestrator runs it inline, with shell tools, never delegated, for about thirty thousand tokens, reading the engine's output by its findings and summary notes and never whole. It re-runs the writer's procedures against ground truth and compares the answers, because a self-report cannot prove itself; it does not redo the writer's work or read the page for style, and its reach into prose is bounded to what the generators print. In single-agent mode the same agent runs it, under SKILL.md's rule: from the output of `kg check` and the dossier, never from memory of writing, and LINT says the pass was self-run.
2. [check-pass.sweeps] Reproduce the sweeps: every class reported fixed reproduces at zero, and every remaining hit matches a recorded exemption, the EXEMPT lines `kg check` printed as notes each re-adjudicated against the exempt column; a class reported clean that fires here means the sweep was not run.
3. [check-pass.reproduce] Re-run the figure sweep, the span closure against the dossier's LINKS table (a discrepancy means the table was hand-edited or stale, and a sample of judgement cells is re-adjudicated), the excerpt and anchor checks in full, and the geometry check.
4. [check-pass.counts] Re-derive two or three load-bearing counts on a basis shaped differently from both the dossier records.
5. [check-pass.generators] Re-run the writing, rhythm and introduction generators and compare with the dossier's lists: a count-led opener, an unexplained excerpt, a catalog-order spine, a hard-limit breach, a sentence without a role, a block map that differs from the recorded one, or an outlier neither revised nor explained is a finding.
6. [check-pass.fixes] A fix is exactly specified when the engine's finding or the check pass names the page line, the text before and the text after, and it changes no claim; anything else is a rewrite (SKILL.md, the two states). Apply an exactly specified fix yourself and re-verify it with the command that found it, deriving a volume fix from an exhaustive grep and never from the sites a report happened to name; then refresh the EVIDENCE section's `page sha256:` line to the fixed page and note the fix in LINT. A factual finding returns to the writer while its transcript lives, otherwise to the run log and the user, who decides whether the page is rewritten (SKILL.md, the two states).
7. [check-pass.record] After a complete full run without FAIL or engine errors and completed human adjudication, record the outcome in LINT, ending with `LINTED <date> page sha256: <digest> qa sha256: <qa-digest>` using both digests printed by that run. Re-verify a fix with its check and then `kg check` whole before recording. A changed page or QA digest, or a legacy record without the QA digest, requires a new pass. Record the state change in the run log; promote a refuted spec claim into dated errata and surface a settled boundary to the user.
