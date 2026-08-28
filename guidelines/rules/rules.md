# Writing rules and gates

Every criterion a generated page is judged against, except the diagram rules (see `diagrams.md`) and the settled adjudications registry (see `7r-adjudications.md`, which is the mandatory first read for every agent). Rule IDs are stable identifiers and never renumber: briefs, dossiers, and campaign specs cite rules by ID. `INDEX.md` maps every ID to its section here. Each rule below states the problem or the requirement, lists the words to watch where a fixed list exists, and shows the fix as a Before/After pair. Example text sits in fenced blocks so it stays byte-greppable; a trailing paragraph names what not to flag.

## Style and prose

How a page reads: sentence shape, banned constructions, and page structure. The writer sweeps these classes itself with 3c's procedure before reporting done, and the check pass reproduces them independently.

### 7. Core writing bans

Six bans that bind every sentence of every page.

**Em dashes.** Do not use them. Write parentheses or two sentences: "CC (Command Completed)", not "CC --- Command Completed".

**Boldface.** Do not use `**...**` in page prose.

**Negative constructions.** State what a thing is, not what it is not. Write "It is synchronous", not "It is synchronous, not asynchronous".

**Anthropomorphic placement verbs.** Code does not "live" anywhere: a symbol "is defined in" a file, a value "is held in" or "is represented by" a struct. Reserve "walk" for traversing a data structure (a list, the tree, the page tables, the ACPI namespace), which is its established kernel meaning; a scalar or state field "transitions through" or "advances through" its values.

**"vtable".** A struct that aggregates function pointers is a "function pointer struct" or its concrete type name (`struct file_operations`). "vtable" is a C++ term, not kernel terminology.

**Question-style headings.** No "Why X does Y" / "How X works" / "Where X happens" framings as H3 or H4 headings in DETAILS, SUMMARY, or any body section. Write declarative statements.

**Before:**

```
### Why _Exx clears status before the method
```

**After:**

```
### _Exx clears status before the method runs
```

**Before:**

```
### How acpi_ev_gpe_dispatch routes the event
```

**After:**

```
### acpi_ev_gpe_dispatch routes by dispatch type
```

**Before:**

```
### Why the EC uses a raw handler
```

**After:**

```
### EC installs a raw GPE handler
```

**Bare-noun DETAILS headings.** Every DETAILS H3/H4 is a declarative "what-does-what" statement (a subject performing an action on an object), never a bare noun or a bare symbol name. A reader should learn what the symbol does from the heading alone.

**Before:**

```
### vma_state_init
```

or

```
### The slab cache
```

**After:**

```
### vma_state_init creates the vm_area_cachep slab
```

**Before:**

```
### vm_refcnt
```

**After:**

```
### vm_refcnt encodes attach state and the per-VMA lock in six values
```

Do not flag the H3 catalog labels in LINUX KERNEL (`### Detection and dispatch (evgpe.c)`, `### _Lxx: level-triggered GPE method`, `### Tree store primitives (vma.h)`): grouped noun-phrase labels are correct there. Both heading bans govern DETAILS, SUMMARY, and body sections only.

### 7a. Label-colon prose

**Problem:** Generated prose leans on the "label: explanation" idiom — a noun phrase, a colon, then the clause that should have been the sentence. Body prose (everything outside H1–H4 headings, fenced code blocks, ASCII diagrams, list bullets, table cells, and Elixir links) must never use it. State the same content as a plain declarative sentence.

The banned forms, each with its fix:

**"X: Y." — Before:**

```
Two-phase handshake: a status read, then a gated write.
```

**After:**

```
The handshake has two phases. advance_transaction reads EC_SC first, and writes the next byte only when IBF is clear.
```

**"X is Y: Z." — Before:**

```
The asymmetry: an edge GPE clears status before the method, a level GPE after.
```

**After:**

```
An edge-triggered GPE clears its status before the method runs; a level-triggered GPE clears it after.
```

**The "is the key:" family** ("X is the key: Y" / "X is essential: Y" / "X is explicit: Y" / "X is significant: Y" / "X is conservative: Y" / "X is deliberate: Y" / "X is the linchpin: Y" / "X is asymmetric: Y" / "X is intentional: Y" / "X is correct: Y" / "X becomes clear here: Y") — **Before:**

```
The IBF gate is essential: IBF stays 1 until the EC consumes the byte just written.
```

**After:**

```
IBF stays 1 until the EC consumes the byte just written, so advance_transaction sends the next byte only when IBF reads 0.
```

**The "The intent:" family** ("The intent: Y" / "The reasoning: Y" / "The result: Y" / "The fix: Y" / "The condition is: Y" / "The order of operations matters: Y" / "The pattern is: Y" / "The point is: Y" / "The takeaway is: Y") — **Before:**

```
The reasoning: a level source stays asserted until the AML quiesces it.
```

**After:**

```
A level-triggered source stays asserted until the AML quiesces the device.
```

**Colon-introduced quotes** ("X says: <quote>" / "X makes Y explicit: <quote>" / "X spells this out: <quote>" / "Comment: <quote>") — **Before:**

```
The comment "Note: disables and clears all GPEs in the block" is the key: events only flow after an explicit enable.
```

**After:**

```
According to the comment "Note: disables and clears all GPEs in the block", events only flow after an explicit enable.
```

**Colon-introduced lists** ("X is called from N places: A, B, C."). Replace with "X is called from N places. A does ..., B does ..., C does ...". The list-after-colon shape is banned even when the items are short.

Never editorialise with "The reasoning:" or any synonym ("The rationale is", "The motivation:") that asserts authorial reasoning: the page describes what the code does, and a rationale exists only where a comment or commit message states one, quoted via "According to the comment <quote>, ...". When removing a colon-label, state the underlying mechanic as a plain declarative sentence; swapping the colon for "X matters because Y" or "X is what makes Y" asserts importance the same way and is banned by 7d.

Do not flag the colon inside H3/H4 headings (catalog labels like `### _Lxx: level-triggered GPE method`), Elixir link titles, code blocks, URLs, ratios (`M:N`), or after Markdown list bullets when the item is a catalog entry in the LINUX KERNEL or KERNEL DOCUMENTATION section. The ban binds flowing prose paragraphs and the lead summary paragraph.

### 7b. Intro sentence + list

