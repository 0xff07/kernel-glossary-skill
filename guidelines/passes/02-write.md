# Pass 02: write

Purpose: compose the complete page, following every writing rule while composing rather than fixing afterward.
Inputs: the dossier (pass 01) and the resolved parameters (pass 00); every dossier fact is re-verified on disk before it lands, because the tree at the documented version is the only ground truth.
Outputs: the draft page at `docs/<dir>/<topic-slug>.md`; the dossier updated where the disk disagreed with it; the parity checklist at `progress/<campaign>/<page-slug>.parity.md`.
Run by: single-agent mode inline; in a campaign the writer agent (`guidelines/agents/writer.md`), on the strongest available model.
Next: pass 03 (`guidelines/passes/03-lint.md`). A campaign writer finishes this pass by closing the parity table and running the mechanical exit suite below — it owns the page's substance end to end — but does not run the style sweeps on its own prose, because a fresh-context style stage does those better. A solo agent continues into pass 03 itself.

Rule IDs (7, 7a-7r) resolve via `guidelines/rules/INDEX.md`; 7g-7i live under `guidelines/diagrams/`.

## Reading list (mandatory, in order)

This pass owns the writer's reading list; the writer brief points here instead of restating rules.

1. `guidelines/rules/INDEX.md`, then every rule file it lists: 7, 7a-7f, 7j-7o, 7q, 7r (7p additionally whenever the page derives from existing material).
2. `guidelines/diagrams/7g-principles.md` always; `guidelines/diagrams/7h-register-bitfield.md` and `guidelines/diagrams/7i-patterns.md` when the page will carry a figure (choose the shape from 7i's use-case index).
3. `guidelines/reference/measured-criteria.md`: the depth rules and tripwires that define what "in-depth, fine-grained" measures as.
4. The sample pages chosen in pass 00 (`guidelines/passes/00-prep.md`), under its doctrine that samples calibrate form only, never facts.
5. The page's subsystem entry in `guidelines/reference/subsystems.md`.
6. `guidelines/gates/gate-b.md`: the writer satisfies its substance items by construction and by the mechanical exit suite below (1 parity, 2 grounded code, 3 links, 6 coverage, 7 driver recency, 9 behavioral claims); the verifier re-runs the whole gate at sign-off. Gate A and the style-shaped items stay with the style stage — the writer never sweeps its own prose.

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

Maintain the catalog-to-DETAILS parity checklist as the page is composed: one row per LINUX KERNEL catalog symbol, recording where DETAILS reproduces its definition as a fenced ` ```c ` block and where it shows a concrete caller or usage as code — the two evidence columns of Gate B item 1. Persist the table at `progress/<campaign>/<page-slug>.parity.md` in the run's artifact directory (`guidelines/campaign/progress-layout.md`) before reporting the page written. Catalog a symbol only when both of its cells can be filled; a symbol the page will not excerpt is mentioned and linked in prose without a catalog bullet. At exit every row is filled or its symbol has been de-cataloged (fill-or-decatalog): there is no deliberately-empty state, and each de-cataloging is named in the writer's final report.

This is construction bookkeeping — tracking coverage forward while writing, the same duty class as the 7o enumerations — not a style sweep. The verify pass audits the table independently against the page; a checklist entry is a hint, never evidence (the same relationship the dossier has). The checklist exists because parity holes that survive the writer cost a follow-up round-trip an order of magnitude more expensive than the missing excerpts themselves.

## Mechanical exit suite (run before reporting done)

After the page is complete, the writer verifies its own substance with the procedures below and fixes what they find before reporting. These are procedures against ground truth, not the style sweeps (which stay with the style-lint stage); running them is part of writing the page, and they are reliable in the writer's own hands precisely because they are mechanical.

1. Excerpts: byte-compare every fenced ` ```c ` unit against its provenance file at the cited line (tabs included; an interior `/* path:line */` delimiter starts a new unit, a standalone `...` line is a declared elision). Every unit begins at its cited line.
2. Anchors: extract every Elixir link target, print the disk line at each, and confirm a symbol link lands on the definition line and a location link on the exact site the prose describes (7m; the 7r settled rulings govern `CONFIG_*` options, generic primitives, and ops-struct members).
3. Parity closure: confirm every catalog symbol appears in at least one fenced block and the parity table has zero empty rows (fill-or-decatalog above).
4. Counts: re-derive every count and every "only"/"never"/"always"/"exactly" enumeration with a search basis shaped differently from the one used during research — a repeated identical grep repeats the same miss — and reconcile, or fix the sentence to what the enumeration shows (7o).
5. Cited examples: for each driver or consumer file cited as an example, confirm a substantive commit within roughly three years (`git log -1` on the file).

Claims that are not disk-settleable (intent, motivation, anything the tree at the documented version cannot witness) are never left as bare assertions: scope them out, weaken them to what the evidence shows (7o), or state them with their basis disclosed (7l, 7n). The writer's report lists this class explicitly; "could not verify" is reserved for it — a disk-settleable claim is settled or dropped, never reported unverified.

## Composing stance

The sample pages under `guidelines/samples/` embody every rule. The closest-matching sample read in the prep pass (`guidelines/passes/00-prep.md`) is the worked example; match its structure, diagram style, code-citation density, and depth. The examples in the rule files use ACPI and mm symbols; they illustrate the rule mechanic, which applies unchanged to every subsystem. All generated content must follow the rules as it is composed; the 7q recipes (`guidelines/rules/7q-rephrase-recipes.md`) exist so compliant phrasing never has to be re-derived per hit, and the 7r registry settles the boundary cases in advance.
