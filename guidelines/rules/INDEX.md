# Rule index

Rules are cited by stable ID everywhere in this skill — briefs, dossiers, campaign specs, and the pass files. **IDs never renumber, and a retired ID stays retired.** One rule per file, grouped by directory; this file maps every ID — current and retired — to its home. Historical artifacts (old dossiers, campaign specs, registry rulings) cite the retired scheme; the legacy tables below keep every one of those citations resolvable.

**Adding a rule touches three things and nothing else:** the new rule file (with the house interface: title line, `> Was:` provenance, INPUT, OUTPUT, body, PASS CRITERIA), one row in the table below, and the pass step that consumes it. No file anywhere carries a rule-range enumeration.

## The directories

| directory | holds | who reads it |
|---|---|---|
| `bans/` | the prose bans | everyone |
| `page/` | page structure, citation, linking, provenance | everyone |
| `facts/` | coverage and claim verification | writers and checkers |
| `plots/` | domain model, semantics tables, organization, derivation | writers and checkers |
| `diagrams/` | the ASCII-figure rules and their catalogs | only an agent whose page will carry a figure |
| `routines/` | the checking harness: protocol, patterns, recipes | everyone who checks |
| `<dir>/<PREFIX>-WAIVERS.md` (one per rule directory) | waivers and settled rulings, harness routed by ROUTINE-01 | every agent, first, always |

Reference boundary: rules reference nothing at all; each directory's `<PREFIX>-WAIVERS.md` is harness (it may name only its own directory's rules, and the checking protocol routes adjudication to it); routines may reference rules and the waivers files, and are referenced only from the passes above the rules tree.

## Current rules

| ID | rule | file |
|---|---|---|
| BAN-01 | Core writing bans | `bans/BAN-01.md` |
| BAN-02 | Label-colon prose | `bans/BAN-02.md` |
| BAN-03 | Intro sentence + list | `bans/BAN-03.md` |
| BAN-04 | Hollow superlatives | `bans/BAN-04.md` |
| BAN-06 | Banned words | `bans/BAN-06.md` |
| BAN-07 | Hedges | `bans/BAN-07.md` |
| PAGE-01 | General page rules | `page/PAGE-01.md` |
| PAGE-02 | Self-contained kernel-source citation | `page/PAGE-02.md` |
| PAGE-03 | Code-block provenance comments | `page/PAGE-03.md` |
| PAGE-04 | Link anchoring and exhaustive span linking | `page/PAGE-04.md` |
| PAGE-05 | OTHER SOURCES provenance | `page/PAGE-05.md` |
| FACT-01 | Behavior and construct coverage | `facts/FACT-01.md` |
| FACT-02 | Driver examples | `facts/FACT-02.md` |
| FACT-03 | Behavioral-claim verification | `facts/FACT-03.md` |
| PLOT-01 | Domain-model layer | `plots/PLOT-01.md` |
| PLOT-02 | Semantics tables for state sets and taxonomies | `plots/PLOT-02.md` |
| PLOT-03 | Journey- or model-first organization | `plots/PLOT-03.md` |
| PLOT-04 | Deriving from an existing page | `plots/PLOT-04.md` |
| DIAG-01 | General ASCII diagram principles | `diagrams/DIAG-01.md` |
| DIAG-02 | Banned figure shapes | `diagrams/DIAG-02.md` |
| DIAG-03 | Register and bitfield figures | `diagrams/DIAG-03.md` |
| DIAG-04 | Other ASCII diagram patterns | `diagrams/DIAG-04.md` |
| ROUTINE-01 | The checking protocol | `routines/ROUTINE-01.md` |
| ROUTINE-04 | Scan patterns | `routines/ROUTINE-04.md` |
| ROUTINE-05 | Rephrase recipes | `routines/ROUTINE-05.md` |
| ROUTINE-07 | Figure geometry check and repair | `routines/ROUTINE-07.md` |
| — | Waivers and settled rulings (was the 7r registry) | one `<PREFIX>-WAIVERS.md` per rule directory |