**Problem:** Generated prose presents an explanation as an intro sentence followed by a bullet or numbered list. In DETAILS, SUMMARY, and the lead summary paragraph, fold the items into a single flowing paragraph. The forbidden shape is "<noun phrase ending in a period or colon> + <bullet/numbered list>" used as exposition; phrases that head such lists ("Two notable details.", "Three layers stack.", "Four cases run from strongest to weakest.", "Concrete uses.", "Five upfront refusals.") are banned even with a period.

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

Do not flag the H3 catalog lists in LINUX KERNEL (grouped by file or functional area as the sample pages do: `EC_SC status bit macros`, `Port accessors`, `Transaction state machine`) or the bullet lists in KERNEL DOCUMENTATION and OTHER SOURCES: those are reference catalogs and remain as lists. Tables remain as tables. The ban covers prose-explanation lists only.

### 7d. Hollow superlatives

**Words to watch:** the most invasive, the most fragmenting, the most aggressive, the most consequential, the most preferred, the least preferred, the most expensive, the cheapest, the cheap path, the slow path, the fast path, the strongest guarantee, the weakest guarantee, the strongest anti-fragmentation guarantee, the worst outcome, the best outcome, the entire performance benefit, the entire correctness benefit, the key invariant, the key difference, the key innovation, the key role, the design assumption, the design intent, X matters, X matters because Y, X is what makes Y, what makes X work, the only mode that, elaborate, elegant, fundamental, cornerstone, linchpin, crucial, critical

**Problem:** Generated prose ranks a kernel construct ("the most invasive handler path", "the key difference") without naming the mechanic that would justify the ranking. Each kernel symbol, mode, or path is unique by definition, so the unexplained superlative adds zero information. "X matters" and "X is what makes Y" assert importance instead of stating the mechanic. "Fast path" and "slow path" are acceptable only where the kernel itself defines them (the fast path of a specific lock implementation). "The only mode that ..." fails when the same is trivially true of every other mode under some other framing.

The test for any adjective in body prose: would the sentence still convey the mechanic with the adjective deleted? If yes, delete it. If no, replace the adjective with the actual mechanic. A superlative that cannot be reduced to a concrete code-level fact does not appear at all.

**Before:**

```
acpi_ev_gpe_dispatch is the most invasive handler path.
```

**After:**

```
acpi_ev_gpe_dispatch disables the GPE with acpi_hw_low_set_gpe(), clears edge-triggered status with acpi_hw_clear_gpe(), then routes by dispatch type.
```

**Before:**

```
A raw handler is the cheap path through acpi_ev_detect_gpe().
```

**After:**

```
acpi_ev_detect_gpe() invokes the raw handler directly at interrupt level, skipping the disable/clear/re-enable protocol that acpi_ev_gpe_dispatch() runs.
```

**Before:**

```
This is the strongest guarantee against a lost edge.
```

**After:**

```
Clearing an edge-triggered GPE's status before queueing the method ensures an edge arriving during servicing re-latches instead of being lost.
```

**Before:**

```
the key difference from a method GPE
```

**After:**

```
a method GPE queues acpi_ev_asynch_execute_gpe_method() via acpi_os_execute(); a raw-handler GPE calls the handler synchronously at interrupt level.
```

Keep direct quotes from kernel source comments, commit messages, and LKML threads verbatim even when they contain superlatives this rule would otherwise forbid.

### 7c. Forbidden phrases checklist

The sweep list for the classes above and the two ban classes that live here. Scan every body paragraph for these before writing on, and rewrite hits as plain declarative sentences; quote comments with "According to the comment <quote>, ..." or "The comment reads <quote>." instead of label-colon framing.

#### Scan patterns

**Words to watch:** The reasoning (any case, with or without colon), The intent:, The asymmetry:, The fix:, The point is:, The takeaway:, The pattern is:, Two-phase pattern:, is the key:, is essential:, is explicit:, is significant:, is conservative:, is deliberate:, is the linchpin:, is asymmetric:, is intentional:, is correct:, becomes clear here:, says: ", spells this out: ", makes explicit: ", makes the trade-off explicit: ", Comment: "

**Problem:** These are the grep-shaped tells of 7a and 7d. Two need care: a label-colon can sit anywhere in a prose sentence, not merely at its start, and 7f puts each paragraph on one unwrapped line, so a line-anchored pattern sees only a paragraph's first clause and misses the rest of the class (3c's prose view is the procedure that actually reaches it). `Comment: "` in prose differs from the LINUX KERNEL bullet form `[symbol]: bit 0xN. Comment: "..."`, which is a catalog entry and acceptable. The "intro sentence + list" shape of 7b and the colon-introduced list ("X is called from N places: A, B, C") belong on the same sweep.

#### Banned words

**Words to watch:** contract, tally, tallied, tallies, tallying, canonical, arm, arms (for a branch or union case)

**Problem:** Each of these asserts a framing without naming a mechanism. Replace each with the concrete rule, count, or helper it stands in for.

**"contract"** (including "the X, Y, Z contract") — name the actual precondition, guarantee, rule, or invariant. **Before:**

```
The reset, duplicate, destroy contract spans every per-object state.
```

**After:** state the reset rule, the duplicate rule, and the destroy rule each path follows.

**"tally"** — use "count" or "running count". **Before:**

```
the running tally of VMAs
```

**After:**

```
the running count of VMAs
```

**"canonical"** — name the helper or path plainly. **Before:**

```
the canonical helper is vma_link() in mm/vma.c
```

**After:**

```
the helper that performs it is vma_link() in mm/vma.c
```

**"arm" / "arms"** for a case of a union, a branch of a conditional, a side of a split, or one member of a pair of code paths — use "branch", "case", "side", "leg", "half", or the concrete symbol name. **Before:**

```
the write-fault arm of do_wp_page
```

**After:**

```
the write-fault branch of do_wp_page
```

Do not flag CPU-architecture names (Arm, ARM64, arm64) or verbatim quotes from kernel source or commit messages.

#### Hedges

**Words to watch:** usually, typically, generally, often, normally, commonly, mostly, in practice, tends to, on a hot cpu

**Problem:** Each hedge dodges the actual condition the code tests. Name that condition instead.

**Before:**

```
A vm_area_alloc() on a hot cpu usually takes a ready object from the per-cpu sheaf without locking a shared slab.
```

**After:**

```
A vm_area_alloc() takes a ready object from the per-cpu main sheaf without locking a shared slab while that sheaf is non-empty, and reaches the shared slab only to refill an empty sheaf.
```

Do not flag a frequency word reproduced verbatim from kernel source inside a fenced block, or a genuine measured statistic that cites a counter or benchmark.

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

