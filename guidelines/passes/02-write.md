# Pass 02: write

Purpose: compose the complete page, following every writing rule while composing rather than fixing afterward.
Inputs: the dossier (pass 01) and the resolved parameters (pass 00); every dossier fact is re-verified on disk before it lands, because the tree at the documented version is the only ground truth.
Outputs: the draft page at `docs/<dir>/<topic-slug>.md`; the dossier updated where the disk disagreed with it.
Run by: single-agent mode inline; in a campaign the writer agent (`guidelines/agents/writer.md`), on the strongest available model.
Next: pass 03 (`guidelines/passes/03-lint.md`). A campaign writer stops after this pass: it follows every rule while composing but does not run the gate loops, because a separate lint stage with fresh context redoes that work better. A solo agent continues into pass 03 itself.

Rule IDs (7, 7a-7r) resolve via `guidelines/rules/INDEX.md`; 7g-7i live under `guidelines/diagrams/`.

## Reading list (mandatory, in order)

This pass owns the writer's reading list; the writer brief points here instead of restating rules.

1. `guidelines/rules/INDEX.md`, then every rule file it lists: 7, 7a-7f, 7j-7o, 7q, 7r (7p additionally whenever the page derives from existing material).
2. `guidelines/diagrams/7g-principles.md` always; `guidelines/diagrams/7h-register-bitfield.md` and `guidelines/diagrams/7i-patterns.md` when the page will carry a figure (choose the shape from 7i's use-case index).
3. `guidelines/reference/measured-criteria.md`: the depth rules and tripwires that define what "in-depth, fine-grained" measures as.
4. The sample pages chosen in pass 00 (`guidelines/passes/00-prep.md`), under its doctrine that samples calibrate form only, never facts.
5. The page's subsystem entry in `guidelines/reference/subsystems.md`.

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

## Composing stance

The sample pages under `guidelines/samples/` embody every rule. The closest-matching sample read in the prep pass (`guidelines/passes/00-prep.md`) is the worked example; match its structure, diagram style, code-citation density, and depth. The examples in the rule files use ACPI and mm symbols; they illustrate the rule mechanic, which applies unchanged to every subsystem. All generated content must follow the rules as it is composed; the 7q recipes (`guidelines/rules/7q-rephrase-recipes.md`) exist so compliant phrasing never has to be re-derived per hit, and the 7r registry settles the boundary cases in advance.
