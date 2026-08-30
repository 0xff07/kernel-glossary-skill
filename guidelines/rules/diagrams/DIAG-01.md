# DIAG-01: General ASCII diagram principles (mandatory)

> Was: 7g. General ASCII diagram principles (mandatory)

**INPUT:** Every figure fence on the page, and the material's drawable relationships (layouts, topologies, reshaping operations, state sets) for the justification test in both directions.

**OUTPUT:** Figures exactly where a spatial, temporal, or transformational relationship earns them (over-drawing deleted, under-drawing filled), each in the mandated geometry (Unicode box-drawing only, titled sub-diagrams, 4-space indent, under 80 columns, junction-aligned rows) with a prose paragraph above its fence; delivered with per-figure sign-off naming the relationship conveyed and the catalog pattern followed.

1. Only include an ASCII diagram when it conveys a spatial or temporal relationship that prose cannot express efficiently.
2. A diagram earns its place when it shows physical layout, parallel structure across multiple lanes, a non-linear graph, an address space, a bit field, a ring/queue with head and tail pointers, or two views of the same data side by side.
3. Concrete examples that justify a diagram include the GPE register block mapped to its per-bit event_info slots, the buddy allocator's per-order freelist columns, a doorbell BAR partitioned across IPs, or a tree of devices with parent/child arrows.

4. Do not draw a diagram for a simple linear sequence of function calls, a top-down call chain, a state machine with two states, or any flow that reads naturally as a paragraph or as a fenced code block of pseudocode.
5. "Function A calls B which calls C" is prose, not a diagram.
6. A single arrow chain in a box is not a diagram.
7. If a reader would understand the same content faster from one sentence of declarative prose, write the sentence and delete the diagram.

8. The test above rejects gratuitous figures; it is not a budget of one per page, and under-drawing is as real a gap as over-drawing.
9. Where the material holds more than one distinct drawable relationship, draw a figure for each: a struct's field or bit layout, the larger structure it sits in, the shape of an operation that rewrites it, and the states it moves through are four different figures, and a page whose material has all four carries all four (the sample corpus reaches four figures on one page).
10. One case is easy to under-draw and worth naming: an operation that changes the shape of a data structure (a split, a merge, an insertion, a teardown, a fork, an in-place encode) earns a before-and-after or pipeline figure showing the structure on each side of the change (the before / after transformation and data dependency patterns), and that figure is usually the most clarifying one on such a page.
11. This does not loosen the restraint above; it says that when real spatial, temporal, or transformational structure is present, the default is to draw it rather than leave it in prose.

12. A figure depicts a journey or a model, never a catalog.
13. It shows a process (a pipeline, a sequence, a before-and-after, a lifecycle) or a structure and its relationships (a state machine, an object topology, a taxonomy, a memory or bit layout).
14. On a page organized around a journey or a model, the primary figure shows that spine whole, so the reader holds a map of the same shape the prose traces.
15. A figure that only lists symbols in boxes with no process or relationship among them is a catalog in visual form; redraw it to show the relationship or drop it.

16. When a diagram is used, follow the style established in the sample pages (for example the page-table-entry bit layouts and slot-map figures in `guidelines/reference/samples/page-encoding-pgtable-entries.md`) and the reference figures in the bit-layout and pattern catalogs.
17. Use Unicode box-drawing characters (`┌ ┐ └ ┘ │ ─ ├ ┤ ┬ ┴ ┼`) and `▼ ▲ ◀ ▶` for arrows.
18. Title each sub-diagram with a short heading underlined by a `────` rule.
19. Multiple sub-diagrams may share one fenced block when each has its own titled section.
20. Indent the whole figure 4 spaces inside the fenced block so it reads as a figure, not as text.
21. Keep every line under 80 columns so the figure renders without wrapping in plain-text views.

22. Pure ASCII `\`, `/`, and `|` are never used as box-drawing or connector characters.
23. The `/` and `|` characters are acceptable inside the figure only as English word separators ("ROOT_PORT / DOWNSTREAM"), as C bitwise expressions (`LBMS | LABS`), or inside reproduced kernel source.
24. All box sides, corners, junctions, and arrows are Unicode.

25. Diagram annotations (legends, per-bit meanings, code-like pseudocode lines, comments below the figure) live inside the same fenced block as the figure.
26. The forbidden-phrase rules do not apply to text inside fenced code blocks, including ASCII figure blocks, but the prose surrounding the figure outside the fence still does.

Four shapes are banned outright whatever the material, and the ban overrides any catalog pattern a figure would otherwise be drawn to.

**PASS CRITERIA:**

1. For each figure, name the spatial, temporal, or transformational relationship it conveys (a physical layout, parallel lanes, a non-linear graph, an address space, a bit field, a ring with head and tail, two views of one data structure). A figure for a linear call chain, a two-state toggle, or anything one declarative sentence conveys is deleted and the sentence written instead.
2. Check under-drawing as seriously as over-drawing: enumerate the material's distinct drawable relationships (a field or bit layout, the containing structure, an operation that reshapes it, the state set) and confirm each one present carries its own figure. A split, merge, insertion, teardown, fork, or in-place encode without a before-and-after or pipeline figure is a coverage gap.
3. Confirm each figure depicts a journey or a model, never a catalog: a figure that only lists symbols in boxes with no process or relationship among them is redrawn to show the relationship or dropped, and on a journey- or model-organized page the primary figure shows that spine whole.
4. Geometry, per figure: Unicode box-drawing and arrow characters only, with ASCII `\`, `/`, `|` never used as sides, corners, junctions, or connectors (`/` and `|` pass only as English word separators, C bitwise expressions, or reproduced kernel source); each sub-diagram titled with a `────` underline; the whole figure indented 4 spaces inside its fence; every line under 80 columns (the one exception is a register drawn as a single row with L-connectors); each content-row `│` landing on a `┬` or `┴` junction of the border rows above and below it; and a prose paragraph sitting immediately above the figure's opening fence, so no fenced block opens against another.
5. Sweep the figure's annotation text: the phrase-class sweeps are lifted inside the fence, but the anthropomorphic-verb, em-dash, and negative-construction bans still bind it, and the prose outside the fence is bound by every rule.
6. Sign off per figure, recording the relationship it conveys and the named catalog pattern it follows.
