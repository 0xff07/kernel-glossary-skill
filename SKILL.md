---
name: kernel-glossary-skill
description: >
  Generate structured Linux kernel reports for this knowledge base.
user-invocable: true
---

# kernel-glossary-skill

Generate a Linux kernel reports following this project's conventions.

## Project Overview

This is a documentation knowledge base covering Linux kernel subsystems, hardware architecture, and driver development. It is built with MkDocs (Material theme) and consists of Markdown articles organized by subsystem.

Content structure:

- `docs/` — all documentation articles
- `docs/templates/TEMPLATE-FULL.md` — full page template with all sections
- `docs/samples/` — the golden-standard reference pages for writing. This directory holds frozen copies of exemplar pages (plus one labelled counterexample) kept independent of the live subsystem directories, so the exemplars stay findable even after the hierarchy under `docs/` is reorganized. The worked examples here define the house standard for the lead summary, section structure, prose, ASCII diagrams, self-contained kernel-source citation, and depth of coverage. When writing any new page, calibrate against the closest-matching page under `docs/samples/`, and refer to example pages only by their `docs/samples/` path.
- `scripts/verify_page.py` — the advisory machine verifier that checks a finished page's Elixir links, code-block verbatimness, and banned prose patterns against the local kernel tree. Its findings are leads, never verdicts; the manual gates in section 9 are the authority and work without it (see "Machine verification (advisory)" near the end of this file)
- Major subsystem directories under `docs/`: one per entry in the Subsystem Map at the end of this file (the `dir` field of each entry)

## Input

`$ARGUMENTS` or conversation context provides:
- The subsystem (e.g., xHCI, PCIe, ACPI, USB4, DRM)
- The topic name (e.g., "host controller initialization", "MSI-X vectors")
- Optionally, an output directory override

If `$ARGUMENTS` is empty, derive the subsystem and topic from the conversation context.

## Procedure

### 1. Read the template and the golden samples

Before generating any content, read `docs/templates/TEMPLATE-FULL.md` (relative to `${CLAUDE_SKILL_DIR}`) for the page structure and section order.

Then read the golden samples under `${CLAUDE_SKILL_DIR}/docs/samples/`. These are frozen copies of real pages that met every gate in this file and passed the machine verifier with zero findings; they are the concrete standard for structure, prose, diagram style, code-citation density, and depth of coverage. Open the one or two whose archetype most resembles the page about to be written and read them in full before writing:

- structure-tour pages (one central struct documented field group by field group, with its accessor and lifecycle catalog): `docs/samples/golden-overview-mm-struct.md`
- lifecycle / refcount / locking-protocol pages: `docs/samples/golden-lifecycle-mm-refcount.md` (also the smallest acceptable depth for a fine-grained page)
- encoding / bitfield / flag-layout pages (including register-figure style): `docs/samples/golden-encoding-pgtable-entries.md`
- pages rebuilt from earlier drafts: `docs/samples/golden-enhanced-vma-overview.md`, read side by side with the counterexample below
- `docs/samples/draft-original-vma-overview.md` is a COUNTEREXAMPLE, the stale draft the enhanced page was rebuilt from. Do not imitate it. It is kept so the measurable difference between a plausible draft and a page meeting this standard stays visible (see "Draft-versus-golden contrast" near the end of this file).

If no archetype matches, pick the structurally closest golden sample anyway. Do not calibrate against pages elsewhere under `docs/`; they may predate the current rules. Where a sample and a rule in this file disagree (a sample can predate a later rule), the rules in this file govern; samples are calibration, not license.

### 2. Determine subsystem and output path

Look up the subsystem in the Subsystem Map (at the end of this file) to find:

- `tag`: the subsystem tag, used when composing the commit message for the page
- `dir`: the output directory under `docs/`
- `kernel_paths`: directories in the kernel source tree to search first
- `spec`: specification name(s) for the SPECIFICATIONS section
- `section6_heading`: the heading to use for section 6 (REGISTERS, METHODS, PRIMITIVES, INTERFACES, or omit)

Construct the output path: `${CLAUDE_SKILL_DIR}/docs/<dir>/<topic-slug>.md`

If the output directory does not exist, create it.

### 3. Search local kernel source code

Search the local kernel source tree (not the web) for relevant code.

If the semcode MCP tools are available (e.g., `find_function`, `find_type`, `grep_functions`), prefer them as the primary search method:

- `find_function` to locate functions and macros by name or regex (returns file path and line number)
- `find_type` to locate structs, enums, and typedefs by name or regex
- `find_callers` / `find_calls` to understand direct call relationships
- `find_callchain` to trace multi-level call chains (useful for the DETAILS section)
- `grep_functions` to search inside function bodies for keywords or spec references
- `find_commit` with `symbol_patterns` or `path_patterns` to find commits that introduced or modified key symbols (commit messages often cite spec sections)
- `dig` on relevant commits to find lore.kernel.org mailing list discussion (useful for OTHER SOURCES and SPECIFICATIONS)
- Fall back to Grep and Glob for things semcode does not cover: standalone macros in headers, `Documentation/` files, Kconfig entries, and non-function code

If semcode tools are not available (e.g., the MCP server is not running), fall back entirely to Grep and Glob:

- Source files in `kernel_paths` relevant to the topic
- Function definitions (with line numbers) using patterns like `^(static\s+)?\w+.*\bfunction_name\b\s*\(`
- Struct and macro definitions
- Comments referencing specification sections
- Files under `Documentation/` related to the topic

Record exact file paths and line numbers for every function, struct, or macro found.

### 4. Construct Elixir cross referencer URLs

Use the base URL: `https://elixir.bootlin.com/linux/v7.0/source/`

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

Which line a link anchors at, and which symbol occurrences must be linked, is governed by rule 7m (definition-line anchoring, file-location links for call sites, and the exhaustive span-linking pass).

### 5. Identify specifications

Check source code comments and headers for references to specification chapters and sections. Map the subsystem to its known specifications using the `spec` field from the Subsystem Map.

If semcode tools are available, supplement source code comments with:

- `find_commit` with `symbol_patterns` for key functions/types: commit messages frequently cite spec sections
- `dig` on the commits that introduced the relevant code: the associated mailing list threads often reference specific spec chapters and provide review discussion suitable for OTHER SOURCES
- `grep_functions` with patterns like `section|chapter|spec|table` to find spec references embedded in function bodies or comments

Format each entry as: `<spec name>, section <N.N>: <section title>`

If no specification applies, leave the SPECIFICATIONS section present but empty.

### 5b. Find usage examples for LINUX KERNEL symbols

For every function, struct, macro, or enum listed in the LINUX KERNEL section, search for at least one concrete usage example in the kernel source before writing the DETAILS section. These examples show where and how the symbol is actually used in practice.

If semcode MCP tools are available:

- `find_callers` to find functions that call a given function or macro
- `find_callchain` to trace how a function fits into a larger call sequence
- `grep_functions` to find code that references a struct, enum, or macro inside function bodies

If semcode is not available, use Grep to search for usages:

- For functions: search for call sites (e.g., `\bfunction_name\(`)
- For structs: search for variable declarations or field accesses (e.g., `struct struct_name` or `->field_name`)
- For macros: search for invocations (e.g., `\bMACRO_NAME\(` or `\bMACRO_NAME\b`)
- For enums: search for usage of enum values

Record the caller/user function name, file path, and line number for each example found.

When writing the DETAILS section, incorporate these usage examples to show the symbol in context. For example, if `acpi_ev_gpe_dispatch` is listed in LINUX KERNEL, the DETAILS section should show where it is called from (called by `acpi_ev_detect_gpe` at SCI time), what arguments it receives, and what it does with the structs and macros also listed in LINUX KERNEL.

### 6. Generate the page

Follow the template structure exactly. The page must contain these sections in order:

1. H1: the topic name (just the name, no extra text)
2. The AI-generated-content caution blockquote, immediately below the H1
3. A short summary paragraph with an ASCII diagram if appropriate
4. `## SUMMARY`
5. `## SPECIFICATIONS`
6. `## LINUX KERNEL`
7. `## KERNEL DOCUMENTATION`
8. `## OTHER SOURCES`
9. `## <section6_heading>` (from Subsystem Map; omit entirely if set to "none")
10. `## DETAILS`

### 7. Writing rules (mandatory)

The golden samples under `docs/samples/` embody every rule in this section. The closest-matching sample you read in step 1 is your worked example; match its structure, diagram style, code-citation density, and depth. The examples in the rules below use ACPI and mm symbols; they illustrate the rule mechanic, which applies unchanged to every subsystem. All generated content must follow these rules:

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

The H3 catalog lists in LINUX KERNEL (grouped by file or functional area as the golden samples do, for example `EC_SC status bit macros`, `Port accessors`, `Transaction state machine`) and the bullet lists in KERNEL DOCUMENTATION and OTHER SOURCES are reference catalogs and remain as lists. Tables remain as tables. This rule applies only to prose-explanation lists, not to reference catalogs.

### 7c. Forbidden phrases checklist

Before writing any body paragraph, scan for these patterns and rewrite if any appear:

- `^.*: [a-z]` (any line where prose ends in `: ` followed by a lowercase clause)
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

### 7g. General ASCII diagram principles (mandatory)

Only include an ASCII diagram when it conveys a spatial or temporal relationship that prose cannot express efficiently. A diagram earns its place when it shows physical layout, parallel structure across multiple lanes, a non-linear graph, an address space, a bit field, a ring/queue with head and tail pointers, or two views of the same data side by side. Concrete examples that justify a diagram include the GPE register block mapped to its per-bit event_info slots, the buddy allocator's per-order freelist columns, a doorbell BAR partitioned across IPs, or a tree of devices with parent/child arrows.

Do not draw a diagram for a simple linear sequence of function calls, a top-down call chain, a state machine with two states, or any flow that reads naturally as a paragraph or as a fenced code block of pseudocode. "Function A calls B which calls C" is prose, not a diagram. A single arrow chain in a box is not a diagram. If a reader would understand the same content faster from one sentence of declarative prose, write the sentence and delete the diagram.

When a diagram is used, follow the style established in the golden samples (for example the page-table-entry bit layouts and slot-map figures in `docs/samples/golden-encoding-pgtable-entries.md`) and the reference figures in 7h and 7i. Use Unicode box-drawing characters (`┌ ┐ └ ┘ │ ─ ├ ┤ ┬ ┴ ┼`) and `▼ ▲ ◀ ▶` for arrows. Title each sub-diagram with a short heading underlined by a `────` rule. Multiple sub-diagrams may share one fenced block when each has its own titled section. Indent the whole figure 4 spaces inside the fenced block so it reads as a figure, not as text. Keep every line under 80 columns so the figure renders without wrapping in plain-text views.

