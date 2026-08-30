# PAGE-02: Self-contained kernel-source citation

> Was: 7e. Self-contained kernel-source citation

**INPUT:** The LINUX KERNEL catalog, the DETAILS section's fenced C blocks, and the on-disk kernel tree at the documented version (the semcode tools find code; the disk is ground truth).

**OUTPUT:** The catalog-to-DETAILS parity table (a definition column and a usage column per catalog symbol, zero empty cells, both directions checked, the shown-versus-enumerated split stated) and a page that passes the sufficiency test: the real code inline for everything it explains.

**Problem:**

1. A page that describes code without showing it forces the reader into the tree.
2. Every page reads as a self-contained source: a reader who never opens the kernel tree still finishes the page knowing exactly what the relevant code does.
3. Wherever the page explains how a function works, what a struct looks like, how a macro is used, or how a call site invokes a callee, the actual code goes inline as a fenced ` ```c ` block before or alongside the explanation.
4. The Elixir link is for navigation; the code block is for comprehension.
5. "See [`func()`](https://elixir...)" does not count as showing the code.

**Rule:**

1. Never fabricate, paraphrase, or approximate kernel source.
2. Every ` ```c ` block is the real code, located and verified with the semcode tools (`find_function`, `find_type`, `grep_functions`) and by reading the on-disk source file, then reproduced verbatim: exact text, all comments, tab indentation.
3. Confirm the symbol exists at the documented version and the lines match the file before citing them; a symbol whose real code cannot be located gets no code block.
4. Where a semcode index disagrees with the working tree, the on-disk source at the documented version is ground truth.

**Rule:**

1. Every function in LINUX KERNEL gets at least one ` ```c ` block in DETAILS: its full body when small, or the body of the case label / branch / inner block the page actually describes.
2. A function whose body fits in a screen of code is shown, not described.
3. Every struct or enum in LINUX KERNEL gets its type definition reproduced (comments and `#ifdef` regions included), so the reader sees the exact field list without leaving the page.
4. Every macro or static array referenced in body prose (`fallbacks[][]`, `__used` lookup tables) is reproduced where the prose first depends on it.

**Rule:**

1. A call-chain walk shows both ends: the caller's invocation site as one block, the callee's body as another.
2. A switch, conditional, or loop whose structure is the point is reproduced verbatim, never paraphrased.
3. A kernel comment is quoted inside the fenced block that contains its surrounding code and referenced in prose via "According to the comment <quote>, ...".
4. A commit message carrying a benchmark table or ASCII figure is reproduced in a plain ` ``` ` fence so the formatting survives.

5. Each block stays as close to the source as practical: tabs preserved, comments retained, `...` elision only for irrelevant intermediate code that changes nothing for the reader.
6. A body too long to reproduce in full is split across blocks at natural boundaries (one per case label, loop, or error-handling tail) with prose between, never truncated.

The sufficiency test:

1. With the page open in one window and no terminal, no other tab, no kernel tree, could the reader describe in their own words exactly which lines run on the documented path?
2. If not, more code blocks are needed.
3. DETAILS is the place for bulk citation; SUMMARY may carry a short snippet when a single line of code conveys the topic best.

**PASS CRITERIA:**

1. Build the catalog-to-DETAILS parity table: one row per LINUX KERNEL symbol, one evidence column for where DETAILS reproduces its definition (or the exact case label or branch the page describes) as a fenced C block, one for where DETAILS shows a concrete caller or usage. Record the table, not a bare count. Pass only at zero empty cells; a catalog symbol appearing nowhere in DETAILS is a hard failure.
2. Check the reverse direction too: a symbol that carries its own DETAILS section belongs in the catalog. When the page names several distinct users or call paths for one symbol, each named one appears as an excerpt or a per-site location link, and the shown-versus-enumerated split is stated.
3. Tripwire before building the table: fewer fenced C blocks than catalog entries guarantees unpaired symbols (every conforming page measured runs 1.03 to 1.47 blocks per entry; a deficient derived page measured 0.73).
4. Confirm every struct and enum definition is reproduced with comments and `#ifdef` regions, every macro or static array the prose depends on is reproduced at first dependence, and every call-chain walk shows the invocation site and the callee body as separate excerpts.
5. Confirm every block was located and verified against the on-disk source at the documented version before citing (semcode finds it; the disk is ground truth), and that a symbol whose real code could not be located has no block.
6. Apply the sufficiency test to the main documented path and record the result: with only the page open, the reader can say exactly which lines run.
