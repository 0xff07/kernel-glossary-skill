# DIAG-04: Other ASCII diagram patterns

> Was: 7i. Other ASCII diagram patterns


When a diagram is justified, prefer one of the named patterns below. Each pattern has a use case and a shape; copying the shape and substituting names is usually enough to produce a clean figure. Reach for a new shape only when none of these fits the spatial relationship in question.

### Use-case index

| pattern | reach for it when |
|---|---|
| parent + N children fan-out | one parent spawns multiple typed children; identity comes from a parent field |
| sparse slot map with conditional backing | a uniform index space where each slot may or may not have a backing object |
| input decode tree | a return value or branch is a deterministic function of a few input bits |
| boxed flowchart with decision nodes | 3+ sequential decision points with side effects and back-edges |
| side-by-side struct comparison | two related types meet at a third operation (match, encode/decode) |
| linked structs via field-level pointers | the field-level pointer topology between existing structs is the point |
| N-to-M source/destination mapping | disjoint inputs feed rows of one tabular destination |
| queue / ring between two stages | producer and consumer communicate through a bounded buffer |
| data dependency (inputs feed a transform) | source structs are read by a function that populates a destination struct |
| before / after transformation | an operation reshapes one data structure; show it on each side of the change |
| signal-timing / waveform | where a bit or sample lands in time relative to a clock or frame edge |
| swimlane sequence (actors × time) | several actors hand work to each other and cross-actor ordering is the point |
| state-transition graph | an object moves through named states with back-edges and self-loops |
| directed graph / DAG | a signal or dependency graph with fan-in/fan-out plus side-attached nodes |
| register / address-offset map | registers at fixed offsets, or a block repeating at base + stride · index |
| layered stack / membrane | layers stack and call through named API boundaries |
| ordered level ladder | a value moves through strictly-ordered levels and travel direction matters |
| refcount rung ladder | a refcount gates hardware action only at the 0↔1 edge transitions |
| cyclic ring buffer with position pointers | two pointers chase each other around one wrapping buffer |
| frame / bandwidth partition grid | one frame of a shared medium divides into slots claimed by entities |

### Pattern: parent + N children fan-out

Use when one parent object spawns multiple typed child objects on a different bus / queue / map / list, and the children's identity comes from a field inside the parent. Draw the parent as a wide top box with field-level content, then N children in a row underneath, joined by a single trunk that splits into N branches.

```
       struct parent (on bus_A)
       ┌──────────────────────────────────────────────────────────┐
       │  field_1  ...                                            │
       │  field_N  ...                                            │
       └──────────────────────────┬───────────────────────────────┘
                                  │ allocation / registration
              ┌──────────┬────────┼────────┬──────────┐
              ▼          ▼        ▼        ▼          ▼
         ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
         │ child0 │ │ child1 │ │ child2 │ │ child3 │ │ child4 │
         └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

### Pattern: sparse slot map with conditional backing

Use when an address space, slot table, or fixed-size index set is divided into uniformly-sized regions and each region may or may not have a backing data structure allocated for it. The figure shows which regions are present (have backing) and which are holes (no backing), with the lookup formulas below. Reach for it when the page needs to convey that the lookup is a direct dereference but the backing array is sparse and only allocated for populated slots.

Draw the slot row as a contiguous strip of N cells joined by `┬` dividers (no gaps between cells, since the slots are contiguous in the index space). Each cell contains a short status word (`present`, `hole`, `valid`, etc.). The bottom border has `┬` connectors only beneath populated slots (the ones that will descend to a backing box). For each populated slot, drop a `▼` arrow from the bottom of the strip to a backing object box drawn directly below; leave the hole slots with no arrow and no box below. Add accessor labels beneath each backing box (the name and field expression by which code reaches that backing object), connected by `▲` arrows pointing up into the backing box. Labels span multiple lines if the field path is long.

Close the figure with a one-line parenthetical noting which slots are skipped, then one or more formula blocks showing the lookup formula for each conversion mode (direct lookup, flat lookup, etc.). Each formula block has a short heading followed by indented pseudocode lines.

This pattern differs from `parent + N children fan-out` (one parent allocating all N children via a single trunk) and from `N-to-M source/destination mapping` (disjoint inputs feeding rows of a tabular destination): here a single uniform index space partitions into independent slots, each independently populated or absent.

```
       Sparse slot map (possibly with holes)
       ─────────────────────────────────────

       Slot 0        Slot 1        Slot 2        Slot 3
       ┌─────────────┬─────────────┬─────────────┬─────────────┐
       │   present   │    hole     │   present   │   present   │
       └──────┬──────┴─────────────┴──────┬──────┴──────┬──────┘
              │                           │             │
              ▼                           ▼             ▼
        ┌───────────┐               ┌───────────┐ ┌───────────┐
        │  backing  │               │  backing  │ │  backing  │
        │  object   │               │  object   │ │  object   │
        └───────────┘               └───────────┘ └───────────┘
              ▲                           ▲             ▲
              │                           │             │
        table[0]                    table[2]      table[3]
        .ptr                        .ptr          .ptr

       (Slot 1 has no backing object; the hole is skipped)

       Direct lookup:
         lookup(idx) = table[idx].ptr + intra_slot_offset

       Flat lookup:
         lookup(idx) = base + idx
         (base is a virtually contiguous array; only populated slots are mapped)