Pure ASCII `\`, `/`, and `|` are never used as box-drawing or connector characters. The `/` and `|` characters are acceptable inside the figure only as English word separators ("ROOT_PORT / DOWNSTREAM"), as C bitwise expressions (`LBMS | LABS`), or inside reproduced kernel source. All box sides, corners, junctions, and arrows are Unicode.

Diagram annotations (legends, per-bit meanings, code-like pseudocode lines, comments below the figure) live inside the same fenced block as the figure. The forbidden-phrase rules from 7a/7c/7d do not apply to text inside fenced code blocks, including ASCII figure blocks, but the prose surrounding the figure outside the fence still does.

### 7h. Register and bitfield figures (mandatory)

A figure that plots a register, a bitfield, a TRB, a context, a packet header, or another bit-field structure follows the rules and reference figures in this section, on top of the general diagram rules in 7g. It is drawn in one of two named styles, the DWORD-grid style and the L-connector style, chosen by the register-versus-structure test below.

Two things decide how to label the bits, and the two resulting styles have names used throughout this skill. The DWORD-grid style writes each field name inside its cell and stacks the DWORDs as `DW0`, `DW1`, ... rows; the L-connector style draws a single row of one-character cells and calls out each bit's name below on an L-shaped leader.

A register is one value at one address; if it is wider than a DWORD the split is only display width, and all its bits are one field set. A structure is several separate words at successive DWORD offsets, each its own named unit. Quick test: is the thing one value, or several separate words? A register is one value (even a 64-bit register is a single 64-bit number), so all its bits sit on one ruler; a structure is several separate words, so each keeps its own row. Registers include EC_SC, the PCI Command and Status words, a USB4 ADP_CS_x register, a 64-bit MSI address, and an encoded-pointer-plus-flags word; structures include an xHCI TRB, a context, a descriptor, and a TLP or TCP header.

The L-connector style is for registers only. Reach for it when a register is mostly single-bit fields whose names will not fit inside one-character cells: give each bit a one-character cell, then run a dashed L-connector from each named bit's column out to its constant, stacking the labels so each elbow lands on its own trunk (reserved bits get no trunk), with a legend mapping each cell to its constant and value. A register drawn this way is a single row of all its bits, whatever its width — a 64-bit register is one wide row, not two stacked DWORDs. When the upper bits of a wide register are a single uniform field (an encoded pointer above its low flags), you may instead draw just the DWORD that carries the interesting fields and note that the upper bits continue that field.

The DWORD-grid style is for everything else: a structure, or a register whose field names fit in the cells. Keep the names inside the cells and stack the DWORDs as `DW0`, `DW1`, ... rows; the L-connector style does not apply to structures.

This governs a figure whose primary subject is the bit-layout. A bit-strip that is one element of a larger structural figure (a flag nibble inside a struct box, a bitmap strip in a pointer-topology diagram) follows the host figure's style, not the register rules here.

Rules:

- Header rows give the bit index from the high bit down to 0, one bit per two-column slot. Use two rows (a tens-digit row, then a ones-digit row) whenever any index reaches two digits, and one row when every index is a single digit (a byte, or any field set within bits 0 to 9). Reuse the exact ruler and the full per-bit `┌─┬...─┐` top border so every cell stays aligned.
- Stack the dwords as rows, each labelled `DW0`, `DW1`, ... in a left gutter (the label sits at column 4 and the box left border at column 10). Use `├──┬──┼──┴──┤` divider rows to transition between the differing field layouts of one dword and the next.
- Each field cell carries the field name, and on a second line for a multi-bit field its `(hi:lo)` bit range, centred in the cell. A single-bit field uses a one-character cell (for example `E` or `R`); when many single-bit fields crowd one register, label each with an L-connector beneath the figure instead (see the single-bit-field example below).
- Box-drawing is Unicode only (`┌ ┐ └ ┘ │ ─ ├ ┤ ┬ ┴ ┼`). Never use ASCII `\`, `/`, or `|` as connectors. Keep every line under 80 columns, except a register drawn as a single row with L-connectors, which may run wider when its bit count requires it (a 64-bit register is roughly 130 columns).
- Add a legend beneath the figure mapping each field to its kernel macro and, where relevant, the cached struct field, as `NAME = MACRO (meaning)`.
- Verify before saving: every content-row `│` lands on a `┬` or `┴` junction of the border rows above and below it.

For a register that is a single dword, draw just the ruler, the `┌─┬...─┐` top border, one `DW0` content row (field names plus `(hi:lo)` ranges), and the bottom border, then the legend. Use the two-row numbered ruler whenever any bit index reaches two digits; a register whose highest bit index is a single digit may use one header row, as the figure below does.

Draw a figure to scale by default: a complete per-bit numbered ruler, cells in proportion to their bit width, every `(hi:lo)` an exact number. Draw to scale whenever every boundary is a fixed number, because the ruler pins each bit and a reader reads positions straight off it.

When a boundary is not a fixed number — it varies by implementation or mode (the x86-64 PTE address field that ends at MAXPHYADDR), or the figure is a generic pattern where exact positions would be fake precision — draw it schematic instead. Label only the boundaries that matter (the high bit, each variable boundary by name such as `N` or `M`, and the low fixed bits), join the gaps with `...`, and size each cell for its label rather than to scale. Schematic trades exact-position readability for the ability to show a boundary that has no fixed value, so use it only as the fallback. This choice is independent of DWORD-grid versus L-connector: either style can be drawn either way (the PTE figure below is a schematic DWORD-grid register, and the worked example shows the same packed register both to scale and schematic).

Reference figure (a structure, drawn as stacked DWORDs — the DWORD-grid style):

```
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │       device_id (31:16)       │       vendor_id (15:0)        │
          ├───────────────┬─┬─────┬───────┴───┬───────────┬───────────────┤
    DW1   │   revision    │R│depth│ max_port  │ upstream  │  cap_offset   │
          │    (31:24)    │ │22:20│  (19:14)  │  (13:8)   │     (7:0)     │
          ├───────────────┴─┴─────┴───────────┴───────────┴───────────────┤
    DW2   │                       route_lo (31:0)                         │
          ├─┬─────────────────────────────────────────────────────────────┤
    DW3   │E│                      route_hi (30:0)                        │
          ├─┴─────────────┬───────────────┬───────────────┬───────────────┤
    DW4   │  tb_version   │   __unknown4  │     cmuv      │ plug_ev_delay │
          │    (31:24)    │    (23:16)    │    (15:8)     │     (7:0)     │
          └───────────────┴───────────────┴───────────────┴───────────────┘
```

Reference figure (a register of many single-bit fields — the L-connector style):

```
    bit    7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │·│M│S│B│C│·│I│O│
          └─┴─┴─┴─┴─┴─┴─┴─┘
             │ │ │ │   │ │
    SMI_EVT ─┘ │ │ │   │ │
    SCI_EVT ───┘ │ │   │ │
      BURST ─────┘ │   │ │
        CMD ───────┘   │ │
        IBF ───────────┘ │
        OBF ─────────────┘

    OBF = ACPI_EC_FLAG_OBF (0x01)      IBF = ACPI_EC_FLAG_IBF (0x02)
    CMD = ACPI_EC_FLAG_CMD (0x08)      BURST = ACPI_EC_FLAG_BURST (0x10)
    SCI_EVT = ACPI_EC_FLAG_SCI (0x20)  SMI_EVT = 0x40 (firmware, no macro)
    bits 2 and 7 reserved (read 0)
```

Reference figure (a DWORD-grid register, schematic — the address field ends at the variable MAXPHYADDR):

```
    x86-64 4-KByte-page table entry (PTE)
    ─────────────────────────────────────────
    (schematic; M = MAXPHYADDR, the boundary varies by CPU)

     63   62           52 51          M M-1              12 11          0
    ┌────┬───────────────┬─────────────┬───────────────────┬─────────────┐
    │ XD │  ignored/MPK  │  reserved   │ physical address  │    flags    │
    │(63)│    (62:52)    │  (51:M, 0)  │     (M-1:12)      │   (11:0)    │
    └────┴───────────────┴─────────────┴───────────────────┴─────────────┘

    M = MAXPHYADDR (physical-address width: 36, 39, 46, or 52)
    flags (8:0): P(0) R/W(1) U/S(2) PWT(3) PCD(4) A(5) D(6) PAT(7) G(8)
    available (11:9): AVL;  reserved bits (51:M) are 0
    the address field high bit moves with M
```

#### Worked example: compound packed field (encoded pointer with status flags)

Use when a single struct field is a packed `unsigned long` (or similar word) that combines an encoded pointer to another struct with multiple status flag bits in the low bits, and the page needs to show both halves at once with the decode formula visible. This is common when the kernel reuses alignment-guaranteed low bits of a pointer to encode metadata; the figure shows the bit positions, the per-bit flag constants, and the formula that extracts the embedded pointer.

Draw it in the L-connector style: a single row of the register's bits under the per-bit numbered ruler and a full per-bit `┌─┬...─┐` top border. The encoded pointer and any intermediate field (NID, type) are range cells carrying a name and `(hi:lo)` range; each status flag in the low bits is a one-character cell (`D`, `C`, `B`, `A`) named by an L-connector below. Because the upper bits of this 64-bit register are all pointer, draw just the low dword and note in the heading that the upper bits continue the pointer, rather than a 130-column full row. The total width of the top border, content row, and bottom border must match, and every content-row `│` lands on a `┬`/`┴` junction.

Below the bottom border, drop a vertical trunk (`│`) from each flag bit's column (under its `D`, `C`, `B`, `A` cell). Connect each trunk to its constant name with an L-shaped corner (`────┘`); the constant labels stack as a left-aligned column on the left and the dashes lengthen from line to line so each elbow lands on its trunk. The leftmost (highest-numbered) flag's trunk gets the shortest dashed line; the rightmost (lowest-numbered) flag's trunk gets the longest.

Close the figure with a multi-line pseudocode block showing the decode formula (`Pointer = field & FIELD_PTR_MASK`, `= real_pointer - base_index(slot)`) and a parenthetical note explaining any bias or invariant.

Use the L-connector style when the flag constants are too long to sit inside one-character cells several across, as here; the connectors keep each flag one bit wide while still naming it, and leave room for the decode formula beneath. Reach for this pattern when the packed field is the entry point into another struct (pointer encoding), where the decode formula matters, not when the field is a plain status register.

```
    struct outer_t.packed_field (encoded pointer + status flags)
    ────────────────────────────────────────────────────────────
    (illustrative; bits 63:32 continue the pointer, low dword shown)

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │          encoded pointer (31:10)          │ NID (9:4) │D│C│B│A│
          └───────────────────────────────────────────┴───────────┴─┴─┴─┴─┘
                                                                   │ │ │ │
                             FLAG_NAME_D ──────────────────────────┘ │ │ │
                             FLAG_NAME_C ────────────────────────────┘ │ │
                             FLAG_NAME_B ──────────────────────────────┘ │
                             FLAG_NAME_A ────────────────────────────────┘

    Pointer = packed_field & FIELD_PTR_MASK   (mask = bits 63:10)
            = real_pointer - base_index(slot)
    (biased so that pointer + idx yields the correct struct target)
```

The figure above is drawn to scale, with concrete bit boundaries. This pattern is a generic illustration, though, so the boundary between the pointer and the flags is not really a fixed bit. When the boundaries are generic or vary (by implementation or mode), draw it schematic instead: name the variable boundary `N`, elide the middle with `...`, and size cells for their labels rather than to scale, as the to-scale-versus-schematic policy above describes. The schematic version of the same figure:

```
    struct outer_t.packed_field (encoded pointer + status flags)
    ────────────────────────────────────────────────────────────
    (schematic; the pointer occupies bits 63:N, and N varies)

     63                                N      ...   3   2   1   0
    ┌─────────────────────────────────┬─────┬─────┬───┬───┬───┬───┐
    │ encoded struct target * pointer │ NID │ ... │ D │ C │ B │ A │
    └─────────────────────────────────┴─────┴─────┴───┴───┴───┴───┘
                                                    │   │   │   │
                                  FLAG_NAME_D ──────┘   │   │   │
                                  FLAG_NAME_C ──────────┘   │   │
                                  FLAG_NAME_B ──────────────┘   │
                                  FLAG_NAME_A ──────────────────┘

    Pointer = packed_field & FIELD_PTR_MASK   (mask = bits 63:N)
            = real_pointer - base_index(slot)
    (biased so that pointer + idx yields the correct struct target)
