# Writing rules and gates

Every criterion a generated page is judged against, except the diagram rules (see `diagrams.md`) and the settled adjudications registry (see `7r-adjudications.md`, which is the mandatory first read for every agent). Rule IDs are stable identifiers and never renumber: briefs, dossiers, and campaign specs cite rules by ID. `INDEX.md` maps every ID to its section here.

## Style and prose

How a page reads: sentence shape, banned constructions, page structure, and how every kernel symbol is linked. The writer sweeps these classes itself with 3c's procedure before reporting done, and the check pass reproduces them independently.

### 7. Writing rules (mandatory)

The composing preamble and the map of every rule ID are in `guidelines/rules/INDEX.md`.

- No em-dashes. Use parentheses instead: "CC (Command Completed)" not "CC --- Command Completed"
- No boldface (`**...**`)
- No negative constructions. Write "It is synchronous" not "It is synchronous, not asynchronous"
- No anthropomorphic or casual placement verbs. Code does not "live" anywhere: a symbol "is defined in" a file, a value "is held in" or "is represented by" a struct. Do not use "walk" for a scalar or state field changing value; a state field "transitions through" or "advances through" its values. Reserve "walk" for traversing a data structure (walk a list, the tree, the page tables, or the ACPI namespace), which is its established kernel meaning.
- No "vtable". A struct that aggregates function pointers is a "function pointer struct" (or its concrete type name, e.g. `struct file_operations`), never a "vtable". "vtable" is a C++ term and is not kernel terminology.
- No question-style or "Why X does Y" / "How X works" / "Where X happens" framings as H3 or H4 headings in DETAILS, SUMMARY, or any body section. Write declarative statements. The H3 catalog labels in LINUX KERNEL (e.g., `### Detection and dispatch (evgpe.c)`, `### _Lxx: level-triggered GPE method`) are fine and should be kept; this rule only forbids question/explanation framings.
  - BAD: `### Why _Exx clears status before the method`
  - GOOD: `### _Exx clears status before the method runs`
  - BAD: `### How acpi_ev_gpe_dispatch routes the event`
  - GOOD: `### acpi_ev_gpe_dispatch routes by dispatch type`
  - BAD: `### Why the EC uses a raw handler`
  - GOOD: `### EC installs a raw GPE handler`
- Every DETAILS H3/H4 heading is a declarative "what-does-what" statement (a subject performing an action on an object), never a bare noun or a bare symbol name. A reader should learn what the symbol does from the heading alone. This applies to DETAILS subsection headings; the H3 catalog labels in LINUX KERNEL (grouped by file or functional area, for example `### Tree store primitives (vma.h)`) stay as noun-phrase labels and are exempt.
  - BAD: `### vma_state_init` or `### The slab cache`
  - GOOD: `### vma_state_init creates the vm_area_cachep slab`
  - BAD: `### vm_refcnt`
  - GOOD: `### vm_refcnt encodes attach state and the per-VMA lock in six values`

### 7a. Prose colon idioms (mandatory)

Body prose (everything outside H1, H2, H3, H4 headings, fenced code blocks, ASCII diagrams, list bullets, table cells, and Elixir links) must never use the "label-colon-explanation" idiom. The colon-followed-by-clause pattern in prose is banned. State the same content as a plain declarative sentence.

This applies to forms like:

- "X: Y." where X is a noun phrase and Y is the explanation. BAD: `Two-phase handshake: a status read, then a gated write.` GOOD: `The handshake has two phases. advance_transaction reads EC_SC first, and writes the next byte only when IBF is clear.`
- "X is Y: Z." BAD: `The asymmetry: an edge GPE clears status before the method, a level GPE after.` GOOD: `An edge-triggered GPE clears its status before the method runs; a level-triggered GPE clears it after.`
- "X is the key: Y" / "X is essential: Y" / "X is explicit: Y" / "X is significant: Y" / "X is conservative: Y" / "X is deliberate: Y" / "X is the linchpin: Y" / "X is asymmetric: Y" / "X is intentional: Y" / "X is correct: Y" / "X becomes clear here: Y". BAD: `The IBF gate is essential: IBF stays 1 until the EC consumes the byte just written.` GOOD: `IBF stays 1 until the EC consumes the byte just written, so advance_transaction sends the next byte only when IBF reads 0.`
- "The intent: Y" / "The reasoning: Y" / "The result: Y" / "The fix: Y" / "The condition is: Y" / "The order of operations matters: Y" / "The pattern is: Y" / "The point is: Y" / "The takeaway is: Y". BAD: `The reasoning: a level source stays asserted until the AML quiesces it.` GOOD: `A level-triggered source stays asserted until the AML quiesces the device.`
- "X says: <quote>" / "X makes Y explicit: <quote>" / "X spells this out: <quote>" / "Comment: <quote>" introducing direct quotes. BAD: `The comment "Note: disables and clears all GPEs in the block" is the key: events only flow after an explicit enable.` GOOD: `According to the comment "Note: disables and clears all GPEs in the block", events only flow after an explicit enable.`
- "X is called from N places: A, B, C." Replace with "X is called from N places. A does ..., B does ..., C does ...". The list-after-colon shape is banned even when the items are short.

Never editorialise with "The reasoning:" or any synonym ("The rationale is", "The motivation:", etc.) that asserts authorial reasoning. The page describes what the code does; if a comment or commit message states a rationale, quote it via "According to the comment <quote>, ..." instead. When you remove a colon-label, state the underlying mechanic as a plain declarative sentence; do not swap the colon for "X matters because Y" or "X is what makes Y", which asserts importance the same way and is banned by 7d.

The colon is acceptable inside H3/H4 headings (catalog labels like `### _Lxx: level-triggered GPE method`), inside Elixir link titles, inside code blocks, inside URLs, inside ratios (`M:N`), and after Markdown list bullets when the item is a catalog entry in the LINUX KERNEL or KERNEL DOCUMENTATION section. It is banned in flowing prose paragraphs and in the lead summary paragraph.

### 7b. Prose lists (mandatory)

Body prose in DETAILS, SUMMARY, and the lead summary paragraph must not use the "intro sentence + list" pattern when the list is explanatory. Fold the items into a single flowing paragraph.

- BAD:

  ```
  Two details deserve attention.
  
  - advance_transaction writes EC_DATA only while IBF is clear.
  - It reads EC_DATA only while OBF is set.
  ```

- GOOD:

  ```
  advance_transaction writes the next byte to EC_DATA only while IBF reads 0, and reads a result byte only while OBF reads 1, so the host never races the controller.
  ```

The forbidden shape is "<noun phrase ending in a period or colon> + <bullet/numbered list>" used as exposition. Phrases that head such lists ("Two notable details.", "Three layers stack.", "Four cases run from strongest to weakest.", "Concrete uses.", "Five upfront refusals.") are banned even with a period. Restate as a paragraph.

The H3 catalog lists in LINUX KERNEL (grouped by file or functional area as the sample pages do, for example `EC_SC status bit macros`, `Port accessors`, `Transaction state machine`) and the bullet lists in KERNEL DOCUMENTATION and OTHER SOURCES are reference catalogs and remain as lists. Tables remain as tables. This rule applies only to prose-explanation lists, not to reference catalogs.

### 7c. Forbidden phrases checklist

Before writing any body paragraph, scan for these patterns and rewrite if any appear:

- A label-colon anywhere in a prose sentence, not merely at its start. Do NOT scan for this with a line-anchored pattern: 7f puts each paragraph on one unwrapped line, so an anchored pattern sees only a paragraph's first clause and misses the rest of the class. 3c's prose view is the procedure that actually reaches it.
- `The reasoning` (in any case, with or without colon)
- `The intent:` / `The asymmetry:` / `The fix:` / `The point is:` / `The takeaway:` / `The pattern is:` / `Two-phase pattern:`
- `is the key:` / `is essential:` / `is explicit:` / `is significant:` / `is conservative:` / `is deliberate:` / `is the linchpin:` / `is asymmetric:` / `is intentional:` / `is correct:` / `becomes clear here:`
- `Comment: "` introducing a quote in prose (different from the LINUX KERNEL bullet form `[symbol]: bit 0xN. Comment: "..."` which is a catalog entry and acceptable)
- `says: "` / `spells this out: "` / `makes explicit: "` / `makes the trade-off explicit: "` introducing a direct quote in prose
- `X is called from N places: A, B, C` (intro-colon list)
- Any `"intro sentence." + bullet/numbered list` shape in DETAILS, SUMMARY, or lead summary paragraphs

