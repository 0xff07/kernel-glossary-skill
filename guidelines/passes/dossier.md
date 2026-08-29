# The dossier

Rules are cited by stable ID; `guidelines/rules/INDEX.md` maps every ID to its file.

The dossier is one of the skill's three artifacts (SKILL.md, "The three artifacts and the three states"), and it is the page's ENTIRE working file. Everything every pass learns about one page goes here: the research, the parity table, the exit-suite evidence, the lint findings, the verify findings. There is no report file beside it, and no pass creates one.

It exists so that a page's work survives the agent that did it — an interrupted page resumes from the dossier instead of transcript archaeology or re-research — so that passes can run in different sessions or by different agents, and so that a later pass starts its re-derivations from recorded search bases instead of reconstructing them.

## Ground truth

The dossier is a hint sheet, never a source. It pins the documented version (tag plus commit) in its HEADER, and every fact taken from it — a line number, a caller list, a count, a spec section — is re-verified against the on-disk tree at that version before it lands in the page (PAGE-02). The lint and verify passes never accept a dossier entry as evidence; they use it only as the starting point for their own re-derivations (FACT-03). A dossier that disagrees with the disk is corrected to match the disk, at the moment the disagreement is found.

## Location and lifecycle

- One dossier per page: `progress/<campaign>/<page-slug>.dossier.md`. A single-page run's campaign name is its topic slug.
- Local scratch, never committed. A run's dossiers are disposable once its campaign closes (keep them until then; gap-fill writers and verify campaigns reuse them). Another run's dossiers are off limits unless the user directs resume, reuse, or verify.
- Whoever runs the research pass creates it and keeps it current: the writer by default, or a dedicated researcher agent (`guidelines/passes/01-research.md`) when a campaign fans research out. Each later pass appends its own section.
- Anything durable a dossier records — a correction against the campaign's specification, a lesson, a settled adjudication — is promoted by the orchestrator into the campaign spec (`campaigns/<campaign>.md`) as a dated amendment, or surfaced to the user for the 7r registry; the spec is the only artifact here that travels. Run events go to the run log (`progress/<campaign>/log.md`). A finding left only in a dossier or the log is lost when the machine is — by design.
- When a writer dies mid-page, resuming that same agent stays the first recovery move (its transcript holds the richer context); the dossier is the machine-local fallback, and a replacement agent starts from the dossier plus the campaign spec instead of redoing the research.
- Helper scripts and working scratch go in the agent's scratchpad directory, not here — under a per-page subdirectory named for the page slug, because the session scratchpad is shared between concurrently dispatched agents and generically named files collide across pages.

## Format

The research sections mirror the research pass one for one, so a single agent can fill them stage by stage and checkpoint between stages. Keep entries to one or two lines each, in the compact anchored-facts style of the inventory digests: the dossier records locations, search bases, and outcomes — not prose.