```

### 7i. Other ASCII diagram patterns

When a diagram is justified, prefer one of the named patterns below. Each pattern has a use case and a shape; copying the shape and substituting names is usually enough to produce a clean figure. Reach for a new shape only when none of these fits the spatial relationship in question.

#### Pattern: parent + N children fan-out

Use when one parent object spawns multiple typed child objects on a different bus / queue / map / list, and the children's identity comes from a field inside the parent. Draw the parent as a wide top box with field-level content, then N children in a row underneath, joined by a single trunk that splits into N branches.

```
       struct parent (on bus_A)
       ┌──────────────────────────────────────────────────────────┐
       │  field_1  ...                                            │
       │  field_N  ...                                            │
       └──────────────────────────┬───────────────────────────────┘
                                  │ allocation / registration
              ┌──────────┬────────┼────────┬──────────┐
              ▼          ▼        ▼        ▼          ▼
         ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
         │ child0 │ │ child1 │ │ child2 │ │ child3 │ │ child4 │
         └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

#### Pattern: sparse slot map with conditional backing

Use when an address space, slot table, or fixed-size index set is divided into uniformly-sized regions and each region may or may not have a backing data structure allocated for it. The figure shows which regions are present (have backing) and which are holes (no backing), with the lookup formulas below. Reach for it when the page needs to convey that the lookup is a direct dereference but the backing array is sparse and only allocated for populated slots.

Draw the slot row as a contiguous strip of N cells joined by `┬` dividers (no gaps between cells, since the slots are contiguous in the index space). Each cell contains a short status word (`present`, `hole`, `valid`, etc.). The bottom border has `┬` connectors only beneath populated slots (the ones that will descend to a backing box). For each populated slot, drop a `▼` arrow from the bottom of the strip to a backing object box drawn directly below; leave the hole slots with no arrow and no box below. Add accessor labels beneath each backing box (the name and field expression by which code reaches that backing object), connected by `▲` arrows pointing up into the backing box. Labels span multiple lines if the field path is long.

Close the figure with a one-line parenthetical noting which slots are skipped, then one or more formula blocks showing the lookup formula for each conversion mode (direct lookup, flat lookup, etc.). Each formula block has a short heading followed by indented pseudocode lines.

This pattern differs from `parent + N children fan-out` (one parent allocating all N children via a single trunk) and from `N-to-M source/destination mapping` (disjoint inputs feeding rows of a tabular destination): here a single uniform index space partitions into independent slots, each independently populated or absent.

```
       Sparse slot map (possibly with holes)
       ─────────────────────────────────────

       Slot 0        Slot 1        Slot 2        Slot 3
       ┌─────────────┬─────────────┬─────────────┬─────────────┐
       │   present   │    hole     │   present   │   present   │
       └──────┬──────┴─────────────┴──────┬──────┴──────┬──────┘
              │                           │             │
              ▼                           ▼             ▼
        ┌───────────┐               ┌───────────┐ ┌───────────┐
        │  backing  │               │  backing  │ │  backing  │
        │  object   │               │  object   │ │  object   │
        └───────────┘               └───────────┘ └───────────┘
              ▲                           ▲             ▲
              │                           │             │
        table[0]                    table[2]      table[3]
        .ptr                        .ptr          .ptr

       (Slot 1 has no backing object; the hole is skipped)

       Direct lookup:
         lookup(idx) = table[idx].ptr + intra_slot_offset

       Flat lookup:
         lookup(idx) = base + idx
         (base is a virtually contiguous array; only populated slots are mapped)
```

#### Pattern: truth table (input bits → output)

Use when a function's return value or the chosen branch is a deterministic function of a small number of input bits. Lay out the inputs as boxed columns on the left and the action / return on the right; one row per distinct input pattern. The handler's sequential flow (read, clear, return) lives in prose outside the diagram, not as additional arrows inside it.

```
       input_a   input_b   result
       ┌───────┬─────────┬───────────────────┐
       │  0    │   X     │ OUTCOME_NONE      │
       │  1    │   0     │ OUTCOME_HANDLED   │
       │  1    │   1     │ OUTCOME_WAKE ──▶  followup_handler
       └───────┴─────────┴───────────────────┘
```

#### Pattern: boxed flowchart with decision nodes

Use when a function has 3+ sequential decision points with side effects and back-edges, and showing each step in its own box adds clarity. Each step gets its own box; each decision node has explicit yes / no labels on outgoing edges; loops draw an explicit back-edge with an arrow. Reserve this for paths with real branching; a 2-state decision should be written as prose instead.

```
       ┌─────────────────┐
       │ acquire lock    │
       └────────┬────────┘
                │
       ┌────────▼────────┐    yes
       │ early-exit cond?│──────────▶  break
       └────────┬────────┘
                │ no
                ▼
       ┌─────────────────┐
       │ read register   │
       └────────┬────────┘
                │
       ┌────────▼────────┐    yes ┌──────────────┐
       │ event present?  │──────▶ │ handle event,│
       └────────┬────────┘        │ continue ────┼── back-edge to top
                │ no              └──────────────┘
                ▼
              break

       break ─▶ release lock, return
```

#### Pattern: side-by-side struct comparison

Use when two related types interact via a third operation (match function, encode / decode pair, pack / unpack helpers). Show both struct definitions as boxes side by side with the operation drawn underneath as the convergence point.

```
       struct lhs                     struct rhs
       ┌─────────────────┐            ┌─────────────────┐
       │ field_x         │            │ field_x         │
       │ field_y         │            │ field_y         │
       │ ...             │            │ ...             │
       └────────┬────────┘            └────────┬────────┘
                │                              │
                └────────► matcher / op ◀──────┘
                                │
                                ▼
                       returns match iff
                         lhs.field_x == rhs.field_x
                         AND (rhs.field_y == ANY || ...)
```

#### Pattern: linked structs via field-level pointers

Use when several related structs and arrays connect via pointer fields, encoded pointers, or per-cell bitmap pointers, and the relationship between them is the field-level pointer topology itself. Each struct is drawn as a labeled box: the struct name (with `struct` keyword) sits on a borderless heading line above the box, and field names are listed inside the box one per line with optional type or comment in parentheses. Fields with internal structure (bit-packed words, embedded arrays, fixed bitmaps) get drawn as nested cell strips inside the outer box.

Pointer fields exit the bottom border of the box (via `┼` or `─┐`), descend as vertical trunks (`│`), and terminate in a `▼` arrow that lands on the target box below. When a nested bitmap has per-cell pointing relationships (one bit per subsection, one entry per slot), each cell descends via its own vertical trunk and `▼` to its target in a parallel array drawn underneath. Length-bracket annotations of the form `|<── span ──>|` mark total spans beneath arrays. Close the figure with a legend block beneath the diagram listing flag and constant meanings as `NAME = MEANING` columns.

This pattern differs from `parent + N children fan-out` (which shows allocation or registration of typed children) and from `side-by-side struct comparison` (which shows two peer structs meeting at one operation): here the structs already exist and the visible shape of the figure is the chain of pointer fields linking them together.

```
       Linked struct hierarchy
       ───────────────────────

       struct outer_t
       ┌──────────────────────────────────────────────────────────┐
       │  packed_field  (unsigned long, encoded)                  │
       │  ┌──────────────────────────────────┬───┬───┬───┬───┐    │
       │  │   encoded target * pointer       │ D │ C │ B │ A │    │
       │  └──────────────────┬───────────────┴───┴───┴───┴───┘    │
       │                     │                                    │
       │  link ──┐           │  (biased: pointer + idx = target)  │
       │         │           │                                    │
       │  optional_field  (only with CONFIG_OPTIONAL)             │
       └─────────┼───────────┼────────────────────────────────────┘
                 │           │
                 │           ▼
                 │      struct target_t[N]
                 │      ┌────┬────┬────┬────┬─────┬─────┐
                 │      │ t0 │ t1 │ t2 │ t3 │ ... │tN-1 │
                 │      └────┴────┴────┴────┴─────┴─────┘
                 │      |<── one entry per index in outer ──>|
                 │
                 ▼
       struct linked_t
       ┌──────────────────────────────────────────────────────────┐
       │  preamble                                                │
       │                                                          │
       │  bitmap[BITS_TO_LONGS(N_CELLS)]                          │
       │       bit:   0    1    2    3    4   ...   N-1           │
       │       ┌────┬────┬────┬────┬────┬─────┬────┐              │
       │       │ 1  │ 0  │ 1  │ 1  │ 0  │ ... │ 1  │              │
       │       └─┬──┴─┬──┴─┬──┴─┬──┴─┬──┴─────┴─┬──┘              │
       │         │    │    │    │    │          │                 │
       │  trailer  (variable-length, computed by helper)          │
       └─────────┼────┼────┼────┼────┼──────────┼─────────────────┘
                 │    │    │    │    │          │
                 ▼    ▼    ▼    ▼    ▼          ▼
                 ┌────┬────┬────┬────┬────┬────┬─────┐
                 │ U0 │ U1 │ U2 │ U3 │ U4 │ ...│UN-1 │  fixed-size units
                 └────┴────┴────┴────┴────┴────┴─────┘  one bit per unit
                 |<──── total span of one linked_t ──────────>|

       Flag bits in packed_field (low bits):
         A = FLAG_NAME_A  (bit 0, marker)
         B = FLAG_NAME_B  (bit 1, has-pointer)
         C = FLAG_NAME_C  (bit 2, online)
         D = FLAG_NAME_D  (bit 3, early-init)
```

#### Pattern: N-to-M source/destination mapping

Use when several disjoint inputs feed a single tabular destination, with some inputs feeding multiple rows of the destination. Sources go in a column on the left; the destination is a stacked box on the right; arrows cross the gap. Annotation that would otherwise hang off the right edge of the destination box belongs as prose below the figure, not as right-aligned brackets, so the figure stays under 80 columns.

```
       Source register              Destination slots
       ───────────────              ─────────────────

       SRC_FIELD_A                  ┌─────────────────────┐
         file path / spec § ──▶     │ slot[0] = result_A  │
                                    │ slot[2] = result_A  │
                                    │ slot[4] = result_A  │
                                    ├─────────────────────┤
       SRC_FIELD_B          ──▶     │ slot[1] = result_B  │
         file path / spec §         ├─────────────────────┤
       SRC_FIELD_C          ──▶     │ slot[3] = result_C  │
         file path / spec §         └─────────────────────┘
```

#### Pattern: queue / ring between two stages

Use when a producer and a consumer communicate through a bounded buffer (kfifo, work_struct, list_head ring). Show the buffer as a row of cells in the middle; the two stages flank it; arrows label the put / get operations.

```
       Producer side              kfifo / work / ring         Consumer side
       ┌──────────────────┐       ┌──┬──┬──┬─────┬───┐        ┌──────────────┐
       │ Stage A reads    │       │e0│e1│e2│ ... │e_n│        │ Stage B      │
       │ source, RW1C     │  put  └──┴──┴──┴─────┴───┘  get   │ dequeues,    │
       │ clear, enqueue   │ ──▶      ▲              │   ──▶   │ processes    │
       │ ... return       │          │              └──────▶  │ ... return   │
       │ IRQ_WAKE_THREAD  │          │                        │ IRQ_HANDLED  │
       └──────────────────┘          │                        └──────────────┘
```

The remaining patterns are each shown with an example figure; copy the shape and relabel it for the subsystem at hand.

#### Pattern: data dependency (inputs feed a transform)

Use when one or more source structs are read by a function that builds or populates a destination struct, and the point is which inputs feed which output (assembling a config, intersecting capabilities, encoding a message). Draw the input struct boxes at the top, the transform function as the labelled junction beneath them, and the produced struct below; the arrows mean feeds / populates / points-to, never call order. The figure is a valid data-dependency picture only because its endpoints are structs: a figure whose nodes are all functions joined by call arrows is the banned code-flow chart. Complements the linked-structs-via-pointers pattern, which shows structs already wired by their fields.

