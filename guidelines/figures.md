# Figures

When a figure earns its place, the shapes that fail, the geometry every figure keeps, the register styles and the pattern index; checking.md [figure-check] says what is checked and how each class of breakage is repaired.

## When a figure is drawn [drawing]

1. [drawing.when] Draw a figure where a spatial, temporal, transformational or quantitative relationship would otherwise cost the reader effort to remember, recover or reconstruct: a physical layout, parallel lanes, a non-linear graph, an address space, a bit field, a ring with head and tail, two views of one structure, a quantity compared by length or height on one axis. A relationship can be expressible in prose and still benefit from a local figure; prose alone stays where one clear sentence does the same work more directly.
2. [drawing.never-chains] A relationship one sentence states stays prose: a linear or top-down call chain ("A calls B which calls C"), a two-state toggle, or a flow that reads as a paragraph; a single arrow chain in a box asserts nothing a sentence lacks.
3. [drawing.each-relationship] The test is not a budget of one per page, and under-drawing is as real a gap as over-drawing. Where the material holds several drawable relationships, each gets its figure: a field or bit layout, the structure it sits in, an operation that reshapes it, and its state set are four figures. Containment and connections, ownership and data mappings, and partitioning and state changes are drawn locally, beside the explanation that needs them, when the drawing gives a concrete reading benefit; no subsection needs a figure by default.
4. [drawing.reshaping] An operation that changes the shape of a structure (a split, merge, insertion, teardown, fork, in-place encode) earns a before-and-after or pipeline figure showing the structure on each side, and it is usually the most clarifying figure on such a page. Creation and attachment, ownership transfer, representation change, splitting and merging, and recovery and teardown are the prompts the pattern index matches to rows.
5. [drawing.journey-or-model] A figure depicts a journey or a model, never a catalog: a pipeline, a sequence, a before-and-after, a lifecycle, or a structure and its relationships. On a page organized around a journey or model the primary figure shows that spine whole, and a local figure shows the objects and boundaries of the current operation; the two may share objects, the local one keeps its orientation within the larger model, and omitted branches never turn a partial view into a claim of completeness. Figures of successive stages keep names, positions and directions where those are unchanged and update what the operation changes.
6. [drawing.assertions] A figure's arrows and boundaries assert relationships and its labels assert behavior; the source beside it supports them, and its placement keeps the excerpts it prepares or follows intact. A local figure stays complete: object names, directions, boundaries and enough notation to be read where it stands, with nothing added to reach a line count and nothing cut to shrink it.

## The strip test and the shapes that fail it [shapes]

1. [shapes.strip-test] Strip every label and read what is left. A figure survives when the skeleton still asserts something (this contains that, this becomes that, these ends meet here, this partitions into those, time runs this way across these actors) through a spatial property: position on an axis, a length, containment, alignment, the direction of a flow. A box is a container, not a shape; a column of boxes whose meaning is in their labels fails, and so does an axis whose positions mean nothing.
2. [shapes.banned] Four shapes fail the test however true their content, and this outranks every pattern below: a plain table, a `┌─┬─┐` grid of records by attributes, which belongs in a Markdown table (a grid is a figure only when its cells partition something); a plain function-flow graph, nodes that are all function names joined by edges that all mean "calls" (edges that mean feeds, points at, transitions to, is claimed by, gates or is written by are structure and are welcome; a swimlane that would survive deleting all but one lane is this shape wearing lanes); a plain listing of struct members, a box nothing exits; and plain text in a fence.
3. [shapes.redraw] A failed figure is redrawn into a shape that carries structure or deleted with its content folded into a table or the prose. A source excerpt and a verbatim-quotation fence are not figures and are never tested.

## Geometry [geometry]