```

### Pattern: input decode tree

Use when a function's return value or the chosen branch is a deterministic function of a small number of input bits or fields. Draw it as a tree that consumes one input at a time: the tested input on a trunk, one labelled edge per value, and the outcome at each leaf. The reader follows a path rather than scanning rows, and the shape shows which inputs are read only on some paths.

Do NOT draw this as a grid of input columns against an outcome column. That is the plain table 7v bans, and it was the form this catalog carried until 7v retired it. When the material really is a flat product of every input against every outcome with no nesting, it is a semantics table and belongs in Markdown under 7t, with no figure at all.

```
       input_a ?
          │
          ├─ 0 ──────────────────────▶ OUTCOME_NONE
          │      (input_b is not read on this path)
          │
          └─ 1 ──▶ input_b ?
                      │
                      ├─ 0 ─────────▶ OUTCOME_HANDLED
                      │
                      └─ 1 ─────────▶ OUTCOME_WAKE
                                        │
                                        ▼
                                      followup_handler
```

### Pattern: boxed flowchart with decision nodes

Use when a function has 3+ sequential decision points with side effects and back-edges, and showing each step in its own box adds clarity. Each step gets its own box; each decision node has explicit yes / no labels on outgoing edges; loops draw an explicit back-edge with an arrow. Reserve this for paths with real branching; a 2-state decision should be written as prose instead.

The boxes name conditions and effects, never callees. A chart whose boxes are function names and whose edges mean "calls" is the banned flow graph of 7v however many decision diamonds are drawn around it; the test is whether removing every function name would leave a decision structure behind.

```
       ┌─────────────────┐
       │ acquire lock    │
       └────────┬────────┘
                │
       ┌────────▼────────┐    yes
       │ early-exit cond?│──────────▶  break
       └────────┬────────┘
                │ no
                ▼
       ┌─────────────────┐
       │ read register   │
       └────────┬────────┘
                │
       ┌────────▼────────┐    yes ┌──────────────┐
       │ event present?  │──────▶ │ handle event,│
       └────────┬────────┘        │ continue ────┼── back-edge to top
                │ no              └──────────────┘
                ▼
              break

       break ─▶ release lock, return
```

### Pattern: side-by-side struct comparison

Use when two related types interact via a third operation (match function, encode / decode pair, pack / unpack helpers). Show both struct definitions as boxes side by side with the operation drawn underneath as the convergence point.

```
       struct lhs                     struct rhs
       ┌─────────────────┐            ┌─────────────────┐
       │ field_x         │            │ field_x         │
       │ field_y         │            │ field_y         │
       │ ...             │            │ ...             │
       └────────┬────────┘            └────────┬────────┘
                │                              │
                └────────► matcher / op ◀──────┘
                                │
                                ▼
                       returns match iff
                         lhs.field_x == rhs.field_x
                         AND (rhs.field_y == ANY || ...)
