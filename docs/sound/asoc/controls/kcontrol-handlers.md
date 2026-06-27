# ASoC kcontrol I/O handlers (soc-ops.c)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A control template wires three function pointers into every ASoC mixer control, and [`soc-ops.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c) supplies the generic bodies those pointers name. The [`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) callback answers a userspace query about the control type, channel count, and value range, the [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) callback reads the current value, and the [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) callback writes a new one and returns 1 when the stored value changed. These handlers are stateless, so the per-control register, bit shift, and value range travel in [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47), which each handler casts back to a [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) (volume or switch), a [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) (enumerated), a [`struct soc_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1248) (byte array), or a [`struct soc_mreg_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1267) (multi-register signed). The volume-and-switch family is the common case, built around [`soc_get_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L288) and [`soc_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L233) with a pair of conversion helpers that move a value between its register encoding and the 0-based integer userspace sees. The Realtek [`rt722-sdca`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c) codec on x86 SoundWire serves as the worked example for the escape hatch where a driver supplies its own [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) and [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47).

```
    Generic volsw conversion (soc-ops.c)
    ─────────────────────────────────────

    get: register ─▶ control value        put: control value ─▶ register
    ┌─────────────────────────────┐       ┌─────────────────────────────┐
    │ snd_soc_component_read(reg) │       │ soc_mixer_valid_ctl(val)    │
    └──────────────┬──────────────┘       └──────────────┬──────────────┘
                   ▼                                      ▼
    ┌─────────────────────────────┐       ┌─────────────────────────────┐
    │ soc_mixer_reg_to_ctl:       │       │ soc_mixer_ctl_to_reg:       │
    │   (reg >> shift) & mask     │       │   invert ? max - val : val  │
    │   sign_extend32(sign_bit)   │       │   reg_val = val + min       │
    │   clamp(min, max); val -= min       │   (reg_val & mask) << shift │
    │   invert ? max - val : val  │       │                             │
    └──────────────┬──────────────┘       └──────────────┬──────────────┘
                   ▼                                      ▼
        ucontrol->value.integer        snd_soc_component_update_bits(reg)
                                          (returns 1 when the value changed)

    mask = soc_mixer_mask(mc)        range presented to userspace = max - min
```

## SUMMARY

The volume-and-switch handlers are the generic [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) and [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) most controls use. [`snd_soc_info_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L332), [`snd_soc_get_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L375), and [`snd_soc_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L396) read the [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) out of [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) and call the shared workers [`soc_get_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L288) and [`soc_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L233) with the field mask from [`soc_mixer_mask()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L195) and a presented range of [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) minus [`min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231). [`soc_mixer_reg_to_ctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L144) shifts and masks the field out of the register, sign-extends it when [`sign_bit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) is set, clamps it into the hardware range, subtracts [`min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) so the value starts at zero, and applies [`invert`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231); [`soc_mixer_ctl_to_reg()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L167) runs the reverse and [`soc_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L233) writes it with [`snd_soc_component_update_bits()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L751), whose nonzero return becomes the change flag. A range control needs no separate handler in this kernel; [`SOC_SINGLE_RANGE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L66) sets a nonzero [`min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) and reuses the same three volsw handlers. A signed control without a sign bit uses [`snd_soc_get_volsw_sx()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L417) and [`snd_soc_put_volsw_sx()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L437), which take the same workers with the wider mask from [`soc_mixer_sx_mask()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L203) and the step count [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231).

