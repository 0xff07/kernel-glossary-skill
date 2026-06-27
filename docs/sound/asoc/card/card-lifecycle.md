# ASoC card lifecycle

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

An ASoC card is the top-level object that ties a machine driver's DAI links to the codec and platform components they reference, and the kernel drives it through four stages. A machine driver registers the [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) with [`snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2557), the core binds it in [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163), that bind runs the full instantiation sequence and sets [`instantiated`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), and teardown runs in reverse through [`snd_soc_unbind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2153) and [`soc_cleanup_card_resources()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2114). Two locks order the work. The file-static [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48) in [`soc-core.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c) guards the global component list and every bind and unbind, while [`card->mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), taken inside it by [`snd_soc_card_mutex_lock()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L21), serializes one card's instantiation against its later runtime operations. When a DAI link names a component that has not registered yet, [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602) returns `-EPROBE_DEFER`, the card is parked on [`unbind_card_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L50), and [`snd_soc_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885) rebinds it through [`snd_soc_rebind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2347) once the missing component appears.

```
    register                    instantiated card
    ┌───────────────────────┐   ┌─────────────────────────────────┐
    │ snd_soc_register_card │   │ snd_card_register done          │
    │  INIT_LIST_HEAD x9    │   │ instantiated = 1                │
    │  mutex_init mutex     │   │ rtd_list, component_dev_list    │
    │  mutex_init dapm/pcm  │   │ populated                       │
    └───────────┬───────────┘   └─────────────────────────────────┘
                │ under client_mutex              ▲
                ▼                                 │ snd_soc_bind_card
    ┌─────────────────────────┐                   │ under card->mutex
    │ all components present? │── yes ────────────┘
    └───────────┬─────────────┘
                │ no (-EPROBE_DEFER from soc_probe_component)
                ▼
    ┌─────────────────────────┐   component registers later
    │ park on unbind_card_list│◀──── snd_soc_add_component ──┐
    └───────────┬─────────────┘                              │
                │ snd_soc_rebind_card                        │
                └────────────────── retry bind ──────────────┘

    lock nesting:  client_mutex  ⊃  card->mutex  (bind/unbind hold both)
```

## SUMMARY

A machine driver fills one [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) with a name, an owner module, an array of DAI links in [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) sized by [`num_links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), and optional DAPM widgets, routes, and controls, then hands it to [`snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2557) or the device-managed wrapper [`devm_snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L65). Registration initialises the card's nine list heads and its three mutexes ([`mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), [`dapm_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), [`pcm_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972)), takes [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48), and calls [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163).

[`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) takes [`card->mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) through [`snd_soc_card_mutex_lock_root()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L16) and runs the instantiation sequence in one pass. It binds the auxiliary devices, adds one PCM runtime per DAI link onto [`rtd_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) with [`snd_soc_add_pcm_runtimes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1269), creates the ALSA sound card with [`snd_card_new()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L171), adds the card DAPM widgets, probes every component used by the links through [`soc_probe_link_components()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1742), probes the DAIs through [`soc_probe_link_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1707), adds the card controls and DAPM routes, and finishes by registering the device with [`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870) and setting [`instantiated`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) to 1. Any failure in that sequence jumps to a tail that calls [`soc_cleanup_card_resources()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2114), so a half-built card is always torn down before the lock drops.

Teardown is the mirror image. [`snd_soc_unregister_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2609) takes [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48), calls [`snd_soc_unbind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2153) which clears [`instantiated`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) and runs [`soc_cleanup_card_resources()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2114), then unlinks the card from the global card [`list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972). When a component named by a link has not registered at bind time, [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602) returns `-EPROBE_DEFER` up through [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163), and [`snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2557) parks the card on [`unbind_card_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L50) instead of failing. Each later [`snd_soc_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885) walks that list under [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48) and retries every waiting card through [`snd_soc_rebind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2347), so the card binds as soon as its last dependency registers.

## SPECIFICATIONS

The [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) object is a Linux kernel software construct and has no standalone hardware specification. The components it binds drive hardware described by their own interface standards (Intel High Definition Audio, SoundWire, I2S), and on an x86-64 ACPI platform the machine driver learns which codec to bind from the ACPI HID carried in a [`struct snd_soc_acpi_mach`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) passed as platform data.

## LINUX KERNEL

### The card object and its lock/list fields (soc.h)