### 7f. General page rules

Page-shape requirements that apply to every page regardless of subsystem.

**Rule:** H1 is always the topic name only. Immediately below the H1, before the summary paragraph, every generated page carries this exact AI-generated-content caution blockquote, reproduced verbatim (including the repeated final line):

```
> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.
```

**Rule:** `Documentation/` references go in KERNEL DOCUMENTATION, never in OTHER SOURCES. When an existing page has `Documentation/` links in OTHER SOURCES (or `docs.kernel.org` / `kernel.org/doc` URLs), move them to KERNEL DOCUMENTATION; do not convert the existing URLs, add a new Elixir cross referencer reference entry pointing to the same in-tree kernel doc file.

**Rule:** No hard line wrapping in prose. Each paragraph is a single long line, with line breaks only between paragraphs, at no column width. Code blocks (between ` ``` ` markers), ASCII diagrams (indented lines), list items, and table rows are exempt.

**Rule:** Every mention of a kernel symbol (function, macro, struct, enum, typedef) is an Elixir cross referencer link. No exceptions. This covers every inline code span (`` ` `` ... `` ` ``) in every section — SUMMARY, LINUX KERNEL, INTERFACES, DETAILS, and prose paragraphs — including inline code with arguments such as `` `func(arg1, arg2)` `` in INTERFACES sections.

- Write [`function_name()`](https://elixir.bootlin.com/linux/v7.0/source/path/to/file.c#L123) instead of bare `function_name()`.
- Write [`func(arg1, arg2)`](https://elixir.bootlin.com/linux/v7.0/source/path/to/file.c#L123) instead of bare `func(arg1, arg2)`.
- Write [`struct foo`](https://elixir.bootlin.com/linux/v7.0/source/path/to/file.h#L45) instead of bare `struct foo`.
- Write [`MACRO_NAME`](https://elixir.bootlin.com/linux/v7.0/source/path/to/file.h#L78) instead of bare `MACRO_NAME`.

The only place bare symbol names are acceptable is inside fenced code blocks (` ``` `) that show code snippets or struct definitions. A symbol appearing several times on the same page is linked at every occurrence outside code blocks (repeat the link). A symbol whose file and line cannot be determined is looked up before it is written; a name that truly is not in the kernel source (a spec-defined ACPI method like `_PS0`, a hardware register like `SLP_EN`) may stay unlinked with a comment noting it is a spec/hardware name.

**Rule:** A struct or enum type always carries its `struct` or `enum` keyword (`struct acpi_gpe_event_info`, `enum ec_command`) unless the type is a typedef. This applies everywhere: LINUX KERNEL entries, SUMMARY, INTERFACES, DETAILS, and inline prose. In the LINUX KERNEL `'\<...\>'` entry format the keyword goes inside the angle brackets: `'\<struct acpi_gpe_register_info\>'`, `'\<enum ec_command\>'`.

**Rule:** No internal cross-links. Do not link to other pages in the knowledge base (`[Page Title](other-page.md)`); each page is self-contained.

**Rule:** Kernel source cited in Markdown code blocks keeps the exact indentation of the kernel source: tabs (8-space width), never converted to spaces — function bodies, switch/case statements, and multi-line expressions alike.

**Rule:** Every OTHER SOURCES entry uses the markdown link format `[Title](URL)`; no bare URLs, no `Title — URL` style.

**Rule:** The DETAILS section includes detailed kernel code walkthroughs: step-by-step traces through function call chains, real driver API usage examples, and lifecycle coverage for key objects. Every function/struct/enum in the LINUX KERNEL section gets at least one concrete driver usage shown in DETAILS. Kernel code paths are cited as fenced ` ```c ` blocks, then explained — never described in prose alone.

---

## Facts, code, and coverage

What a page must prove and how it must prove it: excerpts, provenance, enumeration, claim verification. These are the classes the writer owns end to end and the exit suite checks.

### 7e. Self-contained kernel-source citation

**Problem:** A page that describes code without showing it forces the reader into the tree. Every page reads as a self-contained source: a reader who never opens the kernel tree still finishes the page knowing exactly what the relevant code does. Wherever the page explains how a function works, what a struct looks like, how a macro is used, or how a call site invokes a callee, the actual code goes inline as a fenced ` ```c ` block before or alongside the explanation. The Elixir link is for navigation; the code block is for comprehension. "See [`func()`](https://elixir...)" does not count as showing the code.

**Rule:** Never fabricate, paraphrase, or approximate kernel source. Every ` ```c ` block is the real code, located and verified with the semcode tools (`find_function`, `find_type`, `grep_functions`) and by reading the on-disk source file, then reproduced verbatim: exact text, all comments, tab indentation. Confirm the symbol exists at the documented version and the lines match the file before citing them; a symbol whose real code cannot be located gets no code block. Where a semcode index disagrees with the working tree, the on-disk source at the documented version is ground truth.

**Rule:** Every function in LINUX KERNEL gets at least one ` ```c ` block in DETAILS: its full body when small, or the body of the case label / branch / inner block the page actually describes. A function whose body fits in a screen of code is shown, not described. Every struct or enum in LINUX KERNEL gets its type definition reproduced (comments and `#ifdef` regions included), so the reader sees the exact field list without leaving the page. Every macro or static array referenced in body prose (`fallbacks[][]`, `__used` lookup tables) is reproduced where the prose first depends on it.

**Rule:** A call-chain walk shows both ends: the caller's invocation site as one block, the callee's body as another. A switch, conditional, or loop whose structure is the point is reproduced verbatim, never paraphrased. A kernel comment is quoted inside the fenced block that contains its surrounding code and referenced in prose via "According to the comment <quote>, ...". A commit message carrying a benchmark table or ASCII figure is reproduced in a plain ` ``` ` fence so the formatting survives.

Each block stays as close to the source as practical: tabs preserved, comments retained, `...` elision only for irrelevant intermediate code that changes nothing for the reader. A body too long to reproduce in full is split across blocks at natural boundaries (one per case label, loop, or error-handling tail) with prose between, never truncated.

The sufficiency test: with the page open in one window and no terminal, no other tab, no kernel tree, could the reader describe in their own words exactly which lines run on the documented path? If not, more code blocks are needed. DETAILS is the place for bulk citation; SUMMARY may carry a short snippet when a single line of code conveys the topic best.

### 7l. Code-block provenance comments

**Rule:** Every fenced ` ```c ` block opens with a provenance comment naming the on-disk origin of the excerpt, in the exact form `/* path/from/tree/root.c:LINE */` on its own first line, where LINE is the number of the first reproduced line in the file at the documented version. A short annotation may follow the line number (`/* mm/vma.c:497 (in __split_vma()) */`). A block that stitches excerpts from several places (a caller plus its callee, two distant case labels, a struct field plus the helper that writes it) marks each excerpt's start with its own interior `/* path:line */` delimiter, and marks elided code with a standalone `...` line. Everything between delimiters is verbatim file content per 7e.

