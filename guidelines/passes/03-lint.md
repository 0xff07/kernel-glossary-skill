# Pass 03: style lint

Purpose: an independent, fresh-context sweep of a finished page for prose and form defects — the classes a writer reliably misses in its own prose. This pass finds and adjudicates; it does not edit. Substance (parity, excerpt grounding, anchor correctness, counts, behavioral claims) is the writer's to deliver (pass 02) and the verifier's to audit (pass 04); this pass never re-derives facts, and a substance defect it happens to notice is reported for the verifier, never fixed here.
Inputs: the draft page; the 7r registry; the writing rules the sweeps exercise.
Outputs: an adjudicated finding list at `progress/<campaign>/<page-slug>.lint.md` (the run's artifact directory, `guidelines/campaign/progress-layout.md`): every candidate found, each judged against the rule text and the 7r registry, with a proposed 7q-recipe fix for confirmed findings and reasoning for exempt ones. The page itself is not modified by this pass.
Run by: single-agent mode inline (a solo agent applies its own confirmed findings afterward and continues); in a campaign a style-lint agent on a different, cheaper model with fresh context (`guidelines/agents/lint.md`), whose confirmed findings the orchestrator reviews and hands to a patch agent (`guidelines/agents/patcher.md`).
Next: patch application (campaigns), then pass 04 (`guidelines/passes/04-verify.md`).

Rule IDs (7, 7a-7r) resolve via `guidelines/rules/INDEX.md`; 7g-7i live under `guidelines/diagrams/`.

Read `guidelines/rules/7r-adjudications.md` before touching the page, and judge every candidate against it BEFORE proposing a fix. A hit on an exempt construct is a false candidate, and proposing to reword a compliant phrase to silence a pattern is itself a defect.

## Steps

1. Gate A candidate greps, fence-aware, per `guidelines/gates/mechanical-checks.md` item 3: em-dashes, label-colon shapes, hedges, the arm-word ban, banned words, negative constructions, internal `.md` links, banned heading shapes, boldface.
2. Read-through sweeps for what the greps cannot express: 7b intro-sentence-plus-list shapes, 7d superlatives judged in context, anthropomorphic verbs (`lives`/`sits`/`wants` for code or data placement; `walk` outside data-structure traversal), and heading shape (declarative subject-verb-object, no bare nouns or symbol names; heading truth against section content stays with the verifier's Gate B item 4/9).
3. Exhaustive 7m span-form pass: every occurrence of every kernel symbol outside fenced blocks is linked, INCLUDING repeats, `CONFIG_*` options, generic primitives, field paths, and named ops-struct members, with `struct`/`enum` keywords kept (7f). Exemptions and rulings come from the 7r registry. Report each bare span as a finding with the correct link target stated; whether an existing anchor lands on the right disk line is anchor correctness — the writer's exit suite and the verifier own that, not this pass.
4. For each confirmed finding, state the fix with the 7q recipes, precisely enough to apply without judgment (the patch agent applies it verbatim). For each exempt candidate, state the ruling applied.
5. Do not edit the page, do not re-derive counts or claims, do not audit parity, and do not byte-check excerpts; those live in passes 02 and 04. A suspected substance defect noticed in passing goes in a SUBSTANCE NOTES section of the report for the verifier. Anything you persist goes in `progress/<campaign>/` under a unique `<page-slug>.`-prefixed name (shared names have collided between concurrent agents).
