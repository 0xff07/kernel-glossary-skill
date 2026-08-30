# FACT-02: Driver examples

> Was: 7k. Driver examples

**INPUT:** Every driver the page cites as an example, that driver's own source, and its file's git history (`git log`, or semcode `find_commit` with `path_patterns`).

**OUTPUT:** Only recently-active drivers cited, each described from its own source on this page (vendor, bus or device class, file, and callback); delivered with the newest-substantive-commit record per driver and zero by-analogy descriptions.

**Rule:**

1. Cite only actively-maintained drivers.
2. A driver used as a usage example has major activity in the three years before the documented version's release (for a v7.0 tree, roughly 2023 onward), confirmed before citing via `git log` on its file or semcode `find_commit` with `path_patterns`, ignoring treewide renames, whitespace, and mechanical churn.
3. A dormant driver may use deprecated patterns that misrepresent current usage; if no recently-active driver exercises the behavior, say so rather than reaching for a stale one.

**Rule:**

1. Describe a driver from its own kernel source, on this page: its role (vendor, bus, device class) and its file and relevant callback cited inline.
2. Do not point the reader to another driver or page as a substitute, and do not explain by analogy to a driver documented elsewhere.

**Before:**

```
The cs35l56 driver registers a jack-detect callback, just like the codec documented elsewhere in this knowledge base.
```

**After:**

```
The cs35l56 driver (a Cirrus Logic amplifier in sound/soc/codecs/cs35l56.c) registers a jack-detect callback through its set_jack component op.
```

**PASS CRITERIA:**

1. For every driver cited as an example, run `git log` on its file (or semcode `find_commit` with `path_patterns`) and confirm substantive commits within roughly three years of the documented version's release, ignoring treewide renames, whitespace, and mechanical churn; record the newest substantive commit per driver.
2. Confirm each driver is described from its own source on this page: vendor, bus or device class, its file, and the relevant callback cited inline, with no pointer to another driver or page as a substitute and no explanation by analogy.
3. Where no recently-active driver exercises the behavior, confirm the page says so instead of citing a stale one.
4. Pass with recency evidence recorded for every cited driver and zero by-analogy descriptions.