1. [geometry.unicode, qa] Any character may draw: the box-drawing block (`┌ ┐ └ ┘ │ ─ ├ ┤ ┬ ┴ ┼`, the double `═ ║ ╔ ╗ ╚ ╝ ╤ ╧` for emphasis or a construct of another kind, the dashed `╎ ┆ ╏` for a guide, a barrier or a second class of path, `╳` for a crossing), the block elements `█ ▒ ░` as fills, the arrows and geometric shapes (`▼ ▲ ◀ ▶ ►`, `◉`) as arrowheads and markers, plain ASCII (`+ - | / \ < > ^ v`), circled digits (`① ②`) as markers a one-line legend resolves, and `·` for a placeholder cell. Within one figure one glyph means one thing, and one kind of line is drawn with one set of glyphs. Emoji and pictographs never appear in a figure; the check fails any character of the emoji blocks and any character a variation selector turns into one.

2. [geometry.layout, qa] A figure carries a short title underlined with a `────` rule where several sub-diagrams share one fence or a subsection holds more than one figure, so a reader can tell them apart; a subsection's only figure may go untitled when the paragraph above it names what it shows. On a page the whole figure is indented four spaces inside the fence; a reference figure in the catalogue keeps the indent it has, and the writer re-indents the copy. Keep every line within 120 columns (a register drawn as a single row with L-connectors may run wider), and give every `│` something drawn to join in the row above or the row below: a trunk lands on a `┬` or `┴` of the border it meets (`╤` or `╧` on a double border), and a `│` with nothing drawn on either side is loose. Legends, per-bit meanings and comments live inside the same fence, under the drawing. A prose paragraph sits above the fence. The geometry checks check the ASCII connectors, the width and the loose verticals; the title rule, the indent, the box borders, the trunk ends and the legend placement are read.

3. [geometry.bans-reach-figures] The em dash, the negative construction and the placement verbs bind figure text; the other sweeps lift inside the fence. The geometry checks behind `kg check` find the mechanical part of the breakage (an emoji, the width and a vertical joining nothing), and checking.md [figure-check] says what is read and how each class is repaired.

## Registers and bitfields [registers]

1. [registers.scope] A figure whose primary subject is a bit layout (a register, TRB, context, descriptor, packet header) follows these rules on top of the general ones; a bit strip inside a larger structural figure follows the host figure's style.
2. [registers.styles] Two styles, chosen by one test: is the thing one value, or several separate words? A register is one value at one address, however wide, and all its bits sit on one ruler; a structure is several words at successive DWORD offsets, each its own row. The DWORD-grid style writes field names inside cells and stacks `DW0`, `DW1`, ... rows, for a structure or a register whose names fit. The L-connector style, for registers only, draws one row of one-character cells and calls each named bit out below on an L-shaped leader when the register is mostly single-bit fields; a wide register whose upper bits are one uniform field may show only the interesting DWORD with a note.
3. [registers.ruler] The ruler runs from the high bit down to 0, one bit per two-column slot, in two rows (tens, then ones) whenever an index reaches two digits; the full per-bit `┌─┬...─┐` border keeps every cell aligned. DWORD labels sit in a left gutter at column 4 with the box border at column 10; `├──┬──┼──┴──┤` divider rows transition between layouts; each multi-bit cell carries its name and `(hi:lo)`; a legend beneath maps each field to its macro and cached struct field as `NAME = MACRO (meaning)`; reserved bits get no trunk; each elbow lands on its own trunk, the rightmost callout nesting first.
4. [registers.to-scale] Draw to scale by default, with a complete ruler and exact `(hi:lo)` ranges. Draw schematic only where a boundary has no fixed number (a field that ends at MAXPHYADDR, a generic pattern): name the variable boundary `N` or `M`, join the gaps with `...`, and size cells for their labels. Exact positions on a generic pattern are fake precision. Every range, constant and macro in the figure and its legend is a behavioral claim, verified against the reproduced definition.

## Pattern index [patterns]

Match a justified figure to a row by its "reach for it when" column, record the pattern at sign-off, and reach for a new shape only when no row fits, recording why. Then read the matched row's file under `references/figures/`, and no other, before drawing: each carries the pattern's notes and one or two reference figures. The reference figures below show the shape of the families used most; copying the shape and substituting names is usually enough.

