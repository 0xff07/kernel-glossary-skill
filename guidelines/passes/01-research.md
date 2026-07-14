# Pass 01: research

Purpose: locate and record every fact the page will need, before any prose exists.
Inputs: the resolved parameters from pass 00 (subsystem entry, topic scope, documented version); in a campaign also the catalog row's scope statement and boundary rules.
Outputs: the research dossier at `progress/<campaign>/<page-slug>.dossier.md`, in the run's artifact directory (SKILL.md ("The progress/ workspace")), per `guidelines/passes/dossier.md`.
Run by: the writer by default (single-agent inline, or the campaign writer agent before composing); a dedicated researcher agent (brief at the end of this file) when a campaign fans research out explicitly.
Next: pass 02 (`guidelines/passes/02-write.md`).

Rules are cited by stable ID; `guidelines/rules/INDEX.md` maps every ID to its file.

## Search local kernel source code

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

Record every located symbol into the dossier as you go. Elixir URL syntax and anchor selection are governed by rule 7m (`guidelines/rules/rules.md` (7m)).

## Identify specifications

Check source code comments and headers for references to specification chapters and sections. Map the subsystem to its known specifications using the `spec` field from the subsystem's entry (`guidelines/reference/subsystems.md`).

If semcode tools are available, supplement source code comments with:

- `find_commit` with `symbol_patterns` for key functions/types: commit messages frequently cite spec sections
- `dig` on the commits that introduced the relevant code: the associated mailing list threads often reference specific spec chapters and provide review discussion suitable for OTHER SOURCES
- `grep_functions` with patterns like `section|chapter|spec|table` to find spec references embedded in function bodies or comments

Format each entry as: `<spec name>, section <N.N>: <section title>`

If no specification applies, leave the SPECIFICATIONS section present but empty.

## Find usage examples for LINUX KERNEL symbols

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

Write or update the dossier before moving to the write pass; the dossier is the recovery point for an interrupted page and the re-derivation hint sheet for the lint-fix and verify passes. Every dossier fact is a hint to re-verify on disk at write time, never a citation.

## Dispatching a researcher (optional campaign fan-out)

The campaign default is that the writer researches its own page (SKILL.md ("Modes")); dispatch dedicated researchers only as an explicit opt-in, when research should fan out ahead of writing (pre-building dossiers for a batch) or when a single agent is stepping the passes one at a time across sessions. Model tier: strong enough for research judgment; the dossier's search bases and version-drift notes are what the later passes build on. The researcher writes only the dossier, inside the run's artifact directory; everything else is read-only. Its final message is a two-line summary, never the dossier text. On death, resume the same agent and ask it to flush what it has into the dossier; a partially filled dossier with accurate OPEN GAPS is a valid deliverable.

```
Research the page <page slug> for the <subsystem> knowledge base; do not
write the page.

SKILL_DIR: <absolute path to the kernel-glossary-skill checkout>

MANDATORY READING, in order:
1. <SKILL_DIR>/guidelines/passes/00-prep.md — resolve the parameters;
   skip the sample reading, which is the writer's job.
2. <SKILL_DIR>/guidelines/passes/01-research.md — your procedure.
3. <SKILL_DIR>/guidelines/passes/dossier.md — your deliverable's format.
4. <SKILL_DIR>/guidelines/reference/subsystems.md — read only the page's subsystem entry.

MISSION. <Scope statement from the catalog row, naming the anchor symbols
with file:line hints, and the boundary rules for this page's cluster.>

FACTS. Documented tree: <path>, version <tag>, commit <sha>.
Architecture scope: <arch>. Index line numbers are hints; confirm on disk
before recording a location.

Write the dossier to <SKILL_DIR>/progress/<campaign>/<slug>.dossier.md,
and write nowhere else in progress/, which belongs to other runs too.
Your final message is a two-line summary (symbol count, enumerations
recorded, open gaps), not the dossier text.
```
