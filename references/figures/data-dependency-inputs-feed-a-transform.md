# Pattern: data dependency (inputs feed a transform)

1. Use when one or more source structs are read by a function that builds or populates a destination struct, and the point is which inputs feed which output (assembling a config, intersecting capabilities, encoding a message).
2. Draw the input struct boxes at the top, the transform function as the labelled junction beneath them, and the produced struct below; the arrows mean feeds / populates / points-to, never call order.
3. The figure is a valid data-dependency picture only because its endpoints are structs: a figure whose nodes are all functions joined by call arrows is the banned code-flow chart.
4. Complements the linked-structs-via-pointers pattern, which shows structs already wired by their fields.

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
                 !rates / !formats / empty channels
                          ─▶ -EINVAL  "No matching ..."
```
