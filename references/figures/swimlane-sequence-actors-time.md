# Pattern: swimlane sequence (actors × time)

1. Use when several actors (userspace, a core layer, a driver, hardware) hand work to each other over time and the cross-actor ordering is the point.
2. Draw one vertical lane per actor separated by │ columns, time running downward, and a cross-lane ──▶ arrow for each step; annotate each lane with the state it reaches.
3. Distinct from queue/ring (a buffer between two stages): this shows N actors over one timeline.
4. The cells carry the state each actor reaches, not the next function it calls.
5. A walkthrough page is where this goes wrong most often: a lane diagram of one call stack, with every cell a callee and every arrow a call, is the banned flow graph with lane rules drawn on it.
6. If the figure would survive deleting all but one lane, it was never a swimlane.

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
