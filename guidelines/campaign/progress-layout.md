# The progress/ workspace: naming, layout, and isolation

Rule IDs (7, 7a-7r) resolve via `guidelines/rules/INDEX.md`; 7g-7i live under `guidelines/diagrams/`.

`progress/` (under the skill root, gitignored, never committed) is the runtime workspace for every run of this skill, and it accumulates: finished, suspended, and abandoned runs stay on disk until the user deletes them. The layout below keeps runs from contaminating each other, so a prompt similar to an earlier one produces a clean new run beside the old one instead of inheriting its files.

## One run, one name

Every run — a multi-page campaign or a single-page task — owns a unique short name, chosen at run start, and at most two top-level entries under `progress/`:

- `progress/<campaign>.md` — the plan file (structure: `guidelines/campaign/plan-file.md`). Campaigns only; a single-page run keeps no plan file.
- `progress/<campaign>/` — the artifact directory: the per-page dossiers (`<slug>.dossier.md`), lint reports (`<slug>.lint.md`), verify reports (`<slug>.verify.md`), and every other intermediate a sub-agent persists (parity tables, span inventories, follow-up notes, helper-script output), named `<slug>.<purpose>.<ext>`.

Nothing else lands at the top level of `progress/`. Pages never land here (they go under `docs/` per the save policy in SKILL.md), and no run writes inside another run's entries. Create the artifact directory the moment the run starts: at planning for a campaign (`guidelines/campaign/planning.md`), at pass 00 for a single page (`guidelines/passes/00-prep.md`).

The chosen name is recorded where a resuming agent will find it — the plan file's Context section for a campaign, the dossier HEADER for a single page — and every sub-agent brief carries the artifact directory as an absolute path (the `<campaign>` bracket in the templates under `guidelines/agents/`); a sub-agent writes only inside its own run's directory.

## Choosing the name

One to three lowercase hyphenated words naming the run's subsystem area: `mm`, `pagecache`, `usb4-tunneling`; a single-page run uses its topic slug. The name must not collide with any existing top-level entry in `progress/`: list the entry names (`ls progress/`), and on collision append the date, then a counter — `pagecache` → `pagecache-20260711` → `pagecache-20260711-2`. That listing is a name-availability check only, never license to read the colliding run's files.

## New runs start from scratch

Existing `progress/` entries belong to other runs: earlier sessions, parallel campaigns, superseded attempts. A session starting a new run reads nothing inside them — not the plan files, not the dossiers — and plans from scratch per `guidelines/campaign/planning.md`, even when an old entry plainly covers a similar topic. Never resume, merge, or adopt half-finished work found in `progress/` uninvited; the old run stays untouched for reference, and deleting or overwriting another run's entries is the user's call, never the skill's.

There are two ways into an existing run's files, both requiring the user to say so:

- Resume: the user asks to continue a specific campaign. The resume state is `progress/<campaign>.md` (Status section first), the pages on disk, and the artifact directory, per `guidelines/campaign/planning.md`. When the user wants to resume but names no run, list `progress/*.md` and ask which.
- Reuse: the user directs the new run to consume a prior run's artifacts ("reuse the dossiers from the mm campaign"). Record what was reused in the new plan file's Context section; prior-run artifacts are hints under the same ground-truth rule as any dossier (7e, 7o), never evidence.

Entries following neither shape (layouts predating this scheme) are opaque: treat them as reserved names and leave them alone.