```

### Pattern: linked structs via field-level pointers

Use when several related structs and arrays connect via pointer fields, encoded pointers, or per-cell bitmap pointers, and the relationship between them is the field-level pointer topology itself. Each struct is drawn as a labeled box: the struct name (with `struct` keyword) sits on a borderless heading line above the box, and field names are listed inside the box one per line with optional type or comment in parentheses. Fields with internal structure (bit-packed words, embedded arrays, fixed bitmaps) get drawn as nested cell strips inside the outer box.

Pointer fields exit the bottom border of the box (via `┼` or `─┐`), descend as vertical trunks (`│`), and terminate in a `▼` arrow that lands on the target box below. When a nested bitmap has per-cell pointing relationships (one bit per subsection, one entry per slot), each cell descends via its own vertical trunk and `▼` to its target in a parallel array drawn underneath. Length-bracket annotations of the form `|<── span ──>|` mark total spans beneath arrays. Close the figure with a legend block beneath the diagram listing flag and constant meanings as `NAME = MEANING` columns.

This pattern differs from `parent + N children fan-out` (which shows allocation or registration of typed children) and from `side-by-side struct comparison` (which shows two peer structs meeting at one operation): here the structs already exist and the visible shape of the figure is the chain of pointer fields linking them together.

```
       Linked struct hierarchy
       ───────────────────────

       struct outer_t
       ┌──────────────────────────────────────────────────────────┐
       │  packed_field  (unsigned long, encoded)                  │
       │  ┌──────────────────────────────────┬───┬───┬───┬───┐    │
       │  │   encoded target * pointer       │ D │ C │ B │ A │    │
       │  └──────────────────┬───────────────┴───┴───┴───┴───┘    │
       │                     │                                    │
       │  link ──┐           │  (biased: pointer + idx = target)  │
       │         │           │                                    │
       │  optional_field  (only with CONFIG_OPTIONAL)             │
       └─────────┼───────────┼────────────────────────────────────┘
                 │           │
                 │           ▼
                 │      struct target_t[N]
                 │      ┌────┬────┬────┬────┬─────┬─────┐
                 │      │ t0 │ t1 │ t2 │ t3 │ ... │tN-1 │
                 │      └────┴────┴────┴────┴─────┴─────┘
                 │      |<── one entry per index in outer ──>|
                 │
                 ▼
       struct linked_t
       ┌──────────────────────────────────────────────────────────┐
       │  preamble                                                │
       │                                                          │
       │  bitmap[BITS_TO_LONGS(N_CELLS)]                          │
       │       bit:   0    1    2    3    4   ...   N-1           │
       │       ┌────┬────┬────┬────┬────┬─────┬────┐              │
       │       │ 1  │ 0  │ 1  │ 1  │ 0  │ ... │ 1  │              │
       │       └─┬──┴─┬──┴─┬──┴─┬──┴─┬──┴─────┴─┬──┘              │
       │         │    │    │    │    │          │                 │
       │  trailer  (variable-length, computed by helper)          │
       └─────────┼────┼────┼────┼────┼──────────┼─────────────────┘
                 │    │    │    │    │          │
                 ▼    ▼    ▼    ▼    ▼          ▼
                 ┌────┬────┬────┬────┬────┬────┬─────┐
                 │ U0 │ U1 │ U2 │ U3 │ U4 │ ...│UN-1 │  fixed-size units
                 └────┴────┴────┴────┴────┴────┴─────┘  one bit per unit
                 |<──── total span of one linked_t ──────────>|

       Flag bits in packed_field (low bits):
         A = FLAG_NAME_A  (bit 0, marker)
         B = FLAG_NAME_B  (bit 1, has-pointer)
         C = FLAG_NAME_C  (bit 2, online)
         D = FLAG_NAME_D  (bit 3, early-init)
```

### Pattern: N-to-M source/destination mapping

Use when several disjoint inputs feed a single tabular destination, with some inputs feeding multiple rows of the destination. Sources go in a column on the left; the destination is a stacked box on the right; arrows cross the gap. Annotation that would otherwise hang off the right edge of the destination box belongs as prose below the figure, not as right-aligned brackets, so the figure stays under 80 columns.

```
       Source register              Destination slots
       ───────────────              ─────────────────

       SRC_FIELD_A                  ┌─────────────────────┐
         file path / spec § ──▶     │ slot[0] = result_A  │
                                    │ slot[2] = result_A  │
                                    │ slot[4] = result_A  │
                                    ├─────────────────────┤
       SRC_FIELD_B          ──▶     │ slot[1] = result_B  │
         file path / spec §         ├─────────────────────┤
       SRC_FIELD_C          ──▶     │ slot[3] = result_C  │
         file path / spec §         └─────────────────────┘