| pattern | reach for it when | file |
|---|---|---|
| parent + N children fan-out | one parent spawns multiple typed children; identity comes from a parent field | `references/figures/parent-n-children-fan-out.md` |
| sparse slot map with conditional backing | a uniform index space where each slot may or may not have a backing object | `references/figures/sparse-slot-map-with-conditional-backing.md` |
| boxed flowchart with decision nodes | 3+ sequential decision points with side effects and back-edges | `references/figures/boxed-flowchart-with-decision-nodes.md` |
| side-by-side struct comparison | two related types meet at a third operation (match, encode/decode) | `references/figures/side-by-side-struct-comparison.md` |
| linked structs via field-level pointers | the field-level pointer topology between existing structs is the point | `references/figures/linked-structs-via-field-level-pointers.md` |
| N-to-M source/destination mapping | disjoint inputs feed rows of one tabular destination | `references/figures/n-to-m-source-destination-mapping.md` |
| queue / ring between two stages | producer and consumer communicate through a bounded buffer | `references/figures/queue-ring-between-two-stages.md` |
| data dependency (inputs feed a transform) | source structs are read by a function that populates a destination struct | `references/figures/data-dependency-inputs-feed-a-transform.md` |
| before / after transformation | an operation reshapes one data structure; show it on each side of the change | `references/figures/before-after-transformation.md` |
| signal-timing / waveform | where a bit or sample lands in time relative to a clock or frame edge | `references/figures/signal-timing-waveform.md` |
| swimlane sequence (actors × time) | several actors hand work to each other and cross-actor ordering is the point | `references/figures/swimlane-sequence-actors-time.md` |
| state-transition graph | an object moves through named states with back-edges and self-loops | `references/figures/state-transition-graph.md` |
| directed graph / DAG | a signal or dependency graph with fan-in/fan-out plus side-attached nodes | `references/figures/directed-graph-dag.md` |
| register / address-offset map | registers at fixed offsets, or a block repeating at base + stride · index | `references/figures/register-address-offset-map.md` |
| layered stack / membrane | layers stack and call through named API boundaries | `references/figures/layered-stack-membrane.md` |
| ordered level ladder | a value moves through strictly-ordered levels and travel direction matters | `references/figures/ordered-level-ladder.md` |
| refcount with threshold actions | a refcount gates hardware action only at the 0↔1 edge transitions | `references/figures/refcount-with-threshold-actions.md` |
| cyclic ring buffer with position pointers | two pointers chase each other around one wrapping buffer | `references/figures/cyclic-ring-buffer-with-position-pointers.md` |
| frame / bandwidth partition grid | one frame of a shared medium divides into slots claimed by entities | `references/figures/frame-bandwidth-partition-grid.md` |
| values on one scale | several values are positions on one axis with a floor or a ceiling, and where each lands relative to the others matters | `references/figures/values-on-one-scale.md` |
| topology with a boundary | a guard or a policy is a place in the device tree (a depth limit, a per-port bit), and which rule can reach a device depends on where it sits | `references/figures/topology-with-a-boundary.md` |
| nested spans | what holds true inside a bracket (a lock held, a feature off) around an operation, with brackets nested | `references/figures/nested-spans.md` |
| race window | one path acts on what it read earlier while another path changes it in between | `references/figures/race-window.md` |
| lifetime Gantt | who may touch an object changes at named handovers, and the count is the sum of the holders | `references/figures/lifetime-gantt.md` |
| drain | a transition waits for in-flight work to leave before it proceeds | `references/figures/drain.md` |
| two-view memory strip | one buffer seen from two address spaces, with something on each side pointing into it | `references/figures/two-view-memory-strip.md` |
| lengths against one ruler | a fixed budget must contain a sum of parts, and the failing case matters as much as the fitting one | `references/figures/lengths-against-one-ruler.md` |
| scan bar chart | a loop keeps a running maximum or minimum over a set and one member can abort it | `references/figures/scan-bar-chart.md` |
| metro map (routes over shared stations) | several ordered paths pass through one set of common stops, and which stop each path visits, skips or reverses is the point | `references/figures/metro-map-shared-stations.md` |
| router stack with tunnel tracks | routers in a chain, and which adapter each tunnel leaves and enters, with the hub's own switch or hub between one tunnel and the next | `references/figures/router-stack-tunnel-tracks.md` |
| protocol columns through a router stack | the passage of one protocol's traffic through a router: protocol adapter, lane adapters, link, lane adapters, protocol adapter | `references/figures/protocol-columns-router-stack.md` |
| object lifecycle strip | one object's fields are written by different functions at named events, and the order and the inconsistent intervals are the point | `references/figures/object-lifecycle-strip.md` |
| two-field state pair | an object's state is the relation between two of its fields, and numbered actions move it between the settled and the divergent state | `references/figures/two-field-state-pair.md` |

