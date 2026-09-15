# Pattern: router stack with tunnel tracks

1. Use when several routers in a chain are the subject and the point is which adapter each tunnel leaves and which it enters, with the adapters' numbers, and what the tunnelled protocol's own constructs do inside a hub between one tunnel and the next.
2. Draw the routers stacked, each a box; a link is a pair of ║ rails between a downstream lane pair and the upstream lane pair of the router below; every adapter is a single-line box with its number at the right edge (`#0` is the control adapter; lane adapters come in consecutive pairs, lane 0 first); the tunnelled protocol's own constructs, a PCIe switch or a USB hub, are double-line boxes chained under the up adapter and over the down adapter they connect; tunnels are dotted tracks in the margins, one glyph per protocol, the tunnels arriving from above on the right and the ones the hub starts on the left, each track turning into the adapter it ends at and leaving the adapter it starts at.
3. Distinct from topology with a boundary (a device tree with a rule on it) and from a layered stack (layers calling through an interface): here the objects are hardware parts and the lines are traffic.
4. A track never crosses a label or another track; a PCIe or USB3 tunnel ends at an up adapter and a new one starts at a down adapter, it never passes a router; a DP tunnel may.
5. The reference is drawn at 112 columns, within the 120-column limit as it stands; a narrower page drops the note column and shortens the adapter boxes.

