# 7h. Register and bitfield figures (mandatory)

Rule IDs (3a-3c, 7, 7a-7r) resolve via `guidelines/rules/INDEX.md`.

A figure that plots a register, a bitfield, a TRB, a context, a packet header, or another bit-field structure follows the rules and reference figures in this section, on top of the general diagram rules in 7g (`guidelines/rules/7g-principles.md`). It is drawn in one of two named styles, the DWORD-grid style and the L-connector style, chosen by the register-versus-structure test below.

Two things decide how to label the bits, and the two resulting styles have names used throughout this skill. The DWORD-grid style writes each field name inside its cell and stacks the DWORDs as `DW0`, `DW1`, ... rows; the L-connector style draws a single row of one-character cells and calls out each bit's name below on an L-shaped leader.

A register is one value at one address; if it is wider than a DWORD the split is only display width, and all its bits are one field set. A structure is several separate words at successive DWORD offsets, each its own named unit. Quick test: is the thing one value, or several separate words? A register is one value (even a 64-bit register is a single 64-bit number), so all its bits sit on one ruler; a structure is several separate words, so each keeps its own row. Registers include EC_SC, the PCI Command and Status words, a USB4 ADP_CS_x register, a 64-bit MSI address, and an encoded-pointer-plus-flags word; structures include an xHCI TRB, a context, a descriptor, and a TLP or TCP header.

The L-connector style is for registers only. Reach for it when a register is mostly single-bit fields whose names will not fit inside one-character cells: give each bit a one-character cell, then run a dashed L-connector from each named bit's column out to its constant, stacking the labels so each elbow lands on its own trunk (reserved bits get no trunk), with a legend mapping each cell to its constant and value. A register drawn this way is a single row of all its bits, whatever its width — a 64-bit register is one wide row, not two stacked DWORDs. When the upper bits of a wide register are a single uniform field (an encoded pointer above its low flags), you may instead draw just the DWORD that carries the interesting fields and note that the upper bits continue that field.

The DWORD-grid style is for everything else: a structure, or a register whose field names fit in the cells. Keep the names inside the cells and stack the DWORDs as `DW0`, `DW1`, ... rows; the L-connector style does not apply to structures.

This governs a figure whose primary subject is the bit-layout. A bit-strip that is one element of a larger structural figure (a flag nibble inside a struct box, a bitmap strip in a pointer-topology diagram) follows the host figure's style, not the register rules here.

Rules:

- Header rows give the bit index from the high bit down to 0, one bit per two-column slot. Use two rows (a tens-digit row, then a ones-digit row) whenever any index reaches two digits, and one row when every index is a single digit (a byte, or any field set within bits 0 to 9). Reuse the exact ruler and the full per-bit `┌─┬...─┐` top border so every cell stays aligned.
- Stack the dwords as rows, each labelled `DW0`, `DW1`, ... in a left gutter (the label sits at column 4 and the box left border at column 10). Use `├──┬──┼──┴──┤` divider rows to transition between the differing field layouts of one dword and the next.
- Each field cell carries the field name, and on a second line for a multi-bit field its `(hi:lo)` bit range, centred in the cell. A single-bit field uses a one-character cell (for example `E` or `R`); when many single-bit fields crowd one register, label each with an L-connector beneath the figure instead (see the single-bit-field example below).
- Box-drawing is Unicode only (`┌ ┐ └ ┘ │ ─ ├ ┤ ┬ ┴ ┼`). Never use ASCII `\`, `/`, or `|` as connectors. Keep every line under 80 columns, except a register drawn as a single row with L-connectors, which may run wider when its bit count requires it (a 64-bit register is roughly 130 columns).
- Add a legend beneath the figure mapping each field to its kernel macro and, where relevant, the cached struct field, as `NAME = MACRO (meaning)`.
- Verify before saving: every content-row `│` lands on a `┬` or `┴` junction of the border rows above and below it.

For a register that is a single dword, draw just the ruler, the `┌─┬...─┐` top border, one `DW0` content row (field names plus `(hi:lo)` ranges), and the bottom border, then the legend. Use the two-row numbered ruler whenever any bit index reaches two digits; a register whose highest bit index is a single digit may use one header row, as the figure below does.

Draw a figure to scale by default: a complete per-bit numbered ruler, cells in proportion to their bit width, every `(hi:lo)` an exact number. Draw to scale whenever every boundary is a fixed number, because the ruler pins each bit and a reader reads positions straight off it.

When a boundary is not a fixed number — it varies by implementation or mode (the x86-64 PTE address field that ends at MAXPHYADDR), or the figure is a generic pattern where exact positions would be fake precision — draw it schematic instead. Label only the boundaries that matter (the high bit, each variable boundary by name such as `N` or `M`, and the low fixed bits), join the gaps with `...`, and size each cell for its label rather than to scale. Schematic trades exact-position readability for the ability to show a boundary that has no fixed value, so use it only as the fallback. This choice is independent of DWORD-grid versus L-connector: either style can be drawn either way (the PTE figure below is a schematic DWORD-grid register, and the worked example shows the same packed register both to scale and schematic).

Reference figure (a structure, drawn as stacked DWORDs — the DWORD-grid style):

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

Reference figure (a register of many single-bit fields — the L-connector style):

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

Reference figure (a DWORD-grid register, schematic — the address field ends at the variable MAXPHYADDR):

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

## Worked example: compound packed field (encoded pointer with status flags)

Use when a single struct field is a packed `unsigned long` (or similar word) that combines an encoded pointer to another struct with multiple status flag bits in the low bits, and the page needs to show both halves at once with the decode formula visible. This is common when the kernel reuses alignment-guaranteed low bits of a pointer to encode metadata; the figure shows the bit positions, the per-bit flag constants, and the formula that extracts the embedded pointer.

Draw it in the L-connector style: a single row of the register's bits under the per-bit numbered ruler and a full per-bit `┌─┬...─┐` top border. The encoded pointer and any intermediate field (NID, type) are range cells carrying a name and `(hi:lo)` range; each status flag in the low bits is a one-character cell (`D`, `C`, `B`, `A`) named by an L-connector below. Because the upper bits of this 64-bit register are all pointer, draw just the low dword and note in the heading that the upper bits continue the pointer, rather than a 130-column full row. The total width of the top border, content row, and bottom border must match, and every content-row `│` lands on a `┬`/`┴` junction.

Below the bottom border, drop a vertical trunk (`│`) from each flag bit's column (under its `D`, `C`, `B`, `A` cell). Connect each trunk to its constant name with an L-shaped corner (`────┘`); the constant labels stack as a left-aligned column on the left and the dashes lengthen from line to line so each elbow lands on its trunk. The leftmost (highest-numbered) flag's trunk gets the shortest dashed line; the rightmost (lowest-numbered) flag's trunk gets the longest.

Close the figure with a multi-line pseudocode block showing the decode formula (`Pointer = field & FIELD_PTR_MASK`, `= real_pointer - base_index(slot)`) and a parenthetical note explaining any bias or invariant.

Use the L-connector style when the flag constants are too long to sit inside one-character cells several across, as here; the connectors keep each flag one bit wide while still naming it, and leave room for the decode formula beneath. Reach for this pattern when the packed field is the entry point into another struct (pointer encoding), where the decode formula matters, not when the field is a plain status register.

```
    struct outer_t.packed_field (encoded pointer + status flags)
    ────────────────────────────────────────────────────────────
    (illustrative; bits 63:32 continue the pointer, low dword shown)

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │          encoded pointer (31:10)          │ NID (9:4) │D│C│B│A│
          └───────────────────────────────────────────┴───────────┴─┴─┴─┴─┘
                                                                   │ │ │ │
                             FLAG_NAME_D ──────────────────────────┘ │ │ │
                             FLAG_NAME_C ────────────────────────────┘ │ │
                             FLAG_NAME_B ──────────────────────────────┘ │
                             FLAG_NAME_A ────────────────────────────────┘

    Pointer = packed_field & FIELD_PTR_MASK   (mask = bits 63:10)
            = real_pointer - base_index(slot)
    (biased so that pointer + idx yields the correct struct target)
```

The figure above is drawn to scale, with concrete bit boundaries. This pattern is a generic illustration, though, so the boundary between the pointer and the flags is not really a fixed bit. When the boundaries are generic or vary (by implementation or mode), draw it schematic instead: name the variable boundary `N`, elide the middle with `...`, and size cells for their labels rather than to scale, as the to-scale-versus-schematic policy above describes. The schematic version of the same figure:

```
    struct outer_t.packed_field (encoded pointer + status flags)
    ────────────────────────────────────────────────────────────
    (schematic; the pointer occupies bits 63:N, and N varies)

     63                                N      ...   3   2   1   0
    ┌─────────────────────────────────┬─────┬─────┬───┬───┬───┬───┐
    │ encoded struct target * pointer │ NID │ ... │ D │ C │ B │ A │
    └─────────────────────────────────┴─────┴─────┴───┴───┴───┴───┘
                                                    │   │   │   │
                                  FLAG_NAME_D ──────┘   │   │   │
                                  FLAG_NAME_C ──────────┘   │   │
                                  FLAG_NAME_B ──────────────┘   │
                                  FLAG_NAME_A ──────────────────┘

    Pointer = packed_field & FIELD_PTR_MASK   (mask = bits 63:N)
            = real_pointer - base_index(slot)
    (biased so that pointer + idx yields the correct struct target)
```