Retired numbers stay retired: BAN-05, ROUTINE-02, ROUTINE-03, ROUTINE-06, PIPELINE-01, PIPELINE-02 (and the SUITE-XX/CHECK-XX/FLOW-XX schemes) are never reissued. The pipelines/ directory itself is retired; its fix-routing map lives in ROUTINE-05 and its legacy tables live here.

The sample pages under `guidelines/reference/samples/` embody every rule. The closest-matching sample read in the prep pass (`guidelines/passes/00-prep.md`) is the worked example; match its structure, diagram style, code-citation density, and depth. The examples inside the rule text use ACPI and mm symbols; they illustrate the rule mechanic, which applies unchanged to every subsystem.

## Legacy: the retired ID scheme

`rules.md` is retired: removed from the live tree, pinned in git history — 715 lines, sha256 `86bd23c9a99ed0d3d87b820f573f0ed65cf912de581350ec8bd65d470319cf8f`, retrievable with `git show 706be39:guidelines/rules/rules.md`. `diagrams.md` is retired the same way: 714 lines, sha256 `0f0c5b072d29c350d10d80e7af7cb6365717c653c514b1e0936f1ffb954af2bd`, retrievable with `git show 4039106:guidelines/rules/diagrams.md`. The gates took IDs 3a-3c in a one-time move from a former `guidelines/gates/` directory, never repeated.

Old rule IDs resolve as:

| old | new | old | new |
|---|---|---|---|
| 7 | BAN-01 | 7m | PAGE-04 |
| 7a | BAN-02 | 7n | PAGE-05 |
| 7b | BAN-03 | 7o | FACT-03 |
| 7c | ROUTINE-04 + BAN-06 + BAN-07 | 7p | PLOT-04 |
| 7d | BAN-04 | 7q | ROUTINE-05 |
| 7e | PAGE-02 | 7r | the per-directory `<PREFIX>-WAIVERS.md` files (retired file `7r-adjudications.md`) |
| 7f | PAGE-01 | 7s | PLOT-01 |
| 7g | DIAG-01 | 7t | PLOT-02 |
| 7h | DIAG-03 | 7u | PLOT-03 |
| 7i | DIAG-04 | 7v | DIAG-02 |
| 7j | FACT-01 | 3a, 3b, 3c | ROUTINE-01 (protocol) + per-rule PASS CRITERIA |
| 7k | FACT-02 | 7l | PAGE-03 |

Range phrases in historical text expand in ID order before resolving: "7 through 7d" is 7, 7a, 7b, 7c, 7d.

**The gate names.** "Gate A" (was 3a) is the mechanical sweep: ROUTINE-01's protocol executing ROUTINE-04's candidate patterns. "Gate B" (was 3b) is the review sign-off, dissolved into the owning rules' PASS CRITERIA. "3c" is the by-hand procedure set, carried by ROUTINE-01 (the prose-view builder, the link-target and excerpt procedures, the figure sweep, the regions-times-rules closure); the no-checker-script doctrine lives there too.

**Gate B's nine items** (historical dossiers and specs cite them by number) resolve to the owning rules:

| item | was | owning rules |
|---|---|---|
| 1 | catalog-to-DETAILS parity | PAGE-02 (with FACT-01) |
| 2 | grounded, non-fabricated code | PAGE-02, PAGE-03 |
| 3 | every symbol linked, keyword kept | PAGE-01, PAGE-04 |
| 4 | what-does-what DETAILS headings, journey- or model-first | BAN-01, PLOT-03 |
| 5 | no negative constructions or anthropomorphic verbs | BAN-01 |
| 6 | full coverage and domain model | FACT-01, PLOT-01, PLOT-02 |
| 7 | driver examples actively maintained | FACT-02 |
| 8 | ASCII diagrams | DIAG-01, DIAG-02, DIAG-03, DIAG-04 |
| 9 | behavioral-claim audit | FACT-03 |

The ownership, independence, and evidence discipline that prefaced the nine items is ROUTINE-01's protocol. 3c's numbered procedures: item 1 (link targets) → ROUTINE-01 with PAGE-04's criteria; item 2 (excerpt verbatimness) → ROUTINE-01 with PAGE-02/PAGE-03's criteria; item 3 (candidates and the prose view) → ROUTINE-01 + ROUTINE-04.
