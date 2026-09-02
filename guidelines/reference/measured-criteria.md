# Measured criteria

Rules are cited by stable ID; `guidelines/rules/INDEX.md` maps every ID to its file.

The exemplar pages under `docs/sound/` (113 pages, written 2026-06-25 to 27) are what a writer reads before writing (`guidelines/passes/00-prep.md`). Their measured shape is calibration for what "in-depth, fine-grained" measures as on this corpus, context for a writer's expectations, never a criterion:

| exemplar | c blocks | Elixir links | figures |
|---|---|---|---|
| `docs/sound/alsa/pcm/pcm-substream.md` | 24 | 358 | 6 |
| `docs/sound/soundwire/bus-device-model.md` | 21 | 310 | 5 |
| `docs/sound/alsa/card.md` | 23 | 375 | 8 |
| `docs/sound/alsa/pcm/pcm-state-machine.md` | 12 | 141 | 6 |
| `docs/sound/hda/hdac-core.md` | 28 | 385 | 10 |
| `docs/sound/formats/i2s.md` | 9 | 103 | 8 |
| `docs/sound/flows/playback.md` | 32 | 313 | 6 |
| `docs/sound/flows/suspend.md` | 29 | 280 | 5 |
| `docs/sound/alsa/pcm/pcm-ops.md` | 35 | 433 | 5 |
| `docs/sound/asoc/controls/kcontrol-handlers.md` | 37 | 377 | 6 |
| `docs/sound/dapm/power/power-engine.md` | 30 | 302 | 8 |

Across the 113 pages the per-page ranges are 4 to 37 code blocks, 79 to 498 Elixir links and 2 to 10 figures. The corpus carries 2,451 excerpts at a median of 16 lines, 88 prose words per code block, a binding sentence ending in a colon before 98 of every 100 excerpts, and a member named beside 84 of every 100 definition excerpts. These numbers are outcomes, not targets: a page ends when coverage is complete, and a conforming page on a narrow mechanism measures below every range above. A page's line count measures nothing and is not recorded.

## The coverage tripwires

- Blocks per catalog entry below 1.0: fewer fenced C blocks than LINUX KERNEL catalog entries means unpaired symbols, because every symbol needs a definition and a usage excerpt (PAGE-02). The sound exemplars mostly sit below this wire (median 0.76 over 113 pages) because their catalogs are broader than their excerpts; that breadth is not imitated, and the wire binds every new page.
- Catalog coverage of scope (fill-or-descope): every anchor symbol in the page's scope statement and every symbol in the dossier's SYMBOLS section is either cataloged or explicitly de-scoped in the writer's report, with the reason (FACT-01).
- A catalog that shrank across a rewrite without reported cuts (PLOT-04).

A tripped wire forces the parity audit and, for a derived page, the PLOT-04 disposition list. The fix is completing coverage or cutting scope explicitly; never padding prose and never silent thinning.

## The excerpt criteria

An excerpt shows enough of the construct to carry the point the prose makes about it: a byte-exact block holding a signature and an opening brace proves the provenance line and teaches nothing. Measured at v7.0, an excerpt unit runs a median of 15 lines in `docs/acpi/` and 16 in `docs/sound/`; units of five lines or fewer are 14% and 10% of the total, a legitimate residue of one-line defines and prototypes, not a budget for truncated bodies. The check is per unit, never per page: a unit that opens a function, struct, enum or union continues far enough to show the behavior the prose asserts, cutting from the middle with the house `...` marker rather than stopping at the brace.

The paragraph beside an excerpt explains it (WRITING rule 3); ROUTINE-04's member generator counts the members it names, and `guidelines/LESSONS.md` keeps the per-era measurement that produced the rule.

## The depth rules

- Definition plus usage, per symbol: every LINUX KERNEL symbol gets its definition excerpt and at least one real usage excerpt in DETAILS (PAGE-02).
- Full site enumeration with counts: when prose says a helper is used at N sites, N is a verified count and the sites are enumerated with per-site location links, or a representative spread is cited with the total stated (FACT-01, FACT-03, PAGE-04).
- Every hard-coded limit named with its value and its defining file and line (FACT-01).
- Lifecycle and state transitions in full: allocation, initialization, teardown order, the serializing locks, reference counting, and every state a tracked field moves through with the transition drivers cited (FACT-01).