The provenance comment is what makes a page checkable: a reviewer opens the named file at the cited line and compares the unit directly (the 3c procedures), so a missing or wrong provenance line turns an on-disk match into a finding, and a silently drifted excerpt is caught on the first comparison. Non-code fences (ASCII figures, quoted commit-message tables, shell output) carry no provenance comment and are not diffed.

### 7m. Link anchoring and exhaustive span linking

This rule extends the every-symbol-linked rule in 7f with URL construction, anchor selection, and exhaustiveness. It is what the numbers in `guidelines/reference/measured-criteria.md` call links per page.

**Rule:** URLs use the base `https://elixir.bootlin.com/linux/<version>/source/`, where `<version>` is the documented kernel version from SKILL.md's Input section (for campaigns, the version pinned in the plan file's Context). One page never mixes versions. The examples below use `v7.0`.

For file references:
```
[`path/to/file.c`](https://elixir.bootlin.com/linux/v7.0/source/path/to/file.c)
```

For function references (include the line number; the `\<...\>` word-boundary markers keep the reference compatible with `git log -L`):
```
[`'\<function_name\>':'path/to/file.c'`](https://elixir.bootlin.com/linux/v7.0/source/path/to/file.c#L1234)
```

For kernel documentation files:
```
[`Documentation/subsystem/file.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/subsystem/file.rst): brief description
```

**Rule:** A link whose text is a symbol name (`` `vma_start_read()` ``, `` `struct mm_struct` ``, `` `VM_LOCKED` ``, the LINUX KERNEL `` `'\<sym\>':'path'` `` form) anchors at the symbol's DEFINITION line, so the reference stays valid for `git log -L` and survives unrelated churn — never at a call site, a comment mention, or a line inside some other function's body, even when that line is what the prose discusses. A reference to a specific non-definition place (a call site, one branch, one field assignment) is a file-location link whose text is the path and line: [`mm/vma.c:717`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L717). Prose that enumerates call sites carries one location link per site, so every count is checkable one click deep.

**Rule:** Every occurrence of every kernel symbol outside fenced blocks is linked, repeats included. The exhaustive pass covers the classes easiest to skip: `CONFIG_*` options link to the `config X` line of the declaring Kconfig file; generic primitives (`READ_ONCE()`, `memcpy()`, `rcu_read_lock()`, `atomic_read()`, and the like) link to the definition relevant to the documented architecture; a field path written `a->b` or `foo.bar` links to the field's declaration line inside the struct definition; an ops-struct member named in prose ("the `fault` hook") links to that member's line in the ops struct definition.

Do not flag these settled bare spans: C keywords and operators; local variables, parameters, and goto labels quoted from an excerpt; literal and error values (`-EINVAL`, `NULL` as a value); `/proc`, `/sys`, and sysctl path strings; Kconfig syntax fragments (`=y`); tracepoint field names; a wildcard family name (`VM_*`) when the members it stands for are linked nearby; commit hashes; the `name(2)` man-page notation when the page links the syscall's kernel entry point elsewhere; symbols verified absent from the documented tree (state the absence in prose). Precedent never overrides the rule: "other pages leave `CONFIG_FOO` bare" or "this page already has thirty bare `READ_ONCE()` spans" is not a reason to leave the next one bare — the rule wins, and pre-existing in-family spans get fixed in the same pass.

### 7n. OTHER SOURCES provenance

**Rule:** Every OTHER SOURCES entry is a mailing-list URL taken byte-exactly from a `Link:` trailer in `git log` output for a commit the page discusses (both `https://lore.kernel.org/...` and `https://lkml.kernel.org/r/<message-id>` trailer forms qualify), or a lore.kernel.org URL returned by the semcode `dig` tool for that commit. Never construct, guess, or "normalize" a URL: no hand-built `git.kernel.org/.../commit/?id=` links, no reconstructed lore paths, no search-result URLs. Format each entry as `[<commit subject> (commit <abbreviated sha>)](<trailer URL>)`. A relevant commit with no `Link:` trailer is cited in prose by sha and subject and gets no OTHER SOURCES entry.

### 7j. Behavior and construct coverage

**Problem:** A page that documents only the single function path that prompted it is incomplete. Breadth of coverage — every site that exhibits a behavior, every struct and helper that backs it, the full object lifecycle — is as mandatory as the prose and citation rules (7 through 7f).

**Rule:** Cite every site that matches a behavior, not one. Enumerate the full set with `find_callers`, `grep_functions`, and Grep before writing; cite each site with an inline Elixir link at the mention and a ` ```c ` block in DETAILS. When the set is too large to cite exhaustively, cite a representative spread (the core implementation plus several users) and state how many sites exist — never silently narrow to one.

**Rule:** Cover the data structures and their helpers, not only entry-point functions: the structs, enums, and typedefs that hold the state, plus the helpers and accessor macros that allocate, initialize, read, modify, and destroy them — listed in LINUX KERNEL, defined as ` ```c ` blocks in DETAILS, and shown in use. A page that names a behavior but omits the struct that records the state, or the helper that changes it, is incomplete.

**Rule:** Draw the structure, not only describe it. A mechanism with spatial, temporal, or transformational structure (a data or bit layout, an object topology, a reshaping operation, a state machine, a sequence across actors) is drawn per the diagram rules (7g, 7v, 7h, 7i in `guidelines/rules/diagrams.md`), with as many figures as the material earns and never in one of 7v's banned shapes. A page that walks a split, merge, insertion, teardown, or fork without showing the structure before and after has a coverage gap. 7g's restraint still decides which candidates are real: no figure for a plain call chain, a two-state toggle, or anything one declarative sentence conveys.

**Rule:** Cover the object lifecycle and asynchronous behavior: allocation, initialization, freeing, the serializing locks, reference counting (`kref` / `refcount_t` get and put, and the put that frees), state transitions (which field advances through which states and what drives each edge), notification mechanisms (notifier chains, `struct completion`, wait queues, eventfd, uevents), deferred work (`work_struct` and `delayed_work`, tasklets, timers, threaded IRQs, RCU callbacks), and the ordering and concurrency rules between them. Tracing only "function A calls function B" misses what the page exists to explain.