```
# Dossier: <page slug>

## HEADER
- output path: docs/<dir>/<topic-slug>.md
- campaign: <run short name> (directory progress/<campaign>/)
- subsystem: <name> (entry in guidelines/reference/subsystems.md)
- documented version: <tag>, commit <sha>
- architecture / CONFIG scope: <arch>; <CONFIG assumptions>
- boundary statement: <verbatim from the campaign spec, campaigns only>

## SYMBOLS
One line per function, struct, enum, macro, or typedef the page will
catalog: name, kind, file:line of the DEFINITION, one-line role.

## USAGE
Per catalog symbol: at least one concrete caller or user, each with the
caller name and file:line, recording the exact line range the page will
excerpt (feeds the definition-plus-usage depth rule and the PARITY
table below).

## ENUMERATIONS
Per behavior or per counted claim: the full site list with file:line per
site, AND the search basis used (tool, pattern, directories searched,
headers included or excluded). The basis is what a later pass re-runs (FACT-03).

## SPECIFICATIONS
One line per spec reference: <spec name>, section <N.N>: <title>, and
where in the code or commit history it was found.

## COMMITS AND LORE
Per relevant commit: sha, subject, and the byte-exact Link: trailer URL
from git log (or the dig result), marked usable/unusable for OTHER
SOURCES per PAGE-05.

## HARD LIMITS
Per constant bounding the mechanism: name or literal, value, file:line
(feeds FACT-01's limit coverage).

## VERSION DRIFT
Symbols renamed, removed, or newly added at the documented version
relative to widely-documented older kernels; known stale-index hints.

## LINKS
MACHINE-EMITTED, not hand-authored. The write pass's exit suite (item 2)
runs the extractor script printed there over the finished page; the
script emits this table, one fixed six-column row per distinct inline
span:

| span | region | linked | anchor URL | disk line | kind / reason |

The first five columns are SCRIPT OUTPUT and must not be hand-edited:
`span` is the backticked text; `region` is `prose` (the lead paragraph,
SUMMARY, and DETAILS) or `catalog` (the reference sections); `linked` is
yes/no; `anchor URL` and `disk line` are the URL and the tree line the
script fetched at it, blank for a bare span. Only the last column is the
writer's, and it holds either a `kind` (for a linked row: symbol /
location / config / generated / file) confirming the anchor, or a
`reason` (for a bare row: the 7r exemption that licenses leaving it
unlinked). The split is the point — the script owns which spans exist and
what their anchors are, the writer owns whether each anchor is right.

Two obligations run off this one table. ANCHOR CONFIRMATION is page-wide:
every `linked` row's disk line is judged against what the prose claims,
`catalog` rows included, because a wrong URL is a defect anywhere. SPAN
CLOSURE (exit-suite item 6) is scoped to the prose region: every `prose`
row must have a non-empty `kind / reason` cell, and an empty one is the
defect. `catalog` rows are out of closure scope for now (the reference
sections are covered by PARITY); a bare `catalog` row may be left blank.
The check pass (guidelines/passes/03-check.md) RE-RUNS THE SAME SCRIPT and
diffs — because both derive the span set from identical code, the diff
cannot disagree on which spans exist, only on a judgment cell, which is
exactly what an independent check should be comparing.

## PARITY
Written by the write pass (guidelines/passes/02-write.md) and closed
before the page is reported written. One row per LINUX KERNEL catalog
symbol, two cells: where DETAILS shows its DEFINITION as a fenced c
block, and where it shows a concrete USAGE as code — the two evidence
columns of the parity criteria (PAGE-02; was Gate B item 1). At exit every row is filled or its symbol is
de-cataloged to a linked prose mention with a one-line reason
(fill-or-decatalog; there is no deliberately-empty state). Record the
final blocks-per-catalog-entry ratio; below 1.0 means unpaired symbols,
which are real gaps (guidelines/reference/measured-criteria.md).

## EVIDENCE
Written by the write pass's exit suite. Per count and per universal
claim the page states: the claim text, the two derivation bases used
(the research basis and the differently-shaped exit basis), and the
reconciled result. Plus the suite's outcomes: excerpt units
byte-verified, link anchors confirmed, quotations checked. A verify pass
starts its re-derivations here and must use a basis shaped differently
from the recorded ones; entries are starting points, never proof.

## LINT
The sweep record (was the Gate A record). The WRITER writes it as part of its exit suite
(guidelines/passes/02-write.md, item 7): every candidate the prose view
and the figure sweep surfaced, each FIXED (with the exact before/after),
ESCALATED (unsure — for the orchestrator), or EXEMPT (with the 7r ruling
applied). Write the verdict down BEFORE acting on it; that is what stops
a writer's defence of its own prose from being silent. The check pass
(guidelines/passes/03-check.md) then appends its own reproduction of
these classes, and a disagreement is a finding.

## VERIFY
Written by the verify pass (guidelines/passes/04-verify.md). Per-rule
sweep and criteria outcomes (was Gate A and Gate B) with their evidence
(a count or a list, never "looks fine"), and every finding: rule, class,
location, exact text, what the tree shows.

## OPEN GAPS
Anything not yet located or verified, so a resuming agent knows exactly
what work remains.
```
