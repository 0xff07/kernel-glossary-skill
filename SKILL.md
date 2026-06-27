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
- `docs/acpi/` — the golden-standard reference pages for writing. The worked examples under this directory define the house style for the lead summary, section structure, prose, ASCII diagrams, and self-contained kernel-source citation. When writing any new page, imitate the closest-matching page under `docs/acpi/`, and not pages in any other subsystem directory.
- Major subsystem directories under `docs/`: one per entry in the Subsystem Map at the end of this file (the `dir` field of each entry)

## Input

`$ARGUMENTS` or conversation context provides:
- The subsystem (e.g., xHCI, PCIe, ACPI, USB4, DRM)
- The topic name (e.g., "host controller initialization", "MSI-X vectors")
- Optionally, an output directory override

If `$ARGUMENTS` is empty, derive the subsystem and topic from the conversation context.

## Procedure

### 1. Read the template and the golden reference pages

Before generating any content, read `docs/templates/TEMPLATE-FULL.md` (relative to `${CLAUDE_SKILL_DIR}`) for the page structure and section order.

Then pick the golden-standard reference page to imitate. The pages under `docs/acpi/`, and not pages in any other subsystem directory, are the golden standard for writing: they define the house style for structure, prose, ASCII diagrams, and self-contained kernel-source citation. Open the one or two whose scenario most resembles the page about to be written, read them in full, and use them as the concrete reference while writing. Map the new page to the closest analog:

- register or bitfield pages: `docs/acpi/ec/registers.md`
- control method / AML object pages: `docs/acpi/core/evaluate-object.md`, `docs/acpi/config/crs.md`, `docs/acpi/config/dsm.md`
- event, interrupt, and dispatch pages: `docs/acpi/event/gpe.md`, `docs/acpi/event/sci.md`, `docs/acpi/event/fixed-events.md`
- notification / callback pages: `docs/acpi/notify/notify.md`, `docs/acpi/notify/handlers.md`
- identification / enumeration object pages: `docs/acpi/id/hid.md`, `docs/acpi/id/sta.md`
- power-state pages: `docs/acpi/pm/d-states.md`, `docs/acpi/pm/power-resources.md`

If none matches exactly, pick the closest structural analog under `docs/acpi/` anyway. Do not fall back to pages outside `docs/acpi/` as the style model.

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

The golden-standard reference pages under `docs/acpi/` already embody every rule in this section. The closest-matching page you read in step 1 is your worked example; mirror its structure, phrasing, diagram style, and code-citation density. The examples in the rules below use ACPI symbols to match those pages; they illustrate the rule mechanic, and the page to imitate is always the closest `docs/acpi` page. All generated content must follow these rules:

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

The H3 catalog lists in LINUX KERNEL (grouped by file or functional area as the docs/acpi pages do, for example `EC_SC status bit macros`, `Port accessors`, `Transaction state machine`) and the bullet lists in KERNEL DOCUMENTATION and OTHER SOURCES are reference catalogs and remain as lists. Tables remain as tables. This rule applies only to prose-explanation lists, not to reference catalogs.

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

When a diagram is used, follow the style established in the golden-standard pages under `docs/acpi/` (for example the status-byte register map in `docs/acpi/ec/registers.md` and the sparse GPE slot map in `docs/acpi/event/gpe.md`). Use Unicode box-drawing characters (`┌ ┐ └ ┘ │ ─ ├ ┤ ┬ ┴ ┼`) and `▼ ▲ ◀ ▶` for arrows. Title each sub-diagram with a short heading underlined by a `────` rule. Multiple sub-diagrams may share one fenced block when each has its own titled section. Indent the whole figure 4 spaces inside the fenced block so it reads as a figure, not as text. Keep every line under 80 columns so the figure renders without wrapping in plain-text views.

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
- Order DETAILS from generic to specific. Within DETAILS, present the subsystem-generic mechanism first (the core data structures, the shared code path, the framework behavior), then the vendor-, channel-, or driver-specific instances built on top of it. The reader should understand the general mechanism before reading how a particular driver specializes it.

### 7k. Driver examples (mandatory)

When a page illustrates a behavior with a concrete driver, both the choice of driver and the way the page keeps that example self-contained matter.

- Cite only actively-maintained drivers. When choosing a driver as a usage example, pick one with major activity in the past three years (roughly 2023 onward for the v7.0 tree). Confirm this before citing: run `git log` on the driver's file, or semcode `find_commit` with `path_patterns` for the driver's path, and check for substantive commits within the last three years (ignore treewide renames, whitespace, and other mechanical churn). Do not illustrate current behavior with a driver whose only recent commits are trivial or whose last real change is years old; a dormant driver may use deprecated patterns that misrepresent how the mechanism is used today. If no recently-active driver exercises the behavior, say so rather than reaching for a stale one.
- Describe a driver example from its own kernel source, and keep the explanation on this page. Give the driver's role (vendor, bus, device class) and cite its file and the relevant function or callback inline, so the reader needs nothing beyond this page to understand it. Do not point the reader to another driver or another page as a substitute for the explanation, and do not explain the driver by analogy to one documented elsewhere; everything the reader needs is stated here, from this driver's own code.
  - BAD: "The cs35l56 driver registers a jack-detect callback, just like the codec documented elsewhere in this knowledge base."
  - GOOD: "The cs35l56 driver (a Cirrus Logic amplifier in `sound/soc/codecs/cs35l56.c`) registers a jack-detect callback through its `set_jack` component op."

### 8. Behavioral rules

- When asked to "discuss" or "review" a plan, engage conversationally with concise observations and questions. Do not immediately start executing, writing files, or producing verbose output. Wait for explicit approval before creating files.
- When creating large batches of documentation pages (10+), work in batches of 5-6 files at a time to avoid rate limits. After each batch, checkpoint progress and report what is done vs remaining.
- Always read template/reference files first before generating any content.
- When using parallel sub-agents (Agent tool), ensure they have Write permissions before spawning. If Write is unavailable to agents, fall back to sequential processing immediately rather than failing and retrying.
- When performing batch edits across many files, preserve existing content (e.g., lspci output, code references) that was added in prior passes. Read the full file before editing to avoid accidentally removing prior enrichments.

### 9. Save the page

Write the completed page to: `${CLAUDE_SKILL_DIR}/docs/<dir>/<topic-slug>.md`

Do not modify `SUMMARY.md` or `mkdocs.yml`.

Ask before doing actual save.

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