**Rule:** Call out hard-coded limits explicitly: timeouts, retry and attempt counts, maximum error counts, buffer and queue sizes, poll and backoff intervals — macro, enum value, or bare literal. Find as many as exist; name each with its value and the symbol or literal that holds it, cite its file and line, and reproduce the defining line where the value governs a walked path. A described timeout, retry loop, or threshold without its actual number is incomplete.

**Rule:** The catalog and the scope statement define done-ness. A page is complete when every LINUX KERNEL symbol and every scoped behavior is covered to the rules above; "the core API is documented" is not a completion test, and importance ranking never shrinks coverage. Material that outgrows one page splits along a boundary statement into sibling pages; no page thins its coverage to shorten itself. Compression may remove words, never coverage: shortening must not drop cataloged symbols, behaviors, call-site enumerations, layout-bearing figures, or KERNEL DOCUMENTATION / OTHER SOURCES entries — any such cut is a deliberate scope change (catalog and scope shrink in the same edit, and the cut is reported; 7p governs derivation). Within DETAILS, order generic to specific: the shared mechanism first, then the vendor-, channel-, or driver-specific instances.

### 7k. Driver examples

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

### 7o. Behavioral-claim verification

**Problem:** A page is a set of claims about kernel behavior, and the class of error that reads correctly, links correctly, and survives every mechanical check is the unverified claim. Each claim class below has a named audit action: perform them while writing, and re-perform them when reviewing, enhancing, or reusing a page.

**Rule:** Universal quantifiers are enumerations. A sentence containing "only", "never", "always", "all", "every", "exactly N", "the single", or "once" asserts the size or uniformity of a set: enumerate that set first (semcode `find_callers` plus a tree-wide grep that includes headers), then cite every member with location links or weaken the sentence to what the enumeration shows. History: a page asserted a helper "is invoked from exactly one place" while the tree held four callers (the plain store helper, its gfp variant, the fork-path bulk store, an error-path rollback); only re-running the enumeration catches this class.

**Rule:** A per-member claim is as many claims as the family has members. "Each X ..." / "every X ..." over a family ("each wrapper forwards to exactly one underlying primitive", "every callback runs under the lock", "each descriptor slot maps to one register") is verified by building the member-to-property mapping first; one exception falsifies the sentence. When an exception exists, restate to what the mapping shows, restrict the family explicitly ("every read-side helper ..."), or name the classifier and what falls outside it ("one primary primitive, plus cursor-bookkeeping helpers") — an unstated classifier is how a strictly-false claim reads as true. History: a lead sentence claimed each wrapper "forwards to exactly one" primitive while the page's own per-helper table showed one wrapper calling a range-setup helper plus the store primitive.

**Rule:** Lead and SUMMARY compression gets no precision waiver. Quantified, universal, and per-member claims there are audited exactly like DETAILS claims and must agree with the DETAILS evidence on the same page; cross-check every lead and SUMMARY quantifier against the page's own tables and enumerations at sign-off. Compression may drop detail, never trade accuracy for sweep.

**Rule:** Every enumeration states its search basis inline — directories searched, headers included or not, definition sites excluded, architecture and CONFIG filter: "a grep across mm/, fs/, kernel/, drivers/, arch/x86/, and include/ at this tree finds 118 call sites of ... outside their definitions". A count without its basis cannot be re-verified and does not qualify; a count that holds only under the page's CONFIG assumptions (a caller compiled out without `CONFIG_MMU`) says so at the claim. Counts are re-derived at every review, never trusted — a re-count on a live page corrected a written 119 to the 118 on disk.

**Rule:** A restated condition is derived, not paraphrased. Prose restating a guard or threshold ("requires map_count + 2 < sysctl_max_map_count - 3") is derived from the reproduced code by exact negation of its operator, keeps the exact constants, and shows the guard as a code block beside the sentence so the reader can repeat the derivation.

**Rule:** Headings are claims. A DETAILS heading must be true of everything in its section, and a heading edit is a claim edit; verify each heading against its section's excerpts after writing and after every rewording. History: a polish pass strengthened "the accessors mediate every flag change" into "the accessors take the write lock before every flag change" directly above an excerpt whose own kernel comment reads "needs no locking".

**Rule:** Prose does not outrun its excerpt. Read each behavioral sentence against the adjacent code line by line. Semantics carried by a primitive's own name are behavior and are stated: an ordering suffix (`refcount_set_release()` orders the preceding field writes before the count becomes visible to an acquiring reader), a `_locked`/`_unlocked` variant, an RCU flavor, saturation semantics. The one licensed exception is the disclosed domain-model synthesis of 7s — assembled from named on-disk materials with every fact under it still individually cited; it never licenses an undisclosed, unsourced, or guessed assertion, and 7c and 7d bind it in full.

**Rule:** Invariant claims get a counterexample search. Before asserting "set once and never changes", "always called under lock L", or "freed only through F", search explicitly: every assignment site, every lock-less caller, every free path. Cite the kernel's own enforcement where it exists (`lockdep_assert_held()`, `VM_WARN_ON()`, a `const` qualifier) — an assertion line is stronger evidence than a grep that found nothing. Provenance line numbers are claims too (7l): content matching does not validate them; open the file and confirm the excerpt begins at the cited line.

### 7s. Domain-model layer

**Problem:** A page that opens straight into per-symbol definitions leaves the reader to reverse-engineer the model the page exists to convey — the difference between a reference catalog and an explanation. A page teaches the subsystem's model of its topic: the states an object moves through and their transitions, the phases of a process, the taxonomy its parts fall into, and the rules that govern these. State the model as a model, in the lead and SUMMARY and ahead of the DETAILS walkthroughs, and let it organize the body (7u) rather than sit as a preamble to a per-symbol catalog.

