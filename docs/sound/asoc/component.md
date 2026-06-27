# ASoC component (snd_soc_component)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

An ASoC component is one functional audio block (a codec, a DSP platform, a CPU DAI driver) as the SoC sound layer sees it, and the kernel represents it in two parts. The static descriptor [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) is what a codec or platform driver registers, and the runtime instance [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) is what [`snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2932) allocates from it. The descriptor carries the function pointer struct of every callback the core may invoke plus the probe-order and behavior bit flags, and the runtime instance carries the binding state, the [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L213) open-stream use count, the [`io_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L229) that serializes register access, the [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L223) of [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) it owns, and the [`list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L217) node that places it on the global component_list. The Realtek [`rt5682`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c) codec serves as the worked example, an I2C device enumerated through ACPI on Intel platforms that registers one [`rt5682_soc_component_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L3066) descriptor and lets [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) build one component carrying two DAIs.

```
    struct snd_soc_component_driver   (const, shared)
    ┌──────────────────────────────────────────────────┐
    │ name, controls, dapm_widgets                     │
    │ probe / remove / suspend / resume                │
    │ read / write   pcm_construct / pcm_destruct      │
    │ open close hw_params trigger pointer ...         │
    │ probe_order   idle_bias_on   endianness          │
    └──────────────────────────────────────────────────┘
                          ▲  .driver
                          │
    struct snd_soc_component   (devm_kzalloc, per instance)
    ┌──────────────────────────────────────────────────┐
    │ active    io_mutex    suspended:1                │
    │ list ─────▶ component_list      (global)         │
    │ card_list ▶ card->component_dev_list             │
    │ dai_list ─▶ snd_soc_dai ─▶ snd_soc_dai ...       │
    └──────────────────────────────────────────────────┘
        one runtime component per registration; one driver
        may back many components across many cards
```

## SUMMARY

