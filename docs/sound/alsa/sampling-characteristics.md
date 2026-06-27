# Audio sampling characteristics

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A PCM stream is described by five parameters, the sample format, the sample rate, the channel count, the access mode, and the buffer geometry, and ALSA carries them in one userspace-visible object, [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408), which the kernel refines during the [`SNDRV_PCM_IOCTL_HW_REFINE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L680) and [`SNDRV_PCM_IOCTL_HW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L681) calls until each parameter is pinned to a value the hardware accepts. The two parameter shapes are stored differently. An enumerated parameter (the sample format and the access mode) is a [`struct snd_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L404), a bitmap of every permitted value, and a ranged parameter (the rate, the channel count, the period size, and the buffer size) is a [`struct snd_interval`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L394), a `[min, max]` pair with open-endpoint and integer flags. The sample format itself is a [`snd_pcm_format_t`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L180) token, and the geometry of the bits behind that token (the valid width inside the physical word, the signedness, the endianness, the byte size) is read back through the helpers in [`pcm_misc.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c) such as [`snd_pcm_format_width()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L335) and [`snd_pcm_format_physical_width()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L354), which index the static [`pcm_formats`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L35) table. Once the parameters settle, the accepted value of each is committed into the matching field of [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362), and the [`params_format()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L313) family of accessors reads the single settled value straight out of the mask or interval.

```
    one PCM stream parameter set
    ────────────────────────────

    enumerated (snd_mask)            ranged (snd_interval)
    ┌───────────────────────┐        ┌───────────────────────┐
    │ access  (bitmap)      │        │ rate         [min,max]│
    │ format  (bitmap)      │        │ channels     [min,max]│
    │ subformat (bitmap)    │        │ period_size  [min,max]│
    └───────────┬───────────┘        │ buffer_size  [min,max]│
                │                    └───────────┬───────────┘
       snd_mask_refine()              snd_interval_refine()
                │   HW_REFINE / HW_PARAMS        │
                ▼                                ▼
    ┌─────────────────────────────────────────────────────────┐
    │ struct snd_pcm_runtime  (settled values)                │
    │  format, access   rate, channels   period_size, periods │
    │  frame_bits = channels x physical_width(format)         │
    └─────────────────────────────────────────────────────────┘
```

## SUMMARY

ALSA negotiates a PCM stream's parameters through one structure, [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408). It holds an array of [`struct snd_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L404) for the enumerated parameters indexed from [`SNDRV_PCM_HW_PARAM_FIRST_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L359), an array of [`struct snd_interval`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L394) for the ranged parameters indexed from [`SNDRV_PCM_HW_PARAM_FIRST_INTERVAL`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L384), and the [`rmask`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) and [`cmask`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) words that mark which parameters a caller asked to change and which the kernel narrowed in response. The sample format is one of the [`snd_pcm_format_t`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L180) tokens, [`SNDRV_PCM_FORMAT_S16_LE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L183), [`SNDRV_PCM_FORMAT_S24_LE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L187), [`SNDRV_PCM_FORMAT_S32_LE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L196), and the rest up to [`SNDRV_PCM_FORMAT_LAST`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L238). The token only names the format; the [`pcm_formats`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L35) table in [`pcm_misc.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c) stores the actual geometry per format, and [`snd_pcm_format_width()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L335), [`snd_pcm_format_physical_width()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L354), [`snd_pcm_format_size()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L374), [`snd_pcm_format_signed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L249), [`snd_pcm_format_big_endian()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L317), and [`snd_pcm_format_set_silence()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L409) read it out.

The rate is described by the [`SNDRV_PCM_RATE_*`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L109) flags in the driver's capability mask, with [`SNDRV_PCM_RATE_CONTINUOUS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L131) marking a driver that accepts any rate inside its min/max and [`SNDRV_PCM_RATE_KNOT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L132) marking one that accepts a discrete list outside the standard grid. The channel count is an interval, and the access mode is one of [`SNDRV_PCM_ACCESS_RW_INTERLEAVED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L176), [`SNDRV_PCM_ACCESS_RW_NONINTERLEAVED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L177), [`SNDRV_PCM_ACCESS_MMAP_INTERLEAVED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L173), or [`SNDRV_PCM_ACCESS_MMAP_NONINTERLEAVED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L174). The geometry of the data buffer is three nested units. A frame is one sample for every channel taken at one instant, a period is the run of frames the hardware consumes between two interrupts, and the buffer is the ring of periods the DMA engine cycles through, all committed into the [`period_size`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L384), [`periods`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L385), and [`buffer_size`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L386) fields of [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) and converted to and from bytes by [`frames_to_bytes()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L775) and [`bytes_to_frames()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L751) using the cached [`frame_bits`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L389). The narrowing itself runs through [`snd_mask_refine()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L153) for the masks and [`snd_interval_refine()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L626) for the intervals, and a driver adds its own restrictions through [`snd_pcm_hw_constraint_minmax()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1284), [`snd_pcm_hw_constraint_list()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1316), and [`snd_pcm_hw_constraint_integer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1265).

## SPECIFICATIONS

The PCM parameter set is a Linux kernel and ALSA software construct and has no standalone hardware specification. The sample formats it enumerates correspond to the linear PCM, IEEE-754 float, and DSD encodings carried on the wire formats defined by the Intel High Definition Audio Specification and the USB Audio Class Specification, while the [`snd_pcm_format_t`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L180) numbering and the mask/interval algebra are ALSA's own.

## LINUX KERNEL

### Format token and the format table (asound.h, pcm_misc.c)

