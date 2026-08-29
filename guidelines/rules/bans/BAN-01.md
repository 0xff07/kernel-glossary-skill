# BAN-01: Core writing bans

> Was: 7. Core writing bans

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
