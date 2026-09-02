# Rule index

Rules are cited by stable ID everywhere in this skill: briefs, dossiers, campaign specs and pass files. IDs never renumber, and a retired ID stays retired. One rule per file; this file maps every ID, current and retired, to its home, so historical dossiers, specs and log entries still resolve. Adding a rule touches the new rule file, one row below, and the pass step that consumes it, and nothing else.

## What a writer reads, in order

1. `WRITING.md`: what a page is for. Read first.
2. `BANS.md`: what is trimmed from every sentence, with each ban's fix and exemptions.
3. `page/` and `facts/`: the mechanics a page must prove (excerpts, provenance, links, table cells, sources; coverage, driver examples, claims, the activation delta). `plots/PLOT-04.md` only when the page derives from existing material.
4. `diagrams/`, only when the page will carry a figure.
5. At the exit suite, not before: the harness in `routines/`, the settled rulings in `WAIVERS.md`, and the dossier spec in `../passes/dossier.md`.

## Current rules

| ID | rule | file |
|---|---|---|
| WRITING | What a page is for | `WRITING.md` |
| BANS | What is trimmed from every sentence | `BANS.md` |
| PAGE-01 | General page rules | `page/PAGE-01.md` |
| PAGE-02 | Self-contained kernel-source citation | `page/PAGE-02.md` |
| PAGE-03 | Code-block provenance comments | `page/PAGE-03.md` |
| PAGE-04 | Link anchoring and exhaustive span linking | `page/PAGE-04.md` |
| PAGE-05 | OTHER SOURCES provenance | `page/PAGE-05.md` |
| PAGE-06 | Linked code in table cells | `page/PAGE-06.md` |
| FACT-01 | Behavior and construct coverage | `facts/FACT-01.md` |
| FACT-02 | Driver examples | `facts/FACT-02.md` |
| FACT-03 | Behavioral-claim verification | `facts/FACT-03.md` |
| FACT-04 | Activation delta | `facts/FACT-04.md` |
| PLOT-04 | Deriving from an existing page | `plots/PLOT-04.md` |
| DIAG-01 | General ASCII diagram principles | `diagrams/DIAG-01.md` |
| DIAG-02 | Banned figure shapes | `diagrams/DIAG-02.md` |
| DIAG-03 | Register and bitfield figures | `diagrams/DIAG-03.md` |
| DIAG-04 | Other ASCII diagram patterns | `diagrams/DIAG-04.md` |
| ROUTINE-01 | The checking protocol | `routines/ROUTINE-01.md` |
| ROUTINE-04 | Candidate generators | `routines/ROUTINE-04.md` |
| ROUTINE-07 | Figure geometry check and repair | `routines/ROUTINE-07.md` |
| WAIVERS | Settled rulings for the page, fact, plot and diagram rules | `WAIVERS.md` |

## Reference boundary

A rule file (WRITING, BANS, PAGE, FACT, PLOT-04, DIAG) cites no other rule and no shared file, beyond the retired IDs its own `> Was:` provenance line names. `WAIVERS.md` is harness and may name the rules it modifies. Routines cite rules, the harness and each other. The passes above the rules tree cite everything. Each rule directory's README carries the grep that keeps its rules clean.

## Retired IDs

| retired | resolves to |
|---|---|
| PAGE-07 (prose explains what it quotes), PAGE-08 (leading paragraphs open on purpose, never on a count), PLOT-01 (domain-model layer), PLOT-02 (semantics tables for state sets and taxonomies), PLOT-03 (journey- or model-first organization) | WRITING |
| BAN-01 (core writing bans), BAN-02 (label-colon prose), BAN-03 (intro sentence plus list), BAN-04 (hollow superlatives), BAN-06 (banned words), BAN-07 (hedges), BAN-08 (run-on enumerations), BAN-WAIVERS | BANS |
| ROUTINE-05 (rephrase recipes) | BANS, the fix column |
| PAGE-WAIVERS, FACT-WAIVERS, PLOT-WAIVERS, DIAG-WAIVERS | WAIVERS |
| BAN-05, ROUTINE-02, ROUTINE-03, ROUTINE-06, PIPELINE-01, PIPELINE-02, the SUITE-XX, CHECK-XX and FLOW-XX schemes, the CERTIFIED state, the verify pass, the fix-list pass | retired without a successor; never reissued |

The pre-split files are pinned in git history: `rules.md` (715 lines, sha256 `86bd23c9a99ed0d3d87b820f573f0ed65cf912de581350ec8bd65d470319cf8f`, `git show 706be39:guidelines/rules/rules.md`) and `diagrams.md` (714 lines, sha256 `0f0c5b072d29c350d10d80e7af7cb6365717c653c514b1e0936f1ffb954af2bd`, `git show 4039106:guidelines/rules/diagrams.md`). Their IDs resolve as:

| old | new | old | new |
|---|---|---|---|
| 7 | BANS | 7m | PAGE-04 |
| 7a | BANS | 7n | PAGE-05 |
| 7b | BANS | 7o | FACT-03 |
| 7c | BANS and ROUTINE-04 | 7p | PLOT-04 |
| 7d | BANS | 7q | BANS |
| 7e | PAGE-02 | 7r | WAIVERS, and BANS for the bans' rulings |
| 7f | PAGE-01 | 7s | WRITING |
| 7g | DIAG-01 | 7t | WRITING |
| 7h | DIAG-03 | 7u | WRITING |
| 7i | DIAG-04 | 7v | DIAG-02 |
| 7j | FACT-01 | 7l | PAGE-03 |
| 7k | FACT-02 | 3a, 3b, 3c | ROUTINE-01 and the per-rule PASS CRITERIA |

Range phrases in historical text expand in ID order before resolving: "7 through 7d" is 7, 7a, 7b, 7c, 7d. "Gate A" (was 3a) is the batched sweep, ROUTINE-01 running BANS' patterns. "Gate B" (was 3b) was the review sign-off; its nine items resolve to PAGE-02 with FACT-01 (1), PAGE-02 and PAGE-03 (2), PAGE-01 and PAGE-04 (3), BANS for heading shape and WRITING for the spine (4), BANS (5), FACT-01 and WRITING (6), FACT-02 (7), DIAG-01 through DIAG-04 (8), FACT-03 (9). "3c" was the by-hand procedure set, carried by ROUTINE-01 with the PAGE-04, PAGE-02 and PAGE-03 criteria and by ROUTINE-04.
