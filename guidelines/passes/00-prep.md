# Pass 00: prep

Purpose: resolve everything the later passes consume, before any research or writing.
Inputs: the subsystem, the topic, and the documented kernel version (SKILL.md "Input").
Outputs: the resolved subsystem entry (tag, dir, kernel_paths, spec, section6_heading), the output path, the run's workspace under `progress/`, and the chosen sample archetype; recorded in the dossier HEADER (`guidelines/passes/dossier.md`).
Run by: single-agent mode inline, as the first pass; in a campaign the orchestrator resolves these once per page into the writer brief, and the writer re-reads this file for the samples doctrine.
Next: pass 01 (`guidelines/passes/01-research.md`).

Rules are cited by stable ID; `guidelines/rules/INDEX.md` maps every ID to its file.

## Read the template and the samples

Before generating any content, read `guidelines/reference/TEMPLATE-FULL.md` (relative to `${CLAUDE_SKILL_DIR}`) for the page structure and section order.

Then read the samples under `${CLAUDE_SKILL_DIR}/guidelines/reference/samples/`. These are frozen copies of real pages that met the full rule set — every PASS CRITERIA under the ROUTINE-01 checking protocol (was Gate A and Gate B; `guidelines/rules/INDEX.md` maps every rule) — with zero findings under the mechanical checks; they are the concrete standard for structure, prose, diagram style, code-citation density, and depth of coverage. Open the one or two whose archetype most resembles the page about to be written and read them in full before writing:

- structure-tour pages (one central struct documented field group by field group, with its accessor and lifecycle catalog): `guidelines/reference/samples/page-overview-mm-struct.md`
- lifecycle / refcount / locking-protocol pages: `guidelines/reference/samples/page-lifecycle-mm-refcount.md` (also the smallest acceptable depth for a fine-grained page)
- encoding / bitfield / flag-layout pages (including register-figure style): `guidelines/reference/samples/page-encoding-pgtable-entries.md`
- pages rebuilt from earlier drafts: `guidelines/reference/samples/page-enhanced-vma-overview.md`, read side by side with the counterexample below
- `guidelines/reference/samples/draft-original-vma-overview.md` is a COUNTEREXAMPLE, the stale draft the enhanced page was rebuilt from. Do not imitate it. It is kept so the measurable difference between a plausible draft and a page meeting this standard stays visible (see `guidelines/reference/draft-contrast.md`).

If no archetype matches, pick the structurally closest sample page anyway. Do not calibrate against pages elsewhere under `docs/`; they may predate the current rules. Where a sample and a rule in this skill disagree (a sample can predate a later rule), the rules under `guidelines/rules/` govern; samples are calibration, not license. Samples calibrate form only, never facts: a sample documents its own tree at its own version, and a sample page has carried a false claim found only by a later audit (see `guidelines/reference/draft-contrast.md`). Take zero kernel facts, line numbers, or excerpts from a sample into the page being written; research every fact against the documented tree.

## Determine subsystem and output path

Look up the subsystem in the Subsystem Map (`guidelines/reference/subsystems.md`; one entry per subsystem) to find:

- `tag`: the subsystem tag, used when composing the commit message for the page
- `dir`: the output directory under `docs/`
- `kernel_paths`: directories in the kernel source tree to search first
- `spec`: specification name(s) for the SPECIFICATIONS section
- `section6_heading`: the heading to use for section 6 (REGISTERS, METHODS, PRIMITIVES, INTERFACES, or omit)

Construct the output path: `${CLAUDE_SKILL_DIR}/docs/<dir>/<topic-slug>.md`

If the output directory does not exist, create it.

## Create the run workspace

For a run outside a campaign, choose the run's short name and create its workspace directory `progress/<campaign>/` now, per SKILL.md ("The three artifacts and the two states") (a campaign created its workspace at planning; the writer brief carries the path). Record the name in the dossier HEADER. Collision-check the name against both `campaigns/` and `progress/`. Existing `progress/` workspaces belong to other campaigns: list their names only for the collision check, and read nothing inside them.
