# Digital Audio Interface (DAI)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A DAI (Digital Audio Interface) is the port through which an ASoC component moves a PCM stream, and the kernel represents it in two parts. The static descriptor [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) is what a codec or platform driver registers, and the runtime instance [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) is what [`snd_soc_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2706) allocates from it. The descriptor carries a [`playback`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) and a [`capture`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) [`struct snd_soc_pcm_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) capability set and one [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) function pointer struct, and the runtime instance carries a per-direction [`struct snd_soc_dai_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424) holding the active usage count and the DMA data pointer. The ASoC core never dereferences an op pointer directly. It calls a [`snd_soc_dai_*()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c) wrapper such as [`snd_soc_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L405), and each wrapper checks the op is present, invokes it, records progress with a per-substream mark, and annotates any error through [`soc_dai_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L13). The Realtek [`rt722-sdca`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c) codec serves as the worked example, exposing three DAIs over SoundWire and implementing only the [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1116), [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1226), [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1102), and [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1110) callbacks while every other op stays a no-op behind the wrapper guards.

```
                struct snd_soc_dai_driver   (const, shared)
                ┌──────────────────────────────────────┐
                │ name, id    ops ─▶ snd_soc_dai_ops   │
                │ playback / capture                   │
                └──────────────────────────────────────┘
                     ▲                          ▲
            .driver  │                          │  .driver
        struct snd_soc_dai          struct snd_soc_dai
        ┌──────────────────────┐    ┌──────────────────────┐
        │ component            │    │ component            │
        │ stream[2]            │    │ stream[2]            │
        │ active, dma_data     │    │ active, dma_data     │
        └──────────────────────┘    └──────────────────────┘
                one runtime instance per registration (mutable, per component)
```

## SUMMARY

