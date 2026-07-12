# 7m. Link anchoring and exhaustive span linking (mandatory)

Rule IDs (3a-3c, 7, 7a-7r) resolve via `guidelines/rules/INDEX.md`.

## Constructing Elixir cross referencer URLs

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

## Anchoring and exhaustiveness

This rule extends the every-symbol-linked rule in 7f with anchor selection and exhaustiveness. It is what the numbers in `guidelines/reference/measured-criteria.md` ("Samples and measured criteria") call links per page.

- A link whose text is a symbol name (`` `vma_start_read()` ``, `` `struct mm_struct` ``, `` `VM_LOCKED` ``, and the LINUX KERNEL `` `'\<sym\>':'path'` `` form) anchors at the symbol's DEFINITION line, so the reference stays valid for `git log -L` and survives unrelated churn elsewhere in the file. It does not anchor at a call site, a comment mention, or a line inside some other function's body, even when that line is what the surrounding prose discusses.
- A reference to a specific non-definition place in code (a call site, one branch, one field assignment) is written as a file-location link whose text is the path and line, for example [`mm/vma.c:717`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L717). Prose that enumerates call sites uses one location link per site, so every count in the page is checkable one click deep.
- Every occurrence of every kernel symbol outside fenced blocks is linked, including repeats of the same symbol on the same page. The exhaustive pass includes the classes that are easiest to skip: `CONFIG_*` options link to the `config X` line of the Kconfig file that declares them; generic primitives (`READ_ONCE()`, `memcpy()`, `rcu_read_lock()`, `atomic_read()`, and the like) link to the definition relevant to the documented architecture; a field path written as `a->b` or `foo.bar` links to the field's declaration line inside the struct definition; an ops-struct member named in prose ("the `fault` hook") links to that member's line in the ops struct definition.
- Settled exemptions (spans that may stay bare): C keywords and operators; local variables, parameters, and goto labels quoted from an excerpt; literal and error values (`-EINVAL`, `NULL` as a value); `/proc`, `/sys`, and sysctl path strings; Kconfig syntax fragments (`=y`); tracepoint field names; a wildcard family name (`VM_*`) when the members it stands for are linked nearby; commit hashes; the `name(2)` man-page notation when the page links the syscall's kernel entry point elsewhere; and symbols verified absent from the documented tree (state the absence in prose).
- Precedent never overrides the rule. "Other pages leave `CONFIG_FOO` bare" or "this page already has thirty bare `READ_ONCE()` spans" is not a reason to leave the next one bare; the rule wins, and the pre-existing in-family spans get fixed in the same pass.