- [`'\<struct snd_soc_card\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972): the top-level card; holds the DAI link array, the runtime and component lists, the three mutexes, and the [`instantiated`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) bit
- [`'mutex':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972): the per-card instantiation lock, taken by [`snd_soc_card_mutex_lock()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L21); serializes bind against runtime DAPM and control changes
- [`'dapm_mutex':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972): guards the DAPM graph (widgets, paths, power transitions)
- [`'pcm_mutex':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972): guards PCM open, close, and parameter operations
- [`'rtd_list':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972): the list of [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143), one per bound DAI link, walked by [`for_each_card_rtds`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1109)
- [`'component_dev_list':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972): the list of components probed onto this card, walked by [`for_each_card_components`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1120)
- [`'dai_link':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) / [`'num_links':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972): the predefined DAI link array the machine driver supplies and its count
- [`'instantiated':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972): the single bit that records whether the card is fully bound, read by [`snd_soc_card_is_instantiated()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1132)

### Registration and the device-managed wrapper

- [`'\<snd_soc_register_card\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2557): initialise the list heads and mutexes, then bind under [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48); parks the card on [`unbind_card_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L50) on `-EPROBE_DEFER`
- [`'\<devm_snd_soc_register_card\>':'sound/soc/soc-devres.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L65): the resource-managed form that registers a [`devm_card_release`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L57) action so the card unregisters when the platform device goes away
- [`'\<snd_soc_unregister_card\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2609): unbind under [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48) and unlink from the global card list

### Bind, instantiate, and the deferred-probe path (soc-core.c)

- [`'\<snd_soc_bind_card\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163): the full instantiation sequence run under [`card->mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972); on any error jumps to its cleanup tail
- [`'\<devm_snd_soc_bind_card\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2327): bind a card whose unregistration is device-managed, keeping the devres entry on `-EPROBE_DEFER`
- [`'\<snd_soc_rebind_card\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2347): retry a parked card and unlink it from [`unbind_card_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L50) once it binds
- [`'\<soc_probe_link_components\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1742): probe every component used by the DAI links, in [`probe_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L158)
- [`'\<soc_probe_component\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602): probe one component and add it to [`component_dev_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972); the source of `-EPROBE_DEFER` when a module is not yet ready
- [`'\<soc_probe_link_dais\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1707): run [`snd_soc_pcm_dai_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L520) for every runtime's DAIs
- [`'\<snd_soc_add_pcm_runtimes\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1269): add one [`struct snd_soc_pcm_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1143) per DAI link onto [`rtd_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972)
- [`'\<snd_soc_add_component\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885): register a component's DAIs, add it to the global component list, then walk [`unbind_card_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L50) and rebind waiting cards

### Teardown (soc-core.c)

- [`'\<snd_soc_unbind_card\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2153): clear [`instantiated`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), flush delayed work, and run [`soc_cleanup_card_resources()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2114), gated by [`snd_soc_card_is_instantiated()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1132)
- [`'\<soc_cleanup_card_resources\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2114): disconnect the ALSA card, remove DAIs and components, free the PCM runtimes, and free the [`snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80)
- [`'\<soc_remove_link_dais\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1694): run [`snd_soc_pcm_dai_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L546) for every runtime's DAIs in reverse order
- [`'\<snd_soc_flush_all_delayed_work\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L610): flush each runtime's [`delayed_work`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1170) before DAIs and widgets are removed

### The two locks and their helpers

- [`'client_mutex':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48): the file-static mutex guarding the global [`component_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L49), [`unbind_card_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L50), and every bind and unbind; asserted by [`lockdep_assert_held()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/lockdep.h) in the registration helpers
- [`'unbind_card_list':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L50): the list of cards waiting on a deferred component
- [`'\<snd_soc_card_mutex_lock\>':'include/sound/soc-card.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L21) / [`'\<snd_soc_card_mutex_unlock\>':'include/sound/soc-card.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L26): take and drop [`card->mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) at the `SND_SOC_CARD_CLASS_RUNTIME` lockdep subclass
- [`'\<snd_soc_card_mutex_lock_root\>':'include/sound/soc-card.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L16): take [`card->mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) at the `SND_SOC_CARD_CLASS_ROOT` subclass during bind, so lockdep distinguishes the bind-time hold from later nested runtime holds
- [`'\<enum snd_soc_card_subclass\>':'include/sound/soc-card.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L11): the two lockdep subclasses (`SND_SOC_CARD_CLASS_ROOT` = 0, `SND_SOC_CARD_CLASS_RUNTIME` = 1) for [`card->mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972)
- [`'\<snd_soc_card_is_instantiated\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1132): read the [`instantiated`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) bit, guarding teardown and runtime control paths against a card that never bound

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/machine.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/machine.rst): the machine driver and the [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) it registers
- [`Documentation/sound/soc/overview.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/overview.rst): how the card, DAI link, codec, and platform pieces fit together
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): the DAPM widget, route, and control graph that [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) builds during instantiation
- [`Documentation/driver-api/driver-model/driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/driver-model/driver.rst): the driver-model probe and `-EPROBE_DEFER` mechanism the rebind path mirrors for components

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) layer](https://www.kernel.org/doc/html/latest/sound/soc/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The card lifecycle turns on two locks with a fixed nesting order. [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48) is a single file-static [`struct mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mutex_types.h) defined at the top of [`soc-core.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c), and it is the outer lock. It protects the two file-static lists, the global [`component_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L49) every component registers onto and the [`unbind_card_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L50) of cards waiting on a deferred component, and it serializes the whole bind and unbind of any card so that a component registering or unregistering cannot race a card that is being assembled or torn down. The registration helpers assert it with [`lockdep_assert_held()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/lockdep.h) rather than take it themselves, which is why a caller such as [`snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2557) acquires it before calling into the bind path.

```
    static, file scope (sound/soc/soc-core.c)
    ┌───────────────────────────────────────────────────────────┐
    │  client_mutex            (L48)   outer lock               │
    │  component_list          (L49)   every registered comp    │
    │  unbind_card_list        (L50)   cards waiting on defer   │
    └───────────────────────────────────────────────────────────┘

    per card (struct snd_soc_card)
    ┌───────────────────────────────────────────────────────────┐
    │  mutex                 inner; ROOT subclass during bind   │
    │  dapm_mutex            DAPM graph                         │
    │  pcm_mutex             PCM open/close/params              │
    │  instantiated          set at end of bind                 │
    └───────────────────────────────────────────────────────────┘

    bind/unbind hold:   client_mutex  then  card->mutex
```

[`card->mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) is the inner lock, one per card, taken inside [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48) by [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) and dropped only when bind returns. It serializes a single card's instantiation against the runtime operations that take the same lock later, such as a DAPM change or an out-of-band control update. The helpers are thin wrappers over [`mutex_lock_nested()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mutex.h), and the lockdep subclass distinguishes the bind-time hold from a nested runtime hold. [`snd_soc_card_mutex_lock_root()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L16) takes it at [`SND_SOC_CARD_CLASS_ROOT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L12) and [`snd_soc_card_mutex_lock()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L21) at [`SND_SOC_CARD_CLASS_RUNTIME`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L13), the two values of [`enum snd_soc_card_subclass`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-card.h#L11).

The [`instantiated`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) bit is the single-bit flag that records whether the card finished binding. [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) sets it to 1 only after [`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870) succeeds, [`snd_soc_unbind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2153) clears it, and [`snd_soc_card_is_instantiated()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1132) reads it so that teardown skips a card that never bound and runtime paths refuse to touch one that is not ready.

## DETAILS

### Registration initialises the lists and mutexes, then binds

A machine driver hands its card to [`snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2557). The function validates that the card has a name and a device, allocates the DAPM context, and then brings the card's bookkeeping into a known state, initialising all nine list heads and the three mutexes before any binding can run:

```c
/* sound/soc/soc-core.c:2557 */
int snd_soc_register_card(struct snd_soc_card *card)
{
	int ret;

	if (!card->name || !card->dev)
		return -EINVAL;

	card->dapm = snd_soc_dapm_alloc(card->dev);
	if (!card->dapm)
		return -ENOMEM;

	dev_set_drvdata(card->dev, card);

	INIT_LIST_HEAD(&card->widgets);
	INIT_LIST_HEAD(&card->paths);
	INIT_LIST_HEAD(&card->dapm_list);
	INIT_LIST_HEAD(&card->aux_comp_list);
	INIT_LIST_HEAD(&card->component_dev_list);
	INIT_LIST_HEAD(&card->list);
	INIT_LIST_HEAD(&card->rtd_list);
	INIT_LIST_HEAD(&card->dapm_dirty);
	INIT_LIST_HEAD(&card->dobj_list);

	card->instantiated = 0;
	mutex_init(&card->mutex);
	mutex_init(&card->dapm_mutex);
	mutex_init(&card->pcm_mutex);

	mutex_lock(&client_mutex);

	if (card->devres_dev) {
		ret = devm_snd_soc_bind_card(card->devres_dev, card);
		if (ret == -EPROBE_DEFER) {
			list_add(&card->list, &unbind_card_list);
			ret = 0;
		}
	} else {
		ret = snd_soc_bind_card(card);
	}

	mutex_unlock(&client_mutex);

	return ret;
}
```

The function clears [`instantiated`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) to 0, takes [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48), and binds. The branch on [`card->devres_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) selects whether unregistration is device-managed, where a device-managed card binds through [`devm_snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2327) and a plain one through [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163). A `-EPROBE_DEFER` from the device-managed path is not treated as an error. The card is added to [`unbind_card_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L50) and the function returns 0, leaving the card parked until a component registers.

Most x86-64 ACPI machine drivers do not call [`snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2557) directly. They use [`devm_snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L65), which registers a release action so the card unregisters automatically when the platform device is removed:

```c
/* sound/soc/soc-devres.c:65 */
int devm_snd_soc_register_card(struct device *dev, struct snd_soc_card *card)
{
	struct snd_soc_card **ptr;
	int ret;

	ptr = devres_alloc(devm_card_release, sizeof(*ptr), GFP_KERNEL);
	if (!ptr)
		return -ENOMEM;

	ret = snd_soc_register_card(card);
	if (ret == 0) {
		*ptr = card;
		devres_add(dev, ptr);
	} else {
		devres_free(ptr);
	}

	return ret;
}
```

### A machine driver fills the card and registers it

The Intel SOF ES8336 board is an x86-64 example. It declares a static [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) with a name, an owner module, and its DAPM widgets, routes, and controls, leaving [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) and the final [`num_links`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) to be filled at probe time once the firmware quirks are known:

```c
/* sound/soc/intel/boards/sof_es8336.c:421 */
static struct snd_soc_card sof_es8336_card = {
	.name = "essx8336", /* sof- prefix added automatically */
	.owner = THIS_MODULE,
	.dapm_widgets = sof_es8316_widgets,
	.num_dapm_widgets = ARRAY_SIZE(sof_es8316_widgets),
	.dapm_routes = sof_es8316_audio_map,
	.num_dapm_routes = ARRAY_SIZE(sof_es8316_audio_map),
	.controls = sof_es8316_controls,
	.num_controls = ARRAY_SIZE(sof_es8316_controls),
	.fully_routed = true,
	.late_probe = sof_es8336_late_probe,
	.num_links = 1,
};
```

In [`sof_es8336_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_es8336.c#L599) the driver computes the real link count, builds the link array, fixes up the codec name from the ACPI HID carried in the [`struct snd_soc_acpi_mach`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) it received as platform data, assigns the array to [`dai_link`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), and registers the card:

```c
/* sound/soc/intel/boards/sof_es8336.c:655 */
	/* compute number of dai links */
	sof_es8336_card.num_links = 1 + dmic_be_num + hdmi_num;
	...
	sof_es8336_card.dai_link = dai_links;

	/* fixup codec name based on HID */
	adev = acpi_dev_get_first_match_dev(mach->id, NULL, -1);
	if (adev) {
		snprintf(codec_name, sizeof(codec_name),
			 "i2c-%s", acpi_dev_name(adev));
		dai_links[0].codecs->name = codec_name;
		...
	}
```

The card is registered with [`devm_snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L65) near the end of the probe, so removing the platform device unregisters the card without an explicit teardown call in the driver.

### snd_soc_bind_card runs the instantiation sequence under card->mutex

[`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) is the heart of the lifecycle. It runs once, under [`card->mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), and performs every step needed to turn a description into a live ALSA card. The opening of the function takes the lock at the root subclass, sets up DAPM, binds the auxiliary devices, adds one PCM runtime per DAI link, and creates the ALSA sound card:

```c
/* sound/soc/soc-core.c:2163 */
static int snd_soc_bind_card(struct snd_soc_card *card)
{
	struct snd_soc_pcm_runtime *rtd;
	struct snd_soc_component *component;
	struct snd_soc_dapm_context *dapm = snd_soc_card_to_dapm(card);
	int ret;

	snd_soc_card_mutex_lock_root(card);
	snd_soc_fill_dummy_dai(card);

	snd_soc_dapm_init(dapm, card, NULL);

	/* check whether any platform is ignore machine FE and using topology */
	soc_check_tplg_fes(card);

	/* bind aux_devs too */
	ret = soc_bind_aux_dev(card);
	if (ret < 0)
		goto probe_end;

	/* add predefined DAI links to the list */
	card->num_rtd = 0;
	ret = snd_soc_add_pcm_runtimes(card, card->dai_link, card->num_links);
	if (ret < 0)
		goto probe_end;

	/* card bind complete so register a sound card */
	ret = snd_card_new(card->dev, SNDRV_DEFAULT_IDX1, SNDRV_DEFAULT_STR1,
			card->owner, 0, &card->snd_card);
	if (ret < 0) {
		dev_err(card->dev,
			"ASoC: can't create sound card for card %s: %d\n",
			card->name, ret);
		goto probe_end;
	}
	...
```

After the sound card exists, the middle of the function adds the card DAPM widgets, runs the card's [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) callback, and probes the components and DAIs that the links reference:

```c
/* sound/soc/soc-core.c:2163 */
	/* probe all components used by DAI links on this card */
	ret = soc_probe_link_components(card);
	if (ret < 0) {
		if (ret != -EPROBE_DEFER) {
			dev_err(card->dev,
				"ASoC: failed to instantiate card %d\n", ret);
		}
		goto probe_end;
	}

	/* probe auxiliary components */
	ret = soc_probe_aux_devices(card);
	if (ret < 0) {
		dev_err(card->dev,
			"ASoC: failed to probe aux component %d\n", ret);
		goto probe_end;
	}

	/* probe all DAI links on this card */
	ret = soc_probe_link_dais(card);
	if (ret < 0) {
		dev_err(card->dev,
			"ASoC: failed to instantiate card %d\n", ret);
		goto probe_end;
	}
```

The tail adds the card controls and DAPM routes, sets the card name, runs the late probe, registers the device, and only then commits the card as instantiated:

```c
/* sound/soc/soc-core.c:2163 */
	ret = snd_card_register(card->snd_card);
	if (ret < 0) {
		dev_err(card->dev, "ASoC: failed to register soundcard %d\n",
				ret);
		goto probe_end;
	}

	card->instantiated = 1;
	snd_soc_dapm_mark_endpoints_dirty(card);
	snd_soc_dapm_sync(dapm);

	/* deactivate pins to sleep state */
	for_each_card_components(card, component)
		if (!snd_soc_component_active(component))
			pinctrl_pm_select_sleep_state(component->dev);

probe_end:
	if (ret < 0)
		soc_cleanup_card_resources(card);
	snd_soc_card_mutex_unlock(card);

	return ret;
}
```

Every error check in the sequence jumps to the `probe_end` label. A non-zero `ret` runs [`soc_cleanup_card_resources()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2114) before the lock drops, so a card that fails at any step is fully unwound, and [`instantiated`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) is set to 1 only on the success path after [`snd_card_register()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c#L870) returns.

```
    snd_soc_bind_card instantiation sequence (one pass, card->mutex held)
    ────────────────────────────────────────────────────────────────────

    snd_soc_card_mutex_lock_root      take card->mutex at ROOT subclass
              │
              ▼
    snd_soc_dapm_init                 set up the card DAPM context
              │
              ▼
    soc_bind_aux_dev                  bind the auxiliary devices
              │
              ▼
    snd_soc_add_pcm_runtimes          one rtd per dai_link onto rtd_list
              │
              ▼
    snd_card_new                      create the ALSA sound card
              │
              ▼
    soc_probe_link_components         probe each component (may DEFER)
              │
              ▼
    soc_probe_aux_devices             probe the auxiliary components
              │
              ▼
    soc_probe_link_dais               probe every runtime's DAIs
              │
              ▼
    add card controls + dapm_routes   stitch the board graph
              │
              ▼
    snd_card_register                 expose the card to userspace
              │
              ▼
    instantiated = 1                  commit (success path only)

    any step < 0 ─▶ goto probe_end ─▶ soc_cleanup_card_resources
```

### soc_probe_component is where a deferred dependency surfaces

[`soc_probe_link_components()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1742) walks the runtimes in [`probe_order`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L158) and probes each component, propagating the first error up to the bind function. Inside [`soc_probe_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1602) the call to [`snd_soc_component_module_get_when_probe()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h) is the point where a missing module produces `-EPROBE_DEFER`. The function returns it immediately, before claiming the component for the card:

```c
/* sound/soc/soc-core.c:1602 */
static int soc_probe_component(struct snd_soc_card *card,
			       struct snd_soc_component *component)
{
	struct snd_soc_dapm_context *dapm = snd_soc_component_to_dapm(component);
	struct snd_soc_dai *dai;
	int probed = 0;
	int ret;

	if (snd_soc_component_is_dummy(component))
		return 0;
	...
	ret = snd_soc_component_module_get_when_probe(component);
	if (ret < 0)
		return ret;

	component->card = card;
	...
	/* see for_each_card_components */
	list_add(&component->card_list, &card->component_dev_list);

err_probe:
	if (ret < 0)
		soc_remove_component(component, probed);

	return ret;
}
```

That error propagates back through [`soc_probe_link_components()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1742) and [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163), where the `probe_end` tail cleans up the partial card and returns `-EPROBE_DEFER` to [`snd_soc_register_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2557), which parks the card on [`unbind_card_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L50).

### The rebind path retries parked cards when a component registers

A component registers through [`snd_soc_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885). It runs under [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48), registers the component's DAIs, adds the component to the global [`component_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L49), and then walks [`unbind_card_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L50) retrying every waiting card:

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
	...
	ret = snd_soc_register_dais(component, dai_drv, num_dai);
	if (ret < 0) {
		dev_err(component->dev, "ASoC: Failed to register DAIs: %d\n",
			ret);
		goto err_cleanup;
	}
	...
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

[`snd_soc_rebind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2347) retries the bind. It dispatches to the device-managed or plain bind path, and unlinks the card from [`unbind_card_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L50) only when the bind no longer defers:

```c
/* sound/soc/soc-core.c:2347 */
static int snd_soc_rebind_card(struct snd_soc_card *card)
{
	int ret;

	if (card->devres_dev) {
		devres_destroy(card->devres_dev, devm_card_bind_release, NULL, NULL);
		ret = devm_snd_soc_bind_card(card->devres_dev, card);
	} else {
		ret = snd_soc_bind_card(card);
	}

	if (ret != -EPROBE_DEFER)
		list_del_init(&card->list);

	return ret;
}
```

A card that still defers stays on the list and is retried again on the next [`snd_soc_add_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2885), so a card with several missing components binds only after the last of them registers. The reverse case is symmetric. When a component is removed while cards depend on it, [`snd_soc_del_component_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2833) re-adds the affected card to [`unbind_card_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L50) so a later re-registration of the component triggers a rebind.

### Teardown unwinds the card in reverse

[`snd_soc_unregister_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2609) is the entry point for removal. It takes [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48), unbinds the card, and removes it from the global card list:

```c
/* sound/soc/soc-core.c:2609 */
void snd_soc_unregister_card(struct snd_soc_card *card)
{
	mutex_lock(&client_mutex);
	snd_soc_unbind_card(card);
	list_del(&card->list);
	mutex_unlock(&client_mutex);
	dev_dbg(card->dev, "ASoC: Unregistered card '%s'\n", card->name);
}
```

[`snd_soc_unbind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2153) gates the teardown on [`snd_soc_card_is_instantiated()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1132), so a card that was only ever parked on [`unbind_card_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L50) and never bound has nothing to clean up. It clears [`instantiated`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), flushes the delayed work, and runs the resource cleanup:

```c
/* sound/soc/soc-core.c:2153 */
static void snd_soc_unbind_card(struct snd_soc_card *card)
{
	if (snd_soc_card_is_instantiated(card)) {
		card->instantiated = false;
		snd_soc_flush_all_delayed_work(card);

		soc_cleanup_card_resources(card);
	}
}
```

[`soc_cleanup_card_resources()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2114) reverses the bind sequence. It disconnects the ALSA card from userspace first with [`snd_card_disconnect_sync()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/init.c), shuts down DAPM, removes the DAIs and components, frees each PCM runtime, and frees the [`snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/core.h#L80):

```c
/* sound/soc/soc-core.c:2114 */
static void soc_cleanup_card_resources(struct snd_soc_card *card)
{
	struct snd_soc_pcm_runtime *rtd, *n;

	if (card->snd_card)
		snd_card_disconnect_sync(card->snd_card);

	snd_soc_dapm_shutdown(card);

	/* release machine specific resources */
	for_each_card_rtds(card, rtd)
		if (rtd->initialized)
			snd_soc_link_exit(rtd);
	/* flush delayed work before removing DAIs and DAPM widgets */
	snd_soc_flush_all_delayed_work(card);

	/* remove and free each DAI */
	soc_remove_link_dais(card);
	soc_remove_link_components(card);

	for_each_card_rtds_safe(card, rtd, n)
		snd_soc_remove_pcm_runtime(card, rtd);

	/* remove auxiliary devices */
	soc_remove_aux_devices(card);
	soc_unbind_aux_dev(card);

	snd_soc_dapm_free(snd_soc_card_to_dapm(card));
	soc_cleanup_card_debugfs(card);

	/* remove the card */
	snd_soc_card_remove(card);

	if (card->snd_card) {
		snd_card_free(card->snd_card);
		card->snd_card = NULL;
	}
}
```

The DAI removal step [`soc_remove_link_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1694) walks the same [`rtd_list`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) that [`snd_soc_add_pcm_runtimes()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1269) populated at bind time, running [`snd_soc_pcm_dai_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dai.c#L546) in component order so each DAI's [`remove`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op pairs with the [`probe`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) op that [`soc_probe_link_dais()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L1707) ran during instantiation. Because [`soc_cleanup_card_resources()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2114) is called from two places, the `probe_end` tail of [`snd_soc_bind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2163) on an instantiation error and [`snd_soc_unbind_card()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L2153) on normal removal, one function unwinds both a failed bind and a live card, and its guards on [`card->snd_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972) and [`rtd->initialized`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1188) make it safe to run against a card that only got partway through the sequence.

```
    soc_cleanup_card_resources unwinds the bind in reverse
    ──────────────────────────────────────────────────────
    (left: teardown step      right: the bind step it undoes)

    snd_card_disconnect_sync      ◀── undoes ──  snd_card_register
              │
              ▼
    snd_soc_dapm_shutdown         ◀── undoes ──  card DAPM widgets
              │
              ▼
    snd_soc_flush_all_delayed_work   flush before DAIs are removed
              │
              ▼
    soc_remove_link_dais          ◀── undoes ──  soc_probe_link_dais
              │
              ▼
    soc_remove_link_components    ◀── undoes ──  soc_probe_link_components
              │
              ▼
    snd_soc_remove_pcm_runtime    ◀── undoes ──  snd_soc_add_pcm_runtimes
              │
              ▼
    soc_remove + soc_unbind_aux_dev  ◀ undoes ─  soc_bind_aux_dev
              │
              ▼
    snd_card_free                 ◀── undoes ──  snd_card_new

    guards: card->snd_card and rtd->initialized make a partial
    bind safe to unwind through the same path
```

### The two file-scope globals and the per-card lock fields

The outer [`client_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L48), the [`component_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L49), and the [`unbind_card_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L50) defined at file scope in [`soc-core.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c) sit above the inner [`mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L997), [`dapm_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L998), [`pcm_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1001), and [`instantiated`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1091) fields of each [`struct snd_soc_card`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L972), and bind and unbind hold the file-scope lock then the per-card one.

```
    static, file scope (sound/soc/soc-core.c)
    ┌───────────────────────────────────────────────────────────┐
    │  client_mutex            (L48)   outer lock               │
    │  component_list          (L49)   every registered comp    │
    │  unbind_card_list        (L50)   cards waiting on defer   │
    └───────────────────────────────────────────────────────────┘

    per card (struct snd_soc_card)
    ┌───────────────────────────────────────────────────────────┐
    │  mutex        (L997)   inner; ROOT subclass during bind   │
    │  dapm_mutex   (L998)   DAPM graph                         │
    │  pcm_mutex    (L1001)  PCM open/close/params              │
    │  instantiated (L1091)  set at end of bind                 │
    └───────────────────────────────────────────────────────────┘

    bind/unbind hold:   client_mutex  then  card->mutex
```