```

### Pattern: queue / ring between two stages

Use when a producer and a consumer communicate through a bounded buffer (kfifo, work_struct, list_head ring). Show the buffer as a row of cells in the middle; the two stages flank it; arrows label the put / get operations.

```
       Producer side              kfifo / work / ring         Consumer side
       ┌──────────────────┐       ┌──┬──┬──┬─────┬───┐        ┌──────────────┐
       │ Stage A reads    │       │e0│e1│e2│ ... │e_n│        │ Stage B      │
       │ source, RW1C     │  put  └──┴──┴──┴─────┴───┘  get   │ dequeues,    │
       │ clear, enqueue   │ ──▶      ▲              │   ──▶   │ processes    │
       │ ... return       │          │              └──────▶  │ ... return   │
       │ IRQ_WAKE_THREAD  │          │                        │ IRQ_HANDLED  │
       └──────────────────┘          │                        └──────────────┘
```

The remaining patterns are each shown with an example figure; copy the shape and relabel it for the subsystem at hand.

### Pattern: data dependency (inputs feed a transform)

Use when one or more source structs are read by a function that builds or populates a destination struct, and the point is which inputs feed which output (assembling a config, intersecting capabilities, encoding a message). Draw the input struct boxes at the top, the transform function as the labelled junction beneath them, and the produced struct below; the arrows mean feeds / populates / points-to, never call order. The figure is a valid data-dependency picture only because its endpoints are structs: a figure whose nodes are all functions joined by call arrows is the banned code-flow chart. Complements the linked-structs-via-pointers pattern, which shows structs already wired by their fields.

```
       snd_soc_runtime_calc_hw: intersect every CPU and codec DAI
       ──────────────────────────────────────────────────────────

       each CPU DAI stream        each codec DAI stream
       ┌────────────────────┐     ┌────────────────────┐
       │ rate_min..rate_max │     │ rate_min..rate_max │
       │ channels_min..max  │     │ channels_min..max  │
       │ formats mask       │     │ formats mask       │
       └──────────┬─────────┘     └─────────┬──────────┘
                  │  for_each_rtd_cpu_dais  │  for_each_rtd_codec_dais
                  └───────────┬─────────────┘
                              ▼  raise min, lower max, AND the formats
                 ┌──────────────────────────────────┐
                 │ substream->runtime->hw           │
                 │  rates  channels_min..max        │
                 │  formats   (&= starting formats) │
                 └────────────────┬─────────────────┘
                                  ▼  soc_hw_sanity_check
                 !rates  /  !formats  /  empty channels
                          ─▶ -EINVAL  "No matching ..."
```

### Pattern: before / after transformation

Use when an operation changes the shape of one data structure (a split, a merge, an insert, a remove, a move, an in-place encode) and the point is the structure before versus after. Draw the structure twice in the same cell style, labelled `before` and `after`, with the operation as a labelled `──▶` between them (or the two states stacked, before above after), so the change is read by diffing the two drawings. Keeping the cell style identical across the two sides is what makes the diff legible. Distinct from data dependency, which feeds inputs through a transform into a *different* destination struct: here the *same* structure is shown reshaped on both sides.

```
    __split_vma at boundary S: one maple-tree interval before and after
    ───────────────────────────────────────────────────────────────────

    before                          after
    ┌─────────────────────────┐     ┌────────────┬────────────┐
    │ node  [vm_start, vm_end)│ ──▶ │ [vm_start, │ [S,        │
    │ one interval            │     │  S)        │  vm_end)   │
    └─────────────────────────┘     └────────────┴────────────┘

    one node becomes two, the covered range is unchanged, and the
    new node is a vm_area_dup copy of the original with its own range
```

### Pattern: signal-timing / waveform

Use when the point is where a data bit or sample lands in time relative to a clock or frame edge (a serial-bus frame, a strobe, a sampling instant). Draw each wire as a square-wave trace built from ─ levels and ┌ ┐ └ ┘ │ edges, one trace per line, with a vertical reference column (▼ and │) marking the frame edge so the offset reads straight off the grid; align the data cells under a per-cell clock tick.

```
       I2S vs left-justified: where the left-channel MSB sits
       ────────────────────────────────────────────────────────
       (▼ = tick 0, the WS falling edge that opens the left slot;
        each data cell is one BCLK period)

                     ▼
       WS    ────────┐
                     └────────────────────────────────

       I2S   ─────────────┌────┬────┬────┬────┐    MSB starts one
       SD            ·····│MSB │ b14│ b13│ b12│    BCLK after the edge

       LEFT  ────────┌────┬────┬────┬────┐          MSB starts on
       SD            │MSB │ b14│ b13│ b12│          the edge (no delay)
