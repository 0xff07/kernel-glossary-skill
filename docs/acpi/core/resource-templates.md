# Resource Templates and struct acpi_resource

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A `ResourceTemplate () {}` block in ASL compiles into a Buffer holding a stream of byte-encoded resource descriptors, and each descriptor crosses three kernel representations on its way to a driver. The raw bytes are overlaid by the packed structs of [`union aml_resource`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L509), ACPICA's table-driven converter [`acpi_rs_convert_aml_to_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsmisc.c#L35) executes a [`struct acpi_rsconvert_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acresrc.h#L32) script that rewrites each one into a [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678) record whose `type` selects one member of [`union acpi_resource_data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L639), and the Linux layer in [`drivers/acpi/resource.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c) turns the members that have a generic analog into [`struct resource`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L22) objects while gpiolib-acpi, the I2C core, the SPI core, and serdev read the connector members straight out of the union. This page catalogs that mapping macro by macro, pairing every ASL macro with the AML tag byte it compiles to (the [`ACPI_RESOURCE_NAME_GPIO`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1136) family of constants), the decoded [`ACPI_RESOURCE_TYPE_GPIO`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L626) family of type values, the union member the payload lands in, and the consumer code that reads it.

```
    ASL macro to AML cell to union acpi_resource_data member
    ─────────────────────────────────────────────────────────

    ASL macro              AML descriptor cell           union member
    ─────────              ───────────────────           ────────────

    Memory32Fixed()  ───▶  ┌─────────────────────┐  ───▶  .fixed_memory32
                           │ tag 0x86 (large)    │        ACPI_RESOURCE_TYPE_
                           │ RW flag, base, len  │        FIXED_MEMORY32 = 10
                           ├─────────────────────┤
    Interrupt()      ───▶  │ tag 0x89 (large)    │  ───▶  .extended_irq
                           │ flags, count, INTs, │        ACPI_RESOURCE_TYPE_
                           │ optional source     │        EXTENDED_IRQ = 15
                           ├─────────────────────┤
    GpioInt()        ───▶  │ tag 0x8C (large)    │  ───▶  .gpio
    GpioIo()               │ int_flags, pin      │        ACPI_RESOURCE_TYPE_
                           │ table, source path  │        GPIO = 17
                           ├─────────────────────┤
    I2cSerialBus()   ───▶  │ tag 0x8E (large)    │  ───▶  .i2c_serial_bus
                           │ bus-type byte = 1,  │        ACPI_RESOURCE_TYPE_
                           │ speed, address      │        SERIAL_BUS = 19
                           ├─────────────────────┤
    End Tag (auto)   ───▶  │ tag 0x79 (small)    │  ───▶  .end_tag
                           │ checksum byte       │        ACPI_RESOURCE_TYPE_
                           └─────────────────────┘        END_TAG = 7

    (one Buffer is one contiguous stream of cells; the tag byte selects
     the conversion table, the table fills exactly one union member, and
     the serial-bus cell dispatches a second time on its bus-type byte)
```

## SUMMARY

The ACPI specification defines two descriptor encodings in section 6.4. A small item packs its type into bits 6:3 of the first byte and its payload length into bits 2:0, a large item sets bit 7 and keeps the type in bits 6:0 with a 16-bit little-endian length in the next two bytes, and every template ends with the small End Tag item whose tag byte is 0x79. The kernel mirrors the tag values one for one in the ACPICA-private constants [`ACPI_RESOURCE_NAME_LARGE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1097), [`ACPI_RESOURCE_NAME_SMALL_MASK`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1100), and the per-descriptor names from [`ACPI_RESOURCE_NAME_IRQ`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1108) (0x20) through [`ACPI_RESOURCE_NAME_CLOCK_INPUT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1143) (0x93), and it mirrors the byte layouts in the packed overlay structs of [`drivers/acpi/acpica/amlresrc.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h) such as [`struct aml_resource_gpio`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L281) and [`struct aml_resource_extended_irq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L261). The ASL side of the same mapping is the macro catalog of section 19.6, where `Memory32Fixed`, `Interrupt`, `GpioInt`, `I2cSerialBus`, and the rest each emit exactly one descriptor kind, and iASL appends the End Tag automatically per section 19.3.3.