**Rule:** The model's source decides how it is written. When a normative specification fixes it (an ACPI, PCIe, USB, or hardware-manual definition of a register layout, state set, or protocol), cite the spec in SPECIFICATIONS, present the model as the spec defines it, and map the kernel's constructs onto it (the spec-semantics-paired-with-kernel-slots form), so the reader learns a state's specified meaning and the constant that carries it together. When no specification defines it — the common case for pure-software subsystems — the model is a synthesis assembled from the kernel's own materials: the code, the enumerating comments and struct doc-comments, the relevant `Documentation/` pages, and the commit messages of the introducing series. This is the one place a page states more than a single excerpt witnesses, licensed only under disclosure: name the materials ("Assembled from the type comment, `Documentation/mm/process_addrs.rst`, and the series that introduced the per-VMA lock, the model is ..."), keep every fact under the model separately cited per 7e and 7m, and weaken or scope anything the materials do not support per 7o. 7c and 7d bind in full: plain declaratives naming mechanics, no hollow superlatives, no importance-framing, no label-colons. The frozen mm samples (`guidelines/reference/samples/`) show the synthesis stated up front.

A model the tree's own materials do not support is never invented to fill the section: state what the sources establish and stop. A guessed model ("the design is presumably ...") is worse than none.

### 7t. Semantics tables for state sets and taxonomies

