# Pattern: protocol columns through a router stack

1. Use when the point is the passage of traffic through a router: from a protocol adapter into the lane adapters of a USB4 port, over the link, out of the lane adapters of the upstream port and into the protocol adapter of the next router, with the tunnelled protocol's own constructs shown where they sit between one tunnel and the next.
2. Draw one column per protocol and the routers stacked; each router's USB4 port is one wide box the tunnels enter from above (▼) and leave from below; the protocol adapters sit directly under their columns; a hub's native constructs (double-line boxes) sit in the column between its up adapter and its down adapter, joined by plain verticals; a tunnel is a dotted vertical, one glyph per protocol, continuous from the adapter it leaves to the adapter it enters; labels sit only in the gaps between columns.
3. Distinct from the router stack with tunnel tracks: that one shows which adapters pair up, this one shows the route the bytes take; distinct from a swimlane: the columns are protocols, not actors, and nothing crosses between them.
4. A column carries text nowhere; a tunnel that ends stops at its adapter and the column stays empty below; a router's title goes in the gap on its top border.
5. The reference is drawn at 116 columns, within the 120-column limit as it stands; a narrower page draws two protocol columns, or shortens the boxes to twenty.

```
┌──────┐ a USB4 adapter of the router, #n its adapter number      ╔══════╗ a construct of the tunnelled protocol
└──────┘                                                          ╚══════╝
  :  PCIe tunnel     ┆  USB3 tunnel     ╏  DP tunnel      ▼  the tunnel enters the adapter or the port below

┌── HOST ROUTER  route 0  (inside the controller) ─────────────────────────────────────────────────────────────────┐
│                                                                                                                  │
│       ┌──────────────────────────┐        ┌──────────────────────────┐                                           │
│       │ control adapter       #0 │        │ NHI adapter ◀ CPU     #9 │                                           │
│       └──────────────────────────┘        └──────────────────────────┘                                           │
│         the router itself                   the host interface: rings                                            │
│                                                                                                                  │
│       ┌──────────────────────────┐        ┌──────────────────────────┐        ┌──────────────────────────┐       │
│       │ PCIe down adapter     #5 │        │ USB3 down adapter     #7 │        │ DP IN adapter ◀ GPU   #8 │       │
│       └────────────:─────────────┘        └────────────┆─────────────┘        └────────────╏─────────────┘       │
│                    :  each adapter hands its traffic   ┆                                   ╏                     │
│                    :  to the lane adapters below       ┆                                   ╏                     │
│     ┌──────────────▼───────────────────────────────────▼───────────────────────────────────▼───────────────┐     │
│     │ USB4 port 1, downstream:  lane 0 adapter #1  +  lane 1 adapter #2, bonded into one link              │     │
│     └──────────────:───────────────────────────────────┆───────────────────────────────────╏───────────────┘     │
└────────────────────:───────────────────────────────────┆───────────────────────────────────╏─────────────────────┘
      ║              :  link 1, the two lanes            ┆                                   ╏               ║
      ║              :  three tunnels, one hop each      ┆                                   ╏               ║
      ║              :                                   ┆                                   ╏               ║
┌────────────────────:── HUB ROUTER  route 0x1 ──────────┆───────────────────────────────────╏─────────────────────┐
│     ┌──────────────▼───────────────────────────────────▼───────────────────────────────────▼───────────────┐     │
│     │ USB4 port 1, upstream:  lane 0 adapter #1  +  lane 1 adapter #2                                      │     │
│     └──────────────:───────────────────────────────────┆───────────────────────────────────╏───────────────┘     │
│                    :  the lane adapters deliver        ┆                                   ╏                     │
│                    :  each tunnel to its adapter       ┆                                   ╏                     │
│       ┌────────────▼─────────────┐        ┌────────────▼─────────────┐        ┌────────────▼─────────────┐       │
│       │ PCIe up adapter       #7 │        │ USB3 up adapter       #9 │        │ DP OUT ▶ monitor     #11 │       │
│       └────────────┬─────────────┘        └────────────┬─────────────┘        └──────────────────────────┘       │
│                    │ PCIe leaves USB4 here             │ USB3 leaves USB4 here    the DP tunnel ends here        │
│                    │ the switch's upstream port        │ the hub's upstream port                                 │
│       ╔════════════╧═════════════╗        ╔════════════╧═════════════╗                                           │
│       ║ PCIe switch              ║        ║ USB hub                  ║                                           │
│       ╚════════════╤═════════════╝        ╚════════════╤═════════════╝                                           │
│                    │ one downstream port; the others   │ one downstream port; the others                         │
│                    │ serve the on-board PCIe devices   │ serve the dock's own USB devices                        │
│       ┌────────────┴─────────────┐        ┌────────────┴─────────────┐                                           │
│       │ PCIe down adapter     #8 │        │ USB3 down adapter    #10 │                                           │
│       └────────────:─────────────┘        └────────────┆─────────────┘                                           │
│                    :  two new tunnels, one hop each,   ┆                                                         │
│                    :  start here                       ┆                                                         │
│     ┌──────────────▼───────────────────────────────────▼───────────────────────────────────────────────────┐     │
│     │ USB4 port 2, downstream:  lane 0 adapter #3  +  lane 1 adapter #4, bonded into one link              │     │
│     └──────────────:───────────────────────────────────┆───────────────────────────────────────────────────┘     │
└────────────────────:───────────────────────────────────┆─────────────────────────────────────────────────────────┘
      ║              :  link 3, the two lanes            ┆                                                   ║
      ║              :  the dock's own two tunnels       ┆                                                   ║
      ║              :                                   ┆                                                   ║
┌────────────────────:── DEVICE ROUTER  route 0x301 ─────┆─────────────────────────────────────────────────────────┐
│     ┌──────────────▼───────────────────────────────────▼───────────────────────────────────────────────────┐     │
│     │ USB4 port 1, upstream:  lane 0 adapter #1  +  lane 1 adapter #2                                      │     │
│     └──────────────:───────────────────────────────────┆───────────────────────────────────────────────────┘     │
│                    :                                   ┆                                                         │
│       ┌────────────▼─────────────┐        ┌────────────▼─────────────┐        ┌──────────────────────────┐       │
│       │ PCIe up ▶ NVMe        #3 │        │ USB3 up adapter       #4 │        │ DP OUT adapter        #5 │       │
│       └──────────────────────────┘        └──────────────────────────┘        └──────────────────────────┘       │
│         the dock's PCIe tunnel ends         the dock's USB3 tunnel ends         no tunnel reaches it             │
│                                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```