- [`'\<snd_pcm_format_t\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L180): the `__bitwise` typedef naming a sample format; values run [`SNDRV_PCM_FORMAT_S8`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L181) (0) through [`SNDRV_PCM_FORMAT_LAST`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L238)
- [`'\<struct pcm_format_data\>':'sound/core/pcm_misc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L19): the per-format geometry record holding [`width`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L20), [`phys`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L21), [`le`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L22), [`signd`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L23), and the [`silence`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L24) pattern
- [`'\<pcm_formats\>':'sound/core/pcm_misc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L35): the static array of [`struct pcm_format_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L19) indexed by the format token
- [`'\<snd_pcm_format_width\>':'sound/core/pcm_misc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L335): the count of valid sample bits (24 for [`SNDRV_PCM_FORMAT_S24_LE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L187))
- [`'\<snd_pcm_format_physical_width\>':'sound/core/pcm_misc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L354): the count of bits the sample occupies on the bus (32 for [`SNDRV_PCM_FORMAT_S24_LE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L187))
- [`'\<snd_pcm_format_size\>':'sound/core/pcm_misc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L374): the byte count of N samples, `samples * phys / 8`
- [`'\<snd_pcm_format_signed\>':'sound/core/pcm_misc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L249) / [`'\<snd_pcm_format_unsigned\>':'sound/core/pcm_misc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L268): linear sign, or a negative error for non-linear formats
- [`'\<snd_pcm_format_little_endian\>':'sound/core/pcm_misc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L298) / [`'\<snd_pcm_format_big_endian\>':'sound/core/pcm_misc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L317): byte order, with [`snd_pcm_format_big_endian()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L317) defined as the negation of the little-endian result
- [`'\<snd_pcm_format_set_silence\>':'sound/core/pcm_misc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L409): write the format's silence pattern across a sample run, used to pad the buffer
- [`'\<SNDRV_PCM_FMTBIT_S16_LE\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L151): the `1ULL << format` bit a driver ORs into its capability mask, built by [`_SNDRV_PCM_FMTBIT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L148)

### Rate and access constants (pcm.h, asound.h)

- [`'\<SNDRV_PCM_RATE_44100\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L115) / [`'\<SNDRV_PCM_RATE_48000\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L116): single-rate flags on the standard grid (each `1U << n`), starting at [`SNDRV_PCM_RATE_5512`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L109)
- [`'\<SNDRV_PCM_RATE_CONTINUOUS\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L131): the driver accepts any rate between its rate_min and rate_max
- [`'\<SNDRV_PCM_RATE_KNOT\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L132): the driver accepts discrete rates off the grid, supplied as a constraint list
- [`'\<snd_pcm_access_t\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L172): the access-mode token; [`SNDRV_PCM_ACCESS_RW_INTERLEAVED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L176) (channels packed per frame), [`SNDRV_PCM_ACCESS_RW_NONINTERLEAVED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L177) (one buffer per channel), and the [`SNDRV_PCM_ACCESS_MMAP_INTERLEAVED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L173) / [`SNDRV_PCM_ACCESS_MMAP_NONINTERLEAVED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L174) mmap variants

### Parameter container and algebra (asound.h, pcm_params.h, pcm.h)

- [`'\<struct snd_pcm_hw_params\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408): the userspace-visible parameter set, an array of masks and an array of intervals plus the [`rmask`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408)/[`cmask`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) request/change words
- [`'\<struct snd_mask\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L404): the bitmap of permitted enumerated values (format, access, subformat)
- [`'\<struct snd_interval\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L394): the `[min, max]` range with [`openmin`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L394), [`openmax`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L394), [`integer`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L394), and [`empty`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L394) flags (rate, channels, sizes)
- [`'\<snd_pcm_hw_param_t\>':'include/uapi/sound/asound.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L355): the parameter index; the mask range begins at [`SNDRV_PCM_HW_PARAM_FIRST_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L359), the interval range at [`SNDRV_PCM_HW_PARAM_FIRST_INTERVAL`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L384)
- [`'\<hw_param_mask_c\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L990) / [`'\<hw_param_interval_c\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L996): select one mask or one interval out of [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) by parameter index
- [`'\<params_format\>':'include/sound/pcm_params.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L313) / [`'\<params_access\>':'include/sound/pcm_params.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L303) / [`'\<params_subformat\>':'include/sound/pcm_params.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L323): read the settled enumerated value via [`snd_mask_min()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L45)
- [`'\<params_rate\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1019) / [`'\<params_channels\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1008) / [`'\<params_period_size\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1030) / [`'\<params_buffer_size\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1052): read the settled ranged value (the interval `min`)
- [`'\<params_period_bytes\>':'include/sound/pcm_params.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L334): the period size already converted to bytes
- [`'\<snd_mask_min\>':'include/sound/pcm_params.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L45) / [`'\<snd_mask_test\>':'include/sound/pcm_params.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L126): the lowest set value of a mask, and a membership test
- [`'\<snd_interval_single\>':'include/sound/pcm_params.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L241) / [`'\<snd_interval_value\>':'include/sound/pcm_params.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L247): test whether an interval has collapsed to one value and read it

### Refinement and constraints (pcm_lib.c, pcm_native.c)

- [`'\<snd_mask_refine\>':'include/sound/pcm_params.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L153): intersect a mask with a reference mask, returning a change flag or `-EINVAL` if it empties
- [`'\<snd_interval_refine\>':'sound/core/pcm_lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L626): tighten an interval to the overlap of two intervals, re-evaluating the endpoint and integer flags
- [`'\<snd_pcm_hw_refine\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L551): the `HW_REFINE` entry point; runs [`constrain_mask_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L289) then the interval and rule passes
- [`'\<constrain_mask_params\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L289): walk every mask parameter the caller flagged in [`rmask`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) and refine it against the driver's constraint mask
- [`'\<snd_pcm_hw_constraint_minmax\>':'sound/core/pcm_lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1284): clamp an interval parameter to a `[min, max]` a driver imposes
- [`'\<snd_pcm_hw_constraint_list\>':'sound/core/pcm_lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1316): restrict a parameter to a discrete list, the mechanism behind [`SNDRV_PCM_RATE_KNOT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L132)
- [`'\<snd_pcm_hw_constraint_integer\>':'sound/core/pcm_lib.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1265): force a parameter to integer values, set on the period and buffer sizes
- [`'\<snd_pcm_hw_param_value\>':'include/sound/pcm_params.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L18): read a single settled parameter, with [`snd_pcm_hw_param_first()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L12) and [`snd_pcm_hw_param_last()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L15) collapsing it to its low or high end

### Settled runtime fields and frame conversion (pcm.h)

- [`'\<struct snd_pcm_runtime\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362): the per-substream state; the HW params block holds [`access`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L379), [`format`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L380), [`rate`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L382), [`channels`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L383), [`period_size`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L384), [`periods`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L385), [`buffer_size`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L386), [`frame_bits`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L389), and [`sample_bits`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L390)
- [`'\<frames_to_bytes\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L775) / [`'\<bytes_to_frames\>':'include/sound/pcm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L751): scale between frames and bytes using the cached [`frame_bits`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L389)

## KERNEL DOCUMENTATION

- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the driver-side capability declaration, the hardware constraints, the HW params callback, and the period/buffer model
- [`Documentation/sound/kernel-api/alsa-driver-api.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/alsa-driver-api.rst): the kernel-API reference pulling in the PCM helpers, the runtime struct, and the format functions
- [`Documentation/sound/designs/timestamping.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/timestamping.rst): how the frame counters relate to the buffer and period geometry described here

## OTHER SOURCES

- [ALSA project library documentation (PCM interface)](https://www.alsa-project.org/alsa-doc/alsa-lib/pcm.html)
- [A Tutorial on Using the ALSA Audio API (Paul Davis)](https://users.suse.com/~mana/alsa090_howto.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

User space reaches the parameter set through two ioctls on the PCM character device, [`SNDRV_PCM_IOCTL_HW_REFINE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L680) and [`SNDRV_PCM_IOCTL_HW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L681), both carrying a [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408). The refine ioctl narrows the parameters without committing, so a client can probe what the hardware allows, and the params ioctl narrows them and, once every parameter has collapsed to a single value, commits the result into [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362). The mapping from the ioctl a client issues to the kernel parameter it touches is fixed.

| ioctl / accessor | parameter | container |
|------------------|-----------|-----------|
| [`SNDRV_PCM_IOCTL_HW_REFINE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L680) | all (probe, no commit) | [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) |
| [`SNDRV_PCM_IOCTL_HW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L681) | all (narrow and commit) | [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362) |
| [`params_format()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L313) | sample format | mask [`SNDRV_PCM_HW_PARAM_FORMAT`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L357) |
| [`params_access()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L303) | access mode | mask [`SNDRV_PCM_HW_PARAM_ACCESS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L356) |
| [`params_rate()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1019) | sample rate | interval [`SNDRV_PCM_HW_PARAM_RATE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L365) |
| [`params_channels()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1008) | channel count | interval |
| [`params_period_size()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1030) | period size (frames) | interval |
| [`params_buffer_size()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1052) | buffer size (frames) | interval |

## DETAILS

### The sample format names an index into the geometry table

A [`snd_pcm_format_t`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L180) token is a `__bitwise` integer, and the constants are small consecutive numbers, [`SNDRV_PCM_FORMAT_S8`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L181) is 0, [`SNDRV_PCM_FORMAT_S16_LE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L183) is 2, [`SNDRV_PCM_FORMAT_S24_LE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L187) is 6, up to [`SNDRV_PCM_FORMAT_LAST`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L238). The token carries no geometry by itself; it indexes the static [`pcm_formats`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L35) array, whose element type [`struct pcm_format_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L19) records the valid width, the physical width, the byte order, the sign, and the silence pattern:

```c
/* sound/core/pcm_misc.c:19 */
struct pcm_format_data {
	unsigned char width;	/* bit width */
	unsigned char phys;	/* physical bit width */
	signed char le;	/* 0 = big-endian, 1 = little-endian, -1 = others */
	signed char signd;	/* 0 = unsigned, 1 = signed, -1 = others */
	unsigned char silence[8];	/* silence data to fill */
};
```

The distinction between [`width`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L20) and [`phys`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L21) is the count of meaningful bits against the count of bits the sample takes up in memory and on the bus. For [`SNDRV_PCM_FORMAT_S16_LE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L183) the two are equal at 16, while [`SNDRV_PCM_FORMAT_S24_LE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L187) carries 24 valid bits inside a 32-bit physical word, and [`SNDRV_PCM_FORMAT_S24_3LE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L217) packs the same 24 bits into exactly 3 bytes. The table rows show the difference directly:

```c
/* sound/core/pcm_misc.c:44 */
	[SNDRV_PCM_FORMAT_S16_LE] = {
		.width = 16, .phys = 16, .le = 1, .signd = 1,
		.silence = {},
	},
	...
	[SNDRV_PCM_FORMAT_S24_LE] = {
		.width = 24, .phys = 32, .le = 1, .signd = 1,
		.silence = {},
	},
	...
	[SNDRV_PCM_FORMAT_S24_3LE] = {
		.width = 24, .phys = 24, .le = 1, .signd = 1,
		.silence = {},
	},
```

Those width and phys numbers lay out as bytes, the padding byte appearing only where the valid width falls short of the physical word:

```
    valid sample bits inside the physical word, per format
    ────────────────────────────────────────────────────────
    (each cell is one byte; V = valid sample byte, P = padding)

    S16_LE   width 16  phys 16   ┌────┬────┐
                                 │ V  │ V  │        2 bytes, no pad
                                 └────┴────┘
    S24_LE   width 24  phys 32   ┌────┬────┬────┬────┐
                                 │ V  │ V  │ V  │ P  │  4 bytes, 1 pad
                                 └────┴────┴────┴────┘
    S24_3LE  width 24  phys 24   ┌────┬────┬────┐
                                 │ V  │ V  │ V  │       3 bytes, packed
                                 └────┴────┴────┘
    (le = 1 little-endian, signd = 1 signed for all three)
```

### The format helpers read the table after validating the token

[`snd_pcm_format_width()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L335) returns the valid-bit count. It checks the token is in range, indexes [`pcm_formats`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L35), and treats a zero width as an unknown format:

```c
/* sound/core/pcm_misc.c:335 */
int snd_pcm_format_width(snd_pcm_format_t format)
{
	int val;
	if (!valid_format(format))
		return -EINVAL;
	val = pcm_formats[(INT)format].width;
	if (!val)
		return -EINVAL;
	return val;
}
```

[`snd_pcm_format_physical_width()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L354) is the same function over the [`phys`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L21) field, and [`snd_pcm_format_size()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L374) builds on it to turn a sample count into a byte count, so a driver sizing a DMA buffer multiplies frames by channels and feeds the product here:

```c
/* sound/core/pcm_misc.c:374 */
ssize_t snd_pcm_format_size(snd_pcm_format_t format, size_t samples)
{
	int phys_width = snd_pcm_format_physical_width(format);
	if (phys_width < 0)
		return -EINVAL;
	return samples * phys_width / 8;
}
```

The sign and endianness helpers read the [`signd`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L23) and [`le`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L22) fields, both encoded so that `-1` means the question does not apply to a non-linear format. [`snd_pcm_format_signed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L249) returns 1 for a signed linear format, 0 for unsigned linear, and a negative error otherwise, and [`snd_pcm_format_big_endian()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L317) is defined purely by negating [`snd_pcm_format_little_endian()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L298):

```c
/* sound/core/pcm_misc.c:249 */
int snd_pcm_format_signed(snd_pcm_format_t format)
{
	int val;
	if (!valid_format(format))
		return -EINVAL;
	val = pcm_formats[(INT)format].signd;
	if (val < 0)
		return -EINVAL;
	return val;
}
```

The other two members of the linear-geometry trio are defined by negation. [`snd_pcm_format_unsigned()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L268) inverts [`snd_pcm_format_signed()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L249), so a [`SNDRV_PCM_FORMAT_U16_LE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L185) sample reports unsigned and a [`SNDRV_PCM_FORMAT_S16_LE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L183) one reports signed, and a non-linear token propagates the same negative error through both:

```c
/* sound/core/pcm_misc.c:268 */
int snd_pcm_format_unsigned(snd_pcm_format_t format)
{
	int val;

	val = snd_pcm_format_signed(format);
	if (val < 0)
		return val;
	return !val;
}
```

The byte-order pair works the same way. [`snd_pcm_format_little_endian()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L298) reads the [`le`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L22) field directly, distinguishing [`SNDRV_PCM_FORMAT_S16_LE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L183) from its [`SNDRV_PCM_FORMAT_S16_BE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L184) sibling, and [`snd_pcm_format_big_endian()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L317) is the same query negated:

```c
/* sound/core/pcm_misc.c:298 */
int snd_pcm_format_little_endian(snd_pcm_format_t format)
{
	int val;
	if (!valid_format(format))
		return -EINVAL;
	val = pcm_formats[(INT)format].le;
	if (val < 0)
		return -EINVAL;
	return val;
}
```

```c
/* sound/core/pcm_misc.c:317 */
int snd_pcm_format_big_endian(snd_pcm_format_t format)
{
	int val;

	val = snd_pcm_format_little_endian(format);
	if (val < 0)
		return val;
	return !val;
}
```

[`snd_pcm_format_set_silence()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L409) uses the [`silence`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_misc.c#L24) pattern to fill a sample run, which the core needs because the byte value that encodes silence depends on the sign. A signed format is silent at all-zero bytes, so the function takes a [`memset()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fortify-string.h#L510) shortcut, while an unsigned format such as [`SNDRV_PCM_FORMAT_U16_LE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L185) carries its midpoint `0x8000` and must copy the multi-byte pattern per sample:

```c
/* sound/core/pcm_misc.c:409 */
int snd_pcm_format_set_silence(snd_pcm_format_t format, void *data, unsigned int samples)
{
	int width;
	unsigned char *dst;
	const unsigned char *pat;

	if (!valid_format(format))
		return -EINVAL;
	if (samples == 0)
		return 0;
	width = pcm_formats[(INT)format].phys; /* physical width */
	if (!width)
		return -EINVAL;
	pat = pcm_formats[(INT)format].silence;
	/* signed or 1 byte data */
	if (pcm_formats[(INT)format].signd == 1 || width <= 8) {
		unsigned int bytes = samples * width / 8;
		memset(data, *pat, bytes);
		return 0;
	}
	...
}
```

Each accessor pulls one column from the same table row, the width helper giving valid bits, the physical-width helper the bus width, and the size helper the byte count:

```
    sample format ─▶ geometry the format helpers return
    ─────────────────────────────────────────────────────

    format       width   phys   size(1 sample)
    ───────────────────────────────────────────────
    S16_LE         16      16        2 bytes
    S24_LE         24      32        4 bytes
    S24_3LE        24      24        3 bytes
    ───────────────────────────────────────────────
      snd_pcm_format_width()          ─▶ valid bits
      snd_pcm_format_physical_width() ─▶ bus bits (phys)
      snd_pcm_format_size(n)          ─▶ n x phys / 8 bytes
```

### The rate is a flag set or a continuous range

A driver advertises the rates it supports as a mask of [`SNDRV_PCM_RATE_*`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L109) flags, each a single bit on a fixed grid, [`SNDRV_PCM_RATE_44100`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L115) is `1U << 6` and [`SNDRV_PCM_RATE_48000`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L116) is `1U << 7`. The two high bits change the meaning of the mask. [`SNDRV_PCM_RATE_CONTINUOUS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L131) marks a driver, a software rate converter for instance, that accepts every rate between its declared minimum and maximum rather than only the grid points, and [`SNDRV_PCM_RATE_KNOT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L132) marks a driver whose clock yields a discrete set of rates that do not fall on the grid, which it then supplies as an explicit list through [`snd_pcm_hw_constraint_list()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1316). Inside [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) the rate is stored as an interval at [`SNDRV_PCM_HW_PARAM_RATE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L365) rather than this flag mask, and [`params_rate()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1019) reads its settled value off the interval `min` once it has collapsed to one number:

```c
/* include/sound/pcm.h:1019 */
static inline unsigned int params_rate(const struct snd_pcm_hw_params *p)
{
	return hw_param_interval_c(p, SNDRV_PCM_HW_PARAM_RATE)->min;
}
```

The settled rate the reader returns traces back to a driver capability mask of one bit per grid rate, the two high bits widening it to a continuous span or a discrete off-grid list:

```
    SNDRV_PCM_RATE_* capability mask (each grid rate = 1U << n)
    ───────────────────────────────────────────────────────────

    bit   high bits ...    7        6     ...     0
        ┌──────────────┬────────┬────────┬─────┬────────┐
        │ KNOT / CONT  │ 48000  │ 44100  │ ... │  5512  │
        │              │ 1U<<7  │ 1U<<6  │     │ 1U<<0  │
        └──────┬───────┴────────┴────────┴─────┴────────┘
               │
               └─ high bits change how the mask reads:
                  CONTINUOUS = any rate in [rate_min, rate_max]
                  KNOT       = a discrete off-grid list
```

### Channels and access mode

The channel count is a ranged parameter, read by [`params_channels()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1008) off the interval at [`SNDRV_PCM_HW_PARAM_CHANNELS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L364), and a driver constrains it with [`snd_pcm_hw_constraint_minmax()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1284) when only certain counts are wired. The access mode is an enumerated parameter held in a mask, and the four values split along two axes. [`SNDRV_PCM_ACCESS_RW_INTERLEAVED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L176) and [`SNDRV_PCM_ACCESS_RW_NONINTERLEAVED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L177) move data through `read()`/`write()` copies, while [`SNDRV_PCM_ACCESS_MMAP_INTERLEAVED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L173) and [`SNDRV_PCM_ACCESS_MMAP_NONINTERLEAVED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L174) let the client touch the DMA buffer directly. The interleaved variants pack one frame's channels contiguously (L R L R for stereo), and the non-interleaved variants keep one separate buffer per channel. [`params_access()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L303) reads the settled value with the same [`snd_mask_min()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L45) call that [`params_format()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L313) uses:

```c
/* include/sound/pcm_params.h:303 */
static inline snd_pcm_access_t params_access(const struct snd_pcm_hw_params *p)
{
	return (__force snd_pcm_access_t)snd_mask_min(hw_param_mask_c(p,
		SNDRV_PCM_HW_PARAM_ACCESS));
}
```

The channel count travels in an interval rather than a mask, so its accessor takes the parallel form, [`params_channels()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1008) reads the interval `min` at [`SNDRV_PCM_HW_PARAM_CHANNELS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L364) the same way [`params_rate()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1019) reads the rate, and the value it returns is the multiplier behind the frame size, since one frame holds that many samples:

```c
/* include/sound/pcm.h:1008 */
static inline unsigned int params_channels(const struct snd_pcm_hw_params *p)
{
	return hw_param_interval_c(p, SNDRV_PCM_HW_PARAM_CHANNELS)->min;
}
```

The enumerated parameter held alongside the format is the subformat, and [`params_subformat()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L324) reads it from its own mask at [`SNDRV_PCM_HW_PARAM_SUBFORMAT`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L358) with the same [`snd_mask_min()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L45) call the format and access accessors use, returning the settled [`snd_pcm_subformat_t`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L268) token:

```c
/* include/sound/pcm_params.h:324 */
static inline snd_pcm_subformat_t
params_subformat(const struct snd_pcm_hw_params *p)
{
	return (__force snd_pcm_subformat_t)snd_mask_min(hw_param_mask_c(p,
		SNDRV_PCM_HW_PARAM_SUBFORMAT));
}
```

Access mode settles out of its mask the same way, its four values sitting at the crossing of a transfer-method axis (read/write or mmap) and a layout axis (interleaved or non-interleaved):

```
    access mode: two independent axes
    ───────────────────────────────────
    (one mask value selects one cell)

                     │ interleaved        │ non-interleaved
    ─────────────────┼────────────────────┼──────────────────
     read() / write()│ RW_INTERLEAVED     │ RW_NONINTERLEAVED
     mmap (direct)   │ MMAP_INTERLEAVED   │ MMAP_NONINTERLEAVED

    interleaved frame (stereo)        non-interleaved (stereo)
    ┌────┬────┬────┬────┐             ┌──────────────────┐ L
    │ L0 │ R0 │ L1 │ R1 │             └──────────────────┘
    └────┴────┴────┴────┘             ┌──────────────────┐ R
    channels packed per frame         └──────────────────┘
                                      one buffer per channel
```

### Frames, periods, and the buffer ring

The buffer geometry nests three units. A sample is one value of one channel, occupying physical-width bits with the valid width inside it. A frame is one sample for every channel taken at the same instant, so its size in bits is the channel count times the physical width, cached as [`frame_bits`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L389). A period is the count of frames the hardware transfers between two interrupts, committed as [`period_size`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L384), and the buffer is the ring of [`periods`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L385) periods the DMA engine cycles through, with the whole span committed as [`buffer_size`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L386).

The runtime caches the bit geometry so the data path never recomputes it. [`frames_to_bytes()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L775) and [`bytes_to_frames()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L751) both multiply or divide by [`frame_bits`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L389), which is the channel count times the physical width:

```c
/* include/sound/pcm.h:775 */
static inline ssize_t frames_to_bytes(struct snd_pcm_runtime *runtime, snd_pcm_sframes_t size)
{
	return size * runtime->frame_bits / 8;
}
```

[`bytes_to_frames()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L751) is the exact inverse, dividing a byte count by the same cached [`frame_bits`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L389), so a residue from the hardware pointer in bytes converts straight back to a whole frame offset:

```c
/* include/sound/pcm.h:751 */
static inline snd_pcm_sframes_t bytes_to_frames(struct snd_pcm_runtime *runtime, ssize_t size)
{
	return size * 8 / runtime->frame_bits;
}
```

The period and buffer sizes are read back from [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) the same way the rate is, off an interval `min`. [`params_period_size()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1030) reads the period in frames, and [`params_buffer_size()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1052) the whole ring:

```c
/* include/sound/pcm.h:1030 */
static inline unsigned int params_period_size(const struct snd_pcm_hw_params *p)
{
	return hw_param_interval_c(p, SNDRV_PCM_HW_PARAM_PERIOD_SIZE)->min;
}
```

[`params_buffer_size()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1052) reaches the outer unit the same way, off the interval at [`SNDRV_PCM_HW_PARAM_BUFFER_SIZE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L381), and gives back the whole ring in frames:

```c
/* include/sound/pcm.h:1052 */
static inline unsigned int params_buffer_size(const struct snd_pcm_hw_params *p)
{
	return hw_param_interval_c(p, SNDRV_PCM_HW_PARAM_BUFFER_SIZE)->min;
}
```

The frame sizes have byte-denominated companions stored as their own intervals so a driver never has to multiply by the frame size itself, [`params_period_bytes()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L335) returns the period already in bytes off the interval at [`SNDRV_PCM_HW_PARAM_PERIOD_BYTES`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L372), the figure a DMA descriptor wants directly:

```c
/* include/sound/pcm_params.h:335 */
static inline unsigned int
params_period_bytes(const struct snd_pcm_hw_params *p)
{
	return hw_param_interval_c(p, SNDRV_PCM_HW_PARAM_PERIOD_BYTES)->min;
}
```

Those same frame counts nest on the buffer, four periods filling the ring and an interrupt firing at each period boundary, one period holding period_size frames and one frame holding a sample per channel:

```
    Audio ring buffer (buffer_size frames, periods = 4)
    ───────────────────────────────────────────────────

    ┌────────────┬────────────┬────────────┬────────────┐
    │  period 0  │  period 1  │  period 2  │  period 3  │
    └────────────┴─────▲──────┴────────────┴────────────┘
                       │ IRQ at each period boundary
          |<───────── buffer_size frames ──────────>|

    one period
    ──────────
    ┌────┬────┬────┬─────┬────┐    period_size frames
    │ f0 │ f1 │ f2 │ ... │ fN │
    └─┬──┴────┴────┴─────┴────┘
      │ one frame = channels x one sample
      ▼
    ┌──────────────┬──────────────┐   stereo, S24_LE
    │  L sample    │  R sample    │
    │ ┌──────────┐ │ ┌──────────┐ │
    │ │24 valid  │0│ │24 valid  │0│   32 physical bits each,
    │ │  bits    │ │ │  bits    │ │   8 padding bits per sample
    │ └──────────┘ │ └──────────┘ │
    └──────────────┴──────────────┘
      frame_bits = 2 x 32 = 64
```

### Masks hold enumerated values, intervals hold ranges

[`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) carries both parameter shapes in two arrays plus the request/change bookkeeping words. The [`masks`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) array covers the enumerated parameters and the [`intervals`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) array the ranged ones, while [`rmask`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) records which parameters the caller is asking to change and [`cmask`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) which ones the kernel actually narrowed:

```c
/* include/uapi/sound/asound.h:408 */
struct snd_pcm_hw_params {
	unsigned int flags;
	struct snd_mask masks[SNDRV_PCM_HW_PARAM_LAST_MASK -
			       SNDRV_PCM_HW_PARAM_FIRST_MASK + 1];
	struct snd_mask mres[5];	/* reserved masks */
	struct snd_interval intervals[SNDRV_PCM_HW_PARAM_LAST_INTERVAL -
				        SNDRV_PCM_HW_PARAM_FIRST_INTERVAL + 1];
	struct snd_interval ires[9];	/* reserved intervals */
	unsigned int rmask;		/* W: requested masks */
	unsigned int cmask;		/* R: changed masks */
	unsigned int info;		/* R: Info flags for returned setup */
	unsigned int msbits;		/* R: used most significant bits (in sample bit-width) */
	unsigned int rate_num;		/* R: rate numerator */
	unsigned int rate_den;		/* R: rate denominator */
	snd_pcm_uframes_t fifo_size;	/* R: chip FIFO size in frames */
	unsigned char sync[16];		/* R: synchronization ID (perfect sync - one clock source) */
	unsigned char reserved[48];	/* reserved for future */
};
```

A [`struct snd_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L404) is a fixed-size bitmap, one bit per possible value of an enumerated parameter, so an access mask with both R/W modes set and an mmap mode set has three bits lit until refinement clears all but one:

```c
/* include/uapi/sound/asound.h:404 */
struct snd_mask {
	__u32 bits[(SNDRV_MASK_MAX+31)/32];
};
```

A [`struct snd_interval`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L394) is a `[min, max]` pair carrying four flags, [`openmin`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L394) and [`openmax`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L394) for exclusive endpoints, [`integer`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L394) when only whole values are legal, and [`empty`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L394) when the range has been contradicted:

```c
/* include/uapi/sound/asound.h:394 */
struct snd_interval {
	unsigned int min, max;
	unsigned int openmin:1,
		     openmax:1,
		     integer:1,
		     empty:1;
};
```

Both shapes pack into the container in two arrays, the masks holding the enumerated params and the intervals the ranged ones, with the rmask and cmask words tracking what was asked and what narrowed:

```
    struct snd_pcm_hw_params memory layout
    ─────────────────────────────────────────

    ┌──────────────────────────────────────────────────┐
    │ flags                                            │
    ├──────────────────────────────────────────────────┤
    │ masks[]   one snd_mask per enumerated param      │  access,
    │   snd_mask { bits[] } bitmap of allowed vals     │  format,
    │ mres[5]   reserved masks                         │  subformat
    ├──────────────────────────────────────────────────┤
    │ intervals[] one snd_interval per ranged param    │  rate,
    │   { min,max, openmin,openmax, integer,empty }    │  channels,
    │ ires[9]   reserved intervals                     │  sizes
    ├──────────────────────────────────────────────────┤
    │ rmask  W: params the caller asks to change       │
    │ cmask  R: params the kernel actually narrowed    │
    └──────────────────────────────────────────────────┘
```

### Refinement intersects each parameter against the driver's limits

A mask is narrowed by [`snd_mask_refine()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L153), which intersects the caller's mask with the driver's reference mask and reports `-EINVAL` if nothing remains, so two ends of a link agree only on the formats both list:

```c
/* include/sound/pcm_params.h:153 */
static inline int snd_mask_refine(struct snd_mask *mask,
				  const struct snd_mask *v)
{
	struct snd_mask old;
	snd_mask_copy(&old, mask);
	snd_mask_intersect(mask, v);
	if (snd_mask_empty(mask))
		return -EINVAL;
	return !snd_mask_eq(mask, &old);
}
```

An interval is narrowed by [`snd_interval_refine()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L626), which raises the low bound and lowers the high bound to the overlap of the two ranges, re-evaluates the open-endpoint flags, and forces integer behaviour when either side demands it, returning `-EINVAL` if the overlap is empty:

```c
/* sound/core/pcm_lib.c:626 */
int snd_interval_refine(struct snd_interval *i, const struct snd_interval *v)
{
	int changed = 0;
	if (snd_BUG_ON(snd_interval_empty(i)))
		return -EINVAL;
	if (i->min < v->min) {
		i->min = v->min;
		i->openmin = v->openmin;
		changed = 1;
	} else if (i->min == v->min && !i->openmin && v->openmin) {
		i->openmin = 1;
		changed = 1;
	}
	if (i->max > v->max) {
		i->max = v->max;
		i->openmax = v->openmax;
		changed = 1;
	} else if (i->max == v->max && !i->openmax && v->openmax) {
		i->openmax = 1;
		changed = 1;
	}
	...
	if (snd_interval_checkempty(i)) {
		snd_interval_none(i);
		return -EINVAL;
	}
	return changed;
}
```

The `HW_REFINE` ioctl reaches these through [`snd_pcm_hw_refine()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L551), which clears the result-only fields and then runs three passes, the mask pass, the interval pass, and a rules pass for parameters that depend on each other:

```c
/* sound/core/pcm_native.c:551 */
int snd_pcm_hw_refine(struct snd_pcm_substream *substream,
		      struct snd_pcm_hw_params *params)
{
	int err;

	params->info = 0;
	params->fifo_size = 0;
	...
	err = constrain_mask_params(substream, params);
	if (err < 0)
		return err;

	err = constrain_interval_params(substream, params);
	if (err < 0)
		return err;

	err = constrain_params_by_rules(substream, params);
	if (err < 0)
		return err;

	params->rmask = 0;

	return 0;
}
```

[`constrain_mask_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L289) shows the per-parameter loop. It walks every mask index from [`SNDRV_PCM_HW_PARAM_FIRST_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L359), skips any parameter the caller did not flag in [`rmask`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408), refines the rest against the driver's stored constraint mask with [`snd_mask_refine()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L153), and records a narrowing in [`cmask`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) so the caller learns which parameters moved:

```c
/* sound/core/pcm_native.c:289 */
static int constrain_mask_params(struct snd_pcm_substream *substream,
				 struct snd_pcm_hw_params *params)
{
	struct snd_pcm_hw_constraints *constrs =
					&substream->runtime->hw_constraints;
	struct snd_mask *m;
	unsigned int k;
	struct snd_mask old_mask __maybe_unused;
	int changed;

	for (k = SNDRV_PCM_HW_PARAM_FIRST_MASK; k <= SNDRV_PCM_HW_PARAM_LAST_MASK; k++) {
		m = hw_param_mask(params, k);
		if (snd_mask_empty(m))
			return -EINVAL;

		/* This parameter is not requested to change by a caller. */
		if (!(params->rmask & PARAM_MASK_BIT(k)))
			continue;
		...
		changed = snd_mask_refine(m, constrs_mask(constrs, k));
		if (changed < 0)
			return changed;
		if (changed == 0)
			continue;

		/* Set corresponding flag so that the caller gets it. */
		trace_hw_mask_param(substream, k, 0, &old_mask, m);
		params->cmask |= PARAM_MASK_BIT(k);
	}

	return 0;
}
```

### A driver injects its own constraints before refinement

The driver-supplied constraints the refinement passes intersect against are installed in the substream's open path. [`snd_pcm_hw_constraint_minmax()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1284) clamps an interval parameter, building a reference interval and calling [`snd_interval_refine()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L626) against the parameter's stored constraint:

```c
/* sound/core/pcm_lib.c:1284 */
int snd_pcm_hw_constraint_minmax(struct snd_pcm_runtime *runtime, snd_pcm_hw_param_t var,
				 unsigned int min, unsigned int max)
{
	struct snd_pcm_hw_constraints *constrs = &runtime->hw_constraints;
	struct snd_interval t;
	t.min = min;
	t.max = max;
	t.openmin = t.openmax = 0;
	t.integer = 0;
	return snd_interval_refine(constrs_interval(constrs, var), &t);
}
```

[`snd_pcm_hw_constraint_integer()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1265) sets the [`integer`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L394) flag on a parameter so its interval can never settle on a fractional value, the constraint a driver applies to the period and buffer sizes that must be whole frame counts. It does no interval arithmetic of its own, it forwards the parameter's stored interval to [`snd_interval_setinteger()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L279), which raises the flag and reports whether it changed:

```c
/* sound/core/pcm_lib.c:1265 */
int snd_pcm_hw_constraint_integer(struct snd_pcm_runtime *runtime, snd_pcm_hw_param_t var)
{
	struct snd_pcm_hw_constraints *constrs = &runtime->hw_constraints;
	return snd_interval_setinteger(constrs_interval(constrs, var));
}
```

[`snd_pcm_hw_constraint_list()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1316) restricts a parameter to a discrete set supplied as a [`struct snd_pcm_hw_constraint_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L298), which a [`SNDRV_PCM_RATE_KNOT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L132) driver uses to publish its handful of clock-derived rates:

```c
/* sound/core/pcm_lib.c:1316 */
int snd_pcm_hw_constraint_list(struct snd_pcm_runtime *runtime,
			       unsigned int cond,
			       snd_pcm_hw_param_t var,
			       const struct snd_pcm_hw_constraint_list *l)
{
	return snd_pcm_hw_rule_add(runtime, cond, var,
				   snd_pcm_hw_rule_list, (void *)l,
				   var, -1);
}
```

### User space sets the parameters and reads them back

A client opens the PCM device, then issues [`SNDRV_PCM_IOCTL_HW_REFINE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L680) and [`SNDRV_PCM_IOCTL_HW_PARAMS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L681), both carrying a [`struct snd_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408). In alsa-lib the client builds that structure through `snd_pcm_hw_params_set_format`, `snd_pcm_hw_params_set_rate`, `snd_pcm_hw_params_set_channels`, and `snd_pcm_hw_params_set_access`, each of which sets one bit in the matching mask or pins one bound of the matching interval before the library issues the refine or params ioctl. The kernel narrows every flagged parameter against the driver constraints and, on `HW_PARAMS`, commits the settled values into [`struct snd_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L362). Kernel code that runs later (a DAI hw_params op, a DMA setup) reads the same structure back through the [`params_format()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L313), [`params_rate()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1019), [`params_channels()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1008), [`params_period_size()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1030), and [`params_buffer_size()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L1052) accessors, each returning the one value its mask or interval has collapsed to. [`params_format()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L313) reads the format mask, then the format helpers translate that token into the bit geometry the hardware programming needs:

```c
/* include/sound/pcm_params.h:313 */
static inline snd_pcm_format_t params_format(const struct snd_pcm_hw_params *p)
{
	return (__force snd_pcm_format_t)snd_mask_min(hw_param_mask_c(p,
		SNDRV_PCM_HW_PARAM_FORMAT));
}
```

[`snd_mask_min()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L45) returns the lowest set bit of the mask, which after refinement is the only bit, so the accessor yields the single negotiated format, and [`hw_param_mask_c()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L990) is the indexing helper that selects the format mask out of the [`masks`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L408) array:

```c
/* include/sound/pcm_params.h:45 */
static inline unsigned int snd_mask_min(const struct snd_mask *mask)
{
	int i;
	for (i = 0; i < SNDRV_MASK_SIZE; i++) {
		if (mask->bits[i])
			return __ffs(mask->bits[i]) + (i << 5);
	}
	return 0;
}
```

### A settled parameter has collapsed to a single value

The `params_*` accessors return the interval `min` or the lowest mask bit unconditionally, which is only the negotiated value once refinement has driven the parameter down to one possibility. The predicates that confirm that collapse are the membership and single-value tests on the raw containers. [`snd_mask_test()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L126) reports whether one enumerated value is still set in a mask, the bit-addressing primitive a caller uses to ask whether a given [`snd_pcm_format_t`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L180) survives in the format mask:

```c
/* include/sound/pcm_params.h:126 */
static inline int snd_mask_test(const struct snd_mask *mask, unsigned int val)
{
	return mask->bits[MASK_OFS(val)] & MASK_BIT(val);
}
```

On the interval side [`snd_interval_single()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L241) decides whether a range has pinned down to exactly one legal value, treating an adjacent `[n, n+1]` pair as single when one endpoint is open, and [`snd_interval_value()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L247) then yields that value, choosing `max` over `min` only in the open-low case so an exclusive lower bound still resolves to the surviving number:

```c
/* include/sound/pcm_params.h:241 */
static inline int snd_interval_single(const struct snd_interval *i)
{
	return (i->min == i->max || 
		(i->min + 1 == i->max && (i->openmin || i->openmax)));
}
```

```c
/* include/sound/pcm_params.h:247 */
static inline int snd_interval_value(const struct snd_interval *i)
{
	if (i->openmin && !i->openmax)
		return i->max;
	return i->min;
}
```

[`snd_pcm_hw_param_value()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_lib.c#L1597) is the shape-agnostic reader the core uses, it branches on whether the parameter index is a mask or an interval, requires the container to have already settled, and returns `-EINVAL` if it has not, so it is the safe counterpart to the unconditional `params_*` accessors. The mask path runs [`snd_mask_single()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L138) then [`snd_mask_value()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm_params.h#L210), the interval path the two predicates above, and either path can hand back the direction through `dir`:

```c
/* sound/core/pcm_lib.c:1597 */
int snd_pcm_hw_param_value(const struct snd_pcm_hw_params *params,
			   snd_pcm_hw_param_t var, int *dir)
{
	if (hw_is_mask(var)) {
		const struct snd_mask *mask = hw_param_mask_c(params, var);
		if (!snd_mask_single(mask))
			return -EINVAL;
		if (dir)
			*dir = 0;
		return snd_mask_value(mask);
	}
	if (hw_is_interval(var)) {
		const struct snd_interval *i = hw_param_interval_c(params, var);
		if (!snd_interval_single(i))
			return -EINVAL;
		if (dir)
			*dir = i->openmin;
		return snd_interval_value(i);
	}
	return -EINVAL;
}
```
