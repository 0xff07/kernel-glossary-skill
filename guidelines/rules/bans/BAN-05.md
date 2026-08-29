# BAN-05

> Was: Scan patterns

**Words to watch:** The reasoning (any case, with or without colon), The intent:, The asymmetry:, The fix:, The point is:, The takeaway:, The pattern is:, Two-phase pattern:, is the key:, is essential:, is explicit:, is significant:, is conservative:, is deliberate:, is the linchpin:, is asymmetric:, is intentional:, is correct:, becomes clear here:, says: ", spells this out: ", makes explicit: ", makes the trade-off explicit: ", Comment: "

**Caution:**: Two need care: a label-colon can sit anywhere in a prose sentence, not merely at its start, `Comment: "` in prose differs from the LINUX KERNEL bullet form `[symbol]: bit 0xN. Comment: "..."`, which is a catalog entry and acceptable. The "intro sentence + list" shape of 7b and the colon-introduced list ("X is called from N places: A, B, C") belong on the same sweep.

**PASS CRITERIA:** The sweep itself is the check: confirm every pattern in the words-to-watch list was run, case-insensitively, over a prose view of the page rather than the raw file, and never anchored to line start (one unwrapped line per paragraph makes an anchored pattern blind to every mid-paragraph hit; the view builder and its rationale live in `../rules.md` under 3c). Confirm the intro-sentence-plus-list shape (BAN-03) and the colon-introduced list rode the same sweep. Adjudicate every candidate against the rule exemptions and the settled adjudications registry (`../7r-adjudications.md`); the LINUX KERNEL bullet form `[symbol]: bit 0xN. Comment: "..."` is a catalog entry and acceptable. Pass when every candidate is either fixed with a BAN-QUICKFIX recipe or recorded as exempt, and no compliant construct was reworded just to silence a pattern.
