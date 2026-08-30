# BAN-01: Core writing bans

> Was: 7. Core writing bans

**INPUT:** Every body sentence and every H3/H4 heading of DETAILS, SUMMARY, and body sections on the finished page: a prose view of the page for the sentence-level sweeps, the raw file for the heading and boldface checks, and the figure-annotation text inside fences for the placement-verb, em-dash, and negative-construction bans.

**OUTPUT:** Prose with zero em dashes, boldface, negative constructions, anthropomorphic placement verbs, and "vtable", and headings that are declarative what-does-what statements; delivered with an adjudicated candidate list (every hit fixed or recorded exempt) at zero unadjudicated findings.

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

**PASS CRITERIA:**

- Em dashes: zero hits for the em-dash character outside fenced blocks, and zero in figure-annotation text, which the figure sweep reaches separately; no exemption applies in either region.
- Boldface: zero `**` in page prose on the raw file (`/**` kerneldoc openers inside fenced code are exempt).
- Negative constructions: sweep `(,|\band)\s+(not|never)\s` over the prose (do not require the comma, and keep digits in scope: ", not 31." was a real finding), then judge each candidate in context; a sentence asserting X by denying Y is a hit.
- Anthropomorphic placement verbs: sweep the full lemma sets `live/lives/lived/living`, `sit/sits/sat/sitting`, `hang/hangs/hung/hanging`, `want/wants/wanted/wanting` (base forms included, not just three inflections; this list is the authoritative lemma set the waivers cite) and judge each: banned for code, data, and physical devices alike in authored prose per the settled waiver; a userspace process as a real actor is exempt ("the reader wants the buffer"), the adjective "live" ("the live counter") is not the verb, and verbatim quotes keep their verbs. Confirm "walk" appears only for traversing a data structure.
- "vtable": zero occurrences in authored prose.
- Question headings: zero hits for `^#{2,4} (Why|How|Where|What)` and for trailing-`?` headings on the raw file (headings are legitimately line-anchored).
- Bare-noun headings: read every H3/H4 in DETAILS, SUMMARY, and body sections and confirm each is a declarative what-does-what statement, never a bare noun or symbol; LINUX KERNEL catalog labels are exempt.
- Sweep case-insensitively and fence-aware, then use case as evidence when judging. The page passes at zero unadjudicated findings, with exempt constructs left unreworded.
