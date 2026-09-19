# The Linux-kernel profile

writing.md says how a page explains; this file says what a Linux-kernel page is made of: the sources it may use, the sections it carries and their forms, the provenance of its excerpts, its links, the coverage a kernel construct demands, and where the subsystem conventions live. Every requirement is marked with its slug. This is the first step toward a domain profile, not the whole of one: writing.md still names semcode and C excerpts in places, template.md is a kernel page's skeleton, and the QA scripts check C fences and Elixir links. A profile for another domain would supply this file's six sections, the template, the source and version resolution the scripts use, the citation URL rules and the checks that apply; those dependencies move out of the shared files as a second domain makes them concrete. For another Linux subsystem, the subsystem map suffices while its fields do.

## Sources and the documented version [sources]

1. [sources.on-disk] Every fact comes from the local kernel tree at the documented version, read on disk: never the web, never memory, never another page.
2. [sources.one-version, qa] The version is one value used everywhere, the one SKILL.md resolves from the input: every Elixir URL embeds it, every claim is checked at it, the scripts run against the tree checked out at its tag, and a campaign pins it with its commit. The rule checks the URLs, and the engine's input check binds the tree's tag to them.

3. [sources.semcode-first] Research runs with the semcode tools first (`find_function`, `find_type`, `find_callers`, `find_calls`, `find_callchain`, `grep_functions`, `find_commit`, `dig`) and with Grep and Read for what they do not reach (macros in headers, `Documentation/`, Kconfig); a machine without an index falls back to Grep and Read against the pinned tree and says so in the worksheet.

## The page's sections [sections]

1. [sections.caution, qa] The H1 is the topic name only. Directly under it stands this blockquote, byte for byte:

```
> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.
```

2. [sections.order, qa] Then, in order: the lead, `## SUMMARY`, `## SPECIFICATIONS`, `## COVERAGE`, `## DOCUMENTATION`, `## OTHER SOURCES`, the subsystem's section-six heading (REGISTERS, METHODS, PRIMITIVES or INTERFACES, omitted when the entry says none) and `## DETAILS`. `guidelines/template.md` shows the skeleton.