```

### Pattern: swimlane sequence (actors × time)

Use when several actors (userspace, a core layer, a driver, hardware) hand work to each other over time and the cross-actor ordering is the point. Draw one vertical lane per actor separated by │ columns, time running downward, and a cross-lane ──▶ arrow for each step; annotate each lane with the state it reaches. Distinct from queue/ring (a buffer between two stages): this shows N actors over one timeline.

The cells carry the state each actor reaches, not the next function it calls. A walkthrough page is where this goes wrong most often: a lane diagram of one call stack, with every cell a callee and every arrow a call, is the banned flow graph of 7v with lane rules drawn on it. If the figure would survive deleting all but one lane, it was never a swimlane.

```
       trigger START fan-out across the soc_pcm_trigger[][] rows
       ──────────────────────────────────────────────────────────
       time ↓
       ALSA core      │ soc-pcm     │ SOF + IPC4    │ SDW BE / host DMA
       ───────────────┼─────────────┼───────────────┼──────────────────
       snd_pcm_start  │             │               │
         do_start ──▶ │ soc_pcm_    │               │
                      │  trigger    │               │
                      │ runs the    │               │
                      │ 3 rows ──▶  │               │
         link row ────────────────────────────────▶ │ asoc_sdw_trigger
                      │             │               │  ─▶ sdw_enable_
                      │             │               │     stream ENABLED
         comp row ──────────────────▶ sof_pcm_      │
                      │             │  trigger ─▶   │
                      │             │ IPC4 SET_     │
                      │             │ PIPELINE_     │
                      │             │ STATE RUNNING │
         DAI row ─────────────────────────────────▶ │ hda_dsp_stream_
                      │             │               │  trigger: DMA run
       state RUNNING  │             │               │
```

### Pattern: state-transition graph

Use when an object moves through named states and the legal transitions (including back-edges and self-loops) are the point. Draw each state as a boxed node and each event as a labelled directed ──▶ edge; draw the back-edges explicitly. Distinct from the boxed decision flowchart, which traces control flow through one function; this traces an object's state across its lifetime.

```
       Tip-sense plug state machine (in cs42l42_irq_thread)
       ────────────────────────────────────────────────────
       current_plug_status drives plug_state; only a real change
       of state acts, so repeated reports are ignored.

                       ┌───────────────────────────┐
               ┌──────▶│ CS42L42_TS_UNPLUG         │
               │       │  cancel hs type detect,   │
               │       │  report 0 over the wide   │
               │       │  HEADSET + BTN_0..3 mask  │
               │       └─────────────┬─────────────┘
               │ TS_UNPLUG           │ TS_PLUG
               │                     ▼
               │       ┌───────────────────────────┐
               │       │ CS42L42_TS_PLUG           │
               └───────┤  cs42l42_init_hs_type_    │
                       │  detect (start a cycle)   │
                       └─────────────┬─────────────┘
                                     │ neither bit set
                                     ▼
                       ┌───────────────────────────┐
                       │ CS42L42_TS_TRANS          │
                       │  transient, no report     │
                       └───────────────────────────┘
```

### Pattern: directed graph / DAG

Use when a multi-node signal or dependency graph has fan-in and fan-out, plus auxiliary nodes (supplies, clocks) that attach to the side rather than carry signal. Draw the signal nodes as boxes joined left-to-right by ──▶ edges, mux fan-in with ─┐/─┘ collectors, and side nodes attached with ◀── or a ▲ stem. More general than parent + N children fan-out (one parent, one level).

```
       rt722-sdca playback + speaker paths; PDE supplies hang off sideways
       ──────────────────────────────────────────────────────────────────

         ┌────────┐      ┌────────┐      ┌────────┐
         │ DP1RX  │ ───▶ │ FU 42  │ ───▶ │   HP   │ ◀── PDE 47 (supply)
         │ aif_in │      │  dac   │      │ output │
         └────────┘      └────────┘      └────────┘

         ┌────────┐      ┌────────┐      ┌────────┐
         │ DP3RX  │ ───▶ │ FU 21  │ ───▶ │  SPK   │ ◀── PDE 23 (supply)
         │ aif_in │      │  dac   │      │ output │
         └────────┘      └────────┘      └────────┘

         static routes {"HP",NULL,"FU 42"} and {"SPK",NULL,"FU 21"} pass
         signal; {"HP",NULL,"PDE 47"} ties the supply to the output pin.
