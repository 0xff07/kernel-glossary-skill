# FACT-02: Driver examples

> Was: 7k. Driver examples

**Rule:** Cite only actively-maintained drivers. A driver used as a usage example has major activity in the three years before the documented version's release (for a v7.0 tree, roughly 2023 onward), confirmed before citing via `git log` on its file or semcode `find_commit` with `path_patterns`, ignoring treewide renames, whitespace, and mechanical churn. A dormant driver may use deprecated patterns that misrepresent current usage; if no recently-active driver exercises the behavior, say so rather than reaching for a stale one.

**Rule:** Describe a driver from its own kernel source, on this page: its role (vendor, bus, device class) and its file and relevant callback cited inline. Do not point the reader to another driver or page as a substitute, and do not explain by analogy to a driver documented elsewhere.

**Before:**

```
The cs35l56 driver registers a jack-detect callback, just like the codec documented elsewhere in this knowledge base.
```

**After:**

```
The cs35l56 driver (a Cirrus Logic amplifier in sound/soc/codecs/cs35l56.c) registers a jack-detect callback through its set_jack component op.
```

**PASS CRITERIA:** For every driver cited as an example, run `git log` on its file (or semcode `find_commit` with `path_patterns`) and confirm substantive commits within roughly three years of the documented version's release, ignoring treewide renames, whitespace, and mechanical churn; record the newest substantive commit per driver. Confirm each driver is described from its own source on this page: vendor, bus or device class, its file, and the relevant callback cited inline, with no pointer to another driver or page as a substitute and no explanation by analogy. Where no recently-active driver exercises the behavior, confirm the page says so instead of citing a stale one. Pass with recency evidence recorded for every cited driver and zero by-analogy descriptions.