If any of these appear in body prose, rewrite the paragraph as plain declarative sentences. Quote comments with "According to the comment <quote>, ..." or "The comment reads <quote>." instead of label-colon framing.

Do not use these words in body prose; each asserts a framing without naming a mechanism. Replace each with the concrete rule, count, or helper it stands in for.

- "contract" (including "the X, Y, Z contract"): name the actual precondition, guarantee, rule, or invariant. BAD: `The reset, duplicate, destroy contract spans every per-object state.` GOOD: state the reset rule, the duplicate rule, and the destroy rule each path follows.
- "tally": use "count" or "running count". BAD: `the running tally of VMAs`. GOOD: `the running count of VMAs`.
- "canonical": name the helper or path plainly. BAD: `the canonical helper is vma_link() in mm/vma.c`. GOOD: `the helper that performs it is vma_link() in mm/vma.c`.
- "arm" / "arms" for a case of a union, a branch of a conditional, a side of a split, or one member of a pair of code paths: use "branch", "case", "side", "leg", "half", or the concrete symbol name instead. BAD: `the write-fault arm of do_wp_page`. GOOD: `the write-fault branch of do_wp_page`. CPU-architecture names (Arm, ARM64, arm64) and verbatim quotes from kernel source or commit messages are exempt.

Do not hedge with vague frequency or generality words in prose ("usually", "typically", "generally", "often", "normally", "commonly", "mostly", "in practice", "tends to", "on a hot cpu"). Each dodges the actual condition the code tests. Name that condition instead. BAD: `A vm_area_alloc() on a hot cpu usually takes a ready object from the per-cpu sheaf without locking a shared slab.` GOOD: `A vm_area_alloc() takes a ready object from the per-cpu main sheaf without locking a shared slab while that sheaf is non-empty, and reaches the shared slab only to refill an empty sheaf.` A frequency word reproduced verbatim from kernel source inside a fenced block, or a genuine measured statistic that cites a counter or benchmark, is exempt.

### 7d. Hollow superlatives and unsupported adjectives (mandatory)

Never characterize a kernel construct with a ranking adjective unless the same sentence (or the next one) names the concrete mechanic that justifies the ranking. Each kernel symbol, mode, or path is unique by definition; saying it is "the most X" or "the least Y" or "the strongest Z" without explaining the comparison adds zero information and is banned.

Banned phrasings (when not immediately followed by the supporting mechanic):

- "the most invasive" / "the most fragmenting" / "the most aggressive" / "the most consequential" / "the most preferred" / "the least preferred" / "the most expensive" / "the cheapest"
- "the cheap path" / "the slow path" / "the fast path" used as standalone characterization (use only when "fast" or "slow" is a defined kernel term, e.g. "fast path" of a specific lock implementation)
- "the strongest guarantee" / "the weakest guarantee" / "the strongest anti-fragmentation guarantee"
- "the worst outcome" / "the best outcome"
- "the entire performance benefit" / "the entire correctness benefit"
- "the key invariant" / "the key difference" / "the key innovation" / "the key role" / "the design assumption" / "the design intent"
- "X matters" / "X matters because Y" / "X is what makes Y" / "what makes X work" (asserts importance instead of stating the mechanic)
- "the only mode that ..." (when the same is trivially true of every other mode under some other framing)
- "elaborate", "elegant", "fundamental", "cornerstone", "linchpin", "crucial", "critical" used as standalone characterizations

Acceptable forms:

- BAD: "acpi_ev_gpe_dispatch is the most invasive handler path."
- GOOD: "acpi_ev_gpe_dispatch disables the GPE with acpi_hw_low_set_gpe(), clears edge-triggered status with acpi_hw_clear_gpe(), then routes by dispatch type."
- BAD: "A raw handler is the cheap path through acpi_ev_detect_gpe()."
- GOOD: "acpi_ev_detect_gpe() invokes the raw handler directly at interrupt level, skipping the disable/clear/re-enable protocol that acpi_ev_gpe_dispatch() runs."
- BAD: "This is the strongest guarantee against a lost edge."
- GOOD: "Clearing an edge-triggered GPE's status before queueing the method ensures an edge arriving during servicing re-latches instead of being lost."
- BAD: "the key difference from a method GPE"
- GOOD: "a method GPE queues acpi_ev_asynch_execute_gpe_method() via acpi_os_execute(); a raw-handler GPE calls the handler synchronously at interrupt level."

Test for any adjective in body prose: ask "would the sentence still convey the mechanic if I deleted this adjective?" If yes, delete it. If no, replace the adjective with the actual mechanic. Hollow superlatives that cannot be reduced to a concrete code-level fact must not appear in body prose at all.

The two legitimate exceptions are direct quotes from kernel source comments and direct quotes from commit messages or LKML threads, which are reproduced verbatim even when they contain superlatives the rule would otherwise forbid.

### 7f. General page rules (mandatory)

These apply to every page regardless of subsystem.

- H1 is always the topic name only
- Immediately below the H1, before the summary paragraph, every generated page carries this exact AI-generated-content caution blockquote, reproduced verbatim (including the repeated final line):

  ```
  > CAUTION: AI-GENERATED CONTENT
  >
  > STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.
  ```