```
       snd_soc_runtime_calc_hw: intersect every CPU and codec DAI
       ──────────────────────────────────────────────────────────

       each CPU DAI stream        each codec DAI stream
       ┌────────────────────┐     ┌────────────────────┐
       │ rate_min..rate_max │     │ rate_min..rate_max │
       │ channels_min..max  │     │ channels_min..max  │
       │ formats mask       │     │ formats mask       │
       └──────────┬─────────┘     └─────────┬──────────┘
                  │  for_each_rtd_cpu_dais  │  for_each_rtd_codec_dais
                  └───────────┬─────────────┘
                              ▼  raise min, lower max, AND the formats
                 ┌──────────────────────────────────┐
                 │ substream->runtime->hw           │
                 │  rates  channels_min..max        │
                 │  formats   (&= starting formats) │
                 └────────────────┬─────────────────┘
                                  ▼  soc_hw_sanity_check
                 !rates  /  !formats  /  empty channels
                          ─▶ -EINVAL  "No matching ..."
```

#### Pattern: signal-timing / waveform

Use when the point is where a data bit or sample lands in time relative to a clock or frame edge (a serial-bus frame, a strobe, a sampling instant). Draw each wire as a square-wave trace built from ─ levels and ┌ ┐ └ ┘ │ edges, one trace per line, with a vertical reference column (▼ and │) marking the frame edge so the offset reads straight off the grid; align the data cells under a per-cell clock tick.

```
       I2S vs left-justified: where the left-channel MSB sits
       ────────────────────────────────────────────────────────
       (▼ = tick 0, the WS falling edge that opens the left slot;
        each data cell is one BCLK period)

                     ▼
       WS    ────────┐
                     └────────────────────────────────

       I2S   ─────────────┌────┬────┬────┬────┐    MSB starts one
       SD            ·····│MSB │ b14│ b13│ b12│    BCLK after the edge

       LEFT  ────────┌────┬────┬────┬────┐          MSB starts on
       SD            │MSB │ b14│ b13│ b12│          the edge (no delay)
```

#### Pattern: swimlane sequence (actors × time)

Use when several actors (userspace, a core layer, a driver, hardware) hand work to each other over time and the cross-actor ordering is the point. Draw one vertical lane per actor separated by │ columns, time running downward, and a cross-lane ──▶ arrow for each step; annotate each lane with the state it reaches. Distinct from queue/ring (a buffer between two stages): this shows N actors over one timeline.

```
       trigger START fan-out across the soc_pcm_trigger[][] rows
       ──────────────────────────────────────────────────────────
       time ↓
       ALSA core      │ soc-pcm     │ SOF + IPC4    │ SDW BE / host DMA
       ───────────────┼─────────────┼───────────────┼──────────────────
       snd_pcm_start  │             │               │
         do_start ──▶ │ soc_pcm_    │               │
                      │  trigger    │               │
                      │ runs the    │               │
                      │ 3 rows ──▶  │               │
         link row ────────────────────────────────▶ │ asoc_sdw_trigger
                      │             │               │  ─▶ sdw_enable_
                      │             │               │     stream ENABLED
         comp row ──────────────────▶ sof_pcm_      │
                      │             │  trigger ─▶   │
                      │             │ IPC4 SET_     │
                      │             │ PIPELINE_     │
                      │             │ STATE RUNNING │
         DAI row ─────────────────────────────────▶ │ hda_dsp_stream_
                      │             │               │  trigger: DMA run
       state RUNNING  │             │               │
```

#### Pattern: state-transition graph

Use when an object moves through named states and the legal transitions (including back-edges and self-loops) are the point. Draw each state as a boxed node and each event as a labelled directed ──▶ edge; draw the back-edges explicitly. Distinct from the boxed decision flowchart, which traces control flow through one function; this traces an object's state across its lifetime.

```
       Tip-sense plug state machine (in cs42l42_irq_thread)
       ────────────────────────────────────────────────────
       current_plug_status drives plug_state; only a real change
       of state acts, so repeated reports are ignored.

                       ┌───────────────────────────┐
               ┌──────▶│ CS42L42_TS_UNPLUG         │
               │       │  cancel hs type detect,   │
               │       │  report 0 over the wide   │
               │       │  HEADSET + BTN_0..3 mask  │
               │       └─────────────┬─────────────┘
               │ TS_UNPLUG           │ TS_PLUG
               │                     ▼
               │       ┌───────────────────────────┐
               │       │ CS42L42_TS_PLUG           │
               └───────┤  cs42l42_init_hs_type_    │
                       │  detect (start a cycle)   │
                       └─────────────┬─────────────┘
                                     │ neither bit set
                                     ▼
                       ┌───────────────────────────┐
                       │ CS42L42_TS_TRANS          │
                       │  transient, no report     │
                       └───────────────────────────┘
```

#### Pattern: directed graph / DAG

Use when a multi-node signal or dependency graph has fan-in and fan-out, plus auxiliary nodes (supplies, clocks) that attach to the side rather than carry signal. Draw the signal nodes as boxes joined left-to-right by ──▶ edges, mux fan-in with ─┐/─┘ collectors, and side nodes attached with ◀── or a ▲ stem. More general than parent + N children fan-out (one parent, one level).

```
       rt722-sdca playback + speaker paths; PDE supplies hang off sideways
       ──────────────────────────────────────────────────────────────────

         ┌────────┐      ┌────────┐      ┌────────┐
         │ DP1RX  │ ───▶ │ FU 42  │ ───▶ │   HP   │ ◀── PDE 47 (supply)
         │ aif_in │      │  dac   │      │ output │
         └────────┘      └────────┘      └────────┘

         ┌────────┐      ┌────────┐      ┌────────┐
         │ DP3RX  │ ───▶ │ FU 21  │ ───▶ │  SPK   │ ◀── PDE 23 (supply)
         │ aif_in │      │  dac   │      │ output │
         └────────┘      └────────┘      └────────┘

         static routes {"HP",NULL,"FU 42"} and {"SPK",NULL,"FU 21"} pass
         signal; {"HP",NULL,"PDE 47"} ties the supply to the output pin.
```

#### Pattern: register / address-offset map

Use when several registers sit at fixed offsets within a block, or one block repeats at base + stride · index, and the addressing is the point (per-stream, per-port, or per-lane blocks). Draw the index ──▶ base-address column on the left, and one representative block expanded as a box of its named registers on the right. Distinct from a single-register bitfield (7h), which plots the bits of one register.

```
       Per-stream SDn register blocks (one per host DMA engine)
       ──────────────────────────────────────────────────────────
       SDn block base = remap_addr + 0x80 + 0x20 * idx   (stride 0x20)

         idx        SDn block base
         ───        ──────────────
          0   ───▶  remap_addr + 0x80     ┌──────────────────────┐
          1   ───▶  remap_addr + 0xA0     │ SDn descriptor:      │
          2   ───▶  remap_addr + 0xC0     │   stream tag         │
          .                               │   cyclic buf length  │
          .                               │   format value       │
          n   ───▶  remap_addr            │   last-valid-index   │
                     + 0x80 + 0x20*n      │   BDL base address   │
                                          └──────────────────────┘

       snd_hdac_stream_setup() programs the block for the assigned idx
       idx split: capture  = [0 .. capture_streams)
                  playback = [capture_streams .. num_streams)
```

#### Pattern: layered stack / membrane

Use when the point is how layers stack and where one layer calls through to the next across a named API boundary (userspace / core / driver / firmware-or-hardware). Draw each layer as a full-width box stacked above the next, and label each ▼ divider with the boundary it crosses (the ioctl, the ops vector, the message channel). The boundary labels are the point, not the box contents.

```
       ASoC core (sound/soc/soc-core.c)
               │  devm_snd_soc_register_component(&sdev->plat_drv, ...)
               ▼
       ┌──────────────────────────────────────────────────────────────┐
       │  struct snd_sof_dev          (sound/soc/sof/sof-priv.h:547)  │
       │   ops ───── sof_ops() ─────▶  struct snd_sof_dsp_ops         │
       │   ipc ─────────────────────▶  struct snd_sof_ipc ─▶ ops      │
       └───────────────┬──────────────────────────────┬───────────────┘
                       │ block_write, run, send_msg   │ tx_msg (IPC3/IPC4)
                       ▼                              ▼
               DSP hardware (HDA-gen)            DSP firmware (SOF)
```

#### Pattern: ordered level ladder

Use when a value moves through a small set of strictly-ordered levels and the travel direction matters (power/bias states, D-states, link states). Draw the levels as rows in numeric order, highest at the top, with ▲ (up) and ▼ (down) markers down the side and the per-step rule. Distinct from a state-transition graph: a ladder is monotonic and totally ordered, traversed one step at a time.

```
       enum snd_soc_bias_level: one context climbs and descends the ladder
       ──────────────────────────────────────────────────────────────────

         value   level                  bias_level ──▶ target_bias_level

           3   ┌──────────────┐  ON        full power, signal flowing
               │ SND_SOC_BIAS │
           2   │   _PREPARE   │  PREPARE   transitional, around ON
           1   │              │  STANDBY   supplies up, idle floor
           0   └──────────────┘  OFF       powered down (init seed)

         up:    OFF ─▶ STANDBY ─▶ PREPARE ─▶ ON
         down:  ON  ─▶ PREPARE ─▶ STANDBY ─▶ OFF
```

#### Pattern: refcount with threshold actions

Use when a reference count gates a hardware action only at a threshold crossing (first user enables, last user disables; the 0↔1 edge). Draw a small table or column of the ++/-- events with each count transition (0 ─▶ 1, 1 ─▶ 2, ...) and, against each, whether it reaches the hardware or is skipped. The point is that only the edge transitions act.

```
       be_start refcount: a shared BE starts once and stops once
       ─────────────────────────────────────────────────────────
       (two FEs trigger the same BE; only the edges touch hardware)

         command       be_start       hardware action (soc_pcm_trigger)
         ┌───────────┬─────────────┬──────────────────────────────────┐
         │ START     │  0 ─▶ 1     │ soc_pcm_trigger(START); →START   │
         │ START     │  1 ─▶ 2     │ (skip: be_start != 1)            │
         ├───────────┼─────────────┼──────────────────────────────────┤
         │ STOP      │  2 ─▶ 1     │ (skip: be_start != 0)            │
         │ STOP      │  1 ─▶ 0     │ soc_pcm_trigger(STOP);  →STOP    │
         └───────────┴─────────────┴──────────────────────────────────┘

       START is also gated on state ∈ {PREPARE, STOP, PAUSED};
       STOP is gated on state ∈ {START, PAUSED}, and decrements
       be_start only from STATE_START.  First starter and last
       stopper are the only callers that reach the hardware.
```

#### Pattern: cyclic ring buffer with position pointers

Use when a single cyclic buffer is split into periods/slots and two pointers (a producer and a consumer, e.g. appl_ptr and hw_ptr) chase each other around it with wrap. Draw the periods as a contiguous row of cells, a ▼ from each pointer onto its cell, and note which span is filled vs free and where the pointers wrap. A specialization of queue/ring for one wrapping buffer with two positions.

```
       The PCM ring buffer: hw_ptr and appl_ptr chase around it
       ─────────────────────────────────────────────────────────
       (buffer_size frames, split into periods of period_size)

       ┌────────┬────────┬────────┬────────┬────────┬────────┐
       │ period │ period │ period │ period │ period │ period │
       │   0    │   1    │   2    │   3    │   4    │   5    │
       └────────┴───┬────┴────────┴────────┴────┬───┴────────┘
                    │                           │
                    ▼                           ▼
                 hw_ptr                      appl_ptr
          pointer op reports it      pcm_lib_apply_appl_ptr moves it
          snd_pcm_update_hw_ptr0     after each copy / fill_silence chunk

       playback: appl_ptr leads (app fills ahead), hw_ptr trails (DMA)
       both wrap at runtime->boundary; ack op fires when appl_ptr moves
```

