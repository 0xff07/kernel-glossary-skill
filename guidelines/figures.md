# Figures

When a figure earns its place, the shapes that fail, the geometry every figure keeps, the register styles and the pattern index; checking.md [figure-check] says what is checked and how each class of breakage is repaired.

## When a figure is drawn [drawing]

1. [drawing.when] Draw a figure where a spatial, temporal, transformational or quantitative relationship would otherwise cost the reader effort to remember, recover or reconstruct: a physical layout, parallel lanes, a non-linear graph, an address space, a bit field, a ring with head and tail, two views of one structure, a quantity compared by length or height on one axis. A relationship can be expressible in prose and still benefit from a local figure; prose alone stays where one clear sentence does the same work more directly.
2. [drawing.never-chains] A relationship one sentence states stays prose: a linear or top-down call chain ("A calls B which calls C"), a two-state toggle, or a flow that reads as a paragraph; a single arrow chain in a box asserts nothing a sentence lacks.
3. [drawing.each-relationship] The test is not a budget of one per page, and under-drawing is as real a gap as over-drawing. Where the material holds several drawable relationships, each gets its figure: a field or bit layout, the structure it sits in, an operation that reshapes it, and its state set are four figures. Containment and connections, ownership and data mappings, and partitioning and state changes are drawn locally, beside the explanation that needs them, when the drawing gives a concrete reading benefit; no subsection needs a figure by default.
4. [drawing.reshaping] An operation that changes the shape of a structure (a split, merge, insertion, teardown, fork, in-place encode) earns a before-and-after or pipeline figure showing the structure on each side, and it is usually the most clarifying figure on such a page. Creation and attachment, ownership transfer, representation change, splitting and merging, and recovery and teardown are the prompts the pattern index matches to rows.
5. [drawing.journey-or-model] A figure depicts a journey or a model, never a catalog: a pipeline, a sequence, a before-and-after, a lifecycle, or a structure and its relationships. On a page organized around a journey or model the primary figure shows that spine whole, and a local figure shows the objects and boundaries of the current operation; the two may share objects, the local one keeps its orientation within the larger model, and omitted branches never turn a partial view into a claim of completeness. Figures of successive stages keep names, positions and directions where those are unchanged and update what the operation changes.
6. [drawing.assertions] A figure's arrows and boundaries assert relationships and its labels assert behavior; the source beside it supports them, and its placement keeps the excerpts it prepares or follows intact. A local figure stays complete: object names, directions, boundaries and enough notation to be read where it stands, with nothing added to reach a line count and nothing cut to shrink it.

7. [drawing.legend, qa] A figure names a function only through a mark from one of the five alphabets of [drawing.marks], resolved by a legend inside the fence beneath the drawing, one entry per line in the form `① name file:line  what happens there`: the mark, the function, its site, and a phrase of a few words saying what that site does to the object or decides, so the legend answers who, where and what. The drawing itself carries objects, fields, events and values, and may set a one-word verb beside a mark. The check matches the marks in the drawing to the legend's, requires every legend site to be a line an excerpt on the page reproduces and to lie in the named function, and requires the phrase; on a lifecycle figure the phrase names the field the writer sets.

8. [drawing.triggers, qa] The shapes below are drawn wherever a DETAILS subsection carries them: the table is the obligation, the pattern index the form, and a subsection that carries a shape and no figure records why the shape is not its point. The check lists such subsections from their prose and excerpts.

| the material | draw it as | exempt |
|---|---|---|
| a set of three or more named states, modes or classes the prose walks | state-transition graph, or the two-field state pair when the state is a relation between two fields | a set the page only tabulates, no transition described |
| two or more actors handing work to each other: parent and child router, upstream and downstream, host and device, producer and consumer | swimlane sequence | one call from one actor to the other |
| a definition of six or more members, or a word partitioned into named bit ranges | side-by-side struct comparison, linked structs via pointers, the two-view memory strip, or the register grid | a definition shown for the one member the paragraph is about |
| an operation that reshapes a structure: allocate and attach, insert, split, merge, tear down | before-and-after transformation | one scalar written |
| routers, adapters and tunnels in a tree, or a guard that is a place in the tree | topology with a boundary, or parent and children fan-out | a single link named |
| a field two or more functions write | the object lifecycle strip ([lifecycle]) | none |
| three or more ordered steps across two actors or two files | swimlane sequence or lifetime Gantt | the steps of one function, which the walkthrough reads |