- `Documentation/` references go in KERNEL DOCUMENTATION, never in OTHER SOURCES
- If an existing page has `Documentation/` links in OTHER SOURCES (or using `docs.kernel.org` / `kernel.org/doc` URLs), move them to KERNEL DOCUMENTATION. Do not convert existing URLs; instead, add a new Elixir cross referencer reference entry pointing to the same in-tree kernel doc file.
- No hard line wrapping in prose. Each paragraph of prose text must be a single long line, with line breaks only between paragraphs. Do not wrap lines at 80 or any other column width. Code blocks (between ` ``` ` markers), ASCII diagrams (indented lines), list items, and table rows are exempt from this rule.
- Every mention of a kernel symbol (function, macro, struct, enum, typedef) must be an Elixir cross referencer link. No exceptions. This applies to every inline code span (`` ` `` ... `` ` ``) in every section of the page: SUMMARY, LINUX KERNEL, INTERFACES, DETAILS, and prose paragraphs. This includes inline code with arguments such as `` `func(arg1, arg2)` `` in INTERFACES sections. Write [`function_name()`](https://elixir.bootlin.com/linux/v7.0/source/path/to/file.c#L123) instead of bare `function_name()`. Write [`func(arg1, arg2)`](https://elixir.bootlin.com/linux/v7.0/source/path/to/file.c#L123) instead of bare `func(arg1, arg2)`. Write [`struct foo`](https://elixir.bootlin.com/linux/v7.0/source/path/to/file.h#L45) instead of bare `struct foo`. Write [`MACRO_NAME`](https://elixir.bootlin.com/linux/v7.0/source/path/to/file.h#L78) instead of bare `MACRO_NAME`. The only place bare symbol names are acceptable is inside fenced code blocks (` ``` `) that show code snippets or struct definitions. If a symbol appears multiple times on the same page, every occurrence outside a code block must be linked (repeat the link). If you cannot determine the file and line number for a symbol, look it up before writing it. If it truly cannot be found in the kernel source (e.g., it is a spec-defined ACPI method name like `_PS0` or a hardware register name like `SLP_EN`), it may remain unlinked, but add a comment noting it is a spec/hardware name.
- When referencing a struct or enum type, always include the `struct` or `enum` keyword (e.g., `struct acpi_gpe_event_info`, `enum ec_command`). Do not omit the keyword unless the type is a typedef. This applies everywhere: LINUX KERNEL entries, SUMMARY, INTERFACES, DETAILS, and inline prose. For LINUX KERNEL section entries using the `'\<...\>'` format, the keyword goes inside the angle brackets: `'\<struct acpi_gpe_register_info\>'`, `'\<enum ec_command\>'`.
- Do not reference internal pages. Do not add cross-links to other pages in the knowledge base (e.g., `[Page Title](other-page.md)`). Each page must be self-contained.
- When citing kernel source code in Markdown code blocks, preserve the exact indentation style from the kernel source. The kernel uses tabs (8-space width) for indentation. Do not convert tabs to spaces. This includes function bodies, switch/case statements, and multi-line expressions.
- Use markdown link format `[Title](URL)` for all entries in the OTHER SOURCES section. Do not use bare URLs or `Title — URL` style.
- The DETAILS section must include detailed kernel code walkthroughs: step-by-step traces through function call chains, real driver API usage examples, and lifecycle coverage for key objects. For every function/struct/enum in the LINUX KERNEL section, find at least one concrete driver usage and show it in DETAILS. When elaborating on kernel code paths, always cite the actual implementation as fenced Markdown code blocks (` ```c `) rather than only describing it in prose. Show the relevant code, then explain it.

### 7m. Link anchoring and exhaustive span linking (mandatory)

#### Constructing Elixir cross referencer URLs

Use the base URL `https://elixir.bootlin.com/linux/<version>/source/`, where `<version>` is the documented kernel version from SKILL.md's Input section (for campaigns, the version pinned in the plan file's Context). One page never mixes versions. The examples below use `v7.0`:

For file references:
```
[`path/to/file.c`](https://elixir.bootlin.com/linux/v7.0/source/path/to/file.c)
```

For function references (include line number). The `\<...\>` word-boundary markers make these references compatible with `git log -L`:
```
[`'\<function_name\>':'path/to/file.c'`](https://elixir.bootlin.com/linux/v7.0/source/path/to/file.c#L1234)
```

For kernel documentation files:
```
[`Documentation/subsystem/file.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/subsystem/file.rst): brief description
```

Which line a link anchors at, and which symbol occurrences must be linked, is governed by the anchoring rules below (definition-line anchoring, file-location links for call sites, and the exhaustive span-linking pass).

#### Anchoring and exhaustiveness

This rule extends the every-symbol-linked rule in 7f with anchor selection and exhaustiveness. It is what the numbers in `guidelines/reference/measured-criteria.md` ("Samples and measured criteria") call links per page.

- A link whose text is a symbol name (`` `vma_start_read()` ``, `` `struct mm_struct` ``, `` `VM_LOCKED` ``, and the LINUX KERNEL `` `'\<sym\>':'path'` `` form) anchors at the symbol's DEFINITION line, so the reference stays valid for `git log -L` and survives unrelated churn elsewhere in the file. It does not anchor at a call site, a comment mention, or a line inside some other function's body, even when that line is what the surrounding prose discusses.
- A reference to a specific non-definition place in code (a call site, one branch, one field assignment) is written as a file-location link whose text is the path and line, for example [`mm/vma.c:717`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L717). Prose that enumerates call sites uses one location link per site, so every count in the page is checkable one click deep.
- Every occurrence of every kernel symbol outside fenced blocks is linked, including repeats of the same symbol on the same page. The exhaustive pass includes the classes that are easiest to skip: `CONFIG_*` options link to the `config X` line of the Kconfig file that declares them; generic primitives (`READ_ONCE()`, `memcpy()`, `rcu_read_lock()`, `atomic_read()`, and the like) link to the definition relevant to the documented architecture; a field path written as `a->b` or `foo.bar` links to the field's declaration line inside the struct definition; an ops-struct member named in prose ("the `fault` hook") links to that member's line in the ops struct definition.
- Settled exemptions (spans that may stay bare): C keywords and operators; local variables, parameters, and goto labels quoted from an excerpt; literal and error values (`-EINVAL`, `NULL` as a value); `/proc`, `/sys`, and sysctl path strings; Kconfig syntax fragments (`=y`); tracepoint field names; a wildcard family name (`VM_*`) when the members it stands for are linked nearby; commit hashes; the `name(2)` man-page notation when the page links the syscall's kernel entry point elsewhere; and symbols verified absent from the documented tree (state the absence in prose).
- Precedent never overrides the rule. "Other pages leave `CONFIG_FOO` bare" or "this page already has thirty bare `READ_ONCE()` spans" is not a reason to leave the next one bare; the rule wins, and the pre-existing in-family spans get fixed in the same pass.

### 7q. Rephrase recipes (quick reference)

Every ban has a one-line recipe; apply the recipe instead of re-deriving compliant phrasing per hit. The full rules with worked examples are 7 through 7d (`guidelines/rules/INDEX.md` maps each ID to its file); this table is the lookup.

| banned | recipe |
|---|---|
| em-dash | parentheses, or two sentences |
| label-colon prose ("X: Y", "The fix: Y") | one plain declarative sentence; introduce quotes with "According to the comment ..." |
| intro sentence + explanatory list | fold the items into one flowing sentence |
| hedge (usually, typically, often, in practice, ...) | name the exact condition the code tests |
| hollow superlative, "X matters", "the key ..." | name the mechanic in the same clause and drop the ranking |
| "contract" | state the precondition, guarantee, or invariant it stands for |
| "tally" | "count" |
| "canonical X" | "the X that performs it", named plainly |
| "arm"/"arms" for a branch or union case | "branch", "case", "side", "leg", or the symbol name |
| "X, not Y" | state X plainly; drop the contrast |
| lives / sits / wants for code placement | "is defined in", "is held in", "is stored in" |
| "walk" for a scalar changing value | "transitions through", "advances through" |
| Why/How/Where or question headings | declarative subject-verb-object heading |
| "vtable" | "function pointer struct" or the concrete type name |
| bare kernel-symbol span | Elixir link anchored at the definition line (7m) |

## Facts, code, and coverage

What a page must prove and how it must prove it: excerpts, provenance, enumeration, claim verification. These are the classes the writer owns end to end and the exit suite checks.

### 7e. Self-contained kernel-source citation (mandatory)

Every page must read as a self-contained source. A reader who never opens the kernel tree must still finish the page knowing exactly what the relevant code does. Whenever the page explains how a function works, what a struct looks like, how a macro is used, or how a call site invokes a callee, the actual code goes inline as a fenced ` ```c ` block before or alongside the explanation. Linking to Elixir is not a substitute for showing the code; the link is for navigation, the code block is for comprehension.

Concrete requirements:

- Never fabricate, paraphrase, or approximate kernel source. Every fenced ` ```c ` block must be the real code, located and verified with the semcode tools (`find_function`, `find_type`, `grep_functions`) and by reading the on-disk source file, then reproduced verbatim (exact text, all comments, and tab indentation). Confirm the symbol exists at the documented version and that the reproduced lines match the file before citing them; if you cannot locate the real code for a symbol, do not show a code block for it. Where a semcode index is stale or disagrees with the working tree, the on-disk source at the documented version is the ground truth.
- For every function listed in LINUX KERNEL, the DETAILS section must contain at least one fenced ` ```c ` block showing either its full body (when it is small) or the body of the case label / branch / inner block that the page is actually describing. Do not describe a function's behavior in prose alone when the body would fit in a screen of code.
- For every struct or enum listed in LINUX KERNEL, the DETAILS section must contain a fenced ` ```c ` block reproducing the type definition (including comments and `#ifdef` regions). The reader must see the exact field list and any decorative comments without leaving the page.
- For every macro or static array (e.g. `fallbacks[][]`, `__used` lookup tables) referenced in body prose, reproduce the definition as a fenced block at the point where the prose first depends on it.
- When walking a call chain, show the caller's invocation site as a code block as well as (separately) the callee's body. The reader has to see both ends of the call, not just one.
- When explaining a switch statement, conditional, or loop whose structure is the point of the explanation, the code block must reproduce that structure verbatim. Paraphrasing the control flow in prose is forbidden when the actual code would convey it more directly.
- When citing a kernel comment, quote the comment text inside the same fenced code block that contains the surrounding code, and refer to it via "According to the comment <quote>, ..." in the prose.
- When citing a commit message that contains a benchmark table, ASCII figure, or other formatted text, reproduce it inside a fenced code block (use ` ``` ` without a language hint) so the formatting survives.

Each fenced code block stays as close to the kernel source as practical: tab indentation preserved, all original comments retained, no truncation other than `...` to elide irrelevant intermediate code (and only when the elided code would not change the reader's understanding). When a function body is too long to reproduce in full, split it across multiple code blocks at natural boundaries (one per case label, one per loop, one per error-handling tail) rather than truncating, and explain each block in the prose between them.

The test for whether enough code has been cited: assume the reader has the page open in one window with no other terminals, no other browser tabs, and no kernel tree. Could they still describe in their own words exactly which lines run on the path the page is documenting? If not, more code blocks are needed. Adding a sentence "see [`func()`](https://elixir...)" does not count as showing the code; the link is for the reader who wants to verify or explore further, not for understanding the page.

The DETAILS section is the canonical place for this. SUMMARY may include short snippets when a single line of code is the cleanest way to convey the topic, but bulk code citation belongs in DETAILS, interleaved with the prose that walks through it.

### 7j. Behavior and construct coverage (mandatory)

A page documents a mechanism in full, not only the single function path that prompted it. Breadth of coverage (every site that exhibits a behavior, every struct and helper that backs it, the full object lifecycle) is as mandatory as the prose and citation rules (7 through 7f, `guidelines/rules/`).

- Cite every site that matches a behavior, not one. For each behavior the page describes, find all the places in the kernel source that implement or exhibit it, and cite each one with its file path and line number, as an inline Elixir cross referencer link at the mention and as a fenced ` ```c ` block in the DETAILS section reproducing the relevant lines. When a behavior recurs across many call sites or drivers, cite as many as is practical rather than stopping at the first match. Enumerate the full set with `find_callers`, `grep_functions`, and Grep before writing. If the set is too large to cite exhaustively, cite a representative spread (the core implementation plus several users) and state how many sites exist, rather than silently narrowing to one.
- Cover the data structures and their helpers, not only entry-point functions. Identify the kernel's internal data structures for the topic (the structs, enums, and typedefs that hold the state) together with the helper functions and accessor macros that allocate, initialize, read, modify, and destroy them. List them in the LINUX KERNEL section, reproduce their definitions as fenced ` ```c ` blocks in the DETAILS section, and show the accessors in use there. A page that names a behavior but omits the struct that records the state, or the helper that changes it, is incomplete.
- Draw the structure, do not only describe it. A mechanism with spatial, temporal, or transformational structure (a data or bit layout, an object topology, an operation that reshapes a structure, a state machine, a sequence of steps across actors) is usually clearer as a figure than as prose, and identifying those figures is part of covering the mechanism, not a later styling choice. Draw them per the diagram rules (7g-7i, `guidelines/rules/diagrams.md`), using as many figures as the material earns rather than a default of one. A page that walks an operation reshaping a data structure (a split, merge, insertion, teardown, or fork) without showing that structure before and after has a coverage gap, not a stylistic economy. The restraint in 7g still decides which candidates are real: no figure for a plain call chain, a two-state toggle, or anything a single declarative sentence conveys.
- Cover the object lifecycle and asynchronous behavior, not only static call sites. For each key object, document its life cycle: allocation, initialization, freeing, the locks that serialize access to it, and its reference counting (`kref` / `refcount_t` get and put, and the put that drops the last reference and frees it). Document the dynamic behavior as well: state transitions (which field advances through which states, and what drives each transition), notification mechanisms (notifier chains, `struct completion`, wait queues, eventfd, uevents), and deferred or asynchronous work (`work_struct` and `delayed_work` on a workqueue, tasklets, timers, threaded IRQs, RCU callbacks), along with the ordering and concurrency rules between them. Tracing only "function A calls function B" misses the lifecycle and asynchronous behavior the page exists to explain.
- Call out hard-coded limit values explicitly. Search the code for the constants that bound the mechanism: timeouts, retry and attempt counts, maximum allowable error counts, buffer and queue sizes, poll and backoff intervals, and similar thresholds, whether defined as a macro, an enum value, or a bare literal. Find as many as exist rather than stopping at the first; name each one in the page with its value and the macro or literal that holds it, cite its file and line, and reproduce the defining line in a fenced ` ```c ` block where the value governs a code path the page walks. A page that describes a timeout, a retry loop, or an error threshold without stating the actual number is incomplete.
- The catalog and the scope statement define done-ness. A page is complete when every symbol in its LINUX KERNEL catalog and every behavior in its scope statement is covered to the rules above; "the core API is documented" is not a completion test, and importance ranking never shrinks coverage. When the material outgrows one page, split it along a boundary statement into finer sibling pages; never thin any page's coverage to shorten it.
- Compression may remove words, never coverage. Shortening or rewriting a page must not remove cataloged symbols, documented behaviors, call-site enumerations, figures that carry layout facts, or KERNEL DOCUMENTATION / OTHER SOURCES entries. Removing any of those is a scope change made deliberately: the catalog and the scope statement shrink in the same edit, and the cut is reported. Rule 7p governs the procedure when the shortening happens while deriving from existing material.
- Order DETAILS from generic to specific. Within DETAILS, present the subsystem-generic mechanism first (the core data structures, the shared code path, the framework behavior), then the vendor-, channel-, or driver-specific instances built on top of it. The reader should understand the general mechanism before reading how a particular driver specializes it.

### 7k. Driver examples (mandatory)

When a page illustrates a behavior with a concrete driver, both the choice of driver and the way the page keeps that example self-contained matter.

- Cite only actively-maintained drivers. When choosing a driver as a usage example, pick one with major activity in the three years leading up to the documented version's release (for a v7.0 tree, roughly 2023 onward). Confirm this before citing: run `git log` on the driver's file, or semcode `find_commit` with `path_patterns` for the driver's path, and check for substantive commits within the last three years (ignore treewide renames, whitespace, and other mechanical churn). Do not illustrate current behavior with a driver whose only recent commits are trivial or whose last real change is years old; a dormant driver may use deprecated patterns that misrepresent how the mechanism is used today. If no recently-active driver exercises the behavior, say so rather than reaching for a stale one.
- Describe a driver example from its own kernel source, and keep the explanation on this page. Give the driver's role (vendor, bus, device class) and cite its file and the relevant function or callback inline, so the reader needs nothing beyond this page to understand it. Do not point the reader to another driver or another page as a substitute for the explanation, and do not explain the driver by analogy to one documented elsewhere; everything the reader needs is stated here, from this driver's own code.
  - BAD: "The cs35l56 driver registers a jack-detect callback, just like the codec documented elsewhere in this knowledge base."
  - GOOD: "The cs35l56 driver (a Cirrus Logic amplifier in `sound/soc/codecs/cs35l56.c`) registers a jack-detect callback through its `set_jack` component op."

### 7l. Code-block provenance comments (mandatory)

Every fenced ` ```c ` block opens with a provenance comment naming the on-disk origin of the excerpt, in the exact form `/* path/from/tree/root.c:LINE */` on its own first line, where LINE is the number of the first reproduced line in the file at the documented version. A short annotation may follow the line number inside the comment (`/* mm/vma.c:497 (in __split_vma()) */`). A block that stitches excerpts from several places (a caller plus its callee, two case labels far apart, a struct field plus the helper that writes it) marks each excerpt's start with its own interior `/* path:line */` delimiter line, and marks elided code inside an excerpt with a standalone `...` line. Everything between delimiters is verbatim file content per 7e (tabs preserved, comments retained, no reflowed lines).

The provenance comment is what makes a page checkable. A reviewer opens the named file at the cited line and compares the unit directly (see the 3c check procedures in this file), so a missing or wrong provenance line turns an on-disk match into a finding, and a silently drifted excerpt is caught on the first comparison. Non-code fenced blocks (ASCII figures, quoted commit-message tables, shell output) carry no provenance comment and are not diffed.

### 7n. OTHER SOURCES provenance (mandatory)

Every OTHER SOURCES entry is a mailing-list URL taken byte-exactly from a `Link:` trailer in `git log` output for a commit the page discusses (both `https://lore.kernel.org/...` and `https://lkml.kernel.org/r/<message-id>` trailer forms qualify), or a lore.kernel.org URL returned by the semcode `dig` tool for that commit. Never construct, guess, or "normalize" a URL: no hand-built `git.kernel.org/.../commit/?id=` links, no reconstructed lore paths, no search-result URLs. Format each entry as `[<commit subject> (commit <abbreviated sha>)](<trailer URL>)`. A relevant commit that has no `Link:` trailer is cited in prose by sha and subject and gets no OTHER SOURCES entry.

### 7o. Behavioral-claim verification (mandatory)

A page is a set of claims about kernel behavior, and each claim class below has a named audit action. The style and linking rules make a page readable and navigable; these actions are what make it true. Perform them while writing, and re-perform them whenever reviewing, enhancing, or reusing a page, because they catch the class of error that reads correctly, links correctly, and survives every mechanical check.

- Universal quantifiers are enumerations. Every sentence containing "only", "never", "always", "all", "every", "exactly N", "the single", or "once" asserts the size or uniformity of a set. Enumerate that set before writing the sentence (semcode `find_callers` plus a tree-wide grep that includes headers), then either cite every member with location links or weaken the sentence to what the enumeration shows. A page in this knowledge base asserted a helper "is invoked from exactly one place" while the tree held four callers (the plain store helper, its gfp variant, the fork-path bulk store, and an error-path rollback); only re-running the enumeration catches this class.
- A per-member claim is as many claims as the family has members. A sentence of the form "each X ..." or "every X ..." that asserts a property or a one-to-one relationship over a family ("each wrapper forwards to exactly one underlying primitive", "every callback runs under the lock", "each descriptor slot maps to one register") is verified by building the member-to-property mapping first: list every member of the family and, for each member, everything the property names for it. One exception falsifies the sentence. When an exception exists, restate the sentence to what the mapping shows, restrict the family explicitly ("every read-side helper ..."), or name the classifier that makes the claim true and say what falls outside it ("one primary primitive, plus cursor-bookkeeping helpers"); an unstated classifier is how a strictly-false claim reads as true and survives review. A lead sentence in this knowledge base asserted that each wrapper helper "forwards to exactly one" underlying primitive while the page's own per-helper table showed one wrapper calling a range-setup helper plus the store primitive; the mapping audit catches this, and the heading failure under "Headings are claims" below is the same shape applied to a section.
- Lead and SUMMARY compression gets no precision waiver. Quantified, universal, and per-member claims in the lead paragraph and in SUMMARY are audited exactly like DETAILS claims, and each must agree with the DETAILS evidence that carries it (the section, table, or enumeration on the same page). Cross-check every lead and SUMMARY quantifier against the page's own tables and enumerations at sign-off; a summary that contradicts the page's own table is the first inconsistency a reader finds. Compression may drop detail; it may never trade accuracy for sweep.
- Every enumeration states its search basis inline. Give the scope with the number (directories searched, headers included or not, definition sites excluded, the architecture and CONFIG filter): "a grep across mm/, fs/, kernel/, drivers/, arch/x86/, and include/ at this tree finds 118 call sites of ... outside their definitions". A count whose basis is unstated cannot be re-verified and does not qualify. When a count holds only under the page's CONFIG assumptions (a caller compiled out without `CONFIG_MMU`), say so at the claim, not only in the page preamble.
- Counts are re-derived at review, never trusted. Whoever reviews, lints, or enhances the page re-runs every enumeration and corrects drift; a re-count on a live page corrected a written 119 to the 118 actually on disk.
- A restated condition is derived, not paraphrased. When prose restates a guard or threshold in words ("requires map_count + 2 < sysctl_max_map_count - 3"), derive the restatement from the reproduced code by exact negation of its operator, keep the exact constants, and show the guard as a code block beside the sentence so a reader can repeat the derivation.
- Headings are claims. A DETAILS heading must be true of everything in its section, and a heading edit is a claim edit. One polish pass strengthened "the accessors mediate every flag change" into "the accessors take the write lock before every flag change" directly above an excerpt whose own kernel comment reads "needs no locking"; the stronger heading was false. Verify each heading against the section's excerpts after writing it and after every rewording.
- Prose does not outrun its excerpt. Read each behavioral sentence against the adjacent code line by line. Semantics carried by the primitive's own name are behavior and are stated, not dropped: an ordering suffix (`refcount_set_release()` orders the preceding field writes before the count becomes visible to an acquiring reader), a `_locked`/`_unlocked` variant, an RCU flavor, saturation semantics.
- Invariant claims get a counterexample search. Before asserting a lifecycle invariant ("set once and never changes", "always called under lock L", "freed only through F"), search for the counterexample explicitly: every assignment site of the field, every caller that lacks the lock, every free path. Cite the kernel's own enforcement when it exists (a `lockdep_assert_held()`, a `VM_WARN_ON()`, a `const` qualifier), because an assertion line is stronger evidence than a grep that found nothing.
- Provenance line numbers are claims too (7l). Content matching does not validate them; open the file and confirm the excerpt begins at the cited line.
- The one licensed exception to "prose does not outrun its excerpt" is the disclosed domain-model synthesis of 7s: a model assembled from named on-disk materials (the code, enumerating comments, `Documentation/`, and the introducing commits), with every fact under it still individually cited. It never licenses an undisclosed, unsourced, or guessed assertion, and 7c and 7d bind it in full.

### 7p. Deriving from an existing page (mandatory)

These rules govern producing a page from existing material of any provenance, in any subsystem: an earlier-generation draft, a prior revision of the same page, or pages being compressed, merged, or split.

1. Inventory the source first. List the source's LINUX KERNEL catalog entries, its DETAILS sections, the distinct behaviors and call-site enumerations it documents, its figures, and its KERNEL DOCUMENTATION and OTHER SOURCES entries.
2. Give every inventory item an explicit disposition: kept (and where it now lands), merged (into which section), or cut (with the reason). No item disappears without a disposition; a coverage loss that happens as a side effect of rewriting is the failure mode this rule exists to prevent.
3. A cut is a scope decision, not an edit. It removes the item from the LINUX KERNEL catalog and from the scope statement in the same change, and it is reported in the final message (and recorded in the campaign plan file) so the orchestrator or the user can veto it. A symbol that stays in the catalog cannot have its DETAILS coverage cut.
4. The derived page passes the same Gate B parity audit (item 1; Gate B (3b) in this file) as a fresh page. Coverage in the source is not coverage in the derived page; "the source covered it" fails the audit.

A measured failure of exactly this kind motivates the rule: a 2,645-line page compressed to 1,268 lines kept its iterator-helper symbols in the LINUX KERNEL catalog while silently dropping their DETAILS sections, kept one catalog symbol with no DETAILS mention at all, and landed at 0.73 fenced blocks per catalog entry where every conforming page measures at least 1.0. The parity audit catches the desync mechanically; the disposition list is what makes any removal legitimate.

### 7s. Domain-model layer (mandatory)

A page teaches the subsystem's model of its topic, not only an annotated catalog of the symbols that implement it. The model is the abstraction the code realizes: the states an object moves through and the transitions between them, the phases of a process, the taxonomy its parts fall into, and the rules that govern these. State the model as a model, in the lead and SUMMARY and ahead of the DETAILS walkthroughs, so a reader understands what the thing is before reading how each symbol serves it, and let it organize the body rather than sit as a preamble to a per-symbol catalog (7u). A page that opens straight into per-symbol definitions leaves the reader to reverse-engineer the model the page exists to convey, which is the difference between a reference catalog and an explanation.

The model's source decides how it is written.

- When a normative specification fixes it (an ACPI, PCIe, USB, or hardware-manual definition of a register layout, a state set, or a protocol), cite the spec in SPECIFICATIONS, present the model as the spec defines it, and map the kernel's constructs onto it (the spec-semantics-paired-with-kernel-slots form), so the reader learns a state's specified meaning and the constant that carries it together.
- When no specification defines it, which is the common case for a pure-software subsystem, the model is a synthesis the writer assembles from the kernel's own materials: the code, the enumerating comments and struct doc-comments, the relevant `Documentation/` pages, and the commit messages of the series that introduced the mechanism. This is the one place a page states more than a single excerpt witnesses, and it is licensed only under disclosure. Name the materials the model is drawn from ("Assembled from the type comment, `Documentation/mm/process_addrs.rst`, and the series that introduced the per-VMA lock, the model is ..."), keep every fact under the model separately cited per 7e and 7m, and weaken or scope any part the materials do not support per 7o rather than asserting it. 7c and 7d bind in full, so the model is stated in plain declaratives that name mechanics, never in hollow superlatives, importance-framing, or label-colon idioms. The frozen mm samples (`guidelines/reference/samples/`) show this synthesis stated up front.

A model the tree's own materials do not support is never invented to fill the section. If it cannot be grounded in named on-disk sources, state what those sources establish and stop; a guessed model ("the design is presumably ...") is worse than none.

### 7t. Semantics tables for state sets and taxonomies (mandatory)

When a topic carries a fixed set of states or modes, or a classification its parts fall into (a device power-state set, a page-fault-type set, a flag taxonomy, an error-code family, the callback set of an ops struct), present it as a table rather than a bare list of constants. One row per member, with a meaning column stating what the member is in the model (7s) and a construct column linking the defining code (7m). The encoding and lifecycle archetypes among the frozen samples (`guidelines/reference/samples/`) show this member-meaning-construct shape for bitfields and for object states.

A state set additionally documents its legal transitions: which member advances to which, and what drives each edge, as a transition table or, where the transitions carry spatial or temporal structure, an ASCII state figure under 7g through 7i. A taxonomy documents its classifying axis: state what distinguishes each class from its siblings, not only that the classes exist.

### 7u. Journey- or model-first organization (mandatory)

A page is organized as a journey or around a model, never as a catalog of its symbols. The LINUX KERNEL section is the reference catalog, where a list is correct; DETAILS is not a catalog. Its sections are the chapters of a journey (the phases of a process traced from start to end) or the facets of a model (the roles, states, or classes the mechanism has), and each cataloged symbol appears inside the chapter or facet where it does its work, shown there with its definition and usage excerpts, rather than getting its own section walked in catalog or declaration order.

Choose the spine from the topic. An operation or a pipeline (a syscall path, a page fault, a split or a merge, a device probe, a translation from an on-disk or on-wire form into a kernel structure) is a JOURNEY: organize DETAILS by its phases in the order they run. A static object or a state space (a struct, a flag set, a lock's states, a power-state set) is a MODEL: organize DETAILS by its roles, states, or classes. A page that is an object with an operation on it leads with the model and then traces the operation as a journey through it.

The catalog-first anti-pattern is the failure this rule names, and the test for it is the DETAILS headings. Headings that are one-per-symbol, named for each function or field and walked in the order the catalog lists them, are catalog-first and are reorganized. Headings that name the phases of a process ("the boot table is parsed before the namespace exists", "the handler is wired to the address space") or the facets of a model ("the range and identity fields", "the per-VMA lock state"), with the symbols shown inside, are journey- or model-first.

This never weakens coverage. Every cataloged symbol still appears in DETAILS with its definition and usage excerpts (3b item 1); journey- or model-first organization changes WHERE a symbol is shown (inside the phase or facet where it acts), not WHETHER it is shown. A cataloged symbol that fits no phase or facet is a signal that the organization is wrong or that the symbol does not belong in the catalog, never license to append a stray per-symbol section.

Diagrams obey the same rule (7g). A figure depicts the page's journey (a pipeline, a sequence, a before-and-after transformation, a lifecycle) or its model (a state machine, an object topology, a taxonomy), so the figure is the visual form of the same spine the prose traces; where the journey or the model is large enough to carry the page, one figure shows it whole as the reader's map. A figure that is only an inventory of symbols in boxes, with no process or relationship among them, is a catalog in visual form and is redrawn to show the relationship or dropped.

This rule and 7s are a pair: 7s puts the model at the top of the page, 7u organizes the body around it. Together they retire the catalog-first page, whose lead announces a member-by-member tour and whose DETAILS delivers one.

## The gates

What a finished page is measured against. Gate A is mechanical, Gate B is the review sign-off, and 3c holds the by-hand procedures both of them use.

### 3a. Gate A (mechanical, grep the finished page)

Confirm zero hits for each, and re-run after every edit including your own hand-edits: em-dashes; `**` boldface in prose; the label-colon-explanation idiom in prose (7a/7c), excluding the caution blockquote and text inside quotes; the 7c/7d editorializing and superlative phrases (`the reasoning`, `is the key`, `X matters`, `X is what makes Y`, `the pattern is`, `worthwhile`, `crucial`, `elegant`, `cornerstone`, `the most <adj>`, and the like); the banned words `contract`, `tally` (also `tallied`/`tallies`/`tallying`), `canonical`; vague hedges (`usually`, `typically`, `generally`, `normally`, `commonly`, `mostly`, `in practice`, `tends to`); `vtable`; the word `arm`/`arms` for a branch or union case (7c; CPU-architecture names and verbatim quotes exempt); internal `.md` cross-links; and `Why`/`How`/`Where` or trailing-`?` headings. The grep list above is the gate. Run it by hand, fence-aware, using the candidate greps in the 3c check procedures below, and judge every hit against the exemptions and the 7r registry before editing; never reword an exempt construct to silence a pattern. **Match case-insensitively when sweeping, then use case as evidence when judging.** The phrases above are written lowercase, and a case-sensitive sweep silently misses every sentence-initial occurrence — a writer hit exactly this, its "What matters here is that…" surviving the cleft pattern because `what matters` was matched literally, and it surfaced only under an unrelated superlative grep. Case still carries meaning at the judging step, which is where it belongs: the arm-word ban exempts the capitalized CPU-architecture names (`Arm`, `ARM64`) per 7r, so a case-insensitive sweep is expected to surface those and the adjudication is expected to clear them. Sweep wide, judge narrow; a pattern that cannot see a candidate cannot be adjudicated at all. The same reasoning applies to word boundaries: `\b` treats `_` as a word character, so a banned token inside an identifier (`TRB_NEC_GET_FW`) is invisible to `\bnec\b` — sweep such tokens with letters as the only delimiter. Boldface and the 7b prose-list shapes are read-through checks.

A page is final only at zero unadjudicated findings. The gate is a manual procedure; the 3c check procedures in this file carry the candidate greps and the no-checker-script doctrine.

### 3b. Gate B (review sign-off, the rules a grep cannot catch)

Verify each item by performing the named action and recording the evidence (a count or a list, not "looks fine"). A page is not done until every item is confirmed; reading the page is not sufficient.

Ownership and timing: the writer owns this gate's factual items by construction and by its mechanical exit suite (`guidelines/passes/02-write.md`), and it also runs Gate A (3a/3c) on its own prose — an earlier split that forbade this was withdrawn, because the sweeps are procedure rather than perception and survive self-application (the reasoning is in `guidelines/passes/03-check.md`). The orchestrator then re-runs every mechanical check independently and compares the answers; it adjudicates every residual and never delegates that. A verify campaign re-runs the whole gate later, on a newer tree or under a different model.

1. Catalog-to-DETAILS parity (7e/7j). Build a parity table with one row per LINUX KERNEL catalog symbol and two evidence columns: where DETAILS reproduces its definition (or the exact case label / branch the page describes) as a fenced ` ```c ` block, and where DETAILS shows a concrete caller or usage as code. Every cell must hold a location in the page; an empty cell is a gap, and a catalog symbol that appears nowhere in DETAILS is a hard failure. Check the reverse direction too: a symbol that carries its own DETAILS section belongs in the catalog. When the page names several distinct users or call paths for one symbol, each named one appears as an excerpt or a per-site location link (7m) and the shown-versus-enumerated split is stated. Tripwire before building the table: fewer fenced ` ```c ` blocks than catalog entries means unpaired symbols (every conforming page measured runs 1.03 to 1.47 blocks per entry; a deficient derived page measured 0.73). Record the table; a bare count does not qualify. Sign off only at zero empty cells.
2. Grounded, non-fabricated code (7e/7l). For every fenced ` ```c ` block, open the on-disk source at its cited `path:line` and confirm the block matches verbatim (tab indentation and comments preserved, `...` only for disclosed elisions). Cross-check with the semcode tools, but the on-disk source at the documented version is ground truth. Print the file's lines at the cited range (`sed -n 'START,ENDp'`) beside each block and compare directly, unit by unit for stitched blocks; the excerpt must begin at the cited line, and content matching elsewhere in the file with a wrong claimed line is a finding. Record the count of code blocks and that every one was confirmed against the file. Sign off only when none is left unverified.
3. Every symbol linked, keyword kept (7f). Scan every inline `` `code` `` span outside fenced blocks. Confirm each kernel symbol is an Elixir link to the correct `path#Lline`, and that types keep the `struct`/`enum` keyword. Spot-read the cited lines on disk. Record any bare span or wrong line found and fixed. Sign off at zero.
4. What-does-what DETAILS headings, journey- or model-first (7/7u). Read every H3 and H4 under `## DETAILS`. Confirm each is a declarative subject-verb-object sentence, not a bare noun or symbol name, and that the headings together trace a journey (the phases of a process) or lay out a model (the roles, states, or classes of the mechanism), not a per-symbol catalog walked in declaration order (7u). A DETAILS section that is one heading per cataloged symbol in catalog order is the catalog-first failure and is reorganized, every symbol re-homed inside the phase or facet where it acts (coverage is preserved, per item 1). Sign off with the heading count and the spine (journey or model) the headings form.
5. No negative constructions or anthropomorphic verbs (7). Read the prose. Confirm no `It is X, not Y` constructions, no `lives`/`sits`/`wants` for code, and `walk` used only for traversing a data structure. Grep `[^a-z]not `, ` lives`, ` sits `, ` wants ` for candidates, then judge each in context. Sign off after reading, not after grepping alone.
6. Full coverage and domain model (7j/7s/7t). For each behavior the page documents, enumerate every site that exhibits it with `find_callers`/`grep` and confirm the page cites all of them, or cites a representative spread and states how many exist. Confirm every hard-coded limit or constant is named with its value, and that the object lifecycle (allocation, initialization, freeing, the serializing locks, reference counting) and the asynchronous behavior are covered. Confirm the page states the domain model of its topic ahead of the DETAILS walkthroughs (7s), either spec-defined and mapped onto the kernel constructs, or a disclosed synthesis that names its on-disk sources and keeps every sub-claim cited, and that every fixed state set, mode set, or part taxonomy appears as a member-meaning-construct semantics table (7t) with a state set's legal transitions shown. Record the enumeration and the model's sources. Sign off.
7. Driver examples actively maintained (7k). For each driver cited as an example, run `git log` on its file and confirm substantive commits within roughly three years, and that its role is explained from its own source on this page. Record the newest substantive commit per driver. Sign off.
8. ASCII diagrams (7g-7i). For each figure, confirm Unicode box-drawing only with no ASCII `\`, `|`, or `/` used as a connector, every line under 80 columns, each content-row `│` landing on a `┬` or `┴` junction of the borders above and below, and that the figure shows a spatial or temporal relationship rather than a function-call chain. Sign off per figure.
9. Behavioral-claim audit (7o). List every universal quantifier ("only", "never", "always", "all", "every", "exactly N"), every count, every per-member "each/every X" claim, every restated guard or threshold, and every lifecycle invariant in the page. For each, re-run the enumeration or derivation (record the search performed and its result) and correct the sentence to match; for per-member claims, rebuild the member-to-property mapping and confirm every member, or confirm the stated classifier and its boundary. Confirm every DETAILS heading is true of everything in its section, every behavioral sentence agrees with its adjacent excerpt, and every lead and SUMMARY quantifier agrees with the DETAILS section, table, or enumeration that carries its evidence. Sign off with the claim list and its evidence.

A page is final only at zero unadjudicated findings.

### 3c. Mechanical checks (by hand)

The mechanical layer of the gates is executed with an editor and standard shell tools. There is no checker script to run, maintain, or trust; a script's regexes age into false positives and its passes into false confidence, so the checks below are the procedure itself. Work page by page.

1. Link targets. List every cited location, then open each one and confirm what the link claims:

```
grep -oE 'source/[^)#[:space:]]+#L[0-9]+' page.md | sed 's|source/||; s|#L| |' | sort -u |
while read f l; do echo "== $f:$l"; sed -n "${l}p" "/path/to/tree/$f"; done
```

Judge each printed line: a symbol-name link must land on the symbol's definition line itself (7m), and a file:line location link must land on the exact site the prose describes. When link and code disagree, fix the anchor by re-finding the symbol on disk.

2. Excerpt verbatimness. For every fenced ` ```c ` block, open the provenance file at the cited line and compare unit by unit (an interior `/* path:line */` delimiter starts a new unit; a standalone `...` line marks a declared elision):

```
sed -n 'START,ENDp' path/from/provenance.c
```

Each unit must begin at its cited line and match byte for byte, tabs included. Content that matches elsewhere in the file with a wrong claimed line number is a finding (7l, 7o).

3. Gate A candidates. The patterns below GENERATE CANDIDATES; they are not the gate. Judge EVERY hit against the rule's exemptions and the settled adjudications registry (7r) before touching the page. A hit on an exempt construct is a false candidate, and rewording a compliant phrase to silence a pattern is itself an error: a writer once reworded a correct "32-bit Arm" purely to quiet an arm-word pattern, and that rewording was the only defect introduced. Fix confirmed hits with the 7q recipes.

**Build the prose view first.** Every pattern below runs against a prose view of the page, never the raw file. This step is not optional bookkeeping — it is what makes the candidates trustworthy, and skipping it is what let the label-colon class ship for eight consecutive pages. The view strips exactly what 7r already exempts, and it judges nothing:

```
python3 - page.md <<'EOF'
import re, sys
CAT = ("## LINUX KERNEL", "## KERNEL DOCUMENTATION", "## OTHER SOURCES", "## SPECIFICATIONS")
fence = cat = False
for n, l in enumerate(open(sys.argv[1], encoding="utf-8"), 1):
    l = l.rstrip("\n")
    if l.startswith("```"): fence = not fence; continue    # fenced blocks exempt (7f)
    if fence: continue
    if l.startswith("## "): cat = l.strip() in CAT; continue
    if l.startswith("#"):                                  # headings are GOVERNED (7, 7d, 7o):
        print(f"{n}:[H] {l.lstrip('#').strip()}"); continue #   emit them, do not drop them
    if l.startswith(">"): continue                          # caution blockquote
    tag = ""                                               # [C] = label-colon exempt (7r) ONLY;
    if cat or l.startswith("|") or l.lstrip().startswith(("- ", "* ")):
        tag = "[C] "                                       #   every OTHER ban still binds here
    l = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", l)         # [text](url) -> text; kills URL colons
    l = re.sub(r"`[^`]*`", "\u00a7", l)                      # inline code -> placeholder
    l = re.sub(r'"[^"]*"', "\u00a7", l)                      # double-quoted verbatim (7r)
    l = re.sub(r"\b[\w/.-]+\.(c|h|rst|S):\d+", "\u00a7", l)  # file:line citations
    l = re.sub(r"::|\d+:\d+", "\u00a7", l)                   # scope form, ratios
    print(f"{n}:{l}")
EOF
```

This is a view builder, not a checker: it never reports pass or fail, and every candidate it surfaces is still adjudicated by hand. Run the patterns against its output.

**Rows tagged `[C]` are catalog bullets, list items, and table cells. 7r exempts the LABEL-COLON shape there and nothing else** — so skip label-colon candidates on `[C]` rows and adjudicate every other pattern on them exactly as you would on flowing prose. The em-dash, hedge, cleft, superlative, banned-word, anthropomorphic-verb and negative-construction bans all bind those regions. An earlier version of this view dropped the four catalog sections outright with a blanket `if cat: continue` justified as "catalog bullets exempt (7r)", which over-applied a shape-specific exemption to every rule at once and left SPECIFICATIONS, LINUX KERNEL, KERNEL DOCUMENTATION and OTHER SOURCES governed by six rules and reached by zero patterns. Two writers on one batch found it independently, each after a defect shipped in SPECIFICATIONS and was caught downstream; building the complement view surfaced a further anthropomorphic verb in KERNEL DOCUMENTATION that no sweep had ever been able to see. **Do not read this as making label-colons bind in SPECIFICATIONS.** An earlier revision of this paragraph claimed exactly that, reasoning that 7r's catalog carve-out names LINUX KERNEL, KERNEL DOCUMENTATION and OTHER SOURCES but not SPECIFICATIONS. That was wrong, and a writer correctly refused the resulting instruction. 7a does not depend on 7r here at all: its own scope sentence puts **list bullets** outside body prose entirely, whatever section they sit in, and SPECIFICATIONS entries are list bullets. Their colon is also the format `guidelines/passes/01-research.md` mandates (`<spec name>, section <N.N>: <section title>`), so rewording them to silence the pattern would break a format another guideline requires — the compliant-construct defect this file warns about two paragraphs down. Label-colon candidates are skipped on every `[C]` row; the OTHER patterns are what the `[C]` tag exists to let through. (One inconsistency to be aware of while judging: 7a's scope sentence excludes all list bullets, while its later enumeration of acceptable placements names only LINUX KERNEL and KERNEL DOCUMENTATION catalog entries. The scope sentence governs; the enumeration is the narrower and older gloss.)

- `—` — em-dashes; no exemption outside fenced blocks.
- `[^:;.!?]{3,90}:\s+[A-Za-z0-9§]` — label-colon candidates (7a). **Never anchor this to line start.** 7f mandates one unwrapped line per paragraph, so a `^`-anchored pattern can only ever see a colon in a paragraph's FIRST clause, and every mid-paragraph label-colon — which is nearly all of them — is structurally invisible to it. Measured over eleven pages and ninety-nine known hits: the old `^[A-Z][^:]{2,80}: [a-z]` caught **12%**; this pattern over the prose view catches **100%**, at about eleven candidates per page and roughly 81% precision. Adjudicate all eleven; do not re-anchor the pattern to make the list shorter.
- `(usually|typically|generally|normally|commonly|mostly|often|simply|essentially|basically|arguably|in practice|tends to)` — hedges; hyphenated compounds ("read-mostly", "update-often") are exempt, and the prose view has already removed quoted text and fenced comments, which were the bulk of the old false positives.
- `(^|[^a-z])arms?([^a-z]|$)` — the branch-metaphor ban; the ban is on arming a BRANCH or a UNION CASE. Capitalized architecture names (Arm, ARM64, arm64) are exempt, and "arms a delayed work item" is the ordinary English verb and is compliant.
- `(contract|tall(y|ies|ied)|canonical|vtable)` — banned words.
- `\bis what\b|\bwhat matters\b|\bthe reasoning\b` — hollow clefts (7c/7d). Match the FRAME `is what`, never a list of spellings: a writer produced "is what keeps", "is what put", "is what lets" and "is what the … jumps to", and a three-spelling pattern saw none of them.
- `\b(live|lives|lived|living|sit|sits|sat|sitting|want|wants|wanted|wanting)\b` — anthropomorphic verbs applied to CODE (Gate B item 5). Grep the LEMMAS, not three inflections: a pass that greps only `lives`/`sits`/`wants` misses the base forms, where real hits have been found. The ban is on anthropomorphizing code or data placement; a userspace process is a real actor ("the reader wants the buffer" is exempt), and the adjective "live" ("the live counter") is not the verb.
- `(,|\band)\s+(not|never)\s` — negative constructions (asserting X by denying Y). Do NOT require the comma: a writer produced five of these as "X and never Y" / "X and not Y", every one invisible to a comma-anchored pattern. The digit class matters too — ", not 31." was a real finding an alphabetic-only pattern missed.
- `](.*\.md)` — internal cross-link candidates (run on the RAW file); only non-URL `.md` targets are violations, and 7f forbids them absolutely.
- ``\[`[a-z0-9/-]+\.md`\]\(`` — a page path carrying ANY link target (run on the RAW file). This is the stricter companion to the grep above and catches what it cannot: a sibling page named as a span but anchored to a SOURCE URL, e.g. ``[`device/container-context.md`](https://elixir.../xhci.h#L320)``. The target is not an `.md` path, so the first pattern passes it, and the anchor resolves cleanly, so an anchor check passes it too — yet it asserts that a page path is a kernel symbol. A page path is never a link of any kind; carry it bare. The same reasoning covers any non-symbol span: a tool name (`find_callers`, `git log`), a search-basis literal, or a prose phrase must never carry a source anchor, because a wrong-but-resolving anchor reads as clean to every mechanical check and asserts a false identity to the reader. Both instances of this class found so far were caught only by reading, after the anchor passed every automated check.
- `^#{2,4} (Why|How|Where|What)|^#{2,4} .*\?$` — banned heading shapes (run on the RAW file; headings are legitimately line-anchored).
- `\*\*` — boldface candidates (run on the RAW file); `/**` kerneldoc openers inside fenced code are exempt.

**Then sweep the figures, which the prose view cannot see.** The prose view discards every fenced block, so figure annotations are invisible to every pattern above — yet they are still governed. 7g lifts only the forbidden-PHRASE rules (7a, 7c, 7d) inside a figure; it does not lift rule 7, so the anthropomorphic-verb ban, the em-dash ban, and the negative-construction ban all still bind figure text. That combination — bound by a rule, unreachable by the mechanism — is exactly what let the label-colon class ship for eight pages, so close it explicitly:

```
awk '/^```/{f=!f; lang=(f? substr($0,4) : ""); next} f && lang!="c"' page.md
```

Adjudicate what that prints against rule 7 (anthropomorphic verbs, em-dashes, negative constructions). Two exemptions apply and are the common case: a ` ```c ` block is a source excerpt and is never swept (the filter above already excludes it), and a fenced block reproducing a VERBATIM quotation — a commit message, a kernel comment — is exempt like any other verbatim text (7r). What is left is figure annotation the page itself authored, and it is bound.

What no pattern can express stays a read-through: 7b prose-list shapes, 7d superlatives judged in context, heading truth (Gate B item 4, 7o), definition-plus-usage parity (Gate B item 1, 3b), coverage (item 6), figure geometry (item 8), and the whole 7o behavioral-claim audit. Every finding is fixed or recorded as a 7r adjudication with reasoning, never silenced.

**A grep is a candidate generator, never the gate.** FOUR classes have now shipped behind a pattern that structurally could not see them: the mid-paragraph label-colon behind a `^`-anchored grep; the figure annotation behind a fence-stripping view; the heading behind a prose view that dropped every `#` line, even though rule 7, 7d and 7o all bind headings; and the whole catalog region behind a blanket `if cat: continue` that generalized one shape-specific 7r exemption into a total blind spot. Two further near-misses came from the pattern rather than the region: a case-sensitive sweep cannot see a sentence-initial `What matters`, and `\b` treats `_` as a word character, so `\bnec\b` cannot see `TRB_NEC_GET_FW`. Each time, the check ran clean and the clean run meant nothing.

So the discipline is not "write better patterns", it is: **when a rule binds a region, confirm some mechanism actually reaches that region.** Enumerate the page's regions — prose, headings, figures, catalog bullets, table cells, fenced excerpts — and for each rule, name the pattern that can fire there. A region no pattern reaches is not clean; it is unexamined, and it reads exactly like clean.

The same trap has a second form, found the same way: **a permissive checker is worse than no checker.** A writer's excerpt verifier resynchronized on any mismatch and reported 44 of 44 units correct while two fabricated comment terminators sat in the page. It was tightened to resync only after a declared elision, and both fabrications surfaced immediately. A check that cannot fail is not a check.