```
┌──────┐ a USB4 adapter of the router, #n its adapter number     ╔══════╗ a construct of the tunnelled protocol
└──────┘ (struct tb_port; port->port holds the number)          ╚══════╝ which the driver does not model

numbering: #0 is the control adapter, the router itself; lane adapters come in consecutive pairs, lane 0 then
lane 1 at the next number (the driver pairs them so in tb_switch_default_link_ports); the other numbers up to
max_port_number, at most 63, are the protocol and host-interface adapters, in the order the router reports them

┌─ HOST ROUTER  route 0  (inside the controller) ──────────────────────────────────────────────────────────────┐
│                                                             tunnels over link 1:   ╏ DP    ┆ USB3    : PCIe  │
│               ┌──────────────────────────┐                                                                   │
│               │ control adapter       #0 │                                                                   │
│               └──────────────────────────┘  the router's own configuration space                             │
│               ┌──────────────────────────┐                                                                   │
│               │ NHI adapter ◀ CPU     #9 │                                                                   │
│               └──────────────────────────┘                                                                   │
│               ┌──────────────────────────┐                                                                   │
│               │ PCIe down adapter     #5 │──────────────────────────────────────────────────────────:        │
│               └──────────────────────────┘                                                                   │
│               ┌──────────────────────────┐                                                          :        │
│               │ USB3 down adapter     #7 │────────────────────────────────────────────────────┆     :        │
│               └──────────────────────────┘                                                          :        │
│               ┌──────────────────────────┐                                                    ┆     :        │
│               │ DP IN adapter ◀ GPU   #8 │────────────────────────────────────────────╏       ┆     :        │
│               └──────────────────────────┘                                                    ┆     :        │
│               USB4 port 1  (downstream)       USB4 port 2, empty                      ╏       ┆     :        │
│               ┌────────────┬────────────┐     ┌────────────┬────────────┐             ╏       ┆     :        │
│               │ lane 0  #1 │ lane 1  #2 │     │ lane 0  #3 │ lane 1  #4 │             ╏       ┆     :        │
└───────────────┴────────────┴────────────┴─────┴────────────┴────────────┴─────────────╏───────┆─────:────────┘
                       ║            ║  link 1: two bonded lanes                         ╏       ┆     :
                       ║            ║  three tunnels, one hop each, ride it             ╏       ┆     :
                       ║            ║                                                   ╏       ┆     :
┌───────────────┬────────────┬────────────┬─────────────────────────────────────────────╏───────┆─────:────────┐
│               │ lane 0  #1 │ lane 1  #2 │  USB4 port 1  (upstream)                    ╏       ┆     :        │
│               └────────────┴────────────┘                                             ╏       ┆     :        │
│               HUB ROUTER  route 0x1  (a dock)                                         ╏       ┆     :        │
│ tunnels over  ┌──────────────────────────┐                                            ╏       ┆     :        │
│ link 3:       │ control adapter       #0 │                                            ╏       ┆     :        │
│ ┆ USB3 : PCIe └──────────────────────────┘                                            ╏       ┆     :        │
│               ┌──────────────────────────┐                                                    ┆     :        │
│               │ DP OUT ▶ monitor     #11 │◀───────────────────────────────────────────╯       ┆     :        │
│               └──────────────────────────┘  the DP tunnel ends at the dock's own adapter      ┆     :        │
│               ┌──────────────────────────┐                                                          :        │
│               │ USB3 up adapter       #9 │◀───────────────────────────────────────────────────╯     :        │
│               └──────────────────────────┘  the USB3 tunnel from the host ends here                 :        │
│                            │                                                                        :        │
│               ╔══════════════════════════╗                                                          :        │
│               ║ USB hub                  ║                                                          :        │
│               ╚══════════════════════════╝  one hub port per device on the dock, one for the next USB4 port  │
│                            │                                                                        :        │
│               ┌──────────────────────────┐                                                          :        │
│    ┆──────────│ USB3 down adapter    #10 │                                                          :        │
│               └──────────────────────────┘  a new USB3 tunnel, one hop, starts here                 :        │
│    ┆          ┌──────────────────────────┐                                                                   │
│    ┆          │ PCIe up adapter       #7 │◀─────────────────────────────────────────────────────────╯        │
│    ┆          └──────────────────────────┘  the PCIe tunnel from the host ends here                          │
│    ┆                       │ the switch's upstream port                                                      │
│    ┆          ╔══════════════════════════╗                                                                   │
│    ┆          ║ PCIe switch              ║                                                                   │
│    ┆          ╚══════════════════════════╝  downstream ports: one per USB4 port, plus on-board devices       │
│    ┆                       │ one of its downstream ports                                                     │
│    ┆          ┌──────────────────────────┐                                                                   │
│    ┆    :─────│ PCIe down adapter     #8 │                                                                   │
│    ┆          └──────────────────────────┘  a new PCIe tunnel, one hop, starts here                          │
│    ┆    :     USB4 port 2  (downstream)       USB4 port 3, empty                                             │
│    ┆    :     ┌────────────┬────────────┐     ┌────────────┬────────────┐                                    │
│    ┆    :     │ lane 0  #3 │ lane 1  #4 │     │ lane 0  #5 │ lane 1  #6 │                                    │
└────┆────:─────┴────────────┴────────────┴─────┴────────────┴────────────┴────────────────────────────────────┘
     ┆    :            ║            ║  link 3: two bonded lanes
     ┆    :            ║            ║  the dock's own tunnels ride it: USB3 ┆ and PCIe :
     ┆    :            ║            ║
┌────┆────:─────┬────────────┬────────────┬────────────────────────────────────────────────────────────────────┐
│    ┆    :     │ lane 0  #1 │ lane 1  #2 │  USB4 port 1  (upstream)                                           │
│    ┆    :     └────────────┴────────────┘                                                                    │
│    ┆    :     DEVICE ROUTER  route 0x301                                                                     │
│    ┆    :     ┌──────────────────────────┐                                                                   │
│    ┆    :     │ control adapter       #0 │                                                                   │
│    ┆    :     └──────────────────────────┘                                                                   │
│    ┆          ┌──────────────────────────┐                                                                   │
│    ┆    ╰────▶│ PCIe up ▶ NVMe        #3 │                                                                   │
│    ┆          └──────────────────────────┘  the dock's PCIe tunnel ends here                                 │
│               ┌──────────────────────────┐                                                                   │
│    ╰─────────▶│ USB3 up adapter       #4 │                                                                   │
│               └──────────────────────────┘  the dock's USB3 tunnel ends here                                 │
│               ┌──────────────────────────┐                                                                   │
│               │ DP OUT adapter        #5 │                                                                   │
│               └──────────────────────────┘  no tunnel: the DP tunnel ended at the dock                       │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```