Decoding is table driven. [`acpi_ut_validate_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utresrc.c#L266) checks each tag byte against [`acpi_gbl_resource_aml_sizes[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utresrc.c#L19) and computes a dispatch index (small tags shift right by 3, large tags subtract 0x70), [`acpi_rs_convert_aml_to_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rslist.c#L30) uses that index to pick a conversion table from [`acpi_gbl_get_resource_dispatch[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsinfo.c#L57) (serial-bus descriptors dispatch a second time on their bus-type byte through [`acpi_gbl_convert_resource_serial_bus_dispatch[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsinfo.c#L103)), and [`acpi_rs_convert_aml_to_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsmisc.c#L35) interprets the chosen [`struct acpi_rsconvert_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acresrc.h#L32) opcode script entry by entry, producing one [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678) record per descriptor. Each record is the fixed `type`/`length` header plus one member of [`union acpi_resource_data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L639), the `type` value comes from the [`ACPI_RESOURCE_TYPE_IRQ`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L609) (0) through [`ACPI_RESOURCE_TYPE_CLOCK_INPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L634) (25) enumeration that is decoupled from the AML tag values, and [`ACPI_NEXT_RESOURCE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L694) steps from record to record using the per-record `length` that the conversion grew to cover variable pin tables, interrupt arrays, and resource-source strings.

The Linux consumption layer splits in two. For descriptors with a generic analog, [`acpi_dev_get_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1000) runs the per-type converters [`acpi_dev_resource_memory()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L107), [`acpi_dev_resource_io()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L180), [`acpi_dev_resource_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L828), and [`acpi_dev_resource_address_space()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L290), which map union members onto [`struct resource`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L22) start/end/flags with [`acpi_dev_irq_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L342) translating triggering/polarity/shareable/wake into `IORESOURCE_IRQ_*` bits. Connector descriptors keep their full payloads only in the union, so their consumers read it directly. [`acpi_gpio_get_irq_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L175) and [`acpi_populate_gpio_lookup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L686) read [`struct acpi_resource_gpio`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L355), [`i2c_acpi_get_i2c_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-acpi.c#L55) reads [`struct acpi_resource_i2c_serialbus`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L422), [`serdev_acpi_get_uart_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/tty/serdev/core.c#L572) reads [`struct acpi_resource_uart_serialbus`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L463), [`acpi_spi_add_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/spi/spi.c#L2809) reads [`struct acpi_resource_spi_serialbus`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L433), and [`acpi_dma_parse_fixed_dma()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/dma/acpi-dma.c#L326) reads [`struct acpi_resource_fixed_dma`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L186). The PnP ACPI parser in [`pnpacpi_allocated_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L164) and [`pnpacpi_option_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L454) exercises both styles across nearly the whole catalog in two functions.

## SPECIFICATIONS

- ACPI Specification, section 6.4: Resource Data Types for ACPI
- ACPI Specification, section 6.4.1: ASL Macros for Resource Descriptors
- ACPI Specification, section 6.4.2: Small Resource Data Type
- ACPI Specification, section 6.4.3: Large Resource Data Type
- ACPI Specification, section 6.4.3.5: Address Space Resource Descriptors (cited by the comment in [`acpi_decode_space()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L207))
- ACPI Specification, section 6.4.3.8.2.4: Camera Serial Interface (CSI-2) Connection Resource Descriptor (cited by [`drivers/acpi/mipi-disco-img.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/mipi-disco-img.c))
- ACPI Specification 1.0b, section 6.4.2.8: End Tag (cited by the comment in [`acpi_rs_convert_end_tag[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsio.c#L132))
- ACPI Specification, section 19.3.3: ASL Resource Templates
- ACPI Specification, section 19.6: ASL Operator Reference (one macro per descriptor kind)

## LINUX KERNEL

### Decoded resource model (include/acpi/acrestyp.h)

- [`'\<struct acpi_resource\>':'include/acpi/acrestyp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678): decoded record, `type`/`length` header plus payload union
- [`'\<union acpi_resource_data\>':'include/acpi/acrestyp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L639): master payload union, one member per descriptor kind
- [`'\<struct acpi_resource_fixed_memory32\>':'include/acpi/acrestyp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L235): Memory32Fixed payload, write protect plus base and length
- [`'\<struct acpi_resource_extended_irq\>':'include/acpi/acrestyp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L333): Interrupt payload, mode bytes plus flexible GSI array
- [`'\<struct acpi_resource_gpio\>':'include/acpi/acrestyp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L355): GpioInt/GpioIo payload, mode bytes, pin table, controller path
- [`'\<struct acpi_resource_common_serialbus\>':'include/acpi/acrestyp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L407): shared serial-bus header carried by all four bus payloads
- [`'\<struct acpi_resource_i2c_serialbus\>':'include/acpi/acrestyp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L422): I2cSerialBus payload, access mode, slave address, speed
- [`'\<struct acpi_resource_source\>':'include/acpi/acrestyp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L269): ResourceSource index/length/string triple used by GPIO, serial bus, and address descriptors
- [`ACPI_NEXT_RESOURCE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L694): steps to the next decoded record by adding `length`
- [`ACPI_RS_SIZE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L690): header size plus payload struct size, the minimum record length

### Raw AML overlays (drivers/acpi/acpica/amlresrc.h, aclocal.h)

- [`'\<union aml_resource\>':'drivers/acpi/acpica/amlresrc.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L509): union of every packed descriptor overlay, cast onto the raw byte stream
- [`'\<struct aml_resource_fixed_memory32\>':'drivers/acpi/acpica/amlresrc.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L206): raw Memory32Fixed layout, tag 0x86
- [`'\<struct aml_resource_extended_irq\>':'drivers/acpi/acpica/amlresrc.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L261): raw Interrupt layout, tag 0x89
- [`'\<struct aml_resource_gpio\>':'drivers/acpi/acpica/amlresrc.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L281): raw GpioInt/GpioIo layout, tag 0x8C, offset-addressed pin table and source string
- [`'\<struct aml_resource_i2c_serialbus\>':'drivers/acpi/acpica/amlresrc.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L346): raw I2cSerialBus layout, tag 0x8E with bus type 1
- [`AML_RESOURCE_SMALL_HEADER_COMMON`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L115): one tag byte, the entire small-item header
- [`AML_RESOURCE_LARGE_HEADER_COMMON`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L174): tag byte plus 16-bit `resource_length`, the large-item header
- [`ACPI_RESOURCE_NAME_LARGE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1097): bit 7 marker separating the two encodings
- [`ACPI_RESOURCE_NAME_GPIO`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1136): the 0x8C GPIO tag, one entry of the 0x81-0x93 large-name block
- [`'\<acpi_gbl_resource_aml_sizes\>':'drivers/acpi/acpica/utresrc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utresrc.c#L19): minimum raw size per dispatch index, used to validate descriptor lengths

### Conversion machinery (drivers/acpi/acpica)

- [`'\<struct acpi_rsconvert_info\>':'drivers/acpi/acpica/acresrc.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acresrc.h#L32): one conversion-script entry, opcode plus two offsets and a value
- [`ACPI_RS_OFFSET`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acresrc.h#L85): offset of a field inside [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678), the script's destination side
- [`AML_OFFSET`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acresrc.h#L86): offset of a field inside [`union aml_resource`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L509), the script's source side
- [`ACPI_RSC_TABLE_SIZE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acresrc.h#L83): entry count stored in the table's first entry
- [`'\<acpi_rs_convert_aml_to_resource\>':'drivers/acpi/acpica/rsmisc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsmisc.c#L35): opcode interpreter that executes one conversion table
- [`'\<acpi_rs_convert_aml_to_resources\>':'drivers/acpi/acpica/rslist.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rslist.c#L30): per-descriptor dispatch callback invoked once per stream cell
- [`'\<acpi_ut_walk_aml_resources\>':'drivers/acpi/acpica/utresrc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utresrc.c#L141): walks the raw byte stream and invokes the callback per descriptor
- [`'\<acpi_ut_validate_resource\>':'drivers/acpi/acpica/utresrc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utresrc.c#L266): validates a tag byte and computes the dispatch index
- [`'\<acpi_gbl_get_resource_dispatch\>':'drivers/acpi/acpica/rsinfo.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsinfo.c#L57): dispatch index to conversion table, AML-to-resource direction
- [`'\<acpi_gbl_convert_resource_serial_bus_dispatch\>':'drivers/acpi/acpica/rsinfo.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsinfo.c#L103): second-level dispatch on the serial-bus type byte
- [`'\<acpi_rs_convert_gpio\>':'drivers/acpi/acpica/rsserial.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsserial.c#L20): 18-entry script for GpioInt/GpioIo
- [`'\<acpi_rs_convert_ext_irq\>':'drivers/acpi/acpica/rsirq.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsirq.c#L156): 10-entry script for Interrupt
- [`'\<acpi_rs_convert_fixed_memory32\>':'drivers/acpi/acpica/rsmemory.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsmemory.c#L84): 4-entry script for Memory32Fixed
- [`'\<acpi_rs_convert_i2c_serial_bus\>':'drivers/acpi/acpica/rsserial.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsserial.c#L318): 17-entry script for I2cSerialBus
- [`'\<acpi_rs_convert_end_tag\>':'drivers/acpi/acpica/rsio.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsio.c#L132): 2-entry script for the End Tag
- [`'\<acpi_resource_to_address64\>':'drivers/acpi/acpica/rsxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L332): normalizes the 16/32/64-bit address payloads into one layout

### Linux conversion layer (drivers/acpi/resource.c)

- [`'\<acpi_dev_get_resources\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1000): walks `_CRS` and converts records into a [`struct resource_entry`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/resource_ext.h#L23) list
- [`'\<acpi_dev_resource_memory\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L107): Memory24/Memory32/Memory32Fixed payloads to [`IORESOURCE_MEM`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L41)
- [`'\<acpi_dev_resource_io\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L180): IO/FixedIO payloads to [`IORESOURCE_IO`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L40)
- [`'\<acpi_dev_resource_interrupt\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L828): IRQ/Interrupt payloads to [`IORESOURCE_IRQ`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L43), one GSI per call index
- [`'\<acpi_dev_resource_address_space\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L290): Word/DWord/QWord address payloads to memory, IO, or bus resources
- [`'\<acpi_dev_resource_ext_address_space\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L319): ExtendedSpace payload through the same decoder
- [`'\<acpi_dev_irq_flags\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L342): triggering/polarity/shareable/wake bytes to `IORESOURCE_IRQ_*` bits
- [`'\<acpi_dev_get_irq_type\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L368): the same two bytes to `IRQ_TYPE_*` values for irqchip configuration

### Direct union readers (connector consumers)

- [`'\<acpi_gpio_get_irq_resource\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L175): type filter returning the [`struct acpi_resource_gpio`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L355) payload of a GpioInt record
- [`'\<acpi_populate_gpio_lookup\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L686): preproc callback that reads pin table, polarity, triggering, and bias out of the GPIO payload
- [`'\<acpi_gpio_resource_lookup\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L742): runs the `_CRS` walk that feeds the populate callback
- [`'\<struct acpi_gpio_lookup\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L679): walk context pairing index parameters with the result descriptor
- [`'\<struct acpi_gpio_info\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L83): captured GpioInt attributes (polarity, triggering, debounce, wake)
- [`'\<acpi_dev_gpio_irq_wake_get_by\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L996): translates the n-th GpioInt into a Linux IRQ and programs its trigger type
- [`'\<acpi_dev_gpio_irq_get\>':'include/linux/acpi.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1324): index-only wrapper drivers call from probe
- [`'\<acpi_gpiochip_alloc_event\>':'drivers/gpio/gpiolib-acpi-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343): `_AEI` walk callback that arms `_Exx`/`_Lxx`/`_EVT` GPIO event handlers
- [`'\<i2c_acpi_get_i2c_resource\>':'drivers/i2c/i2c-core-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-acpi.c#L55): type-and-subtype filter for I2cSerialBus payloads
- [`'\<i2c_acpi_fill_info\>':'drivers/i2c/i2c-core-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-acpi.c#L104): preproc that copies slave address, speed, and addressing mode into board info
- [`'\<serdev_acpi_get_uart_resource\>':'drivers/tty/serdev/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/tty/serdev/core.c#L572): type-and-subtype filter for UartSerialBus payloads
- [`'\<acpi_serdev_parse_resource\>':'drivers/tty/serdev/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/tty/serdev/core.c#L589): resolves the UART connector's controller path to a handle
- [`'\<acpi_spi_add_resource\>':'drivers/spi/spi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/spi/spi.c#L2809): reads chip select, speed, word size, and SPI mode out of SpiSerialBus
- [`'\<acpi_dma_parse_fixed_dma\>':'drivers/dma/acpi-dma.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/dma/acpi-dma.c#L326): reads request line and channel out of FixedDMA
- [`'\<pnpacpi_allocated_resource\>':'drivers/pnp/pnpacpi/rsparser.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L164): `_CRS` callback mixing the generic converters with raw DMA/vendor/GPIO reads
- [`'\<pnpacpi_option_resource\>':'drivers/pnp/pnpacpi/rsparser.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L454): `_PRS` callback reading raw union members for every legacy descriptor family

## KERNEL DOCUMENTATION

- [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst): how connector descriptors (I2cSerialBus, SpiSerialBus, UartSerialBus, GpioInt, FixedDMA) steer device enumeration onto the right bus
- [`Documentation/firmware-guide/acpi/gpio-properties.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/gpio-properties.rst): pairing GpioInt/GpioIo descriptors with `_DSD` names and how polarity in the descriptor interacts with the property cells
- [`Documentation/PCI/acpi-info.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/PCI/acpi-info.rst): address-space descriptors as host bridge windows, the producer/consumer distinction
- [`Documentation/driver-api/acpi/linuxized-acpica.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/acpi/linuxized-acpica.rst): maintenance model of the imported ACPICA code that owns the descriptor tables

## OTHER SOURCES

- [ACPI Specification 6.5, chapter 6: Device Configuration](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html)
- [ACPI Specification 6.5, chapter 19: ASL Reference](https://uefi.org/specs/ACPI/6.5/19_ASL_Reference.html)
- [Commit e0fe0a8d4ed5 ("ACPI 5.0: Support for all new resource descriptors")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=e0fe0a8d4ed5474261d0ee1452f5d9ae77236958)
- [Commit 9cea6249c915 ("ACPICA: Resources: Split interrupt share/wake bits into two fields.")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=9cea6249c9154a7d0b322a226261697f947692ad)
- [Commit 8e345c991c8c ("ACPI: Centralized processing of ACPI device resources")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=8e345c991c8c7a3c081199ef77deada79e37618a)
- [Commit 907ddf89d0bb ("i2c / ACPI: add ACPI enumeration support")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=907ddf89d0bb7f57e1e21485900e6564a1ab512a)

## INTERFACES

### Small items (tag bits 6:3, length bits 2:0)

- `IRQ()` / `IRQNoFlags()`: tag [`ACPI_RESOURCE_NAME_IRQ`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1108) 0x20, decoded as [`ACPI_RESOURCE_TYPE_IRQ`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L609) (0) into `irq` ([`struct acpi_resource_irq`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L138)) by [`acpi_rs_get_irq[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsirq.c#L20)
- `DMA()`: tag [`ACPI_RESOURCE_NAME_DMA`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1109) 0x28, decoded as [`ACPI_RESOURCE_TYPE_DMA`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L610) (1) into `dma` ([`struct acpi_resource_dma`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L151)) by [`acpi_rs_convert_dma[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsirq.c#L214)
- `StartDependentFn()` / `StartDependentFnNoPri()`: tag [`ACPI_RESOURCE_NAME_START_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1110) 0x30, decoded as [`ACPI_RESOURCE_TYPE_START_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L611) (2) into `start_dpf` ([`struct acpi_resource_start_dependent`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L162)) by [`acpi_rs_get_start_dpf[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsio.c#L153)
- `EndDependentFn()`: tag [`ACPI_RESOURCE_NAME_END_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1111) 0x38, decoded as [`ACPI_RESOURCE_TYPE_END_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L612) (3), header-only record via [`acpi_rs_convert_end_dpf[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsio.c#L116)
- `IO()`: tag [`ACPI_RESOURCE_NAME_IO`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1112) 0x40, decoded as [`ACPI_RESOURCE_TYPE_IO`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L613) (4) into `io` ([`struct acpi_resource_io`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L173)) by [`acpi_rs_convert_io[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsio.c#L20)
- `FixedIO()`: tag [`ACPI_RESOURCE_NAME_FIXED_IO`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1113) 0x48, decoded as [`ACPI_RESOURCE_TYPE_FIXED_IO`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L614) (5) into `fixed_io` ([`struct acpi_resource_fixed_io`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L181)) by [`acpi_rs_convert_fixed_io[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsio.c#L56)
- `FixedDMA()`: tag [`ACPI_RESOURCE_NAME_FIXED_DMA`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1114) 0x50, decoded as [`ACPI_RESOURCE_TYPE_FIXED_DMA`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L627) (18) into `fixed_dma` ([`struct acpi_resource_fixed_dma`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L186)) by [`acpi_rs_convert_fixed_dma[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsirq.c#L250)
- `VendorShort()`: tag [`ACPI_RESOURCE_NAME_VENDOR_SMALL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1118) 0x70, decoded as [`ACPI_RESOURCE_TYPE_VENDOR`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L615) (6) into `vendor` ([`struct acpi_resource_vendor`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L201)) by [`acpi_rs_get_vendor_small[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsmemory.c#L114)
- End Tag (emitted by iASL, no macro): tag [`ACPI_RESOURCE_NAME_END_TAG`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1119) 0x78 (byte 0x79 with length 1), decoded as [`ACPI_RESOURCE_TYPE_END_TAG`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L616) (7) into `end_tag` ([`struct acpi_resource_end_tag`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L215)) by [`acpi_rs_convert_end_tag[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsio.c#L132)

### Large items (tag bit 7 set, 16-bit length)

- `Memory24()`: tag [`ACPI_RESOURCE_NAME_MEMORY24`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1125) 0x81, decoded as [`ACPI_RESOURCE_TYPE_MEMORY24`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L617) (8) into `memory24` ([`struct acpi_resource_memory24`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L219)) by [`acpi_rs_convert_memory24[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsmemory.c#L20)
- `Register()`: tag [`ACPI_RESOURCE_NAME_GENERIC_REGISTER`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1126) 0x82, decoded as [`ACPI_RESOURCE_TYPE_GENERIC_REGISTER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L625) (16) into `generic_reg` ([`struct acpi_resource_generic_register`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L347)) by [`acpi_rs_convert_generic_reg[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsio.c#L84)
- `VendorLong()`: tag [`ACPI_RESOURCE_NAME_VENDOR_LARGE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1128) 0x84, decoded as [`ACPI_RESOURCE_TYPE_VENDOR`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L615) (6) into `vendor_typed` ([`struct acpi_resource_vendor_typed`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L208)) by [`acpi_rs_get_vendor_large[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsmemory.c#L138)
- `Memory32()`: tag [`ACPI_RESOURCE_NAME_MEMORY32`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1129) 0x85, decoded as [`ACPI_RESOURCE_TYPE_MEMORY32`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L618) (9) into `memory32` ([`struct acpi_resource_memory32`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L227)) by [`acpi_rs_convert_memory32[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsmemory.c#L52)
- `Memory32Fixed()`: tag [`ACPI_RESOURCE_NAME_FIXED_MEMORY32`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1130) 0x86, decoded as [`ACPI_RESOURCE_TYPE_FIXED_MEMORY32`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L619) (10) into `fixed_memory32` ([`struct acpi_resource_fixed_memory32`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L235)) by [`acpi_rs_convert_fixed_memory32[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsmemory.c#L84)
- `DWordIO()` / `DWordMemory()` / `DWordSpace()`: tag [`ACPI_RESOURCE_NAME_ADDRESS32`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1131) 0x87, decoded as [`ACPI_RESOURCE_TYPE_ADDRESS32`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L621) (12) into `address32` ([`struct acpi_resource_address32`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L317)) by [`acpi_rs_convert_address32[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsaddr.c#L58)
- `WordIO()` / `WordBusNumber()` / `WordSpace()`: tag [`ACPI_RESOURCE_NAME_ADDRESS16`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1132) 0x88, decoded as [`ACPI_RESOURCE_TYPE_ADDRESS16`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L620) (11) into `address16` ([`struct acpi_resource_address16`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L312)) by [`acpi_rs_convert_address16[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsaddr.c#L20)
- `Interrupt()`: tag [`ACPI_RESOURCE_NAME_EXTENDED_IRQ`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1133) 0x89, decoded as [`ACPI_RESOURCE_TYPE_EXTENDED_IRQ`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L624) (15) into `extended_irq` ([`struct acpi_resource_extended_irq`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L333)) by [`acpi_rs_convert_ext_irq[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsirq.c#L156)
- `QWordIO()` / `QWordMemory()` / `QWordSpace()`: tag [`ACPI_RESOURCE_NAME_ADDRESS64`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1134) 0x8A, decoded as [`ACPI_RESOURCE_TYPE_ADDRESS64`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L622) (13) into `address64` ([`struct acpi_resource_address64`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L322)) by [`acpi_rs_convert_address64[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsaddr.c#L96)
- `ExtendedIO()` / `ExtendedMemory()` / `ExtendedSpace()`: tag [`ACPI_RESOURCE_NAME_EXTENDED_ADDRESS64`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1135) 0x8B, decoded as [`ACPI_RESOURCE_TYPE_EXTENDED_ADDRESS64`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L623) (14) into `ext_address64` ([`struct acpi_resource_extended_address64`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L327)) by [`acpi_rs_convert_ext_address64[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsaddr.c#L134)
- `GpioInt()` / `GpioIo()`: tag [`ACPI_RESOURCE_NAME_GPIO`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1136) 0x8C, decoded as [`ACPI_RESOURCE_TYPE_GPIO`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L626) (17) into `gpio` ([`struct acpi_resource_gpio`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L355)) by [`acpi_rs_convert_gpio[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsserial.c#L20), the two macros separated by `connection_type` ([`ACPI_RESOURCE_GPIO_TYPE_INT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L376) / [`ACPI_RESOURCE_GPIO_TYPE_IO`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L377))
- `PinFunction()`: tag [`ACPI_RESOURCE_NAME_PIN_FUNCTION`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1137) 0x8D, decoded as [`ACPI_RESOURCE_TYPE_PIN_FUNCTION`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L629) (20) into `pin_function` ([`struct acpi_resource_pin_function`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L523)) by [`acpi_rs_convert_pin_function[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsserial.c#L167)
- `I2cSerialBus()` / `I2cSerialBusV2()`: tag [`ACPI_RESOURCE_NAME_SERIAL_BUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1138) 0x8E with bus type [`AML_RESOURCE_I2C_SERIALBUSTYPE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L323) (1), decoded as [`ACPI_RESOURCE_TYPE_SERIAL_BUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L628) (19) into `i2c_serial_bus` ([`struct acpi_resource_i2c_serialbus`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L422), subtype [`ACPI_RESOURCE_SERIAL_TYPE_I2C`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L412)) by [`acpi_rs_convert_i2c_serial_bus[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsserial.c#L318)
- `SpiSerialBus()` / `SpiSerialBusV2()`: same tag 0x8E with bus type 2, decoded as [`ACPI_RESOURCE_TYPE_SERIAL_BUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L628) (19) into `spi_serial_bus` ([`struct acpi_resource_spi_serialbus`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L433), subtype [`ACPI_RESOURCE_SERIAL_TYPE_SPI`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L413)) by [`acpi_rs_convert_spi_serial_bus[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsserial.c#L409)
- `UartSerialBus()` / `UartSerialBusV2()`: same tag 0x8E with bus type 3, decoded as [`ACPI_RESOURCE_TYPE_SERIAL_BUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L628) (19) into `uart_serial_bus` ([`struct acpi_resource_uart_serialbus`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L463), subtype [`ACPI_RESOURCE_SERIAL_TYPE_UART`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L414)) by [`acpi_rs_convert_uart_serial_bus[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsserial.c#L516)
- `Csi2Bus()`: same tag 0x8E with bus type 4, decoded as [`ACPI_RESOURCE_TYPE_SERIAL_BUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L628) (19) into `csi2_serial_bus` ([`struct acpi_resource_csi2_serialbus`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L518), subtype [`ACPI_RESOURCE_SERIAL_TYPE_CSI2`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L415)) by [`acpi_rs_convert_csi2_serial_bus[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsserial.c#L243)
- `PinConfig()`: tag [`ACPI_RESOURCE_NAME_PIN_CONFIG`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1139) 0x8F, decoded as [`ACPI_RESOURCE_TYPE_PIN_CONFIG`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L630) (21) into `pin_config` ([`struct acpi_resource_pin_config`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L535)) by [`acpi_rs_convert_pin_config[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsserial.c#L632)
- `PinGroup()`: tag [`ACPI_RESOURCE_NAME_PIN_GROUP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1140) 0x90, decoded as [`ACPI_RESOURCE_TYPE_PIN_GROUP`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L631) (22) into `pin_group` ([`struct acpi_resource_pin_group`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L574)) by [`acpi_rs_convert_pin_group[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsserial.c#L710)
- `PinGroupFunction()`: tag [`ACPI_RESOURCE_NAME_PIN_GROUP_FUNCTION`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1141) 0x91, decoded as [`ACPI_RESOURCE_TYPE_PIN_GROUP_FUNCTION`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L632) (23) into `pin_group_function` ([`struct acpi_resource_pin_group_function`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L584)) by [`acpi_rs_convert_pin_group_function[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsserial.c#L772)
- `PinGroupConfig()`: tag [`ACPI_RESOURCE_NAME_PIN_GROUP_CONFIG`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1142) 0x92, decoded as [`ACPI_RESOURCE_TYPE_PIN_GROUP_CONFIG`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L633) (24) into `pin_group_config` ([`struct acpi_resource_pin_group_config`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L595)) by [`acpi_rs_convert_pin_group_config[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsserial.c#L849)
- `ClockInput()`: tag [`ACPI_RESOURCE_NAME_CLOCK_INPUT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1143) 0x93, decoded as [`ACPI_RESOURCE_TYPE_CLOCK_INPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L634) (25) into `clock_input` ([`struct acpi_resource_clock_input`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L548)) by [`acpi_rs_convert_clock_input[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsserial.c#L118)

## DETAILS

### A ResourceTemplate compiles to a tagged descriptor Buffer

The following SSDT fragment, taken from the spec-style sensor example, declares an I2C device whose `_CRS` template exercises five descriptor encodings at once, two small items (FixedDMA and the compiler-appended End Tag) and three large items (Memory32Fixed, Interrupt, and the GpioInt plus I2cSerialBus connectors):

```asl
Device (\_SB.PCI0.I2C1.TMP0)
{
    Name (_HID, "PRP0001")
    Name (_UID, 0)
    Name (_CRS, ResourceTemplate ()
    {
        Memory32Fixed (ReadWrite, 0xFED00000, 0x00000400)
        Interrupt (ResourceConsumer, Level, ActiveLow, Exclusive) { 0x20 }
        FixedDMA (0x0018, 0x0004, Width32bit, )
        I2cSerialBus (0x48, ControllerInitiated, 400000,
                      AddressingMode7Bit, "\\_SB.PCI0.I2C1",
                      0x00, ResourceConsumer, , Exclusive,)
        GpioInt (Level, ActiveLow, ExclusiveAndWake, PullUp, 0,
                 "\\_SB.PCI0.GPI0", 0, ResourceConsumer,,) { 12 }
    })                                  // iASL appends the End Tag
}
```

`ResourceTemplate ()` is the section 19.3.3 construct that turns the macro list into a Buffer object, and each macro contributes one byte-encoded descriptor in declaration order, with iASL computing every length field and appending the terminating End Tag. The Buffer is what the kernel actually receives. When code evaluates `_CRS` (or `_PRS`, `_AEI`, `_DMA`) through [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) or [`acpi_get_current_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L167), ACPICA evaluates the named object via [`METHOD_NAME__CRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L21), demands a Buffer-typed result, and hands the raw bytes to the conversion pipeline this page documents. A static `Name (_CRS, ResourceTemplate () {...})` and a `Method (_CRS) {... Return (SBUF)}` form produce the same byte stream, the only difference being that the Method form recomputes it on every evaluation.

### Macro catalog: every layer of the mapping in one table

Each row pairs an ASL macro with the AML tag byte its descriptor starts with, the decoded `type` constant ACPICA assigns, and the [`union acpi_resource_data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L639) member the payload lands in. The tag column names the kernel constant from [`drivers/acpi/acpica/aclocal.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h); for small items the stored byte is the constant plus the 3-bit payload length, which is why templates store the End Tag constant 0x78 as the byte 0x79.

| ASL macro (section 19.6) | AML descriptor (tag) | Decoded type constant | Union member |
|---|---|---|---|
| `IRQ()`, `IRQNoFlags()` | small, [`ACPI_RESOURCE_NAME_IRQ`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1108) 0x20 | [`ACPI_RESOURCE_TYPE_IRQ`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L609) (0) | `irq`, [`struct acpi_resource_irq`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L138) |
| `DMA()` | small, [`ACPI_RESOURCE_NAME_DMA`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1109) 0x28 | [`ACPI_RESOURCE_TYPE_DMA`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L610) (1) | `dma`, [`struct acpi_resource_dma`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L151) |
| `StartDependentFn()`, `StartDependentFnNoPri()` | small, [`ACPI_RESOURCE_NAME_START_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1110) 0x30 | [`ACPI_RESOURCE_TYPE_START_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L611) (2) | `start_dpf`, [`struct acpi_resource_start_dependent`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L162) |
| `EndDependentFn()` | small, [`ACPI_RESOURCE_NAME_END_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1111) 0x38 | [`ACPI_RESOURCE_TYPE_END_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L612) (3) | header-only record |
| `IO()` | small, [`ACPI_RESOURCE_NAME_IO`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1112) 0x40 | [`ACPI_RESOURCE_TYPE_IO`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L613) (4) | `io`, [`struct acpi_resource_io`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L173) |
| `FixedIO()` | small, [`ACPI_RESOURCE_NAME_FIXED_IO`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1113) 0x48 | [`ACPI_RESOURCE_TYPE_FIXED_IO`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L614) (5) | `fixed_io`, [`struct acpi_resource_fixed_io`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L181) |
| `FixedDMA()` | small, [`ACPI_RESOURCE_NAME_FIXED_DMA`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1114) 0x50 | [`ACPI_RESOURCE_TYPE_FIXED_DMA`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L627) (18) | `fixed_dma`, [`struct acpi_resource_fixed_dma`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L186) |
| `VendorShort()` | small, [`ACPI_RESOURCE_NAME_VENDOR_SMALL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1118) 0x70 | [`ACPI_RESOURCE_TYPE_VENDOR`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L615) (6) | `vendor`, [`struct acpi_resource_vendor`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L201) |
| End Tag (implicit) | small, [`ACPI_RESOURCE_NAME_END_TAG`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1119) 0x78, byte 0x79 | [`ACPI_RESOURCE_TYPE_END_TAG`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L616) (7) | `end_tag`, [`struct acpi_resource_end_tag`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L215) |
| `Memory24()` | large, [`ACPI_RESOURCE_NAME_MEMORY24`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1125) 0x81 | [`ACPI_RESOURCE_TYPE_MEMORY24`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L617) (8) | `memory24`, [`struct acpi_resource_memory24`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L219) |
| `Register()` | large, [`ACPI_RESOURCE_NAME_GENERIC_REGISTER`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1126) 0x82 | [`ACPI_RESOURCE_TYPE_GENERIC_REGISTER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L625) (16) | `generic_reg`, [`struct acpi_resource_generic_register`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L347) |
| `VendorLong()` | large, [`ACPI_RESOURCE_NAME_VENDOR_LARGE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1128) 0x84 | [`ACPI_RESOURCE_TYPE_VENDOR`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L615) (6) | `vendor_typed`, [`struct acpi_resource_vendor_typed`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L208) |
| `Memory32()` | large, [`ACPI_RESOURCE_NAME_MEMORY32`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1129) 0x85 | [`ACPI_RESOURCE_TYPE_MEMORY32`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L618) (9) | `memory32`, [`struct acpi_resource_memory32`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L227) |
| `Memory32Fixed()` | large, [`ACPI_RESOURCE_NAME_FIXED_MEMORY32`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1130) 0x86 | [`ACPI_RESOURCE_TYPE_FIXED_MEMORY32`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L619) (10) | `fixed_memory32`, [`struct acpi_resource_fixed_memory32`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L235) |
| `DWordIO()`, `DWordMemory()`, `DWordSpace()` | large, [`ACPI_RESOURCE_NAME_ADDRESS32`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1131) 0x87 | [`ACPI_RESOURCE_TYPE_ADDRESS32`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L621) (12) | `address32`, [`struct acpi_resource_address32`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L317) |
| `WordIO()`, `WordBusNumber()`, `WordSpace()` | large, [`ACPI_RESOURCE_NAME_ADDRESS16`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1132) 0x88 | [`ACPI_RESOURCE_TYPE_ADDRESS16`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L620) (11) | `address16`, [`struct acpi_resource_address16`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L312) |
| `Interrupt()` | large, [`ACPI_RESOURCE_NAME_EXTENDED_IRQ`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1133) 0x89 | [`ACPI_RESOURCE_TYPE_EXTENDED_IRQ`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L624) (15) | `extended_irq`, [`struct acpi_resource_extended_irq`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L333) |
| `QWordIO()`, `QWordMemory()`, `QWordSpace()` | large, [`ACPI_RESOURCE_NAME_ADDRESS64`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1134) 0x8A | [`ACPI_RESOURCE_TYPE_ADDRESS64`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L622) (13) | `address64`, [`struct acpi_resource_address64`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L322) |
| `ExtendedIO()`, `ExtendedMemory()`, `ExtendedSpace()` | large, [`ACPI_RESOURCE_NAME_EXTENDED_ADDRESS64`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1135) 0x8B | [`ACPI_RESOURCE_TYPE_EXTENDED_ADDRESS64`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L623) (14) | `ext_address64`, [`struct acpi_resource_extended_address64`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L327) |
| `GpioInt()`, `GpioIo()` | large, [`ACPI_RESOURCE_NAME_GPIO`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1136) 0x8C | [`ACPI_RESOURCE_TYPE_GPIO`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L626) (17) | `gpio`, [`struct acpi_resource_gpio`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L355) |
| `PinFunction()` | large, [`ACPI_RESOURCE_NAME_PIN_FUNCTION`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1137) 0x8D | [`ACPI_RESOURCE_TYPE_PIN_FUNCTION`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L629) (20) | `pin_function`, [`struct acpi_resource_pin_function`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L523) |
| `I2cSerialBus()`, `I2cSerialBusV2()` | large, [`ACPI_RESOURCE_NAME_SERIAL_BUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1138) 0x8E, bus type 1 | [`ACPI_RESOURCE_TYPE_SERIAL_BUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L628) (19) | `i2c_serial_bus`, [`struct acpi_resource_i2c_serialbus`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L422) |
| `SpiSerialBus()`, `SpiSerialBusV2()` | large, same tag 0x8E, bus type 2 | [`ACPI_RESOURCE_TYPE_SERIAL_BUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L628) (19) | `spi_serial_bus`, [`struct acpi_resource_spi_serialbus`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L433) |
| `UartSerialBus()`, `UartSerialBusV2()` | large, same tag 0x8E, bus type 3 | [`ACPI_RESOURCE_TYPE_SERIAL_BUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L628) (19) | `uart_serial_bus`, [`struct acpi_resource_uart_serialbus`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L463) |
| `Csi2Bus()` | large, same tag 0x8E, bus type 4 | [`ACPI_RESOURCE_TYPE_SERIAL_BUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L628) (19) | `csi2_serial_bus`, [`struct acpi_resource_csi2_serialbus`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L518) |
| `PinConfig()` | large, [`ACPI_RESOURCE_NAME_PIN_CONFIG`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1139) 0x8F | [`ACPI_RESOURCE_TYPE_PIN_CONFIG`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L630) (21) | `pin_config`, [`struct acpi_resource_pin_config`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L535) |
| `PinGroup()` | large, [`ACPI_RESOURCE_NAME_PIN_GROUP`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1140) 0x90 | [`ACPI_RESOURCE_TYPE_PIN_GROUP`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L631) (22) | `pin_group`, [`struct acpi_resource_pin_group`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L574) |
| `PinGroupFunction()` | large, [`ACPI_RESOURCE_NAME_PIN_GROUP_FUNCTION`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1141) 0x91 | [`ACPI_RESOURCE_TYPE_PIN_GROUP_FUNCTION`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L632) (23) | `pin_group_function`, [`struct acpi_resource_pin_group_function`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L584) |
| `PinGroupConfig()` | large, [`ACPI_RESOURCE_NAME_PIN_GROUP_CONFIG`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1142) 0x92 | [`ACPI_RESOURCE_TYPE_PIN_GROUP_CONFIG`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L633) (24) | `pin_group_config`, [`struct acpi_resource_pin_group_config`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L595) |
| `ClockInput()` | large, [`ACPI_RESOURCE_NAME_CLOCK_INPUT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1143) 0x93 | [`ACPI_RESOURCE_TYPE_CLOCK_INPUT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L634) (25) | `clock_input`, [`struct acpi_resource_clock_input`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L548) |

Three rows deserve a note. The two vendor macros share one decoded type value (6) and differ only in the union member that carries the bytes, all four serial-bus macros share one decoded type value (19) and are separated by the `type` field inside the common serial-bus header, and the address-space macro families (Word/DWord/QWord with their IO, Memory, BusNumber, and Space variants) map onto one tag per width because the AML descriptor distinguishes IO, memory, and bus-number ranges by a `resource_type` byte inside the payload rather than by the tag.

### Small and large item headers and the dispatch index

Section 6.4.2 and 6.4.3 define the two header shapes, and the kernel encodes both the field masks and every assigned tag value as constants in the ACPICA-private header:

```
    Descriptor header byte layout (spec sections 6.4.2 and 6.4.3)
    ──────────────────────────────────────────────────────────────

    Small item, byte 0:
       bit:    7         6:3               2:0
              ┌────┬────────────────┬───────────────┐
              │ 0  │   item name    │  data length  │
              └────┴────────────────┴───────────────┘
       End Tag byte 0x79 = name 0x0F << 3 | length 1 (checksum byte)
       dispatch index = (byte0 & 0x78) >> 3          (0x00..0x0F)

    Large item, bytes 0..2:
       bit:    7         6:0                bytes 1..2 (little endian)
              ┌────┬────────────────┐      ┌─────────────────────────┐
              │ 1  │   item name    │      │  resource_length (u16)  │
              └────┴────────────────┘      └─────────────────────────┘
       GpioInt tag byte = 0x8C; resource_length excludes the 3 header bytes
       dispatch index = byte0 - 0x70               (0x80..0x93 → 0x10..0x23)
```

```c
/* drivers/acpi/acpica/aclocal.h:1095 */
/* Resource descriptor types and masks */

#define ACPI_RESOURCE_NAME_LARGE                0x80
#define ACPI_RESOURCE_NAME_SMALL                0x00

#define ACPI_RESOURCE_NAME_SMALL_MASK           0x78	/* Bits 6:3 contain the type */
#define ACPI_RESOURCE_NAME_SMALL_LENGTH_MASK    0x07	/* Bits 2:0 contain the length */
#define ACPI_RESOURCE_NAME_LARGE_MASK           0x7F	/* Bits 6:0 contain the type */

/*
 * Small resource descriptor "names" as defined by the ACPI specification.
 * Note: Bits 2:0 are used for the descriptor length
 */
#define ACPI_RESOURCE_NAME_IRQ                  0x20
#define ACPI_RESOURCE_NAME_DMA                  0x28
#define ACPI_RESOURCE_NAME_START_DEPENDENT      0x30
#define ACPI_RESOURCE_NAME_END_DEPENDENT        0x38
#define ACPI_RESOURCE_NAME_IO                   0x40
#define ACPI_RESOURCE_NAME_FIXED_IO             0x48
#define ACPI_RESOURCE_NAME_FIXED_DMA            0x50
...
#define ACPI_RESOURCE_NAME_VENDOR_SMALL         0x70
#define ACPI_RESOURCE_NAME_END_TAG              0x78

/*
 * Large resource descriptor "names" as defined by the ACPI specification.
 * Note: includes the Large Descriptor bit in bit[7]
 */
#define ACPI_RESOURCE_NAME_MEMORY24             0x81
#define ACPI_RESOURCE_NAME_GENERIC_REGISTER     0x82
#define ACPI_RESOURCE_NAME_RESERVED_L1          0x83
#define ACPI_RESOURCE_NAME_VENDOR_LARGE         0x84
#define ACPI_RESOURCE_NAME_MEMORY32             0x85
#define ACPI_RESOURCE_NAME_FIXED_MEMORY32       0x86
#define ACPI_RESOURCE_NAME_ADDRESS32            0x87
#define ACPI_RESOURCE_NAME_ADDRESS16            0x88
#define ACPI_RESOURCE_NAME_EXTENDED_IRQ         0x89
#define ACPI_RESOURCE_NAME_ADDRESS64            0x8A
#define ACPI_RESOURCE_NAME_EXTENDED_ADDRESS64   0x8B
#define ACPI_RESOURCE_NAME_GPIO                 0x8C
#define ACPI_RESOURCE_NAME_PIN_FUNCTION         0x8D
#define ACPI_RESOURCE_NAME_SERIAL_BUS           0x8E
#define ACPI_RESOURCE_NAME_PIN_CONFIG           0x8F
#define ACPI_RESOURCE_NAME_PIN_GROUP            0x90
#define ACPI_RESOURCE_NAME_PIN_GROUP_FUNCTION   0x91
#define ACPI_RESOURCE_NAME_PIN_GROUP_CONFIG     0x92
#define ACPI_RESOURCE_NAME_CLOCK_INPUT          0x93
#define ACPI_RESOURCE_NAME_LARGE_MAX            0x93
```

[`acpi_ut_validate_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utresrc.c#L266) is the function that performs the two index computations from the figure, and it rejects any tag whose entry in the per-index tables is zero:

```c
/* drivers/acpi/acpica/utresrc.c:282 */
	/*
	 * Byte 0 contains the descriptor name (Resource Type)
	 * Examine the large/small bit in the resource header
	 */
	if (resource_type & ACPI_RESOURCE_NAME_LARGE) {

		/* Verify the large resource type (name) against the max */

		if (resource_type > ACPI_RESOURCE_NAME_LARGE_MAX) {
			goto invalid_resource;
		}

		/*
		 * Large Resource Type -- bits 6:0 contain the name
		 * Translate range 0x80-0x8B to index range 0x10-0x1B
		 */
		resource_index = (u8) (resource_type - 0x70);
	} else {
		/*
		 * Small Resource Type -- bits 6:3 contain the name
		 * Shift range to index range 0x00-0x0F
		 */
		resource_index = (u8)
		    ((resource_type & ACPI_RESOURCE_NAME_SMALL_MASK) >> 3);
	}

	/*
	 * Check validity of the resource type, via acpi_gbl_resource_types.
	 * Zero indicates an invalid resource.
	 */
	if (!acpi_gbl_resource_types[resource_index]) {
		goto invalid_resource;
	}

	/*
	 * Validate the resource_length field. This ensures that the length
	 * is at least reasonable, and guarantees that it is non-zero.
	 */
	resource_length = acpi_ut_get_resource_length(aml);
	minimum_resource_length = acpi_gbl_resource_aml_sizes[resource_index];
```

The same function then compares the descriptor's length field against the per-index minimum from [`acpi_gbl_resource_aml_sizes[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utresrc.c#L19), an array built by applying [`ACPI_AML_SIZE_SMALL()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L102) and [`ACPI_AML_SIZE_LARGE()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L101) to every raw overlay struct, which makes this array the place where each [`struct aml_resource_gpio`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L281)-style layout is consumed as a size authority:

```c
/* drivers/acpi/acpica/utresrc.c:19 */
const u8 acpi_gbl_resource_aml_sizes[] = {
	/* Small descriptors */

	0,
	0,
	0,
	0,
	ACPI_AML_SIZE_SMALL(struct aml_resource_irq),
	ACPI_AML_SIZE_SMALL(struct aml_resource_dma),
	ACPI_AML_SIZE_SMALL(struct aml_resource_start_dependent),
	ACPI_AML_SIZE_SMALL(struct aml_resource_end_dependent),
	ACPI_AML_SIZE_SMALL(struct aml_resource_io),
	ACPI_AML_SIZE_SMALL(struct aml_resource_fixed_io),
	ACPI_AML_SIZE_SMALL(struct aml_resource_fixed_dma),
	0,
	0,
	0,
	ACPI_AML_SIZE_SMALL(struct aml_resource_vendor_small),
	ACPI_AML_SIZE_SMALL(struct aml_resource_end_tag),

	/* Large descriptors */

	0,
	ACPI_AML_SIZE_LARGE(struct aml_resource_memory24),
	ACPI_AML_SIZE_LARGE(struct aml_resource_generic_register),
	0,
	ACPI_AML_SIZE_LARGE(struct aml_resource_vendor_large),
	ACPI_AML_SIZE_LARGE(struct aml_resource_memory32),
	ACPI_AML_SIZE_LARGE(struct aml_resource_fixed_memory32),
	ACPI_AML_SIZE_LARGE(struct aml_resource_address32),
	ACPI_AML_SIZE_LARGE(struct aml_resource_address16),
	ACPI_AML_SIZE_LARGE(struct aml_resource_extended_irq),
	ACPI_AML_SIZE_LARGE(struct aml_resource_address64),
	ACPI_AML_SIZE_LARGE(struct aml_resource_extended_address64),
	ACPI_AML_SIZE_LARGE(struct aml_resource_gpio),
	ACPI_AML_SIZE_LARGE(struct aml_resource_pin_function),
	ACPI_AML_SIZE_LARGE(struct aml_resource_common_serialbus),
	ACPI_AML_SIZE_LARGE(struct aml_resource_pin_config),
	ACPI_AML_SIZE_LARGE(struct aml_resource_pin_group),
	ACPI_AML_SIZE_LARGE(struct aml_resource_pin_group_function),
	ACPI_AML_SIZE_LARGE(struct aml_resource_pin_group_config),
	ACPI_AML_SIZE_LARGE(struct aml_resource_clock_input),

};
```

### Raw descriptor overlays in union aml_resource

The structs in [`drivers/acpi/acpica/amlresrc.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h) reproduce the wire format byte for byte. According to the comment "Packing/alignment must be BYTE because these descriptors are used to overlay the raw AML byte stream", the whole file sits inside `#pragma pack(1)`, and every struct begins with one of the two header macros:

```c
/* drivers/acpi/acpica/amlresrc.h:115 */
#define AML_RESOURCE_SMALL_HEADER_COMMON \
	u8                              descriptor_type;

struct aml_resource_small_header {
AML_RESOURCE_SMALL_HEADER_COMMON};
...
/* drivers/acpi/acpica/amlresrc.h:174 */
#define AML_RESOURCE_LARGE_HEADER_COMMON \
	u8                              descriptor_type;\
	u16                             resource_length;

struct aml_resource_large_header {
AML_RESOURCE_LARGE_HEADER_COMMON};
```

Three representative large-item overlays show the range of shapes the converter has to handle. [`struct aml_resource_fixed_memory32`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L206) is entirely fixed-size, [`struct aml_resource_extended_irq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L261) carries a flexible 32-bit interrupt array followed by an optional ResourceSource, and [`struct aml_resource_gpio`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L281) holds three variable-length regions (pin table, source string, vendor data) addressed by 16-bit offsets from the start of the descriptor:

```c
/* drivers/acpi/acpica/amlresrc.h:206 */
struct aml_resource_fixed_memory32 {
	AML_RESOURCE_LARGE_HEADER_COMMON u8 flags;
	u32 address;
	u32 address_length;
};
```

```c
/* drivers/acpi/acpica/amlresrc.h:261 */
struct aml_resource_extended_irq {
	AML_RESOURCE_LARGE_HEADER_COMMON u8 flags;
	u8 interrupt_count;
	union {
		u32 interrupt;
		 ACPI_FLEX_ARRAY(u32, interrupts);
	};
	/* res_source_index, res_source optional fields follow */
};
```

```c
/* drivers/acpi/acpica/amlresrc.h:279 */
/* Common descriptor for gpio_int and gpio_io (ACPI 5.0) */

struct aml_resource_gpio {
	AML_RESOURCE_LARGE_HEADER_COMMON u8 revision_id;
	u8 connection_type;
	u16 flags;
	u16 int_flags;
	u8 pin_config;
	u16 drive_strength;
	u16 debounce_timeout;
	u16 pin_table_offset;
	u8 res_source_index;
	u16 res_source_offset;
	u16 vendor_offset;
	u16 vendor_length;
	/*
	 * Optional fields follow immediately:
	 * 1) PIN list (Words)
	 * 2) Resource Source String
	 * 3) Vendor Data bytes
	 */
};
```

The serial-bus overlays add a second header layer. [`AML_RESOURCE_SERIAL_COMMON`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L312) follows the large header in every bus variant, its `type` byte is the second-level dispatch key ([`AML_RESOURCE_I2C_SERIALBUSTYPE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L323) 1 through [`AML_RESOURCE_MAX_SERIALBUSTYPE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L327) 4), and [`struct aml_resource_i2c_serialbus`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L346) appends the I2C-specific speed and address fields:

```c
/* drivers/acpi/acpica/amlresrc.h:310 */
/* Common preamble for all serial descriptors (ACPI 5.0) */

#define AML_RESOURCE_SERIAL_COMMON \
	u8                              revision_id; \
	u8                              res_source_index; \
	u8                              type; \
	u8                              flags; \
	u16                             type_specific_flags; \
	u8                              type_revision_id; \
	u16                             type_data_length; \

/* Values for the type field above */

#define AML_RESOURCE_I2C_SERIALBUSTYPE          1
#define AML_RESOURCE_SPI_SERIALBUSTYPE          2
#define AML_RESOURCE_UART_SERIALBUSTYPE         3
#define AML_RESOURCE_CSI2_SERIALBUSTYPE         4
#define AML_RESOURCE_MAX_SERIALBUSTYPE          4
...
struct aml_resource_i2c_serialbus {
	AML_RESOURCE_LARGE_HEADER_COMMON
	    AML_RESOURCE_SERIAL_COMMON u32 connection_speed;
	u16 slave_address;
	/*
	 * Optional fields follow immediately:
	 * 1) Vendor Data bytes
	 * 2) Resource Source String
	 */
};
```

All the overlays collect into [`union aml_resource`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L509), which is the type the converter casts the raw byte pointer to. According to the comment "Union of all resource descriptors, so we can allocate the worst case", one allocation of this union can stage any descriptor during encode:

```c
/* drivers/acpi/acpica/amlresrc.h:507 */
/* Union of all resource descriptors, so we can allocate the worst case */

union aml_resource {
	/* Descriptor headers */

	u8 descriptor_type;
	struct aml_resource_small_header small_header;
	struct aml_resource_large_header large_header;

	/* Small resource descriptors */

	struct aml_resource_irq irq;
	struct aml_resource_dma dma;
	struct aml_resource_start_dependent start_dpf;
	struct aml_resource_end_dependent end_dpf;
	struct aml_resource_io io;
	struct aml_resource_fixed_io fixed_io;
	struct aml_resource_fixed_dma fixed_dma;
	struct aml_resource_vendor_small vendor_small;
	struct aml_resource_end_tag end_tag;

	/* Large resource descriptors */

	struct aml_resource_memory24 memory24;
	struct aml_resource_generic_register generic_reg;
	struct aml_resource_vendor_large vendor_large;
	struct aml_resource_memory32 memory32;
	struct aml_resource_fixed_memory32 fixed_memory32;
	struct aml_resource_address16 address16;
	struct aml_resource_address32 address32;
	struct aml_resource_address64 address64;
	struct aml_resource_extended_address64 ext_address64;
	struct aml_resource_extended_irq extended_irq;
	struct aml_resource_gpio gpio;
	struct aml_resource_i2c_serialbus i2c_serial_bus;
	struct aml_resource_spi_serialbus spi_serial_bus;
	struct aml_resource_uart_serialbus uart_serial_bus;
	struct aml_resource_csi2_serialbus csi2_serial_bus;
	struct aml_resource_common_serialbus common_serial_bus;
	struct aml_resource_pin_function pin_function;
	struct aml_resource_pin_config pin_config;
	struct aml_resource_pin_group pin_group;
	struct aml_resource_pin_group_function pin_group_function;
	struct aml_resource_pin_group_config pin_group_config;
	struct aml_resource_clock_input clock_input;

	/* Utility overlays */

	struct aml_resource_address address;
	u32 dword_item;
	u16 word_item;
	u8 byte_item;
};
```

### The decoded record: struct acpi_resource and union acpi_resource_data

The conversion output is an array of [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678) records, each a fixed `type`/`length` header followed by exactly one member of the master payload union. The `type` values form their own enumeration, decoupled from the AML tags so consumers stay independent of the wire encoding:

```c
/* include/acpi/acrestyp.h:607 */
/* ACPI_RESOURCE_TYPEs */

#define ACPI_RESOURCE_TYPE_IRQ                  0
#define ACPI_RESOURCE_TYPE_DMA                  1
#define ACPI_RESOURCE_TYPE_START_DEPENDENT      2
#define ACPI_RESOURCE_TYPE_END_DEPENDENT        3
#define ACPI_RESOURCE_TYPE_IO                   4
#define ACPI_RESOURCE_TYPE_FIXED_IO             5
#define ACPI_RESOURCE_TYPE_VENDOR               6
#define ACPI_RESOURCE_TYPE_END_TAG              7
#define ACPI_RESOURCE_TYPE_MEMORY24             8
#define ACPI_RESOURCE_TYPE_MEMORY32             9
#define ACPI_RESOURCE_TYPE_FIXED_MEMORY32       10
#define ACPI_RESOURCE_TYPE_ADDRESS16            11
#define ACPI_RESOURCE_TYPE_ADDRESS32            12
#define ACPI_RESOURCE_TYPE_ADDRESS64            13
#define ACPI_RESOURCE_TYPE_EXTENDED_ADDRESS64   14	/* ACPI 3.0 */
#define ACPI_RESOURCE_TYPE_EXTENDED_IRQ         15
#define ACPI_RESOURCE_TYPE_GENERIC_REGISTER     16
#define ACPI_RESOURCE_TYPE_GPIO                 17	/* ACPI 5.0 */
#define ACPI_RESOURCE_TYPE_FIXED_DMA            18	/* ACPI 5.0 */
#define ACPI_RESOURCE_TYPE_SERIAL_BUS           19	/* ACPI 5.0 */
#define ACPI_RESOURCE_TYPE_PIN_FUNCTION         20	/* ACPI 6.2 */
#define ACPI_RESOURCE_TYPE_PIN_CONFIG           21	/* ACPI 6.2 */
#define ACPI_RESOURCE_TYPE_PIN_GROUP            22	/* ACPI 6.2 */
#define ACPI_RESOURCE_TYPE_PIN_GROUP_FUNCTION   23	/* ACPI 6.2 */
#define ACPI_RESOURCE_TYPE_PIN_GROUP_CONFIG     24	/* ACPI 6.2 */
#define ACPI_RESOURCE_TYPE_CLOCK_INPUT          25	/* ACPI 6.5 */
#define ACPI_RESOURCE_TYPE_MAX                  25
```

```c
/* include/acpi/acrestyp.h:637 */
/* Master union for resource descriptors */

union acpi_resource_data {
	struct acpi_resource_irq irq;
	struct acpi_resource_dma dma;
	struct acpi_resource_start_dependent start_dpf;
	struct acpi_resource_io io;
	struct acpi_resource_fixed_io fixed_io;
	struct acpi_resource_fixed_dma fixed_dma;
	struct acpi_resource_vendor vendor;
	struct acpi_resource_vendor_typed vendor_typed;
	struct acpi_resource_end_tag end_tag;
	struct acpi_resource_memory24 memory24;
	struct acpi_resource_memory32 memory32;
	struct acpi_resource_fixed_memory32 fixed_memory32;
	struct acpi_resource_address16 address16;
	struct acpi_resource_address32 address32;
	struct acpi_resource_address64 address64;
	struct acpi_resource_extended_address64 ext_address64;
	struct acpi_resource_extended_irq extended_irq;
	struct acpi_resource_generic_register generic_reg;
	struct acpi_resource_gpio gpio;
	struct acpi_resource_i2c_serialbus i2c_serial_bus;
	struct acpi_resource_spi_serialbus spi_serial_bus;
	struct acpi_resource_uart_serialbus uart_serial_bus;
	struct acpi_resource_csi2_serialbus csi2_serial_bus;
	struct acpi_resource_common_serialbus common_serial_bus;
	struct acpi_resource_pin_function pin_function;
	struct acpi_resource_pin_config pin_config;
	struct acpi_resource_pin_group pin_group;
	struct acpi_resource_pin_group_function pin_group_function;
	struct acpi_resource_pin_group_config pin_group_config;
	struct acpi_resource_clock_input clock_input;

	/* Common fields */

	struct acpi_resource_address address;	/* Common 16/32/64 address fields */
};

/* Common resource header */

struct acpi_resource {
	u32 type;
	u32 length;
	union acpi_resource_data data;
};
```

The `address` member at the bottom is a deliberate aliasing aid. [`struct acpi_resource_address`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L309) consists only of the [`ACPI_RESOURCE_ADDRESS_COMMON`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L277) prefix (`resource_type`, `producer_consumer`, `decode`, fixed-range flags, and the attribute union) that all four address payloads start with, so code can classify a Word/DWord/QWord/Extended record through `data.address.resource_type` without knowing the width.

`length` is a per-record value rather than a constant. [`ACPI_RS_SIZE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L690) gives the minimum (8-byte header plus the payload struct), the conversion grows it for trailing pin tables, interrupt arrays, source strings, and vendor data, and [`ACPI_NEXT_RESOURCE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L694) relies on it to step through the output array:

```c
/* include/acpi/acrestyp.h:688 */
#define ACPI_RS_SIZE_NO_DATA                8	/* Id + Length fields */
#define ACPI_RS_SIZE_MIN                    (u32) ACPI_ROUND_UP_TO_NATIVE_WORD (12)
#define ACPI_RS_SIZE(type)                  (u32) (ACPI_RS_SIZE_NO_DATA + sizeof (type))

/* Macro for walking resource templates with multiple descriptors */

#define ACPI_NEXT_RESOURCE(res) \
	ACPI_ADD_PTR (struct acpi_resource, (res), (res)->length)
```

The four payload structs this page walks in depth illustrate the decode conventions. Flag fields that occupy single bits on the wire become whole `u8` fields, offset-addressed regions become real pointers into the record's own tail storage, and the ResourceSource triple becomes a [`struct acpi_resource_source`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L269):

```c
/* include/acpi/acrestyp.h:235 */
struct acpi_resource_fixed_memory32 {
	u8 write_protect;
	u32 address;
	u32 address_length;
};
```

```c
/* include/acpi/acrestyp.h:269 */
struct acpi_resource_source {
	u8 index;
	u16 string_length;
	char *string_ptr;
};
```

```c
/* include/acpi/acrestyp.h:333 */
struct acpi_resource_extended_irq {
	u8 producer_consumer;
	u8 triggering;
	u8 polarity;
	u8 shareable;
	u8 wake_capable;
	u8 interrupt_count;
	struct acpi_resource_source resource_source;
	union {
		u32 interrupt;
		 ACPI_FLEX_ARRAY(u32, interrupts);
	};
};
```

```c
/* include/acpi/acrestyp.h:355 */
struct acpi_resource_gpio {
	u8 revision_id;
	u8 connection_type;
	u8 producer_consumer;	/* For values, see Producer/Consumer above */
	u8 pin_config;
	u8 shareable;		/* For values, see Interrupt Attributes above */
	u8 wake_capable;	/* For values, see Interrupt Attributes above */
	u8 io_restriction;
	u8 triggering;		/* For values, see Interrupt Attributes above */
	u8 polarity;		/* For values, see Interrupt Attributes above */
	u16 drive_strength;
	u16 debounce_timeout;
	u16 pin_table_length;
	u16 vendor_length;
	struct acpi_resource_source resource_source;
	u16 *pin_table;
	u8 *vendor_data;
};

/* Values for GPIO connection_type field above */

#define ACPI_RESOURCE_GPIO_TYPE_INT             0
#define ACPI_RESOURCE_GPIO_TYPE_IO              1
```

The serial-bus payloads repeat the two-layer shape of their AML counterparts. [`ACPI_RESOURCE_SERIAL_COMMON`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L395) expands to the shared header (revision, bus `type`, producer/slave/sharing bytes, type revision, payload length, vendor data, and the ResourceSource pointing at the controller), [`struct acpi_resource_common_serialbus`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L407) is that header alone for type-agnostic code, and [`struct acpi_resource_i2c_serialbus`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L422) appends the I2C triple that the I2C core copies into board info:

```c
/* include/acpi/acrestyp.h:393 */
/* Common structure for I2C, SPI, UART, CSI2 serial descriptors */

#define ACPI_RESOURCE_SERIAL_COMMON \
	u8                                      revision_id; \
	u8                                      type; \
	u8                                      producer_consumer;   /* For values, see Producer/Consumer above */\
	u8                                      slave_mode; \
	u8                                      connection_sharing; \
	u8                                      type_revision_id; \
	u16                                     type_data_length; \
	u16                                     vendor_length; \
	struct acpi_resource_source             resource_source; \
	u8                                      *vendor_data;

struct acpi_resource_common_serialbus {
ACPI_RESOURCE_SERIAL_COMMON};

/* Values for the Type field above */

#define ACPI_RESOURCE_SERIAL_TYPE_I2C           1
#define ACPI_RESOURCE_SERIAL_TYPE_SPI           2
#define ACPI_RESOURCE_SERIAL_TYPE_UART          3
#define ACPI_RESOURCE_SERIAL_TYPE_CSI2          4
...
struct acpi_resource_i2c_serialbus {
	ACPI_RESOURCE_SERIAL_COMMON u8 access_mode;
	u16 slave_address;
	u32 connection_speed;
};
```

### Conversion scripts: struct acpi_rsconvert_info and its opcodes

Per-descriptor decode knowledge lives in data, in const arrays of 4-byte script entries rather than in per-type C functions. Each entry carries an opcode, an offset into the destination [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678) (computed by [`ACPI_RS_OFFSET()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acresrc.h#L85)), an offset into the source [`union aml_resource`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L509) (computed by [`AML_OFFSET()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acresrc.h#L86)), and an opcode-specific value byte such as a bit position or an item size:

```c
/* drivers/acpi/acpica/acresrc.h:29 */
/*
 * Individual entry for the resource conversion tables
 */
typedef const struct acpi_rsconvert_info {
	u8 opcode;
	u8 resource_offset;
	u8 aml_offset;
	u8 value;

} acpi_rsconvert_info;

/* Resource conversion opcodes */

typedef enum {
	ACPI_RSC_INITGET = 0,
	ACPI_RSC_INITSET,
	ACPI_RSC_FLAGINIT,
	ACPI_RSC_1BITFLAG,
	ACPI_RSC_2BITFLAG,
	ACPI_RSC_3BITFLAG,
	ACPI_RSC_6BITFLAG,
	ACPI_RSC_ADDRESS,
	ACPI_RSC_BITMASK,
	ACPI_RSC_BITMASK16,
	ACPI_RSC_COUNT,
	ACPI_RSC_COUNT16,
	ACPI_RSC_COUNT_GPIO_PIN,
	ACPI_RSC_COUNT_GPIO_RES,
	ACPI_RSC_COUNT_GPIO_VEN,
	ACPI_RSC_COUNT_SERIAL_RES,
	ACPI_RSC_COUNT_SERIAL_VEN,
	ACPI_RSC_DATA8,
	ACPI_RSC_EXIT_EQ,
	ACPI_RSC_EXIT_LE,
	ACPI_RSC_EXIT_NE,
	ACPI_RSC_LENGTH,
	ACPI_RSC_MOVE_GPIO_PIN,
	ACPI_RSC_MOVE_GPIO_RES,
	ACPI_RSC_MOVE_SERIAL_RES,
	ACPI_RSC_MOVE_SERIAL_VEN,
	ACPI_RSC_MOVE8,
	ACPI_RSC_MOVE16,
	ACPI_RSC_MOVE32,
	ACPI_RSC_MOVE64,
	ACPI_RSC_SET8,
	ACPI_RSC_SOURCE,
	ACPI_RSC_SOURCEX
} ACPI_RSCONVERT_OPCODES;

/* Resource Conversion sub-opcodes */

#define ACPI_RSC_COMPARE_AML_LENGTH     0
#define ACPI_RSC_COMPARE_VALUE          1

#define ACPI_RSC_TABLE_SIZE(d)          (sizeof (d) / sizeof (struct acpi_rsconvert_info))

#define ACPI_RS_OFFSET(f)               (u8) ACPI_OFFSET (struct acpi_resource,f)
#define AML_OFFSET(f)                   (u8) ACPI_OFFSET (union aml_resource,f)
```

One table serves both directions. The first entry is [`ACPI_RSC_INITGET`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acresrc.h#L43), which during AML-to-resource conversion zeroes the record, stores the decoded type constant from its `resource_offset` slot, stores the minimum record length from its `aml_offset` slot, and carries the table's entry count (via [`ACPI_RSC_TABLE_SIZE()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acresrc.h#L83)) in `value`. The second entry is [`ACPI_RSC_INITSET`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acresrc.h#L44), a no-op on the get path that seeds the AML tag byte and raw descriptor size when [`acpi_rs_convert_resource_to_aml()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsmisc.c#L445) encodes templates for `_SRS`. The Interrupt table shows the whole vocabulary in ten entries:

```c
/* drivers/acpi/acpica/rsirq.c:156 */
struct acpi_rsconvert_info acpi_rs_convert_ext_irq[10] = {
	{ACPI_RSC_INITGET, ACPI_RESOURCE_TYPE_EXTENDED_IRQ,
	 ACPI_RS_SIZE(struct acpi_resource_extended_irq),
	 ACPI_RSC_TABLE_SIZE(acpi_rs_convert_ext_irq)},

	{ACPI_RSC_INITSET, ACPI_RESOURCE_NAME_EXTENDED_IRQ,
	 sizeof(struct aml_resource_extended_irq),
	 0},

	/*
	 * Flags: Producer/Consumer[0], Triggering[1], Polarity[2],
	 *        Sharing[3], Wake[4]
	 */
	{ACPI_RSC_1BITFLAG, ACPI_RS_OFFSET(data.extended_irq.producer_consumer),
	 AML_OFFSET(extended_irq.flags),
	 0},

	{ACPI_RSC_1BITFLAG, ACPI_RS_OFFSET(data.extended_irq.triggering),
	 AML_OFFSET(extended_irq.flags),
	 1},

	{ACPI_RSC_1BITFLAG, ACPI_RS_OFFSET(data.extended_irq.polarity),
	 AML_OFFSET(extended_irq.flags),
	 2},

	{ACPI_RSC_1BITFLAG, ACPI_RS_OFFSET(data.extended_irq.shareable),
	 AML_OFFSET(extended_irq.flags),
	 3},

	{ACPI_RSC_1BITFLAG, ACPI_RS_OFFSET(data.extended_irq.wake_capable),
	 AML_OFFSET(extended_irq.flags),
	 4},

	/* IRQ Table length (Byte4) */

	{ACPI_RSC_COUNT, ACPI_RS_OFFSET(data.extended_irq.interrupt_count),
	 AML_OFFSET(extended_irq.interrupt_count),
	 sizeof(u32)},

	/* Copy every IRQ in the table, each is 32 bits */

	{ACPI_RSC_MOVE32, ACPI_RS_OFFSET(data.extended_irq.interrupts[0]),
	 AML_OFFSET(extended_irq.interrupts[0]),
	 0},

	/* Optional resource_source (Index and String) */

	{ACPI_RSC_SOURCEX, ACPI_RS_OFFSET(data.extended_irq.resource_source),
	 ACPI_RS_OFFSET(data.extended_irq.interrupts[0]),
	 sizeof(struct aml_resource_extended_irq)}
};
```

Reading this table against the example template's `Interrupt (ResourceConsumer, Level, ActiveLow, Exclusive) { 0x20 }`, the five [`ACPI_RSC_1BITFLAG`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acresrc.h#L46) entries shift the raw `flags` byte right by 0 through 4 and mask one bit each (consumer 1, level 0, active-low 1, exclusive 0, wake 0), the [`ACPI_RSC_COUNT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acresrc.h#L53) entry reads `interrupt_count` 1 and grows `resource->length` by `sizeof(u32)` for every interrupt beyond the first, the [`ACPI_RSC_MOVE32`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acresrc.h#L71) entry copies the GSI array (here the single value 0x20), and the [`ACPI_RSC_SOURCEX`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acresrc.h#L75) entry appends the optional ResourceSource string after the interrupt array. The Memory32Fixed table needs only four entries because its payload is fixed-size:

```c
/* drivers/acpi/acpica/rsmemory.c:84 */
struct acpi_rsconvert_info acpi_rs_convert_fixed_memory32[4] = {
	{ACPI_RSC_INITGET, ACPI_RESOURCE_TYPE_FIXED_MEMORY32,
	 ACPI_RS_SIZE(struct acpi_resource_fixed_memory32),
	 ACPI_RSC_TABLE_SIZE(acpi_rs_convert_fixed_memory32)},

	{ACPI_RSC_INITSET, ACPI_RESOURCE_NAME_FIXED_MEMORY32,
	 sizeof(struct aml_resource_fixed_memory32),
	 0},

	/* Read/Write bit */

	{ACPI_RSC_1BITFLAG, ACPI_RS_OFFSET(data.fixed_memory32.write_protect),
	 AML_OFFSET(fixed_memory32.flags),
	 0},
	/*
	 * These fields are contiguous in both the source and destination:
	 * Base Address
	 * Range Length
	 */
	{ACPI_RSC_MOVE32, ACPI_RS_OFFSET(data.fixed_memory32.address),
	 AML_OFFSET(fixed_memory32.address),
	 2}
};
```

The End Tag table is the degenerate case, two init entries and nothing else, and according to the comment "The checksum field is set to zero, meaning that the resource data is treated as if the checksum operation succeeded. (ACPI Spec 1.0b Section 6.4.2.8)", the encode direction always writes a zero checksum:

```c
/* drivers/acpi/acpica/rsio.c:132 */
struct acpi_rsconvert_info acpi_rs_convert_end_tag[2] = {
	{ACPI_RSC_INITGET, ACPI_RESOURCE_TYPE_END_TAG,
	 ACPI_RS_SIZE_MIN,
	 ACPI_RSC_TABLE_SIZE(acpi_rs_convert_end_tag)},

	/*
	 * Note: The checksum field is set to zero, meaning that the resource
	 * data is treated as if the checksum operation succeeded.
	 * (ACPI Spec 1.0b Section 6.4.2.8)
	 */
	{ACPI_RSC_INITSET, ACPI_RESOURCE_NAME_END_TAG,
	 sizeof(struct aml_resource_end_tag),
	 0}
};
```

[`acpi_rs_convert_aml_to_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsmisc.c#L35) is the interpreter that executes whichever table the dispatch selected. Its loop reads the entry count out of the first entry, computes source and destination pointers from the two offsets, and switches on the opcode; the excerpt below keeps the opcodes the tables above use:

```c
/* drivers/acpi/acpica/rsmisc.c:34 */
acpi_status
acpi_rs_convert_aml_to_resource(struct acpi_resource *resource,
				union aml_resource *aml,
				struct acpi_rsconvert_info *info)
{
	acpi_rs_length aml_resource_length;
	void *source;
	void *destination;
	char *target;
	u8 count;
	u8 flags_mode = FALSE;
	u16 item_count = 0;
	u16 temp16 = 0;
	...
	/* Extract the resource Length field (does not include header length) */

	aml_resource_length = acpi_ut_get_resource_length(aml);

	/*
	 * First table entry must be ACPI_RSC_INITxxx and must contain the
	 * table length (# of table entries)
	 */
	count = INIT_TABLE_LENGTH(info);
	while (count) {
		target = NULL;

		/*
		 * Source is the external AML byte stream buffer,
		 * destination is the internal resource descriptor
		 */
		source = ACPI_ADD_PTR(void, aml, info->aml_offset);
		destination =
		    ACPI_ADD_PTR(void, resource, info->resource_offset);

		switch (info->opcode) {
		case ACPI_RSC_INITGET:
			/*
			 * Get the resource type and the initial (minimum) length
			 */
			memset(resource, 0, INIT_RESOURCE_LENGTH(info));
			resource->type = INIT_RESOURCE_TYPE(info);
			resource->length = INIT_RESOURCE_LENGTH(info);
			break;

		case ACPI_RSC_INITSET:
			break;
		...
		case ACPI_RSC_1BITFLAG:
			/*
			 * Mask and shift the flag bit
			 */
			ACPI_SET8(destination,
				  ((ACPI_GET8(source) >> info->value) & 0x01));
			break;

		case ACPI_RSC_2BITFLAG:
			/*
			 * Mask and shift the flag bits
			 */
			ACPI_SET8(destination,
				  ((ACPI_GET8(source) >> info->value) & 0x03));
			break;
		...
		case ACPI_RSC_COUNT:

			item_count = ACPI_GET8(source);
			ACPI_SET8(destination, item_count);

			resource->length = resource->length +
			    (info->value * (item_count - 1));
			break;
		...
		case ACPI_RSC_COUNT_GPIO_PIN:

			target = ACPI_ADD_PTR(void, aml, info->value);
			item_count = ACPI_GET16(target) - ACPI_GET16(source);

			resource->length = resource->length + item_count;
			item_count = item_count / 2;
			ACPI_SET16(destination, item_count);
			break;
		...
		case ACPI_RSC_MOVE8:
		case ACPI_RSC_MOVE16:
		case ACPI_RSC_MOVE32:
		case ACPI_RSC_MOVE64:
			/*
			 * Raw data move. Use the Info value field unless item_count has
			 * been previously initialized via a COUNT opcode
			 */
			if (info->value) {
				item_count = info->value;
			}
			acpi_rs_move_data(destination, source, item_count,
					  info->opcode);
			break;

		case ACPI_RSC_MOVE_GPIO_PIN:

			/* Generate and set the PIN data pointer */

			target = (char *)ACPI_ADD_PTR(void, resource,
						      (resource->length -
						       item_count * 2));
			*(u16 **)destination = ACPI_CAST_PTR(u16, target);

			/* Copy the PIN data */

			source = ACPI_ADD_PTR(void, aml, ACPI_GET16(source));
			acpi_rs_move_data(target, source, item_count,
					  info->opcode);
			break;

		case ACPI_RSC_MOVE_GPIO_RES:

			/* Generate and set the resource_source string pointer */

			target = (char *)ACPI_ADD_PTR(void, resource,
						      (resource->length -
						       item_count));
			*(u8 **)destination = ACPI_CAST_PTR(u8, target);

			/* Copy the resource_source string */

			source = ACPI_ADD_PTR(void, aml, ACPI_GET16(source));
			acpi_rs_move_data(target, source, item_count,
					  info->opcode);
			break;
		...
		case ACPI_RSC_SOURCEX:
			/*
			 * Optional resource_source (Index and String). This is the more
			 * complicated case used by the Interrupt() macro
			 */
			target = ACPI_ADD_PTR(char, resource,
					      info->aml_offset +
					      (item_count * 4));

			resource->length +=
			    acpi_rs_get_resource_source(aml_resource_length,
							(acpi_rs_length)
							(((item_count -
							   1) * sizeof(u32)) +
							 info->value),
							destination, aml,
							target);
			break;
		...
		}

		count--;
		info++;
	}
	...
}
```

The COUNT opcodes and the MOVE_GPIO/MOVE_SERIAL opcodes cooperate through `item_count` and `resource->length`. A COUNT entry runs first, derives the element count (for [`ACPI_RSC_COUNT_GPIO_PIN`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acresrc.h#L55) the byte distance between the pin-table offset and the following region, halved into a word count), and grows the record length; the matching MOVE entry then carves the destination out of the record's grown tail, stores that pointer into the payload field, and copies the data. This is how `pin_table`, `vendor_data`, and every `string_ptr` end up as real pointers inside a single contiguous [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678) record.

### Tag-indexed dispatch from acpi_rs_convert_aml_to_resources

The walk over the raw Buffer is shared infrastructure. [`acpi_rs_create_resource_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rscreate.c#L103), reached from [`acpi_get_current_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L167) and [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) after the `_CRS`/`_PRS`/`_AEI`/`_DMA` evaluation, sizes the output buffer and then drives [`acpi_ut_walk_aml_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utresrc.c#L141) with the converter as its per-descriptor callback:

```c
/* drivers/acpi/acpica/rscreate.c:138 */
	/* Do the conversion */

	resource = output_buffer->pointer;
	status = acpi_ut_walk_aml_resources(NULL, aml_start, aml_buffer_length,
					    acpi_rs_convert_aml_to_resources,
					    &resource);
```

The walker validates each tag with [`acpi_ut_validate_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utresrc.c#L266), derives the cell length with [`acpi_ut_get_descriptor_length()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utresrc.c#L521), invokes the callback with the validated dispatch index, and stops at the End Tag (synthesizing one when broken firmware omits it):

```c
/* drivers/acpi/acpica/utresrc.c:166 */
	/* Walk the byte list, abort on any invalid descriptor type or length */

	while (aml < end_aml) {

		/* Validate the Resource Type and Resource Length */

		status =
		    acpi_ut_validate_resource(walk_state, aml, &resource_index);
		if (ACPI_FAILURE(status)) {
			/*
			 * Exit on failure. Cannot continue because the descriptor
			 * length may be bogus also.
			 */
			return_ACPI_STATUS(status);
		}

		/* Get the length of this descriptor */

		length = acpi_ut_get_descriptor_length(aml);

		/* Invoke the user function */

		if (user_function) {
			status =
			    user_function(aml, length, offset, resource_index,
					  context);
			if (ACPI_FAILURE(status)) {
				return_ACPI_STATUS(status);
			}
		}

		/* An end_tag descriptor terminates this resource template */

		if (acpi_ut_get_resource_type(aml) ==
		    ACPI_RESOURCE_NAME_END_TAG) {
		...
		}
		...
	}
```

The callback is where the index turns into a conversion table:

```c
/* drivers/acpi/acpica/rslist.c:30 */
acpi_status
acpi_rs_convert_aml_to_resources(u8 * aml,
				 u32 length,
				 u32 offset, u8 resource_index, void **context)
{
	struct acpi_resource **resource_ptr =
	    ACPI_CAST_INDIRECT_PTR(struct acpi_resource, context);
	struct acpi_resource *resource;
	union aml_resource *aml_resource;
	struct acpi_rsconvert_info *conversion_table;
	acpi_status status;
	...
	/* Get the appropriate conversion info table */

	aml_resource = ACPI_CAST_PTR(union aml_resource, aml);

	if (acpi_ut_get_resource_type(aml) == ACPI_RESOURCE_NAME_SERIAL_BUS) {

		/* Avoid undefined behavior: member access within misaligned address */

		struct aml_resource_common_serialbus common_serial_bus;
		memcpy(&common_serial_bus, aml_resource,
		       sizeof(common_serial_bus));

		if (common_serial_bus.type > AML_RESOURCE_MAX_SERIALBUSTYPE) {
			conversion_table = NULL;
		} else {
			/* This is an I2C, SPI, UART, or CSI2 serial_bus descriptor */

			conversion_table =
			    acpi_gbl_convert_resource_serial_bus_dispatch
			    [common_serial_bus.type];
		}
	} else {
		conversion_table =
		    acpi_gbl_get_resource_dispatch[resource_index];
	}

	if (!conversion_table) {
		ACPI_ERROR((AE_INFO,
			    "Invalid/unsupported resource descriptor: Type 0x%2.2X",
			    resource_index));
		return_ACPI_STATUS(AE_AML_INVALID_RESOURCE_TYPE);
	}

	/* Convert the AML byte stream resource to a local resource struct */

	status =
	    acpi_rs_convert_aml_to_resource(resource, aml_resource,
					    conversion_table);
	...
	/* Point to the next structure in the output buffer */

	*resource_ptr = ACPI_NEXT_RESOURCE(resource);
	return_ACPI_STATUS(AE_OK);
}
```

[`acpi_gbl_get_resource_dispatch[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsinfo.c#L57) is the index-to-table mapping itself, 16 small-item slots followed by the large-item block, and [`acpi_gbl_convert_resource_serial_bus_dispatch[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsinfo.c#L103) is the bus-type second level used for tag 0x8E. According to the file comment "The tables for Large descriptors are indexed by bits 6:0 of the AML descriptor type byte. The tables for Small descriptors are indexed by bits 6:3 of the descriptor byte", these arrays are the one place every new descriptor kind must be registered:

```c
/* drivers/acpi/acpica/rsinfo.c:57 */
struct acpi_rsconvert_info *acpi_gbl_get_resource_dispatch[] = {
	/* Small descriptors */

	NULL,			/* 0x00, Reserved */
	NULL,			/* 0x01, Reserved */
	NULL,			/* 0x02, Reserved */
	NULL,			/* 0x03, Reserved */
	acpi_rs_get_irq,	/* 0x04, ACPI_RESOURCE_NAME_IRQ */
	acpi_rs_convert_dma,	/* 0x05, ACPI_RESOURCE_NAME_DMA */
	acpi_rs_get_start_dpf,	/* 0x06, ACPI_RESOURCE_NAME_START_DEPENDENT */
	acpi_rs_convert_end_dpf,	/* 0x07, ACPI_RESOURCE_NAME_END_DEPENDENT */
	acpi_rs_convert_io,	/* 0x08, ACPI_RESOURCE_NAME_IO */
	acpi_rs_convert_fixed_io,	/* 0x09, ACPI_RESOURCE_NAME_FIXED_IO */
	acpi_rs_convert_fixed_dma,	/* 0x0A, ACPI_RESOURCE_NAME_FIXED_DMA */
	NULL,			/* 0x0B, Reserved */
	NULL,			/* 0x0C, Reserved */
	NULL,			/* 0x0D, Reserved */
	acpi_rs_get_vendor_small,	/* 0x0E, ACPI_RESOURCE_NAME_VENDOR_SMALL */
	acpi_rs_convert_end_tag,	/* 0x0F, ACPI_RESOURCE_NAME_END_TAG */

	/* Large descriptors */

	NULL,			/* 0x00, Reserved */
	acpi_rs_convert_memory24,	/* 0x01, ACPI_RESOURCE_NAME_MEMORY24 */
	acpi_rs_convert_generic_reg,	/* 0x02, ACPI_RESOURCE_NAME_GENERIC_REGISTER */
	NULL,			/* 0x03, Reserved */
	acpi_rs_get_vendor_large,	/* 0x04, ACPI_RESOURCE_NAME_VENDOR_LARGE */
	acpi_rs_convert_memory32,	/* 0x05, ACPI_RESOURCE_NAME_MEMORY32 */
	acpi_rs_convert_fixed_memory32,	/* 0x06, ACPI_RESOURCE_NAME_FIXED_MEMORY32 */
	acpi_rs_convert_address32,	/* 0x07, ACPI_RESOURCE_NAME_ADDRESS32 */
	acpi_rs_convert_address16,	/* 0x08, ACPI_RESOURCE_NAME_ADDRESS16 */
	acpi_rs_convert_ext_irq,	/* 0x09, ACPI_RESOURCE_NAME_EXTENDED_IRQ */
	acpi_rs_convert_address64,	/* 0x0A, ACPI_RESOURCE_NAME_ADDRESS64 */
	acpi_rs_convert_ext_address64,	/* 0x0B, ACPI_RESOURCE_NAME_EXTENDED_ADDRESS64 */
	acpi_rs_convert_gpio,	/* 0x0C, ACPI_RESOURCE_NAME_GPIO */
	acpi_rs_convert_pin_function,	/* 0x0D, ACPI_RESOURCE_NAME_PIN_FUNCTION */
	NULL,			/* 0x0E, ACPI_RESOURCE_NAME_SERIAL_BUS - Use subtype table below */
	acpi_rs_convert_pin_config,	/* 0x0F, ACPI_RESOURCE_NAME_PIN_CONFIG */
	acpi_rs_convert_pin_group,	/* 0x10, ACPI_RESOURCE_NAME_PIN_GROUP */
	acpi_rs_convert_pin_group_function,	/* 0x11, ACPI_RESOURCE_NAME_PIN_GROUP_FUNCTION */
	acpi_rs_convert_pin_group_config,	/* 0x12, ACPI_RESOURCE_NAME_PIN_GROUP_CONFIG */
	acpi_rs_convert_clock_input,	/* 0x13, ACPI_RESOURCE_NAME_CLOCK_INPUT */
};

/* Subtype table for serial_bus -- I2C, SPI, UART, and CSI2 */

struct acpi_rsconvert_info *acpi_gbl_convert_resource_serial_bus_dispatch[] = {
	NULL,
	acpi_rs_convert_i2c_serial_bus,
	acpi_rs_convert_spi_serial_bus,
	acpi_rs_convert_uart_serial_bus,
	acpi_rs_convert_csi2_serial_bus
};
```

The same file defines [`acpi_gbl_set_resource_dispatch[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsinfo.c#L26), indexed by the decoded [`ACPI_RESOURCE_TYPE_IRQ`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L609) values instead of tag bits, for the reverse `_SRS` encode direction; most rows reuse the same bidirectional tables, and only IRQ, StartDependentFn, and Vendor need distinct get/set scripts ([`acpi_rs_get_irq[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsirq.c#L20) versus [`acpi_rs_set_irq[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsirq.c#L72)) because the legacy IRQ descriptor encodes its interrupt list as a 16-bit mask via [`ACPI_RSC_BITMASK16`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acresrc.h#L52) and shrinks to the 2-byte `IRQNoFlags` form when the flags match defaults.

The ACPI 6.2 pin families and the ACPI 6.5 ClockInput decode through this exact machinery, with their scripts living alongside the GPIO one in [`drivers/acpi/acpica/rsserial.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsserial.c); their INITGET heads bind the type constant, payload struct, and tag in the same triple every other family uses, and according to the comment in [`acpi_rs_convert_pin_function[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsserial.c#L167) "It is OK to use GPIO operations here because none of them refer GPIO structures directly but instead use offsets given here", the pin tables reuse the GPIO COUNT/MOVE opcodes:

```c
/* drivers/acpi/acpica/rsserial.c:167 */
struct acpi_rsconvert_info acpi_rs_convert_pin_function[13] = {
	{ACPI_RSC_INITGET, ACPI_RESOURCE_TYPE_PIN_FUNCTION,
	 ACPI_RS_SIZE(struct acpi_resource_pin_function),
	 ACPI_RSC_TABLE_SIZE(acpi_rs_convert_pin_function)},

	{ACPI_RSC_INITSET, ACPI_RESOURCE_NAME_PIN_FUNCTION,
	 sizeof(struct aml_resource_pin_function),
	 0},
	...
};
```

```c
/* drivers/acpi/acpica/rsserial.c:118 */
struct acpi_rsconvert_info acpi_rs_convert_clock_input[8] = {
	{ACPI_RSC_INITGET, ACPI_RESOURCE_TYPE_CLOCK_INPUT,
	 ACPI_RS_SIZE(struct acpi_resource_clock_input),
	 ACPI_RSC_TABLE_SIZE(acpi_rs_convert_clock_input)},

	{ACPI_RSC_INITSET, ACPI_RESOURCE_NAME_CLOCK_INPUT,
	 sizeof(struct aml_resource_clock_input),
	 0}
	,
	...
};
```

The remaining pin-family scripts repeat the identical head shape, each binding its decoded type constant to its payload struct and AML tag in the first two entries:

```c
/* drivers/acpi/acpica/rsserial.c:632 */
struct acpi_rsconvert_info acpi_rs_convert_pin_config[14] = {
	{ACPI_RSC_INITGET, ACPI_RESOURCE_TYPE_PIN_CONFIG,
	 ACPI_RS_SIZE(struct acpi_resource_pin_config),
	 ACPI_RSC_TABLE_SIZE(acpi_rs_convert_pin_config)},
	...
};

/* drivers/acpi/acpica/rsserial.c:710 */
struct acpi_rsconvert_info acpi_rs_convert_pin_group[10] = {
	{ACPI_RSC_INITGET, ACPI_RESOURCE_TYPE_PIN_GROUP,
	 ACPI_RS_SIZE(struct acpi_resource_pin_group),
	 ACPI_RSC_TABLE_SIZE(acpi_rs_convert_pin_group)},
	...
};

/* drivers/acpi/acpica/rsserial.c:772 */
struct acpi_rsconvert_info acpi_rs_convert_pin_group_function[13] = {
	{ACPI_RSC_INITGET, ACPI_RESOURCE_TYPE_PIN_GROUP_FUNCTION,
	 ACPI_RS_SIZE(struct acpi_resource_pin_group_function),
	 ACPI_RSC_TABLE_SIZE(acpi_rs_convert_pin_group_function)},
	...
};

/* drivers/acpi/acpica/rsserial.c:849 */
struct acpi_rsconvert_info acpi_rs_convert_pin_group_config[14] = {
	{ACPI_RSC_INITGET, ACPI_RESOURCE_TYPE_PIN_GROUP_CONFIG,
	 ACPI_RS_SIZE(struct acpi_resource_pin_group_config),
	 ACPI_RSC_TABLE_SIZE(acpi_rs_convert_pin_group_config)},
	...
};
```

### Linux converters: union members become struct resource

[`acpi_dev_get_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1000) wraps the decoded walk for Linux consumers, offering every record to an optional preproc callback and then to a converter cascade that produces one [`struct resource`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L22) per convertible record; the per-type converters below are also exported individually so callbacks like the PnP and SPI ones can invoke them on single records. [`acpi_dev_resource_memory()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L107) maps the three memory payloads onto [`IORESOURCE_MEM`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L41), shifting the Memory24 fields left by 8 because that payload stores address bits 23:8:

```c
/* drivers/acpi/resource.c:107 */
bool acpi_dev_resource_memory(struct acpi_resource *ares, struct resource *res)
{
	struct acpi_resource_memory24 *memory24;
	struct acpi_resource_memory32 *memory32;
	struct acpi_resource_fixed_memory32 *fixed_memory32;

	switch (ares->type) {
	case ACPI_RESOURCE_TYPE_MEMORY24:
		memory24 = &ares->data.memory24;
		acpi_dev_get_memresource(res, memory24->minimum << 8,
					 memory24->address_length << 8,
					 memory24->write_protect);
		break;
	case ACPI_RESOURCE_TYPE_MEMORY32:
		memory32 = &ares->data.memory32;
		acpi_dev_get_memresource(res, memory32->minimum,
					 memory32->address_length,
					 memory32->write_protect);
		break;
	case ACPI_RESOURCE_TYPE_FIXED_MEMORY32:
		fixed_memory32 = &ares->data.fixed_memory32;
		acpi_dev_get_memresource(res, fixed_memory32->address,
					 fixed_memory32->address_length,
					 fixed_memory32->write_protect);
		break;
	default:
		res->flags = 0;
		return false;
	}

	return !(res->flags & IORESOURCE_DISABLED);
}
```

```c
/* drivers/acpi/resource.c:73 */
static void acpi_dev_memresource_flags(struct resource *res, u64 len,
				       u8 write_protect)
{
	res->flags = IORESOURCE_MEM;

	if (!acpi_dev_resource_len_valid(res->start, res->end, len, false))
		res->flags |= IORESOURCE_DISABLED | IORESOURCE_UNSET;

	if (write_protect == ACPI_READ_WRITE_MEMORY)
		res->flags |= IORESOURCE_MEM_WRITEABLE;
}

static void acpi_dev_get_memresource(struct resource *res, u64 start, u64 len,
				     u8 write_protect)
{
	res->start = start;
	res->end = start + len - 1;
	acpi_dev_memresource_flags(res, len, write_protect);
}
```

For the example template's `Memory32Fixed (ReadWrite, 0xFED00000, 0x00000400)`, the record arrives as [`ACPI_RESOURCE_TYPE_FIXED_MEMORY32`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L619) with `data.fixed_memory32.address` 0xFED00000 and `address_length` 0x400, so the converter emits a resource spanning 0xFED00000..0xFED003FF flagged [`IORESOURCE_MEM`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L41) | [`IORESOURCE_MEM_WRITEABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L103), the ReadWrite keyword having become `write_protect ==` [`ACPI_READ_WRITE_MEMORY`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L23). [`acpi_dev_resource_io()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L180) follows the identical shape for the two port payloads, forcing [`ACPI_DECODE_10`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L49) for FixedIO because that descriptor carries 10-bit decode by definition:

```c
/* drivers/acpi/resource.c:180 */
bool acpi_dev_resource_io(struct acpi_resource *ares, struct resource *res)
{
	struct acpi_resource_io *io;
	struct acpi_resource_fixed_io *fixed_io;

	switch (ares->type) {
	case ACPI_RESOURCE_TYPE_IO:
		io = &ares->data.io;
		acpi_dev_get_ioresource(res, io->minimum,
					io->address_length,
					io->io_decode);
		break;
	case ACPI_RESOURCE_TYPE_FIXED_IO:
		fixed_io = &ares->data.fixed_io;
		acpi_dev_get_ioresource(res, fixed_io->address,
					fixed_io->address_length,
					ACPI_DECODE_10);
		break;
	default:
		res->flags = 0;
		return false;
	}

	return !(res->flags & IORESOURCE_DISABLED);
}
```

[`acpi_dev_resource_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L828) covers both interrupt payloads, indexed because one descriptor can list several GSIs. According to the comment "Per spec, only one interrupt per descriptor is allowed in _CRS, but some firmware violates this, so parse them all", the legacy branch tolerates over-populated descriptors:

```c
/* drivers/acpi/resource.c:828 */
bool acpi_dev_resource_interrupt(struct acpi_resource *ares, int index,
				 struct resource *res)
{
	struct acpi_resource_irq *irq;
	struct acpi_resource_extended_irq *ext_irq;

	switch (ares->type) {
	case ACPI_RESOURCE_TYPE_IRQ:
		/*
		 * Per spec, only one interrupt per descriptor is allowed in
		 * _CRS, but some firmware violates this, so parse them all.
		 */
		irq = &ares->data.irq;
		if (index >= irq->interrupt_count) {
			irqresource_disabled(res, 0);
			return false;
		}
		acpi_dev_get_irqresource(res, irq->interrupts[index],
					 irq->triggering, irq->polarity,
					 irq->shareable, irq->wake_capable,
					 true);
		break;
	case ACPI_RESOURCE_TYPE_EXTENDED_IRQ:
		ext_irq = &ares->data.extended_irq;
		if (index >= ext_irq->interrupt_count) {
			irqresource_disabled(res, 0);
			return false;
		}
		if (is_gsi(ext_irq))
			acpi_dev_get_irqresource(res, ext_irq->interrupts[index],
					 ext_irq->triggering, ext_irq->polarity,
					 ext_irq->shareable, ext_irq->wake_capable,
					 false);
		else
			irqresource_disabled(res, 0);
		break;
	default:
		res->flags = 0;
		return false;
	}

	return true;
}
```

[`acpi_dev_get_irqresource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L761) registers the GSI and stores the Linux IRQ number into the resource, and the `check_override` flag it receives distinguishes the two descriptor families (true for legacy `IRQ()`, false for `Interrupt()`), because per the comment "With modern ACPI 5 devices using extended IRQ descriptors we take the IRQ configuration from _CRS directly", IO-APIC interrupt source overrides apply only to the legacy ISA family:

```c
/* drivers/acpi/resource.c:799 */
	res->flags = acpi_dev_irq_flags(triggering, polarity, shareable, wake_capable);
	irq = acpi_register_gsi(NULL, gsi, triggering, polarity);
	if (irq >= 0) {
		res->start = irq;
		res->end = irq;
	} else {
		irqresource_disabled(res, gsi);
	}
```

The flags translation is the four-byte-to-bitmask mapping shared by every interrupt-shaped descriptor, pairing [`ACPI_LEVEL_SENSITIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L58)/[`ACPI_EDGE_SENSITIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L59) and [`ACPI_ACTIVE_LOW`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L64)/[`ACPI_ACTIVE_HIGH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L63) with the [`IORESOURCE_IRQ_HIGHEDGE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L78) family, and a second helper produces `IRQ_TYPE_*` values for irqchip programming from the same two bytes:

```c
/* drivers/acpi/resource.c:342 */
unsigned long acpi_dev_irq_flags(u8 triggering, u8 polarity, u8 shareable, u8 wake_capable)
{
	unsigned long flags;

	if (triggering == ACPI_LEVEL_SENSITIVE)
		flags = polarity == ACPI_ACTIVE_LOW ?
			IORESOURCE_IRQ_LOWLEVEL : IORESOURCE_IRQ_HIGHLEVEL;
	else
		flags = polarity == ACPI_ACTIVE_LOW ?
			IORESOURCE_IRQ_LOWEDGE : IORESOURCE_IRQ_HIGHEDGE;

	if (shareable == ACPI_SHARED)
		flags |= IORESOURCE_IRQ_SHAREABLE;

	if (wake_capable == ACPI_WAKE_CAPABLE)
		flags |= IORESOURCE_IRQ_WAKECAPABLE;

	return flags | IORESOURCE_IRQ;
}
```

```c
/* drivers/acpi/resource.c:368 */
unsigned int acpi_dev_get_irq_type(int triggering, int polarity)
{
	switch (polarity) {
	case ACPI_ACTIVE_LOW:
		return triggering == ACPI_EDGE_SENSITIVE ?
		       IRQ_TYPE_EDGE_FALLING :
		       IRQ_TYPE_LEVEL_LOW;
	case ACPI_ACTIVE_HIGH:
		return triggering == ACPI_EDGE_SENSITIVE ?
		       IRQ_TYPE_EDGE_RISING :
		       IRQ_TYPE_LEVEL_HIGH;
	case ACPI_ACTIVE_BOTH:
		if (triggering == ACPI_EDGE_SENSITIVE)
			return IRQ_TYPE_EDGE_BOTH;
		fallthrough;
	default:
		return IRQ_TYPE_NONE;
	}
}
```

For the example's `Interrupt (ResourceConsumer, Level, ActiveLow, Exclusive) { 0x20 }`, [`acpi_dev_irq_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L342) yields [`IORESOURCE_IRQ`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L43) | [`IORESOURCE_IRQ_LOWLEVEL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L81), and the resource's `start` becomes the Linux IRQ that [`acpi_register_gsi()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/irq.c#L56) mapped for GSI 0x20. The address-space family converges through normalization. [`acpi_dev_resource_address_space()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L290) calls ACPICA's [`acpi_resource_to_address64()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L332) to widen the 16/32-bit payloads into one [`struct acpi_resource_address64`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L322) layout, [`acpi_dev_resource_ext_address_space()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L319) feeds the ExtendedSpace payload to the same decoder, and [`acpi_decode_space()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L207) dispatches on the common `resource_type` byte to pick [`IORESOURCE_MEM`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L41), [`IORESOURCE_IO`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L40), or [`IORESOURCE_BUS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L45) (the WordBusNumber case):

```c
/* drivers/acpi/resource.c:290 */
bool acpi_dev_resource_address_space(struct acpi_resource *ares,
				     struct resource_win *win)
{
	struct acpi_resource_address64 addr;

	win->res.flags = 0;
	if (ACPI_FAILURE(acpi_resource_to_address64(ares, &addr)))
		return false;

	return acpi_decode_space(win, (struct acpi_resource_address *)&addr,
				 &addr.address);
}
```

```c
/* drivers/acpi/acpica/rsxface.c:344 */
	switch (resource->type) {
	case ACPI_RESOURCE_TYPE_ADDRESS16:

		address16 =
		    ACPI_CAST_PTR(struct acpi_resource_address16,
				  &resource->data);
		ACPI_COPY_ADDRESS(out, address16);
		break;

	case ACPI_RESOURCE_TYPE_ADDRESS32:

		address32 =
		    ACPI_CAST_PTR(struct acpi_resource_address32,
				  &resource->data);
		ACPI_COPY_ADDRESS(out, address32);
		break;

	case ACPI_RESOURCE_TYPE_ADDRESS64:

		/* Simple copy for 64 bit source */

		memcpy(out, &resource->data,
		       sizeof(struct acpi_resource_address64));
		break;
	...
	}
```

```c
/* drivers/acpi/resource.c:319 */
bool acpi_dev_resource_ext_address_space(struct acpi_resource *ares,
					 struct resource_win *win)
{
	struct acpi_resource_extended_address64 *ext_addr;

	win->res.flags = 0;
	if (ares->type != ACPI_RESOURCE_TYPE_EXTENDED_ADDRESS64)
		return false;

	ext_addr = &ares->data.ext_address64;

	return acpi_decode_space(win, (struct acpi_resource_address *)ext_addr,
				 &ext_addr->address);
}
```

```c
/* drivers/acpi/resource.c:248 */
	switch (addr->resource_type) {
	case ACPI_MEMORY_RANGE:
		acpi_dev_memresource_flags(res, len, wp);

		if (addr->info.mem.caching == ACPI_PREFETCHABLE_MEMORY)
			res->flags |= IORESOURCE_PREFETCH;
		break;
	case ACPI_IO_RANGE:
		acpi_dev_ioresource_flags(res, len, iodec,
					  addr->info.io.translation_type);
		break;
	case ACPI_BUS_NUMBER_RANGE:
		res->flags = IORESOURCE_BUS;
		break;
	default:
		return false;
	}

	if (addr->producer_consumer == ACPI_PRODUCER)
		res->flags |= IORESOURCE_WINDOW;
```

The cast to [`struct acpi_resource_address`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L309) in both converters works because every address payload begins with the [`ACPI_RESOURCE_ADDRESS_COMMON`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L277) prefix, the same aliasing the union's `address` member encodes. `DWordMemory`, `QWordMemory`, `WordIO`, and `WordBusNumber` macros all funnel through this one decoder, with [`ACPI_MEMORY_RANGE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L102), [`ACPI_IO_RANGE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L103), and [`ACPI_BUS_NUMBER_RANGE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L104) carrying the distinction the macro names imply, and [`IORESOURCE_WINDOW`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L57) marking bridge-forwarded producer ranges.

### pnpacpi consumes both styles across the whole legacy catalog

The PnP ACPI parser is the broadest single consumer of the union and demonstrates both consumption styles in two callbacks. [`pnpacpi_parse_allocated_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L271) hands `_CRS` to the first one:

```c
/* drivers/pnp/pnpacpi/rsparser.c:281 */
	status = acpi_walk_resources(handle, METHOD_NAME__CRS,
				     pnpacpi_allocated_resource, dev);
```

[`pnpacpi_allocated_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L164) first offers each record to the generic converters and falls back to raw union reads for the families they skip, including the legacy DMA payload, the vendor payload, and a GpioInt record that it converts to an IRQ through gpiolib:

```c
/* drivers/pnp/pnpacpi/rsparser.c:164 */
static acpi_status pnpacpi_allocated_resource(struct acpi_resource *res,
					      void *data)
{
	struct pnp_dev *dev = data;
	struct acpi_resource_dma *dma;
	struct acpi_resource_vendor_typed *vendor_typed;
	struct acpi_resource_gpio *gpio;
	struct resource_win win = {{0}, 0};
	struct resource *r = &win.res;
	int i, flags;

	if (acpi_dev_resource_address_space(res, &win)
	    || acpi_dev_resource_ext_address_space(res, &win)) {
		pnp_add_resource(dev, &win.res);
		return AE_OK;
	}

	r->flags = 0;
	if (acpi_dev_resource_interrupt(res, 0, r)) {
		pnpacpi_add_irqresource(dev, r);
		for (i = 1; acpi_dev_resource_interrupt(res, i, r); i++)
			pnpacpi_add_irqresource(dev, r);
		...
		return AE_OK;
	} else if (acpi_gpio_get_irq_resource(res, &gpio)) {
		/*
		 * If the resource is GpioInt() type then extract the IRQ
		 * from GPIO resource and fill it into IRQ resource type.
		 */
		i = acpi_dev_gpio_irq_get(dev->data, 0);
		if (i >= 0) {
			flags = acpi_dev_irq_flags(gpio->triggering,
						   gpio->polarity,
						   gpio->shareable,
						   gpio->wake_capable);
		} else {
			flags = IORESOURCE_DISABLED;
		}
		pnp_add_irq_resource(dev, i, flags);
		return AE_OK;
	} else if (r->flags & IORESOURCE_DISABLED) {
		pnp_add_irq_resource(dev, 0, IORESOURCE_DISABLED);
		return AE_OK;
	}

	switch (res->type) {
	case ACPI_RESOURCE_TYPE_MEMORY24:
	case ACPI_RESOURCE_TYPE_MEMORY32:
	case ACPI_RESOURCE_TYPE_FIXED_MEMORY32:
		if (acpi_dev_resource_memory(res, r))
			pnp_add_resource(dev, r);
		break;
	case ACPI_RESOURCE_TYPE_IO:
	case ACPI_RESOURCE_TYPE_FIXED_IO:
		if (acpi_dev_resource_io(res, r))
			pnp_add_resource(dev, r);
		break;
	case ACPI_RESOURCE_TYPE_DMA:
		dma = &res->data.dma;
		if (dma->channel_count > 0 && dma->channels[0] != (u8) -1)
			flags = dma_flags(dev, dma->type, dma->bus_master,
					  dma->transfer);
		else
			flags = IORESOURCE_DISABLED;
		pnp_add_dma_resource(dev, dma->channels[0], flags);
		break;

	case ACPI_RESOURCE_TYPE_START_DEPENDENT:
	case ACPI_RESOURCE_TYPE_END_DEPENDENT:
		break;

	case ACPI_RESOURCE_TYPE_VENDOR:
		vendor_typed = &res->data.vendor_typed;
		pnpacpi_parse_allocated_vendor(dev, vendor_typed);
		break;

	case ACPI_RESOURCE_TYPE_END_TAG:
		break;

	case ACPI_RESOURCE_TYPE_GENERIC_REGISTER:
		break;

	case ACPI_RESOURCE_TYPE_SERIAL_BUS:
		/* serial bus connections (I2C/SPI/UART) are not pnp */
		break;

	default:
		dev_warn(&dev->dev, "unknown resource type %d in _CRS\n",
			 res->type);
		return AE_ERROR;
	}

	return AE_OK;
}
```

Its `_PRS` sibling reads raw union members exclusively, and it is the in-tree consumer of `StartDependentFn`/`EndDependentFn` semantics, mapping the [`struct acpi_resource_start_dependent`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L162) priority byte ([`ACPI_GOOD_CONFIGURATION`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L95) and its two siblings) onto PnP dependent-set priorities. [`pnpacpi_parse_resource_option_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L550) starts the walk and [`pnpacpi_option_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L454) touches every legacy family by name:

```c
/* drivers/pnp/pnpacpi/rsparser.c:562 */
	status = acpi_walk_resources(handle, METHOD_NAME__PRS,
				     pnpacpi_option_resource, &parse_data);
```

```c
/* drivers/pnp/pnpacpi/rsparser.c:454 */
static __init acpi_status pnpacpi_option_resource(struct acpi_resource *res,
						  void *data)
{
	int priority;
	struct acpipnp_parse_option_s *parse_data = data;
	struct pnp_dev *dev = parse_data->dev;
	unsigned int option_flags = parse_data->option_flags;

	switch (res->type) {
	case ACPI_RESOURCE_TYPE_IRQ:
		pnpacpi_parse_irq_option(dev, option_flags, &res->data.irq);
		break;

	case ACPI_RESOURCE_TYPE_DMA:
		pnpacpi_parse_dma_option(dev, option_flags, &res->data.dma);
		break;

	case ACPI_RESOURCE_TYPE_START_DEPENDENT:
		switch (res->data.start_dpf.compatibility_priority) {
		case ACPI_GOOD_CONFIGURATION:
			priority = PNP_RES_PRIORITY_PREFERRED;
			break;

		case ACPI_ACCEPTABLE_CONFIGURATION:
			priority = PNP_RES_PRIORITY_ACCEPTABLE;
			break;

		case ACPI_SUB_OPTIMAL_CONFIGURATION:
			priority = PNP_RES_PRIORITY_FUNCTIONAL;
			break;
		default:
			priority = PNP_RES_PRIORITY_INVALID;
			break;
		}
		parse_data->option_flags = pnp_new_dependent_set(dev, priority);
		break;

	case ACPI_RESOURCE_TYPE_END_DEPENDENT:
		parse_data->option_flags = 0;
		break;

	case ACPI_RESOURCE_TYPE_IO:
		pnpacpi_parse_port_option(dev, option_flags, &res->data.io);
		break;

	case ACPI_RESOURCE_TYPE_FIXED_IO:
		pnpacpi_parse_fixed_port_option(dev, option_flags,
					        &res->data.fixed_io);
		break;

	case ACPI_RESOURCE_TYPE_VENDOR:
	case ACPI_RESOURCE_TYPE_END_TAG:
		break;

	case ACPI_RESOURCE_TYPE_MEMORY24:
		pnpacpi_parse_mem24_option(dev, option_flags,
					   &res->data.memory24);
		break;

	case ACPI_RESOURCE_TYPE_MEMORY32:
		pnpacpi_parse_mem32_option(dev, option_flags,
					   &res->data.memory32);
		break;

	case ACPI_RESOURCE_TYPE_FIXED_MEMORY32:
		pnpacpi_parse_fixed_mem32_option(dev, option_flags,
						 &res->data.fixed_memory32);
		break;

	case ACPI_RESOURCE_TYPE_ADDRESS16:
	case ACPI_RESOURCE_TYPE_ADDRESS32:
	case ACPI_RESOURCE_TYPE_ADDRESS64:
		pnpacpi_parse_address_option(dev, option_flags, res);
		break;

	case ACPI_RESOURCE_TYPE_EXTENDED_ADDRESS64:
		pnpacpi_parse_ext_address_option(dev, option_flags, res);
		break;

	case ACPI_RESOURCE_TYPE_EXTENDED_IRQ:
		pnpacpi_parse_ext_irq_option(dev, option_flags,
					     &res->data.extended_irq);
		break;

	case ACPI_RESOURCE_TYPE_GENERIC_REGISTER:
		break;

	default:
		dev_warn(&dev->dev, "unknown resource type %d in _PRS\n",
			 res->type);
		return AE_ERROR;
	}

	return AE_OK;
}
```

This one switch statement is a usable cross-check of the mapping table above, since each `case` label names a decoded type constant and each handler argument names the union member that the table pairs with it, `&res->data.irq` under [`ACPI_RESOURCE_TYPE_IRQ`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L609), `&res->data.start_dpf` under [`ACPI_RESOURCE_TYPE_START_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L611), `&res->data.extended_irq` under [`ACPI_RESOURCE_TYPE_EXTENDED_IRQ`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L624), and so on through the catalog.

### Serial-bus and FixedDMA consumers read the union directly

Connector descriptors carry bus topology (a controller path plus per-bus wiring parameters) that has no [`struct resource`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L22) expression, so each bus core ships a small filter that recognizes its record and returns a typed pointer into the union. The I2C core's filter checks the record type and then the bus subtype inside the shared serial header:

```c
/* drivers/i2c/i2c-core-acpi.c:55 */
bool i2c_acpi_get_i2c_resource(struct acpi_resource *ares,
			       struct acpi_resource_i2c_serialbus **i2c)
{
	struct acpi_resource_i2c_serialbus *sb;

	if (ares->type != ACPI_RESOURCE_TYPE_SERIAL_BUS)
		return false;

	sb = &ares->data.i2c_serial_bus;
	if (sb->type != ACPI_RESOURCE_SERIAL_TYPE_I2C)
		return false;

	*i2c = sb;
	return true;
}
```

The payload it returns was produced by [`acpi_rs_convert_i2c_serial_bus[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsserial.c#L318), whose entries first fill the [`struct acpi_resource_common_serialbus`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L407) header fields shared by all four bus kinds and then the I2C-specific tail, and whose sibling [`acpi_rs_convert_csi2_serial_bus[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsserial.c#L243) binds the same record type to [`struct acpi_resource_csi2_serialbus`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L518):

```c
/* drivers/acpi/acpica/rsserial.c:318 */
struct acpi_rsconvert_info acpi_rs_convert_i2c_serial_bus[17] = {
	{ACPI_RSC_INITGET, ACPI_RESOURCE_TYPE_SERIAL_BUS,
	 ACPI_RS_SIZE(struct acpi_resource_i2c_serialbus),
	 ACPI_RSC_TABLE_SIZE(acpi_rs_convert_i2c_serial_bus)},

	{ACPI_RSC_INITSET, ACPI_RESOURCE_NAME_SERIAL_BUS,
	 sizeof(struct aml_resource_i2c_serialbus),
	 0},

	{ACPI_RSC_MOVE8, ACPI_RS_OFFSET(data.common_serial_bus.revision_id),
	 AML_OFFSET(common_serial_bus.revision_id),
	 1},

	{ACPI_RSC_MOVE8, ACPI_RS_OFFSET(data.common_serial_bus.type),
	 AML_OFFSET(common_serial_bus.type),
	 1},

	{ACPI_RSC_1BITFLAG, ACPI_RS_OFFSET(data.common_serial_bus.slave_mode),
	 AML_OFFSET(common_serial_bus.flags),
	 0},
	...
	/* I2C bus type specific */

	{ACPI_RSC_1BITFLAG, ACPI_RS_OFFSET(data.i2c_serial_bus.access_mode),
	 AML_OFFSET(i2c_serial_bus.type_specific_flags),
	 0},

	{ACPI_RSC_MOVE32, ACPI_RS_OFFSET(data.i2c_serial_bus.connection_speed),
	 AML_OFFSET(i2c_serial_bus.connection_speed),
	 1},

	{ACPI_RSC_MOVE16, ACPI_RS_OFFSET(data.i2c_serial_bus.slave_address),
	 AML_OFFSET(i2c_serial_bus.slave_address),
	 1},
};
```

```c
/* drivers/acpi/acpica/rsserial.c:243 */
struct acpi_rsconvert_info acpi_rs_convert_csi2_serial_bus[14] = {
	{ ACPI_RSC_INITGET, ACPI_RESOURCE_TYPE_SERIAL_BUS,
	 ACPI_RS_SIZE(struct acpi_resource_csi2_serialbus),
	 ACPI_RSC_TABLE_SIZE(acpi_rs_convert_csi2_serial_bus) },

	{ ACPI_RSC_INITSET, ACPI_RESOURCE_NAME_SERIAL_BUS,
	 sizeof(struct aml_resource_csi2_serialbus),
	 0 },
	...
};
```

[`i2c_acpi_fill_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-acpi.c#L104) consumes the pointer as an [`acpi_dev_get_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1000) preproc, resolving the `resource_source` controller path to a handle and copying the I2C triple (the `0x48`, `400000`, and `AddressingMode7Bit` arguments of the example's I2cSerialBus macro) into the board info, with [`ACPI_I2C_10BIT_MODE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L431) selecting the ten-bit client flag:

```c
/* drivers/i2c/i2c-core-acpi.c:104 */
static int i2c_acpi_fill_info(struct acpi_resource *ares, void *data)
{
	struct i2c_acpi_lookup *lookup = data;
	struct i2c_board_info *info = lookup->info;
	struct acpi_resource_i2c_serialbus *sb;
	acpi_status status;

	if (info->addr || !i2c_acpi_get_i2c_resource(ares, &sb))
		return 1;

	if (lookup->index != -1 && lookup->n++ != lookup->index)
		return 1;

	status = acpi_get_handle(lookup->device_handle,
				 sb->resource_source.string_ptr,
				 &lookup->adapter_handle);
	if (ACPI_FAILURE(status))
		return 1;

	info->addr = sb->slave_address;
	lookup->speed = sb->connection_speed;
	if (sb->access_mode == ACPI_I2C_10BIT_MODE)
		info->flags |= I2C_CLIENT_TEN;

	return 1;
}
```

```c
/* drivers/i2c/i2c-core-acpi.c:157 */
	/* Look up for I2cSerialBus resource */
	INIT_LIST_HEAD(&resource_list);
	ret = acpi_dev_get_resources(adev, &resource_list,
				     i2c_acpi_fill_info, lookup);
	acpi_dev_free_resource_list(&resource_list);
```

The SPI core does the same against [`struct acpi_resource_spi_serialbus`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L433), translating `clock_phase`, `clock_polarity`, and `device_polarity` into the [`SPI_CPHA`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/spi/spi.h#L7), [`SPI_CPOL`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/spi/spi.h#L8), and [`SPI_CS_HIGH`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/spi/spi.h#L16) mode bits and reusing [`acpi_dev_resource_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L828) inline for any plain Interrupt record in the same template; [`acpi_spi_device_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/spi/spi.c#L2903) registers it as the preproc:

```c
/* drivers/spi/spi.c:2809 */
static int acpi_spi_add_resource(struct acpi_resource *ares, void *data)
{
	struct acpi_spi_lookup *lookup = data;
	struct spi_controller *ctlr = lookup->ctlr;

	if (ares->type == ACPI_RESOURCE_TYPE_SERIAL_BUS) {
		struct acpi_resource_spi_serialbus *sb;
		acpi_handle parent_handle;
		acpi_status status;

		sb = &ares->data.spi_serial_bus;
		if (sb->type == ACPI_RESOURCE_SERIAL_TYPE_SPI) {

			if (lookup->index != -1 && lookup->n++ != lookup->index)
				return 1;

			status = acpi_get_handle(NULL,
						 sb->resource_source.string_ptr,
						 &parent_handle);
			...
			if (ctlr->fw_translate_cs) {
				int cs = ctlr->fw_translate_cs(ctlr,
						sb->device_selection);
				if (cs < 0)
					return cs;
				lookup->chip_select = cs;
			} else {
				lookup->chip_select = sb->device_selection;
			}

			lookup->max_speed_hz = sb->connection_speed;
			lookup->bits_per_word = sb->data_bit_length;

			if (sb->clock_phase == ACPI_SPI_SECOND_PHASE)
				lookup->mode |= SPI_CPHA;
			if (sb->clock_polarity == ACPI_SPI_START_HIGH)
				lookup->mode |= SPI_CPOL;
			if (sb->device_polarity == ACPI_SPI_ACTIVE_HIGH)
				lookup->mode |= SPI_CS_HIGH;
		}
	} else if (lookup->irq < 0) {
		struct resource r;

		if (acpi_dev_resource_interrupt(ares, 0, &r))
			lookup->irq = r.start;
	}

	/* Always tell the ACPI core to skip this resource */
	return 1;
}
```

```c
/* drivers/spi/spi.c:2921 */
	INIT_LIST_HEAD(&resource_list);
	ret = acpi_dev_get_resources(adev, &resource_list,
				     acpi_spi_add_resource, &lookup);
	acpi_dev_free_resource_list(&resource_list);
```

serdev repeats the pattern for [`struct acpi_resource_uart_serialbus`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L463), where the filter and its caller resolve which UART controller the client node belongs to:

```c
/* drivers/tty/serdev/core.c:572 */
bool serdev_acpi_get_uart_resource(struct acpi_resource *ares,
				   struct acpi_resource_uart_serialbus **uart)
{
	struct acpi_resource_uart_serialbus *sb;

	if (ares->type != ACPI_RESOURCE_TYPE_SERIAL_BUS)
		return false;

	sb = &ares->data.uart_serial_bus;
	if (sb->type != ACPI_RESOURCE_SERIAL_TYPE_UART)
		return false;

	*uart = sb;
	return true;
}

static int acpi_serdev_parse_resource(struct acpi_resource *ares, void *data)
{
	struct acpi_serdev_lookup *lookup = data;
	struct acpi_resource_uart_serialbus *sb;
	acpi_status status;

	if (!serdev_acpi_get_uart_resource(ares, &sb))
		return 1;

	if (lookup->index != -1 && lookup->n++ != lookup->index)
		return 1;

	status = acpi_get_handle(lookup->device_handle,
				 sb->resource_source.string_ptr,
				 &lookup->controller_handle);
	if (ACPI_FAILURE(status))
		return 1;

	/*
	 * NOTE: Ideally, we would also want to retrieve other properties here,
	 * once setting them before opening the device is supported by serdev.
	 */

	return 1;
}
```

```c
/* drivers/tty/serdev/core.c:625 */
	INIT_LIST_HEAD(&resource_list);
	ret = acpi_dev_get_resources(adev, &resource_list,
				     acpi_serdev_parse_resource, lookup);
	acpi_dev_free_resource_list(&resource_list);
```

The FixedDMA consumer lives in the generic ACPI DMA helper library. [`acpi_dma_request_slave_chan_by_index()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/dma/acpi-dma.c#L351) walks `_CRS` with [`acpi_dma_parse_fixed_dma()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/dma/acpi-dma.c#L326) as the preproc, and the callback copies the [`struct acpi_resource_fixed_dma`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L186) pair (the `0x0018` request line and `0x0004` channel of the example's FixedDMA macro) into a DMA specifier the controller's xlate resolves to a channel:

```c
/* drivers/dma/acpi-dma.c:326 */
static int acpi_dma_parse_fixed_dma(struct acpi_resource *res, void *data)
{
	struct acpi_dma_parser_data *pdata = data;

	if (res->type == ACPI_RESOURCE_TYPE_FIXED_DMA) {
		struct acpi_resource_fixed_dma *dma = &res->data.fixed_dma;

		if (pdata->n++ == pdata->index) {
			pdata->dma_spec.chan_id = dma->channels;
			pdata->dma_spec.slave_id = dma->request_lines;
		}
	}

	/* Tell the ACPI core to skip this resource */
	return 1;
}
```

```c
/* drivers/dma/acpi-dma.c:370 */
	INIT_LIST_HEAD(&resource_list);
	ret = acpi_dev_get_resources(adev, &resource_list,
				     acpi_dma_parse_fixed_dma, &pdata);
	acpi_dev_free_resource_list(&resource_list);
```

All four consumers return 1 unconditionally, which under the [`acpi_dev_get_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1000) preproc contract suppresses the generic converter cascade for every record, so these walks produce an empty resource list and exist purely to capture union payloads.

### GpioInt walked end to end

The example template's GPIO line crosses every layer this page describes, so this section follows it stage by stage. The ASL source is the sensor's interrupt pin:

```asl
GpioInt (Level, ActiveLow, ExclusiveAndWake, PullUp, 0,
         "\\_SB.PCI0.GPI0", 0, ResourceConsumer,,) { 12 }
```

iASL compiles it into one 40-byte large item whose layout is exactly [`struct aml_resource_gpio`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/amlresrc.h#L281) followed by the two variable regions the offsets point at, with the keyword arguments packed into the `flags`, `int_flags`, and `pin_config` fields:

```
    GpioInt descriptor bytes, annotated against struct aml_resource_gpio
    ─────────────────────────────────────────────────────────────────────

    offset  bytes              field and decoded meaning
    ──────  ─────────────────  ─────────────────────────────────────────
     0      8C                 descriptor_type (large item, GPIO)
     1..2   25 00              resource_length = 37 (40 minus 3 header)
     3      01                 revision_id = 1
     4      00                 connection_type = 0 (GpioInt)
     5..6   01 00              flags: bit0 = 1, ResourceConsumer
     7..8   12 00              int_flags: bit0 = 0   Level trigger
                                 bits2:1 = 01        ActiveLow polarity
                                 bit3    = 0         Exclusive
                                 bit4    = 1         wake capable
     9      01                 pin_config = 1 (PullUp)
    10..11  00 00              drive_strength = 0 (GpioIo only)
    12..13  00 00              debounce_timeout = 0
    14..15  17 00              pin_table_offset = 23
    16      00                 res_source_index = 0
    17..18  19 00              res_source_offset = 25
    19..20  00 00              vendor_offset (ignored, vendor_length 0)
    21..22  00 00              vendor_length = 0
    23..24  0C 00              pin table: one u16 entry, pin 12
    25..39  5C 5F 53 42 2E 50  resource source string
            43 49 30 2E 47 50  "\_SB.PCI0.GPI0" plus NUL
            49 30 00
```

[`acpi_ut_validate_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utresrc.c#L266) maps tag 0x8C to dispatch index 0x1C, [`acpi_gbl_get_resource_dispatch[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsinfo.c#L57) selects [`acpi_rs_convert_gpio[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsserial.c#L20), and the interpreter runs its 18 entries top to bottom:

```c
/* drivers/acpi/acpica/rsserial.c:20 */
struct acpi_rsconvert_info acpi_rs_convert_gpio[18] = {
	{ACPI_RSC_INITGET, ACPI_RESOURCE_TYPE_GPIO,
	 ACPI_RS_SIZE(struct acpi_resource_gpio),
	 ACPI_RSC_TABLE_SIZE(acpi_rs_convert_gpio)},

	{ACPI_RSC_INITSET, ACPI_RESOURCE_NAME_GPIO,
	 sizeof(struct aml_resource_gpio),
	 0},

	/*
	 * These fields are contiguous in both the source and destination:
	 * revision_id
	 * connection_type
	 */
	{ACPI_RSC_MOVE8, ACPI_RS_OFFSET(data.gpio.revision_id),
	 AML_OFFSET(gpio.revision_id),
	 2},

	{ACPI_RSC_1BITFLAG, ACPI_RS_OFFSET(data.gpio.producer_consumer),
	 AML_OFFSET(gpio.flags),
	 0},

	{ACPI_RSC_1BITFLAG, ACPI_RS_OFFSET(data.gpio.shareable),
	 AML_OFFSET(gpio.int_flags),
	 3},

	{ACPI_RSC_1BITFLAG, ACPI_RS_OFFSET(data.gpio.wake_capable),
	 AML_OFFSET(gpio.int_flags),
	 4},

	{ACPI_RSC_2BITFLAG, ACPI_RS_OFFSET(data.gpio.io_restriction),
	 AML_OFFSET(gpio.int_flags),
	 0},

	{ACPI_RSC_1BITFLAG, ACPI_RS_OFFSET(data.gpio.triggering),
	 AML_OFFSET(gpio.int_flags),
	 0},

	{ACPI_RSC_2BITFLAG, ACPI_RS_OFFSET(data.gpio.polarity),
	 AML_OFFSET(gpio.int_flags),
	 1},

	{ACPI_RSC_MOVE8, ACPI_RS_OFFSET(data.gpio.pin_config),
	 AML_OFFSET(gpio.pin_config),
	 1},

	/*
	 * These fields are contiguous in both the source and destination:
	 * drive_strength
	 * debounce_timeout
	 */
	{ACPI_RSC_MOVE16, ACPI_RS_OFFSET(data.gpio.drive_strength),
	 AML_OFFSET(gpio.drive_strength),
	 2},

	/* Pin Table */

	{ACPI_RSC_COUNT_GPIO_PIN, ACPI_RS_OFFSET(data.gpio.pin_table_length),
	 AML_OFFSET(gpio.pin_table_offset),
	 AML_OFFSET(gpio.res_source_offset)},

	{ACPI_RSC_MOVE_GPIO_PIN, ACPI_RS_OFFSET(data.gpio.pin_table),
	 AML_OFFSET(gpio.pin_table_offset),
	 0},

	/* Resource Source */

	{ACPI_RSC_MOVE8, ACPI_RS_OFFSET(data.gpio.resource_source.index),
	 AML_OFFSET(gpio.res_source_index),
	 1},

	{ACPI_RSC_COUNT_GPIO_RES,
	 ACPI_RS_OFFSET(data.gpio.resource_source.string_length),
	 AML_OFFSET(gpio.res_source_offset),
	 AML_OFFSET(gpio.vendor_offset)},

	{ACPI_RSC_MOVE_GPIO_RES,
	 ACPI_RS_OFFSET(data.gpio.resource_source.string_ptr),
	 AML_OFFSET(gpio.res_source_offset),
	 0},

	/* Vendor Data */

	{ACPI_RSC_COUNT_GPIO_VEN, ACPI_RS_OFFSET(data.gpio.vendor_length),
	 AML_OFFSET(gpio.vendor_length),
	 1},

	{ACPI_RSC_MOVE_GPIO_RES, ACPI_RS_OFFSET(data.gpio.vendor_data),
	 AML_OFFSET(gpio.vendor_offset),
	 0},
};
```

Applied to the bytes above, the [`ACPI_RSC_2BITFLAG`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acresrc.h#L47) entry at bit 1 extracts polarity 01 from `int_flags` 0x12 while the [`ACPI_RSC_1BITFLAG`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acresrc.h#L46) entries pull triggering 0 from bit 0, shareable 0 from bit 3, and wake 1 from bit 4 (the `io_restriction` entry also decodes bits 1:0, a field only GpioIo consumers trust, since [`commit 9cea6249c915`](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=9cea6249c9154a7d0b322a226261697f947692ad) split the shared bits into separate struct fields per connection type). The [`ACPI_RSC_COUNT_GPIO_PIN`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acresrc.h#L55) entry computes the pin count as (`res_source_offset` 25 minus `pin_table_offset` 23) / 2 = 1, [`ACPI_RSC_MOVE_GPIO_PIN`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acresrc.h#L65) plants `pin_table` into the record tail and copies the word 12, and [`ACPI_RSC_COUNT_GPIO_RES`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acresrc.h#L56) sees `vendor_length` 0 and therefore measures the string against the descriptor end, total length 40 minus offset 25 = 15 bytes including the NUL. The decoded record reads:

```
    struct acpi_resource for the GpioInt cell, after conversion
    ────────────────────────────────────────────────────────────
    .type   = ACPI_RESOURCE_TYPE_GPIO (17)
    .length = ACPI_RS_SIZE(struct acpi_resource_gpio)
              + 2 (pin table) + 15 (source string), rounded up

    .data.gpio.revision_id                    = 1
    .data.gpio.connection_type                = ACPI_RESOURCE_GPIO_TYPE_INT (0)
    .data.gpio.producer_consumer              = ACPI_CONSUMER (1)
    .data.gpio.pin_config                     = ACPI_PIN_CONFIG_PULLUP (1)
    .data.gpio.shareable                      = ACPI_EXCLUSIVE (0)
    .data.gpio.wake_capable                   = ACPI_WAKE_CAPABLE (1)
    .data.gpio.io_restriction                 = 2 (GpioIo field, decoded too)
    .data.gpio.triggering                     = ACPI_LEVEL_SENSITIVE (0)
    .data.gpio.polarity                       = ACPI_ACTIVE_LOW (1)
    .data.gpio.drive_strength                 = 0
    .data.gpio.debounce_timeout               = 0
    .data.gpio.pin_table_length               = 1
    .data.gpio.vendor_length                  = 0
    .data.gpio.resource_source.string_length  = 15
    .data.gpio.resource_source.string_ptr     = "\_SB.PCI0.GPI0"
    .data.gpio.pin_table[0]                   = 12
```

The consumer side starts at the driver-facing wrapper. The sensor driver asks for its interrupt with [`acpi_dev_gpio_irq_get()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1324) (the same call [`pnpacpi_allocated_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L164) makes when it meets a GpioInt, shown earlier), and the wrapper chain ends in [`acpi_dev_gpio_irq_wake_get_by()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L996):

```c
/* include/linux/acpi.h:1324 */
static inline int acpi_dev_gpio_irq_get(struct acpi_device *adev, int index)
{
	return acpi_dev_gpio_irq_wake_get_by(adev, NULL, index, NULL);
}
```

The lookup machinery underneath fetches the decoded records through the standard walk. [`acpi_get_gpiod_by_index()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L828) fills a [`struct acpi_gpio_lookup`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L679) context (resolving any `_DSD` property name to a `crs_entry_index` first) and tail-calls [`acpi_gpio_resource_lookup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L742), which is a textbook [`acpi_dev_get_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1000) caller:

```c
/* drivers/gpio/gpiolib-acpi-core.c:845 */
	} else {
		dev_dbg(&adev->dev, "GPIO: looking up %u in _CRS\n", params->crs_entry_index);
		info->adev = adev;
	}

	return acpi_gpio_resource_lookup(lookup);
}
```

```c
/* drivers/gpio/gpiolib-acpi-core.c:679 */
struct acpi_gpio_lookup {
	struct acpi_gpio_params params;
	struct acpi_gpio_info *info;
	struct gpio_desc *desc;
	int n;
};
```

```c
/* drivers/gpio/gpiolib-acpi-core.c:742 */
static int acpi_gpio_resource_lookup(struct acpi_gpio_lookup *lookup)
{
	struct acpi_gpio_info *info = lookup->info;
	struct acpi_device *adev = info->adev;
	struct list_head res_list;
	int ret;

	INIT_LIST_HEAD(&res_list);

	ret = acpi_dev_get_resources(adev, &res_list,
				     acpi_populate_gpio_lookup,
				     lookup);
	if (ret < 0)
		return ret;

	acpi_dev_free_resource_list(&res_list);

	if (!lookup->desc)
		return -ENOENT;

	return 0;
}
```

[`acpi_populate_gpio_lookup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L686) is the stage that finally reads the union member the conversion produced. It filters on [`ACPI_RESOURCE_TYPE_GPIO`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L626), counts GPIO records until it reaches the requested `crs_entry_index`, indexes `pin_table[]` with the requested `line_index`, resolves the `resource_source` path plus controller-relative pin into a GPIO descriptor, and copies `pin_config`, `debounce_timeout`, `triggering`, and `polarity` into a [`struct acpi_gpio_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L83):

```c
/* drivers/gpio/gpiolib-acpi-core.c:71 */
/**
 * struct acpi_gpio_info - ACPI GPIO specific information
 * @adev: reference to ACPI device which consumes GPIO resource
 * @flags: GPIO initialization flags
 * @gpioint: if %true this GPIO is of type GpioInt otherwise type is GpioIo
 * @wake_capable: wake capability as provided by ACPI
 * @pin_config: pin bias as provided by ACPI
 * @polarity: interrupt polarity as provided by ACPI
 * @triggering: triggering type as provided by ACPI
 * @debounce: debounce timeout as provided by ACPI
 * @quirks: Linux specific quirks as provided by struct acpi_gpio_mapping
 */
struct acpi_gpio_info {
	struct acpi_device *adev;
	enum gpiod_flags flags;
	bool gpioint;
	bool wake_capable;
	int pin_config;
	int polarity;
	int triggering;
	unsigned int debounce;
	unsigned int quirks;
};
```

```c
/* drivers/gpio/gpiolib-acpi-core.c:686 */
static int acpi_populate_gpio_lookup(struct acpi_resource *ares, void *data)
{
	struct acpi_gpio_lookup *lookup = data;
	struct acpi_gpio_params *params = &lookup->params;
	struct acpi_gpio_info *info = lookup->info;

	if (ares->type != ACPI_RESOURCE_TYPE_GPIO)
		return 1;

	if (!lookup->desc) {
		const struct acpi_resource_gpio *agpio = &ares->data.gpio;
		bool gpioint = agpio->connection_type == ACPI_RESOURCE_GPIO_TYPE_INT;
		struct gpio_desc *desc;
		u16 pin_index;

		if (info->quirks & ACPI_GPIO_QUIRK_ONLY_GPIOIO && gpioint)
			params->crs_entry_index++;

		if (lookup->n++ != params->crs_entry_index)
			return 1;

		pin_index = params->line_index;
		if (pin_index >= agpio->pin_table_length)
			return 1;

		if (info->quirks & ACPI_GPIO_QUIRK_ABSOLUTE_NUMBER)
			desc = gpio_to_desc(agpio->pin_table[pin_index]);
		else
			desc = acpi_get_gpiod(agpio->resource_source.string_ptr,
					      agpio->pin_table[pin_index]);
		lookup->desc = desc;
		info->pin_config = agpio->pin_config;
		info->debounce = agpio->debounce_timeout;
		info->gpioint = gpioint;
		info->wake_capable = acpi_gpio_irq_is_wake(&info->adev->dev, agpio);

		/*
		 * Polarity and triggering are only specified for GpioInt
		 * resource.
		 * Note: we expect here:
		 * - ACPI_ACTIVE_LOW == GPIO_ACTIVE_LOW
		 * - ACPI_ACTIVE_HIGH == GPIO_ACTIVE_HIGH
		 */
		if (info->gpioint) {
			info->polarity = agpio->polarity;
			info->triggering = agpio->triggering;
		} else {
			info->polarity = params->active_low;
		}

		info->flags = acpi_gpio_to_gpiod_flags(agpio, info->polarity);
	}

	return 1;
}
```

According to the comment "Polarity and triggering are only specified for GpioInt resource", the GpioIo path ignores those two decoded fields and takes polarity from the `_DSD` cell instead, which is the consumer-side half of the dual decode noted at the conversion table. Back in [`acpi_dev_gpio_irq_wake_get_by()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L996), the captured info configures the line and the IRQ. For the example descriptor, `info.triggering` [`ACPI_LEVEL_SENSITIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L58) and `info.polarity` [`ACPI_ACTIVE_LOW`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L64) become [`IRQ_TYPE_LEVEL_LOW`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/irq.h#L82) through [`acpi_dev_get_irq_type()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L368), and the wake bit from `int_flags` surfaces through the `wake_capable` out-parameter:

```c
/* drivers/gpio/gpiolib-acpi-core.c:1029 */
		if (info.gpioint && idx++ == index) {
			unsigned long lflags = GPIO_LOOKUP_FLAGS_DEFAULT;
			enum gpiod_flags dflags = GPIOD_ASIS;
			char label[32];
			int irq;

			if (IS_ERR(desc))
				return PTR_ERR(desc);

			irq = gpiod_to_irq(desc);
			if (irq < 0)
				return irq;
			...
			ret = gpiod_configure_flags(desc, label, lflags, dflags);
			if (ret < 0)
				return ret;

			/* ACPI uses hundredths of milliseconds units */
			ret = gpio_set_debounce_timeout(desc, info.debounce * 10);
			if (ret)
				return ret;

			irq_flags = acpi_dev_get_irq_type(info.triggering,
							  info.polarity);

			/*
			 * If the IRQ is not already in use then set type
			 * if specified and different than the current one.
			 */
			if (can_request_irq(irq, irq_flags)) {
				if (irq_flags != IRQ_TYPE_NONE &&
				    irq_flags != irq_get_trigger_type(irq))
					irq_set_irq_type(irq, irq_flags);
			} else {
				dev_dbg(&adev->dev, "IRQ %d already in use\n", irq);
			}

			/* avoid suspend issues with GPIOs when systems are using S3 */
			if (wake_capable && acpi_gbl_FADT.flags & ACPI_FADT_LOW_POWER_S0)
				*wake_capable = info.wake_capable;

			return irq;
		}
```

A second gpiolib consumer reads the same union member on a different path. When a GPIO controller's `_AEI` object lists GpioInt event pins, [`acpi_gpiochip_request_interrupts()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L460) walks them during controller registration:

```c
/* drivers/gpio/gpiolib-acpi-core.c:480 */
	acpi_walk_resources(handle, METHOD_NAME__AEI,
			    acpi_gpiochip_alloc_event, acpi_gpio);
```

[`acpi_gpiochip_alloc_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L343) then runs once per record, filters with [`acpi_gpio_get_irq_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpio/gpiolib-acpi-core.c#L175), derives the `_E0C`/`_L0C`-style handler name from `triggering` plus `pin_table[0]`, and folds `triggering` and `polarity` into request flags such as [`IRQF_TRIGGER_LOW`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/interrupt.h#L35):

```c
/* drivers/gpio/gpiolib-acpi-core.c:175 */
bool acpi_gpio_get_irq_resource(struct acpi_resource *ares,
				struct acpi_resource_gpio **agpio)
{
	struct acpi_resource_gpio *gpio;

	if (ares->type != ACPI_RESOURCE_TYPE_GPIO)
		return false;

	gpio = &ares->data.gpio;
	if (gpio->connection_type != ACPI_RESOURCE_GPIO_TYPE_INT)
		return false;

	*agpio = gpio;
	return true;
}
```

```c
/* drivers/gpio/gpiolib-acpi-core.c:343 */
static acpi_status acpi_gpiochip_alloc_event(struct acpi_resource *ares,
					     void *context)
{
	struct acpi_gpio_chip *acpi_gpio = context;
	struct gpio_chip *chip = acpi_gpio->chip;
	struct acpi_resource_gpio *agpio;
	acpi_handle handle, evt_handle;
	struct acpi_gpio_event *event;
	irq_handler_t handler = NULL;
	struct gpio_desc *desc;
	unsigned int pin;
	int ret, irq;

	if (!acpi_gpio_get_irq_resource(ares, &agpio))
		return AE_OK;

	handle = ACPI_HANDLE(chip->parent);
	pin = agpio->pin_table[0];

	if (pin <= 255) {
		char ev_name[8];
		sprintf(ev_name, "_%c%02X",
			agpio->triggering == ACPI_EDGE_SENSITIVE ? 'E' : 'L',
			pin);
		if (ACPI_SUCCESS(acpi_get_handle(handle, ev_name, &evt_handle)))
			handler = acpi_gpio_irq_handler;
	}
	if (!handler) {
		if (ACPI_SUCCESS(acpi_get_handle(handle, "_EVT", &evt_handle)))
			handler = acpi_gpio_irq_handler_evt;
	}
	if (!handler)
		return AE_OK;
	...
	event->irqflags = IRQF_ONESHOT;
	if (agpio->triggering == ACPI_LEVEL_SENSITIVE) {
		if (agpio->polarity == ACPI_ACTIVE_HIGH)
			event->irqflags |= IRQF_TRIGGER_HIGH;
		else
			event->irqflags |= IRQF_TRIGGER_LOW;
	} else {
		switch (agpio->polarity) {
		case ACPI_ACTIVE_HIGH:
			event->irqflags |= IRQF_TRIGGER_RISING;
			break;
		case ACPI_ACTIVE_LOW:
			event->irqflags |= IRQF_TRIGGER_FALLING;
			break;
		default:
			event->irqflags |= IRQF_TRIGGER_RISING |
					   IRQF_TRIGGER_FALLING;
			break;
		}
	}
	...
	return AE_OK;
}
```

Summed up for the example line, the ASL keywords `Level`, `ActiveLow`, `ExclusiveAndWake`, and `PullUp` traveled as four bit fields inside two bytes of the 0x8C descriptor, became the four `u8` fields `triggering` 0, `polarity` 1, `wake_capable` 1, and `pin_config` 1 of [`struct acpi_resource_gpio`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L355) under [`ACPI_RESOURCE_TYPE_GPIO`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L626), and surfaced to the driver as a Linux IRQ programmed [`IRQ_TYPE_LEVEL_LOW`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/irq.h#L82) on pin 12 of the controller named by the descriptor's `resource_source` string, which is the complete macro-to-consumer mapping in one descriptor.
