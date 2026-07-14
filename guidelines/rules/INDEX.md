# Rule index

Rules are cited by stable ID everywhere in this skill — briefs, dossiers, campaign files, and the pass files. **IDs never renumber.** One recorded exception: the gates took IDs 3a-3c in a one-time move from a former `guidelines/gates/` directory, never to be repeated; prose throughout the skill keeps their names — Gate A (3a), Gate B (3b) — alongside the IDs.

Three files hold every rule.

| file | holds | who reads it |
|---|---|---|
| `rules.md` | the writing rules and the gates | everyone |
| `diagrams.md` | the ASCII-figure rules and their figure catalogs (7g, 7h, 7i) | only an agent whose page will carry a figure |
| `7r-adjudications.md` | the settled adjudications registry | every agent, first, always |

**Adding a rule touches one file.** A new rule is appended to `rules.md` as a `### <ID>. <Title>` section, unless it is a diagram rule, in which case it goes in `diagrams.md`. Nothing else has to change: no file anywhere carries a rule-range enumeration, and the listing below is a convenience, not an authority — a rule missing from it still resolves by its heading in the file above.

The sample pages under `guidelines/reference/samples/` embody every rule. The closest-matching sample read in the prep pass (`guidelines/passes/00-prep.md`) is the worked example for a new page; match its structure, diagram style, code-citation density, and depth. The examples inside the rule text use ACPI and mm symbols; they illustrate the rule mechanic, which applies unchanged to every subsystem. All generated content must follow these rules.

## Convenience listing

| ID | rule | file |
|---|---|---|
| 7 | Writing rules (core) | `rules.md` |
| 7a | Prose colon idioms | `rules.md` |
| 7b | Prose lists | `rules.md` |
| 7c | Forbidden phrases checklist | `rules.md` |
| 7d | Hollow superlatives and unsupported adjectives | `rules.md` |
| 7e | Self-contained kernel-source citation | `rules.md` |
| 7f | General page rules | `rules.md` |
| 7g | General ASCII diagram principles | `diagrams.md` |
| 7h | Register and bitfield figures | `diagrams.md` |
| 7i | Other ASCII diagram patterns | `diagrams.md` |
| 7j | Behavior and construct coverage | `rules.md` |
| 7k | Driver examples | `rules.md` |
| 7l | Code-block provenance comments | `rules.md` |
| 7m | Link anchoring and exhaustive span linking | `rules.md` |
| 7n | OTHER SOURCES provenance | `rules.md` |
| 7o | Behavioral-claim verification | `rules.md` |
| 7p | Deriving from an existing page | `rules.md` |
| 7q | Rephrase recipes | `rules.md` |
| 7r | Settled adjudications registry | `7r-adjudications.md` |
| 3a | Gate A: the mechanical grep gate | `rules.md` |
| 3b | Gate B: the nine-item review sign-off | `rules.md` |
| 3c | The by-hand check procedures both gates use | `rules.md` |