#### Pattern: frame / bandwidth partition grid

Use when one frame or period of a shared medium is divided into slots or row/column cells, each claimed by an entity (TDM slots, a bus frame's columns, channel allocations). Draw the frame as a contiguous ┌─┬─┐ strip of equal cells labelled by slot, optionally a second strip showing a wider or narrower division of the same frame. The point is how the fixed bandwidth partitions.

```
       I2S frame = the two-slot case of TDM
       ──────────────────────────────────────
       (one sample per slot; set_fmt picks I2S, set_tdm_slot widens it)

       One WS (LRCLK) period:
       ┌───────────────────────┬───────────────────────┐
       │       left slot       │       right slot      │
       │       (WS low)        │       (WS high)       │   I2S = 2 slots
       └───────────────────────┴───────────────────────┘

       Same wires, a wider TDM frame (one FSYNC period, N slots):
       ┌──────┬──────┬──────┬──────┬──────┬─────┬───────┐
       │slot 0│slot 1│slot 2│slot 3│slot 4│ ... │slotN-1│
       └──────┴──────┴──────┴──────┴──────┴─────┴───────┘
          set_tdm_slot assigns each codec channel a slot mask (N > 2)
```

### 7j. Behavior and construct coverage (mandatory)

A page documents a mechanism in full, not only the single function path that prompted it. Breadth of coverage (every site that exhibits a behavior, every struct and helper that backs it, the full object lifecycle) is as mandatory as the prose and citation rules above.

- Cite every site that matches a behavior, not one. For each behavior the page describes, find all the places in the kernel source that implement or exhibit it, and cite each one with its file path and line number, as an inline Elixir cross referencer link at the mention and as a fenced ` ```c ` block in the DETAILS section reproducing the relevant lines. When a behavior recurs across many call sites or drivers, cite as many as is practical rather than stopping at the first match. Enumerate the full set with `find_callers`, `grep_functions`, and Grep before writing. If the set is too large to cite exhaustively, cite a representative spread (the core implementation plus several users) and state how many sites exist, rather than silently narrowing to one.
- Cover the data structures and their helpers, not only entry-point functions. Identify the kernel's internal data structures for the topic (the structs, enums, and typedefs that hold the state) together with the helper functions and accessor macros that allocate, initialize, read, modify, and destroy them. List them in the LINUX KERNEL section, reproduce their definitions as fenced ` ```c ` blocks in the DETAILS section, and show the accessors in use there. A page that names a behavior but omits the struct that records the state, or the helper that changes it, is incomplete.
- Cover the object lifecycle and asynchronous behavior, not only static call sites. For each key object, document its life cycle: allocation, initialization, freeing, the locks that serialize access to it, and its reference counting (`kref` / `refcount_t` get and put, and the put that drops the last reference and frees it). Document the dynamic behavior as well: state transitions (which field advances through which states, and what drives each transition), notification mechanisms (notifier chains, `struct completion`, wait queues, eventfd, uevents), and deferred or asynchronous work (`work_struct` and `delayed_work` on a workqueue, tasklets, timers, threaded IRQs, RCU callbacks), along with the ordering and concurrency rules between them. Tracing only "function A calls function B" misses the lifecycle and asynchronous behavior the page exists to explain.
- Call out hard-coded limit values explicitly. Search the code for the constants that bound the mechanism: timeouts, retry and attempt counts, maximum allowable error counts, buffer and queue sizes, poll and backoff intervals, and similar thresholds, whether defined as a macro, an enum value, or a bare literal. Find as many as exist rather than stopping at the first; name each one in the page with its value and the macro or literal that holds it, cite its file and line, and reproduce the defining line in a fenced ` ```c ` block where the value governs a code path the page walks. A page that describes a timeout, a retry loop, or an error threshold without stating the actual number is incomplete.
- The catalog and the scope statement define done-ness. A page is complete when every symbol in its LINUX KERNEL catalog and every behavior in its scope statement is covered to the rules above; "the core API is documented" is not a completion test, and importance ranking never shrinks coverage. When the material outgrows one page, split it along a boundary statement into finer sibling pages; never thin any page's coverage to shorten it.
- Compression may remove words, never coverage. Shortening or rewriting a page must not remove cataloged symbols, documented behaviors, call-site enumerations, figures that carry layout facts, or KERNEL DOCUMENTATION / OTHER SOURCES entries. Removing any of those is a scope change made deliberately: the catalog and the scope statement shrink in the same edit, and the cut is reported. Rule 7p governs the procedure when the shortening happens while deriving from existing material.
- Order DETAILS from generic to specific. Within DETAILS, present the subsystem-generic mechanism first (the core data structures, the shared code path, the framework behavior), then the vendor-, channel-, or driver-specific instances built on top of it. The reader should understand the general mechanism before reading how a particular driver specializes it.

### 7k. Driver examples (mandatory)

When a page illustrates a behavior with a concrete driver, both the choice of driver and the way the page keeps that example self-contained matter.

- Cite only actively-maintained drivers. When choosing a driver as a usage example, pick one with major activity in the past three years (roughly 2023 onward for the v7.0 tree). Confirm this before citing: run `git log` on the driver's file, or semcode `find_commit` with `path_patterns` for the driver's path, and check for substantive commits within the last three years (ignore treewide renames, whitespace, and other mechanical churn). Do not illustrate current behavior with a driver whose only recent commits are trivial or whose last real change is years old; a dormant driver may use deprecated patterns that misrepresent how the mechanism is used today. If no recently-active driver exercises the behavior, say so rather than reaching for a stale one.
- Describe a driver example from its own kernel source, and keep the explanation on this page. Give the driver's role (vendor, bus, device class) and cite its file and the relevant function or callback inline, so the reader needs nothing beyond this page to understand it. Do not point the reader to another driver or another page as a substitute for the explanation, and do not explain the driver by analogy to one documented elsewhere; everything the reader needs is stated here, from this driver's own code.
  - BAD: "The cs35l56 driver registers a jack-detect callback, just like the codec documented elsewhere in this knowledge base."
  - GOOD: "The cs35l56 driver (a Cirrus Logic amplifier in `sound/soc/codecs/cs35l56.c`) registers a jack-detect callback through its `set_jack` component op."

### 7l. Code-block provenance comments (mandatory)

Every fenced ` ```c ` block opens with a provenance comment naming the on-disk origin of the excerpt, in the exact form `/* path/from/tree/root.c:LINE */` on its own first line, where LINE is the number of the first reproduced line in the file at the documented version. A short annotation may follow the line number inside the comment (`/* mm/vma.c:497 (in __split_vma()) */`). A block that stitches excerpts from several places (a caller plus its callee, two case labels far apart, a struct field plus the helper that writes it) marks each excerpt's start with its own interior `/* path:line */` delimiter line, and marks elided code inside an excerpt with a standalone `...` line. Everything between delimiters is verbatim file content per 7e (tabs preserved, comments retained, no reflowed lines).

The provenance comment is what makes a page machine-checkable. `scripts/verify_page.py` splits each block at its delimiters and diffs every unit against the named file, so a missing or wrong provenance line turns an on-disk match into a finding, and a silently drifted excerpt is caught the moment the script runs. Non-code fenced blocks (ASCII figures, quoted commit-message tables, shell output) carry no provenance comment and are not diffed.

### 7m. Link anchoring and exhaustive span linking (mandatory)

This rule extends the every-symbol-linked rule in 7f with anchor selection and exhaustiveness. It is what the numbers in "Golden samples and measured criteria" call links per page.

- A link whose text is a symbol name (`` `vma_start_read()` ``, `` `struct mm_struct` ``, `` `VM_LOCKED` ``, and the LINUX KERNEL `` `'\<sym\>':'path'` `` form) anchors at the symbol's DEFINITION line, so the reference stays valid for `git log -L` and survives unrelated churn elsewhere in the file. It does not anchor at a call site, a comment mention, or a line inside some other function's body, even when that line is what the surrounding prose discusses.
- A reference to a specific non-definition place in code (a call site, one branch, one field assignment) is written as a file-location link whose text is the path and line, for example [`mm/vma.c:717`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L717). Prose that enumerates call sites uses one location link per site, so every count in the page is checkable one click deep.
- Every occurrence of every kernel symbol outside fenced blocks is linked, including repeats of the same symbol on the same page. The exhaustive pass includes the classes that are easiest to skip: `CONFIG_*` options link to the `config X` line of the Kconfig file that declares them; generic primitives (`READ_ONCE()`, `memcpy()`, `rcu_read_lock()`, `atomic_read()`, and the like) link to the definition relevant to the documented architecture; a field path written as `a->b` or `foo.bar` links to the field's declaration line inside the struct definition; an ops-struct member named in prose ("the `fault` hook") links to that member's line in the ops struct definition.
- Settled exemptions (spans that may stay bare): C keywords and operators; local variables, parameters, and goto labels quoted from an excerpt; literal and error values (`-EINVAL`, `NULL` as a value); `/proc`, `/sys`, and sysctl path strings; Kconfig syntax fragments (`=y`); tracepoint field names; a wildcard family name (`VM_*`) when the members it stands for are linked nearby; commit hashes; the `name(2)` man-page notation when the page links the syscall's kernel entry point elsewhere; and symbols verified absent from the documented tree (state the absence in prose).
- Precedent never overrides the rule. "Other pages leave `CONFIG_FOO` bare" or "this page already has thirty bare `READ_ONCE()` spans" is not a reason to leave the next one bare; the rule wins, and the pre-existing in-family spans get fixed in the same pass.

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

### 7p. Deriving from an existing page (mandatory)

These rules govern producing a page from existing material of any provenance, in any subsystem: an earlier-generation draft, a prior revision of the same page, or pages being compressed, merged, or split.

1. Inventory the source first. List the source's LINUX KERNEL catalog entries, its DETAILS sections, the distinct behaviors and call-site enumerations it documents, its figures, and its KERNEL DOCUMENTATION and OTHER SOURCES entries.
2. Give every inventory item an explicit disposition: kept (and where it now lands), merged (into which section), or cut (with the reason). No item disappears without a disposition; a coverage loss that happens as a side effect of rewriting is the failure mode this rule exists to prevent.
3. A cut is a scope decision, not an edit. It removes the item from the LINUX KERNEL catalog and from the scope statement in the same change, and it is reported in the final message (and recorded in the campaign plan file) so the orchestrator or the user can veto it. A symbol that stays in the catalog cannot have its DETAILS coverage cut.
4. The derived page passes the same Gate B parity audit (item 1) as a fresh page. Coverage in the source is not coverage in the derived page; "the source covered it" fails the audit.

A measured failure of exactly this kind motivates the rule: a 2,645-line page compressed to 1,268 lines kept its iterator-helper symbols in the LINUX KERNEL catalog while silently dropping their DETAILS sections, kept one catalog symbol with no DETAILS mention at all, and landed at 0.73 fenced blocks per catalog entry where every conforming page measures at least 1.0. The parity audit catches the desync mechanically; the disposition list is what makes any removal legitimate.

### 8. Behavioral rules

- When asked to "discuss" or "review" a plan, engage conversationally with concise observations and questions. Do not immediately start executing, writing files, or producing verbose output. Wait for explicit approval before creating files.
- When creating a multi-page documentation set, generate in batches of about five pages: dispatch one writer agent per page, roughly five in flight at once, wait for the batch to finish, then checkpoint (record status in the plan file, report done versus remaining) before launching the next batch. Do not launch the whole catalog at once; a session rate limit or API outage kills every in-flight writer, and about five resumable agents is a loss a checkpointed campaign absorbs. Lint agents may trail into the next batch. The full campaign workflow is in "Multi-page campaigns" below.
- When a sub-agent dies mid-page (rate limit, transient API error), resume that same agent by sending it a message; its research context survives in its transcript. Tell it explicitly to skip re-research and write (or fix) from what it already has. Spawn a fresh agent only after resuming fails, and then hand it a compact state summary.
- Always read template/reference files first before generating any content.
- When using parallel sub-agents (Agent tool), ensure they have Write permissions before spawning. If Write is unavailable to agents, fall back to sequential processing immediately rather than failing and retrying.
- When performing batch edits across many files, preserve existing content (e.g., lspci output, code references) that was added in prior passes. Read the full file before editing to avoid accidentally removing prior enrichments.

### 9. Save the page

A page is not done until both gates below pass, and who runs them depends on the mode. A single agent or human producing a page end-to-end runs both gates itself before the page is final. In the pipelined campaign mode (see "Multi-page campaigns" below), the writer follows every rule while composing but does not run the gate loops; a separate lint agent runs Gate A plus the mechanical parts of Gate B (accelerated by the advisory `scripts/verify_page.py` where it helps) and the exhaustive 7m span pass, fixing violations in place; the orchestrator then re-runs the gates as final sign-off. In both modes a page is final only at zero unadjudicated findings. The gates are defined by the manual procedures below and are executable entirely by hand; the script only speeds them up and can be dropped without weakening them.

**Gate A (mechanical, grep the finished page).** Confirm zero hits for each, and re-run after every edit including your own hand-edits: em-dashes; `**` boldface in prose; the label-colon-explanation idiom in prose (7a/7c), excluding the caution blockquote and text inside quotes; the 7c/7d editorializing and superlative phrases (`the reasoning`, `is the key`, `X matters`, `X is what makes Y`, `the pattern is`, `worthwhile`, `crucial`, `elegant`, `cornerstone`, `the most <adj>`, and the like); the banned words `contract`, `tally` (also `tallied`/`tallies`/`tallying`), `canonical`; vague hedges (`usually`, `typically`, `generally`, `normally`, `commonly`, `mostly`, `in practice`, `tends to`); `vtable`; the word `arm`/`arms` for a branch or union case (7c; CPU-architecture names and verbatim quotes exempt); internal `.md` cross-links; and `Why`/`How`/`Where` or trailing-`?` headings. The grep list above is the gate; `scripts/verify_page.py` accelerates it but is advisory (see "Machine verification (advisory)"). When the script is unavailable, fails, or its output looks wrong, run the greps above by hand, fence-aware, and judge each hit in context; boldface and the 7b prose-list shapes are manual either way.

**Gate B (review sign-off, the rules a grep cannot catch).** Verify each item by performing the named action and recording the evidence (a count or a list, not "looks fine"). A page is not done until every item is confirmed; reading the page is not sufficient.

1. Catalog-to-DETAILS parity (7e/7j). Build a parity table with one row per LINUX KERNEL catalog symbol and two evidence columns: where DETAILS reproduces its definition (or the exact case label / branch the page describes) as a fenced ` ```c ` block, and where DETAILS shows a concrete caller or usage as code. Every cell must hold a location in the page; an empty cell is a gap, and a catalog symbol that appears nowhere in DETAILS is a hard failure. Check the reverse direction too: a symbol that carries its own DETAILS section belongs in the catalog. When the page names several distinct users or call paths for one symbol, each named one appears as an excerpt or a per-site location link (7m) and the shown-versus-enumerated split is stated. Tripwire before building the table: fewer fenced ` ```c ` blocks than catalog entries means unpaired symbols (every conforming page measured runs 1.03 to 1.47 blocks per entry; a deficient derived page measured 0.73). Record the table; a bare count does not qualify. Sign off only at zero empty cells.
2. Grounded, non-fabricated code (7e/7l). For every fenced ` ```c ` block, open the on-disk source at its cited `path:line` and confirm the block matches verbatim (tab indentation and comments preserved, `...` only for disclosed elisions). Cross-check with the semcode tools, but the on-disk source at the documented version is ground truth. `scripts/verify_page.py` accelerates this via the 7l provenance comments, but it matches content anywhere in the named file and does not validate the claimed line number; confirm the excerpt actually begins at the cited line. Fallback when the script is unavailable: print the file's lines at the cited range (`sed -n 'START,ENDp'`) beside each block and compare directly. Record the count of code blocks and that every one was confirmed against the file. Sign off only when none is left unverified.
3. Every symbol linked, keyword kept (7f). Scan every inline `` `code` `` span outside fenced blocks. Confirm each kernel symbol is an Elixir link to the correct `path#Lline`, and that types keep the `struct`/`enum` keyword. Spot-read the cited lines on disk. Record any bare span or wrong line found and fixed. Sign off at zero.
4. What-does-what DETAILS headings (7). Read every H3 and H4 under `## DETAILS`. Confirm each is a declarative subject-verb-object sentence, not a bare noun or symbol name. Sign off with the heading count.
5. No negative constructions or anthropomorphic verbs (7). Read the prose. Confirm no `It is X, not Y` constructions, no `lives`/`sits`/`wants` for code, and `walk` used only for traversing a data structure. Grep `[^a-z]not `, ` lives`, ` sits `, ` wants ` for candidates, then judge each in context. Sign off after reading, not after grepping alone.
6. Full coverage (7j). For each behavior the page documents, enumerate every site that exhibits it with `find_callers`/`grep` and confirm the page cites all of them, or cites a representative spread and states how many exist. Confirm every hard-coded limit or constant is named with its value, and that the object lifecycle (allocation, initialization, freeing, the serializing locks, reference counting) and the asynchronous behavior are covered. Record the enumeration. Sign off.
7. Driver examples actively maintained (7k). For each driver cited as an example, run `git log` on its file and confirm substantive commits within roughly three years, and that its role is explained from its own source on this page. Record the newest substantive commit per driver. Sign off.
8. ASCII diagrams (7g-7i). For each figure, confirm Unicode box-drawing only with no ASCII `\`, `|`, or `/` used as a connector, every line under 80 columns, each content-row `│` landing on a `┬` or `┴` junction of the borders above and below, and that the figure shows a spatial or temporal relationship rather than a function-call chain. Sign off per figure.
9. Behavioral-claim audit (7o). List every universal quantifier ("only", "never", "always", "all", "every", "exactly N"), every count, every per-member "each/every X" claim, every restated guard or threshold, and every lifecycle invariant in the page. For each, re-run the enumeration or derivation (record the search performed and its result) and correct the sentence to match; for per-member claims, rebuild the member-to-property mapping and confirm every member, or confirm the stated classifier and its boundary. Confirm every DETAILS heading is true of everything in its section, every behavioral sentence agrees with its adjacent excerpt, and every lead and SUMMARY quantifier agrees with the DETAILS section, table, or enumeration that carries its evidence. Sign off with the claim list and its evidence.

Record the outcome of Gate A and Gate B before saving. If any item cannot be confirmed, the page is not done and is not written.

Write the completed page to: `${CLAUDE_SKILL_DIR}/docs/<dir>/<topic-slug>.md`

Do not modify `SUMMARY.md` or `mkdocs.yml`.

In interactive single-page use, ask before the actual save. In a campaign whose page catalog the user has already approved, save each finished page without a per-page ask and checkpoint per the behavioral rules; git commits still require an explicit user go.

## Multi-page campaigns: planning, dispatch, and verification

Everything above defines a single page. This section defines the workflow for producing a whole documentation set (tens of pages) for one subsystem area: how to plan the set, dispatch page production to sub-agents, and verify the result. It is the workflow that produced the golden samples under `docs/samples/`, written here in subsystem-independent terms; substitute any subsystem's `kernel_paths`, structures, and syscall surface for the mm examples.

### Plan before generating

A campaign starts with a plan the user approves, kept in a durable plan file that survives context loss and session interruption. Build it in this order:

1. Inventory. Spawn read-only research agents, one per major area of the topic, over the subsystem's `kernel_paths` at the documented kernel version. Each agent returns a compact digest: the core structs and their field groups, the API families with file:line anchors, lifecycle and locking facts, hard-coded limits, and version-specific renames or removals (the facts that make pages version-correct). Record the digests in the plan file. Treat every line number in a digest as a hint to re-verify at write time, never as a citation; semcode indexes can lag the tree, and the on-disk source at the documented version is always ground truth.
2. Catalog. Turn the inventory into a page catalog: one table row per page with (a) the output path `docs/<dir>/<group>/<slug>.md`, (b) a scope statement naming the anchor symbols the page is built around, each with a file:line hint, and (c) a tag recording whether the page was explicitly requested or curated to fill a gap. Prefer fine granularity: one mechanism, one page. A vague or blank bullet in the user's topic list is a gap to curate into concrete pages, never a topic to skip. Record explicitly which suggested topics were folded into other pages rather than given their own (the fold-in list prevents re-litigating scope later).
3. Boundary rules. Self-contained pages overlap by design, so for every cluster of sibling pages write one boundary statement that fixes each page's mission. The useful form names the seam symbol: "page A owns the syscall surface and treats the X machinery as a black box; page B owns X's object pipeline; page C owns the physical teardown; helper Y at file:line is the seam where A's coverage ends and B's opens". These statements go into the plan file and later verbatim into each writer brief, so siblings recap each other in at most one short paragraph instead of duplicating walkthroughs.
4. Batch order. Order pages foundational-to-derived: encodings and counters before the objects that hold them, objects before the tree/list machinery that indexes them, machinery before the syscalls that drive it, core mechanisms before driver instances. Split the catalog into batches of about five pages; the batch is the unit of dispatch and checkpointing (see "Batch generation and interruption recovery" below).
5. Checkpoint with the user. Present the catalog and directory layout and get an explicit go before generating anything. Record every subsequent user amendment (priority reorders, pipeline changes, new bans) in a dated amendments section of the plan file at the moment it arrives; amendments supersede the original order silently otherwise.

The plan file is the campaign's memory: inventory digests, the catalog, boundary rules, amendments, per-batch status, the draft-reuse map, and lessons learned (verifier false-positive classes, settled linking adjudications). After any interruption, the plan file plus the pages on disk are sufficient to resume without redoing research.

### Golden samples and measured criteria

The golden samples were produced by this workflow and passed `scripts/verify_page.py` with zero findings against their kernel tree. Their measured shape defines concretely what "in-depth, fine-grained" means for this knowledge base:

| sample | lines | c blocks | Elixir links | figures |
|---|---|---|---|---|
| `docs/samples/golden-overview-mm-struct.md` | 2,940 | 98 | 861 | 1 |
| `docs/samples/golden-lifecycle-mm-refcount.md` | 1,743 | 59 | 591 | 1 |
| `docs/samples/golden-encoding-pgtable-entries.md` | 3,024 | 141 | 718 | 3 |
| `docs/samples/golden-enhanced-vma-overview.md` | 2,922 | 107 | 634 | 1 |

Across the thirteen pages of the campaign that produced them, the per-page ranges were 1,468 to 3,270 lines, 46 to 141 code blocks, and 357 to 861 Elixir links. These numbers are outcomes, not targets: they fall out of the depth rules below when applied to a fine-grained topic. Three tripwires convert them into checks that work for any subsystem: a finished fine-grained page below the smallest golden sample (1,468 lines); a page with fewer fenced ` ```c ` blocks than LINUX KERNEL catalog entries (conforming pages measure 1.03 to 1.47 blocks per entry, because every symbol needs a definition and a usage excerpt; a deficient derived page measured 0.73); and a catalog that shrank across a rewrite without reported cuts. Any tripped wire forces the Gate B parity audit (item 1) and, for a derived page, the 7p disposition list before the page can be called done. The fix for a tripped page is completing coverage per 7j and Gate B, or cutting scope explicitly per 7p; it is never padding prose and never silent thinning. There is no length ceiling; a page ends when coverage is complete, not at a line count.

The depth rules that produce those numbers:

- Definition plus usage, per symbol. Every symbol in the LINUX KERNEL catalog gets both its definition excerpt and at least one real caller or usage excerpt in DETAILS (Gate B item 1). A page of definitions alone reads like a header file; the usage excerpt is what makes each symbol's role concrete.
- Full site enumeration with counts. When prose says a helper is used at N sites, N is a verified count (semcode `find_callers` plus grep, re-checked on disk) and the sites are enumerated with per-site file-location links (7m), or a representative spread is cited with the total stated.
- Every hard-coded limit named with its value and its defining file and line (7j).
- Lifecycle and state transitions in full: allocation, initialization, teardown order, the serializing locks, reference counting, and every state a tracked field moves through with the transition drivers cited (7j).

### Draft-versus-golden contrast

`docs/samples/draft-original-vma-overview.md` is an earlier-generation draft of the same topic as `docs/samples/golden-enhanced-vma-overview.md`; the golden page was rebuilt from it. The pair is kept in `docs/samples/` so the gap between a plausible draft and a page meeting this standard stays concrete and measurable:

| measure | draft | golden |
|---|---|---|
| lines | 1,161 | 2,922 |
| fenced c blocks | 43 | 107 |
| provenance comments | 43 (one per block; single-excerpt blocks only) | 127 (stitched blocks with interior 7l delimiters) |
| Elixir links | 409 | 634 |
| `verify_page.py` result | 1 non-verbatim code block, 1 Gate A hit | zero findings |

The differences that matter are not the raw sizes but what produced them:

- Verification versus plausibility. The draft states facts that read correctly and are wrong at the tree. It claims the VMA's `vm_mm` back-pointer "is set once, at allocation, and never changes"; the golden page shows the second writer (the fork path, where `vm_area_init_from()` copies the parent's pointer and `dup_mmap()` then redirects the clone at the child address space) with both excerpts inline. It claims the anonymous-VMA `vm_pgoff` "holds the starting PFN of the range"; the golden page reproduces the on-disk code showing `vma->vm_pgoff = vma->vm_start >> PAGE_SHIFT` (a virtual page index) together with the kernel's own comment. It claims `vma_set_range()` has "seven call sites in mm/vma.c" and that "every path that resizes a VMA goes through it"; the golden page enumerates all seven sites with location links (six in `mm/vma.c` plus one in `mm/mmap.c`) and shows the split path that adjusts the fields directly. Every draft claim was re-verified symbol by symbol before it survived into the golden page.
- Definition-plus-usage depth. The draft's `vm_lock_seq` section is one paragraph (4 lines); the golden page's runs 88 lines with the field definition, the writer-side stamping code, and the reader-side comparison code. Section for section, the golden page carries the caller excerpt the draft only alludes to.
- Enumeration with location links. The draft asserts counts in prose; the golden page links each site individually, so every count is checkable one click deep.
- Source-of-truth links in OTHER SOURCES. The draft hand-built `git.kernel.org/.../commit/?id=` URLs; the golden page carries byte-exact `Link:` trailer URLs from `git log` (7n).
- Machine cleanliness. The draft fails the verifier (one stitched excerpt does not match the tree verbatim; one label-colon idiom in prose); the golden page has zero findings.
- Coverage. The golden page adds whole sections absent from the draft (the per-VMA lock state catalog, the lifecycle-driver catalog, the mapping-path orchestration walk, the newer preparation-descriptor struct) because the coverage rules in 7j demanded them.

