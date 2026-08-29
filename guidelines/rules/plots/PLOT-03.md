# PLOT-03: Journey- or model-first organization

> Was: 7u. Journey- or model-first organization

**Problem:** The catalog-first page — one DETAILS heading per symbol, walked in declaration order — is a reference catalog wearing an explanation's clothes. A page is organized as a journey or around a model, never as a catalog of its symbols: LINUX KERNEL is the reference catalog, where a list is correct; DETAILS is not. Its sections are the chapters of a journey (the phases of a process traced start to end) or the facets of a model (the roles, states, or classes of the mechanism), and each cataloged symbol appears inside the chapter or facet where it does its work, shown there with its definition and usage excerpts.

**Rule:** Choose the spine from the topic. An operation or pipeline (a syscall path, a page fault, a split or merge, a device probe, an on-disk or on-wire translation) is a JOURNEY: organize DETAILS by its phases in run order. A static object or state space (a struct, a flag set, a lock's states, a power-state set) is a MODEL: organize by roles, states, or classes. An object with an operation on it leads with the model, then traces the operation as a journey through it.

**Rule:** The test is the DETAILS headings. Headings one-per-symbol in catalog order are the catalog-first failure and are reorganized, every symbol re-homed inside the phase or facet where it acts. Headings naming phases ("the boot table is parsed before the namespace exists") or facets ("the per-VMA lock state") are journey- or model-first. Reorganization never weakens coverage: every cataloged symbol still appears in DETAILS with definition and usage excerpts (3b item 1) — organization changes WHERE a symbol is shown, not WHETHER. A symbol that fits no phase or facet signals wrong organization or wrong catalog membership, never license for a stray per-symbol section.

**Rule:** Diagrams obey the same spine (7g): a figure depicts the page's journey (pipeline, sequence, before-and-after, lifecycle) or its model (state machine, topology, taxonomy); where the journey or model is large enough to carry the page, one figure shows it whole as the reader's map. A figure that is only symbols in boxes with no process or relationship is a catalog in visual form — redrawn to show the relationship, or dropped.

This rule and 7s are a pair: 7s puts the model at the top of the page, 7u organizes the body around it.
