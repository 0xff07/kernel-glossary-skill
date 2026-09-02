# Pass 00: prep

Purpose: resolve everything the later passes consume, before any research or writing.
Inputs: the subsystem, the topic, and the documented kernel version (SKILL.md "Input").
Outputs: the resolved subsystem entry (tag, dir, kernel_paths, spec, section6_heading), the output path, the run's workspace under `progress/`, and the chosen exemplar pages under `docs/sound/`; recorded in the dossier HEADER (`guidelines/passes/dossier.md`).
Run by: single-agent mode inline, as the first pass; in a campaign the orchestrator resolves these once per page into the writer brief, and the writer re-reads this file for the exemplar doctrine.
Next: pass 01 (`guidelines/passes/01-research.md`).

Rules are cited by stable ID; `guidelines/rules/INDEX.md` maps every ID to its file.

## Read the template and the exemplar pages

Before generating any content, read `guidelines/reference/TEMPLATE-FULL.md` (relative to `${CLAUDE_SKILL_DIR}`) for the page structure and section order.

Then read one or two exemplar pages under `${CLAUDE_SKILL_DIR}/docs/sound/`, the ones whose archetype most resembles the page about to be written, in full, before writing. The sound corpus is the exemplar because its pages explain what they quote. Measured on 2026-09-02 with the member generator in ROUTINE-04, the paragraph beside a definition excerpt names at least one of the members the excerpt shows on 84 of every 100 excerpts, against about half on the pages written between 2026-08-31 and 2026-09-02; the corpus carries 88 prose words per code block and introduces 98 of every 100 excerpts with a sentence that says what the excerpt is about to show (the figures are in `guidelines/reference/measured-criteria.md`). Read the exemplars for exactly that: how the lead states the model, how each DETAILS section is a phase or a facet rather than a symbol, and how the paragraph beside every excerpt says what each member holds and who writes or reads it, or what the shown lines do.

- structure-tour pages (one central struct documented field group by field group, with its accessor and lifecycle catalog): `docs/sound/alsa/pcm/pcm-substream.md`; and `docs/sound/soundwire/bus-device-model.md` for a page whose excerpts are many small structs, each walked member by member
- lifecycle / refcount / locking-protocol pages: `docs/sound/alsa/card.md` (a kref-carried lifetime and the two locks over the control set, the locks cataloged under INTERFACES); and `docs/sound/alsa/pcm/pcm-state-machine.md` for a state set and the protocol that moves an object through it
- encoding / bitfield / register pages (including register-figure style): `docs/sound/hda/hdac-core.md` (a REGISTERS section and register-block figures); `docs/sound/formats/i2s.md` (frame-timing waveforms and a format-field figure); and `docs/sound/soundwire/stream/bank-switch.md` for banked registers
- journey pages (one process traced in order from entry to completion): `docs/sound/flows/playback.md`; `docs/sound/flows/suspend.md`
- function-pointer-struct pages (an ops table and the paths that call each callback): `docs/sound/alsa/pcm/pcm-ops.md`; `docs/sound/asoc/controls/kcontrol-handlers.md`
- algorithm or engine pages (one routine and the decisions it makes): `docs/sound/dapm/power/power-engine.md`
- pages rebuilt from earlier drafts: the archetype match above for form; PLOT-04 governs the derivation itself

If no archetype matches, pick the structurally closest `docs/sound/` page anyway. Do not calibrate against pages under any other `docs/` directory: they were written under earlier or since-withdrawn rules. The frozen mm samples that were the exemplar until 2026-09-02 are gone; `guidelines/LESSONS.md` records why.

Exemplars calibrate form only, never facts. A sound page documents the sound subsystem at its own version and can carry errors found only by a later audit. Take zero kernel facts, line numbers, or excerpts from an exemplar into the page being written; research every fact against the documented tree (PAGE-02, FACT-03).

Where an exemplar and a rule in this skill disagree, the rules under `guidelines/rules/` govern; exemplars are calibration, not license. The sound pages predate most of the current rule corpus, and three things on them are known not to carry over. Their LINUX KERNEL catalogs are broader than their excerpts (most measure below one fenced block per catalog entry), and PAGE-02's parity table still binds: every cataloged symbol gets its definition and usage excerpts, or is de-cataloged. A few of their sentences use a placement verb or a label-colon that BANS trims; the ban governs. And where a sound excerpt shows members its paragraph does not explain, WRITING rule 3 governs: the excerpt is cut to what the paragraph explains, or the paragraph is extended.

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