When drafts of any prior generation exist for a topic (next section), this contrast is the acceptance test: reusing a draft is legitimate only when the result is indistinguishable from a fresh page written to this standard.

The audit does not stop at golden. A later enhancement pass over this same golden page corrected an off-by-one call-site count (a written 119 for the 118 on disk) and a provenance comment two lines off its excerpt, and a 7o audit after that found a false universal claim both passes had missed: the page asserted a helper "is invoked from exactly one place" while the tree holds four callers (the plain store helper, its gfp variant, the fork-path bulk store, and an error-path rollback). Golden samples calibrate form and depth; correctness is established only by re-running the 7o actions against the tree, on every page, however golden its history.

### Deriving from prior drafts and pages

When earlier-generation drafts or prior revisions exist for topics in the catalog, mine them instead of ignoring them, under these rules (rule 7p carries the per-page mechanics):

1. Map first, read once. Spawn research agents to read the draft corpus once and record a reuse map in the plan file: for each draft, a verdict (backbone-reusable, mine-sections-only, or ignore), symbol spot-check results against the documented tree, its defect classes with counts (banned wording, stale symbol names, non-verbatim excerpts), and pointers from draft sections to the catalog pages they feed. All later work consults the map, not the corpus.
2. Reuse structure, re-verify everything. A draft may contribute its skeleton, section ordering, tables, and figures. Every symbol, line number, code excerpt, and factual claim taken from a draft is re-verified against the on-disk tree at the documented version before it lands. Treat drafts as unverified claims with good structure; the staleness class that survives spot checks is the silently renamed symbol, so re-find each symbol rather than trusting name continuity.
3. Extend to standard. Reused sections are extended to the definition-plus-usage depth, full enumerations, and lifecycle coverage above. A reused page that stays at draft depth is not done.
4. Scrub to the rules. Sweep reused prose for every Gate A class (drafts predate some rules; branch-metaphor "arm" and label-colon idioms cluster in them), add or correct 7l provenance comments, and rebuild OTHER SOURCES per 7n.
5. Collect across drafts. One catalog page may assemble sections mined from several drafts; the boundary rules decide what belongs where.
6. Disposition, not disappearance. Every source catalog entry, DETAILS section, behavior, enumeration, figure, and reference gets a 7p disposition (kept, merged, or cut with its reason). Cuts shrink the derived page's catalog and scope statement in the same change and are recorded in the plan file so the orchestrator or the user can veto them; the derived page then passes the Gate B parity audit like a fresh one.

