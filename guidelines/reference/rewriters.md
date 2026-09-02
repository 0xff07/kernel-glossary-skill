# Rewriter skills

A rewriter is an external prose-style skill a writer would read at compose time. This table is the only switch, the setting is global, and a campaign spec or a slice invocation never carries one.

| rewriter | sibling skill | default | governs |
|---|---|---|---|
| humanizer | `humanizer` (github.com/blader/humanizer v2.11.2; 35 patterns from Wikipedia's "Signs of AI writing") | OFF | AI-writing tells: inflated claims, filler, qualifier stacking, repeated openings, punctuation habits |
| asd-ste100 | `asd-ste100` (github.com/danyuchn/asd-ste100-skill v0.4.0) | OFF | controlled-language shape: sentence length, active voice, one instruction per sentence, noun clusters |

Both are OFF. With no rewriter ON, the writer reads nothing beyond this table, and `guidelines/rules/BANS.md` alone governs style. The humanizer was ON from 2026-09-01 to 2026-09-02; `guidelines/LESSONS.md` records what it did to the pages written under it.

Switching one on: set the column to ON and list here the bans it displaces. The writer then reads that skill's SKILL.md in full at compose time; the rewriter outranks BANS where the two disagree and outranks nothing else (facts, excerpts, citations, page structure and figures stay with the house rules, and where a rewriter contradicts a PAGE, FACT or DIAG rule the house rule governs). A skill qualifies only if it rewrites without inventing, preserves modality, is readable as rules rather than as a service, and has a fixed, citable source.
