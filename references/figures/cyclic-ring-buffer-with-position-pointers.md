# Pattern: cyclic ring buffer with position pointers

1. Use when a single cyclic buffer is split into periods/slots and two pointers (a producer and a consumer, e.g. appl_ptr and hw_ptr) chase each other around it with wrap.
2. Draw the periods as a contiguous row of cells, a ▼ from each pointer onto its cell, and note which span is filled vs free and where the pointers wrap.
3. A specialization of queue/ring for one wrapping buffer with two positions.

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