### Dispatch pipeline: writer, lint, verify

Campaign pages are produced by a three-stage pipeline. The separation exists because a writer re-reading its own page misses its own blind spots; an independent pass with fresh context reliably catches wrong anchors, drifted excerpts, and skipped spans the writer cannot see.

1. Writer (the strongest available model). Researches with semcode plus Grep/Read, confirms every fact on disk, and writes the complete page following every rule in this file while composing. The writer does not run the Gate A/B loops after writing; its brief says so explicitly, because self-lint spends the strongest model's budget on work the next stage redoes better.
2. Lint (a different, cheaper model, fresh context). Runs the advisory `scripts/verify_page.py`, falling back to the manual gate procedures when the script fails or is absent; performs the manual sweeps the script cannot do (boldface, 7b prose-list shapes, 7d superlatives judged in context, negative constructions, anthropomorphic verbs); re-derives the page's counts, universal claims, and restated conditions per 7o; and executes the exhaustive 7m span-linking pass. Fixes everything in place, re-checks after its own edits, and reports what changed plus every finding it adjudicated as a false positive, with reasoning. Concurrent lint agents use unique scratchpad filenames for any helper scripts (shared names have collided).
3. Final verify (the orchestrator). Re-runs the gates after lint (script-accelerated or manual), spot-audits the adjudications, confirms the Gate B parity table has zero empty cells (dispatching a writer follow-up for any coverage gap lint flagged, since lint does not write new sections), and confirms any 7p cuts were reported before marking the page done in the plan file. Residual findings are fixed or recorded in the plan file as settled false-positive classes for future lint briefs.

Model-tier guidance, subsystem-independent: page writing needs the strongest model available (research judgment, prose discipline, figure quality); the lint pass is mechanical-plus-checklist work a mid-tier model performs reliably when the brief is explicit and exhaustive; the orchestrator keeps final sign-off and never delegates it.

### Writer brief template

Fill the brackets from the plan file. Reproduce the conventions in the brief itself; a writer must never have to guess a house rule.

```
Write the page <output path> for the <subsystem> knowledge base, following
the kernel-glossary-skill SKILL.md in full.

MISSION. <Scope statement from the catalog row, naming the anchor symbols
with file:line hints.> <The boundary rules for this page's cluster: what
this page owns, what each sibling page owns, the seam symbols. Recap of
sibling territory is limited to one short paragraph.>

GROUND RULES.
- Documented tree: <path>, version <tag>. Every fact, line number, and
  excerpt is verified against the on-disk tree before it lands; semcode
  results are hints, the disk is ground truth. Architecture scope: <arch>.
  State CONFIG assumptions in the page where behavior depends on them:
  <list>.
- Research with semcode (find_function, find_type, find_callers,
  grep_functions, find_commit, dig) plus Grep/Read. Enumerate call-site
  populations before writing any prose that counts or characterizes them.
- Template section order exactly; section 6 heading for this subsystem:
  <value or "omit">. The page is self-contained; no internal .md links.
- Every ```c block verbatim from disk with a /* path:line */ provenance
  comment (7l); interior delimiters for stitched excerpts; tabs preserved.
- Symbol-name links anchor at definition lines; call sites use file:line
  location links; every symbol occurrence outside fences is linked (7m).
