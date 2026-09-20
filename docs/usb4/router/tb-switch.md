# struct tb_switch

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A USB4 fabric is a tree of routers, and a router is the switching element inside a host or an attached device. The driver reads a router's own state by sending a configuration transaction across that fabric, so it asks once and keeps the answer. Each router therefore gets one object holding its identity, its place in the tree, its offsets and its policy. This page takes that object member by member, giving each the path that writes it and the path that reads it. It also covers the inline helpers that reach a router, classify it and prefix its log lines.

```
    the router on the wire                          the object the driver keeps
    ┌────────────────────────────┐                  ┌──────────────────────────────────┐
    │ port 0, the control port   │                  │ dev       the embedded device    │
    │  ┌──────────────────────┐  │   read once at   │ tb        the owning domain      │
    │  │ Router CS_0 .. CS_4  │  ├─────────────────▶│ config    those five dwords      │
    │  └──────────────────────┘  │   allocation     │ uid uuid vendor device names     │
    │                            │                  │ cap_plug_events cap_vsec_tmu     │
    │ adapter 1                  │                  │ cap_lc cap_lp   is_unplugged     │
    │ adapter 2                  │                  │ drom nvm no_nvm_upgrade quirks   │
    │  ...                       │                  │ boot rpm authorized key          │
    │ adapter max_port_number    │                  │ five credit counts   clx   tmu   │
    │                            │                  │ ports ──┐                        │
    └─────────────┴──────────────┘                  └─────────┼────────────────────────┘
                  ▲                                           │
                  │                                           ▼
                  │            struct tb_port[0 .. max_port_number]
                  │            ┌──────┬──────┬──────┬───────┬──────────────────┐
                  └────────────┤  0   │  1   │  2   │  ...  │ max_port_number  │
                    one entry  └──────┴──────┴──────┴───────┴──────────────────┘
                    per adapter
```

## SUMMARY

The object answers from memory what the fabric would otherwise have to be asked again. [`struct tb_switch`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L171) is one allocation per router, holding an embedded [`struct device`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L703), a copy of the five dwords the router answers with, and an array of [`struct tb_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L280) sized from that copy. The driver core owns that allocation, and the remaining members take their values as the router is set up and used.

```
    One router object, field by field, from allocation to removal
    ─────────────────────────────────────────────────────────────

    time ───────────────────────────────────────────────────────────────────────────────▶

    event            alloc      host start    scan       add      publish   userspace   remove
                       ▼            ▼          ▼          ▼          ▼          ▼          ▼
                    ┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬─────────
    drom            │ NULL     │ NULL     │ NULL     │ image  ② │ image    │ image    │ image
                    │          │          │          │ NULL   ③ │          │          │
                    └──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴─────────
                    ┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬─────────
    nvm             │ NULL     │ NULL     │ NULL     │ object ④ │ object   │ object   │ NULL  ⑦
                    └──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴─────────
                    ┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬─────────
    no_nvm_upgrade  │ false    │ true   ⑧ │ false    │ true  ⑤⑥ │ as set   │ as set   │ as set
                    └──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴─────────
                    ┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬─────────
    rpm             │ false    │ USB4   ⑨ │ gen>1  ⑩ │ arms PM  │ as set   │ as set   │ as set
                    └──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴─────────
                    ┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬─────────
    authorized      │ host 1 ⑪ │ 0        │ 0        │ 0        │ boot 1 ① │ 0,1,2 ⑫⑬ │ as set
                    └──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴─────────
                    ┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬─────────
    clx             │ 0        │ 0        │ 0        │ hw     ⑭ │ hw       │ +clx  ⑮⑯ │ as set
                    └──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴─────────

    the marks count in the order the subsections below reach these writes, an
    order the declaration sets while the columns follow the clock

    ① tb_scan_finalize_switch    tb.c:2985      authorized ← 1 where boot firmware tunneled
    ② tb_switch_drom_alloc       eeprom.c:449   drom ← a zeroed buffer the size the DROM reports
    ③ tb_switch_drom_free        eeprom.c:467   drom ← NULL once the image is freed again
    ④ tb_switch_nvm_init         switch.c:346   nvm ← the object whose version read succeeded
    ⑤ tb_switch_nvm_init         switch.c:351   no_nvm_upgrade ← true on either failure path
    ⑥ tb_switch_nvm_add          switch.c:388   no_nvm_upgrade ← true when registration fails
    ⑦ tb_switch_nvm_remove       switch.c:399   nvm ← NULL before the object is handed back
    ⑧ tb_start                   tb.c:3014      no_nvm_upgrade ← true unless the host is USB4
    ⑨ tb_start                   tb.c:3016      rpm ← true when the host router is USB4
    ⑩ tb_scan_port               tb.c:1373      rpm ← true for a router above generation 1
    ⑪ tb_switch_alloc            switch.c:2537  authorized ← true for the host router
    ⑫ tb_switch_set_authorized   switch.c:1859  authorized ← the value userspace wrote
    ⑬ disapprove_switch          switch.c:1812  authorized ← 0 down the whole subtree
    ⑭ tb_switch_clx_init         clx.c:236      clx ← the CL states the link already holds
    ⑮ tb_switch_clx_enable       clx.c:383      clx ← the states both adapters accepted
    ⑯ tb_switch_clx_disable      clx.c:424      clx ← 0 after both adapters drop them
```

Every configuration transaction the driver sends through [`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) and [`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686) is built from three members and refused once [`is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L193) is true. The kerneldoc requires the domain lock [`lock`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L84) held while a router joins or leaves the domain, and the sysfs paths that can race it take the same lock. Seven members carry state that only the firmware connection manager's paths write, which this page names and leaves there.

## SPECIFICATIONS

No specification numbers a section that defines this structure. The USB4 Specification defines the router the structure stands for, and the kerneldoc says so at [tb.h:169](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L169), where the comment reads "In USB4 terminology this structure represents a router." The five buffer-allocation parameters the credit members cache keep the specification's own names in the warning text of [`usb4_switch_credits_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L758), which names baMaxHI at [usb4.c:829](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L829), baMinDPaux and baMinDPmain at [usb4.c:841](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L841), baMaxUSB3 at [usb4.c:857](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L857) and baMaxPCIe at [usb4.c:862](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L862).

Everything below is a disclosed synthesis over [`drivers/thunderbolt/tb.h`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h), [`drivers/thunderbolt/tb_regs.h`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h), [`drivers/thunderbolt/switch.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c), [`drivers/thunderbolt/eeprom.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c), [`drivers/thunderbolt/usb4.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c), [`drivers/thunderbolt/tb.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c), [`drivers/thunderbolt/tunnel.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c), [`drivers/thunderbolt/clx.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c), [`drivers/thunderbolt/tmu.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c) and [`drivers/thunderbolt/quirks.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c) at v7.2, and every claim under it carries its citation into those files.

## COVERAGE

### The router object (tb.h)