```

### Pattern: register / address-offset map

Use when several registers sit at fixed offsets within a block, or one block repeats at base + stride · index, and the addressing is the point (per-stream, per-port, or per-lane blocks). Draw the index ──▶ base-address column on the left, and one representative block expanded as a box of its named registers on the right. Distinct from a single-register bitfield (the 7h catalog in this file), which plots the bits of one register.

```
       Per-stream SDn register blocks (one per host DMA engine)
       ──────────────────────────────────────────────────────────
       SDn block base = remap_addr + 0x80 + 0x20 * idx   (stride 0x20)

         idx        SDn block base
         ───        ──────────────
          0   ───▶  remap_addr + 0x80     ┌──────────────────────┐
          1   ───▶  remap_addr + 0xA0     │ SDn descriptor:      │
          2   ───▶  remap_addr + 0xC0     │   stream tag         │
          .                               │   cyclic buf length  │
          .                               │   format value       │
          n   ───▶  remap_addr            │   last-valid-index   │
                     + 0x80 + 0x20*n      │   BDL base address   │
                                          └──────────────────────┘

       snd_hdac_stream_setup() programs the block for the assigned idx
       idx split: capture  = [0 .. capture_streams)
                  playback = [capture_streams .. num_streams)
```

### Pattern: layered stack / membrane

Use when the point is how layers stack and where one layer calls through to the next across a named API boundary (userspace / core / driver / firmware-or-hardware). Draw each layer as a full-width box stacked above the next, and label each ▼ divider with the boundary it crosses (the ioctl, the ops vector, the message channel). The boundary labels are the point, not the box contents.

```
       ASoC core (sound/soc/soc-core.c)
               │  devm_snd_soc_register_component(&sdev->plat_drv, ...)
               ▼
       ┌──────────────────────────────────────────────────────────────┐
       │  struct snd_sof_dev          (sound/soc/sof/sof-priv.h:547)  │
       │   ops ───── sof_ops() ─────▶  struct snd_sof_dsp_ops         │
       │   ipc ─────────────────────▶  struct snd_sof_ipc ─▶ ops      │
       └───────────────┬──────────────────────────────┬───────────────┘
                       │ block_write, run, send_msg   │ tx_msg (IPC3/IPC4)
                       ▼                              ▼
               DSP hardware (HDA-gen)            DSP firmware (SOF)
```

### Pattern: ordered level ladder

Use when a value moves through a small set of strictly-ordered levels and the travel direction matters (power/bias states, D-states, link states). Draw the levels as rows in numeric order, highest at the top, with ▲ (up) and ▼ (down) markers down the side and the per-step rule. Distinct from a state-transition graph: a ladder is monotonic and totally ordered, traversed one step at a time.

```
       enum snd_soc_bias_level: one context climbs and descends the ladder
       ──────────────────────────────────────────────────────────────────

         value   level                  bias_level ──▶ target_bias_level

           3   ┌──────────────┐  ON        full power, signal flowing
               │ SND_SOC_BIAS │
           2   │   _PREPARE   │  PREPARE   transitional, around ON
           1   │              │  STANDBY   supplies up, idle floor
           0   └──────────────┘  OFF       powered down (init seed)

         up:    OFF ─▶ STANDBY ─▶ PREPARE ─▶ ON
         down:  ON  ─▶ PREPARE ─▶ STANDBY ─▶ OFF
```

### Pattern: refcount with threshold actions

Use when a reference count gates a hardware action only at a threshold crossing (first user enables, last user disables; the 0↔1 edge). Draw the count as horizontal rungs, the raising events climbing one side and the lowering events descending the other, and mark the one rung crossing that reaches the hardware. The shape puts the acting edge next to the inert ones, so the asymmetry is read off the picture rather than counted out of rows.

Do NOT draw this as a grid of events against transitions against actions. That is the plain table 7v bans, and it was the form this catalog carried until 7v retired it.

```
       be_start: the hardware sees only the edges next to 0
       ─────────────────────────────────────────────────────────────
       (two FEs sharing one BE; START climbs the left side, STOP
        descends the right)

         2  ─────────────────────────────────────────────────────
              ▲  a second FE joins.        │  one of the two FEs
              │  be_start reads 1 first,   │  leaves. be_start does
              │  so no trigger is sent     ▼  not reach 0, no trigger
         1  ─────────────────────────────────────────────────────
              ▲  the first FE starts.      │  the last FE leaves.
              │  soc_pcm_trigger(START)    │  soc_pcm_trigger(STOP)
              │  reaches the BE            ▼  reaches the BE
         0  ─────────────────────────────────────────────────────

         START acts only from BE state PREPARE, STOP or PAUSED;
         STOP acts only from START or PAUSED, and lowers be_start
         only when the BE was in START