ASoC describes one Digital Audio Interface with a static [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) that a codec or platform driver places in an array and registers through [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29). That descriptor names the interface, declares its [`playback`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) and [`capture`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) capabilities as two [`struct snd_soc_pcm_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) records (supported formats, rates, and channel counts), and points at one [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) function pointer struct. For each descriptor in the array, [`snd_soc_register_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2773) calls [`snd_soc_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2706), which allocates one runtime [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) with [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h) and links it onto the parent component's [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L223) under [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48).

The runtime instance carries the mutable per-direction state. The [`stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) array, indexed by [`SNDRV_PCM_STREAM_PLAYBACK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L167) and [`SNDRV_PCM_STREAM_CAPTURE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L168), holds the [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424) usage count [`snd_soc_dai_action()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L497) maintains and the [`dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424) pointer the transport stores. Every public entry point follows one shape, defined in [`soc-dai.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c), where the wrapper tests for the op, calls it, marks the substream on the teardown-bearing ops, and passes the result through [`soc_dai_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L13). The marks make error rollback exact, and [`snd_soc_dai_stream_active()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L529) reads the usage count the suspend and DAPM paths consult. The catalogue of every callback the function pointer struct can hold is documented separately as the DAI operations.

## SPECIFICATIONS

The [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) object is a Linux kernel software construct and has no standalone hardware specification. The serial-audio wire formats that its [`set_fmt`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L194) callback programs (I2S, DSP_A, DSP_B, Left-Justified, Right-Justified, PDM) are defined by their respective interface standards.

## LINUX KERNEL

### Descriptor and runtime types (soc-dai.h, soc.h)

- [`'\<struct snd_soc_dai_driver\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403): static description a codec/platform driver registers, one per DAI; holds the ops pointer and the playback/capture capability records
- [`'\<struct snd_soc_dai\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438): runtime instance allocated at registration; carries the back pointer to the driver and component, the per-direction stream state, and the function marks
- [`'\<struct snd_soc_dai_ops\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269): the function pointer struct grouping the probe, clocking, format, stream, mute, and PCM callbacks
- [`'\<struct snd_soc_dai_stream\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424): per-direction runtime state with the [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424) usage count, the [`dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424) pointer, and the bound [`widget`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424)
- [`'\<struct snd_soc_pcm_stream\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610): one direction's capability set (`formats`, `rates`, `channels_min`/`channels_max`, `sig_bits`)

### Registration and lifecycle (soc-core.c)

- [`'\<snd_soc_register_dai\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2706): allocate one runtime DAI, name it, and add it to the component's [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L223); asserts [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48)
- [`'\<snd_soc_register_dais\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2773): loop over the descriptor array, registering each entry and rolling back on failure
- [`'\<snd_soc_unregister_dais\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2758): drop the DAIs from the component list during cleanup
- [`'\<snd_soc_pcm_dai_probe\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L520) / [`'\<snd_soc_pcm_dai_remove\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L546): run the [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269)/[`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) ops in [`probe_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), set/clear the [`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) bit

### State, usage count, and accessors (soc-dai.c, soc-dai.h)

- [`'\<snd_soc_dai_action\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L497): add a signed delta to the per-direction [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424) count and to the component's [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L213) count
- [`'\<snd_soc_dai_active\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L508): sum the usage count across both directions
- [`'\<snd_soc_dai_stream_active\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L529): read one direction's usage count
- [`'\<snd_soc_dai_stream_valid\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L489): test whether a DAI supports a direction by checking [`channels_min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610)
- [`'\<snd_soc_dai_get_pcm_stream\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L473): select the playback or capture capability record by direction
- [`'\<snd_soc_dai_dma_data_set\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L506): store the per-direction [`dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424) pointer; reached through the [`snd_soc_dai_set_dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L505) and [`snd_soc_dai_get_dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L497) macros
- [`soc_dai_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L13) / [`soc_dai_mark_push()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L25): the error-annotation and substream-mark macros every wrapper uses

### Example wrappers (soc-dai.c)

- [`'\<snd_soc_dai_set_sysclk\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L38): set the MCLK/SYSCLK; falls back to [`snd_soc_component_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L78) when the DAI has no op
- [`'\<snd_soc_dai_hw_params\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L405) / [`'\<snd_soc_dai_hw_free\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L422): apply and release hardware parameters; push/pop the [`mark_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) mark
- [`'\<snd_soc_dai_startup\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L437) / [`'\<snd_soc_dai_shutdown\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L456): open and close the DAI for a substream; push/pop the [`mark_startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) mark
- [`'\<snd_soc_pcm_dai_trigger\>':'sound/soc/soc-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L618): drive start/stop/pause across all DAIs of a runtime, applying mute-on-trigger and the [`mark_trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) mark

### rt722-sdca worked example (codecs/rt722-sdca.c)

- [`'\<rt722_sdca_dai\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1253): the three [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) entries (`aif1`, `aif2`, `aif3`)
- [`'rt722_sdca_ops':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1246): the function pointer struct populating only four callbacks
- [`'\<rt722_sdca_pcm_hw_params\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1116): builds the SoundWire stream config and calls [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117)
- [`'\<rt722_sdca_pcm_hw_free\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1226): tears the slave out of the stream with [`sdw_stream_remove_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228)
- [`'\<rt722_sdca_set_sdw_stream\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1102): the [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op storing the SoundWire stream handle as [`dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424)

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst): the Digital Audio Interface concept and the AC97, I2S, and PCM families
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): codec component guide covering the DAI driver and its ops
- [`Documentation/sound/soc/clocking.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/clocking.rst): the MCLK/BCLK/LRCLK relationships the clocking ops configure
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle the rt722-sdca DAI joins from its hw_params op

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) layer](https://www.kernel.org/doc/html/latest/sound/soc/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A DAI is registered with its component, found by the binder, and driven through the [`soc-dai.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c) wrapper set. A codec or platform driver writes a const [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) array, and the core builds one runtime [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) per entry.

| Step | Function | Effect |
|------|----------|--------|
| register array | [`snd_soc_register_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2773) | loop the descriptor array, register each entry |
| register one | [`snd_soc_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2706) | allocate a runtime DAI, link onto [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L223) |
| probe | [`snd_soc_pcm_dai_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L520) | run the [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op, set the [`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) bit |
| count streams | [`snd_soc_dai_action()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L497) | adjust per-direction and component [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424) |
| read use count | [`snd_soc_dai_stream_active()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L529) | return one direction's [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424) |
| store DMA handle | [`snd_soc_dai_dma_data_set()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L506) | write the per-direction [`dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424) |
| unregister | [`snd_soc_unregister_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2758) | unlink the DAIs at component teardown |

## DETAILS

### The descriptor and the runtime instance

A codec driver writes one [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) per interface. The descriptor is static and shared across every card that instantiates the codec, so it holds only immutable description, the name and id, the playback and capture capability records, the symmetry flags, and the pointer to the function pointer struct:

```c
/* include/sound/soc-dai.h:403 */
struct snd_soc_dai_driver {
	/* DAI description */
	const char *name;
	unsigned int id;
	unsigned int base;
	struct snd_soc_dobj dobj;
	const struct of_phandle_args *dai_args;

	/* ops */
	const struct snd_soc_dai_ops *ops;
	const struct snd_soc_cdai_ops *cops;

	/* DAI capabilities */
	struct snd_soc_pcm_stream capture;
	struct snd_soc_pcm_stream playback;
	unsigned int symmetric_rate:1;
	unsigned int symmetric_channels:1;
	unsigned int symmetric_sample_bits:1;
};
```

Each capability record is a [`struct snd_soc_pcm_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) that states what the direction can carry, and the core intersects the codec record with the CPU DAI record to compute the hardware constraints a userspace client sees:

```c
/* include/sound/soc.h:610 */
struct snd_soc_pcm_stream {
	const char *stream_name;
	u64 formats;			/* SNDRV_PCM_FMTBIT_* */
	u32 subformats;			/* for S32_LE format, SNDRV_PCM_SUBFMTBIT_* */
	unsigned int rates;		/* SNDRV_PCM_RATE_* */
	unsigned int rate_min;		/* min rate */
	unsigned int rate_max;		/* max rate */
	unsigned int channels_min;	/* min channels */
	unsigned int channels_max;	/* max channels */
	unsigned int sig_bits;		/* number of bits of content */
};
```

The runtime [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) is the per-instance object. It points back at its descriptor and parent component, sits on the component's DAI list, and keeps the mutable state, the per-direction [`stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) array, the function marks, and the [`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) bit:

```c
/* include/sound/soc-dai.h:438 */
struct snd_soc_dai {
	const char *name;
	int id;
	struct device *dev;

	/* driver ops */
	struct snd_soc_dai_driver *driver;

	/* DAI runtime info */
	struct snd_soc_dai_stream stream[SNDRV_PCM_STREAM_LAST + 1];

	/* Symmetry data - only valid if symmetry is being enforced */
	unsigned int symmetric_rate;
	unsigned int symmetric_channels;
	unsigned int symmetric_sample_bits;

	/* parent platform/codec */
	struct snd_soc_component *component;

	struct list_head list;

	/* function mark */
	struct snd_pcm_substream *mark_startup;
	struct snd_pcm_substream *mark_hw_params;
	struct snd_pcm_substream *mark_trigger;
	struct snd_compr_stream  *mark_compr_startup;

	/* bit field */
	unsigned int probed:1;

	/* DAI private data */
	void *priv;
};
```

The [`stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) array is indexed by [`SNDRV_PCM_STREAM_PLAYBACK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L167) and [`SNDRV_PCM_STREAM_CAPTURE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L168), and each element is a [`struct snd_soc_dai_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424) that records the usage count, the DMA data pointer the transport stores, and the DAPM widget the DAI feeds:

```c
/* include/sound/soc-dai.h:424 */
struct snd_soc_dai_stream {
	struct snd_soc_dapm_widget *widget;

	unsigned int active;	/* usage count */
	unsigned int tdm_mask;	/* CODEC TDM slot masks and params (for fixup) */

	void *dma_data;		/* DAI DMA data */
};
```

The descriptor's [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) and capability fields point at [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) and [`struct snd_soc_pcm_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610), and each runtime [`stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) slot points at one [`struct snd_soc_dai_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424). The catalogue of every op the function pointer struct can hold is documented separately as the DAI operations.

```
    snd_soc_dai_driver          static, shared by every card
       ops                 ─▶  snd_soc_dai_ops  (probe, hw_params, ...)
       playback / capture  ─▶  snd_soc_pcm_stream
            │  snd_soc_register_dai()
            ▼
    snd_soc_dai                 runtime, one per DAI
       driver, component
       stream[PLAYBACK]    ─▶  snd_soc_dai_stream { active, dma_data, widget }
       stream[CAPTURE]     ─▶  snd_soc_dai_stream { active, dma_data, widget }
```

```
                  static descriptor        runtime instance
                  snd_soc_dai_driver       snd_soc_dai
                  (const, shared)          (devm_kzalloc, per DAI)
      ──────────  ───────────────────────  ──────────────────────────
      identity    name, id                 name, id  (copied)
      callbacks   ops ─▶ snd_soc_dai_ops   reached via .driver
      capability  playback / capture       read via .driver
      binding     (none)                   component, list node
      live state  (none)                   stream[2]: active, dma_data
      progress    (none)                   mark_*, probed

      link:  snd_soc_dai.driver ─▶ snd_soc_dai_driver
```

### Registration allocates the runtime DAI

A component registers its DAIs through [`snd_soc_register_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2773), which walks the descriptor array and registers each entry, unwinding the whole set if any one fails:

```c
/* sound/soc/soc-core.c:2773 */
static int snd_soc_register_dais(struct snd_soc_component *component,
				 struct snd_soc_dai_driver *dai_drv,
				 size_t count)
{
	struct snd_soc_dai *dai;
	unsigned int i;
	int ret;

	for (i = 0; i < count; i++) {
		dai = snd_soc_register_dai(component, dai_drv + i, count == 1 &&
					   component->driver->legacy_dai_naming);
		if (dai == NULL) {
			ret = -ENOMEM;
			goto err;
		}
	}

	return 0;

err:
	snd_soc_unregister_dais(component);

	return ret;
}
```

[`snd_soc_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2706) is where the runtime object comes into existence. It allocates the [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) with [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h) tied to the component device, names it (the multi-name format unless the component requested legacy naming), links it onto [`component->dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L223), and bumps [`component->num_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L224), all while holding [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48):

```c
/* sound/soc/soc-core.c:2706 */
struct snd_soc_dai *snd_soc_register_dai(struct snd_soc_component *component,
					 struct snd_soc_dai_driver *dai_drv,
					 bool legacy_dai_naming)
{
	struct device *dev = component->dev;
	struct snd_soc_dai *dai;

	lockdep_assert_held(&client_mutex);

	dai = devm_kzalloc(dev, sizeof(*dai), GFP_KERNEL);
	if (dai == NULL)
		return NULL;
	...
	dai->component = component;
	dai->dev = dev;
	dai->driver = dai_drv;

	/* see for_each_component_dais */
	list_add_tail(&dai->list, &component->dai_list);
	component->num_dai++;

	dev_dbg(dev, "ASoC: Registered DAI '%s'\n", dai->name);
	return dai;
}
```

Because the allocation is device-managed, there is no explicit free for the runtime DAI. According to the comment on [`snd_soc_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2706), "These DAIs's widgets will be freed in the card cleanup and the DAIs will be freed in the component cleanup", so the DAI lives exactly as long as its component and [`snd_soc_unregister_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2758) only unlinks them from the list during teardown.

### Probing and removing the DAIs of a runtime

Registration only links a DAI onto its component. The DAI's own [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op runs later, once the DAI is bound into a [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143), and [`snd_soc_pcm_dai_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L520) is the wrapper that drives it across every DAI of that runtime. It honors the [`probe_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) field so a DAI can ask to be probed before or after the rest, skips any DAI already carrying the [`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) bit, calls the op only when the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) struct supplies one, and sets the [`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) bit so the matching remove pass knows this DAI ran its setup:

```c
/* sound/soc/soc-dai.c:520 */
int snd_soc_pcm_dai_probe(struct snd_soc_pcm_runtime *rtd, int order)
{
	struct snd_soc_dai *dai;
	int i;

	for_each_rtd_dais(rtd, i, dai) {
		if (dai->probed)
			continue;

		if (dai->driver->ops) {
			if (dai->driver->ops->probe_order != order)
				continue;

			if (dai->driver->ops->probe) {
				int ret = dai->driver->ops->probe(dai);

				if (ret < 0)
					return soc_dai_ret(dai, ret);
			}
		}
		dai->probed = 1;
	}

	return 0;
}
```

[`snd_soc_pcm_dai_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L546) is the mirror image. It walks the same DAIs in the matching [`remove_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269), runs the [`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op only on a DAI whose [`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) bit is set, and clears the bit. Unlike probe, it does not stop on the first error. It keeps the last non-zero return so every probed DAI still gets torn down:

```c
/* sound/soc/soc-dai.c:546 */
int snd_soc_pcm_dai_remove(struct snd_soc_pcm_runtime *rtd, int order)
{
	struct snd_soc_dai *dai;
	int i, r, ret = 0;

	for_each_rtd_dais(rtd, i, dai) {
		if (!dai->probed)
			continue;

		if (dai->driver->ops) {
			if (dai->driver->ops->remove_order != order)
				continue;

			if (dai->driver->ops->remove) {
				r = dai->driver->ops->remove(dai);
				if (r < 0)
					ret = r; /* use last error */
			}
		}
		dai->probed = 0;
	}

	return ret;
}
```

The [`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) bit is the runtime instance's own record that its lifecycle op has run, the same role the per-substream marks play for the streaming ops below.

### The wrapper shape and the rollback marks

The ASoC core reaches a DAI op only through a wrapper in [`soc-dai.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c), and the wrappers share one shape. Two macros at the top of the file carry the boilerplate, [`soc_dai_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L13) for error annotation and [`soc_dai_mark_push()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L25) for the per-substream marks:

```c
/* sound/soc/soc-dai.c:13 */
#define soc_dai_ret(dai, ret) _soc_dai_ret(dai, __func__, ret)
static inline int _soc_dai_ret(const struct snd_soc_dai *dai,
			       const char *func, int ret)
{
	return snd_soc_ret(dai->dev, ret,
			   "at %s() on %s\n", func, dai->name);
}

#define soc_dai_mark_push(dai, substream, tgt)	((dai)->mark_##tgt = substream)
#define soc_dai_mark_pop(dai, tgt)	((dai)->mark_##tgt = NULL)
#define soc_dai_mark_match(dai, substream, tgt)	((dai)->mark_##tgt == substream)
```

[`snd_soc_dai_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L405) shows the PCM variant, where the wrapper records the substream in the matching mark after a successful call so the teardown path can find it:

```c
/* sound/soc/soc-dai.c:405 */
int snd_soc_dai_hw_params(struct snd_soc_dai *dai,
			  struct snd_pcm_substream *substream,
			  struct snd_pcm_hw_params *params)
{
	int ret = 0;

	if (dai->driver->ops &&
	    dai->driver->ops->hw_params)
		ret = dai->driver->ops->hw_params(substream, params, dai);

	/* mark substream if succeeded */
	if (ret == 0)
		soc_dai_mark_push(dai, substream, hw_params);

	return soc_dai_ret(dai, ret);
}
```

The marks exist so an error during multi-DAI bring-up tears down only the DAIs that actually ran their setup op. [`snd_soc_dai_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L422) takes a `rollback` argument, and when it is set the function returns early for any DAI whose [`mark_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) does not match the substream being unwound:

```c
/* sound/soc/soc-dai.c:422 */
void snd_soc_dai_hw_free(struct snd_soc_dai *dai,
			 struct snd_pcm_substream *substream,
			 int rollback)
{
	if (rollback && !soc_dai_mark_match(dai, substream, hw_params))
		return;

	if (dai->driver->ops &&
	    dai->driver->ops->hw_free)
		dai->driver->ops->hw_free(substream, dai);

	/* remove marked substream */
	soc_dai_mark_pop(dai, hw_params);
}
```

The streaming-lifecycle pair follows the same contract one stage earlier. [`snd_soc_dai_startup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L437) opens the DAI for a substream when the PCM is first opened. It returns success straight away for a direction the DAI does not support, calls the [`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op only when one is present, and pushes the [`mark_startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) mark after a clean call:

```c
/* sound/soc/soc-dai.c:437 */
int snd_soc_dai_startup(struct snd_soc_dai *dai,
			struct snd_pcm_substream *substream)
{
	int ret = 0;

	if (!snd_soc_dai_stream_valid(dai, substream->stream))
		return 0;

	if (dai->driver->ops &&
	    dai->driver->ops->startup)
		ret = dai->driver->ops->startup(substream, dai);

	/* mark substream if succeeded */
	if (ret == 0)
		soc_dai_mark_push(dai, substream, startup);

	return soc_dai_ret(dai, ret);
}
```

[`snd_soc_dai_shutdown()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L456) closes the DAI again and is the teardown half that reads the mark. It skips an unsupported direction, returns early under `rollback` for any DAI whose [`mark_startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) does not match the substream being unwound, runs the [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op, and pops the mark, so a startup that never ran is never paired with a shutdown:

```c
/* sound/soc/soc-dai.c:456 */
void snd_soc_dai_shutdown(struct snd_soc_dai *dai,
			  struct snd_pcm_substream *substream,
			  int rollback)
{
	if (!snd_soc_dai_stream_valid(dai, substream->stream))
		return;

	if (rollback && !soc_dai_mark_match(dai, substream, startup))
		return;

	if (dai->driver->ops &&
	    dai->driver->ops->shutdown)
		dai->driver->ops->shutdown(substream, dai);

	/* remove marked substream */
	soc_dai_mark_pop(dai, startup);
}
```

Not every wrapper carries a mark. [`snd_soc_dai_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L38) programs the DAI master (MCLK) or system (SYSCLK) clock and is a configuration call with nothing to roll back, so it runs the [`set_sysclk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op when present and otherwise falls through to [`snd_soc_component_set_sysclk()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L78), letting the parent component answer for a DAI that has no clocking op of its own:

```c
/* sound/soc/soc-dai.c:38 */
int snd_soc_dai_set_sysclk(struct snd_soc_dai *dai, int clk_id,
			   unsigned int freq, int dir)
{
	int ret;

	if (dai->driver->ops &&
	    dai->driver->ops->set_sysclk)
		ret = dai->driver->ops->set_sysclk(dai, clk_id, freq, dir);
	else
		ret = snd_soc_component_set_sysclk(dai->component, clk_id, 0,
						   freq, dir);

	return soc_dai_ret(dai, ret);
}
```

[`snd_soc_dai_stream_valid()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L489) reads the capability record for the direction and treats a non-zero [`channels_min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L610) as proof the DAI supports it, which is how a wrapper skips a direction a DAI does not implement:

```c
/* sound/soc/soc-dai.c:489 */
bool snd_soc_dai_stream_valid(const struct snd_soc_dai *dai, int dir)
{
	const struct snd_soc_pcm_stream *stream = snd_soc_dai_get_pcm_stream(dai, dir);

	/* If the codec specifies any channels at all, it supports the stream */
	return stream->channels_min;
}
```

Each of the three setup ops writes its mark on success and the matching teardown consults that mark under rollback, the inner box showing the push, the skip, and the pop on one DAI:

```
    Per-substream marks make multi-DAI rollback exact
    ─────────────────────────────────────────────────
    (setup pushes the mark on success; teardown under
     rollback skips any DAI whose mark does not match)

    setup op (on success)         teardown op (under rollback)
    ─────────────────────────     ───────────────────────────
    startup   ─▶ mark_startup     shutdown skips if
                                   mark_startup  != substream
    hw_params ─▶ mark_hw_params   hw_free  skips if
                                   mark_hw_params != substream
    trigger   ─▶ mark_trigger     stop grp skips if
                                   mark_trigger  != substream

    per markable op on one struct snd_soc_dai:
    ┌────────────────────────────────────────┐
    │ op ok  ─▶  mark_X = substream   (push) │
    │ rollback & mark_X != substream ─▶ skip │
    │ teardown ok ─▶ mark_X = NULL    (pop)  │
    └────────────────────────────────────────┘
```

### Trigger ordering across the DAIs of a runtime

[`snd_soc_pcm_dai_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L618) drives every DAI of a runtime through one command. The start group (START, RESUME, PAUSE_RELEASE) iterates forward, runs the per-DAI op, optionally unmutes when the DAI controls mute at trigger, and pushes the [`mark_trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) mark, while the stop group (STOP, SUSPEND, PAUSE_PUSH) mutes first, honors the rollback mark, runs the op, and pops the mark:

```c
/* sound/soc/soc-dai.c:618 */
int snd_soc_pcm_dai_trigger(struct snd_pcm_substream *substream,
			    int cmd, int rollback)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_soc_dai *dai;
	int i, r, ret = 0;

	switch (cmd) {
	case SNDRV_PCM_TRIGGER_START:
	case SNDRV_PCM_TRIGGER_RESUME:
	case SNDRV_PCM_TRIGGER_PAUSE_RELEASE:
		for_each_rtd_dais(rtd, i, dai) {
			ret = soc_dai_trigger(dai, substream, cmd);
			if (ret < 0)
				break;

			if (snd_soc_dai_mute_is_ctrled_at_trigger(dai))
				snd_soc_dai_digital_mute(dai, 0, substream->stream);

			soc_dai_mark_push(dai, substream, trigger);
		}
		break;
	case SNDRV_PCM_TRIGGER_STOP:
	case SNDRV_PCM_TRIGGER_SUSPEND:
	case SNDRV_PCM_TRIGGER_PAUSE_PUSH:
		for_each_rtd_dais(rtd, i, dai) {
			if (rollback && !soc_dai_mark_match(dai, substream, trigger))
				continue;

			if (snd_soc_dai_mute_is_ctrled_at_trigger(dai))
				snd_soc_dai_digital_mute(dai, 1, substream->stream);

			r = soc_dai_trigger(dai, substream, cmd);
			if (r < 0)
				ret = r; /* use last ret */
			soc_dai_mark_pop(dai, trigger);
		}
	}

	return ret;
}
```

The switch splits into the two columns drawn here, the start group triggering then unmuting and pushing the mark, the stop group muting and skipping unmarked DAIs before it triggers and pops:

```
    snd_soc_pcm_dai_trigger: two command groups over the rtd DAIs
    ────────────────────────────────────────────────────────────

    START / RESUME / PAUSE_RELEASE   (start group, for_each_rtd_dais)
       for each DAI:
          soc_dai_trigger(cmd)  ─▶  unmute (if mute@trigger)
                                ─▶  push mark_trigger

    STOP / SUSPEND / PAUSE_PUSH      (stop group, for_each_rtd_dais)
       for each DAI:
          rollback & mark_trigger != substream ─▶ skip this DAI
          mute (if mute@trigger)  ─▶  soc_dai_trigger(cmd)
                                  ─▶  pop mark_trigger

    start: trigger then unmute     stop: mute then trigger
    start: stops on first error    stop: keeps last error, runs all
```

### Per-direction usage count

[`snd_soc_dai_action()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L497) maintains the usage count. It adds a signed delta to the per-direction [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424) field and to the parent component's [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L213) field in one step, so a single accounting point keeps both counts in sync:

```c
/* sound/soc/soc-dai.c:497 */
void snd_soc_dai_action(struct snd_soc_dai *dai,
			int stream, int action)
{
	/* see snd_soc_dai_stream_active() */
	dai->stream[stream].active	+= action;

	/* see snd_soc_component_active() */
	dai->component->active		+= action;
}
```

[`snd_soc_dai_stream_active()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L529) reads one direction's count, and [`snd_soc_dai_active()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L508) sums both, which the suspend path and DAPM use to decide whether a DAI is still carrying audio:

```c
/* include/sound/soc-dai.h:529 */
static inline unsigned int snd_soc_dai_stream_active(const struct snd_soc_dai *dai,
						     int stream)
{
	/* see snd_soc_dai_action() for setup */
	return dai->stream[stream].active;
}
```

Where [`snd_soc_dai_stream_active()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L529) is the per-direction inline accessor, [`snd_soc_dai_active()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L508) is its whole-DAI counterpart out in [`soc-dai.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c). It folds the count over every direction with [`for_each_pcm_streams()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L699), returning non-zero whenever the DAI is carrying audio in either direction, which is the form the suspend and DAPM paths read when they only need to know that a DAI is busy at all:

```c
/* sound/soc/soc-dai.c:508 */
int snd_soc_dai_active(const struct snd_soc_dai *dai)
{
	int stream, active;

	active = 0;
	for_each_pcm_streams(stream)
		active += dai->stream[stream].active;

	return active;
}
```

### Worked example: rt722-sdca DAIs over SoundWire

The Realtek RT722 is an SDCA codec reached over SoundWire, and it registers its DAIs under the [`soc_sdca_dev_rt722`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1090) component driver. Its [`rt722_sdca_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1253) array declares three interfaces, a headphone-playback and headset-capture pair on `aif1`, a speaker-playback on `aif2`, and a four-channel digital-microphone capture on `aif3`:

```c
/* sound/soc/codecs/rt722-sdca.c:1253 */
static struct snd_soc_dai_driver rt722_sdca_dai[] = {
	{
		.name = "rt722-sdca-aif1",
		.id = RT722_AIF1,
		.playback = {
			.stream_name = "DP1 Headphone Playback",
			.channels_min = 1,
			.channels_max = 2,
			.rates = RT722_STEREO_RATES,
			.formats = RT722_FORMATS,
		},
		.capture = {
			.stream_name = "DP2 Headset Capture",
			.channels_min = 1,
			.channels_max = 2,
			.rates = RT722_STEREO_RATES,
			.formats = RT722_FORMATS,
		},
		.ops = &rt722_sdca_ops,
	},
	...
	{
		.name = "rt722-sdca-aif3",
		.id = RT722_AIF3,
		.capture = {
			.stream_name = "DP6 DMic Capture",
			.channels_min = 1,
			.channels_max = 4,
			.rates = RT722_STEREO_RATES,
			.formats = RT722_FORMATS,
		},
		.ops = &rt722_sdca_ops,
	}
};
```

All three DAIs share one function pointer struct, and it sets only four callbacks. Every other op stays NULL and its wrapper returns success or `-ENOTSUPP` without any code in the codec:

```c
/* sound/soc/codecs/rt722-sdca.c:1246 */
static const struct snd_soc_dai_ops rt722_sdca_ops = {
	.hw_params	= rt722_sdca_pcm_hw_params,
	.hw_free	= rt722_sdca_pcm_hw_free,
	.set_stream	= rt722_sdca_set_sdw_stream,
	.shutdown	= rt722_sdca_shutdown,
};
```

The [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op stores the SoundWire stream handle the machine layer passes, using [`snd_soc_dai_dma_data_set()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L506) to keep it in the per-direction [`dma_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L424) slot, and the [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op clears it:

```c
/* sound/soc/codecs/rt722-sdca.c:1102 */
static int rt722_sdca_set_sdw_stream(struct snd_soc_dai *dai, void *sdw_stream,
				int direction)
{
	snd_soc_dai_dma_data_set(dai, direction, sdw_stream);

	return 0;
}

static void rt722_sdca_shutdown(struct snd_pcm_substream *substream,
				struct snd_soc_dai *dai)
{
	snd_soc_dai_set_dma_data(dai, substream, NULL);
}
```

The [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op reads that stored handle back with [`snd_soc_dai_get_dma_data()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L497), translates the negotiated parameters into a [`struct sdw_stream_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L907), selects the SoundWire data port from the DAI id and direction, and joins the codec to the stream with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117):

```c
/* sound/soc/codecs/rt722-sdca.c:1116 */
static int rt722_sdca_pcm_hw_params(struct snd_pcm_substream *substream,
				struct snd_pcm_hw_params *params,
				struct snd_soc_dai *dai)
{
	struct snd_soc_component *component = dai->component;
	struct rt722_sdca_priv *rt722 = snd_soc_component_get_drvdata(component);
	struct sdw_stream_config stream_config;
	struct sdw_port_config port_config;
	enum sdw_data_direction direction;
	struct sdw_stream_runtime *sdw_stream;
	int retval, port, num_channels;
	unsigned int sampling_rate;

	sdw_stream = snd_soc_dai_get_dma_data(dai, substream);

	if (!sdw_stream)
		return -EINVAL;
	...
	stream_config.frame_rate = params_rate(params);
	stream_config.ch_count = params_channels(params);
	stream_config.bps = snd_pcm_format_width(params_format(params));
	stream_config.direction = direction;

	num_channels = params_channels(params);
	port_config.ch_mask = GENMASK(num_channels - 1, 0);
	port_config.num = port;

	retval = sdw_stream_add_slave(rt722->slave, &stream_config,
					&port_config, 1, sdw_stream);
	if (retval) {
		dev_err(dai->dev, "%s: Unable to configure port\n", __func__);
		return retval;
	}
	...
}
```

The [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op reverses exactly that step, removing the codec from the SoundWire stream with [`sdw_stream_remove_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228). The symmetry between the two ops follows the mark contract. The [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) wrapper records the substream in [`mark_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) only after [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117) returns success, so a later failure in the chain runs [`rt722_sdca_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1226) against this codec only if it had actually been added, which prevents a double [`sdw_stream_remove_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228).
