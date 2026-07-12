# Writing rules index

The sample pages under `guidelines/reference/samples/` embody every rule in this directory. The closest-matching sample read in the prep pass (`guidelines/passes/00-prep.md`) is the worked example for a new page; match its structure, diagram style, code-citation density, and depth. The examples in the rule files use ACPI and mm symbols; they illustrate the rule mechanic, which applies unchanged to every subsystem. All generated content must follow these rules.

Rule IDs are stable identifiers: briefs, lint and verify reports, plan files, and the gates cite rules by ID, and the IDs never renumber. One recorded exception: the gates moved into this directory from a former `guidelines/gates/` directory and took IDs 3a-3c in that one-time move (never to be repeated); prose throughout the skill keeps their names — Gate A (3a), Gate B (3b) — with the IDs for file reference. 7g-7i are the diagram rules; their figure catalogs live inside the rule files.

| ID | file | rule |
|---|---|---|
| 3a | `guidelines/rules/3a-gate-a.md` | Gate A: the mechanical grep gate (mandatory) |
| 3b | `guidelines/rules/3b-gate-b.md` | Gate B: the nine-item review sign-off (mandatory) |
| 3c | `guidelines/rules/3c-mechanical-checks.md` | The by-hand check procedures both gates use |
| 7 | `guidelines/rules/7-style-core.md` | Writing rules (mandatory) |
| 7a | `guidelines/rules/7a-prose-colon.md` | Prose colon idioms (mandatory) |
| 7b | `guidelines/rules/7b-prose-lists.md` | Prose lists (mandatory) |
| 7c | `guidelines/rules/7c-forbidden-phrases.md` | Forbidden phrases checklist |
| 7d | `guidelines/rules/7d-superlatives.md` | Hollow superlatives and unsupported adjectives (mandatory) |
| 7e | `guidelines/rules/7e-code-citation.md` | Self-contained kernel-source citation (mandatory) |
| 7f | `guidelines/rules/7f-page-rules.md` | General page rules (mandatory) |
| 7g | `guidelines/rules/7g-principles.md` | General ASCII diagram principles (mandatory) |
| 7h | `guidelines/rules/7h-register-bitfield.md` | Register and bitfield figures (mandatory) |
| 7i | `guidelines/rules/7i-patterns.md` | Other ASCII diagram patterns |
| 7j | `guidelines/rules/7j-coverage.md` | Behavior and construct coverage (mandatory) |
| 7k | `guidelines/rules/7k-driver-examples.md` | Driver examples (mandatory) |
| 7l | `guidelines/rules/7l-provenance.md` | Code-block provenance comments (mandatory) |
| 7m | `guidelines/rules/7m-linking.md` | Link anchoring and exhaustive span linking (mandatory) |
| 7n | `guidelines/rules/7n-other-sources.md` | OTHER SOURCES provenance (mandatory) |
| 7o | `guidelines/rules/7o-claims.md` | Behavioral-claim verification (mandatory) |
| 7p | `guidelines/rules/7p-derivation.md` | Deriving from an existing page (mandatory) |
| 7q | `guidelines/rules/7q-rephrase-recipes.md` | Rephrase recipes (quick reference) |
| 7r | `guidelines/rules/7r-adjudications.md` | Settled adjudications registry (mandatory reading for every brief) |