The remaining families cover the controls a register-field volsw cannot express. [`snd_soc_info_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L39), [`snd_soc_get_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L58), and [`snd_soc_put_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L89) present a [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) as a list of named items, mapping each register value to an item index through [`snd_soc_enum_val_to_item()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1299) and back through [`snd_soc_enum_item_to_val()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1314). [`snd_soc_bytes_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L525) and [`snd_soc_bytes_put()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L562) move a raw register block through regmap for coefficient arrays, [`snd_soc_get_xr_sx()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L709) and [`snd_soc_put_xr_sx()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L753) assemble one signed value from several consecutive registers, and [`snd_soc_get_strobe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L800) and [`snd_soc_put_strobe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L832) pulse a register bit high then low. An SDCA gain control routes the volsw workers through [`sdca_soc_q78_reg_to_ctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L113) and [`sdca_soc_q78_ctl_to_reg()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L129) when the [`sdca_q78`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1242) bit is set, converting the hardware Q7.8 fixed-point gain to a step index. [`snd_soc_limit_volume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L488) caps an existing volume by setting [`platform_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), and [`SOC_SINGLE_EXT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L234) and its relatives let a driver replace the [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) and [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) while keeping [`snd_soc_info_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L332) for the info callback, the path the rt722-sdca volume controls take.

## SPECIFICATIONS

The control handlers are Linux kernel software constructs and have no standalone hardware specification. The info, read, and write protocol they serve is the ALSA control API, and the dB-scale metadata that a TLV control attaches is encoded in the ALSA TLV (Type-Length-Value) format from [`include/uapi/sound/tlv.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/tlv.h). On the x86 SoundWire path an SDCA gain register holds a Q7.8 fixed-point value that [`sdca_soc_q78_reg_to_ctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L113) converts.

## LINUX KERNEL

### Private-data types (soc.h)

- [`'\<struct soc_mixer_control\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231): the volume/switch private data; the handlers read [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), [`rreg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), [`shift`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), [`rshift`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), [`min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), [`platform_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), [`sign_bit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), [`invert`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), and [`sdca_q78`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1242)
- [`'\<struct soc_enum\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273): the enumerated private data; holds [`reg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273), [`shift_l`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273), [`shift_r`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273), [`items`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273), [`mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273), [`texts`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273), and the optional [`values`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) remap table
- [`'\<struct soc_bytes\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1248): the byte-array private data; holds [`base`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1248), [`num_regs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1248), and [`mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1248)
- [`'\<struct soc_bytes_ext\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1254): the TLV byte-control private data; holds [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1254) and the driver [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1254)/[`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1254) byte callbacks
- [`'\<struct soc_mreg_control\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1267): the multi-register signed private data; holds [`min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1267), [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1267), [`regbase`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1267), [`regcount`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1267), [`nbits`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1267), and [`invert`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1267)

### Volume/switch handlers (soc-ops.c)

- [`'\<snd_soc_info_volsw\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L332): report type, count, and 0..(max-min) for a volsw control through [`soc_info_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L209)
- [`'\<snd_soc_get_volsw\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L375): read the field and present it 0-based through [`soc_get_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L288) with the mask from [`soc_mixer_mask()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L195)
- [`'\<snd_soc_put_volsw\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L396): validate, encode, and write the field through [`soc_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L233)
- [`'\<snd_soc_info_volsw_sx\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L355): report a signed (SX) control with a presented range of [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) steps
- [`'\<snd_soc_get_volsw_sx\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L417) and [`'\<snd_soc_put_volsw_sx\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L437): the SX get/put, calling the same workers with the wider mask from [`soc_mixer_sx_mask()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L203)

### Volsw internals (soc-ops.c)

- [`'\<soc_info_volsw\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L209): choose [`SNDRV_CTL_ELEM_TYPE_INTEGER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1118) or boolean, apply [`platform_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), and set the channel count
- [`'\<soc_get_volsw\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L288): the read worker; selects the register-to-control converter and handles the stereo second channel
- [`'\<soc_put_volsw\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L233): the write worker; validates, builds the masked value, and updates one or two registers
- [`'\<soc_mixer_reg_to_ctl\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L144): convert a register field to the 0-based control value (shift, mask, sign-extend, clamp, invert)
- [`'\<soc_mixer_ctl_to_reg\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L167): convert a control value back to a shifted register field (invert, add min, mask, shift)
- [`'\<soc_mixer_valid_ctl\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L181): reject a negative value or one above [`platform_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) or the range
- [`'\<soc_mixer_mask\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L195) and [`'\<soc_mixer_sx_mask\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L203): build the field mask for the volsw and SX cases
- [`'\<sdca_soc_q78_reg_to_ctl\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L113) and [`'\<sdca_soc_q78_ctl_to_reg\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L129): the Q7.8 converters used when [`sdca_q78`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1242) is set

### Enumerated handlers (soc-ops.c, soc.h)

- [`'\<snd_soc_info_enum_double\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L39): report the item names through [`snd_ctl_enum_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2436)
- [`'\<snd_soc_get_enum_double\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L58): read the register and map each field to an item index
- [`'\<snd_soc_put_enum_double\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L89): map the chosen item(s) back to register values and write them
- [`'\<snd_soc_enum_val_to_item\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1299) and [`'\<snd_soc_enum_item_to_val\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1314): the value/item remap used by both enum get and put

### Byte, multi-register, and strobe handlers (soc-ops.c)

- [`'\<snd_soc_bytes_info\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L512), [`'\<snd_soc_bytes_get\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L525), and [`'\<snd_soc_bytes_put\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L562): raw register-block transfer through regmap for a [`struct soc_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1248)
- [`'\<snd_soc_bytes_info_ext\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L634) and [`'\<snd_soc_bytes_tlv_callback\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L646): the TLV byte channel that routes reads and writes to the driver callbacks in a [`struct soc_bytes_ext`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1254)
- [`'\<snd_soc_info_xr_sx\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L680), [`'\<snd_soc_get_xr_sx\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L709), and [`'\<snd_soc_put_xr_sx\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L753): assemble one signed value spanning [`regcount`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1267) registers
- [`'\<snd_soc_get_strobe\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L800) and [`'\<snd_soc_put_strobe\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L832): pulse a single register bit to its active level and back

### Platform-max limiting (soc-ops.c, soc-card.c)

- [`'\<snd_soc_limit_volume\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L488): set [`platform_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) on a named control and clamp its current value
- [`'\<snd_soc_clip_to_platform_max\>':'sound/soc/soc-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L448): read the control, cap each channel at [`platform_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), and write it back
- [`'\<snd_soc_card_get_kcontrol\>':'sound/soc/soc-card.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L22): find a card control by name through [`snd_ctl_find_id_mixer()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L159)

### Common helpers

- [`'\<snd_soc_volsw_is_stereo\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1287): test whether a [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) carries two channels
- [`'\<snd_kcontrol_chip\>':'include/sound/control.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L14): recover the [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) (the component) from a control
- [`'\<snd_soc_component_read\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L671) and [`'\<snd_soc_component_update_bits\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L751): the register read and read/modify/write the handlers drive

### Handler-selecting macros (soc.h)

- [`'\<SOC_SINGLE\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L61), [`'\<SOC_SINGLE_RANGE\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L66), [`'\<SOC_DOUBLE_R\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L110): wire the volsw handlers
- [`'\<SOC_SINGLE_SX_TLV\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L79) and [`'\<SOC_DOUBLE_R_SX_TLV\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L171): wire the SX handlers
- [`'\<SOC_ENUM\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L229) and [`'\<SOC_ENUM_EXT\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L314): wire the enum handlers
- [`'\<SND_SOC_BYTES\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L329) and [`'\<SND_SOC_BYTES_TLV\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L366): wire the byte handlers
- [`'\<SOC_SINGLE_XR_SX\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L374) and [`'\<SOC_SINGLE_STROBE\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L383): wire the multi-register and strobe handlers
- [`'\<SOC_SINGLE_EXT\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L234) and [`'\<SOC_DOUBLE_R_EXT_TLV\>':'include/sound/soc.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L282): keep [`snd_soc_info_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L332) and substitute driver get/put

### rt722-sdca worked example (codecs/rt722-sdca.c)

- [`'\<rt722_sdca_set_gain_get\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L419) and [`'\<rt722_sdca_set_gain_put\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L348): the custom gain handlers a [`SOC_DOUBLE_R_EXT_TLV`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L282) control installs in place of the generic volsw get/put

## KERNEL DOCUMENTATION

- [`Documentation/sound/kernel-api/writing-an-alsa-driver.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/kernel-api/writing-an-alsa-driver.rst): the ALSA control element model and the info/get/put callback contract
- [`Documentation/sound/designs/control-names.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/designs/control-names.rst): the control naming convention the " Volume" suffix test in [`soc_info_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L209) depends on
- [`Documentation/sound/soc/codec.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/codec.rst): the codec component guide where the control macros are declared

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA project library documentation](https://www.alsa-project.org/alsa-doc/alsa-lib/group__Control.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## CALLBACKS

Each control names an [`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47), a [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47), and a [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47), and the macro that defines the control decides which family of soc-ops.c bodies those three name. The families differ in the private struct they decode and in how they map between the register encoding and the value userspace reads.

| Family | info | get / put | private data | wired by |
|--------|------|-----------|--------------|----------|
| volume/switch | [`snd_soc_info_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L332) | [`snd_soc_get_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L375) / [`snd_soc_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L396) | [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) | [`SOC_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L61), [`SOC_DOUBLE_R`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L110), [`SOC_SINGLE_RANGE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L66) |
| signed (SX) | [`snd_soc_info_volsw_sx()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L355) | [`snd_soc_get_volsw_sx()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L417) / [`snd_soc_put_volsw_sx()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L437) | [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) | [`SOC_SINGLE_SX_TLV`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L79), [`SOC_DOUBLE_R_SX_TLV`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L171) |
| enumerated | [`snd_soc_info_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L39) | [`snd_soc_get_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L58) / [`snd_soc_put_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L89) | [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) | [`SOC_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L229) |
| byte array | [`snd_soc_bytes_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L512) | [`snd_soc_bytes_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L525) / [`snd_soc_bytes_put()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L562) | [`struct soc_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1248) | [`SND_SOC_BYTES`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L329) |
| multi-register | [`snd_soc_info_xr_sx()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L680) | [`snd_soc_get_xr_sx()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L709) / [`snd_soc_put_xr_sx()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L753) | [`struct soc_mreg_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1267) | [`SOC_SINGLE_XR_SX`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L374) |
| strobe | [`snd_soc_info_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L39) | [`snd_soc_get_strobe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L800) / [`snd_soc_put_strobe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L832) | [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) | [`SOC_SINGLE_STROBE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L383) |
| custom (EXT) | [`snd_soc_info_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L332) | driver get / driver put | [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) | [`SOC_SINGLE_EXT`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L234), [`SOC_DOUBLE_R_EXT_TLV`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L282) |

The [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) callback returns 1 when the stored value changed and 0 when it did not, so the control core can emit a change notification only on a real change. The generic volsw put produces this flag from [`snd_soc_component_update_bits()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L751), and a custom put returns its own change count.

## DETAILS

### Every handler recovers its component and private data the same way

A control handler receives only the [`struct snd_kcontrol`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) and a value buffer, so its first job is to recover the component it belongs to and the per-control description. The component comes from [`snd_kcontrol_chip()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L14), which reads back the [`private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) the registration path stored, and the description comes from casting [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) to the matching struct:

```c
/* include/sound/control.h:14 */
#define snd_kcontrol_chip(kcontrol) ((kcontrol)->private_data)
```

The enumerated get is the shortest body that shows the full pattern. It casts [`private_value`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) to a [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273), reads the register with [`snd_soc_component_read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L671), extracts the field at [`shift_l`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273), and turns the raw value into an item index, repeating for the second channel when [`shift_l`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) and [`shift_r`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) differ:

```c
/* sound/soc/soc-ops.c:58 */
int snd_soc_get_enum_double(struct snd_kcontrol *kcontrol,
			    struct snd_ctl_elem_value *ucontrol)
{
	struct snd_soc_component *component = snd_kcontrol_chip(kcontrol);
	struct soc_enum *e = (struct soc_enum *)kcontrol->private_value;
	unsigned int val, item;
	unsigned int reg_val;

	reg_val = snd_soc_component_read(component, e->reg);
	val = (reg_val >> e->shift_l) & e->mask;
	item = snd_soc_enum_val_to_item(e, val);
	ucontrol->value.enumerated.item[0] = item;
	if (e->shift_l != e->shift_r) {
		val = (reg_val >> e->shift_r) & e->mask;
		item = snd_soc_enum_val_to_item(e, val);
		ucontrol->value.enumerated.item[1] = item;
	}

	return 0;
}
```

### The volsw info callback picks the type and clamps the range

[`snd_soc_info_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L332) is a thin wrapper that recovers the [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) and calls the shared [`soc_info_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L209) with the presented range, the hardware [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) minus [`min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231):

```c
/* sound/soc/soc-ops.c:332 */
int snd_soc_info_volsw(struct snd_kcontrol *kcontrol,
		       struct snd_ctl_elem_info *uinfo)
{
	struct soc_mixer_control *mc =
		(struct soc_mixer_control *)kcontrol->private_value;

	return soc_info_volsw(kcontrol, uinfo, mc, mc->max - mc->min);
}
```

[`soc_info_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L209) defaults the type to an integer and downgrades it to a boolean only for a single-step control whose name does not end in " Volume", which keeps a two-value " Volume" control reported as an integer so userspace renders it with a slider. It then clamps the reported maximum to [`platform_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) when one is set and sets the channel count from [`snd_soc_volsw_is_stereo()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1287):

```c
/* sound/soc/soc-ops.c:209 */
static int soc_info_volsw(struct snd_kcontrol *kcontrol,
			  struct snd_ctl_elem_info *uinfo,
			  struct soc_mixer_control *mc, int max)
{
	uinfo->type = SNDRV_CTL_ELEM_TYPE_INTEGER;

	if (max == 1) {
		/* Even two value controls ending in Volume should be integer */
		const char *vol_string = strstr(kcontrol->id.name, " Volume");

		if (!vol_string || strcmp(vol_string, " Volume"))
			uinfo->type = SNDRV_CTL_ELEM_TYPE_BOOLEAN;
	}

	if (mc->platform_max && mc->platform_max < max)
		max = mc->platform_max;

	uinfo->count = snd_soc_volsw_is_stereo(mc) ? 2 : 1;
	uinfo->value.integer.min = 0;
	uinfo->value.integer.max = max;

	return 0;
}
```

[`snd_soc_volsw_is_stereo()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1287) reports a single channel only when both the register and the shift match between the two channels, so a control with two shifts in one register or with two distinct registers reports two channels:

```c
/* include/sound/soc.h:1287 */
static inline bool snd_soc_volsw_is_stereo(const struct soc_mixer_control *mc)
{
	if (mc->reg == mc->rreg && mc->shift == mc->rshift)
		return false;
	...
	return true;
}
```

These two tables read the info logic, the upper one choosing integer or boolean from the presented max and the " Volume" suffix, the lower turning the stereo test shown above into a channel count:

```
    soc_info_volsw: type and channel-count decision
    ─────────────────────────────────────────────────

    max == (mc->max - mc->min)        name ends in " Volume"?
    ┌──────────────┬──────────────────┬───────────────────────┐
    │ max          │ name suffix      │ uinfo->type           │
    ├──────────────┼──────────────────┼───────────────────────┤
    │ > 1          │ (any)            │ ELEM_TYPE_INTEGER     │
    │ == 1         │ " Volume"        │ ELEM_TYPE_INTEGER     │
    │ == 1         │ other            │ ELEM_TYPE_BOOLEAN     │
    └──────────────┴──────────────────┴───────────────────────┘
    then  max  ◀── min(max, platform_max)   if platform_max set
          min  ◀── 0

    snd_soc_volsw_is_stereo(mc)  →  uinfo->count
    ┌────────────────────────────────────────┬─────────────────┐
    │ reg == rreg  AND  shift == rshift       │ count = 1       │
    │ otherwise (2 shifts, or 2 registers)    │ count = 2       │
    └────────────────────────────────────────┴─────────────────┘
```

### The volsw get decodes one or two register fields

[`snd_soc_get_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L375) builds the field mask with [`soc_mixer_mask()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L195) and calls [`soc_get_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L288) with the presented range and the non-SX flag:

```c
/* sound/soc/soc-ops.c:375 */
int snd_soc_get_volsw(struct snd_kcontrol *kcontrol,
		      struct snd_ctl_elem_value *ucontrol)
{
	struct soc_mixer_control *mc =
		(struct soc_mixer_control *)kcontrol->private_value;
	unsigned int mask = soc_mixer_mask(mc);

	return soc_get_volsw(kcontrol, ucontrol, mc, mask, mc->max - mc->min, false);
}
```

[`soc_mixer_mask()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L195) covers the [`sign_bit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) when one is declared and otherwise spans exactly the bits needed to hold [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231):

```c
/* sound/soc/soc-ops.c:195 */
static int soc_mixer_mask(struct soc_mixer_control *mc)
{
	if (mc->sign_bit)
		return GENMASK(mc->sign_bit, 0);
	else
		return GENMASK(fls(mc->max) - 1, 0);
}
```

[`soc_get_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L288) selects the register-to-control converter (the Q7.8 path when [`sdca_q78`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1242) is set, otherwise [`soc_mixer_reg_to_ctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L144)), reads the register once, and converts the first channel. For a stereo control sharing one register it converts the second channel from the same read at [`rshift`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231); for a two-register control it reads [`rreg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) separately:

```c
/* sound/soc/soc-ops.c:288 */
static int soc_get_volsw(struct snd_kcontrol *kcontrol,
			 struct snd_ctl_elem_value *ucontrol,
			 struct soc_mixer_control *mc, int mask, int max, bool sx)
{
	int (*reg_to_ctl)(struct soc_mixer_control *, unsigned int, unsigned int,
			  unsigned int, int, bool);
	struct snd_soc_component *component = snd_kcontrol_chip(kcontrol);
	unsigned int reg_val;
	int val;

	if (mc->sdca_q78)
		reg_to_ctl = sdca_soc_q78_reg_to_ctl;
	else
		reg_to_ctl = soc_mixer_reg_to_ctl;

	reg_val = snd_soc_component_read(component, mc->reg);
	val = reg_to_ctl(mc, reg_val, mask, mc->shift, max, sx);

	ucontrol->value.integer.value[0] = val;

	if (snd_soc_volsw_is_stereo(mc)) {
		if (mc->reg == mc->rreg) {
			val = reg_to_ctl(mc, reg_val, mask, mc->rshift, max, sx);
		} else {
			reg_val = snd_soc_component_read(component, mc->rreg);
			val = reg_to_ctl(mc, reg_val, mask, mc->shift, max, sx);
		}

		ucontrol->value.integer.value[1] = val;
	}

	return 0;
}
```

[`soc_mixer_reg_to_ctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L144) is where the register encoding becomes the value userspace reads. It shifts and masks the field, sign-extends it when [`sign_bit`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) is set, then in the non-SX case clamps the result into the hardware range and subtracts [`min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) so the value starts at zero, and finally mirrors it when [`invert`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) is set. According to the comment, the SX branch "intentionally can overflow here", which is how a signed-range control represents values either side of zero without a sign bit:

```c
/* sound/soc/soc-ops.c:144 */
static int soc_mixer_reg_to_ctl(struct soc_mixer_control *mc, unsigned int reg_val,
				unsigned int mask, unsigned int shift, int max,
				bool sx)
{
	int val = (reg_val >> shift) & mask;

	if (mc->sign_bit)
		val = sign_extend32(val, mc->sign_bit);

	if (sx) {
		val -= mc->min; // SX controls intentionally can overflow here
		val = min_t(unsigned int, val & mask, max);
	} else {
		val = clamp(val, mc->min, mc->max);
		val -= mc->min;
	}

	if (mc->invert)
		val = max - val;

	return val;
}
```

### The volsw put validates, encodes, and writes

[`snd_soc_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L396) mirrors the get, recovering the [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) and the mask and calling [`soc_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L233). That worker first selects the control-to-register converter and the value mask, with the Q7.8 path leaving the mask un-shifted because the SDCA converter writes a whole register:

```c
/* sound/soc/soc-ops.c:233 */
static int soc_put_volsw(struct snd_kcontrol *kcontrol,
			 struct snd_ctl_elem_value *ucontrol,
			 struct soc_mixer_control *mc, int mask, int max)
{
	unsigned int (*ctl_to_reg)(struct soc_mixer_control *, int, unsigned int, unsigned int, int);
	struct snd_soc_component *component = snd_kcontrol_chip(kcontrol);
	unsigned int val1, val_mask;
	unsigned int val2 = 0;
	bool double_r = false;
	int ret;

	if (mc->sdca_q78) {
		ctl_to_reg = sdca_soc_q78_ctl_to_reg;
		val_mask = mask;
	} else {
		ctl_to_reg = soc_mixer_ctl_to_reg;
		val_mask = mask << mc->shift;
	}

	ret = soc_mixer_valid_ctl(mc, ucontrol->value.integer.value[0], max);
	if (ret)
		return ret;

	val1 = ctl_to_reg(mc, ucontrol->value.integer.value[0],
				    mask, mc->shift, max);
	...
```

Each channel is checked by [`soc_mixer_valid_ctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L181) before it is encoded, so a value below zero, above [`platform_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), or above the range is rejected with [`-EINVAL`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/asm-generic/errno-base.h#L26) before any register is touched:

```c
/* sound/soc/soc-ops.c:181 */
static int soc_mixer_valid_ctl(struct soc_mixer_control *mc, long val, int max)
{
	if (val < 0)
		return -EINVAL;

	if (mc->platform_max && val > mc->platform_max)
		return -EINVAL;

	if (val > max)
		return -EINVAL;

	return 0;
}
```

The tail of [`soc_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L233) folds a same-register stereo control into one masked write and splits a two-register stereo control into a second write to [`rreg`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231). The change flag from the first [`snd_soc_component_update_bits()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L751) is the return value, and the second write keeps the flag set rather than dropping it:

```c
/* sound/soc/soc-ops.c:259 */
	if (snd_soc_volsw_is_stereo(mc)) {
		ret = soc_mixer_valid_ctl(mc, ucontrol->value.integer.value[1], max);
		if (ret)
			return ret;

		if (mc->reg == mc->rreg) {
			val1 |= ctl_to_reg(mc, ucontrol->value.integer.value[1], mask, mc->rshift, max);
			val_mask |= mask << mc->rshift;
		} else {
			val2 = ctl_to_reg(mc, ucontrol->value.integer.value[1], mask, mc->shift, max);
			double_r = true;
		}
	}

	ret = snd_soc_component_update_bits(component, mc->reg, val_mask, val1);
	if (ret < 0)
		return ret;

	if (double_r) {
		int err = snd_soc_component_update_bits(component, mc->rreg,
							val_mask, val2);
		/* Don't drop change flag */
		if (err)
			return err;
	}

	return ret;
}
```

[`soc_mixer_ctl_to_reg()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L167) is the exact reverse of the read conversion, applying [`invert`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), adding [`min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) back, and shifting the masked value into position:

```c
/* sound/soc/soc-ops.c:167 */
static unsigned int soc_mixer_ctl_to_reg(struct soc_mixer_control *mc, int val,
					 unsigned int mask, unsigned int shift,
					 int max)
{
	unsigned int reg_val;

	if (mc->invert)
		val = max - val;

	reg_val = val + mc->min;

	return (reg_val & mask) << shift;
}
```

The shift and mask the converters apply place the field inside one register word, the figure marking where mc->shift positions it and which register and shift each stereo channel reads:

```
    soc_mixer_control fields → one register word
    ──────────────────────────────────────────────

    register read from mc->reg (one channel shown)
     MSB                                              LSB
    ┌───────────────────────────────────────────────────┐
    │ . . . │ sign_bit │◀── mask ──▶│ . . . . . . . . . │
    └───────────────────┬───────────────────────────────┘
                        └── field starts at mc->shift ──▶ bit 0
      soc_mixer_mask(mc):
        sign_bit set  →  GENMASK(sign_bit, 0)
        else          →  GENMASK(fls(max) - 1, 0)

    stereo source selection (soc_get_volsw)
    ┌──────────────┬──────────────────────┬────────────────┐
    │ channel      │ register read        │ field shift    │
    ├──────────────┼──────────────────────┼────────────────┤
    │ value[0]     │ mc->reg              │ mc->shift      │
    │ value[1]     │ mc->reg  (reg==rreg) │ mc->rshift     │
    │ value[1]     │ mc->rreg (reg!=rreg) │ mc->shift      │
    └──────────────┴──────────────────────┴────────────────┘
```

### Range controls reuse the volsw handlers

A range control needs no dedicated handler in this kernel. [`SOC_SINGLE_RANGE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L66) wires the same [`snd_soc_get_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L375) and [`snd_soc_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L396) as [`SOC_SINGLE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L61) and differs only in passing a nonzero [`min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), which the `val -= mc->min` step in [`soc_mixer_reg_to_ctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L144) and the `val + mc->min` step in [`soc_mixer_ctl_to_reg()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L167) turn into a window starting at zero:

```c
/* include/sound/soc.h:66 */
#define SOC_SINGLE_RANGE(xname, xreg, xshift, xmin, xmax, xinvert) \
{	.iface = SNDRV_CTL_ELEM_IFACE_MIXER, .name = (xname),\
	.info = snd_soc_info_volsw, .get = snd_soc_get_volsw, \
	.put = snd_soc_put_volsw, \
	.private_value = SOC_SINGLE_VALUE(xreg, xshift, xmin, xmax, xinvert, 0) }
```

### Signed controls without a sign bit use the SX path

[`snd_soc_get_volsw_sx()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L417) and [`snd_soc_put_volsw_sx()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L437) call the same workers as the plain volsw handlers, with two differences. The mask comes from [`soc_mixer_sx_mask()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L203), which is one bit wider so the sum of [`min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) and [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) fits, and the presented range is [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) (a count of steps) rather than [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) minus [`min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231):

```c
/* sound/soc/soc-ops.c:417 */
int snd_soc_get_volsw_sx(struct snd_kcontrol *kcontrol,
			 struct snd_ctl_elem_value *ucontrol)
{
	struct soc_mixer_control *mc =
		(struct soc_mixer_control *)kcontrol->private_value;
	unsigned int mask = soc_mixer_sx_mask(mc);

	return soc_get_volsw(kcontrol, ucontrol, mc, mask, mc->max, true);
}
```

```c
/* sound/soc/soc-ops.c:203 */
static int soc_mixer_sx_mask(struct soc_mixer_control *mc)
{
	// min + max will take us 1-bit over the size of the mask
	return GENMASK(fls(mc->min + mc->max) - 2, 0);
}
```

The SX info callback follows the same pattern as the plain volsw one, calling the shared [`soc_info_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L209) but passing the raw step count [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) as the presented maximum rather than [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) minus [`min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), because for an SX control [`min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) is the lowest register value and [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) already counts the steps either side of zero:

```c
/* sound/soc/soc-ops.c:355 */
int snd_soc_info_volsw_sx(struct snd_kcontrol *kcontrol,
			  struct snd_ctl_elem_info *uinfo)
{
	struct soc_mixer_control *mc =
		(struct soc_mixer_control *)kcontrol->private_value;

	return soc_info_volsw(kcontrol, uinfo, mc, mc->max);
}
```

[`snd_soc_put_volsw_sx()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L437) is the write half of the pair and the mirror of the SX get, recovering the [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) and the wider [`soc_mixer_sx_mask()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L203) and handing them to the shared [`soc_put_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L233) worker with the step count [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) as the range:

```c
/* sound/soc/soc-ops.c:437 */
int snd_soc_put_volsw_sx(struct snd_kcontrol *kcontrol,
			 struct snd_ctl_elem_value *ucontrol)
{
	struct soc_mixer_control *mc =
		(struct soc_mixer_control *)kcontrol->private_value;
	unsigned int mask = soc_mixer_sx_mask(mc);

	return soc_put_volsw(kcontrol, ucontrol, mc, mask, mc->max);
}
```

### SDCA gain controls convert Q7.8 fixed point

When [`sdca_q78`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1242) is set on the [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), both volsw workers route through the Q7.8 converters instead of the bit-field ones, because an SDCA gain register holds a signed fixed-point decibel value rather than a step in a field. [`sdca_soc_q78_reg_to_ctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L113) sign-extends the register, scales it by 100/256, divides by the per-step size held in [`shift`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231), and offsets by [`min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231). The [`shift`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) field is reused as the step size here, so the converter warns and bails when it is zero:

```c
/* sound/soc/soc-ops.c:113 */
static int sdca_soc_q78_reg_to_ctl(struct soc_mixer_control *mc, unsigned int reg_val,
				   unsigned int mask, unsigned int shift, int max,
				   bool sx)
{
	int val = reg_val;

	if (WARN_ON(!mc->shift))
		return -EINVAL;

	val = sign_extend32(val, mc->sign_bit);
	val = (((val * 100) >> 8) / (int)mc->shift);
	val -= mc->min;

	return val & mask;
}
```

The converter listed above runs top to bottom here, sign-extending the Q7.8 word, scaling it to centi-dB, dividing by the per-step size in shift, and offsetting by min to a 0-based step:

```
    sdca_q78_reg_to_ctl: Q7.8 register → step index
    ─────────────────────────────────────────────────

    register word (signed Q7.8 fixed point)
     bit 15                                         bit 0
    ┌────────────────────────┬──────────────────────────┐
    │   integer dB (Q7)      │   fraction (.8)          │
    └────────────────────────┴──────────────────────────┘
     ▲ sign at mc->sign_bit

         sign_extend32(val, mc->sign_bit)
                    ▼
         (val * 100) >> 8        scale Q7.8 → centi-dB
                    ▼
         / (int)mc->shift        mc->shift reused as per-step size
                    ▼              (WARN + bail when shift == 0)
         val -= mc->min           offset to a 0-based step
                    ▼
         val & mask               → ucontrol->value.integer
```

### The enumerated info callback names the items

The enum [`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) callback differs from the volsw one in that it reports a list of strings rather than an integer range. [`snd_soc_info_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L39) recovers the [`struct soc_enum`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) and hands [`snd_ctl_enum_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/control.c#L2436) the channel count (two when [`shift_l`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) and [`shift_r`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) differ), the [`items`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) count, and the [`texts`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) name array, so userspace shows a named menu instead of a slider:

```c
/* sound/soc/soc-ops.c:39 */
int snd_soc_info_enum_double(struct snd_kcontrol *kcontrol,
			     struct snd_ctl_elem_info *uinfo)
{
	struct soc_enum *e = (struct soc_enum *)kcontrol->private_value;

	return snd_ctl_enum_info(uinfo, e->shift_l == e->shift_r ? 1 : 2,
				 e->items, e->texts);
}
```

### Enumerated put maps items back to register values

[`snd_soc_put_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L89) range-checks each chosen item against [`items`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273), maps the item index to a register value with [`snd_soc_enum_item_to_val()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1314), positions it at [`shift_l`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) (and [`shift_r`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) for the second channel), and writes the combined mask and value in a single [`snd_soc_component_update_bits()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L751):

```c
/* sound/soc/soc-ops.c:89 */
int snd_soc_put_enum_double(struct snd_kcontrol *kcontrol,
			    struct snd_ctl_elem_value *ucontrol)
{
	struct snd_soc_component *component = snd_kcontrol_chip(kcontrol);
	struct soc_enum *e = (struct soc_enum *)kcontrol->private_value;
	unsigned int *item = ucontrol->value.enumerated.item;
	unsigned int val;
	unsigned int mask;

	if (item[0] >= e->items)
		return -EINVAL;
	val = snd_soc_enum_item_to_val(e, item[0]) << e->shift_l;
	mask = e->mask << e->shift_l;
	if (e->shift_l != e->shift_r) {
		if (item[1] >= e->items)
			return -EINVAL;
		val |= snd_soc_enum_item_to_val(e, item[1]) << e->shift_r;
		mask |= e->mask << e->shift_r;
	}

	return snd_soc_component_update_bits(component, e->reg, mask, val);
}
```

[`snd_soc_enum_item_to_val()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1314) returns the item index unchanged for a plain [`SOC_ENUM`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L229) and indexes the [`values`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1273) table for a value-enum, which is how a non-contiguous register encoding is hidden behind a contiguous item list:

```c
/* include/sound/soc.h:1314 */
static inline unsigned int snd_soc_enum_item_to_val(const struct soc_enum *e,
	unsigned int item)
{
	if (!e->values)
		return item;

	return e->values[item];
}
```

The remap shown above sits in the middle of this path, the chosen item passing straight through or through the values table, then shifting into the field at shift_l (and shift_r for a second channel) for one masked write:

```
    snd_soc_put_enum_double: item index → register field
    ──────────────────────────────────────────────────────

    userspace item[0]  (0 .. e->items-1, range-checked)
                    │
                    ▼  snd_soc_enum_item_to_val(e, item)
    ┌───────────────────────────────┬───────────────────────┐
    │ e->values == NULL (SOC_ENUM)  │ reg_val = item        │
    │ e->values set  (value-enum)   │ reg_val = values[item]│
    └───────────────────────────────┴───────────────────────┘
                    │
                    ▼  place into the register word
       val  = reg_val(item[0]) << shift_l
       mask = e->mask          << shift_l
       if shift_l != shift_r:                  (second channel)
         val  = val  OR (reg_val(item[1]) << shift_r)
         mask = mask OR (e->mask          << shift_r)
                    ▼
       snd_soc_component_update_bits(e->reg, mask, val)
```

### Byte, multi-register, and strobe handlers

A coefficient block uses [`snd_soc_bytes_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L525) and [`snd_soc_bytes_put()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L562), which move a [`struct soc_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1248) region through [`regmap_raw_read()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h) and [`regmap_raw_write()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h) and preserve any masked bits across a write. [`snd_soc_get_xr_sx()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L709) assembles a single signed value from [`regcount`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1267) consecutive registers, each contributing one register-width of bits, and sign-extends the [`nbits`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1267)-wide result when [`min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1267) is negative:

The multi-register info callback is unusual in that it reports [`min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1267) and [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1267) directly rather than a 0-based range, because the [`struct soc_mreg_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1267) already carries a signed value that may include its own sign bit. [`snd_soc_info_xr_sx()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L680) writes the integer type, a single channel, and the stored bounds straight into the [`struct snd_ctl_elem_info`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1118):

```c
/* sound/soc/soc-ops.c:680 */
int snd_soc_info_xr_sx(struct snd_kcontrol *kcontrol,
		       struct snd_ctl_elem_info *uinfo)
{
	struct soc_mreg_control *mc =
		(struct soc_mreg_control *)kcontrol->private_value;

	uinfo->type = SNDRV_CTL_ELEM_TYPE_INTEGER;
	uinfo->count = 1;
	uinfo->value.integer.min = mc->min;
	uinfo->value.integer.max = mc->max;

	return 0;
}
```

```c
/* sound/soc/soc-ops.c:709 */
int snd_soc_get_xr_sx(struct snd_kcontrol *kcontrol,
		      struct snd_ctl_elem_value *ucontrol)
{
	struct snd_soc_component *component = snd_kcontrol_chip(kcontrol);
	struct soc_mreg_control *mc =
		(struct soc_mreg_control *)kcontrol->private_value;
	unsigned int regbase = mc->regbase;
	unsigned int regcount = mc->regcount;
	unsigned int regwshift = component->val_bytes * BITS_PER_BYTE;
	unsigned int regwmask = GENMASK(regwshift - 1, 0);
	unsigned long mask = GENMASK(mc->nbits - 1, 0);
	long val = 0;
	unsigned int i;

	for (i = 0; i < regcount; i++) {
		unsigned int regval = snd_soc_component_read(component, regbase + i);

		val |= (regval & regwmask) << (regwshift * (regcount - i - 1));
	}
	val &= mask;
	if (mc->min < 0 && val > mc->max)
		val |= ~mask;
	if (mc->invert)
		val = mc->max - val;
	ucontrol->value.integer.value[0] = val;

	return 0;
}
```

[`snd_soc_put_xr_sx()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L753) is the write half of the same control, validating the value against [`min`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1267) and [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1267), then slicing the [`nbits`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1267)-wide value into per-register fields and writing each one with [`snd_soc_component_update_bits()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L751). It accumulates the change flag the way the stereo volsw put does, keeping the return positive when any one register actually changed:

```c
/* sound/soc/soc-ops.c:753 */
int snd_soc_put_xr_sx(struct snd_kcontrol *kcontrol,
		      struct snd_ctl_elem_value *ucontrol)
{
	struct snd_soc_component *component = snd_kcontrol_chip(kcontrol);
	struct soc_mreg_control *mc =
		(struct soc_mreg_control *)kcontrol->private_value;
	unsigned int regbase = mc->regbase;
	unsigned int regcount = mc->regcount;
	unsigned int regwshift = component->val_bytes * BITS_PER_BYTE;
	unsigned int regwmask = GENMASK(regwshift - 1, 0);
	unsigned long mask = GENMASK(mc->nbits - 1, 0);
	long val = ucontrol->value.integer.value[0];
	int ret = 0;
	unsigned int i;

	if (val < mc->min || val > mc->max)
		return -EINVAL;
	if (mc->invert)
		val = mc->max - val;
	val &= mask;
	for (i = 0; i < regcount; i++) {
		unsigned int regval = (val >> (regwshift * (regcount - i - 1))) &
				      regwmask;
		unsigned int regmask = (mask >> (regwshift * (regcount - i - 1))) &
				       regwmask;
		int err = snd_soc_component_update_bits(component, regbase + i,
							regmask, regval);

		if (err < 0)
			return err;
		if (err > 0)
			ret = err;
	}

	return ret;
}
```

The strobe pair turns a single bit into a momentary action. [`snd_soc_get_strobe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L800) is the read half and reports the bit at [`shift`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) as an enumerated item, XORing in [`invert`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) so the active level reads back as item 1; it shares [`snd_soc_info_enum_double()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L39) for its info callback because it presents a two-item menu rather than a slider:

```c
/* sound/soc/soc-ops.c:800 */
int snd_soc_get_strobe(struct snd_kcontrol *kcontrol,
		       struct snd_ctl_elem_value *ucontrol)
{
	struct snd_soc_component *component = snd_kcontrol_chip(kcontrol);
	struct soc_mixer_control *mc =
		(struct soc_mixer_control *)kcontrol->private_value;
	unsigned int invert = mc->invert != 0;
	unsigned int mask = BIT(mc->shift);
	unsigned int val;

	val = snd_soc_component_read(component, mc->reg);
	val &= mask;

	if (mc->shift != 0 && val != 0)
		val = val >> mc->shift;

	ucontrol->value.enumerated.item[0] = val ^ invert;

	return 0;
}
```

A momentary action uses [`snd_soc_put_strobe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L832), which writes a bit to its active level and then immediately back, producing a one-pass pulse from a single control write:

```c
/* sound/soc/soc-ops.c:832 */
int snd_soc_put_strobe(struct snd_kcontrol *kcontrol,
		       struct snd_ctl_elem_value *ucontrol)
{
	struct snd_soc_component *component = snd_kcontrol_chip(kcontrol);
	struct soc_mixer_control *mc =
		(struct soc_mixer_control *)kcontrol->private_value;
	unsigned int strobe = ucontrol->value.enumerated.item[0] != 0;
	unsigned int invert = mc->invert != 0;
	unsigned int mask = BIT(mc->shift);
	unsigned int val1 = (strobe ^ invert) ? mask : 0;
	unsigned int val2 = (strobe ^ invert) ? 0 : mask;
	int ret;

	ret = snd_soc_component_update_bits(component, mc->reg, mask, val1);
	if (ret < 0)
		return ret;

	return snd_soc_component_update_bits(component, mc->reg, mask, val2);
}
```

The multi-register read assembles its value the way this figure stacks it, each register from the most significant at regbase shifted into place and ORed, then masked to nbits and sign-filled when min is negative:

```
    snd_soc_get_xr_sx: regcount registers → one nbits value
    ─────────────────────────────────────────────────────────

    regwshift = component->val_bytes * 8   (one register width)

      regbase+0      regbase+1            regbase+regcount-1
    ┌────────────┐ ┌────────────┐  . . . ┌────────────┐
    │ most-sig   │ │            │        │ least-sig  │
    │ reg word   │ │ reg word   │        │ reg word   │
    └─────┬──────┘ └─────┬──────┘        └─────┬──────┘
          │              │                     │
          ▼              ▼                     ▼
       << regwshift*(regcount-1)   . . .   << 0
          └──────────────┴──────────┬──────────┘
                                    ▼  OR-accumulate, then & mask
                       one long val  (mask = GENMASK(nbits-1, 0))
                                    ▼
              if min < 0 and val > max:  set high bits ~mask
              if invert:                 val = max - val
```

### Byte controls move a raw register block through regmap

A byte control carries an opaque block rather than a single field, so its private data is a [`struct soc_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1248) naming a [`base`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1248) register, a [`num_regs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1248) count, and an optional [`mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1248) of bits in the first register the control must not disturb:

```c
/* include/sound/soc.h:1248 */
struct soc_bytes {
	int base;
	int num_regs;
	u32 mask;
};
```

The byte [`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) callback reports a byte type rather than an integer, with the element count fixed at [`num_regs`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1248) times the component register width, so the [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) and [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) work in whole registers:

```c
/* sound/soc/soc-ops.c:512 */
int snd_soc_bytes_info(struct snd_kcontrol *kcontrol,
		       struct snd_ctl_elem_info *uinfo)
{
	struct snd_soc_component *component = snd_kcontrol_chip(kcontrol);
	struct soc_bytes *params = (void *)kcontrol->private_value;

	uinfo->type = SNDRV_CTL_ELEM_TYPE_BYTES;
	uinfo->count = params->num_regs * component->val_bytes;

	return 0;
}
```

[`snd_soc_bytes_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L525) bypasses the per-field [`snd_soc_component_read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L671) path the volsw handlers use and reads the whole region in one [`regmap_raw_read()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h), then clears any [`mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1248) bits in the first register so the masked control reports a stable value:

```c
/* sound/soc/soc-ops.c:525 */
int snd_soc_bytes_get(struct snd_kcontrol *kcontrol,
		      struct snd_ctl_elem_value *ucontrol)
{
	struct snd_soc_component *component = snd_kcontrol_chip(kcontrol);
	struct soc_bytes *params = (void *)kcontrol->private_value;
	int ret;

	if (component->regmap)
		ret = regmap_raw_read(component->regmap, params->base,
				      ucontrol->value.bytes.data,
				      params->num_regs * component->val_bytes);
	else
		ret = -EINVAL;
	...
}
```

[`snd_soc_bytes_put()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L562) copies the incoming bytes, and when a [`mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1248) is present it reads the first register back and merges the preserved bits into the copy before a single [`regmap_raw_write()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/regmap.h), so the read-modify-write that one masked register needs does not corrupt the rest of the block:

```c
/* sound/soc/soc-ops.c:562 */
int snd_soc_bytes_put(struct snd_kcontrol *kcontrol,
		      struct snd_ctl_elem_value *ucontrol)
{
	struct snd_soc_component *component = snd_kcontrol_chip(kcontrol);
	struct soc_bytes *params = (void *)kcontrol->private_value;
	unsigned int val, mask;
	int ret, len;

	if (!component->regmap || !params->num_regs)
		return -EINVAL;

	len = params->num_regs * component->val_bytes;

	void *data __free(kfree) = kmemdup(ucontrol->value.bytes.data, len,
					   GFP_KERNEL | GFP_DMA);
	...
	return regmap_raw_write(component->regmap, params->base, data, len);
}
```

### TLV byte controls route reads and writes to driver callbacks

A TLV byte control is the variant a driver uses when the block is too large for the inline value buffer or needs to pass through the driver, so its private data is a [`struct soc_bytes_ext`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1254) that replaces the register coordinates with a [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1254) byte count and a pair of driver [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1254) and [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1254) callbacks:

```c
/* include/sound/soc.h:1254 */
struct soc_bytes_ext {
	int max;
#ifdef CONFIG_SND_SOC_TOPOLOGY
	struct snd_soc_dobj dobj;
#endif
	/* used for TLV byte control */
	int (*get)(struct snd_kcontrol *kcontrol, unsigned int __user *bytes,
			unsigned int size);
	int (*put)(struct snd_kcontrol *kcontrol, const unsigned int __user *bytes,
			unsigned int size);
};
```

Its [`info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) callback reports the byte type and the [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1254) length, mirroring the plain byte info but reading the count from the ext struct:

```c
/* sound/soc/soc-ops.c:634 */
int snd_soc_bytes_info_ext(struct snd_kcontrol *kcontrol,
			   struct snd_ctl_elem_info *ucontrol)
{
	struct soc_bytes_ext *params = (void *)kcontrol->private_value;

	ucontrol->type = SNDRV_CTL_ELEM_TYPE_BYTES;
	ucontrol->count = params->max;

	return 0;
}
```

Unlike every other family on this page, a TLV byte control has no [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47)/[`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L47) pair at all; the value travels through the control core's TLV channel, and [`snd_soc_bytes_tlv_callback()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L646) is the single entry point that dispatches a read or write to the matching driver callback, clamping the transfer to [`max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1254):

```c
/* sound/soc/soc-ops.c:646 */
int snd_soc_bytes_tlv_callback(struct snd_kcontrol *kcontrol, int op_flag,
			       unsigned int size, unsigned int __user *tlv)
{
	struct soc_bytes_ext *params = (void *)kcontrol->private_value;
	unsigned int count = size < params->max ? size : params->max;
	int ret = -ENXIO;

	switch (op_flag) {
	case SNDRV_CTL_TLV_OP_READ:
		if (params->get)
			ret = params->get(kcontrol, tlv, count);
		break;
	case SNDRV_CTL_TLV_OP_WRITE:
		if (params->put)
			ret = params->put(kcontrol, tlv, count);
		break;
	}

	return ret;
}
```

### Limiting an existing volume

A machine driver caps a codec volume it does not own with [`snd_soc_limit_volume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L488), which looks up the control by name through [`snd_soc_card_get_kcontrol()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L22), sets [`platform_max`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) when the new cap fits inside the hardware range, and immediately re-clamps the current value:

```c
/* sound/soc/soc-ops.c:488 */
int snd_soc_limit_volume(struct snd_soc_card *card, const char *name, int max)
{
	struct snd_kcontrol *kctl;
	int ret = -EINVAL;

	/* Sanity check for name and max */
	if (unlikely(!name || max <= 0))
		return -EINVAL;

	kctl = snd_soc_card_get_kcontrol(card, name);
	if (kctl) {
		struct soc_mixer_control *mc =
			(struct soc_mixer_control *)kctl->private_value;

		if (max <= mc->max - mc->min) {
			mc->platform_max = max;
			ret = snd_soc_clip_to_platform_max(kctl);
		}
	}

	return ret;
}
```

[`snd_soc_clip_to_platform_max()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L448) reuses the control's own [`get`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) and [`put`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/control.h#L70) to read the current value, cap each channel, and write it back, so a volume already louder than the new limit is brought down at once. After this call [`soc_info_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L209) reports the reduced maximum and [`soc_mixer_valid_ctl()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L181) rejects any later write above it.

### Worked example: rt722-sdca custom gain handlers

The Realtek RT722 is an SDCA codec reached over SoundWire on x86 ACPI platforms, and its volume controls cannot use the generic volsw put because an SDCA gain is encoded in a vendor-specific way and reached over two per-channel Control registers. The codec declares the controls with [`SOC_DOUBLE_R_EXT_TLV`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L282), which keeps [`snd_soc_info_volsw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L332) for the info callback and the dB TLV array for userspace, while substituting [`rt722_sdca_set_gain_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L419) and [`rt722_sdca_set_gain_put()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L348) for the value path:

```c
/* sound/soc/codecs/rt722-sdca.c:697 */
static const struct snd_kcontrol_new rt722_sdca_controls[] = {
	/* Headphone playback settings */
	SOC_DOUBLE_R_EXT_TLV("FU05 Playback Volume",
		SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT722_SDCA_ENT_USER_FU05,
			RT722_SDCA_CTL_FU_VOLUME, CH_L),
		SDW_SDCA_CTL(FUNC_NUM_JACK_CODEC, RT722_SDCA_ENT_USER_FU05,
			RT722_SDCA_CTL_FU_VOLUME, CH_R), 0, 0x57, 0,
		rt722_sdca_set_gain_get, rt722_sdca_set_gain_put, out_vol_tlv),
	...
};
```

The custom put recovers the same [`struct soc_mixer_control`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) the generic handler would, reads both channel registers, encodes the userspace value into the codec's gain format (a boost path when [`shift`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1231) is 8, an offset path otherwise), and returns the same change flag the generic put returns by reporting 1 only when a register value differs:

```c
/* sound/soc/codecs/rt722-sdca.c:348 */
static int rt722_sdca_set_gain_put(struct snd_kcontrol *kcontrol,
		struct snd_ctl_elem_value *ucontrol)
{
	struct snd_soc_component *component = snd_kcontrol_chip(kcontrol);
	struct soc_mixer_control *mc =
		(struct soc_mixer_control *)kcontrol->private_value;
	struct rt722_sdca_priv *rt722 = snd_soc_component_get_drvdata(component);
	unsigned int read_l, read_r, gain_l_val, gain_r_val;
	unsigned int adc_vol_flag = 0, changed = 0;
	unsigned int lvalue, rvalue;
	const unsigned int interval_offset = 0xc0;
	const unsigned int tendB = 0xa00;
	...
	if (lvalue != gain_l_val || rvalue != gain_r_val)
		changed = 1;
	else
		return 0;

	/* Lch*/
	regmap_write(rt722->regmap, mc->reg, gain_l_val);

	/* Rch */
	regmap_write(rt722->regmap, mc->rreg, gain_r_val);
	...
	return changed;
}
```

The matching [`rt722_sdca_set_gain_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L419) runs the inverse decode and fills both channels of `ucontrol->value.integer.value`. The EXT family changes only which get and put run; the registration, the info callback, the TLV channel, and the teardown are identical to a generic control, so a driver pays the cost of a custom handler only on the read and write path where the hardware encoding demands it. The same pattern carries SDCA gain encoding into the generic core for codecs that opt into it instead through the [`sdca_q78`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1242) bit and [`sdca_soc_q78_ctl_to_reg()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-ops.c#L129).