9. [drawing.model, qa] Every page carries its model figure under the lead or in SUMMARY: the objects and the relationships the page is about, or the spine of its journey, so the reader holds the map before DETAILS; on an object page it is the lifecycle strip. The check requires one figure in the lead or SUMMARY.

10. [drawing.walk, qa] In DETAILS, the paragraph after a figure with a legend walks its marks in order, one sentence per mark, each sentence naming its mark and the function as a link at its first mention in the paragraph, so the reader goes from the drawing to the code by that paragraph and can pair every mark with its sentence; the model figure under the lead or in SUMMARY carries its legend alone. The check requires every mark of the legend named in the paragraph after the figure and every legend function linked in it, and flags a walk whose marks or functions are out of mark order.

11. [drawing.marks, qa] Five alphabets number the marks, every symbol outside the CJK blocks so a non-CJK font renders it: the circled digits `①` to `⑳`, the negative circled digits `❶` to `❿` continued by `⓫` to `⓴`, the circled capitals `Ⓐ` to `Ⓩ`, the circled small letters `ⓐ` to `ⓩ` and the double-circled digits `⓵` to `⓾`. A marked series, the pieces of one outline table or the marks of one figure, uses one alphabet, counted from its first symbol without a gap, and consecutive series in page order take the alphabets in the cycle `① ❶ Ⓐ ⓐ ⓵`, the first series of a page in circled digits, a series longer than the next alphabet skipping to the one after it, so that a `①` in one figure and a `①` in the next never name different sites while both are in view. The check lists the series in page order with their alphabets, fails a series that mixes alphabets, and lists for reading a series that skips a symbol and a series whose alphabet is not the cycle's next.

## Object lifecycle figures [lifecycle]

1. [lifecycle.when, qa] An object whose field two or more functions write, a struct the page catalogs or a field of another page's struct whose writers this page owns, has a lifecycle to draw: the object lifecycle strip when the order of the events and the intervals in which the object is inconsistent are the point, the two-field state pair when the relation between two fields is the state, one figure per object, placed in the subsection that introduces the object or under the lead when the object is the page's model. The check counts, per cataloged struct the subsystem's own sources define, the functions in those sources that assign each field, and lists an object with such a field and no Lifecycle table as a candidate; the sources are the kernel paths of the page's subsystems.md entry, or the directories the page cites when no entry matches, and a catalog entry for a member (`struct tb_nhi *nhi`) names no object.

2. [lifecycle.figure] The drawing carries the events as columns or the states as boxes, the fields and the values they take, and a mark at every write; the legend beneath names the writer and its site ([drawing.legend]); every writer of a drawn field appears, because a lifecycle with a writer missing asserts a state the code can leave. The worksheet's Lifecycle table is the figure's verified twin (worksheet.md [evidence.lifecycle]).

3. [lifecycle.order, qa] DETAILS follows the object's lifecycle: the writes the figure numbers are shown in the order of their marks, so that reading the subsections in order is reading the strip from left to right, and a page that departs from that order says why where it does. The check finds the first excerpt that shows each numbered write and flags a later mark shown before an earlier one.

## The strip test and the shapes that fail it [shapes]

1. [shapes.strip-test] Strip every label and read what is left. A figure survives when the skeleton still asserts something (this contains that, this becomes that, these ends meet here, this partitions into those, time runs this way across these actors) through a spatial property: position on an axis, a length, containment, alignment, the direction of a flow. A box is a container, not a shape; a column of boxes whose meaning is in their labels fails, and so does an axis whose positions mean nothing.
2. [shapes.banned] Four shapes fail the test however true their content, and this outranks every pattern below: a plain table, a `┌─┬─┐` grid of records by attributes, which belongs in a Markdown table (a grid is a figure only when its cells partition something); a plain function-flow graph, nodes that are all function names joined by edges that all mean "calls" (edges that mean feeds, points at, transitions to, is claimed by, gates or is written by are structure and are welcome; a swimlane that would survive deleting all but one lane is this shape wearing lanes); a plain listing of struct members, a box nothing exits; and plain text in a fence.
3. [shapes.redraw] A failed figure is redrawn into a shape that carries structure or deleted with its content folded into a table or the prose. A source excerpt and a verbatim-quotation fence are not figures and are never tested.

