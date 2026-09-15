# Pattern: queue / ring between two stages

1. Use when a producer and a consumer communicate through a bounded buffer (kfifo, work_struct, list_head ring).
2. Show the buffer as a row of cells in the middle; the two stages flank it; arrows label the put / get operations.

```
       Producer side              kfifo / work / ring         Consumer side
       ┌──────────────────┐       ┌──┬──┬──┬─────┬───┐        ┌──────────────┐
       │ Stage A reads    │  put  │e0│e1│e2│ ... │e_n│  get   │ Stage B      │
       │ source, RW1C     │──────▶└──┴──┴──┴─────┴───┘───────▶│ dequeues,    │
       │ clear, enqueue   │                                   │ processes    │
       │ ... return       │                                   │ ... return   │
       │ IRQ_WAKE_THREAD  │                                   │ IRQ_HANDLED  │
       └──────────────────┘                                   └──────────────┘
```