- [`'\<struct tb_switch\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L171): the per-router object, forty-five members plus one that [`CONFIG_DEBUG_FS`](https://elixir.bootlin.com/linux/v7.2/source/lib/Kconfig.debug#L708) adds

### Reference counting and device recovery (tb.h)

- [`'\<tb_switch_get\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L878): take one reference on the embedded device, tolerating a NULL argument
- [`'\<tb_switch_put\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L885): drop one reference, the call that can reach the release callback
- [`'\<tb_is_switch\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L890): answer whether a device pointer belongs to a router, by device type alone
- [`'\<tb_to_switch\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L895): recover the object from the embedded device, answering NULL for any other type
- [`'\<tb_switch_parent\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L902): the router one level up, taken from the device parent pointer

### Reading and classifying out of the cached header (tb.h)

- [`'\<tb_switch_depth\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L928): the router's depth, read straight out of the cached header
- [`'\<tb_switch_is_icm\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1023): the connection-manager discriminator, one field of the cached header
- [`'\<usb4_switch_version\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1311): the router's USB4 major version, extracted from the cached header
- [`'\<tb_switch_is_usb4\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1322): whether the router is USB4 compliant, layered on the version helper

### Reaching the adapters and the log (tb.h, switch.c)

- [`'\<tb_switch_for_each_port\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L874): iterate the adapter array between the control port and the last adapter the header reports
- [`'\<tb_dump_switch\>':'drivers/thunderbolt/switch.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1563): print thirteen header members to the debug log as the object is created
- [`'\<__TB_SW_PRINT\>':'drivers/thunderbolt/tb.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L734): prefix a domain log line with the router's route string, under four severity wrappers

## DOCUMENTATION

- [`Documentation/ABI/testing/sysfs-bus-thunderbolt`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt): the userspace names of the identity and policy members, with `authorized` at sysfs-bus-thunderbolt:64, `boot` at sysfs-bus-thunderbolt:98, `generation` at sysfs-bus-thunderbolt:105, `key` at sysfs-bus-thunderbolt:113, `device` at sysfs-bus-thunderbolt:123, `device_name` at sysfs-bus-thunderbolt:130, `vendor` at sysfs-bus-thunderbolt:172, `vendor_name` at sysfs-bus-thunderbolt:179, `unique_id` at sysfs-bus-thunderbolt:186 and `nvm_version` at sysfs-bus-thunderbolt:195
- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst): the security levels and the approval procedure the policy members serve, and the statement that a connection manager can be implemented in firmware or in software

## OTHER SOURCES

- [thunderbolt: Add initial support for USB4 (commit b04079837b20)](https://lore.kernel.org/r/20191217123345.31850-5-mika.westerberg@linux.intel.com)
- [thunderbolt: Add support for Time Management Unit (commit cf29b9afb121)](https://lore.kernel.org/r/20191217123345.31850-8-mika.westerberg@linux.intel.com)
- [thunderbolt: fix memory leak of object sw (commit 704a940d551c)](https://lore.kernel.org/r/20191220220526.11307-1-colin.king@canonical.com)

## REGISTERS

The object caches one piece of register state and reaches everything else on demand. [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) reads five dwords from offset zero of the [`TB_CFG_SWITCH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L18) space into [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L173), which covers the registers the specification numbers Router CS_0 through Router CS_4. Those five dwords are laid out by [`struct tb_regs_switch_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L166), a packed structure of fifteen fields, and the copy serves as both the driver's record of the router's answer and the buffer it later sends back.

```
    Router CS_0 through CS_4 as struct tb_regs_switch_header maps them
    ──────────────────────────────────────────────────────────────────

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
    DW4   │  tb_version   │  __unknown4   │     cmuv      │ plug_ev_delay │
          │    (31:24)    │    (23:16)    │    (15:8)     │     (7:0)     │
          └───────────────┴───────────────┴───────────────┴───────────────┘

    R = __unknown1 (bit 23, carried through unchanged)
    E = enabled = ROUTER_CS_3_V (BIT(31), the software manager's enumerated mark)
    cap_offset = first_cap_offset (where the capability list starts)
    upstream = upstream_port_number, max_port = max_port_number
    plug_ev_delay = plug_events_delay (Notification Timeout, milliseconds)
    cmuv = ROUTER_CS_4_CMUV_V1 (0x10) or ROUTER_CS_4_CMUV_V2 (0x20)
    tb_version = thunderbolt_version, whose bits 7:5 are USB4_VERSION_MAJOR_MASK
```

Three positions in that layout decide behavior this page describes. [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) occupies bit 31 of DW3, the position [`ROUTER_CS_3_V`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L197) names, and [`tb_switch_is_icm()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1023) reads that field as its whole answer. [`USB4_VERSION_MAJOR_MASK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L193) selects bits 7:5 of [`thunderbolt_version`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L189), which [`usb4_switch_version()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1311) extracts. The [`cmuv`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L187) byte takes [`ROUTER_CS_4_CMUV_V1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L200) or [`ROUTER_CS_4_CMUV_V2`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L201) before the copy is uploaded from [`ROUTER_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L195) onward.

The seam that carries every such transfer is [`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) and [`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686), which address port 0 of the router itself and take the offset and length from the caller. No other register content is cached in the object, because the four capability members hold dword offsets into that space, and [`clx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L216) and [`quirks`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L209) hold bits the driver defines for itself. Four members carry values the driver re-reads from adapter registers, [`link_speed`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L184), [`link_width`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L185), [`preferred_link_width`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L186) and the CL word, and the subsections below give each of them its refresh path.

## DETAILS

The subsections below follow the declaration from its first member to its last. They open on the structure as a whole, then take the embedded device, its reference count and the recovery predicates. The cached header follows, with the depth accessor, the debug dump, the classifying predicates, the adapter array and the unplug flag. Then come the identity members, the capability offsets, the firmware buffers, the policy flags, the quirk word and the credit counts. The link attributes, the CL word, the time-management structure and the firmware manager's own members close the page.

### The declaration gathers the router's cached answers into member groups

One structure holds every answer the driver keeps about a router, and its members group by where each answer comes from. The table below names each member of [`struct tb_switch`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L171) by group, and the declaration after it reproduces the kerneldoc and the structure whole. Reading the two together gives the origin of each member before the subsections take them one at a time.

| group | members | where the group's values come from |
|---|---|---|
| the kernel objects | [`dev`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L172), [`tb`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L177), [`ports`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L174), [`dma_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L175), [`tmu`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L176) | the allocation, the add order and the time-management setup |
| the cached header | [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L173) | five dwords read from the router, then patched by the driver |
| identity | [`uid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L178), [`uuid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L179), [`vendor`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L180), [`device`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L181), [`vendor_name`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L182), [`device_name`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L183) | the DROM, a router operation, or a value built from the identifier |
| the link above the router | [`link_speed`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L184), [`link_width`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L185), [`preferred_link_width`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L186), [`link_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L187) | the upstream adapter's own registers, re-read on every link change |
| the protocol generation | [`generation`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L188) | the cached header, classified once during allocation |
| the capability offsets | [`cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189), [`cap_vsec_tmu`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L190), [`cap_lc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L191), [`cap_lp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L192) | four searches of the router's capability list during allocation |
| the unplug latch | [`is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L193) | the unplug path, which raises it on a whole subtree |
| the firmware images | [`drom`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L194), [`nvm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L195), [`no_nvm_upgrade`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L196), [`safe_mode`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L197) | the DROM read, the NVM registration, and the firmware manager for the last |
| policy and diagnostics | [`boot`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L198), [`rpm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L199), [`authorized`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L200), [`security_level`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L201), [`debugfs_dir`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L202), [`key`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L203) | the domain code, userspace through sysfs, and debugfs |
| the firmware manager's messaging | [`connection_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L204), [`connection_key`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L205), [`link`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L206), [`depth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L207), [`rpm_complete`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L208) | messages from the firmware connection manager alone |
| the quirk word | [`quirks`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L209) | the quirk pass, which runs inside the add order |
| the buffer allocation | [`credit_allocation`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L210), [`max_usb3_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L211), [`min_dp_aux_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L212), [`min_dp_main_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L213), [`max_pcie_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L214), [`max_dma_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L215) | one router operation that reports the router's preferences |
| the CL states | [`clx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L216) | the CL helpers, which read the link and then program it |
| the debugfs alias | [`drom_blob`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L218) | the DROM allocation, under [`CONFIG_DEBUG_FS`](https://elixir.bootlin.com/linux/v7.2/source/lib/Kconfig.debug#L708) |

The kerneldoc above [`struct tb_switch`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L171) documents those members in declaration order and closes on the rule that governs the object. Its last two sentences give the locking requirement and the mapping onto the specification's own word for the thing.

```c
/* drivers/thunderbolt/tb.h:112 */
/**
 * struct tb_switch - a thunderbolt switch
 * @dev: Device for the switch
 * @config: Switch configuration
 * @ports: Ports in this switch
 * @dma_port: If the switch has port supporting DMA configuration based
 *	      mailbox this will hold the pointer to that (%NULL
 *	      otherwise). If set it also means the switch has
 *	      upgradeable NVM.
 * @tmu: The switch TMU configuration
 * @tb: Pointer to the domain the switch belongs to
 * @uid: Unique ID of the switch
 * @uuid: UUID of the switch (or %NULL if not supported)
 * @vendor: Vendor ID of the switch
 * @device: Device ID of the switch
 * @vendor_name: Name of the vendor (or %NULL if not known)
 * @device_name: Name of the device (or %NULL if not known)
 * @link_speed: Speed of the link in Gb/s
 * @link_width: Width of the upstream facing link
 * @preferred_link_width: Router preferred link width (only set for Gen 4 links)
 * @link_usb4: Upstream link is USB4
 * @generation: Switch Thunderbolt generation
 * @cap_plug_events: Offset to the plug events capability (%0 if not found)
 * @cap_vsec_tmu: Offset to the TMU vendor specific capability (%0 if not found)
 * @cap_lc: Offset to the link controller capability (%0 if not found)
 * @cap_lp: Offset to the low power (CLx for TBT) capability (%0 if not found)
 * @is_unplugged: The switch is going away
 * @drom: DROM of the switch (%NULL if not found)
 * @nvm: Pointer to the NVM if the switch has one (%NULL otherwise)
 * @no_nvm_upgrade: Prevent NVM upgrade of this switch
 * @safe_mode: The switch is in safe-mode
 * @boot: Whether the switch was already authorized on boot or not
 * @rpm: The switch supports runtime PM
 * @authorized: Whether the switch is authorized by user or policy
 * @security_level: Switch supported security level
 * @debugfs_dir: Pointer to the debugfs structure
 * @key: Contains the key used to challenge the device or %NULL if not
 *	 supported. Size of the key is %TB_SWITCH_KEY_SIZE.
 * @connection_id: Connection ID used with ICM messaging
 * @connection_key: Connection key used with ICM messaging
 * @link: Root switch link this switch is connected (ICM only)
 * @depth: Depth in the chain this switch is connected (ICM only)
 * @rpm_complete: Completion used to wait for runtime resume to
 *		  complete (ICM only)
 * @quirks: Quirks used for this Thunderbolt switch
 * @credit_allocation: Are the below buffer allocation parameters valid
 * @max_usb3_credits: Router preferred number of buffers for USB 3.x
 * @min_dp_aux_credits: Router preferred minimum number of buffers for DP AUX
 * @min_dp_main_credits: Router preferred minimum number of buffers for DP MAIN
 * @max_pcie_credits: Router preferred number of buffers for PCIe
 * @max_dma_credits: Router preferred number of buffers for DMA/P2P
 * @clx: CLx states on the upstream link of the router
 * @drom_blob: DROM debugfs blob wrapper
 *
 * When the switch is being added or removed to the domain (other
 * switches) you need to have domain lock held.
 *
 * In USB4 terminology this structure represents a router.
 */
struct tb_switch {
	struct device dev;
	struct tb_regs_switch_header config;
	struct tb_port *ports;
	struct tb_dma_port *dma_port;
	struct tb_switch_tmu tmu;
	struct tb *tb;
	u64 uid;
	uuid_t *uuid;
	u16 vendor;
	u16 device;
	const char *vendor_name;
	const char *device_name;
	unsigned int link_speed;
	enum tb_link_width link_width;
	enum tb_link_width preferred_link_width;
	bool link_usb4;
	unsigned int generation;
	int cap_plug_events;
	int cap_vsec_tmu;
	int cap_lc;
	int cap_lp;
	bool is_unplugged;
	u8 *drom;
	struct tb_nvm *nvm;
	bool no_nvm_upgrade;
	bool safe_mode;
	bool boot;
	bool rpm;
	unsigned int authorized;
	enum tb_security_level security_level;
	struct dentry *debugfs_dir;
	u8 *key;
	u8 connection_id;
	u8 connection_key;
	u8 link;
	u8 depth;
	struct completion rpm_complete;
	unsigned long quirks;
	bool credit_allocation;
	unsigned int max_usb3_credits;
	unsigned int min_dp_aux_credits;
	unsigned int min_dp_main_credits;
	unsigned int max_pcie_credits;
	unsigned int max_dma_credits;
	unsigned int clx;
#ifdef CONFIG_DEBUG_FS
	struct debugfs_blob_wrapper drom_blob;
#endif
};
```

[`struct tb_switch`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L171) opens with six members that give the object an identity inside the kernel. They are the embedded device, the header copy, the adapter array, the mailbox pointer, the time-management state and the domain.

Eleven members carry a kerneldoc line saying that zero or NULL means the thing is absent. Every reader of a pointer or an offset on this page applies that convention. The kerneldoc marks [`safe_mode`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L197) and the five messaging members as the firmware connection manager's. Its closing paragraph requires the domain lock held while a router joins or leaves the domain.

The declaration reads as the router's own history, because each group is written by the step that can first answer it. The subsections below take the groups in that order, from the embedded device to the members only the firmware connection manager writes.

### The embedded device anchors the object in the driver core

A router becomes a kernel device before anything else can reach it, and the allocation prepares that device last. The three excerpts below show the preparation inside [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451), then the pair of inline helpers that move the reference count, then the one call site of the taking helper. Between them they account for every reference the driver holds on a router.

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) initializes the embedded device and fills the four fields the bus needs before it returns the object.

```c
/* drivers/thunderbolt/switch.c:2539 */
	device_initialize(&sw->dev);
	sw->dev.parent = parent;
	sw->dev.bus = &tb_bus_type;
	sw->dev.type = &tb_switch_type;
	sw->dev.groups = switch_groups;
	dev_set_name(&sw->dev, "%u-%llx", tb->index, tb_route(sw));
```

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) calls [`device_initialize()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3227) on [`dev`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L172), which sets the reference count to one and makes the release callback the owner of the memory from that moment. The parent, the bus, the device type and the attribute groups follow, and [`dev_set_name()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3554) composes the router's name from the domain index and its route string. The object is not on the bus yet, so that first reference belongs to whoever called the allocation.

[`tb_switch_get()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L878) and [`tb_switch_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L885) are the whole of the reference interface, and the taking one accepts NULL so that a lookup which found nothing can be returned through it.

```c
/* drivers/thunderbolt/tb.h:878 */
static inline struct tb_switch *tb_switch_get(struct tb_switch *sw)
{
	if (sw)
		get_device(&sw->dev);
	return sw;
}

static inline void tb_switch_put(struct tb_switch *sw)
{
	put_device(&sw->dev);
}
```

[`tb_switch_get()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L878) calls [`get_device()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3866) for a non-NULL argument and returns the argument either way, which makes it usable as the tail of a lookup. [`tb_switch_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L885) calls [`put_device()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3876) on whatever it is given, so the caller has to hold a reference and a NULL object faults. Both reach the embedded [`dev`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L172) and touch no other member.

[`tb_switch_find_by_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3848) is the one call site of the taking helper, and it uses it on the route that names the host router.

```c
/* drivers/thunderbolt/switch.c:3848 */
struct tb_switch *tb_switch_find_by_route(struct tb *tb, u64 route)
{
	struct tb_sw_lookup lookup;
	struct device *dev;

	if (!route)
		return tb_switch_get(tb->root_switch);

```

[`tb_switch_find_by_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3848) reaches [`root_switch`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L88) of the domain directly for route 0 and hands back a reference. That early return matches what the slower lookup below it promises in its kerneldoc. Every other reference comes from [`device_initialize()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3227) at allocation or from a driver-core lookup that raises the count itself.

Those lookups are at [switch.c:3805](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3805), [switch.c:3831](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3831) and [switch.c:3860](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3860). The embedded device is therefore the object's whole identity in the driver core, and its count decides how long the object exists.

### The last reference drop frees every pointer the object owns

Releasing a router hands back the mailbox, the adapter array, five heap buffers and the object itself. One callback does all of that at the last reference drop. Three blocks follow, the figure showing the object on each side of the callback, the callback itself, and a drop that reaches it.

```
    struct tb_switch across the release callback
    ────────────────────────────────────────────

    before                                     after
    ┌────────────────────────────────┐         ┌────────────────────────────────┐
    │ dma_port  ──▶ mailbox object   │         │ mailbox object      freed      │
    │ ports     ──▶ tb_port[0 .. N]  │         │ tb_port[0 .. N]     freed      │
    │                two IDAs each   │   ──▶   │ every IDA above 0   destroyed  │
    │ uuid device_name vendor_name   │         │ those three buffers freed      │
    │ drom key                       │         │ those two buffers   freed      │
    │ dev (embedded, by value)       │         │ the allocation      freed      │
    └────────────────────────────────┘         └────────────────────────────────┘

    the embedded device needs no free of its own, because the final kfree
    releases the allocation it occupies
```

[`tb_switch_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2288) is the release callback of the router device type, so the driver core calls it when the count reaches zero.

```c
/* drivers/thunderbolt/switch.c:2288 */
static void tb_switch_release(struct device *dev)
{
	struct tb_switch *sw = tb_to_switch(dev);
	struct tb_port *port;

	dma_port_free(sw->dma_port);

	tb_switch_for_each_port(sw, port) {
		ida_destroy(&port->in_hopids);
		ida_destroy(&port->out_hopids);
	}

	kfree(sw->uuid);
	kfree(sw->device_name);
	kfree(sw->vendor_name);
	kfree(sw->ports);
	kfree(sw->drom);
	kfree(sw->key);
	kfree(sw);
}
```

[`tb_switch_release()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2288) recovers the object from the device it was handed and hands the mailbox back through [`dma_port_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L227). It destroys the two HopID allocators of every adapter above zero, then frees [`uuid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L179), [`device_name`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L183), [`vendor_name`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L182), [`ports`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L174), [`drom`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L194) and [`key`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L203) with [`kfree()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/slab.h#L592). The [`nvm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L195) handle is absent from that run because the removal path clears it earlier. The embedded [`dev`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L172) is absent because the last [`kfree()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/slab.h#L592) releases the allocation it occupies.

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) shows the shape of a drop that reaches the callback directly, discarding a router whose configuration step failed.

```c
/* drivers/thunderbolt/tb.c:1344 */
	if (tb_switch_configure(sw)) {
		tb_switch_put(sw);
		goto out_rpm_put;
	}
```

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) calls [`tb_switch_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L885) on the reference the allocation gave it, which is the only reference on an object [`device_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L3639) has yet to see. The drop therefore reaches the release callback at once, and the object goes away with most of its members still holding the zeroes the allocation left. The embedded device owns the memory, so one callback frees every pointer the object holds.

### Type checks recover a router from a bare device pointer

Code handed a bare device pointer decides whether it belongs to a router by reading the device type alone. That keeps the test usable from any subsystem, and it makes the device hierarchy the only tree these helpers read. Three blocks follow, the figure of that hierarchy, the excerpt holding the three helpers, and a pass that uses two of them.

```
    the device hierarchy, the only record of the tree these helpers read
    ────────────────────────────────────────────────────────────────────

                     the domain device
                     ┌────────────────────────────────┐
                     │ dev.type is not tb_switch_type │
                     └────────────────▲───────────────┘
                                      │ dev.parent
                     ┌────────────────┴───────────────┐
                     │ host router at route 0         │
                     │ dev.type = tb_switch_type      │
                     └───────▲────────────────▲───────┘
                             │ dev.parent     │ dev.parent
            ┌────────────────┴─────┐   ┌──────┴─────────────────┐
            │ device router        │   │ device router          │
            │ dev.type =           │   │ dev.type =             │
            │ tb_switch_type       │   │ tb_switch_type         │
            └──────────────────────┘   └────────────────────────┘

    a device of any other type converts to NULL, so the parent of the host
    router answers NULL and the parent of a device router answers the router
    above it
```

[`tb_is_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L890) answers the question, [`tb_to_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L895) recovers the object by calling that predicate first, and [`tb_switch_parent()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L902) applies the same recovery to the parent device.

```c
/* drivers/thunderbolt/tb.h:890 */
static inline bool tb_is_switch(const struct device *dev)
{
	return dev->type == &tb_switch_type;
}

static inline struct tb_switch *tb_to_switch(const struct device *dev)
{
	if (tb_is_switch(dev))
		return container_of(dev, struct tb_switch, dev);
	return NULL;
}

static inline struct tb_switch *tb_switch_parent(struct tb_switch *sw)
{
	return tb_to_switch(sw->dev.parent);
}
```

[`tb_is_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L890) compares [`type`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L710) of the device against [`tb_switch_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2373), the [`struct device_type`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L87) the router allocation installs. [`tb_to_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L895) turns a passing device into the object with [`container_of()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/container_of.h#L19) and answers NULL for every other type. [`tb_switch_parent()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L902) applies that conversion to [`parent`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L705) of the embedded device, which is how a router reaches the router above it.

[`tb_scan_finalize_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2974) runs over the device tree after a scan and uses the first two helpers together.

```c
/* drivers/thunderbolt/tb.c:2974 */
static int tb_scan_finalize_switch(struct device *dev, void *data)
{
	if (tb_is_switch(dev)) {
		struct tb_switch *sw = tb_to_switch(dev);

		/*
		 * If we found that the switch was already setup by the
		 * boot firmware, mark it as authorized now before we
		 * send uevent to userspace.
		 */
		if (sw->boot)
			sw->authorized = 1;

		dev_set_uevent_suppress(dev, false);
		kobject_uevent(&dev->kobj, KOBJ_ADD);
		device_for_each_child(dev, NULL, tb_scan_finalize_switch);
	}
```

[`tb_scan_finalize_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2974) is handed every child device of a domain, tests it with [`tb_is_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L890) and converts it with [`tb_to_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L895) inside the guard, so the conversion cannot answer NULL there. The body copies [`boot`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L198) into [`authorized`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L200) before the add event reaches userspace, then recurses into the children through [`device_for_each_child()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L4089).

So far, the object exists with its device initialized, its reference count at one and its memory owned by the driver core. Reading the device type is enough to move from any device pointer to the router object and to its parent.

### The cached header records the router's own answer

The five dwords at offset zero of a router's configuration space say where it is, how many adapters it has and what it implements. The object keeps the copy that read produced, in a packed structure whose fields map the wire layout. The two excerpts below are the declaration that gives that layout and the read that fills the copy.

[`struct tb_regs_switch_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L166) declares fifteen fields grouped by dword, with a comment above it saying where the hardware presents them.

```c
/* drivers/thunderbolt/tb_regs.h:165 */
/* Present on port 0 in TB_CFG_SWITCH at address zero. */
struct tb_regs_switch_header {
	/* DWORD 0 */
	u16 vendor_id;
	u16 device_id;
	/* DWORD 1 */
	u32 first_cap_offset:8;
	u32 upstream_port_number:6;
	u32 max_port_number:6;
	u32 depth:3;
	u32 __unknown1:1;
	u32 revision:8;
	/* DWORD 2 */
	u32 route_lo;
	/* DWORD 3 */
	u32 route_hi:31;
	bool enabled:1;
	/* DWORD 4 */
	u32 plug_events_delay:8; /*
				  * RW, pause between plug events in
				  * milliseconds.
				  */
	u32 cmuv:8;
	u32 __unknown4:8;
	u32 thunderbolt_version:8;
} __packed;
```

[`struct tb_regs_switch_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L166) puts [`vendor_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L168) and [`device_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L169) in DWORD 0, the pair the quirk pass and the generation classifier match on. DWORD 1 packs [`first_cap_offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L171), [`upstream_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L172), [`max_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L173), [`depth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L174), [`__unknown1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L175) and [`revision`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L176) into six bitfields. DWORD 2 and DWORD 3 carry [`route_lo`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L178), [`route_hi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L180) and the one-bit [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181).

DWORD 4 holds [`plug_events_delay`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L183), whose comment marks it read-write and gives its unit as milliseconds, beside [`cmuv`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L187), [`__unknown4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L188) and [`thunderbolt_version`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L189). The structure is marked packed, so a five-dword read lands in it unmodified.

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) makes that read its second act, straight after zeroing the object.

```c
/* drivers/thunderbolt/switch.c:2473 */
	sw = kzalloc_obj(*sw);
	if (!sw)
		return ERR_PTR(-ENOMEM);

	sw->tb = tb;
	ret = tb_cfg_read(tb->ctl, &sw->config, route, 0, TB_CFG_SWITCH, 0, 5);
```

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) zeroes the whole object through [`kzalloc_obj()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/slab.h#L1152), so every member this page describes starts at zero or NULL. It stores the domain in [`tb`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L177) and then calls [`tb_cfg_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1111) with the control channel taken from its own argument, five dwords straight into [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L173). From that statement onward the copy carries the router's own answer about itself.

### The allocation patches five header fields before anything is sent

The copy doubles as the buffer the driver sends back, so the allocation overwrites the five fields that describe the connection the driver is building. Five fields change in one run, and the figure after the excerpt shows the copy on each side of that run. The last of the three blocks is the version write and the upload that sends four of the five dwords.

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) patches the copy under a comment naming the act.

```c
/* drivers/thunderbolt/switch.c:2487 */
	/* configure switch */
	sw->config.upstream_port_number = upstream_port;
	sw->config.depth = depth;
	sw->config.route_hi = upper_32_bits(route);
	sw->config.route_lo = lower_32_bits(route);
	sw->config.enabled = 0;
```

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) writes the upstream adapter number the control channel reported, the depth computed from the route, the two halves of the route and a cleared [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) field. All five writes land in memory, so the copy now describes the connection the driver is building.

```
    the cached copy before and after the allocation patches it
    ──────────────────────────────────────────────────────────

    before, as the router answered          after, as the driver needs it
    ┌─────────────────────────────┐         ┌─────────────────────────────┐
    │ vendor_id  device_id        │         │ vendor_id  device_id        │
    │ first_cap_offset            │         │ first_cap_offset            │
    │ upstream_port_number  ·     │   ──▶   │ upstream_port_number  ◀ ctl │
    │ max_port_number             │         │ max_port_number             │
    │ depth                 ·     │         │ depth                 ◀ len │
    │ __unknown1  revision        │         │ __unknown1  revision        │
    │ route_lo route_hi     ·     │         │ route_lo route_hi     ◀ arg │
    │ enabled               ·     │         │ enabled               = 0   │
    │ DWORD 4, four bytes         │         │ DWORD 4, four bytes         │
    └─────────────────────────────┘         └─────────────────────────────┘

    ctl = the upstream adapter the control channel reported
    len = the hop count of the route string
    arg = the route string the caller asked for
    the other ten fields keep whatever the router answered
```

Four of the five dwords go back to the router later, when the configure step sets [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) again and uploads the copy. [`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) makes that change and that upload.

```c
/* drivers/thunderbolt/switch.c:2617 */
	sw->config.enabled = 1;

	/* Set Notification Timeout to 255 ms for all routers */
	sw->config.plug_events_delay = 0xff;
/* drivers/thunderbolt/switch.c:2628, the version write and the upload of dwords 1 through 4 */
		if (usb4_switch_version(sw) < 2)
			sw->config.cmuv = ROUTER_CS_4_CMUV_V1;
		else
			sw->config.cmuv = ROUTER_CS_4_CMUV_V2;

		/* Enumerate the switch */
		ret = tb_sw_write(sw, (u32 *)&sw->config + 1, TB_CFG_SWITCH,
				  ROUTER_CS_1, 4);
```

[`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) sets [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) back to 1 and writes 0xff into [`plug_events_delay`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L183). The comment above that write gives it as a Notification Timeout of 255 milliseconds for every router.

It then sets [`cmuv`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L187) from the major version [`usb4_switch_version()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1311) extracts, taking the first constant below 2 and the second at or above it. It hands [`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686) the address one dword past the base of [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L173) and a length of four, so DWORD 1 through DWORD 4 reach [`ROUTER_CS_1`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L195) onward. The copy is therefore the driver's record of the router and the source of what the router is told about itself.

### The depth accessor reads one patched header field

The depth a router reports through its accessor is the driver's own hop count from the host router. Three bits of the header hold it, the allocation writes it, and one policy decision in the domain code reads it. The three blocks below are the accessor, a figure of what the reader does with the number, and the climb that makes the decision.

[`tb_switch_depth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L928) returns the field and nothing else, under a kerneldoc that gives the unit.

```c
/* drivers/thunderbolt/tb.h:922 */
/**
 * tb_switch_depth() - Returns depth of the connected router
 * @sw: Router
 *
 * Return: Router depth level as a number.
 */
static inline int tb_switch_depth(const struct tb_switch *sw)
{
	return sw->config.depth;
}
```

[`tb_switch_depth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L928) returns the patched [`depth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L174) field, so it reports the hop count the driver computed from the route string. A host router is reached by route 0, whose hop count is 0, so its field holds 0. The three bits the wire gives the field bound what it can express.

```
    which routers the CL policy can reach from the link above them
    ──────────────────────────────────────────────────────────────
    (depth is the field the allocation patched; the policy acts on
     the link above the router it settles on)

    depth 0   ┌──────────────── host router ─────────────────┐
              │ the climb stops here only when nothing is    │
              │ found, and the policy then returns           │
              └───────┬──────────────────────┬───────────────┘
                      │                      │
              ┌───────┴───────┐      ┌───────┴───────┐
    depth 1   │ device router │      │ device router │  the policy acts
              └───────┬───────┘      └───────────────┘  on this link
                      │
        ─ ─ ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  above this line
              ┌───────┴───────┐                          the climb walks up
    depth 2   │ device router │  the climb starts here
              └───────┬───────┘  and moves to its parent
                      │
              ┌───────┴───────┐
    depth 3   │ device router │  the climb starts here too
              └───────────────┘
```

The climb is in [`tb_enable_clx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L184), which makes two of the three calls to the accessor in the driver.

```c
/* drivers/thunderbolt/tb.c:198 */
	while (sw && tb_switch_depth(sw) > 1)
		sw = tb_switch_parent(sw);

	if (!sw)
		return 0;

	if (tb_switch_depth(sw) != 1)
		return 0;
```

[`tb_enable_clx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L184) climbs to the parent while the depth exceeds 1, then requires the depth to equal 1 before it goes on. A host router, whose depth is 0, leaves the loop unrun and returns 0 at the second test, so the policy never reaches its own link.

The third call to the accessor is at [tb.c:1257](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1257), where the same test above 1 admits a deeper router to a symmetric-link transition. The accessor therefore answers a question about position in the tree, the question the patched field records.

### The debug dump prints the header before the patch

The header copy is complete and unpatched for exactly one statement, and the dump runs there. It prints thirteen of the fifteen fields, so the debug log holds what the router itself answered. The three excerpts below are the dump, the helper that names the generation for its first line, and the one call site.

[`tb_dump_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1563) takes a local pointer to the copy and prints it over five log lines.

```c
/* drivers/thunderbolt/switch.c:1563 */
static void tb_dump_switch(const struct tb *tb, const struct tb_switch *sw)
{
	const struct tb_regs_switch_header *regs = &sw->config;

	tb_dbg(tb, " %s Switch: %x:%x (Revision: %d, TB Version: %d)\n",
	       tb_switch_generation_name(sw), regs->vendor_id, regs->device_id,
	       regs->revision, regs->thunderbolt_version);
	tb_dbg(tb, "  Max Port Number: %d\n", regs->max_port_number);
	tb_dbg(tb, "  Config:\n");
	tb_dbg(tb,
		"   Upstream Port Number: %d Depth: %d Route String: %#llx Enabled: %d, PlugEventsDelay: %dms\n",
	       regs->upstream_port_number, regs->depth,
	       (((u64) regs->route_hi) << 32) | regs->route_lo,
	       regs->enabled, regs->plug_events_delay);
	tb_dbg(tb, "   unknown1: %#x unknown4: %#x\n",
	       regs->__unknown1, regs->__unknown4);
}
```

[`tb_dump_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1563) prints every field of [`config`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L173) except [`first_cap_offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L171) and [`cmuv`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L187), the two the driver reaches through helpers of their own. It recombines [`route_hi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L180) and [`route_lo`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L178) into one 64-bit value by shifting the high half left by 32. Its first line opens with the name that [`tb_switch_generation_name()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1547) derives from a member outside the header.

[`tb_switch_generation_name()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1547) turns the small integer in that member into the protocol name.

```c
/* drivers/thunderbolt/switch.c:1547 */
static const char *tb_switch_generation_name(const struct tb_switch *sw)
{
	switch (sw->generation) {
	case 1:
		return "Thunderbolt 1";
	case 2:
		return "Thunderbolt 2";
	case 3:
		return "Thunderbolt 3";
	case 4:
		return "USB4";
	default:
		return "Unknown";
	}
}
```

[`tb_switch_generation_name()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1547) reads [`generation`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L188) and maps 1 through 3 onto the Thunderbolt names and 4 onto `USB4`, with every other value producing `Unknown`. The member is filled one statement before the dump runs, so the name is available to the first line the dump prints.

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) places the classification and the dump between the read and the patch.

```c
/* drivers/thunderbolt/switch.c:2482 */
	sw->generation = tb_switch_get_generation(sw);

	tb_dbg(tb, "current switch config:\n");
	tb_dump_switch(tb, sw);
```

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) classifies the router into [`generation`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L188) first, so the dump can name it, and calls [`tb_dump_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1563) two statements later. The patch of the copy follows immediately, so the line that prints "current switch config" is the only record of the router's own view.

So far, the object holds the header as the router answered it, patched with the connection the driver is building, and a log line holds the unpatched view. The dump runs at that one call site and nowhere else.

### Predicates classify a router out of the cached header

The driver takes different paths for a router the firmware manager owns and for a USB4 router, and both questions are answered out of the cached header. Three inline predicates carry the answers, two of them layered on the third, and none of them reaches hardware. The two excerpts below hold all three with their kerneldoc, and one optional step guarded by two of them.

[`tb_switch_is_icm()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1023) reads one field of the copy under a kerneldoc that gives its valid window, and [`usb4_switch_version()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1311) and [`tb_switch_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1322) follow it in the second unit.

```c
/* drivers/thunderbolt/tb.h:1011 */
/**
 * tb_switch_is_icm() - Is the switch handled by ICM firmware
 * @sw: Switch to check
 *
 * In case there is a need to differentiate whether ICM firmware or SW CM
 * is handling @sw this function can be called. It is valid to call this
 * after tb_switch_alloc() and tb_switch_configure() has been called
 * (latter only for SW CM case).
 *
 * Return: %true if switch is handled by ICM, %false if handled by
 * software CM.
 */
static inline bool tb_switch_is_icm(const struct tb_switch *sw)
{
	return !sw->config.enabled;
}
/* drivers/thunderbolt/tb.h:1304, usb4_switch_version() and tb_switch_is_usb4() */
/**
 * usb4_switch_version() - Returns USB4 version of the router
 * @sw: Router to check
 *
 * Return: Major version of USB4 router (%1 for v1, %2 for v2 and so
 * on). Can be called to pre-USB4 router too and in that case returns %0.
 */
static inline unsigned int usb4_switch_version(const struct tb_switch *sw)
{
	return FIELD_GET(USB4_VERSION_MAJOR_MASK, sw->config.thunderbolt_version);
}

/**
 * tb_switch_is_usb4() - Is the switch USB4 compliant
 * @sw: Switch to check
 *
 * Return: %true if the @sw is USB4 compliant router, %false otherwise.
 */
static inline bool tb_switch_is_usb4(const struct tb_switch *sw)
{
	return usb4_switch_version(sw) > 0;
}
```

[`tb_switch_is_icm()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1023) answers true while [`enabled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L181) is clear, so a router the software connection manager has configured answers false and every other router answers true. Its kerneldoc puts the valid window after the allocation and, for the software manager, after the configure step that sets the field. [`usb4_switch_version()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1311) extracts the top three bits of [`thunderbolt_version`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L189) with [`FIELD_GET()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/bitfield.h#L175), and [`tb_switch_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1322) is the test that the extracted value exceeds zero.

[`tb_switch_credits_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3256) shows both discriminators as consecutive guards on one optional step of the add order.

```c
/* drivers/thunderbolt/switch.c:3256 */
static void tb_switch_credits_init(struct tb_switch *sw)
{
	if (tb_switch_is_icm(sw))
		return;
	if (!tb_switch_is_usb4(sw))
		return;
	if (usb4_switch_credits_init(sw))
		tb_sw_info(sw, "failed to determine preferred buffer allocation, using defaults\n");
}
```

[`tb_switch_credits_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3256) returns without acting when the firmware manager owns the router, because the router operation behind [`usb4_switch_credits_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L758) belongs to the manager that enumerated it. It returns again when the version predicate answers false, which no pre-USB4 router can pass.

A failure of the operation itself produces an informational line and no error, which leaves the six credit members at zero. Both questions are therefore settled from the copy alone, at any time after the header has been read.

### The header sizes the adapter array and bounds its iterator

An adapter of a router is addressed by number, and the object keeps one [`struct tb_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L280) per number in a flat array. The array is sized from the header the allocation has already read, and index 0 is the control port that carries the router's own configuration space. The three excerpts below build the array, give the iterator that every later traversal uses, and show a traversal over a subset of the adapters.

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) allocates the array from the header field and gives every entry its number.

```c
/* drivers/thunderbolt/switch.c:2500 */
	/* initialize ports */
	sw->ports = kzalloc_objs(*sw->ports, sw->config.max_port_number + 1);
	if (!sw->ports) {
		ret = -ENOMEM;
		goto err_free_sw_ports;
	}

	for (i = 0; i <= sw->config.max_port_number; i++) {
		/* minimum setup for tb_find_cap and tb_drom_read to work */
		sw->ports[i].sw = sw;
		sw->ports[i].port = i;

		/* Control port does not need HopID allocation */
		if (i) {
			ida_init(&sw->ports[i].in_hopids);
			ida_init(&sw->ports[i].out_hopids);
		}
	}
```

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) allocates [`max_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L173) plus one entries with [`kzalloc_objs()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/slab.h#L1154), so index 0 through the highest adapter number are addressable. The loop gives every entry a back pointer to the owning object and its own number. Its comment names that pair of writes as the minimum the capability search and the DROM read require. It initializes the two HopID allocators for every index but 0, and the comment above the condition gives the control port as the reason.

[`tb_switch_for_each_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L874) encodes both bounds, so no caller repeats them.

```c
/* drivers/thunderbolt/tb.h:867 */
/**
 * tb_switch_for_each_port() - Iterate over each switch port
 * @sw: Switch whose ports to iterate
 * @p: Port used as iterator
 *
 * Iterates over each switch port skipping the control port (port %0).
 */
#define tb_switch_for_each_port(sw, p)					\
	for ((p) = &(sw)->ports[1];					\
	     (p) <= &(sw)->ports[(sw)->config.max_port_number]; (p)++)
```

[`tb_switch_for_each_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L874) starts the iterator at index 1 and ends it at [`max_port_number`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L173) inclusive, reading the same cached field the array was sized from. A router that reports zero adapters runs the body zero times, since the start pointer already exceeds the end. The macro re-reads the field on every iteration, which is safe because the allocation is the last write to it.

[`tb_switch_port_hotplug_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3266) shows the shape of a traversal that acts on a subset of the adapters.

```c
/* drivers/thunderbolt/switch.c:3266 */
static int tb_switch_port_hotplug_enable(struct tb_switch *sw)
{
	struct tb_port *port;

	if (tb_switch_is_icm(sw))
		return 0;

	tb_switch_for_each_port(sw, port) {
		int res;

		if (!port->cap_usb4)
			continue;

		res = usb4_port_hotplug_enable(port);
		if (res)
			return res;
	}
	return 0;
}
```

[`tb_switch_port_hotplug_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3266) returns at once on a router the firmware manager owns, then hands the iterator every adapter from 1 upward. The body skips each adapter whose USB4 port capability offset is zero, so the control port is never a candidate and no bound is written at the call site. Thirty-five traversals outside the firmware manager's file use the macro, and each inherits the same two bounds from the header.

So far, the object carries the header, an adapter array sized from it and the three predicates that classify the router from the same copy. The array's length and the iterator's bounds both come from one field, so a caller states neither.

### The unplug flag latches and reaches the whole subtree

A router that has been pulled out still has an object, and every path that would touch its hardware has to fail at once. One boolean carries that state, and the path that sets it marks the router and every router below. The three blocks below are the function that raises it, a table of the three classes of reader, and one of those readers.

[`tb_sw_set_unplugged()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3471) holds the one assignment on the software connection manager's paths, and it refuses two cases before it acts.

```c
/* drivers/thunderbolt/switch.c:3471 */
void tb_sw_set_unplugged(struct tb_switch *sw)
{
	struct tb_port *port;

	if (sw == sw->tb->root_switch) {
		tb_sw_WARN(sw, "cannot unplug root switch\n");
		return;
	}
	if (sw->is_unplugged) {
		tb_sw_WARN(sw, "is_unplugged already set\n");
		return;
	}
	sw->is_unplugged = true;
	tb_switch_for_each_port(sw, port) {
		if (tb_port_has_remote(port))
			tb_sw_set_unplugged(port->remote->sw);
		else if (port->xdomain)
			port->xdomain->is_unplugged = true;
	}
}
```

[`tb_sw_set_unplugged()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3471) compares the object against [`root_switch`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L88) of the domain and returns without acting when they match. It returns again when [`is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L193) is already true, which is the enforcement that makes the flag a latch. After the assignment it iterates the adapters and calls itself for each adapter that has a router behind it. An adapter holding a cross-domain connection instead gets the peer object's own flag of that name, so one call marks a whole subtree.

Three call sites reach that function, [tb.c:2463](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2463) on unplug, [switch.c:3596](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3596) and [switch.c:3610](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3610) on a resume failure. Fourteen sites read the flag back, and the table gives each class of reader what it does while the flag is raised.

| class of reader | what it does while the flag is raised | at |
|---|---|---|
| the four configuration wrappers | answer `-ENODEV` without sending a packet | [tb.h:675](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L675), [tb.h:689](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L689), [tb.h:703](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L703), [tb.h:717](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L717) |
| the teardown paths | skip the hardware work they would otherwise do | [switch.c:571](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L571), [switch.c:3246](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3246), [switch.c:3456](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3456), [clx.c:410](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L410) |
| the traversal and policy guards | treat the router as gone and pass over it | [path.c:602](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L602), [path.c:604](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L604), [tb.c:1172](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1172), [tb.c:1798](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1798), [tb.c:3096](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3096) |

[`tb_path_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L598) is the clearest of the third class, because it reads the flag on both ends of every hop.

```c
/* drivers/thunderbolt/path.c:598 */
bool tb_path_is_invalid(struct tb_path *path)
{
	int i = 0;
	for (i = 0; i < path->path_length; i++) {
		if (path->hops[i].in_port->sw->is_unplugged)
			return true;
		if (path->hops[i].out_port->sw->is_unplugged)
			return true;
	}
	return false;
}
```

[`tb_path_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L598) declares a tunnel path invalid as soon as either adapter of any hop carries the flag, so the teardown that follows never programs a router that has gone. The flag is one-way on these paths, and the firmware connection manager holds the only clear of it. Raising it on one router therefore stops every access to that router and to everything below it.

### The register seam builds each transaction from three members

A configuration transaction the driver sends through the router wrappers is assembled from three members of the object, and a fourth decides whether it is sent at all. The caller supplies what is carried, so the object supplies the destination and the permission. The four blocks below name the parts, then give the pair of wrappers, the address helper they call, and the smallest use of the seam in the driver.

```
    which members of the object build one configuration transaction
    ───────────────────────────────────────────────────────────────

    struct tb_switch                      caller arguments
    ┌───────────────────────────┐         ┌────────────────────┐
    │ is_unplugged              │         │ buffer             │
    │ tb ──▶ ctl                │         │ space, offset      │
    │ config.route_hi, route_lo │         │ length             │
    └─────────────┬─────────────┘         └─────────┬──────────┘
                  │ -ENODEV when raised             │
                  └────────────────┬────────────────┘
                                   ▼
              ┌────────────────────────────────────────┐
              │ one request to port 0 of the router at │
              │ tb_route(sw), over the domain channel  │
              └────────────────────────────────────────┘
```

[`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) and [`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686) read the flag first and then assemble the transaction from the rest of the object.

```c
/* drivers/thunderbolt/tb.h:672 */
static inline int tb_sw_read(struct tb_switch *sw, void *buffer,
			     enum tb_cfg_space space, u32 offset, u32 length)
{
	if (sw->is_unplugged)
		return -ENODEV;
	return tb_cfg_read(sw->tb->ctl,
			   buffer,
			   tb_route(sw),
			   0,
			   space,
			   offset,
			   length);
}

static inline int tb_sw_write(struct tb_switch *sw, const void *buffer,
			      enum tb_cfg_space space, u32 offset, u32 length)
{
	if (sw->is_unplugged)
		return -ENODEV;
	return tb_cfg_write(sw->tb->ctl,
			    buffer,
			    tb_route(sw),
			    0,
			    space,
			    offset,
			    length);
}
```

[`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) and [`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686) answer `-ENODEV` while [`is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L193) is true, and otherwise reach the control channel [`ctl`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L86) of the domain [`tb`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L177) names. Both address the router by [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) and the literal port number 0, and take the space, the offset and the length from the caller. The adapter wrappers at [tb.h:703](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L703) and [tb.h:717](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L717) repeat the same test through the owning router.

[`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) recomposes the address from the two header halves on every call, so no separate member holds it.

```c
/* drivers/thunderbolt/tb.h:583 */
static inline u64 tb_route(const struct tb_switch *sw)
{
	return ((u64) sw->config.route_hi) << 32 | sw->config.route_lo;
}
```

[`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) shifts [`route_hi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L180) left by 32 and merges [`route_lo`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L178) below it, reading the two fields the allocation patched. A host router carries 0 in both halves, which is how the seam addresses it and how the sysfs handlers recognize it. The header read of the allocation itself misses this gate, because it calls [`tb_cfg_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1111) directly on an object whose members are still zero.

[`tb_eeprom_ctl_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L18) and [`tb_eeprom_ctl_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L26) are the smallest use of the seam and show how thin the wrapper is.

```c
/* drivers/thunderbolt/eeprom.c:15 */
/*
 * tb_eeprom_ctl_write() - write control word
 */
static int tb_eeprom_ctl_write(struct tb_switch *sw, struct tb_eeprom_ctl *ctl)
{
	return tb_sw_write(sw, ctl, TB_CFG_SWITCH, sw->cap_plug_events + ROUTER_CS_4, 1);
}

/*
 * tb_eeprom_ctl_read() - read control word
 */
static int tb_eeprom_ctl_read(struct tb_switch *sw, struct tb_eeprom_ctl *ctl)
{
	return tb_sw_read(sw, ctl, TB_CFG_SWITCH, sw->cap_plug_events + ROUTER_CS_4, 1);
}
```

[`tb_eeprom_ctl_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L18) and [`tb_eeprom_ctl_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L26) pass one dword at an offset computed from the cached [`cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189) offset. The gate is applied once in the wrappers and inherited by every caller, the fifty-four call sites of [`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) and the thirty-seven of [`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686) across eight files each. Three members therefore decide where a transaction goes, and a fourth decides whether it goes at all.

### Every router log line carries the route string as prefix

A domain can hold many routers, so a log line naming only the domain leaves the reader unable to tell which router produced it. One macro family solves that by taking the router object and prefixing the message with its route string. The two excerpts below hold the domain-level macros with the router-level family built on them, and a function that uses three of the four severities.

[`__TB_SW_PRINT()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L734) is layered on the domain macros above it, from [`tb_err()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L728) down, which print through the host interface device that owns the domain.

```c
/* drivers/thunderbolt/tb.h:728 */
#define tb_err(tb, fmt, arg...) dev_err((tb)->nhi->dev, fmt, ## arg)
#define tb_WARN(tb, fmt, arg...) dev_WARN((tb)->nhi->dev, fmt, ## arg)
#define tb_warn(tb, fmt, arg...) dev_warn((tb)->nhi->dev, fmt, ## arg)
#define tb_info(tb, fmt, arg...) dev_info((tb)->nhi->dev, fmt, ## arg)
#define tb_dbg(tb, fmt, arg...) dev_dbg((tb)->nhi->dev, fmt, ## arg)

#define __TB_SW_PRINT(level, sw, fmt, arg...)           \
	do {                                            \
		const struct tb_switch *__sw = (sw);    \
		level(__sw->tb, "%llx: " fmt,           \
		      tb_route(__sw), ## arg);          \
	} while (0)
#define tb_sw_WARN(sw, fmt, arg...) __TB_SW_PRINT(tb_WARN, sw, fmt, ##arg)
#define tb_sw_warn(sw, fmt, arg...) __TB_SW_PRINT(tb_warn, sw, fmt, ##arg)
#define tb_sw_info(sw, fmt, arg...) __TB_SW_PRINT(tb_info, sw, fmt, ##arg)
#define tb_sw_dbg(sw, fmt, arg...) __TB_SW_PRINT(tb_dbg, sw, fmt, ##arg)
```

[`__TB_SW_PRINT()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L734) copies its argument into a local pointer so an expression with side effects is evaluated once. It then calls the level macro with [`tb`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L177) and a format prefixed by [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) in hexadecimal. The four wrappers pick one severity each and expand to [`tb_WARN()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L729), [`tb_warn()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L730), [`tb_info()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L731) and [`tb_dbg()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L732), which print through [`dev`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L520) of the [`nhi`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L85) member.

[`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) uses three of the four severities while it decides whether the router that came back is the one that went away.

```c
/* drivers/thunderbolt/switch.c:3550 */
		/* We don't have any way to confirm this was the same device */
		if (!sw->uid)
			return -ENODEV;

		if (tb_switch_is_usb4(sw))
			err = usb4_switch_read_uid(sw, &uid);
		else
			err = tb_drom_read_uid_only(sw, &uid);
		if (err) {
			tb_sw_warn(sw, "uid read failed\n");
			return err;
		}
		if (sw->uid != uid) {
			tb_sw_info(sw,
				"changed while suspended (uid %#llx -> %#llx)\n",
				sw->uid, uid);
			return -ENODEV;
		}
```

[`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) refuses a router whose [`uid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L178) is zero, reads the identifier again over the seam and answers `-ENODEV` when the value differs from the cached one. Its warning and its information line both carry the route of the router they concern, so a reader can attribute them. Two members appear in every router log line, the domain pointer and the cached route.

So far, the object can be addressed, gated and logged against, all from the header copy and the domain pointer. The route string in a log line is the same value the seam puts in the packet.

### The identity members carry a router's name to userspace

A router identifies itself with a unique number and, on newer hardware, a UUID, and its DROM can add vendor and model numbers with printable names. Six members hold those answers, and the DROM parser fills four of them. The three excerpts below are that parser, the older format's own path to the same members, and the sysfs handler shape that publishes them.

[`tb_drom_parse_entry_generic()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L326) fills four of the six from three DROM entry types.

```c
/* drivers/thunderbolt/eeprom.c:326 */
static int tb_drom_parse_entry_generic(struct tb_switch *sw,
		struct tb_drom_entry_header *header)
{
	const struct tb_drom_entry_generic *entry =
		(const struct tb_drom_entry_generic *)header;

	switch (header->index) {
	case 1:
		/* Length includes 2 bytes header so remove it before copy */
		sw->vendor_name = kstrndup(entry->data,
			header->len - sizeof(*header), GFP_KERNEL);
		if (!sw->vendor_name)
			return -ENOMEM;
		break;

	case 2:
		sw->device_name = kstrndup(entry->data,
			header->len - sizeof(*header), GFP_KERNEL);
		if (!sw->device_name)
			return -ENOMEM;
		break;
	case 9: {
		const struct tb_drom_entry_desc *desc =
			(const struct tb_drom_entry_desc *)entry;

		if (!sw->vendor && !sw->device) {
			sw->vendor = desc->idVendor;
			sw->device = desc->idProduct;
		}
		break;
	}
	}

	return 0;
}
```

[`tb_drom_parse_entry_generic()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L326) duplicates entry index 1 into [`vendor_name`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L182) and index 2 into [`device_name`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L183) with [`kstrndup()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/string.h#L300), subtracting the entry header from the declared length. Its index 9 case writes [`vendor`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L180) and [`device`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L181) from the product descriptor, guarded on both being zero so a later descriptor never overrides a value already present. Both strings are freed by the release callback, and the quirk pass matches a router on both numbers.

[`tb_drom_parse_v1()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L592) takes the same numbers out of the older format's header, together with the unique identifier.

```c
/* drivers/thunderbolt/eeprom.c:605 */
	if (!sw->uid)
		sw->uid = header->uid;
	sw->vendor = header->vendor_id;
	sw->device = header->model_id;
```

[`tb_drom_parse_v1()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L592) writes [`uid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L178) only while it is still zero, and writes [`vendor`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L180) and [`device`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L181) unconditionally from the DROM header. Four other sites pass the member by reference to a reader that fills it. Two of them are in the host path, at [eeprom.c:679](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L679) and [eeprom.c:689](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L689), and the others are at [eeprom.c:539](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L539) and [eeprom.c:701](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L701). The sixth site is the UUID step, which reads the identifier over a router operation when it needs one.

[`vendor_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2175) stands for the handlers that read these members back without taking any lock.

```c
/* drivers/thunderbolt/switch.c:2175 */
static ssize_t vendor_show(struct device *dev, struct device_attribute *attr,
			   char *buf)
{
	struct tb_switch *sw = tb_to_switch(dev);

	return sysfs_emit(buf, "%#x\n", sw->vendor);
}
static DEVICE_ATTR_RO(vendor);
```

[`vendor_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2175) converts the device, reads [`vendor`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L180) and emits it, and [`device_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1905), [`device_name_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1914) and [`vendor_name_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2184) have the same three-line shape over their own member. Lock-free reading holds because every write to these six happens inside the add order, ahead of the registration at [switch.c:3369](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3369). The value a sysfs reader finds has therefore already settled.

### The driver builds a missing UUID from the unique identifier

Userspace identifies a router by its UUID, so the driver needs one even where the hardware carries none. The fallback builds sixteen bytes out of the 64-bit identifier the DROM read produced and fills the upper half with ones. The two blocks below show that mapping and the code that performs it.

```
    uid, one 64-bit value            the sixteen bytes kmemdup copies
    ─────────────────────            ────────────────────────────────
                                     ┌───────────────────────────┐
    bits 31:0                  ──▶   │ uuid[0]                   │
    bits 63:32                 ──▶   │ uuid[1]                   │
                                     ├───────────────────────────┤
    the literal 0xffffffff     ──▶   │ uuid[2]                   │
                               ──▶   │ uuid[3]                   │
                                     └───────────────────────────┘

    the two halves of uid land in the low two words in little-endian
    order and a constant fills the high two
```

[`tb_switch_set_uuid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2676) reaches this code when the router supplied no fused UUID of its own.

```c
/* drivers/thunderbolt/switch.c:2703 */
	if (uid) {
		/*
		 * ICM generates UUID based on UID and fills the upper
		 * two words with ones. This is not strictly following
		 * UUID format but we want to be compatible with it so
		 * we do the same here.
		 */
		uuid[0] = sw->uid & 0xffffffff;
		uuid[1] = (sw->uid >> 32) & 0xffffffff;
		uuid[2] = 0xffffffff;
		uuid[3] = 0xffffffff;
	}

	sw->uuid = kmemdup(uuid, sizeof(uuid), GFP_KERNEL);
	if (!sw->uuid)
		return -ENOMEM;
	return 0;
```

[`tb_switch_set_uuid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2676) splits [`uid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L178) into two words and writes ones into the other two, under a comment that attributes the shape to compatibility with the firmware connection manager. [`kmemdup()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/string.h#L302) then places the sixteen bytes on the heap, and a NULL result is the one error the function can return here. The early return at [switch.c:2682](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2682) makes the whole function a no-op once [`uuid`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L179) is set, so the value a router is given first is the value it keeps.

### Generation and link type record what the router speaks

Two members record what protocol generation the router implements and what kind of link reaches it, and they answer different questions from the version predicates. One is a small integer derived from the cached header, and the other is a boolean derived from the adapter below the parent router. The two excerpts below write the second member and then read it in a policy decision.

[`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243) writes the link member from the adapter on the parent's side of the link.

```c
/* drivers/thunderbolt/usb4.c:258 */
	down = tb_switch_downstream_port(sw);
	sw->link_usb4 = link_is_usb4(down);
	tb_sw_dbg(sw, "link: %s\n", sw->link_usb4 ? "USB4" : "TBT");
```

[`usb4_switch_setup()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L243) asks [`link_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L213) about the downstream facing adapter of the parent router, so [`link_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L187) describes the link above the router. A USB4 router reached over a Thunderbolt link therefore holds false there while [`tb_switch_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1322) answers true for it. The same function reads the member back at [usb4.c:272](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L272), where a USB3 tunnel is offered only over a USB4 link.

[`generation`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L188) takes its value from [`tb_switch_get_generation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2380) inside the allocation, which is the one write to it outside the driver's test fixtures. That classifier answers 4 for a USB4 router at [switch.c:2383](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2383) and otherwise picks 1, 2 or 3 from the header's identifier pair. A pair it does not recognize produces a warning at [switch.c:2420](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2420) and the value 1 at [switch.c:2422](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2422), which the comment above the warning gives as the safe assumption.

[`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) reads the link member as the last of three tests before it looks for an adapter to pair with.

```c
/* drivers/thunderbolt/tb.c:913 */
	if (!tb_acpi_may_tunnel_usb3()) {
		tb_dbg(tb, "USB3 tunneling disabled, not creating tunnel\n");
		return 0;
	}

	up = tb_switch_find_port(sw, TB_TYPE_USB3_UP);
	if (!up)
		return 0;

	if (!sw->link_usb4)
		return 0;
```

[`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) returns 0 when [`link_usb4`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L187) is false, so a router reached over a Thunderbolt link gets no USB3 tunnel even where the platform allows one. The register layout of the link controller differs between generations, so [`drivers/thunderbolt/lc.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c) tests [`generation`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L188) in thirteen places, against 2 in some and against 3 in others. The two members therefore answer different questions, one about the router and one about the link above it.

### Cached offsets record where each capability was found

Finding a capability means following a linked list through configuration space, so the driver does it once per capability and keeps the resulting dword offsets. Four members hold them, and each stays at zero when the search found nothing. The two excerpts below re-show the four declarations with the line that opens the structure, and the run of searches that fills them.

[`struct tb_switch`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L171) declares the four as signed integers, and the kerneldoc gives each of them the same absence marker.

```c
/* drivers/thunderbolt/tb.h:171 */
struct tb_switch {
... /* 17 lines, to :189 */
	int cap_plug_events;
	int cap_vsec_tmu;
	int cap_lc;
	int cap_lp;
```

[`cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189), [`cap_vsec_tmu`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L190), [`cap_lc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L191) and [`cap_lp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L192) are signed integers holding a dword offset into the router's configuration space, and zero means the search found nothing. The first locates the plug-events capability the EEPROM control words and the hotplug enable use, and the second the time-management capability. The third locates the link-controller capability and the fourth the low-power capability that carries CL states on pre-USB4 routers.

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) writes all four in one run, each behind the same positive-result guard.

```c
/* drivers/thunderbolt/switch.c:2519 */
	ret = tb_switch_find_vse_cap(sw, TB_VSE_CAP_PLUG_EVENTS);
	if (ret > 0)
		sw->cap_plug_events = ret;

	ret = tb_switch_find_vse_cap(sw, TB_VSE_CAP_TIME2);
	if (ret > 0)
		sw->cap_vsec_tmu = ret;

	ret = tb_switch_find_vse_cap(sw, TB_VSE_CAP_LINK_CONTROLLER);
	if (ret > 0)
		sw->cap_lc = ret;

	ret = tb_switch_find_vse_cap(sw, TB_VSE_CAP_CP_LP);
	if (ret > 0)
		sw->cap_lp = ret;
```

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) stores the answer of [`tb_switch_find_vse_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L234) only while it exceeds zero, so a negative errno and a zero offset both leave the member at the zero the allocation started from. None of the four failures stops the allocation, which is why every reader carries its own absence test. These four assignments are the only writes to the four members in the driver, so a capability the allocation missed stays missing for the life of the object.

So far, the object knows what the router is, where it is in the tree, what it is called and which capabilities it carries. Each of the four offsets was written once, and a zero in one of them is the record that the search failed.

### Each reader handles a zero offset its own way

An offset the search never found is zero, and a reader that added it to a register constant would address the router's own header. Each of the four members therefore leaves the absence to the code that uses it, and only two of them are tested anywhere. The table pairs each member with the file that owns its capability, and the three excerpts after it show an untested add, a second untested add and a refusal.

| member | read in | tested against zero at |
|---|---|---|
| [`cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189) | [`drivers/thunderbolt/eeprom.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c) and [`drivers/thunderbolt/switch.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c) | [eeprom.c:142](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L142) and [switch.c:2645](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2645) |
| [`cap_vsec_tmu`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L190) | [`drivers/thunderbolt/tmu.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c) | no site; its three readers are reached behind a guard of their own |
| [`cap_lc`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L191) | [`drivers/thunderbolt/lc.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c) | [lc.c:22](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L22) and [lc.c:29](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/lc.c#L29) |
| [`cap_lp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L192) | [`drivers/thunderbolt/clx.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c) | no site; its one reader returns early for a router without the capability |

[`tb_switch_tmu_set_time_disruption()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L332) picks its offset from one of two members, and the path it takes for a pre-USB4 router reaches the cached one.

```c
/* drivers/thunderbolt/tmu.c:337 */
	if (tb_switch_is_usb4(sw)) {
		offset = sw->tmu.cap + TMU_RTR_CS_0;
		bit = TMU_RTR_CS_0_TD;
	} else {
		offset = sw->cap_vsec_tmu + TB_TIME_VSEC_3_CS_26;
		bit = TB_TIME_VSEC_3_CS_26_TD;
	}
```

[`tb_switch_tmu_set_time_disruption()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L332) adds [`cap_vsec_tmu`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L190) to a register constant with no test, while the path above it reaches the offset the embedded time-management structure carries. A router that answers true to [`tb_switch_is_usb4()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1322) never reaches the cached member here, and a pre-USB4 router that lacks the capability would address its own header. The two remaining readers of that member, at [tmu.c:711](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L711) and [tmu.c:718](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L718), are reached the same way.

[`tb_switch_mask_clx_objections()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L257) is the one reader of the low-power offset, and it reaches the member twice.

```c
/* drivers/thunderbolt/clx.c:287 */
	ret = tb_sw_read(sw, &val, TB_CFG_SWITCH,
			 sw->cap_lp + offset, ARRAY_SIZE(val));
	if (ret)
		return ret;

	for (i = 0; i < ARRAY_SIZE(val); i++) {
		val[i] |= mask_obj;
		val[i] &= ~unmask_obj;
	}

	return tb_sw_write(sw, &val, TB_CFG_SWITCH,
			   sw->cap_lp + offset, ARRAY_SIZE(val));
```

[`tb_switch_mask_clx_objections()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L257) adds [`cap_lp`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L192) to an offset it holds in a local of its own, once to read two dwords and once to write them back, again with no test. The function returns 0 near its top for any router the driver does not recognize as supporting CL states, so the untested add runs only where the capability exists. Both reaches use the seam, so an unplugged router answers `-ENODEV` before any offset is used.

[`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) is stricter with the plug-events offset, refusing the router outright.

```c
/* drivers/thunderbolt/switch.c:2645 */
		if (!sw->cap_plug_events) {
			tb_sw_warn(sw, "cannot find TB_VSE_CAP_PLUG_EVENTS aborting\n");
			return -ENODEV;
		}
```

[`tb_switch_configure()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2605) answers `-ENODEV` when [`cap_plug_events`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L189) is zero on a router the version predicate rejects, so a failed plug-events search stops that router from being configured at all. The other three members leave their failures to the reader, and a router that reaches the add order can hold a zero in any of them. Each member therefore carries its own absence convention into the file that owns its capability.

### The DROM buffer and the NVM handle hold firmware state

A router's DROM describes its adapters and its identity, and the driver keeps the whole image until the object is released. A router's NVM is a separate device the driver exposes for firmware upgrade, and the object holds a handle to it beside a flag that forbids the upgrade. The fence below holds the two preconditions that read those members, and the two excerpts after it are the allocation and the release of the image buffer.

[`tb_drom_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L723) reads the buffer pointer as a precondition, and [`nvm_upgradeable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L228) reads the veto the same way.

```c
/* drivers/thunderbolt/eeprom.c:723 */
int tb_drom_read(struct tb_switch *sw)
{
	if (sw->drom)
		return 0;

	if (!tb_route(sw))
		return tb_drom_host_read(sw);
	return tb_drom_device_read(sw);
}
/* drivers/thunderbolt/switch.c:228, the veto ahead of the readability test */
static inline bool nvm_upgradeable(struct tb_switch *sw)
{
	if (sw->no_nvm_upgrade)
		return false;
	return nvm_readable(sw);
}
```

[`tb_drom_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L723) returns 0 while [`drom`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L194) is non-NULL, so a second call re-reads nothing and the first image a router gave stands for the life of the object. [`nvm_upgradeable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L228) answers false while [`no_nvm_upgrade`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L196) is set, ahead of the readability test that decides whether the hardware can be reached at all. The two members are therefore read as gates before either mechanism runs.

[`tb_switch_drom_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L447) is the one function that gives [`drom`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L194) a buffer.

```c
/* drivers/thunderbolt/eeprom.c:447 */
static int tb_switch_drom_alloc(struct tb_switch *sw, size_t size)
{
	sw->drom = kzalloc(size, GFP_KERNEL);
	if (!sw->drom)
		return -ENOMEM;

#ifdef CONFIG_DEBUG_FS
	sw->drom_blob.data = sw->drom;
	sw->drom_blob.size = size;
#endif
	return 0;
}
```

[`tb_switch_drom_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L447) allocates a zeroed buffer of the size the DROM reports and points [`drom_blob`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L218) at it under [`CONFIG_DEBUG_FS`](https://elixir.bootlin.com/linux/v7.2/source/lib/Kconfig.debug#L708). The wrapper records the same size, so the two members describe one buffer from the moment it exists. A failed allocation leaves both at their zeroed values and answers `-ENOMEM`.

[`tb_switch_drom_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L460) reverses that pair before it releases the buffer.

```c
/* drivers/thunderbolt/eeprom.c:460 */
static void tb_switch_drom_free(struct tb_switch *sw)
{
#ifdef CONFIG_DEBUG_FS
	sw->drom_blob.data = NULL;
	sw->drom_blob.size = 0;
#endif
	kfree(sw->drom);
	sw->drom = NULL;
}
```

[`tb_switch_drom_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/eeprom.c#L460) clears [`drom_blob`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L218) first and then frees [`drom`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L194) and sets it to NULL, so the wrapper never points at released memory. A parse failure is the path that reaches it, which is why a router can be added with no image at all. The release callback frees the buffer again on the normal path, where the parse succeeded and the image stayed.

```
    the image buffer and its debugfs wrapper, before and after the free
    ──────────────────────────────────────────────────────────────────

    after the allocation                    after the free
    ┌──────────────────────────────┐        ┌──────────────────────────────┐
    │ drom            ──┐          │        │ drom             NULL        │
    │ drom_blob.data  ──┤          │  ──▶   │ drom_blob.data   NULL        │
    │ drom_blob.size  = size       │        │ drom_blob.size   0           │
    └───────────────────┼──────────┘        └──────────────────────────────┘
                        ▼
              ┌────────────────────┐        the wrapper is cleared first, so it
              │ size bytes, zeroed │        never points at memory the free has
              └────────────────────┘        already released
```

The two members therefore describe one buffer while it exists and nothing at all once it is gone.

### The DROM buffer is aliased into a debugfs blob

A router's DROM image is worth reading from userspace while a machine is being brought up, and the driver publishes the same buffer it parses. One wrapper structure carries that buffer's address and its length, and one function reads it. The two excerpts below create the router's debugfs directory and publish the image, and then take the directory down.

[`tb_switch_debugfs_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2418) writes the directory member and reads both the image pointer and the wrapper.

```c
/* drivers/thunderbolt/debugfs.c:2418 */
void tb_switch_debugfs_init(struct tb_switch *sw)
{
	struct dentry *debugfs_dir;
	struct tb_port *port;

	debugfs_dir = debugfs_create_dir(dev_name(&sw->dev), tb_debugfs_root);
	sw->debugfs_dir = debugfs_dir;
	debugfs_create_file("regs", DEBUGFS_MODE, debugfs_dir, sw,
			    &switch_regs_fops);
	if (sw->drom)
		debugfs_create_blob("drom", 0400, debugfs_dir, &sw->drom_blob);

	tb_switch_for_each_port(sw, port) {
		struct dentry *debugfs_dir;
		char dir_name[10];

		if (port->disabled)
			continue;
		if (port->config.type == TB_TYPE_INACTIVE)
			continue;

		snprintf(dir_name, sizeof(dir_name), "port%d", port->port);
		debugfs_dir = debugfs_create_dir(dir_name, sw->debugfs_dir);
		debugfs_create_file("regs", DEBUGFS_MODE, debugfs_dir,
				    port, &port_regs_fops);
		debugfs_create_file("path", 0400, debugfs_dir, port,
				    &path_fops);
		if (port->config.counters_support)
			debugfs_create_file("counters", 0600, debugfs_dir, port,
					    &counters_fops);
		if (port->usb4)
			debugfs_create_file("sb_regs", DEBUGFS_MODE, debugfs_dir,
					    port, &port_sb_regs_fops);
	}

	margining_switch_init(sw);
}
```

[`tb_switch_debugfs_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2418) creates the router's directory under the driver's debugfs root and stores it in [`debugfs_dir`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L202). It publishes the image through [`debugfs_create_blob()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/debugfs.h#L206) only where [`drom`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L194) is non-NULL, which is the one read of [`drom_blob`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L218) in the driver. It then reads the directory member back as the parent of each adapter directory it creates, passing over an adapter the driver has disabled or the router reports inactive.

[`tb_switch_debugfs_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2462) is where the directory member is handed back.

```c
/* drivers/thunderbolt/debugfs.c:2462 */
void tb_switch_debugfs_remove(struct tb_switch *sw)
{
	margining_switch_remove(sw);
	debugfs_remove_recursive(sw->debugfs_dir);
}
```

[`tb_switch_debugfs_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c#L2462) passes [`debugfs_dir`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L202) to [`debugfs_remove_recursive()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/debugfs.h#L161), which takes the whole tree down in one call. Both functions are compiled only under [`CONFIG_DEBUG_FS`](https://elixir.bootlin.com/linux/v7.2/source/lib/Kconfig.debug#L708), and so is the wrapper member itself, which makes it the one member-level configuration dependency in the structure. The image the parser reads and the blob userspace reads are therefore the same bytes.

### The NVM handle is set where the version read succeeds

A router's NVM is registered as a separate device so that firmware can be replaced, and the object keeps a handle to it beside the flag that forbids the replacement. One function writes both, on opposite outcomes of the same attempt. The three excerpts below are that function, the second latch of the same flag, and the clear that runs during removal.

[`tb_switch_nvm_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L328) assigns the handle only after a version read succeeds.

```c
/* drivers/thunderbolt/switch.c:328 */
static int tb_switch_nvm_init(struct tb_switch *sw)
{
	struct tb_nvm *nvm;
	int ret;

	if (!nvm_readable(sw))
		return 0;

	nvm = tb_nvm_alloc(&sw->dev);
	if (IS_ERR(nvm)) {
		ret = PTR_ERR(nvm) == -EOPNOTSUPP ? 0 : PTR_ERR(nvm);
		goto err_nvm;
	}

	ret = tb_nvm_read_version(nvm);
	if (ret)
		goto err_nvm;

	sw->nvm = nvm;
	return 0;

err_nvm:
	tb_sw_dbg(sw, "NVM upgrade disabled\n");
	sw->no_nvm_upgrade = true;
	if (!IS_ERR(nvm))
		tb_nvm_free(nvm);

	return ret;
}
```

[`tb_switch_nvm_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L328) returns before either write when [`nvm_readable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L212) answers false, so a router whose NVM cannot be reached keeps both members at their zeroed values. It assigns [`nvm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L195) after the version read succeeds, and both failure paths latch [`no_nvm_upgrade`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L196) and leave the handle NULL. An unrecognized NVM format arrives as `-EOPNOTSUPP` and is converted to success, so that router is added with the veto set and no NVM device of its own.

[`tb_switch_nvm_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L358) latches the same flag when registering the NVMem devices fails.

```c
/* drivers/thunderbolt/switch.c:386 */
err_nvm:
	tb_sw_dbg(sw, "NVM upgrade disabled\n");
	sw->no_nvm_upgrade = true;
	tb_nvm_free(nvm);

	return ret;
```

[`tb_switch_nvm_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L358) sets [`no_nvm_upgrade`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L196) on its own error label and frees the object the earlier step allocated. [`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) makes the third write, forcing the veto on a host router that is not a USB4 one, which the next subsection reaches. Nothing clears the flag once any of the three has set it.

[`tb_switch_nvm_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L394) clears the handle before it can be used again.

```c
/* drivers/thunderbolt/switch.c:394 */
static void tb_switch_nvm_remove(struct tb_switch *sw)
{
	struct tb_nvm *nvm;

	nvm = sw->nvm;
	sw->nvm = NULL;

	if (!nvm)
		return;
```

[`tb_switch_nvm_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L394) copies the handle into a local and sets [`nvm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L195) to NULL before it tests the local, so a caller that reads the member after this point finds nothing. [`nvm_version_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2153) is the reader that has to cope with that, and it holds the domain lock while it decides, which sets it apart from the other read-only attributes of a router.

So far, the object carries the router's identity, its capability offsets, its DROM image and its NVM handle, with two vetoes recorded beside them. The handle exists only where a version read succeeded, and the image exists only where a parse succeeded.

### Policy flags decide power and approval

Whether a router may be used and whether it may suspend are decisions of the driver and of userspace, and three flags record them. Their writers are the domain code, the sysfs store handlers and the boot-time discovery pass. The three excerpts below set the first flag on a discovered tunnel's path, two of them on the host router, and one on a device router.

[`tb_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1694) climbs the parent chain of a discovered PCIe tunnel and marks every router it passes.

```c
/* drivers/thunderbolt/tb.c:1701 */
	list_for_each_entry(tunnel, &tcm->tunnel_list, list) {
		if (tb_tunnel_is_pci(tunnel)) {
			struct tb_switch *parent = tunnel->dst_port->sw;

			while (parent != tunnel->src_port->sw) {
				parent->boot = true;
				parent = tb_switch_parent(parent);
			}
```

[`tb_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1694) starts at the router a discovered PCIe tunnel ends on and climbs with [`tb_switch_parent()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L902), setting [`boot`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L198) on every router until it reaches the one the tunnel starts at. The loop stops before that router, so the flag marks every router the tunnel passes through. [`boot_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1896) prints the flag for userspace, and the scan's finalizer copies it into [`authorized`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L200) before the add event leaves the kernel.

```
    which routers a discovered PCIe tunnel marks as booted
    ─────────────────────────────────────────────────────

    depth 0   ┌──────────────────────────────┐
              │ host router                  │  the tunnel starts here and
              └──────────────┬───────────────┘  the climb stops before it
                             │ dev.parent
              ┌──────────────┴───────────────┐
    depth 1   │ device router   boot ← true  │
              └──────────────┬───────────────┘
                             │ dev.parent
              ┌──────────────┴───────────────┐
    depth 2   │ device router   boot ← true  │  the tunnel ends here
              └──────────────────────────────┘

    the climb starts at the router the tunnel ends on and moves up to the one
    it starts at, so every router between them carries the flag
```

Each router between the two ends of the tunnel therefore carries the flag. The router the tunnel starts at keeps the value it already had, because the climb stops there.

[`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) settles two flags on the host router from one predicate each, before it configures it.

```c
/* drivers/thunderbolt/tb.c:3014 */
	tb->root_switch->no_nvm_upgrade = !tb_switch_is_usb4(tb->root_switch);
	/* All USB4 routers support runtime PM */
	tb->root_switch->rpm = tb_switch_is_usb4(tb->root_switch);
```

[`tb_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2995) forbids the NVM upgrade of a host router that is not a USB4 router and gives runtime power management to one that is. The comment above the second line carries the reason the tree records, that every USB4 router supports it. Both writes reach the object through [`root_switch`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L88) of the domain, because the host router has no parent to be scanned from.

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) applies a different rule to a device router, one statement before it adds the router.

```c
/* drivers/thunderbolt/tb.c:1369 */
	/*
	 * At the moment Thunderbolt 2 and beyond (devices with LC) we
	 * can support runtime PM.
	 */
	sw->rpm = sw->generation > 1;
```

[`tb_scan_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1289) sets [`rpm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L199) when [`generation`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L188) exceeds 1, which the comment above it attributes to the link controller those routers carry. The flag is therefore settled before the add order runs, and the add order reads it there. Three flags are written this way, each by the path that can first decide it.

### Autosuspend is armed only for a router that supports it

Runtime power management is armed once, during the add order, and only for a router whose flag says it can take it. Two places outside the firmware manager's file read that flag, one arming autosuspend and one undoing it. The excerpt below is the arming, and the excerpt after it is the read on the removal path.

[`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) marks every router active and then enables autosuspend only where the flag is set.

```c
/* drivers/thunderbolt/switch.c:3402 */
	pm_runtime_set_active(&sw->dev);
	if (sw->rpm) {
		pm_runtime_set_autosuspend_delay(&sw->dev, TB_AUTOSUSPEND_DELAY);
		pm_runtime_use_autosuspend(&sw->dev);
		pm_runtime_mark_last_busy(&sw->dev);
		pm_runtime_enable(&sw->dev);
		pm_request_autosuspend(&sw->dev);
	}
```

[`tb_switch_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3298) calls [`pm_runtime_set_active()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L752) for every router, then enters the block only when [`rpm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L199) is set. Inside it [`TB_AUTOSUSPEND_DELAY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L550) gives the delay as 15000 milliseconds, autosuspend is enabled and a request is queued at once. A router without the flag is left active with runtime power management disabled.

[`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) reads the same flag to undo what the add order armed.

```c
/* drivers/thunderbolt/switch.c:3434 */
	tb_switch_debugfs_remove(sw);

	if (sw->rpm) {
		pm_runtime_get_sync(&sw->dev);
		pm_runtime_disable(&sw->dev);
	}
```

[`tb_switch_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3430) resumes the device and disables runtime power management for a flagged router before it touches anything else. Those two reads in [`drivers/thunderbolt/switch.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c) are all the driver makes of the member outside the firmware manager's file. The flag therefore decides one thing, whether the router participates in runtime power management at all.

### Approval moves between three values under the domain lock

Approval is the policy member userspace can change, and every change to it happens under the domain lock. The allocation authorizes the host router by construction, the scan's finalizer authorizes a router the boot firmware had already tunneled through, and the store handler applies what userspace wrote. The three excerpts below are the first write, the handler's own write, and the recursive clear.

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) authorizes the host router as it builds it.

```c
/* drivers/thunderbolt/switch.c:2535 */
	/* Root switch is always authorized */
	if (!route)
		sw->authorized = true;
```

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) sets [`authorized`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L200) for a router reached by route 0 and leaves every other router at zero, under a comment naming the rule. No lock is taken there, because the object is not on the bus and no other path can see it. The comment states the rule as the code applies it, that the root switch is always authorized.

[`tb_switch_set_authorized()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1819) takes the domain lock around the whole decision and writes the member only after the domain operation succeeds.

```c
/* drivers/thunderbolt/switch.c:1825 */
	if (!mutex_trylock(&sw->tb->lock))
		return restart_syscall();

	if (!!sw->authorized == !!val)
		goto unlock;

/* drivers/thunderbolt/switch.c:1857, the write and the uevent */

	if (!ret) {
		sw->authorized = val;
		/*
		 * Notify status change to the userspace, informing the new
		 * value of /sys/bus/thunderbolt/devices/.../authorized.
		 */
		sprintf(envp_string, "AUTHORIZED=%u", sw->authorized);
		kobject_uevent_env(&sw->dev.kobj, KOBJ_CHANGE, envp);
	}
```

[`tb_switch_set_authorized()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1819) answers [`restart_syscall()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/sched/signal.h#L376) when [`mutex_trylock()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/mutex.h#L243) fails, which is how all seven userspace entries in this file treat a busy domain. It leaves the member alone when the requested value matches the current one as a boolean, so a challenge request over an existing approval is refused too. It writes [`authorized`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L200) only on a zero return from the domain operation and publishes the new value as a uevent variable.

[`disapprove_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1794) is the fourth writer, and it clears the member down a whole subtree.

```c
/* drivers/thunderbolt/switch.c:1799 */
	sw = tb_to_switch(dev);
	if (sw && sw->authorized) {
		int ret;

		/* First children */
		ret = device_for_each_child_reverse(&sw->dev, NULL, disapprove_switch);
		if (ret)
			return ret;

		ret = tb_domain_disapprove_switch(sw->tb, sw);
		if (ret)
			return ret;

		sw->authorized = 0;
		kobject_uevent_env(&sw->dev.kobj, KOBJ_CHANGE, envp);
	}
```

[`disapprove_switch()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1794) recovers the object, acts only on a router that is currently authorized and recurses into the children before it touches this router. It writes zero into [`authorized`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L200) after the domain has disconnected the tunnel, and publishes the same uevent variable. Approval is therefore a value between 0 and 2 that four paths write and the domain lock serializes.

### The challenge key changes only while approval is off

A security policy can require a router to prove that it holds a shared secret, and the object carries that secret. The driver refuses to change it once the router is approved, so the secret a challenge is about to use stays put. The two excerpts below are the store handler and the reader that puts the secret to work.

[`key_store()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1950) takes the domain lock and reads the approval member before it touches the buffer.

```c
/* drivers/thunderbolt/switch.c:1950 */
static ssize_t key_store(struct device *dev, struct device_attribute *attr,
			 const char *buf, size_t count)
{
	struct tb_switch *sw = tb_to_switch(dev);
	u8 key[TB_SWITCH_KEY_SIZE];
	ssize_t ret = count;
	bool clear = false;

	if (!strcmp(buf, "\n"))
		clear = true;
	else if (hex2bin(key, buf, sizeof(key)))
		return -EINVAL;

	if (!mutex_trylock(&sw->tb->lock))
		return restart_syscall();

	if (sw->authorized) {
		ret = -EBUSY;
	} else {
		kfree(sw->key);
		if (clear) {
			sw->key = NULL;
		} else {
			sw->key = kmemdup(key, sizeof(key), GFP_KERNEL);
			if (!sw->key)
				ret = -ENOMEM;
		}
	}

	mutex_unlock(&sw->tb->lock);
	return ret;
}
static DEVICE_ATTR(key, 0600, key_show, key_store);
```

[`key_store()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1950) answers `-EBUSY` while [`authorized`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L200) is non-zero, so the secret of an approved router cannot be replaced under it. Otherwise it frees the old buffer and either clears [`key`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L203) or duplicates the thirty-two bytes [`TB_SWITCH_KEY_SIZE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L74) names. The declaration at the end gives the pair mode 0600, so the secret never reaches an unprivileged reader, and [`key_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1932) prints it under the same lock.

[`tb_domain_challenge_switch_key()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L715) is the reader that puts the secret to work, on the approval path the previous subsection followed.

```c
/* drivers/thunderbolt/domain.c:715 */
int tb_domain_challenge_switch_key(struct tb *tb, struct tb_switch *sw)
{
	u8 challenge[TB_SWITCH_KEY_SIZE];
	u8 response[TB_SWITCH_KEY_SIZE];
	u8 hmac[TB_SWITCH_KEY_SIZE];
	struct tb_switch *parent_sw;
	int ret;

	if (!tb->cm_ops->approve_switch || !tb->cm_ops->challenge_switch_key)
		return -EPERM;

	/* The parent switch must be authorized before this one */
	parent_sw = tb_to_switch(sw->dev.parent);
	if (!parent_sw || !parent_sw->authorized)
		return -EINVAL;

	get_random_bytes(challenge, sizeof(challenge));
	ret = tb->cm_ops->challenge_switch_key(tb, sw, challenge, response);
	if (ret)
		return ret;

	static_assert(sizeof(hmac) == SHA256_DIGEST_SIZE);
	hmac_sha256_usingrawkey(sw->key, TB_SWITCH_KEY_SIZE,
				challenge, sizeof(challenge), hmac);

	/* The returned HMAC must match the one we calculated */
	if (crypto_memneq(response, hmac, sizeof(hmac)))
		return -EKEYREJECTED;

	return tb->cm_ops->approve_switch(tb, sw);
}
```

[`tb_domain_challenge_switch_key()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L715) requires the parent router to be authorized already, then sends the router a random challenge. It passes [`key`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L203) to [`hmac_sha256_usingrawkey()`](https://elixir.bootlin.com/linux/v7.2/source/include/crypto/sha2.h#L525) to compute the answer the router owes. A response that differs answers `-EKEYREJECTED`, and the refusal in the store handler keeps the buffer stable across that exchange.

So far, the object carries the policy userspace and the domain apply to it, from the power flag to the approval value and the secret behind it. The secret can be written only while approval is off, and the store handler enforces that.

### The quirk word records what the quirk table matched

Some routers need behavior the driver would otherwise apply uniformly to be suppressed or forced, and one bit word per router records those decisions. The pass that fills it runs once inside the add order and can set three different bits. The three excerpts below are the matching pass, a hook that sets a bit, and a hook that edits a different member instead.

[`tb_check_quirks()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L125) decides which hooks a router gets from four members the object already holds.

```c
/* drivers/thunderbolt/quirks.c:125 */
void tb_check_quirks(struct tb_switch *sw)
{
	int i;

	for (i = 0; i < ARRAY_SIZE(tb_quirks); i++) {
		const struct tb_quirk *q = &tb_quirks[i];

		if (q->hw_vendor_id && q->hw_vendor_id != sw->config.vendor_id)
			continue;
		if (q->hw_device_id && q->hw_device_id != sw->config.device_id)
			continue;
		if (q->vendor && q->vendor != sw->vendor)
			continue;
		if (q->device && q->device != sw->device)
			continue;

		tb_sw_dbg(sw, "running %ps\n", q->hook);
		q->hook(sw);
	}
}
```

[`tb_check_quirks()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L125) tests each table row against the header pair [`vendor_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L168) and [`device_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_regs.h#L169) and the DROM pair [`vendor`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L180) and [`device`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L181). It skips a row on the first key that is set in the row and differs on the router, and runs the row's hook when none of the four rejects it. A key the row leaves at zero matches every router, and because the loop runs to the end of the table one router can collect more than one hook.

[`quirk_force_power_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L10) is a single bitwise OR and a debug line, which is all a quirk needs to record itself.

```c
/* drivers/thunderbolt/quirks.c:10 */
static void quirk_force_power_link(struct tb_switch *sw)
{
	sw->quirks |= QUIRK_FORCE_POWER_LINK_CONTROLLER;
	tb_sw_dbg(sw, "forcing power to link controller\n");
}
```

[`quirk_force_power_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L10) sets [`QUIRK_FORCE_POWER_LINK_CONTROLLER`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L24) in [`quirks`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L209) and logs the fact through [`tb_sw_dbg()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L743), so the route string in the line says which router got it. [`quirk_block_rpm_in_redrive()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L49) has the same shape for [`QUIRK_KEEP_POWER_IN_DP_REDRIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L28), and a third hook sets [`QUIRK_NO_CLX`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L26) at [quirks.c:29](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L29) unless it returns first. Those three bits are the whole of what the word can hold, at positions 0, 1 and 2.

[`quirk_dp_credit_allocation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L16) is the hook that sets no bit at all and edits a credit member instead.

```c
/* drivers/thunderbolt/quirks.c:16 */
static void quirk_dp_credit_allocation(struct tb_switch *sw)
{
	if (sw->credit_allocation && sw->min_dp_main_credits == 56) {
		sw->min_dp_main_credits = 18;
		tb_sw_dbg(sw, "quirked DP main: %u\n", sw->min_dp_main_credits);
	}
}
```

[`quirk_dp_credit_allocation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/quirks.c#L16) rewrites [`min_dp_main_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L213) from 56 to 18, guarded on the validity flag and on the current value, so it edits nothing on a router whose report it does not recognize. A fifth hook writes a bandwidth ceiling onto each USB3 downstream adapter and leaves the word alone as well. Nothing clears the word once the pass has run, so a bit set during the add order holds for the life of the object.

### Each quirk bit is read on the path it governs

A quirk bit changes behavior in the part of the driver that behavior belongs to, so the three bits are read in three different files. Each reader tests one bit and takes one decision from it. The two blocks below pair each bit with the site that reads it and show the reader that decides an attribute's visibility.

| bit | tested by | at |
|---|---|---|
| [`QUIRK_NO_CLX`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L26) | [`tb_switch_clx_is_supported()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L184) | [clx.c:189](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L189) |
| [`QUIRK_FORCE_POWER_LINK_CONTROLLER`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L24) | [`switch_attr_is_visible()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2222) | [switch.c:2270](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2270) |
| [`QUIRK_KEEP_POWER_IN_DP_REDRIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L28) | [`tb_enter_redrive()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2104) | [tb.c:2108](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2108) |
| [`QUIRK_KEEP_POWER_IN_DP_REDRIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L28) | [`tb_exit_redrive()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2129) | [tb.c:2133](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2133) |
| [`QUIRK_KEEP_POWER_IN_DP_REDRIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L28) | [`tb_switch_exit_redrive()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2159) | [tb.c:2163](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2163) |

[`switch_attr_is_visible()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2222) reads its bit as the last test before the group's default answer.

```c
/* drivers/thunderbolt/switch.c:2269 */
	} else if (attr == &dev_attr_nvm_authenticate_on_disconnect.attr) {
		if (sw->quirks & QUIRK_FORCE_POWER_LINK_CONTROLLER)
			return attr->mode;
		return 0;
	}
```

[`switch_attr_is_visible()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2222) returns the attribute's own mode when the bit is set and 0 when it is clear, so the `nvm_authenticate_on_disconnect` file exists only on a router the quirk pass matched. The three redrive readers return without acting while their bit is clear, and each applies a further test of its own before it takes or drops a runtime-PM reference. The comment at [tb.c:2111](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2111) gives the reason the tree records for that behavior.

So far, the object carries a quirk word whose three bits were settled during the add order and are read in three different files. Each bit governs one decision, and the code that owns that decision is the code that tests it.

### The credit members cache the router's preferred buffer allocation

A USB4 router can report how many buffers it prefers each class of tunnel to get, and the driver keeps those numbers when they validate. Six members hold the answer, one saying the other five are usable and five carrying the counts. The three excerpts below are the validation of the router as a whole, the validation of one adapter at a time, and the run of writes both of them guard.

[`usb4_switch_credits_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L758) begins its validation with two tests on the router as a whole.

```c
/* drivers/thunderbolt/usb4.c:827 */
	/* Host router must report baMaxHI */
	if (!tb_route(sw) && max_dma < 0) {
		tb_sw_warn(sw, "host router is missing baMaxHI\n");
		goto err_invalid;
	}

	nports = 0;
	tb_switch_for_each_port(sw, port) {
		if (tb_port_is_null(port))
			nports++;
	}

	/* Must have DP buffer allocation (multiple USB4 ports) */
	if (nports > 2 && (min_dp_aux < 0 || min_dp_main < 0)) {
		tb_sw_warn(sw, "multiple USB4 ports require baMinDPaux/baMinDPmain\n");
		goto err_invalid;
	}
```

[`usb4_switch_credits_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L758) requires a host router to report the DMA figure and jumps to its error label when that figure is missing. It counts the lane adapters, and a router with more than two of them must report both DisplayPort figures. Each failure warns with the specification's own parameter name and leaves every member untouched.

The second pass applies the same rule to one adapter at a time.

```c
/* drivers/thunderbolt/usb4.c:845 */
	tb_switch_for_each_port(sw, port) {
		if (tb_port_is_dpout(port) && min_dp_main < 0) {
			tb_sw_warn(sw, "missing baMinDPmain");
			goto err_invalid;
		}
		if ((tb_port_is_dpin(port) || tb_port_is_dpout(port)) &&
		    min_dp_aux < 0) {
			tb_sw_warn(sw, "missing baMinDPaux");
			goto err_invalid;
		}
		if ((tb_port_is_usb3_down(port) || tb_port_is_usb3_up(port)) &&
		    max_usb3 < 0) {
			tb_sw_warn(sw, "missing baMaxUSB3");
			goto err_invalid;
		}
		if ((tb_port_is_pcie_down(port) || tb_port_is_pcie_up(port)) &&
		    max_pcie < 0) {
			tb_sw_warn(sw, "missing baMaxPCIe");
			goto err_invalid;
		}
	}
```

[`usb4_switch_credits_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L758) runs that loop over every adapter and jumps to the same label on the first DisplayPort, USB3 or PCIe adapter whose figure came back negative. A router that passes therefore owns every count its own adapters use. The loop reads the adapter type through the port predicates and leaves the object's members as they are.

The writes come after both passes, and every count write is guarded on the value exceeding zero.

```c
/* drivers/thunderbolt/usb4.c:871 */
	sw->credit_allocation = true;
	if (max_usb3 > 0)
		sw->max_usb3_credits = max_usb3;
	if (min_dp_aux > 0)
		sw->min_dp_aux_credits = min_dp_aux;
	if (min_dp_main > 0)
		sw->min_dp_main_credits = min_dp_main;
	if (max_pcie > 0)
		sw->max_pcie_credits = max_pcie;
	if (max_dma > 0)
		sw->max_dma_credits = max_dma;

	return 0;
```

[`usb4_switch_credits_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L758) sets [`credit_allocation`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L210) first and then copies each count the router reported, leaving a count the router omitted at the zero the allocation gave it. A parameter the router reported as zero passes the validation and leaves its member at zero as well, so the flag can stand beside a count of zero. The quirk pass runs later in the add order and can still rewrite one of the five.

### The tunnel code reads the counts through one predicate

A tunnel sizes its paths from the router's own numbers only where those numbers are valid, so the choice is taken once in a predicate every caller shares. The excerpt below is that predicate, the table after it gives its six call sites, and the last excerpt is the helper that reads all five counts at once.

[`tb_port_use_credit_allocation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1128) requires a lane adapter as well as the flag.

```c
/* drivers/thunderbolt/tb.h:1128 */
static inline bool tb_port_use_credit_allocation(const struct tb_port *port)
{
	return tb_port_is_null(port) && port->sw->credit_allocation;
}
```

[`tb_port_use_credit_allocation()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1128) answers true only for a lane adapter of a router whose counts are valid, so one call decides between the reported numbers and the driver's own constants. Six places make that decision, all of them in [`drivers/thunderbolt/tunnel.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c), and the table names the count each of them reaches for.

| caller | count it reaches for | at |
|---|---|---|
| [`tb_pci_init_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L391) | [`max_pcie_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L214) | [tunnel.c:397](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L397) |
| [`tb_dp_init_aux_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1454) | [`min_dp_aux_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L212) | [tunnel.c:1459](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1459) |
| [`tb_dp_init_video_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1483) | [`min_dp_main_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L213) | [tunnel.c:1488](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1488) |
| [`tb_dma_reserve_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1767) | the remainder [`tb_dma_available_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1754) computes | [tunnel.c:1771](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1771) |
| [`tb_dma_release_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1858) | none, it returns the reservation | [tunnel.c:1862](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1862) |
| [`tb_usb3_init_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2160) | [`max_usb3_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L211) | [tunnel.c:2166](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2166) |

[`tb_available_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L127) is the helper the two DMA rows reach through, and it reads all five counts.

```c
/* drivers/thunderbolt/tunnel.c:127 */
static unsigned int tb_available_credits(const struct tb_port *port,
					 size_t *max_dp_streams)
{
	const struct tb_switch *sw = port->sw;
	int credits, usb3, pcie, spare;
	size_t ndp;

	usb3 = tb_acpi_may_tunnel_usb3() ? sw->max_usb3_credits : 0;
	pcie = tb_acpi_may_tunnel_pcie() ? sw->max_pcie_credits : 0;

	if (tb_acpi_is_xdomain_allowed()) {
		spare = min_not_zero(sw->max_dma_credits, dma_credits);
		/* Add some credits for potential second DMA tunnel */
		spare += TB_MIN_DMA_CREDITS;
	} else {
		spare = 0;
	}

	credits = tb_usable_credits(port);
	if (tb_acpi_may_tunnel_dp()) {
		/*
		 * Maximum number of DP streams possible through the
		 * lane adapter.
		 */
		if (sw->min_dp_aux_credits + sw->min_dp_main_credits)
			ndp = (credits - (usb3 + pcie + spare)) /
			      (sw->min_dp_aux_credits + sw->min_dp_main_credits);
		else
			ndp = 0;
	} else {
		ndp = 0;
	}
	credits -= ndp * (sw->min_dp_aux_credits + sw->min_dp_main_credits);
	credits -= usb3;

	if (max_dp_streams)
		*max_dp_streams = ndp;

	return credits > 0 ? credits : 0;
}
```

[`tb_available_credits()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L127) reserves [`max_usb3_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L211) and [`max_pcie_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L214) only where the platform permits that class of tunnel, so a firmware setting that forbids PCIe tunneling releases those buffers to the rest. [`min_not_zero()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/minmax.h#L176) lets the module parameter and [`max_dma_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L215) each stand in for the other when one of them is zero. It then prices each DisplayPort stream at the sum of [`min_dp_aux_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L212) and [`min_dp_main_credits`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L213) and subtracts that sum once per stream the lane adapter can carry.

So far, the object carries a validated buffer allocation beside its quirk word, and one predicate decides whether a tunnel uses it. The five counts are read only through that predicate or through the helper it reaches.

### The link members hold one speed and two widths

The speed and width of the link above a router change as lanes are bonded, unbonded or made asymmetric, so the object caches them. Three members carry the result, two of them typed as a width enumeration and one as a plain speed in gigabits per second. The three blocks below give the relation between the two widths, the handler userspace reads the speed through, and the one policy read of the preferred width.

```
    the (link_width, preferred_link_width) pair of one Gen 4 router
    ───────────────────────────────────────────────────────────────

                                  ❷ link init
                                     │
                                     ▼
              ┌───────────────────────┐   ❶ a width change     ┌───────────────────────┐
              │        settled        │ ─────────────────────▶ │       diverged        │
              │  width == preferred   │                        │  width != preferred   │──┐
              │                       │ ◀───────────────────── │                       │◀─┘
              └───────────────────────┘   ❶ a change back      └───────────────────────┘
                                                                 ❶ a change, still apart

    a host router leaves both at zero, and a link below Gen 4 leaves the
    preferred width at zero, so the pair reads as settled on both

    ❶ tb_switch_update_link_attributes  switch.c:2886  link_width ← what the upstream adapter reports
    ❷ tb_switch_link_init               switch.c:2935  preferred_link_width ← link_width, Gen 4 only
```

Mark ❶ is [`tb_switch_update_link_attributes()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2863), which rewrites [`link_width`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L185) from the upstream adapter every time the driver examines the link. Mark ❷ is [`tb_switch_link_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2896), which copies that width into [`preferred_link_width`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L186) once, and only on a Gen 4 link.

[`speed_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1984) is the whole of what userspace sees of the first of the three members.

```c
/* drivers/thunderbolt/switch.c:1984 */
static ssize_t speed_show(struct device *dev, struct device_attribute *attr,
			  char *buf)
{
	struct tb_switch *sw = tb_to_switch(dev);

	return sysfs_emit(buf, "%u.0 Gb/s\n", sw->link_speed);
}
```

[`speed_show()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1984) prints [`link_speed`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L184) with a fixed fraction and the unit, and both the `rx_speed` and the `tx_speed` attribute are declared with that one handler. [`link_width`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L185) and [`preferred_link_width`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L186) are both [`enum tb_link_width`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L191), whose four values are separate bits from [`TB_LINK_WIDTH_SINGLE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L192) at bit 0 to [`TB_LINK_WIDTH_ASYM_RX`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L195) at bit 3. A comparison against [`TB_LINK_WIDTH_DUAL`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L193) therefore orders single below dual below the two asymmetric widths.

[`tb_configure_sym()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1147) is the one reader of the preferred width outside the debug line beside its write.

```c
/* drivers/thunderbolt/tb.c:1194 */
		if (up->sw->link_width == TB_LINK_WIDTH_DUAL)
			continue;

		/*
		 * Here consumed < threshold so we can transition the
		 * link to symmetric.
		 *
		 * However, if the router prefers asymmetric link we
		 * honor that (unless @keep_asym is %false).
		 */
		if (keep_asym &&
		    up->sw->preferred_link_width > TB_LINK_WIDTH_DUAL) {
			tb_sw_dbg(up->sw, "keeping preferred asymmetric link\n");
			continue;
		}
```

[`tb_configure_sym()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1147) passes over a link already at [`TB_LINK_WIDTH_DUAL`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L193) and then reads [`preferred_link_width`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L186) before it narrows one that is wider. It leaves an asymmetric link asymmetric when the router asked for that width and the caller allows it, which the comment above the test states as honoring the router's preference. The pair therefore records both the width the link has and the width the router asked for.

### Link attributes are refreshed whenever the link is examined

A cached figure is only as good as the moment it was read, so the driver rewrites the two hardware-backed members from the upstream adapter every time it touches the link. One function does that reading and reports a change to userspace. The two excerpts below are that function and the step that derives the preferred width from what it just read.

[`tb_switch_update_link_attributes()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2863) writes the speed and the width from the adapter above the router.

```c
/* drivers/thunderbolt/switch.c:2863 */
static int tb_switch_update_link_attributes(struct tb_switch *sw)
{
	struct tb_port *up;
	bool change = false;
	int ret;

	if (!tb_route(sw) || tb_switch_is_icm(sw))
		return 0;

	up = tb_upstream_port(sw);

	ret = tb_port_get_link_speed(up);
	if (ret < 0)
		return ret;
	if (sw->link_speed != ret)
		change = true;
	sw->link_speed = ret;

	ret = tb_port_get_link_width(up);
	if (ret < 0)
		return ret;
	if (sw->link_width != ret)
		change = true;
	sw->link_width = ret;

	/* Notify userspace that there is possible link attribute change */
	if (device_is_registered(&sw->dev) && change)
		kobject_uevent(&sw->dev.kobj, KOBJ_CHANGE);

	return 0;
}
```

[`tb_switch_update_link_attributes()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2863) returns 0 without touching a member when [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) answers 0 or the router belongs to the firmware manager, which is why a host router keeps the zeroes the allocation left. It reads both values through [`tb_port_get_link_speed()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L905) and [`tb_port_get_link_width()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L966), records whether either differs from the cached value, and writes both. A difference produces a change uevent, which the guard one line above restricts to a device the driver core has already registered.

[`tb_switch_link_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2896) runs straight after it and derives the third member from the second.

```c
/* drivers/thunderbolt/switch.c:2926 */
	if (tb_port_get_link_generation(up) < 4)
		return;

	/*
	 * Set the Gen 4 preferred link width. This is what the router
	 * prefers when the link is brought up. If the router does not
	 * support asymmetric link configuration, this also will be set
	 * to TB_LINK_WIDTH_DUAL.
	 */
	sw->preferred_link_width = sw->link_width;
	tb_sw_dbg(sw, "preferred link width %s\n",
		  tb_width_name(sw->preferred_link_width));
```

[`tb_switch_link_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2896) returns for a link below generation 4 and otherwise copies [`link_width`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L185) into [`preferred_link_width`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L186), under a comment giving that width as what the router prefers when the link comes up. The refresh runs from two places in [`drivers/thunderbolt/switch.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c), the add order at [switch.c:3350](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3350) and the width setter at [switch.c:3180](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3180). The cache therefore follows the hardware across bonding and asymmetry changes.

So far, the object carries the credit counts the router reported and the speed and width of the link above it. Both widths are refreshed from the adapter, and the preferred one is written once for a Gen 4 link.

### The CL word records which low-power states the link holds

The CL states of a link are low-power conditions the two adapters at its ends agree on, and the object caches which of them the upstream link currently has. One bit word carries that, filled during the add order from the hardware itself. The two excerpts below are the function that fills it and the per-adapter read it calls twice.

[`tb_switch_clx_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L211) asks both ends of the link and keeps the upstream answer.

```c
/* drivers/thunderbolt/clx.c:211 */
int tb_switch_clx_init(struct tb_switch *sw)
{
	struct tb_port *up, *down;
	unsigned int clx, tmp;

	if (tb_switch_is_icm(sw))
		return 0;

	if (!tb_route(sw))
		return 0;

	if (!tb_switch_clx_is_supported(sw))
		return 0;

	up = tb_upstream_port(sw);
	down = tb_switch_downstream_port(sw);

	clx = tb_port_clx(up);
	tmp = tb_port_clx(down);
	if (clx != tmp)
		tb_sw_warn(sw, "CLx: inconsistent configuration %#x != %#x\n",
			   clx, tmp);

	tb_sw_dbg(sw, "CLx: current mode: %s\n", clx_name(clx));

	sw->clx = clx;
	return 0;
}
```

[`tb_switch_clx_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L211) returns without acting for a router the firmware manager owns, for a host router and for a router the driver does not recognize as supporting CL states. Otherwise it reads the router's upstream adapter and the parent's downstream adapter with [`tb_port_clx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L142), warns when the two disagree, and stores the upstream answer in [`clx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L216). The word therefore starts out describing what the link already does, because the driver can take over a link whose CL states are on.

[`tb_port_clx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L142) opens with a support test and a register read before it builds that answer.

```c
/* drivers/thunderbolt/clx.c:142 */
static int tb_port_clx(struct tb_port *port)
{
	u32 val;
	int ret;

	if (!tb_port_clx_supported(port, TB_CL0S | TB_CL1 | TB_CL2))
		return 0;

	ret = tb_port_read(port, &val, TB_CFG_PORT,
			   port->cap_phy + LANE_ADP_CS_1, 1);
	if (ret)
		return ret;

	if (val & LANE_ADP_CS_1_CL0S_ENABLE)
		ret |= TB_CL0S;
	if (val & LANE_ADP_CS_1_CL1_ENABLE)
		ret |= TB_CL1;
	if (val & LANE_ADP_CS_1_CL2_ENABLE)
		ret |= TB_CL2;

	return ret;
}
```

[`tb_port_clx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L142) answers 0 for a lane adapter that supports no CL state, so an unsupported adapter reads the same as one with every state off. For an adapter that does support them it reads one dword of the lane register and ORs one CL bit into its answer for each enable bit it finds. The word the object keeps is therefore the union of the states the upstream adapter reported.

### The CL helpers write and test the word

Two functions rewrite the cached word, each only after the hardware has accepted the change, and one inline predicate tests it. The three excerpts below are the write inside the enable path, the read and the clear inside the disable path, and the predicate every other file uses.

[`tb_switch_clx_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L321) touches the word only after both adapters have taken the state.

```c
/* drivers/thunderbolt/clx.c:376 */
	ret = tb_switch_mask_clx_objections(sw);
	if (ret) {
		tb_port_clx_disable(up, clx);
		tb_port_clx_disable(down, clx);
		return ret;
	}

	sw->clx |= clx;

	tb_sw_dbg(sw, "CLx: %s enabled\n", clx_name(clx));
	return 0;
```

[`tb_switch_clx_enable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L321) masks the objections of the router before it records anything, and undoes both adapter programs when that step fails. It ORs the accepted states into [`clx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L216) only once the masking has succeeded, so the word never claims a state the hardware refused. The debug line beside the write names the states by the same helper the initialization used.

[`tb_switch_clx_disable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L398) reads the word as its subject and clears it outright.

```c
/* drivers/thunderbolt/clx.c:398 */
int tb_switch_clx_disable(struct tb_switch *sw)
{
	unsigned int clx = sw->clx;
	struct tb_port *up, *down;
	int ret;

	if (!tb_switch_clx_is_supported(sw))
		return 0;

	if (!clx)
		return 0;

	if (sw->is_unplugged)
		return clx;
/* drivers/thunderbolt/clx.c:416, the two adapter disables and the clear */
	ret = tb_port_clx_disable(up, clx);
	if (ret)
		return ret;

	ret = tb_port_clx_disable(down, clx);
	if (ret)
		return ret;

	sw->clx = 0;

	tb_sw_dbg(sw, "CLx: %s disabled\n", clx_name(clx));
	return clx;
```

[`tb_switch_clx_disable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c#L398) copies [`clx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L216) into a local, returns 0 when the word is empty and returns the word unchanged when [`is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L193) is true. Otherwise it turns the states off on both adapters and writes 0 into the word, returning the states it removed so a caller can put them back. Those three assignments in [`drivers/thunderbolt/clx.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/clx.c) are the only writes to the member in the driver.

[`tb_switch_clx_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1088) is the one reader outside that file, and it is a single masked comparison.

```c
/* drivers/thunderbolt/tb.h:1077 */
/**
 * tb_switch_clx_is_enabled() - Checks if the CLx is enabled
 * @sw: Router to check for the CLx
 * @clx: The CLx states to check for
 *
 * Checks if the specified CLx is enabled on the router upstream link.
 *
 * Not applicable for a host router.
 *
 * Return: %true if any of the given states is enabled, %false otherwise.
 */
static inline bool tb_switch_clx_is_enabled(const struct tb_switch *sw,
					    unsigned int clx)
{
	return sw->clx & clx;
}
```

[`tb_switch_clx_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1088) masks [`clx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L216) against the states the caller names, so it answers true when any one of them is on. Its kerneldoc adds that the question does not apply to a host router, which has no upstream link for a CL state to be on. The word therefore holds what the driver last programmed, and every reader outside the CL code goes through this one test.

### Time management keeps a structure of its own

A router's time-management unit has a capability offset and a mode the driver both observes and asks for, which is more state than one member can carry. The object embeds a small structure for it by value, so that state travels with the router and needs no allocation of its own. The three excerpts below are that structure and the two writes that fill it.

[`struct tb_switch_tmu`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L105) declares four members under a kerneldoc that gives each of them its meaning.

```c
/* drivers/thunderbolt/tb.h:96 */
/**
 * struct tb_switch_tmu - Structure holding router TMU configuration
 * @cap: Offset to the TMU capability (%0 if not found)
 * @has_ucap: Does the switch support uni-directional mode
 * @mode: TMU mode related to the upstream router. Reflects the HW
 *	  setting. Don't care for host router.
 * @mode_request: TMU mode requested to set. Related to upstream router.
 *		   Don't care for host router.
 */
struct tb_switch_tmu {
	int cap;
	bool has_ucap;
	enum tb_switch_tmu_mode mode;
	enum tb_switch_tmu_mode mode_request;
};
```

[`struct tb_switch_tmu`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L105) holds one capability offset and three pieces of mode state. [`cap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L106) follows the same zero convention as the four offsets of the outer structure, and [`has_ucap`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L107) records hardware support for uni-directional operation. [`mode`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L108) and [`mode_request`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L109) are both [`enum tb_switch_tmu_mode`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L88), the first reflecting the hardware and the second the mode the driver has asked for.

[`tb_switch_tmu_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L411) fills the capability offset under the same positive-result guard the outer offsets use.

```c
/* drivers/thunderbolt/tmu.c:416 */
	if (tb_switch_is_icm(sw))
		return 0;

	ret = tb_switch_find_cap(sw, TB_SWITCH_CAP_TMU);
	if (ret > 0)
		sw->tmu.cap = ret;
```

[`tb_switch_tmu_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L411) returns 0 for a router the firmware manager owns and otherwise caches what [`tb_switch_find_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/cap.c#L198) returned. The mode members are settled by a helper of its own, which starts the observed mode at [`TB_SWITCH_TMU_MODE_OFF`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L89) and raises it to whatever the rate register and the upstream adapter report.

[`tmu_mode_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L357) closes by matching the request to the mode it settled on.

```c
/* drivers/thunderbolt/tmu.c:394 */
	/* Update the initial request to match the current mode */
	sw->tmu.mode_request = sw->tmu.mode;
	sw->tmu.has_ucap = ucap;
```

[`tmu_mode_init()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c#L357) copies the observed mode into the request so the pair starts settled, and records the uni-directional support it read earlier. Outside [`drivers/thunderbolt/tmu.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tmu.c) the embedded structure is reached only through [`tb_switch_tmu_is_configured()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1052) and [`tb_switch_tmu_is_enabled()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1065). The embedded structure therefore keeps its own two-field state beside the router's other members.

### The firmware connection manager writes its own members

Platform firmware can enumerate routers on its own, and the object carries the state that mode of operation needs. Seven members exist for it, and every assignment to them is on a path only the firmware connection manager reaches. This page names them and stops there, and the table gives the three whose reads do reach shared code.

| member | read in shared code by | at |
|---|---|---|
| [`link`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L206) and [`depth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L207) | [`tb_switch_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3759) | [switch.c:3779](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3779) and [switch.c:3781](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3781) |
| [`security_level`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L201) | [`switch_attr_is_visible()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2222) | [switch.c:2247](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2247) |
| [`safe_mode`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L197) | the add order, the mailbox step, the NVM registration and two attributes | [switch.c:371](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L371), [switch.c:2162](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2162), [switch.c:2275](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2275), [switch.c:2747](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2747) and [switch.c:3319](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3319) |

[`connection_id`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L204), [`connection_key`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L205) and [`rpm_complete`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L208) are the remaining three, and no code outside the firmware manager's file reads them. [`safe_mode`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L197) is the one of the seven whose single assignment is in [`drivers/thunderbolt/switch.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c), inside the allocation the firmware path uses, so a router the software manager created answers false at every one of those five reads. The shared code therefore stays correct without testing which connection manager is in charge, because the zero the allocation left is the right answer for it.