3. [sections.specifications] SPECIFICATIONS cites the normative source of the model, each entry `<spec name>, section <N.N>: <section title>`, found in source comments and commit messages; when no specification applies, the section says so. A model no specification defines is a disclosed synthesis that names its on-disk sources and keeps every fact under it cited.
4. [sections.coverage-form, qa] COVERAGE catalogs the symbols the page owns and excerpts, and only those, under `###` labels, one bullet per symbol in the form `` - [`'\<struct foo\>':'path/to/file.h'`](https://elixir.bootlin.com/linux/v7.0/source/path/to/file.h#L45): one-line role ``, with the `struct` or `enum` keyword inside the angle brackets. A symbol the page will not excerpt is linked in prose and not cataloged. A symbol another page owns is reached across the boundary to whatever depth this page's narrative needs, excerpted where that depth demands it and located in the worksheet's scope closure, and it stays out of the catalog: a bullet would claim the symbol and demand a COMPLETENESS row for another page's material.

5. [sections.documentation] DOCUMENTATION holds every `Documentation/` reference, each `` - [`Documentation/x/y.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/x/y.rst): brief description ``; none goes to OTHER SOURCES.
6. [sections.other-sources, qa] OTHER SOURCES holds mailing-list URLs taken byte for byte from a `Link:` trailer in `git log` or from semcode `dig`, each `[<commit subject> (commit <abbreviated sha>)](<trailer URL>)`; a commit without a trailer is cited in prose by sha and subject and gets no entry. Never construct, guess or normalize a URL.

7. [sections.details] DETAILS carries the walkthroughs: every catalog symbol's definition and a concrete usage as fenced C, then explained, never described in prose alone.

## Excerpt provenance [provenance]

1. [provenance.form, qa] Every fenced C block opens with `/* path/from/tree/root.c:LINE */` naming its first reproduced line, and a short annotation may follow the number. A block stitching several places delimits each unit with its own provenance comment. The one elision, a run of members dropped from a long definition, is a standalone `... /* N lines, to :LINE */` ([excerpts.contiguity]). A non-code fence carries no provenance; it is a figure when a line carries a drawing character and a quotation or listing otherwise.

## Links [links]

1. [links.definition-line, qa] Every kernel symbol outside a fence (function, macro, struct, enum, typedef, argument forms included) is an Elixir link to its definition line at its first occurrence in each paragraph, table cell or list item, later occurrences in the same paragraph left as bare spans so the line stays readable, table cells included, and `struct` and `enum` keep their keyword everywhere. A call site, branch or field assignment is a location link whose text is `path:first-last` for the run of lines the prose describes, or `path:line` where one line is the site, its URL anchored at the first line; prose that enumerates call sites carries one per site. One base, `https://elixir.bootlin.com/linux/<version>/source/`, across the page.

2. [links.always-linked] Always linked: `CONFIG_*` options to the `config X` line of the declaring Kconfig file; generic primitives (`READ_ONCE()`, `memcpy()`, `rcu_read_lock()`, `atomic_read()`) to the definition relevant to the architecture; a field path `a->b` or `foo.bar` to the field's declaration line; an ops-struct member named in prose to its line in the struct. Precedent never excuses a bare span, and pre-existing bare spans of the same family are fixed in the same pass.
3. [links.bare-spans, qa] Left bare, in prose and table cells alike: a symbol linked earlier in the same paragraph; C keywords and operators; locals, parameters and goto labels quoted from an excerpt; literal and error values (`true`, `false`, `0`, `-EINVAL`, `NULL` as a value); literal strings a function prints or logs; a value or expression span, which links a constituent symbol where one exists; `/proc`, `/sys`, sysctl and other path strings; Kconfig fragments and keywords (`=y`); tracepoint field names; a wildcard family name (`VM_*`) when its members are linked nearby; commit hashes; `name(2)` notation when the entry point is linked elsewhere; a designated initializer's member name, whose citation is a location link at the initializer line; a symbol verified absent from the tree, whose absence the prose states. A spec-defined or hardware name (`_PS0`, `SLP_EN`) stays bare with a note saying so. Any other bare span is linked or recorded with its reason, a span in the descriptive text of a catalog bullet included: only the entry's own linked symbol belongs to the catalog, and the rest of the bullet is closed like prose.

## Coverage of kernel constructs and driver examples [coverage]

1. [coverage.constructs] Cite every site that exhibits a behavior, with a location link at the mention and the sites the walkthrough explains as excerpts; when the set is too large, cite a representative spread and state the total. Cover the structs, enums and typedefs that hold the state and the helpers that allocate, initialize, read, modify and destroy them; the lifecycle in full (allocation, initialization, teardown order, serializing locks, reference counting with the put that frees, state transitions and their drivers, notification mechanisms, deferred work and the ordering between them); and every hard-coded limit (timeout, retry count, error cap, buffer or queue size, poll or backoff interval) with its value, its defining symbol or literal and its file and line, reproduced where it governs a walked path. The last of the seven acceptance lines of checking.md [judgement], [judgement.constructs], records that this was done.
2. [coverage.scope-closure, qa] Every anchor symbol and behavior the catalog row (or the request) names has a location on the page or a scope reduction recorded with its reason above the worksheet's catalog table; the catalog table starts from the catalog and cannot supply this, and removing a catalog entry never discharges the obligation. The coverage script resolves the row's spans against the tree under the directories the page cites and prints the ones the page never names; a symbol accounted for in the scope closure is a note.

3. [coverage.recency, qa] A driver cited as an example has substantive commits within three years of the documented version, ignoring renames and churn, and is described from its own source on the page (vendor, bus or class, file and callback), never by analogy to another driver or page. Where no active driver exercises the behavior, say so.

## Subsystem conventions [conventions]

1. [conventions.subsystem-entry] `guidelines/subsystems.md` carries, per subsystem, the tag, the `docs/` directory, the kernel paths, the specification and the section-six heading (REGISTERS, METHODS, PRIMITIVES or INTERFACES); the prep pass resolves the page's entry, and the page follows it.