A sparse slot map is neither a fan-out nor an N-to-M mapping; swimlane cells carry the state each actor reaches, never the next callee; data-dependency endpoints are structs and its arrows mean feeds or populates; a before-and-after keeps the identical cell style on both sides so the change reads as a diff; flowchart boxes name conditions and effects, never callees; an annotation that would hang off the right edge moves beneath the drawing inside the fence. Input-decode material gets no figure, neither a grid of inputs against an outcome nor a decode tree of labels joined by arrows: a flat input-to-outcome product is a Markdown table, a nested one is prose, and a value tested against a limit is drawn to scale only when the magnitudes are the page's own facts. Threshold-refcount material is a rung ladder, never a grid.

## Register reference figures [register-figures]

A structure drawn as stacked DWORDs, the DWORD-grid style.

```
    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │       device_id (31:16)       │       vendor_id (15:0)        │
          ├───────────────┬─┬─────┬───────┴───┬───────────┬───────────────┤
    DW1   │   revision    │R│depth│ max_port  │ upstream  │  cap_offset   │
          │    (31:24)    │ │22:20│  (19:14)  │  (13:8)   │     (7:0)     │
          ├───────────────┴─┴─────┴───────────┴───────────┴───────────────┤
    DW2   │                       route_lo (31:0)                         │
          ├─┬─────────────────────────────────────────────────────────────┤
    DW3   │E│                      route_hi (30:0)                        │
          ├─┴─────────────┬───────────────┬───────────────┬───────────────┤
    DW4   │  tb_version   │   __unknown4  │     cmuv      │ plug_ev_delay │
          │    (31:24)    │    (23:16)    │    (15:8)     │     (7:0)     │
          └───────────────┴───────────────┴───────────────┴───────────────┘
```

A register of single-bit fields, the L-connector style.

```
    bit    7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │·│M│S│B│C│·│I│O│
          └─┴─┴─┴─┴─┴─┴─┴─┘
             │ │ │ │   │ │
    SMI_EVT ─┘ │ │ │   │ │
    SCI_EVT ───┘ │ │   │ │
      BURST ─────┘ │   │ │
        CMD ───────┘   │ │
        IBF ───────────┘ │
        OBF ─────────────┘

    OBF = ACPI_EC_FLAG_OBF (0x01)      IBF = ACPI_EC_FLAG_IBF (0x02)
    CMD = ACPI_EC_FLAG_CMD (0x08)      BURST = ACPI_EC_FLAG_BURST (0x10)
    SCI_EVT = ACPI_EC_FLAG_SCI (0x20)  SMI_EVT = 0x40 (firmware, no macro)
    bits 2 and 7 reserved (read 0)
```

A schematic DWORD-grid register with a variable boundary.

```
    x86-64 4-KByte-page table entry (PTE)
    ─────────────────────────────────────────
    (schematic; M = MAXPHYADDR, the boundary varies by CPU)

     63   62           52 51          M M-1              12 11          0
    ┌────┬───────────────┬─────────────┬───────────────────┬─────────────┐
    │ XD │  ignored/MPK  │  reserved   │ physical address  │    flags    │
    │(63)│    (62:52)    │  (51:M, 0)  │     (M-1:12)      │   (11:0)    │
    └────┴───────────────┴─────────────┴───────────────────┴─────────────┘

    M = MAXPHYADDR (physical-address width: 36, 39, 46, or 52)
    flags (8:0): P(0) R/W(1) U/S(2) PWT(3) PCD(4) A(5) D(6) PAT(7) G(8)
    available (11:9): AVL;  reserved bits (51:M) are 0
    the address field high bit moves with M
```
