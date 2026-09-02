# PLOT-01: Domain-model layer

> Was: 7s. Domain-model layer

**INPUT:** The lead, SUMMARY, and SPECIFICATIONS sections, plus the model's sources: the governing specification where one exists, otherwise the kernel's own materials (the code, enumerating comments and doc-comments, the relevant `Documentation/` pages, and the introducing series).

**OUTPUT:** The topic's model stated before DETAILS: spec-defined and mapped onto the kernel constructs, or a disclosed synthesis naming its materials with every fact under it still individually cited; delivered with the model's sources recorded at sign-off.

**Problem:**

1. A page that opens straight into per-symbol definitions leaves the reader to reverse-engineer the model the page exists to convey — the difference between a reference catalog and an explanation.
2. A page teaches the subsystem's model of its topic: the states an object moves through and their transitions, the phases of a process, the taxonomy its parts fall into, and the rules that govern these.
3. State the model as a model, in the lead and SUMMARY and ahead of the DETAILS walkthroughs, and let it organize the body rather than sit as a preamble to a per-symbol catalog.

**Rule:**

1. The model's source decides how it is written.
2. When a normative specification fixes it (an ACPI, PCIe, USB, or hardware-manual definition of a register layout, state set, or protocol), cite the spec in SPECIFICATIONS, present the model as the spec defines it, and map the kernel's constructs onto it (the spec-semantics-paired-with-kernel-slots form), so the reader learns a state's specified meaning and the constant that carries it together.
3. When no specification defines it — the common case for pure-software subsystems — the model is a synthesis assembled from the kernel's own materials: the code, the enumerating comments and struct doc-comments, the relevant `Documentation/` pages, and the commit messages of the introducing series.
4. This is the one place a page states more than a single excerpt witnesses, licensed only under disclosure: name the materials ("Assembled from the type comment, `Documentation/mm/process_addrs.rst`, and the series that introduced the per-VMA lock, the model is ..."), keep every fact under the model separately cited, and weaken or scope anything the materials do not support.
5. The exemplar pages under `docs/sound/` show the synthesis stated up front: `docs/sound/alsa/pcm/pcm-state-machine.md` opens on the one state value and the pre/do/undo/post dispatch model before any per-symbol walk, and `docs/sound/alsa/object-model.md` opens on the card, component, PCM, stream, substream, and runtime object graph.
6. A model the tree's own materials do not support is never invented to fill the section: state what the sources establish and stop.
7. A guessed model ("the design is presumably ...") is worse than none.

**PASS CRITERIA:**

1. Confirm the lead and SUMMARY state the topic's model (the states and their transitions, the phases, or the taxonomy) before the first DETAILS walkthrough, and that the model organizes the body rather than sitting as a preamble to a per-symbol catalog.
2. Where a normative specification defines the model, confirm the spec is cited in SPECIFICATIONS and every specified state or field is presented as the spec defines it and mapped to the kernel construct that carries it.
3. Where the model is a synthesis, confirm the disclosure sentence names its materials ("Assembled from ..."), that every fact under the model still carries its own citation, and that nothing under it outruns the named materials; the synthesis stays in plain declaratives naming mechanics, with no hollow superlatives, no importance framing, and no label-colons.
4. A guessed model or "presumably" phrasing fails outright, and a topic whose materials support no model must state what the sources establish and stop.
5. Record the model's sources at sign-off.
