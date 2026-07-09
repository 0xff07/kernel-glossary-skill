# 7. Writing rules (mandatory)

Rule IDs (7, 7a-7r) resolve via `guidelines/rules/INDEX.md`; 7g-7i live under `guidelines/diagrams/`.

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