## Geometry [geometry]

1. [geometry.unicode, qa] Any character but an emoji may draw. The box-drawing set is the default; double borders mark emphasis or a construct of another kind, dashed lines a guide, a barrier or a second class of path, `█ ▒ ░` are fills, `▼ ▲ ◀ ▶` arrowheads, circled digits the marks a legend resolves ([drawing.legend]) and `·` a placeholder cell. Within one figure one glyph means one thing, and one kind of line is drawn with one set of glyphs. Emoji and pictographs never appear in a figure; the check fails any character of the emoji blocks and any character a variation selector turns into one.

2. [geometry.layout, qa] A figure carries a short title underlined with a `────` rule where several sub-diagrams share one fence or a subsection holds more than one figure, so a reader can tell them apart; a subsection's only figure may go untitled when the paragraph above it names what it shows. On a page the whole figure is indented four spaces inside the fence; a reference figure in the catalogue keeps the indent it has, and the writer re-indents the copy. Keep every line within 120 columns (a register drawn as a single row with L-connectors may run wider), and give every `│` something drawn to join in the row above or the row below: a trunk lands on a `┬` or `┴` of the border it meets (`╤` or `╧` on a double border), and a `│` with nothing drawn on either side is loose. Legends, per-bit meanings and comments live inside the same fence, under the drawing. A prose paragraph sits above the fence. The geometry checks measure the width and the loose verticals and fail an emoji; the title rule, the indent, the box borders, the trunk ends and the legend placement are read.

3. [geometry.bans-reach-figures] The em dash, the negative construction and the placement verbs bind figure text; the other sweeps lift inside the fence. The geometry checks behind `kg check` find the mechanical part of the breakage (an emoji, the width and a vertical joining nothing), and checking.md [figure-check] says what is read and how each class is repaired.

## Registers and bitfields [registers]

1. [registers.scope] A figure whose primary subject is a bit layout (a register, TRB, context, descriptor, packet header) follows these rules on top of the general ones; a bit strip inside a larger structural figure follows the host figure's style.
2. [registers.styles] Two styles, chosen by one test: is the thing one value, or several separate words? A register is one value at one address, however wide, and all its bits sit on one ruler; a structure is several words at successive DWORD offsets, each its own row. The DWORD-grid style writes field names inside cells and stacks `DW0`, `DW1`, ... rows, for a structure or a register whose names fit. The L-connector style, for registers only, draws one row of one-character cells and calls each named bit out below on an L-shaped leader when the register is mostly single-bit fields; a wide register whose upper bits are one uniform field may show only the interesting DWORD with a note.
3. [registers.ruler] The ruler runs from the high bit down to 0, one bit per two-column slot, in two rows (tens, then ones) whenever an index reaches two digits; the full per-bit `┌─┬...─┐` border keeps every cell aligned. DWORD labels sit in a left gutter at column 4 with the box border at column 10; `├──┬──┼──┴──┤` divider rows transition between layouts; each multi-bit cell carries its name and `(hi:lo)`; a legend beneath maps each field to its macro and cached struct field as `NAME = MACRO (meaning)`; reserved bits get no trunk; each elbow lands on its own trunk, the rightmost callout nesting first.
4. [registers.to-scale] Draw to scale by default, with a complete ruler and exact `(hi:lo)` ranges. Draw schematic only where a boundary has no fixed number (a field that ends at MAXPHYADDR, a generic pattern): name the variable boundary `N` or `M`, join the gaps with `...`, and size cells for their labels. Exact positions on a generic pattern are fake precision. Every range, constant and macro in the figure and its legend is a behavioral claim, verified against the reproduced definition.
5. [registers.section, qa] REGISTERS holds the registers, bitfields and fields the page's paths touch, each drawn in one of the two styles above with the prose beside it saying what each field decides on this page's paths. The functions that read or write them are catalogued in COVERAGE where this page owns them and named in DETAILS at the stage they run; a register no other page catalogs is this page's catalog entry, with its definition excerpt, under a COVERAGE heading that names the register block and its header. The section carries no table: a row per register with its helper, bits and meaning is the shape [drawing.triggers] names for a word partitioned into named bit ranges, and it is drawn. The check lists for reading a table under REGISTERS and a REGISTERS that links register definitions and draws none.

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
