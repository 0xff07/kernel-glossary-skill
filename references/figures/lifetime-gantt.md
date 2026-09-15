# Pattern: lifetime Gantt

1. Use when an object's lifetime is the point and who may touch it changes at named handovers (an URB from allocation to free, a device from registration to unbind, a page from allocation to release).
2. Draw one time axis with the handover functions as column heads and dashed guides `╎` beneath them, one span bar per holder aligned to the guides, and a bottom row giving the count at each column. The count equals the bars a vertical slice crosses, which is how the reader checks it.
3. Distinct from the refcount ladder, which shows what the 0 to 1 edges trigger; this shows who holds and derives the count. Distinct from the state graph, which shows states rather than owners.

```
       One URB, its holders, and the count they add up to
       ───────────────────────────────────────────────────

       time ──────────────────────────────────────────────────────────────▶
                     usb_alloc_urb  usb_submit_urb  completion  usb_free_urb
                     ╎              ╎               ╎           ╎
       caller        ├──────────────────────────────────────────┤
       HCD                          ├───────────────┤
                     ╎              ╎               ╎           ╎
       refcount      1              2               1           0
```