- OTHER SOURCES only from byte-exact Link: trailers in git log (7n).
- Depth: every LINUX KERNEL symbol gets a definition excerpt AND a usage
  excerpt in DETAILS (so the finished page carries at least as many ```c
  blocks as catalog entries); every hard-coded limit named with value and
  line; lifecycle (alloc/init/free/locking/refcount) and all state
  transitions covered (7j). Done-ness is the catalog and scope statement
  exhausted, never "the core API is documented". If the material outgrows
  one page, report a proposed split along a boundary statement; never thin
  coverage to shorten the page.
- Behavioral claims per 7o: enumerate a set before writing "only", "never",
  "always", or "exactly N" about it; build the member-to-property mapping
  before writing any "each/every X" sentence, and when the claim holds only
  for a primary or direct relation, state that classifier and its boundary
  in the sentence; keep every lead and SUMMARY quantifier consistent with
  the page's own DETAILS tables and enumerations; state each enumeration's
  search basis inline; derive restated guards from the reproduced code by
  exact negation; make every DETAILS heading true of its whole section.
- Writing rules 7 through 7k apply while composing: no em-dash, no boldface,
  no label-colon prose, no hedging, no editorializing, no "arm" for a branch
  or union case, declarative DETAILS headings, single-line paragraphs.
- <If an existing draft or prior page feeds this one: the source file(s)
  and sections to mine, the known source defects from the reuse map, and
  the 7p rules: inventory the source's catalog entries, sections,
  behaviors, figures, and references first; give every item a
  kept/merged/cut disposition; report every cut and shrink the catalog and
  scope statement with it. A symbol kept in the catalog keeps its DETAILS
  coverage.>

Do NOT run the Gate A/B verification loops after writing; a separate lint
stage does that. Write the file to <output path>. Your final message is a
short report (sections written, catalog symbol count, call-site counts you
verified, anything you could not verify), not the page text.
```

### Lint brief template

```
Lint the finished page <path> against the kernel tree at <tree path>,
following the kernel-glossary-skill SKILL.md.

1. Run: python3 <skill dir>/scripts/verify_page.py --tree <tree path> <path>
   The script is advisory. If it is unavailable, fails, or a finding looks
   wrong, fall back to the manual gates: the Gate A grep list from SKILL.md
   section 9 run fence-aware, an on-disk comparison of every ```c block at
   its /* path:line */ provenance, and opening each questioned link's target
   line. Fix every confirmed finding in place: wrong anchors get
   re-looked-up on disk, non-verbatim blocks get re-excerpted from the file,
   banned prose gets rewritten per 7a-7d. Re-check after your edits until
   the only remaining findings are adjudicated false positives; report each
   adjudication with its reasoning. Known false-positive classes to
   adjudicate rather than "fix": <from the plan file, e.g. expression spans
   linking one constituent symbol, syscall-name links anchored at the kernel
   entry point, designated-initializer citations>.
2. Manual Gate A sweep for what the script cannot see: boldface in prose,
   intro-sentence-plus-list shapes (7b), hollow superlatives judged in
   context (7d), negative constructions, anthropomorphic verbs.
3. Exhaustive span pass (7m): every occurrence of every kernel symbol
   outside fenced blocks is linked, INCLUDING repeats, CONFIG_* options (to
   the Kconfig config line), generic primitives (READ_ONCE, memcpy,
   rcu_read_lock, ... to their definitions for the documented architecture),
   field paths a->b (to the field declaration), and named ops-struct
   members. Exemptions: <the settled 7m exemption list>. Never cite in-page
   or in-family precedent to leave a span bare; the rule always wins and
   pre-existing bare spans in the same family get fixed too.
4. Correctness re-derivation (7o): re-run the enumeration behind every
   count and every "only"/"never"/"always"/"exactly" claim; rebuild the
   member-to-property mapping behind every "each/every X" sentence (one
   exception falsifies it; fix the sentence, restrict the family, or state
   the classifier and its boundary); check every lead and SUMMARY
   quantifier against the DETAILS section, table, or enumeration that
   carries its evidence; re-derive every restated guard against its
   excerpt; confirm each DETAILS heading is true of everything in its
   section; confirm each excerpt begins at its claimed provenance line.
   These are the only fact edits you may make; report each with the search
   you ran and its result.
5. Parity audit (Gate B item 1): build the catalog-to-DETAILS table, one
   row per LINUX KERNEL symbol, recording where its definition excerpt and
   its usage excerpt land. Flag the tripwire if the page has fewer ```c
   blocks than catalog entries. Do not write missing sections yourself;
   report every empty cell as a coverage gap for a writer follow-up.
6. Beyond the 7o corrections, do not change facts, scope, or structure;
   this is a compliance pass. Use a unique scratchpad filename for any
   helper script you write.

Report: findings fixed by class with counts, 7o corrections with evidence,
parity gaps (catalog symbols lacking a definition or usage excerpt),
adjudicated false positives with reasoning, residual items you could not
resolve.
```

### Batch generation and interruption recovery

- Generate about five pages per batch: one writer agent per page, dispatched together, then a hard checkpoint before the next batch launches. Five keeps what a session rate limit or API outage can kill at once down to a recoverable set (each dead writer resumes from its transcript) while still parallelizing the writing. Do not launch the whole catalog in parallel. Lint agents may trail into the following batch.
- When a writer or lint agent dies mid-page, resume that same agent with a message; its research context survives in its transcript. Say explicitly "do not redo the research; write the page now from what you have". If repeated resumes fail, extract a compact state report and hand the remainder to a fresh agent.
- After every completed page, update the plan file (status, page statistics, adjudications, lessons) so a future session resumes from the plan file plus the on-disk pages alone.
- Pages land only under `${CLAUDE_SKILL_DIR}/docs/<dir>/`. No `SUMMARY.md` or `mkdocs.yml` edits, and no git commits, without an explicit user go.

### Machine verification (advisory)

`${CLAUDE_SKILL_DIR}/scripts/verify_page.py` accelerates the mechanical gates:

```
python3 scripts/verify_page.py --tree /path/to/kernel/tree page.md [more.md ...]
```

It auto-detects the documented kernel version from each page's first Elixir link and checks three layers. First, every Elixir link: the file exists in the tree, the cited line is in range, and the linked symbol's text is found within a few lines of the anchor (with allowances for Kconfig links dropping the `CONFIG_` prefix, `_noprof` allocation wrappers, macro-generated accessors, and wildcard-family links). Second, every fenced c block: diffed verbatim, modulo declared `...` elisions, against the file named by its 7l provenance comment. Third, a fence-aware Gate A sweep (em-dash, label-colon, editorializing, banned words, hedges, "arm", internal `.md` links, negative constructions, bad headings) with a verbatim-quote exemption.

The script is advisory, never authoritative; the manual procedures in section 9 and rule 7o are the gates, and the script only speeds them up. Treat its output as leads, in both directions. False positives accumulate as the script ages out of maintenance (kernel idioms, link forms, and the style rules drift away from its regexes); act on a finding only after the underlying rule in this file confirms it, and record a finding the rule does not confirm as a false-positive class instead of obeying the script. False negatives are structural: the script validates only what is present on the page. It cannot see a missing link, a missing usage excerpt, an unenumerated call site, or a wrong behavioral claim; its symbol check accepts any match within a few lines of the anchor, so a link that violates 7m's definition-line rule can still pass; and its code check matches content anywhere in the named file, so a wrong provenance line number passes. A CLEAN result therefore never closes a gate by itself, and a page that is script-CLEAN can still fail Gate B and the 7o audit.

When the script is unavailable, crashes, or cannot be trusted, run the gates by hand; they are defined to work without it. Gate A is the grep list in section 9 run fence-aware, judging each hit in context. Gate B item 2 is performed by opening every ```c block's provenance file at its cited line (`sed -n 'START,ENDp'`) and comparing the reproduced lines directly. Gate B item 3 is performed by opening each link's target line and confirming the symbol's definition is there. The 7o behavioral-claim audit is manual always. Fold crisp new false-positive classes into the script when convenient, but never let a page's done-ness depend on the script running.

## Subsystem Map

Each entry maps a subsystem to its tag, output directory, primary kernel source paths, specification name(s), and the heading to use for section 6.

### PCIe

- tag: `pcie`
- dir: `pci`
- kernel_paths: `drivers/pci/`, `include/linux/pci.h`, `include/uapi/linux/pci_regs.h`
- spec: PCI Express Base Specification
- section6_heading: REGISTERS

### xHCI

- tag: `usb` (secondary: `xhci`)
- dir: `xhci`
- kernel_paths: `drivers/usb/host/xhci*`, `include/linux/usb/hcd.h`
- spec: xHCI (eXtensible Host Controller Interface) Specification
- section6_heading: REGISTERS

### USB

- tag: `usb`
- dir: `usb`
- kernel_paths: `drivers/usb/core/`, `drivers/usb/common/`, `include/linux/usb.h`, `include/linux/usb/ch9.h`
- spec: USB 2.0 Specification, USB 3.2 Specification
- section6_heading: REGISTERS

### ACPI

- tag: `acpi`
- dir: `acpi`
- kernel_paths: `drivers/acpi/`, `include/acpi/`, `include/linux/acpi.h`
- spec: ACPI Specification
- section6_heading: METHODS

### USB4

- tag: `usb4`
- dir: `usb4`
- kernel_paths: `drivers/thunderbolt/`, `include/linux/thunderbolt.h`
- spec: USB4 Specification, Thunderbolt 3/4 Specification
- section6_heading: REGISTERS

### V4L2

- tag: `v4l2`
- dir: `v4l2`
- kernel_paths: `drivers/media/`, `include/media/`, `include/uapi/linux/videodev2.h`
- spec: (none; refer to V4L2 subsystem documentation)
- section6_heading: INTERFACES

### DisplayPort

- tag: `display-port`
- dir: `dp`
- kernel_paths: `drivers/gpu/drm/display/drm_dp*`, `include/drm/display/drm_dp*`
- spec: VESA DisplayPort Standard, VESA eDP Standard
- section6_heading: REGISTERS

### DRM

- tag: `graphics`
- dir: `drm`
- kernel_paths: `drivers/gpu/drm/`, `include/drm/`, `include/uapi/drm/`
- spec: (none; refer to DRM subsystem documentation)
- section6_heading: INTERFACES

### Sound

- tag: `sound`
- dir: `sound`
- kernel_paths: `sound/`, `include/sound/`, `include/uapi/sound/`
- spec: Intel High Definition Audio Specification, USB Audio Class Specification
- section6_heading: REGISTERS

### Power Management

- tag: `power-management`
- dir: `pm`
- kernel_paths: `drivers/base/power/`, `kernel/power/`, `include/linux/pm.h`, `include/linux/suspend.h`
- spec: ACPI Specification (power management chapters), PCI PM Specification
- section6_heading: none

### Concurrency

- tag: `concurrency`
- dir: `concurrency`
- kernel_paths: `kernel/locking/`, `include/linux/spinlock.h`, `include/linux/mutex.h`, `include/linux/rwsem.h`
- spec: (none)
- section6_heading: PRIMITIVES

### Drivers

- tag: `drivers`
- dir: `drivers`
- kernel_paths: `drivers/base/`, `include/linux/device.h`, `include/linux/platform_device.h`
- spec: (none)
- section6_heading: INTERFACES

### Debugging

- tag: `debugging`
- dir: `debug`
- kernel_paths: `kernel/trace/`, `lib/dynamic_debug.c`, `include/linux/ftrace.h`
- spec: (none)
- section6_heading: none

### ARM64

- tag: `arm64`
- dir: `arm64`
- kernel_paths: `arch/arm64/`, `include/asm-generic/`
- spec: Arm Architecture Reference Manual (Arm ARM)
- section6_heading: REGISTERS

### Workflows

- tag: `workflows`
- dir: `workflows`
- kernel_paths: (none; workflow pages describe development processes)
- spec: (none)
- section6_heading: none

### Networking

- tag: `networking`
- dir: `net`
- kernel_paths: `net/core/`, `net/netfilter/`, `net/sched/`, `net/dsa/`, `net/bridge/`, `net/switchdev/`, `net/netlink/`, `drivers/net/`, `include/linux/netdevice.h`, `include/linux/skbuff.h`, `include/net/`
- spec: (none; linux network subsystem constructs)
- section6_heading: INTERFACES

### Ethernet

- tag: `ethernet`
- dir: `ethernet`
- kernel_paths: `drivers/net/ethernet/`, `drivers/net/phy/`, `drivers/net/mdio/`, `net/ethtool/`, `include/linux/etherdevice.h`, `include/linux/ethtool.h`, `include/linux/phylink.h`, `include/linux/phy.h`, `include/linux/mdio.h`, `include/linux/mii.h`, `include/linux/of_mdio.h`, `include/uapi/linux/ethtool.h`, `include/uapi/linux/ethtool_netlink.h`, `include/uapi/linux/mii.h`
- spec: IEEE 802.3 (Ethernet)
- section6_heading: REGISTERS

### Bluetooth

- tag: `bluetooth`
- dir: `bluetooth`
- kernel_paths: `net/bluetooth/`, `drivers/bluetooth/`, `include/net/bluetooth/`
- spec: Bluetooth Core Specification
- section6_heading: INTERFACES

### Memory Management

- tag: `mm`
- dir: `mm`
- kernel_paths: `mm/`, `include/linux/mm.h`, `include/linux/mm_types.h`, `include/linux/mm_types_task.h`, `include/linux/mmzone.h`, `include/linux/gfp.h`, `include/linux/gfp_types.h`, `include/linux/page-flags.h`, `include/linux/page-flags-layout.h`, `include/linux/page_ref.h`, `include/linux/pageblock-flags.h`, `include/linux/page-isolation.h`, `include/linux/pagemap.h`, `include/linux/pfn.h`, `include/linux/memblock.h`, `include/linux/memremap.h`, `include/linux/slab.h`, `include/linux/nodemask.h`, `include/linux/numa.h`, `include/linux/percpu.h`, `include/linux/mmdebug.h`, `include/linux/poison.h`, `include/linux/highmem-internal.h`, `include/linux/hugetlb.h`, `include/linux/rmap.h`, `include/linux/sched/mm.h`, `include/vdso/page.h`, `include/asm-generic/memory_model.h`, `include/asm-generic/pgalloc.h`, `include/net/page_pool/types.h`, `arch/x86/include/asm/page.h`, `arch/x86/include/asm/page_types.h`, `arch/x86/include/asm/sparsemem.h`
- spec: (none)
- section6_heading: none
