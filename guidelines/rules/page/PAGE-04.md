# PAGE-04: Link anchoring and exhaustive span linking

> Was: 7m. Link anchoring and exhaustive span linking

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
