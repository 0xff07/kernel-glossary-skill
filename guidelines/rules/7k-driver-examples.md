# 7k. Driver examples (mandatory)

Rule IDs (3a-3c, 7, 7a-7r) resolve via `guidelines/rules/INDEX.md`.

When a page illustrates a behavior with a concrete driver, both the choice of driver and the way the page keeps that example self-contained matter.

- Cite only actively-maintained drivers. When choosing a driver as a usage example, pick one with major activity in the three years leading up to the documented version's release (for a v7.0 tree, roughly 2023 onward). Confirm this before citing: run `git log` on the driver's file, or semcode `find_commit` with `path_patterns` for the driver's path, and check for substantive commits within the last three years (ignore treewide renames, whitespace, and other mechanical churn). Do not illustrate current behavior with a driver whose only recent commits are trivial or whose last real change is years old; a dormant driver may use deprecated patterns that misrepresent how the mechanism is used today. If no recently-active driver exercises the behavior, say so rather than reaching for a stale one.
- Describe a driver example from its own kernel source, and keep the explanation on this page. Give the driver's role (vendor, bus, device class) and cite its file and the relevant function or callback inline, so the reader needs nothing beyond this page to understand it. Do not point the reader to another driver or another page as a substitute for the explanation, and do not explain the driver by analogy to one documented elsewhere; everything the reader needs is stated here, from this driver's own code.
  - BAD: "The cs35l56 driver registers a jack-detect callback, just like the codec documented elsewhere in this knowledge base."
  - GOOD: "The cs35l56 driver (a Cirrus Logic amplifier in `sound/soc/codecs/cs35l56.c`) registers a jack-detect callback through its `set_jack` component op."
