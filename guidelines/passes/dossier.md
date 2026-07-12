# The research dossier

Rule IDs (3a-3c, 7, 7a-7r) resolve via `guidelines/rules/INDEX.md`.

The dossier is the durable artifact of the research pass (`guidelines/passes/01-research.md`): everything located for a page, recorded as anchored facts before any prose exists. It exists so that a page's research survives the agent that performed it (an interrupted page resumes from the dossier instead of transcript archaeology or re-research), so that the research and write passes can be run by different agents or in different sessions, and so that the lint and verify passes start their re-derivations from the recorded search bases instead of reconstructing them.

## Ground truth

The dossier is a hint sheet, never a source. It pins the documented version (tag plus commit) in its HEADER, and every fact taken from it (a line number, a caller list, a count, a spec section) is re-verified against the on-disk tree at that version before it lands in the page (7e). The lint and verify passes never accept a dossier entry as evidence; they use it only as the starting point for their own re-derivations (7o). A dossier that disagrees with the disk is corrected to match the disk, at the moment the disagreement is found.

## Location and lifecycle

- One dossier per page: `progress/<campaign>/<page-slug>.dossier.md`, in the run's artifact directory under the skill root (naming and isolation: SKILL.md ("The progress/ workspace"); a single-page run's name is its topic slug). The lint-fix pass writes its report beside it as `<page-slug>.lint.md`, a solo verify writes `<page-slug>.verify.md` there too (a verify campaign's reports land in the verify run's own directory, `guidelines/passes/04-verify.md`), and any other intermediate an agent persists lands in the same directory as `<page-slug>.<purpose>.<ext>`.
- `progress/` is gitignored and never committed, with the verify-artifact exception defined in SKILL.md ("The progress/ workspace"). A run's artifacts are disposable once its campaign closes (keep them until then; enhancement passes, gap-fill writers, and verify campaigns reuse them). Another run's artifacts are off limits unless the user explicitly directs resume or reuse (verify campaigns read their declared parent under that rule).
- Whoever runs the research pass creates the dossier and keeps it current while researching: the writer by default, a dedicated researcher agent (brief in `guidelines/passes/01-research.md`) when a campaign fans research out. The writer updates it whenever the disk disagrees with a recorded hint, and appends the EVIDENCE section when the exit suite runs (`guidelines/passes/02-write.md`).
- When a writer dies mid-page, resuming that same agent (its transcript keeps the richer context) stays the first recovery move; the dossier is the durable fallback, and a replacement agent starts by reading the dossier plus the plan file instead of redoing the research.
- A solo agent single-stepping the passes writes the dossier even for a one-page task; it is what makes each pass resumable in a later session.

## Format

Sections mirror the research pass one for one, so a single agent can fill the dossier stage by stage and checkpoint between stages. Keep entries to one or two lines each, in the compact anchored-facts style of the inventory digests; the dossier records locations and search bases, not prose.

```
# Dossier: <page slug>

## HEADER
- output path: docs/<dir>/<topic-slug>.md
- campaign: <run short name> (artifact directory progress/<campaign>/)
- subsystem: <name> (entry in guidelines/reference/subsystems.md)
- documented version: <tag>, commit <sha>
- architecture / CONFIG scope: <arch>; <CONFIG assumptions>
- boundary statement: <verbatim from the plan file, campaigns only>
- status: <researching | written | linted | certified>

## SYMBOLS
One line per function, struct, enum, macro, or typedef the page will
catalog: name, kind, file:line of the DEFINITION, one-line role.

## USAGE
Per catalog symbol: at least one concrete caller or user, each with the
caller name and file:line, recording the exact line range the page will
excerpt (feeds the definition-plus-usage depth rule and the parity
checklist of guidelines/passes/02-write.md).

## ENUMERATIONS
Per behavior or per counted claim: the full site list with file:line per
site, AND the search basis used (tool, pattern, directories searched,
headers included or excluded). The basis is what lint re-runs (7o).

## SPECIFICATIONS
One line per spec reference: <spec name>, section <N.N>: <title>, and
where in the code or commit history it was found.

## COMMITS AND LORE
Per relevant commit: sha, subject, and the byte-exact Link: trailer URL
from git log (or the dig result), marked usable/unusable for OTHER
SOURCES per 7n.

## HARD LIMITS
Per constant bounding the mechanism: name or literal, value, file:line
(feeds 7j's limit coverage).

## VERSION DRIFT
Symbols renamed, removed, or newly added at the documented version
relative to widely-documented older kernels; known stale-index hints.

## EVIDENCE
Appended by the write pass's exit suite (guidelines/passes/02-write.md).
Per count and per universal claim the page states: the claim text, the
two derivation bases used (the research basis and the differently-shaped
exit basis), and the reconciled result. Plus the suite's outcomes: the
number of excerpt units byte-verified and the number of link anchors
confirmed. A verify campaign starts its re-derivations here and must use
a basis shaped differently from the recorded ones; entries are
re-derivation starting points, never proof.

## OPEN GAPS
Anything not yet located or verified, so a resuming agent knows exactly
what research remains.
```