ASoC describes one functional audio block with a static [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) that a codec or platform driver registers through [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29). That descriptor holds the controls and DAPM tables added after probe, the function pointer struct of every callback the core may call, the [`probe_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L158) and [`remove_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L159) values, and the behavior bit flags [`idle_bias_on`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L179), [`suspend_bias_off`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L180), [`use_pmdown_time`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L181), [`endianness`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L191), and [`legacy_dai_naming`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L192). Registration runs in three steps. [`snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2932) allocates the runtime [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) with [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h), [`snd_soc_component_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2850) sets up the lists and the [`io_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L229), and [`snd_soc_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885) registers the DAIs, attaches a regmap when the driver supplies no [`read`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) or [`write`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback, and links the component onto the global component_list under [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48).

The descriptor is static and shared, so one [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) may back several runtime components when the same codec part appears on more than one card or bus. Each runtime [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) keeps its own mutable state, the [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L223) that [`snd_soc_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2706) links each DAI onto, and the function marks that make error rollback exact. The ASoC core never dereferences a callback pointer directly. It calls a [`snd_soc_component_*()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c) wrapper such as [`snd_soc_component_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L303), and each wrapper checks that the callback is present, invokes it, and annotates any error through [`soc_component_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L16). The register I/O wrappers and the open-stream use count are documented alongside the component I/O machinery, and the per-callback catalogue alongside the component operations.

## SPECIFICATIONS

The [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) object is a Linux kernel software construct and has no standalone hardware specification. A component's register I/O ultimately reaches a hardware bus (I2C, SPI, SoundWire, or memory-mapped registers), each defined by its own bus standard, and a codec component enumerated on an x86-64 platform is described to the kernel by an ACPI device with a `_HID` or `_CID` that the I2C or SPI bus glue matches.

## LINUX KERNEL

### Descriptor and runtime types (soc-component.h)

- [`'\<struct snd_soc_component_driver\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67): static description a codec/platform driver registers; holds the controls and DAPM tables, every callback pointer, the [`probe_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L158)/[`remove_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L159) values, and the behavior bit flags
- [`'\<struct snd_soc_component\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207): runtime instance allocated at registration; carries the back pointer to the driver, the [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L213) use count, the [`io_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L229), the [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L223), and the [`list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L217) and [`card_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L219) nodes
- [`'\<struct snd_soc_dai\>':'include/sound/soc-dai.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438): a runtime DAI the component owns, linked onto its [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L223)
- [`'\<enum snd_soc_bias_level\>':'include/sound/soc-dapm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L415): the power bias the [`set_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback drives, from `SND_SOC_BIAS_OFF` to `SND_SOC_BIAS_ON`

### Registration and lifecycle (soc-core.c, soc-devres.c)

- [`'\<snd_soc_component_initialize\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2850): allocate the DAPM context, initialize the five lists and the [`io_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L229), and store the [`driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L221) back pointer and the name
- [`'\<snd_soc_add_component\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885): register the DAIs, attach a regmap when no [`read`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67)/[`write`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback is set, and add the component to the global component_list under [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48)
- [`'\<snd_soc_register_component\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2932): [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h) the runtime component, then run [`snd_soc_component_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2850) and [`snd_soc_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885)
- [`'\<devm_snd_soc_register_component\>':'sound/soc/soc-devres.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29): the device-managed wrapper most codec drivers call, unregistering the component automatically when the device is removed
- [`'\<snd_soc_unregister_component_by_driver\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2959): tear down every component on a device that matches a given driver name, calling [`snd_soc_del_component_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2833) per component
- [`'\<snd_soc_del_component_unlocked\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2833): unregister the DAIs, unbind the card, and unlink the component from the global component_list
- [`'\<snd_soc_register_dai\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2706): allocate one runtime DAI and link it onto [`component->dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L223), bumping [`num_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L224)

### Lifecycle wrappers (soc-component.c)

- [`'\<snd_soc_component_probe\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L303): run the [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback once when the component binds to its card, called from [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602)
- [`'\<snd_soc_component_remove\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L313): run the [`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback at teardown
- [`'\<snd_soc_component_open\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L251) / [`'\<snd_soc_component_close\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L266): bracket a substream and push/pop the [`mark_open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L247) mark so rollback closes only a component whose open ran

### State and helpers (soc-component.h)

- [`'\<snd_soc_component_get_drvdata\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L356): return the codec driver's private data hung off the component device
- [`'\<snd_soc_component_to_dapm\>':'include/sound/soc-component.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L267): return the component's [`struct snd_soc_dapm_context`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L44)
- [`soc_component_ret()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L16) / [`soc_component_mark_push()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L48): the error-annotation and substream-mark macros every wrapper uses

### rt5682 worked example (codecs/rt5682.c, rt5682-i2c.c)

- [`'rt5682_soc_component_dev':'sound/soc/codecs/rt5682.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L3066): the [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) the codec registers, filling [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), [`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), [`suspend`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), [`resume`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), [`set_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), [`set_sysclk`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), [`set_pll`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), and [`set_jack`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67)
- [`'\<rt5682_probe\>':'sound/soc/codecs/rt5682.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L2928): the [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback reading [`snd_soc_component_get_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L356) and finishing setup through the [`struct snd_soc_dapm_context`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L44) from [`snd_soc_component_to_dapm()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L267)
- [`'rt5682_dai':'sound/soc/codecs/rt5682-i2c.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682-i2c.c#L78): the two [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) entries the component owns, [`rt5682-aif1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682-i2c.c#L80) and [`rt5682-aif2`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682-i2c.c#L99)
- [`'\<rt5682_i2c_probe\>':'sound/soc/codecs/rt5682-i2c.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682-i2c.c#L119): the I2C probe that calls [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29)

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the codec component guide covering the component driver and its callbacks
- [`Documentation/sound/soc/platform.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/platform.rst): the platform component guide for DMA and DSP back ends
- [`Documentation/sound/soc/overview.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/overview.rst): how components, DAIs, and the machine driver fit together
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): Dynamic Audio Power Management, which the component's bias-level and DAPM tables feed

## OTHER SOURCES

- [ALSA System on Chip (ASoC) layer](https://www.kernel.org/doc/html/latest/sound/soc/index.html)
- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

A component is registered, found, and torn down through a small helper set across [`soc-devres.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c) and [`soc-core.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c). A codec or platform driver fills a const [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) and a [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) array, hands them to [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29), and the core builds one runtime [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) carrying one runtime DAI per driver entry.

| Step | Function | Effect |
|------|----------|--------|
| register | [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) | record a devres release action, forward to the core register |
| allocate | [`snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2932) | [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h) the runtime component |
| initialize | [`snd_soc_component_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2850) | set up the DAPM context, the five lists, the [`io_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L229), and the name |
| add | [`snd_soc_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885) | register the DAIs, attach a regmap, link onto component_list |
| register one DAI | [`snd_soc_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2706) | allocate a runtime DAI, link onto [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L223) |
| probe | [`snd_soc_component_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L303) | run the driver [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) when the card binds |
| tear down | [`snd_soc_del_component_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2833) | unregister the DAIs, unbind the card, unlink from component_list |

## DETAILS

### The descriptor and the runtime instance

A codec or platform driver writes one [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) per functional block. The descriptor is static and shared across every card that instantiates the part, so it holds only immutable description, the controls and DAPM tables to add after probe, the callback pointers, the ordering integers, and the behavior bit flags:

```c
/* include/sound/soc-component.h:67 */
struct snd_soc_component_driver {
	const char *name;

	/* Default control and setup, added after probe() is run */
	const struct snd_kcontrol_new *controls;
	unsigned int num_controls;
	const struct snd_soc_dapm_widget *dapm_widgets;
	unsigned int num_dapm_widgets;
	const struct snd_soc_dapm_route *dapm_routes;
	unsigned int num_dapm_routes;

	int (*probe)(struct snd_soc_component *component);
	void (*remove)(struct snd_soc_component *component);
	int (*suspend)(struct snd_soc_component *component);
	int (*resume)(struct snd_soc_component *component);

	unsigned int (*read)(struct snd_soc_component *component,
			     unsigned int reg);
	int (*write)(struct snd_soc_component *component,
		     unsigned int reg, unsigned int val);

	/* pcm creation and destruction */
	int (*pcm_construct)(struct snd_soc_component *component,
			     struct snd_soc_pcm_runtime *rtd);
	void (*pcm_destruct)(struct snd_soc_component *component,
			     struct snd_pcm *pcm);
	...
	/* probe ordering - for components with runtime dependencies */
	int probe_order;
	int remove_order;
	...
	unsigned int module_get_upon_open:1;

	/* bits */
	unsigned int idle_bias_on:1;
	unsigned int suspend_bias_off:1;
	unsigned int use_pmdown_time:1; /* care pmdown_time at stop */
	...
	unsigned int endianness:1;
	unsigned int legacy_dai_naming:1;
	...
};
```

The full callback list (the PCM substream operations, the clocking and jack hooks, the DAPM notifiers) runs to dozens of pointers, and each is reached through a matching wrapper. The set of callbacks is documented separately as the component operations. The point here is the field grouping into identity and tables, callback pointers, ordering integers, and behavior bits, all const and all shared.

The runtime [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) is the per-instance object. It points back at its descriptor through [`driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L221), keeps the binding to its [`card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L211) and the list nodes that place it on the global component_list and the card's component list, counts open streams in [`active`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L213), serializes register access through [`io_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L229), owns its DAIs on [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L223), and records the function marks for exact rollback:

```c
/* include/sound/soc-component.h:207 */
struct snd_soc_component {
	const char *name;
	const char *name_prefix;
	struct device *dev;
	struct snd_soc_card *card;

	unsigned int active;

	unsigned int suspended:1; /* is in suspend PM state */

	struct list_head list;
	struct list_head card_aux_list; /* for auxiliary bound components */
	struct list_head card_list;

	const struct snd_soc_component_driver *driver;

	struct list_head dai_list;
	int num_dai;

	struct regmap *regmap;
	int val_bytes;

	struct mutex io_mutex;

	/* attached dynamic objects */
	struct list_head dobj_list;
	...
	struct snd_soc_dapm_context *dapm;

	/* machine specific init */
	int (*init)(struct snd_soc_component *component);

	/* function mark */
	void *mark_module;
	struct snd_pcm_substream *mark_open;
	struct snd_pcm_substream *mark_hw_params;
	struct snd_pcm_substream *mark_trigger;
	struct snd_compr_stream  *mark_compr_open;
	void *mark_pm;

	struct dentry *debugfs_root;
	const char *debugfs_prefix;
};
```

The [`list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L217) node places the component on the global component_list so the core can find every registered component, the [`card_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L219) node places it on the card it is bound to, and the [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L223) head anchors the DAIs that belong to this component, each a [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438).

Each node on [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L223) is a runtime [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438), the DAI counterpart of the component split. It carries a back pointer to its static [`driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L444) and to the owning [`component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L455), the per-direction [`stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L447) array, the [`list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L457) node that links it onto the component's [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L223), and a [`probed`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L466) bit that mirrors the component's mark scheme for exact rollback:

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
	...
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

The [`component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L455) back pointer reaches the component a DAI belongs to and, through it, the descriptor and the regmap, so the component is the owning object and the DAI is one of its children rather than a peer.

One descriptor callback whose value is itself a small enum is [`set_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), which the DAPM core invokes to move a component between power states. The target it is handed is an [`enum snd_soc_bias_level`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L415), a four-value ladder from fully off to fully on:

```c
/* include/sound/soc-dapm.h:415 */
enum snd_soc_bias_level {
	SND_SOC_BIAS_OFF = 0,
	SND_SOC_BIAS_STANDBY = 1,
	SND_SOC_BIAS_PREPARE = 2,
	SND_SOC_BIAS_ON = 3,
};
```

The component's [`idle_bias_on`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L179) and [`suspend_bias_off`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L180) flags, set on the descriptor, decide how far down this ladder DAPM may take the part when no stream is active, so the bias enum and the behavior bits are the descriptor's contract with the power model.

```
    enum snd_soc_bias_level: the four-rung power ladder
    ────────────────────────────────────────────────────

      value  name                    meaning
      ┌─────┬───────────────────────┬──────────────────────────┐
      │  3  │ SND_SOC_BIAS_ON       │ fully on, stream running │  ▲ powering
      ├─────┼───────────────────────┼──────────────────────────┤  │ up
      │  2  │ SND_SOC_BIAS_PREPARE  │ transitional, ramping    │  │
      ├─────┼───────────────────────┼──────────────────────────┤  │
      │  1  │ SND_SOC_BIAS_STANDBY  │ low power, ready to run  │  ▼ powering
      ├─────┼───────────────────────┼──────────────────────────┤    down
      │  0  │ SND_SOC_BIAS_OFF      │ fully off, no bias       │
      └─────┴───────────────────────┴──────────────────────────┘
        set_bias_level(component, level) drives one step at a time
        idle_bias_on holds at STANDBY (not OFF) when no stream runs
```

```
                  static descriptor               runtime instance
                  snd_soc_component_driver        snd_soc_component
                  (const, shared)                 (devm_kzalloc, per inst)
      ──────────  ──────────────────────────────  ─────────────────────────
      identity    name                            name, name_prefix, dev
      callbacks   probe ... delay (all ptrs)      reached via .driver
      controls    controls, dapm_widgets          added to .dapm at probe
      ordering    probe_order, remove_order       (none)
      flags       idle_bias_on, endianness, ...   (none)
      binding     (none)                           card, list, card_list
      live state  (none)                           active, suspended:1
      registers   (none)                           regmap, io_mutex
      children    (none)                           dai_list, num_dai
      progress    (none)                           mark_open, mark_module

      link:  snd_soc_component.driver ─▶ snd_soc_component_driver
```

```
    snd_soc_component_driver        static, shared by every card
       probe, read, open, ...  ─▶  callback pointers
       controls, dapm_widgets  ─▶  added to component->dapm at probe
            │  snd_soc_register_component()
            ▼
    snd_soc_component               runtime, one per instance
       driver, card
       list                    ─▶  component_list (global)
       card_list               ─▶  card->component_dev_list
       dai_list                ─▶  snd_soc_dai ─▶ snd_soc_dai
       active, io_mutex, regmap
```

### Registration runs in three steps

A codec calls [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29), which records a devres release action and then forwards to [`snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2932):

```c
/* sound/soc/soc-devres.c:29 */
int devm_snd_soc_register_component(struct device *dev,
			 const struct snd_soc_component_driver *cmpnt_drv,
			 struct snd_soc_dai_driver *dai_drv, int num_dai)
{
	const struct snd_soc_component_driver **ptr;
	int ret;

	ptr = devres_alloc(devm_component_release, sizeof(*ptr), GFP_KERNEL);
	if (!ptr)
		return -ENOMEM;

	ret = snd_soc_register_component(dev, cmpnt_drv, dai_drv, num_dai);
	if (ret == 0) {
		*ptr = cmpnt_drv;
		devres_add(dev, ptr);
	} else {
		devres_free(ptr);
	}

	return ret;
}
```

[`snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2932) allocates the runtime [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) with [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h) tied to the device, then runs the initialize and add steps in order:

```c
/* sound/soc/soc-core.c:2932 */
int snd_soc_register_component(struct device *dev,
			const struct snd_soc_component_driver *component_driver,
			struct snd_soc_dai_driver *dai_drv,
			int num_dai)
{
	struct snd_soc_component *component;
	int ret;

	component = devm_kzalloc(dev, sizeof(*component), GFP_KERNEL);
	if (!component)
		return -ENOMEM;

	ret = snd_soc_component_initialize(component, component_driver, dev);
	if (ret < 0)
		return ret;

	return snd_soc_add_component(component, dai_drv, num_dai);
}
```

[`snd_soc_component_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2850) is the first step. It allocates the DAPM context, initializes the [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L223), [`dobj_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L232), [`card_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L219), [`list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L217), and [`card_aux_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L218) heads, sets up the [`io_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L229), assigns a default name when none was set, and stores the [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L210) and [`driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L221) back pointer:

```c
/* sound/soc/soc-core.c:2850 */
int snd_soc_component_initialize(struct snd_soc_component *component,
				 const struct snd_soc_component_driver *driver,
				 struct device *dev)
{
	component->dapm = snd_soc_dapm_alloc(dev);
	if (!component->dapm)
		return -ENOMEM;

	INIT_LIST_HEAD(&component->dai_list);
	INIT_LIST_HEAD(&component->dobj_list);
	INIT_LIST_HEAD(&component->card_list);
	INIT_LIST_HEAD(&component->list);
	INIT_LIST_HEAD(&component->card_aux_list);
	mutex_init(&component->io_mutex);

	if (!component->name) {
		component->name = fmt_single_name(dev, NULL);
		if (!component->name) {
			dev_err(dev, "ASoC: Failed to allocate name\n");
			return -ENOMEM;
		}
	}

	component->dev		= dev;
	component->driver	= driver;
	...
	return 0;
}
```

[`snd_soc_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885) is the second step, run under [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48). It registers the DAIs from the descriptor array through [`snd_soc_register_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2773), attaches a regmap when the driver supplies neither [`write`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) nor [`read`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67), links the component onto the global component_list, and rebinds any card that was waiting on this component:

```c
/* sound/soc/soc-core.c:2885 */
int snd_soc_add_component(struct snd_soc_component *component,
			  struct snd_soc_dai_driver *dai_drv,
			  int num_dai)
{
	struct snd_soc_card *card, *c;
	int ret;
	int i;

	mutex_lock(&client_mutex);

	if (component->driver->endianness) {
		for (i = 0; i < num_dai; i++) {
			convert_endianness_formats(&dai_drv[i].playback);
			convert_endianness_formats(&dai_drv[i].capture);
		}
	}

	ret = snd_soc_register_dais(component, dai_drv, num_dai);
	if (ret < 0) {
		dev_err(component->dev, "ASoC: Failed to register DAIs: %d\n",
			ret);
		goto err_cleanup;
	}

	if (!component->driver->write && !component->driver->read) {
		if (!component->regmap)
			component->regmap = dev_get_regmap(component->dev,
							   NULL);
		if (component->regmap)
			snd_soc_component_setup_regmap(component);
	}

	/* see for_each_component */
	list_add(&component->list, &component_list);

	list_for_each_entry_safe(card, c, &unbind_card_list, list)
		snd_soc_rebind_card(card);

err_cleanup:
	if (ret < 0)
		snd_soc_del_component_unlocked(component);

	mutex_unlock(&client_mutex);
	return ret;
}
```

According to the comment "see for_each_component", the [`list_add()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h) onto component_list is what later iteration over all components walks. Each DAI is allocated and linked by [`snd_soc_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2706), which adds it to [`component->dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L223) and bumps [`component->num_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L224), so after registration the component owns a list of [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) instances.

[`snd_soc_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2706) is the per-DAI step underneath [`snd_soc_register_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2773). Holding [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48), it [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h)s one runtime [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) tied to the component's [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L210), names it, stores the [`component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L455) and [`driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L444) back pointers, then links it onto [`component->dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L223) and increments [`num_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L224):

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

Because the DAI is allocated with [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h) against the component's device, it is reclaimed by the same devres unwind that frees the component, which is why teardown only has to unlink the DAIs and never explicitly frees them.

```
    Registration ordering: what each step builds (top to bottom)
    ──────────────────────────────────────────────────────────────

    step 1  devm_snd_soc_register_component()
            └─ records a devres release action, forwards down

    step 2  snd_soc_register_component()
            └─ devm_kzalloc() the runtime snd_soc_component

    step 3  snd_soc_component_initialize()
            ├─ snd_soc_dapm_alloc()  ─▶ component->dapm
            ├─ INIT_LIST_HEAD x5     ─▶ dai_list, dobj_list,
            │                           card_list, list, card_aux_list
            ├─ mutex_init()          ─▶ io_mutex
            └─ store dev, driver back pointer

    step 4  snd_soc_add_component()   [under client_mutex]
            ├─ snd_soc_register_dais()
            │     per DAI: devm_kzalloc, link ─▶ component->dai_list,
            │              num_dai++
            ├─ attach regmap  (only if no read and no write callback)
            └─ list_add()            ─▶ component_list  (global)
```

### The wrapper shape every callback shares

The ASoC core reaches a component callback only through a wrapper in [`soc-component.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c), and the wrappers share one shape. A macro at the top of the file carries the error annotation, and three more carry the per-substream marks:

```c
/* sound/soc/soc-component.c:16 */
#define soc_component_ret(dai, ret) _soc_component_ret(dai, __func__, ret)
static inline int _soc_component_ret(struct snd_soc_component *component, const char *func, int ret)
{
	return snd_soc_ret(component->dev, ret,
			   "at %s() on %s\n", func, component->name);
}
...
/*
 * We might want to check substream by using list.
 * In such case, we can update these macros.
 */
#define soc_component_mark_push(component, substream, tgt)	((component)->mark_##tgt = substream)
#define soc_component_mark_pop(component, tgt)	((component)->mark_##tgt = NULL)
#define soc_component_mark_match(component, substream, tgt)	((component)->mark_##tgt == substream)
```

[`snd_soc_component_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L303) shows the lifecycle variant, where an absent callback is success:

```c
/* sound/soc/soc-component.c:303 */
int snd_soc_component_probe(struct snd_soc_component *component)
{
	int ret = 0;

	if (component->driver->probe)
		ret = component->driver->probe(component);

	return soc_component_ret(component, ret);
}
```

It is reached from [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602) during card bring-up, the single caller. Its teardown pair [`snd_soc_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L313) is the thinnest wrapper of all, calling the [`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback when the component leaves its card and returning nothing, since unbinding cannot fail:

```c
/* sound/soc/soc-component.c:313 */
void snd_soc_component_remove(struct snd_soc_component *component)
{
	if (component->driver->remove)
		component->driver->remove(component);
}
```

The matching pair of [`snd_soc_component_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L303) and [`snd_soc_component_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L313) brackets a component's bound lifetime on its card, one running the descriptor [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) and the other the descriptor [`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67). [`snd_soc_component_open()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L251) shows the PCM variant, where the wrapper records the substream in [`mark_open`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L247) after a successful call so the teardown path can tell which components actually opened:

```c
/* sound/soc/soc-component.c:251 */
int snd_soc_component_open(struct snd_soc_component *component,
			   struct snd_pcm_substream *substream)
{
	int ret = 0;

	if (component->driver->open)
		ret = component->driver->open(component, substream);

	/* mark substream if succeeded */
	if (ret == 0)
		soc_component_mark_push(component, substream, open);

	return soc_component_ret(component, ret);
}
```

[`snd_soc_component_close()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L266) consults that mark on a rollback, so during an error unwind it closes only a component whose open ran, then pops the mark:

```c
/* sound/soc/soc-component.c:266 */
int snd_soc_component_close(struct snd_soc_component *component,
			    struct snd_pcm_substream *substream,
			    int rollback)
{
	int ret = 0;

	if (rollback && !soc_component_mark_match(component, substream, open))
		return 0;

	if (component->driver->close)
		ret = component->driver->close(component, substream);

	/* remove marked substream */
	soc_component_mark_pop(component, open);

	return soc_component_ret(component, ret);
}
```

### Teardown unlinks the component

At unregistration, [`snd_soc_unregister_component_by_driver()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2959) walks the device's components and tears each down through [`snd_soc_del_component_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2833), which unregisters the DAIs, unbinds the card, and unlinks the component from the global component_list with [`list_del()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h). The by-driver entry point holds [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48) and loops, looking up one component at a time on the device that matches the driver name through [`snd_soc_lookup_component_nolocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L369) and deleting it, until none remain:

```c
/* sound/soc/soc-core.c:2959 */
void snd_soc_unregister_component_by_driver(struct device *dev,
					    const struct snd_soc_component_driver *component_driver)
{
	const char *driver_name = NULL;

	if (component_driver)
		driver_name = component_driver->name;

	mutex_lock(&client_mutex);
	while (1) {
		struct snd_soc_component *component = snd_soc_lookup_component_nolocked(dev, driver_name);

		if (!component)
			break;

		snd_soc_del_component_unlocked(component);
	}
	mutex_unlock(&client_mutex);
}
```

Matching by driver name rather than by device alone drops exactly the components a given driver created on a device that registered several distinct descriptors, leaving any others on the device intact. Each one it finds is handed to [`snd_soc_del_component_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2833):

```c
/* sound/soc/soc-core.c:2833 */
static void snd_soc_del_component_unlocked(struct snd_soc_component *component)
{
	struct snd_soc_card *card = component->card;
	bool instantiated;

	snd_soc_unregister_dais(component);

	if (card) {
		instantiated = card->instantiated;
		snd_soc_unbind_card(card);
		if (instantiated)
			list_add(&card->list, &unbind_card_list);
	}

	list_del(&component->list);
}
```

Because the runtime component was allocated with [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h), there is no explicit free. The structure is reclaimed when the device's devres unwinds, and the [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) release action calls the unregister path on the way down.

### Worked example: the rt5682 codec on an ACPI x86 platform

The Realtek RT5682 is an I2C codec enumerated through an ACPI device whose `_HID` the I2C bus glue matches to the driver, the [`'10EC5682':'sound/soc/codecs/rt5682-i2c.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682-i2c.c#L321) entry in [`rt5682_acpi_match`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682-i2c.c#L320), used on current Intel x86-64 ACPI SOF platforms. Its I2C probe [`rt5682_i2c_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682-i2c.c#L119) allocates the [`rt5682_priv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.h#L1431) private state, hangs it off the I2C client with [`i2c_set_clientdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/i2c.h), builds the I2C regmap, confirms the part by reading its device-ID register, then closes by registering one component carrying two DAIs:

```c
/* sound/soc/codecs/rt5682-i2c.c:119 */
static int rt5682_i2c_probe(struct i2c_client *i2c)
{
	struct rt5682_platform_data *pdata = dev_get_platdata(&i2c->dev);
	struct rt5682_priv *rt5682;
	int i, ret;
	unsigned int val;

	rt5682 = devm_kzalloc(&i2c->dev, sizeof(struct rt5682_priv),
		GFP_KERNEL);
	if (!rt5682)
		return -ENOMEM;

	i2c_set_clientdata(i2c, rt5682);
	...
	rt5682->regmap = devm_regmap_init_i2c(i2c, &rt5682_regmap);
	if (IS_ERR(rt5682->regmap)) {
		ret = PTR_ERR(rt5682->regmap);
		dev_err(&i2c->dev, "Failed to allocate register map: %d\n",
			ret);
		return ret;
	}
	...
	regmap_read(rt5682->regmap, RT5682_DEVICE_ID, &val);
	if (val != DEVICE_ID) {
		dev_err(&i2c->dev,
			"Device with ID register %x is not rt5682\n", val);
		return -ENODEV;
	}
	...
	return devm_snd_soc_register_component(&i2c->dev,
					       &rt5682_soc_component_dev,
					       rt5682_dai, ARRAY_SIZE(rt5682_dai));
}
```

The private state stored with [`i2c_set_clientdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/i2c.h) is later reached from inside callbacks through [`snd_soc_component_get_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L356), and the regmap built here is the one [`snd_soc_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885) picks up with [`dev_get_regmap()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h) because the descriptor supplies no [`read`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) or [`write`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67). The closing [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) is the single line that turns this codec device into an ASoC component:

```c
/* sound/soc/codecs/rt5682-i2c.c:293 */
	return devm_snd_soc_register_component(&i2c->dev,
					       &rt5682_soc_component_dev,
					       rt5682_dai, ARRAY_SIZE(rt5682_dai));
```

The descriptor [`rt5682_soc_component_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L3066) fills the lifecycle and power callbacks, the clock, jack, and bias hooks, and the control and DAPM tables, and sets [`use_pmdown_time`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L181) and [`endianness`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L191). It supplies no [`read`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) or [`write`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) callback, so [`snd_soc_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885) attaches the I2C regmap automatically:

```c
/* sound/soc/codecs/rt5682.c:3066 */
const struct snd_soc_component_driver rt5682_soc_component_dev = {
	.probe = rt5682_probe,
	.remove = rt5682_remove,
	.suspend = rt5682_suspend,
	.resume = rt5682_resume,
	.set_bias_level = rt5682_set_bias_level,
	.controls = rt5682_snd_controls,
	.num_controls = ARRAY_SIZE(rt5682_snd_controls),
	.dapm_widgets = rt5682_dapm_widgets,
	.num_dapm_widgets = ARRAY_SIZE(rt5682_dapm_widgets),
	.dapm_routes = rt5682_dapm_routes,
	.num_dapm_routes = ARRAY_SIZE(rt5682_dapm_routes),
	.set_sysclk = rt5682_set_component_sysclk,
	.set_pll = rt5682_set_component_pll,
	.set_jack = rt5682_set_jack_detect,
	.use_pmdown_time	= 1,
	.endianness		= 1,
};
```

When the card binds, [`snd_soc_component_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L303) calls [`rt5682_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L2928), which reads its private data back with [`snd_soc_component_get_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L356), takes the [`struct snd_soc_dapm_context`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L44) from [`snd_soc_component_to_dapm()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L267), and finishes per-instance setup against that DAPM context:

```c
/* sound/soc/codecs/rt5682.c:2928 */
static int rt5682_probe(struct snd_soc_component *component)
{
	struct rt5682_priv *rt5682 = snd_soc_component_get_drvdata(component);
	struct snd_soc_dapm_context *dapm = snd_soc_component_to_dapm(component);
	struct sdw_slave *slave;
	unsigned long time;

	rt5682->component = component;

	if (rt5682->is_sdw) {
		slave = rt5682->slave;
		time = wait_for_completion_timeout(
			&slave->initialization_complete,
			msecs_to_jiffies(RT5682_PROBE_TIMEOUT));
		if (!time) {
			dev_err(&slave->dev, "Initialization not complete, timed out\n");
			return -ETIMEDOUT;
		}
	}

	snd_soc_dapm_disable_pin(dapm, "MICBIAS");
	snd_soc_dapm_disable_pin(dapm, "Vref2");
	snd_soc_dapm_sync(dapm);
	return 0;
}
```

The two DAIs the component owns are declared in the [`rt5682_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682-i2c.c#L78) array passed to registration, and [`snd_soc_register_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2773) links each onto the component's [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L223), so by the time [`rt5682_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt5682.c#L2928) runs the component already carries its [`struct snd_soc_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L438) instances:

```c
/* sound/soc/codecs/rt5682-i2c.c:78 */
static struct snd_soc_dai_driver rt5682_dai[] = {
	{
		.name = "rt5682-aif1",
		.id = RT5682_AIF1,
		.playback = {
			.stream_name = "AIF1 Playback",
			.channels_min = 1,
			.channels_max = 2,
			.rates = RT5682_STEREO_RATES,
			.formats = RT5682_FORMATS,
		},
		.capture = {
			.stream_name = "AIF1 Capture",
			.channels_min = 1,
			.channels_max = 2,
			.rates = RT5682_STEREO_RATES,
			.formats = RT5682_FORMATS,
		},
		.ops = &rt5682_aif1_dai_ops,
	},
	{
		.name = "rt5682-aif2",
		.id = RT5682_AIF2,
		.capture = {
			.stream_name = "AIF2 Capture",
			.channels_min = 1,
			.channels_max = 2,
			.rates = RT5682_STEREO_RATES,
			.formats = RT5682_FORMATS,
		},
		.ops = &rt5682_aif2_dai_ops,
	},
};
```

Registration assembles these entries under the const descriptor, building one runtime component that points back at the descriptor, picks up the I2C regmap on its own, and carries the two DAIs on its dai_list as a playback-and-capture aif1 and a capture-only aif2:

```
    rt5682: one descriptor builds one component fanning out to two DAIs
    ──────────────────────────────────────────────────────────────────
    ACPI _HID "10EC5682" matched by the I2C glue; rt5682_i2c_probe()
    calls devm_snd_soc_register_component()

    rt5682_soc_component_dev
    (const snd_soc_component_driver)
    ┌─────────────────────────────────────┐
    │ probe remove suspend resume         │
    │ set_bias_level set_sysclk set_pll   │
    │ set_jack                            │
    │ controls, dapm_widgets, dapm_routes │
    │ use_pmdown_time=1  endianness=1     │
    │ (no read, no write callback)        │
    └────────────────────┬────────────────┘
                         │ builds one runtime instance
                         ▼
    ┌─────────────────────────────────────┐
    │ snd_soc_component                   │
    │   driver ─▶ rt5682_soc_component_dev│
    │   regmap ─▶ I2C regmap (auto)       │
    │   dai_list                          │
    └────────────────────┬────────────────┘
                         │ rt5682_dai[] (two entries)
              ┌──────────┴───────────┐
              ▼                      ▼
    ┌──────────────────┐   ┌──────────────────┐
    │ "rt5682-aif1"    │   │ "rt5682-aif2"    │
    │ playback+capture │   │ capture only     │
    └──────────────────┘   └──────────────────┘
```
