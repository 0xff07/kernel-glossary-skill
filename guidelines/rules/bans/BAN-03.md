# BAN-03: Intro sentence + list

> Was: 7b. Intro sentence + list

**INPUT:** Every bullet and numbered list in DETAILS, SUMMARY, and the lead summary paragraph, read in place (this is a read-through; no pattern expresses the shape); catalog lists and tables are out of scope.

**OUTPUT:** Exposition carried in flowing paragraphs only: no intro-sentence-plus-list remains outside the catalog sections.

**Problem:**

1. Generated prose presents an explanation as an intro sentence followed by a bullet or numbered list.
2. In DETAILS, SUMMARY, and the lead summary paragraph, fold the items into a single flowing paragraph.
3. The forbidden shape is "<noun phrase ending in a period or colon> + <bullet/numbered list>" used as exposition; phrases that head such lists ("Two notable details.", "Three layers stack.", "Four cases run from strongest to weakest.", "Concrete uses.", "Five upfront refusals.") are banned even with a period.

**Before:**

```
Two details deserve attention.

- advance_transaction writes EC_DATA only while IBF is clear.
- It reads EC_DATA only while OBF is set.
```

**After:**

```
advance_transaction writes the next byte to EC_DATA only while IBF reads 0, and reads a result byte only while OBF reads 1, so the host never races the controller.
```

Do not flag the H3 catalog lists in LINUX KERNEL (grouped by file or functional area as the exemplar pages under `docs/sound/` do: `Substream and container types (pcm.h)`, `Lifecycle helpers (sound/core/init.c)`, `Trigger commands (include/sound/pcm.h)`) or the bullet lists in KERNEL DOCUMENTATION and OTHER SOURCES: those are reference catalogs and remain as lists. Tables remain as tables. The ban covers prose-explanation lists only.

**PASS CRITERIA:**

1. This is a read-through check; no grep expresses the shape.
2. Read every bullet and numbered list in DETAILS, SUMMARY, and the lead summary paragraph: a list preceded by an intro noun-phrase sentence or colon and used as exposition is a hit (the banned header phrases like "Two details deserve attention." included), and the fix folds the items into one flowing paragraph.
3. The LINUX KERNEL catalog lists, the KERNEL DOCUMENTATION and OTHER SOURCES bullets, and tables are exempt.
4. Pass when no prose-explanation list remains outside the catalog sections.