**Rule:** A fixed set of states or modes, or a classification of parts (a device power-state set, a page-fault-type set, a flag taxonomy, an error-code family, an ops struct's callback set), is presented as a table, not a bare list of constants: one row per member, a meaning column stating what the member is in the model (7s), and a construct column linking the defining code (7m). The encoding and lifecycle archetypes among the frozen samples show this member-meaning-construct shape for bitfields and object states.

**Rule:** A state set additionally documents its legal transitions — which member advances to which, and what drives each edge — as a transition table or, where the transitions carry spatial or temporal structure, an ASCII state figure under 7g, 7v, and the 7i catalog. The table stays Markdown; 7v bans redrawing it in box characters. A taxonomy documents its classifying axis: what distinguishes each class from its siblings, not only that the classes exist.

### 7u. Journey- or model-first organization

**Problem:** The catalog-first page — one DETAILS heading per symbol, walked in declaration order — is a reference catalog wearing an explanation's clothes. A page is organized as a journey or around a model, never as a catalog of its symbols: LINUX KERNEL is the reference catalog, where a list is correct; DETAILS is not. Its sections are the chapters of a journey (the phases of a process traced start to end) or the facets of a model (the roles, states, or classes of the mechanism), and each cataloged symbol appears inside the chapter or facet where it does its work, shown there with its definition and usage excerpts.

**Rule:** Choose the spine from the topic. An operation or pipeline (a syscall path, a page fault, a split or merge, a device probe, an on-disk or on-wire translation) is a JOURNEY: organize DETAILS by its phases in run order. A static object or state space (a struct, a flag set, a lock's states, a power-state set) is a MODEL: organize by roles, states, or classes. An object with an operation on it leads with the model, then traces the operation as a journey through it.

**Rule:** The test is the DETAILS headings. Headings one-per-symbol in catalog order are the catalog-first failure and are reorganized, every symbol re-homed inside the phase or facet where it acts. Headings naming phases ("the boot table is parsed before the namespace exists") or facets ("the per-VMA lock state") are journey- or model-first. Reorganization never weakens coverage: every cataloged symbol still appears in DETAILS with definition and usage excerpts (3b item 1) — organization changes WHERE a symbol is shown, not WHETHER. A symbol that fits no phase or facet signals wrong organization or wrong catalog membership, never license for a stray per-symbol section.

**Rule:** Diagrams obey the same spine (7g): a figure depicts the page's journey (pipeline, sequence, before-and-after, lifecycle) or its model (state machine, topology, taxonomy); where the journey or model is large enough to carry the page, one figure shows it whole as the reader's map. A figure that is only symbols in boxes with no process or relationship is a catalog in visual form — redrawn to show the relationship, or dropped.

This rule and 7s are a pair: 7s puts the model at the top of the page, 7u organizes the body around it.

### 7p. Deriving from an existing page

**Rule:** Producing a page from existing material of any provenance — an earlier-generation draft, a prior revision, pages being compressed, merged, or split — follows four steps:

1. **Inventory the source first.** List its LINUX KERNEL catalog entries, DETAILS sections, distinct behaviors and call-site enumerations, figures, and KERNEL DOCUMENTATION and OTHER SOURCES entries.

2. **Give every inventory item an explicit disposition:** kept (and where it lands), merged (into which section), or cut (with the reason). No item disappears without a disposition — silent coverage loss during rewriting is the failure mode this rule exists to prevent.

3. **A cut is a scope decision, not an edit.** It removes the item from the LINUX KERNEL catalog and the scope statement in the same change, and is reported in the final message (and the campaign plan file) so the orchestrator or user can veto it. A symbol that stays in the catalog cannot have its DETAILS coverage cut.

4. **The derived page passes the same Gate B parity audit (item 1) as a fresh page.** Coverage in the source is not coverage in the derived page; "the source covered it" fails the audit.

History, and the measured failure that motivates the rule: a 2,645-line page compressed to 1,268 lines kept its iterator-helper symbols in the catalog while silently dropping their DETAILS sections, kept one catalog symbol with no DETAILS mention at all, and landed at 0.73 fenced blocks per catalog entry where every conforming page measures at least 1.0. The parity audit catches the desync mechanically; the disposition list is what makes any removal legitimate.

---

## The gates

What a finished page is measured against. Gate A is mechanical, Gate B is the review sign-off, and 3c holds the by-hand procedures both of them use.

### 3a. Gate A (mechanical, grep the finished page)

Confirm zero hits for each, and re-run after every edit including your own hand-edits:

- em-dashes
- `**` boldface in prose
- the label-colon-explanation idiom in prose (7a/7c), excluding the caution blockquote and text inside quotes
- the 7c/7d editorializing and superlative phrases (`the reasoning`, `is the key`, `X matters`, `X is what makes Y`, `the pattern is`, `worthwhile`, `crucial`, `elegant`, `cornerstone`, `the most <adj>`, and the like)
- the banned words `contract`, `tally` (also `tallied`/`tallies`/`tallying`), `canonical`
- vague hedges (`usually`, `typically`, `generally`, `normally`, `commonly`, `mostly`, `in practice`, `tends to`)
- `vtable`
- the word `arm`/`arms` for a branch or union case (7c; CPU-architecture names and verbatim quotes exempt)
- internal `.md` cross-links
- and `Why`/`How`/`Where` or trailing-`?` headings.

The grep list above is the gate. Run it by hand, fence-aware, using the candidate greps in the 3c check procedures below, and judge every hit against the exemptions and the 7r registry before editing; never reword an exempt construct to silence a pattern.

**Match case-insensitively when sweeping, then use case as evidence when judging.** The phrases above are written lowercase, and a case-sensitive sweep silently misses every sentence-initial occurrence. History: a writer's "What matters here is that…" survived the cleft pattern because `what matters` was matched literally, surfacing only under an unrelated superlative grep. Case still carries meaning at the judging step, where it belongs: the arm-word ban exempts the capitalized CPU-architecture names (`Arm`, `ARM64`) per 7r, so a case-insensitive sweep is expected to surface those and the adjudication is expected to clear them. Sweep wide, judge narrow; a pattern that cannot see a candidate cannot be adjudicated at all.

The same reasoning applies to word boundaries: `\b` treats `_` as a word character, so a banned token inside an identifier (`TRB_NEC_GET_FW`) is invisible to `\bnec\b` — sweep such tokens with letters as the only delimiter. Boldface and the 7b prose-list shapes are read-through checks.

A page is final only at zero unadjudicated findings. The gate is a manual procedure; the 3c check procedures in this file carry the candidate greps and the no-checker-script doctrine.

### 3b. Gate B (review sign-off, the rules a grep cannot catch)

Verify each item by performing the named action and recording the evidence (a count or a list, not "looks fine"). A page is not done until every item is confirmed; reading the page is not sufficient.

Ownership and timing: the writer owns this gate's factual items by construction and by its mechanical exit suite (`guidelines/passes/02-write.md`), and it also runs Gate A (3a/3c) on its own prose — an earlier split that forbade this was withdrawn, because the sweeps are procedure rather than perception and survive self-application (the reasoning is in `guidelines/passes/03-check.md`). The orchestrator then re-runs every mechanical check independently and compares the answers; it adjudicates every residual and never delegates that. A verify campaign re-runs the whole gate later, on a newer tree or under a different model.

A page is final only at zero unadjudicated findings.

#### 1. Catalog-to-DETAILS parity (7e/7j)

Build a parity table with one row per LINUX KERNEL catalog symbol and two evidence columns: where DETAILS reproduces its definition (or the exact case label / branch the page describes) as a fenced ` ```c ` block, and where DETAILS shows a concrete caller or usage as code. Every cell must hold a location in the page; an empty cell is a gap, and a catalog symbol that appears nowhere in DETAILS is a hard failure. Check the reverse direction too: a symbol that carries its own DETAILS section belongs in the catalog. When the page names several distinct users or call paths for one symbol, each named one appears as an excerpt or a per-site location link (7m) and the shown-versus-enumerated split is stated. Tripwire before building the table: fewer fenced ` ```c ` blocks than catalog entries means unpaired symbols (every conforming page measured runs 1.03 to 1.47 blocks per entry; a deficient derived page measured 0.73). Record the table; a bare count does not qualify. Sign off only at zero empty cells.

#### 2. Grounded, non-fabricated code (7e/7l)

For every fenced ` ```c ` block, open the on-disk source at its cited `path:line` and confirm the block matches verbatim (tab indentation and comments preserved, `...` only for disclosed elisions). Cross-check with the semcode tools, but the on-disk source at the documented version is ground truth. Print the file's lines at the cited range (`sed -n 'START,ENDp'`) beside each block and compare directly, unit by unit for stitched blocks; the excerpt must begin at the cited line, and content matching elsewhere in the file with a wrong claimed line is a finding. Record the count of code blocks and that every one was confirmed against the file. Sign off only when none is left unverified.

#### 3. Every symbol linked, keyword kept (7f)

Scan every inline `` `code` `` span outside fenced blocks. Confirm each kernel symbol is an Elixir link to the correct `path#Lline`, and that types keep the `struct`/`enum` keyword. Spot-read the cited lines on disk. Record any bare span or wrong line found and fixed. Sign off at zero.

#### 4. What-does-what DETAILS headings, journey- or model-first (7/7u)

Read every H3 and H4 under `## DETAILS`. Confirm each is a declarative subject-verb-object sentence, not a bare noun or symbol name, and that the headings together trace a journey (the phases of a process) or lay out a model (the roles, states, or classes of the mechanism), not a per-symbol catalog walked in declaration order (7u). A DETAILS section that is one heading per cataloged symbol in catalog order is the catalog-first failure and is reorganized, every symbol re-homed inside the phase or facet where it acts (coverage is preserved, per item 1). Sign off with the heading count and the spine (journey or model) the headings form.

#### 5. No negative constructions or anthropomorphic verbs (7)

Read the prose. Confirm no `It is X, not Y` constructions, no `lives`/`sits`/`wants` for code, and `walk` used only for traversing a data structure. Grep `[^a-z]not `, ` lives`, ` sits `, ` wants ` for candidates, then judge each in context. Sign off after reading, not after grepping alone.

#### 6. Full coverage and domain model (7j/7s/7t)

For each behavior the page documents, enumerate every site that exhibits it with `find_callers`/`grep` and confirm the page cites all of them, or cites a representative spread and states how many exist. Confirm every hard-coded limit or constant is named with its value, and that the object lifecycle (allocation, initialization, freeing, the serializing locks, reference counting) and the asynchronous behavior are covered. Confirm the page states the domain model of its topic ahead of the DETAILS walkthroughs (7s), either spec-defined and mapped onto the kernel constructs, or a disclosed synthesis that names its on-disk sources and keeps every sub-claim cited, and that every fixed state set, mode set, or part taxonomy appears as a member-meaning-construct semantics table (7t) with a state set's legal transitions shown. Record the enumeration and the model's sources. Sign off.

#### 7. Driver examples actively maintained (7k)

For each driver cited as an example, run `git log` on its file and confirm substantive commits within roughly three years, and that its role is explained from its own source on this page. Record the newest substantive commit per driver. Sign off.

#### 8. ASCII diagrams (7g-7i, 7v)

For each figure, confirm Unicode box-drawing only with no ASCII `\`, `|`, or `/` used as a connector, every line under 80 columns, each content-row `│` landing on a `┬` or `┴` junction of the borders above and below, and that the figure shows a spatial or temporal relationship rather than a function-call chain. Then apply 7v: the figure is none of the four banned shapes (a plain table, a function-flow graph, a listing of struct members, text in a fence), which is checked by stripping every label and reading what the skeleton still asserts. Confirm as well that a prose paragraph sits immediately above the figure's opening fence, so no fenced block opens against another. Sign off per figure, naming the 7h or 7i pattern it follows.

#### 9. Behavioral-claim audit (7o)

List every universal quantifier ("only", "never", "always", "all", "every", "exactly N"), every count, every per-member "each/every X" claim, every restated guard or threshold, and every lifecycle invariant in the page. For each, re-run the enumeration or derivation (record the search performed and its result) and correct the sentence to match; for per-member claims, rebuild the member-to-property mapping and confirm every member, or confirm the stated classifier and its boundary. Confirm every DETAILS heading is true of everything in its section, every behavioral sentence agrees with its adjacent excerpt, and every lead and SUMMARY quantifier agrees with the DETAILS section, table, or enumeration that carries its evidence. Sign off with the claim list and its evidence.

### 3c. Mechanical checks (by hand)

The mechanical layer of the gates is executed with an editor and standard shell tools. There is no checker script to run, maintain, or trust; a script's regexes age into false positives and its passes into false confidence, so the checks below are the procedure itself. Work page by page.

#### 1. Link targets

List every cited location, then open each one and confirm what the link claims:

```
grep -oE 'source/[^)#[:space:]]+#L[0-9]+' page.md | sed 's|source/||; s|#L| |' | sort -u |
while read f l; do echo "== $f:$l"; sed -n "${l}p" "/path/to/tree/$f"; done
```

Judge each printed line: a symbol-name link must land on the symbol's definition line itself (7m), and a file:line location link must land on the exact site the prose describes. When link and code disagree, fix the anchor by re-finding the symbol on disk.

#### 2. Excerpt verbatimness

For every fenced ` ```c ` block, open the provenance file at the cited line and compare unit by unit (an interior `/* path:line */` delimiter starts a new unit; a standalone `...` line marks a declared elision):

```
sed -n 'START,ENDp' path/from/provenance.c
```

Each unit must begin at its cited line and match byte for byte, tabs included. Content that matches elsewhere in the file with a wrong claimed line number is a finding (7l, 7o).

#### 3. Gate A candidates

The patterns below GENERATE CANDIDATES; they are not the gate. Judge EVERY hit against the rule's exemptions and the settled adjudications registry (7r) before touching the page. A hit on an exempt construct is a false candidate, and rewording a compliant phrase to silence a pattern is itself an error: a writer once reworded a correct "32-bit Arm" purely to quiet an arm-word pattern, and that rewording was the only defect introduced. Fix confirmed hits with the 7q recipes.

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

**Rows tagged `[C]` are catalog bullets, list items, and table cells. 7r exempts the LABEL-COLON shape there and nothing else** — so skip label-colon candidates on `[C]` rows and adjudicate every other pattern on them exactly as you would on flowing prose. The em-dash, hedge, cleft, superlative, banned-word, anthropomorphic-verb and negative-construction bans all bind those regions.

An earlier version of this view dropped the four catalog sections outright with a blanket `if cat: continue` justified as "catalog bullets exempt (7r)", which over-applied a shape-specific exemption to every rule at once and left SPECIFICATIONS, LINUX KERNEL, KERNEL DOCUMENTATION and OTHER SOURCES governed by six rules and reached by zero patterns. Two writers on one batch found it independently, each after a defect shipped in SPECIFICATIONS and was caught downstream; building the complement view surfaced a further anthropomorphic verb in KERNEL DOCUMENTATION that no sweep had ever been able to see.

**Do not read this as making label-colons bind in SPECIFICATIONS.** An earlier revision of this paragraph claimed exactly that, reasoning that 7r's catalog carve-out names LINUX KERNEL, KERNEL DOCUMENTATION and OTHER SOURCES but not SPECIFICATIONS. That was wrong, and a writer correctly refused the resulting instruction. 7a does not depend on 7r here at all: its own scope sentence puts **list bullets** outside body prose entirely, whatever section they sit in, and SPECIFICATIONS entries are list bullets. Their colon is also the format `guidelines/passes/01-research.md` mandates (`<spec name>, section <N.N>: <section title>`), so rewording them to silence the pattern would break a format another guideline requires — the compliant-construct defect this file warns about two paragraphs down. Label-colon candidates are skipped on every `[C]` row; the OTHER patterns are what the `[C]` tag exists to let through.

(One inconsistency to be aware of while judging: 7a's scope sentence excludes all list bullets, while its later enumeration of acceptable placements names only LINUX KERNEL and KERNEL DOCUMENTATION catalog entries. The scope sentence governs; the enumeration is the narrower and older gloss.)

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

Adjudicate what that prints against rule 7 (anthropomorphic verbs, em-dashes, negative constructions), and against 7v, whose four banned shapes no grep can express and which is therefore judged by reading each figure and stripping its labels. Two exemptions apply and are the common case: a ` ```c ` block is a source excerpt and is never swept (the filter above already excludes it), and a fenced block reproducing a VERBATIM quotation — a commit message, a kernel comment — is exempt like any other verbatim text (7r). What is left is figure annotation the page itself authored, and it is bound.

What no pattern can express stays a read-through: 7b prose-list shapes, 7d superlatives judged in context, heading truth (Gate B item 4, 7o), definition-plus-usage parity (Gate B item 1, 3b), coverage (item 6), figure geometry and the 7v banned shapes (item 8), and the whole 7o behavioral-claim audit. Every finding is fixed or recorded as a 7r adjudication with reasoning, never silenced.

#### Blind spots

**A grep is a candidate generator, never the gate.** FOUR classes have now shipped behind a pattern that structurally could not see them: the mid-paragraph label-colon behind a `^`-anchored grep; the figure annotation behind a fence-stripping view; the heading behind a prose view that dropped every `#` line, even though rule 7, 7d and 7o all bind headings; and the whole catalog region behind a blanket `if cat: continue` that generalized one shape-specific 7r exemption into a total blind spot. Two further near-misses came from the pattern rather than the region: a case-sensitive sweep cannot see a sentence-initial `What matters`, and `\b` treats `_` as a word character, so `\bnec\b` cannot see `TRB_NEC_GET_FW`. Each time, the check ran clean and the clean run meant nothing.

So the discipline is not "write better patterns", it is: **when a rule binds a region, confirm some mechanism actually reaches that region.** Enumerate the page's regions — prose, headings, figures, catalog bullets, table cells, fenced excerpts — and for each rule, name the pattern that can fire there. A region no pattern reaches is not clean; it is unexamined, and it reads exactly like clean.

The same trap has a second form, found the same way: **a permissive checker is worse than no checker.** A writer's excerpt verifier resynchronized on any mismatch and reported 44 of 44 units correct while two fabricated comment terminators sat in the page. It was tightened to resync only after a declared elision, and both fabrications surfaced immediately. A check that cannot fail is not a check.