```

### Pattern: cyclic ring buffer with position pointers

Use when a single cyclic buffer is split into periods/slots and two pointers (a producer and a consumer, e.g. appl_ptr and hw_ptr) chase each other around it with wrap. Draw the periods as a contiguous row of cells, a ▼ from each pointer onto its cell, and note which span is filled vs free and where the pointers wrap. A specialization of queue/ring for one wrapping buffer with two positions.

```
       The PCM ring buffer: hw_ptr and appl_ptr chase around it
       ─────────────────────────────────────────────────────────
       (buffer_size frames, split into periods of period_size)

       ┌────────┬────────┬────────┬────────┬────────┬────────┐
       │ period │ period │ period │ period │ period │ period │
       │   0    │   1    │   2    │   3    │   4    │   5    │
       └────────┴───┬────┴────────┴────────┴────┬───┴────────┘
                    │                           │
                    ▼                           ▼
                 hw_ptr                      appl_ptr
          pointer op reports it      pcm_lib_apply_appl_ptr moves it
          snd_pcm_update_hw_ptr0     after each copy / fill_silence chunk

       playback: appl_ptr leads (app fills ahead), hw_ptr trails (DMA)
       both wrap at runtime->boundary; ack op fires when appl_ptr moves
```

### Pattern: frame / bandwidth partition grid

Use when one frame or period of a shared medium is divided into slots or row/column cells, each claimed by an entity (TDM slots, a bus frame's columns, channel allocations). Draw the frame as a contiguous ┌─┬─┐ strip of equal cells labelled by slot, optionally a second strip showing a wider or narrower division of the same frame. The point is how the fixed bandwidth partitions.

```
       I2S frame = the two-slot case of TDM
       ──────────────────────────────────────
       (one sample per slot; set_fmt picks I2S, set_tdm_slot widens it)

       One WS (LRCLK) period:
       ┌───────────────────────┬───────────────────────┐
       │       left slot       │       right slot      │
       │       (WS low)        │       (WS high)       │   I2S = 2 slots
       └───────────────────────┴───────────────────────┘

       Same wires, a wider TDM frame (one FSYNC period, N slots):
       ┌──────┬──────┬──────┬──────┬──────┬─────┬───────┐
       │slot 0│slot 1│slot 2│slot 3│slot 4│ ... │slotN-1│
       └──────┴──────┴──────┴──────┴──────┴─────┴───────┘
          set_tdm_slot assigns each codec channel a slot mask (N > 2)
```

**PASS CRITERIA:** For each justified figure, choose the pattern from the use-case index by matching its "reach for it when" column, and record the pattern name at sign-off; reach for a new shape only when no listed pattern fits the relationship, and record why. Confirm the figure matches its pattern's stated shape and distinguishing notes: a sparse slot map is neither a fan-out (one trunk allocating children) nor an N-to-M mapping (disjoint inputs feeding a tabular destination); swimlane cells carry the state each actor reaches, never the next callee, and a swimlane that would survive deleting all but one lane fails; data-dependency endpoints are structs and its arrows mean feeds or populates, never call order; a before/after keeps the identical cell style on both sides so the change reads as a diff; flowchart boxes name conditions and effects, never callees; annotation that would hang off the destination's right edge moves to prose below the figure so every line stays under 80 columns. Honor the two retired forms this catalog once carried: input-decode material is drawn as a decode tree, never as a grid of input columns against an outcome column, and threshold-refcount material as a rung ladder, never as a grid of events against transitions against actions (both grids are DIAG-02's plain table, and DIAG-02 outranks this catalog). A flat input-to-outcome product with no nesting is a Markdown semantics table per PLOT-02 and gets no figure at all. Pass per figure with the pattern named.
