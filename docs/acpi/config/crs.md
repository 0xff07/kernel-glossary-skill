# _CRS

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

`_CRS` is the Current Resource Settings method that every resource-consuming ACPI device object carries. Evaluating it returns a Buffer holding a stream of byte-encoded resource descriptors terminated by an End Tag, and the kernel fetches that stream through ACPICA, either as one decoded block via [`acpi_get_current_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L167) or descriptor by descriptor via [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) with the [`METHOD_NAME__CRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L21) name string. ACPICA parses the raw AML bytes into [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678) records through the [`acpi_rs_convert_aml_to_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rslist.c#L30) chain, and the Linux layer in [`drivers/acpi/resource.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c) converts those records into generic [`struct resource`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L22) objects collected on a [`struct resource_entry`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/resource_ext.h#L23) list by [`acpi_dev_get_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1000). Consumers range from [`acpi_create_platform_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_platform.c#L110), which turns the list into platform-device resources, through the EC's [`ec_parse_io_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1776) port extraction, to the I2C core's [`i2c_acpi_fill_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-acpi.c#L104), which reads I2cSerialBus connectors out of the same stream.

```
    _CRS Buffer as a tagged descriptor stream
    ─────────────────────────────────────────

    AML bytes (one tag + length + payload per descriptor, End Tag last)
    ┌────────────────┬──────────────┬──────────────┬──────┬─────────┐
    │ Memory32Fixed  │  Interrupt   │  GpioInt     │ ...  │ End Tag │
    │ (0x86, large)  │ (0x89, large)│ (0x8C, large)│      │ (0x79)  │
    └───────┬────────┴──────┬───────┴──────┬───────┴──────┴─────────┘
            │               │              │           (terminates
            ▼               ▼              ▼            the walk)
    struct acpi_resource  struct acpi_resource  struct acpi_resource
    ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
    │ .type = ACPI_     │ │ .type = ACPI_     │ │ .type = ACPI_     │
    │  RESOURCE_TYPE_   │ │  RESOURCE_TYPE_   │ │  RESOURCE_TYPE_   │
    │  FIXED_MEMORY32   │ │  EXTENDED_IRQ     │ │  GPIO             │
    │ .data.            │ │ .data.            │ │ .data.gpio        │
    │  fixed_memory32   │ │  extended_irq     │ │   .pin_table[0]   │
    │   .address        │ │   .interrupts[0]  │ │   .triggering     │
    │   .address_length │ │   .triggering     │ │   .polarity       │
    └───────────────────┘ └───────────────────┘ └───────────────────┘

    (each stream cell is one descriptor; bit 7 of the first byte
     selects the large encoding, the End Tag byte 0x79 is the small
     item 0x0F with length 1; every decoded record is the fixed
     header type/length plus one union acpi_resource_data member,
     and ACPI_NEXT_RESOURCE() steps from record to record)
```

## SUMMARY

The ACPI specification defines `_CRS` in section 6.2.2 as a zero-argument object that returns "a byte stream that describes the system resources currently allocated to a device", encoded as the resource data types of section 6.4. Each descriptor in the stream is either a small item (first byte carries the type in bits 6:3 and the payload length in bits 2:0) or a large item (bit 7 set, type in bits 6:0, 16-bit length in the next two bytes), and the stream ends with the End Tag small item. The kernel mirrors this encoding in [`ACPI_RESOURCE_NAME_LARGE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1097), [`ACPI_RESOURCE_NAME_SMALL_MASK`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1100), and the per-descriptor tag constants such as [`ACPI_RESOURCE_NAME_END_TAG`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1119) (0x78) and [`ACPI_RESOURCE_NAME_MEMORY32`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1129) (0x85). ACPICA evaluates the method through [`acpi_rs_get_crs_method_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsutils.c#L483), requires an [`ACPI_BTYPE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L256) return, and hands the raw bytes to [`acpi_rs_create_resource_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rscreate.c#L103), which sizes an output buffer and lets [`acpi_ut_walk_aml_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utresrc.c#L141) drive [`acpi_rs_convert_aml_to_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rslist.c#L30) once per descriptor, producing an array of [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678) records whose `type` field selects one member of [`union acpi_resource_data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L639).

Two public ACPICA entry points expose the decoded list. [`acpi_get_current_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L167) fills a caller-provided [`struct acpi_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978) with the whole block, and [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) fetches the same block internally and lets [`acpi_walk_resource_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L506) run a callback over each record until the [`ACPI_RESOURCE_TYPE_END_TAG`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L616) record or an [`AE_CTRL_TERMINATE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L186) return. On top of that sits the Linux helper layer in [`drivers/acpi/resource.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c). [`acpi_dev_get_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1000) walks `_CRS` with the [`acpi_dev_process_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L908) callback, which first offers each record to an optional caller preprocessing hook and then tries the per-type converters [`acpi_dev_resource_memory()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L107), [`acpi_dev_resource_io()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L180), [`acpi_dev_resource_address_space()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L290), [`acpi_dev_resource_ext_address_space()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L319), and [`acpi_dev_resource_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L828) in order, materializing one [`struct resource_entry`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/resource_ext.h#L23) per converted record through [`resource_list_create_entry()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/resource.c#L1936). [`acpi_dev_free_resource_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L877) releases the list, and the filtered variants [`acpi_dev_get_memory_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1058) and [`acpi_dev_get_dma_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1040) parameterize the same walk with the [`is_memory()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1009) preprocessing filter and, for the latter, the `_DMA` method name.

The consumers documented here are vendor neutral and cover the three shapes a `_CRS` reader takes. [`acpi_create_platform_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_platform.c#L110) runs the full conversion and copies every [`struct resource`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L22) into the [`struct platform_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L23) it registers, so platform drivers later fetch them with [`platform_get_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/platform.c#L55) and its siblings. The EC driver's [`ec_parse_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1460) bypasses the Linux conversion layer and walks the raw records with [`ec_parse_io_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1776), keeping only the two [`ACPI_RESOURCE_TYPE_IO`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L613) port numbers in [`struct acpi_ec`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194). The I2C core demonstrates the preprocessing-hook shape, where [`i2c_acpi_do_lookup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-acpi.c#L145) passes [`i2c_acpi_fill_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-acpi.c#L104) as the preproc argument so the serial-bus descriptor, which has no [`struct resource`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L22) equivalent, is captured into a [`struct i2c_board_info`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/i2c.h#L425) instead.

## SPECIFICATIONS

- ACPI Specification, section 6.2: Device Configuration Objects
- ACPI Specification, section 6.2.2: _CRS (Current Resource Settings)
- ACPI Specification, section 6.4: Resource Data Types for ACPI
- ACPI Specification, section 6.4.1: ASL Macros for Resource Descriptors
- ACPI Specification, section 6.4.2: Small Resource Data Type
- ACPI Specification, section 6.4.3: Large Resource Data Type
- ACPI Specification, section 6.4.3.5: Address Space Resource Descriptors
- ACPI Specification, section 19.3.3: ASL Resource Templates

## LINUX KERNEL

### ACPICA fetch layer

- [`'\<acpi_get_current_resources\>':'drivers/acpi/acpica/rsxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L167): public block fetch, fills a caller buffer with the decoded `_CRS` list
- [`'\<acpi_walk_resources\>':'drivers/acpi/acpica/rsxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594): public per-descriptor walk over `_CRS`, `_PRS`, `_AEI`, or `_DMA`
- [`'\<acpi_walk_resource_buffer\>':'drivers/acpi/acpica/rsxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L506): iterates a decoded buffer and invokes the callback per record
- [`'\<acpi_rs_get_crs_method_data\>':'drivers/acpi/acpica/rsutils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsutils.c#L483): evaluates `_CRS` and builds the decoded list
- [`'\<acpi_rs_get_method_data\>':'drivers/acpi/acpica/rsutils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsutils.c#L637): name-parameterized variant used by the walk entry point
- [`METHOD_NAME__CRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L21): the `"_CRS"` name string macro
- [`'\<struct acpi_buffer\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978): length/pointer pair carrying the decoded list

### AML byte stream to struct acpi_resource

- [`'\<acpi_rs_create_resource_list\>':'drivers/acpi/acpica/rscreate.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rscreate.c#L103): sizes the output buffer and runs the conversion walk
- [`'\<acpi_ut_walk_aml_resources\>':'drivers/acpi/acpica/utresrc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utresrc.c#L141): validates and steps the raw byte stream descriptor by descriptor
- [`'\<acpi_rs_convert_aml_to_resources\>':'drivers/acpi/acpica/rslist.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rslist.c#L30): per-descriptor dispatch into the conversion tables
- [`'\<struct acpi_resource\>':'include/acpi/acrestyp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678): decoded record, type/length header plus payload union
- [`'\<union acpi_resource_data\>':'include/acpi/acrestyp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L639): master payload union, one member per descriptor kind
- [`ACPI_NEXT_RESOURCE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L694): steps from one decoded record to the next
- [`ACPI_RESOURCE_NAME_LARGE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1097): bit 7 marker separating large from small descriptor tags
- [`ACPI_RESOURCE_TYPE_END_TAG`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L616): decoded type value of the stream-terminating End Tag

### Linux conversion layer

- [`'\<acpi_dev_get_resources\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1000): walks `_CRS` and builds the [`struct resource_entry`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/resource_ext.h#L23) list
- [`'\<__acpi_dev_get_resources\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L947): method-name-parameterized core shared with the `_DMA` variant
- [`'\<acpi_dev_process_resource\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L908): per-record callback, preproc hook plus converter cascade
- [`'\<struct res_proc_context\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L883): walk context carrying list head, preproc, count, and error
- [`'\<acpi_dev_new_resource_entry\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L891): wraps one converted resource into a list entry
- [`'\<acpi_dev_resource_memory\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L107): Memory24/Memory32/Memory32Fixed converter
- [`'\<acpi_dev_resource_io\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L180): IO/FixedIO converter
- [`'\<acpi_dev_resource_interrupt\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L828): IRQ/Interrupt converter, one GSI per call index
- [`'\<acpi_dev_resource_address_space\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L290): WordIO/DWordMemory/QWordMemory address-space converter
- [`'\<acpi_dev_resource_ext_address_space\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L319): ExtendedSpace converter
- [`'\<acpi_decode_space\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L207): shared min/max/offset/flags decoding for both address-space converters
- [`'\<acpi_dev_irq_flags\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L342): maps triggering/polarity/shareable/wake onto `IORESOURCE_IRQ_*` bits
- [`'\<acpi_dev_free_resource_list\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L877): frees every entry produced by the walk
- [`'\<acpi_dev_get_memory_resources\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1058): memory-only `_CRS` walk via the [`is_memory()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1009) filter
- [`'\<acpi_dev_get_dma_resources\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1040): same walk pointed at the `_DMA` method
- [`'\<acpi_dev_filter_resource_type\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1073): reusable preproc that filters records by `IORESOURCE_*` class
- [`'\<is_memory\>':'drivers/acpi/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1009): preproc used by both filtered variants

### Resource list management

- [`'\<struct resource\>':'include/linux/ioport.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L22): generic start/end/flags resource object the converters fill
- [`'\<struct resource_win\>':'include/linux/resource_ext.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/resource_ext.h#L14): resource plus bridge translation offset, used for address-space windows
- [`'\<struct resource_entry\>':'include/linux/resource_ext.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/resource_ext.h#L23): list node owning one converted resource
- [`'\<resource_list_create_entry\>':'kernel/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/resource.c#L1936): allocates an entry with embedded default storage
- [`'\<resource_list_add_tail\>':'include/linux/resource_ext.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/resource_ext.h#L40): appends an entry to the caller's list
- [`'\<resource_list_free\>':'kernel/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/resource.c#L1951): destroys every entry on a list

### Consumers

- [`'\<acpi_create_platform_device\>':'drivers/acpi/acpi_platform.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_platform.c#L110): converts the `_CRS` list into [`struct platform_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/platform_device.h#L23) resources
- [`'\<acpi_platform_fill_resource\>':'drivers/acpi/acpi_platform.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_platform.c#L74): copies one entry and links a PCI parent resource when present
- [`'\<acpi_default_enumeration\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2245): scan-time caller that creates the platform device
- [`'\<ec_parse_device\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1460): EC discovery callback that launches the `_CRS` walk
- [`'\<ec_parse_io_ports\>':'drivers/acpi/ec.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1776): keeps the first two IO descriptors as data and command ports
- [`'\<struct acpi_ec\>':'drivers/acpi/internal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/internal.h#L194): EC state carrying `data_addr` and `command_addr`
- [`'\<i2c_acpi_register_devices\>':'drivers/i2c/i2c-core-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-acpi.c#L320): namespace walk that enumerates I2C slaves behind an adapter
- [`'\<i2c_acpi_get_info\>':'drivers/i2c/i2c-core-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-acpi.c#L232): builds the board info for one candidate slave node
- [`'\<i2c_acpi_do_lookup\>':'drivers/i2c/i2c-core-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-acpi.c#L145): runs the `_CRS` walk with the serial-bus preproc
- [`'\<i2c_acpi_fill_info\>':'drivers/i2c/i2c-core-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-acpi.c#L104): preproc that captures the I2cSerialBus payload
- [`'\<i2c_acpi_get_i2c_resource\>':'drivers/i2c/i2c-core-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-acpi.c#L55): type filter for [`ACPI_RESOURCE_TYPE_SERIAL_BUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L628) records
- [`'\<struct i2c_acpi_lookup\>':'drivers/i2c/i2c-core-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-acpi.c#L33): walk context pairing board info with the adapter handle
- [`'\<struct acpi_resource_i2c_serialbus\>':'include/acpi/acrestyp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L422): decoded I2cSerialBus descriptor payload

## KERNEL DOCUMENTATION

- [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst): how `_CRS` connector resources steer enumeration onto platform, I2C, and SPI buses
- [`Documentation/PCI/acpi-info.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/PCI/acpi-info.rst): `_CRS` as the generalized BAR for host bridge windows and builtin devices
- [`Documentation/firmware-guide/acpi/namespace.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/namespace.rst): the namespace scan that produces the device nodes whose `_CRS` is read
- [`Documentation/driver-api/acpi/linuxized-acpica.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/acpi/linuxized-acpica.rst): maintenance model of the imported ACPICA code implementing the fetch and decode

## OTHER SOURCES

- [ACPI Specification 6.5, chapter 6: Device Configuration](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html)
- [ACPI Specification 6.5, chapter 19: ASL Reference](https://uefi.org/specs/ACPI/6.5/19_ASL_Reference.html)
- [Commit 8e345c991c8c ("ACPI: Centralized processing of ACPI device resources")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=8e345c991c8c7a3c081199ef77deada79e37618a)
- [Commit 046d9ce6820e ("ACPI: Move device resources interpretation code from PNP to ACPI core")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=046d9ce6820e99087e81511284045eada94950e8)
- [Commit 907ddf89d0bb ("i2c / ACPI: add ACPI enumeration support")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=907ddf89d0bb7f57e1e21485900e6564a1ab512a)

## METHODS

### _CRS (current resource settings, 0 arguments)

`_CRS` is a spec-defined object name with no function definition in the kernel; the kernel addresses it through the [`METHOD_NAME__CRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L21) string macro from the ACPICA name table. Section 6.2.2 requires it to return a Buffer whose content is the byte stream of section 6.4 descriptors, and ACPICA enforces the Buffer type by passing [`ACPI_BTYPE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L256) to its internal evaluator inside [`acpi_rs_get_crs_method_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsutils.c#L483). The object can be a static `Name (_CRS, ResourceTemplate () {...})` or a `Method` that computes the template at run time, and the interpreter path is identical for both because [`acpi_ut_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/uteval.c#L37) resolves either form to a buffer object. The kernel evaluates `_CRS` on demand, each time one of the fetch APIs runs. [`acpi_default_enumeration()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2245) triggers it during the namespace scan when it creates a platform device, [`i2c_acpi_register_devices()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-acpi.c#L320) triggers it again for every candidate slave when an adapter registers, and the EC driver triggers it whenever [`ec_parse_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1460) probes a `PNP0C09` node, so a `Method`-form `_CRS` runs once per fetch and its return value is decoded fresh each time. The three fetch APIs are [`acpi_get_current_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L167) for a raw decoded block, [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) for callback iteration, and [`acpi_dev_get_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1000) for the converted [`struct resource_entry`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/resource_ext.h#L23) list; the last one short-circuits to a zero count through [`acpi_has_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L668) when the device lacks the object, since `_CRS` is optional for devices that consume no resources.

## DETAILS

### A complete _CRS ResourceTemplate and the stream it compiles to

The following ASL declares a memory-mapped controller in the style of the spec examples, with one fixed memory window, one extended interrupt, and one GPIO interrupt line, which exercises three different descriptor encodings in a single template:

```asl
Device (\_SB.DEVX)
{
    Name (_HID, "XYZ0001")              // fictional spec-style HID
    Name (_UID, 0)
    Name (_CRS, ResourceTemplate ()
    {
        Memory32Fixed (ReadWrite, 0xFED40000, 0x00001000)
        Interrupt (ResourceConsumer, Level, ActiveHigh, Exclusive) { 42 }
        GpioInt (Edge, ActiveLow, Exclusive, PullUp, ,
                 "\\_SB.GPI0") { 17 }
    })                                  // iASL appends the End Tag
}
```

Evaluating this `_CRS` returns a Buffer whose bytes follow the section 6.4 encoding. Each descriptor starts with a tag byte; bit 7 distinguishes the two families, the small family packs the item type into bits 6:3 and the payload length into bits 2:0, and the large family keeps the type in bits 6:0 with a 16-bit length in the following two bytes. The kernel carries this encoding as constants in the ACPICA-private header, and the same table names the tag values for every descriptor the example uses:

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
...
#define ACPI_RESOURCE_NAME_END_TAG              0x78

/*
 * Large resource descriptor "names" as defined by the ACPI specification.
 * Note: includes the Large Descriptor bit in bit[7]
 */
#define ACPI_RESOURCE_NAME_MEMORY24             0x81
...
#define ACPI_RESOURCE_NAME_MEMORY32             0x85
#define ACPI_RESOURCE_NAME_FIXED_MEMORY32       0x86
#define ACPI_RESOURCE_NAME_ADDRESS32            0x87
#define ACPI_RESOURCE_NAME_ADDRESS16            0x88
#define ACPI_RESOURCE_NAME_EXTENDED_IRQ         0x89
#define ACPI_RESOURCE_NAME_ADDRESS64            0x8A
#define ACPI_RESOURCE_NAME_EXTENDED_ADDRESS64   0x8B
#define ACPI_RESOURCE_NAME_GPIO                 0x8C
```

The `Memory32Fixed` macro emits the large item 0x86, `Interrupt` emits 0x89, `GpioInt` emits 0x8C, and the compiler closes the template with the small End Tag whose first byte is 0x79 ([`ACPI_RESOURCE_NAME_END_TAG`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1119) 0x78 with length bits 001 for the checksum byte). Decoding turns each stream cell into one [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678) record, the fixed header plus the [`union acpi_resource_data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L639) payload whose member is selected by `type`:

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
	...
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

The `type` values are a separate, stable enumeration decoupled from the AML tag bytes, so the Memory32Fixed cell arrives as [`ACPI_RESOURCE_TYPE_FIXED_MEMORY32`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L619) (10) with the payload in `data.fixed_memory32`, the Interrupt cell as [`ACPI_RESOURCE_TYPE_EXTENDED_IRQ`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L624) (15) in `data.extended_irq`, and the GpioInt cell as [`ACPI_RESOURCE_TYPE_GPIO`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L626) (17) in `data.gpio`:

```c
/* include/acpi/acrestyp.h:609 */
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
```

### ACPICA fetch: acpi_get_current_resources and the _CRS evaluator

[`acpi_get_current_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L167) is the block-fetch entry point. It validates the handle and the caller's [`struct acpi_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978), then delegates to the `_CRS`-specific evaluator:

```c
/* drivers/acpi/acpica/rsxface.c:166 */
acpi_status
acpi_get_current_resources(acpi_handle device_handle,
			   struct acpi_buffer *ret_buffer)
{
	acpi_status status;
	struct acpi_namespace_node *node;

	ACPI_FUNCTION_TRACE(acpi_get_current_resources);

	/* Validate parameters then dispatch to internal routine */

	status = acpi_rs_validate_parameters(device_handle, ret_buffer, &node);
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}

	status = acpi_rs_get_crs_method_data(node, ret_buffer);
	return_ACPI_STATUS(status);
}

ACPI_EXPORT_SYMBOL(acpi_get_current_resources)
```

[`acpi_rs_get_crs_method_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsutils.c#L483) runs the interpreter on the `_CRS` object, demands a Buffer-typed result, and converts the returned byte stream into the decoded record list before dropping the interpreter object:

```c
/* drivers/acpi/acpica/rsutils.c:482 */
acpi_status
acpi_rs_get_crs_method_data(struct acpi_namespace_node *node,
			    struct acpi_buffer *ret_buffer)
{
	union acpi_operand_object *obj_desc;
	acpi_status status;

	ACPI_FUNCTION_TRACE(rs_get_crs_method_data);

	/* Parameters guaranteed valid by caller */

	/* Execute the method, no parameters */

	status =
	    acpi_ut_evaluate_object(node, METHOD_NAME__CRS, ACPI_BTYPE_BUFFER,
				    &obj_desc);
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}

	/*
	 * Make the call to create a resource linked list from the
	 * byte stream buffer that comes back from the _CRS method
	 * execution.
	 */
	status = acpi_rs_create_resource_list(obj_desc, ret_buffer);

	/* On exit, we must delete the object returned by evaluateObject */

	acpi_ut_remove_reference(obj_desc);
	return_ACPI_STATUS(status);
}
```

The name string it passes comes from the ACPICA method-name table, the same header that defines the sibling resource method names accepted by the walker:

```c
/* include/acpi/acnames.h:16 */
#define METHOD_NAME__AEI        "_AEI"
...
#define METHOD_NAME__CRS        "_CRS"
...
#define METHOD_NAME__DMA        "_DMA"
...
#define METHOD_NAME__PRS        "_PRS"
...
#define METHOD_NAME__SRS        "_SRS"
```

### ACPICA walk: acpi_walk_resources validates the name and iterates the records

[`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) is the callback-driven variant nearly every kernel consumer uses. It accepts exactly four object names, fetches the decoded block with the name-parameterized [`acpi_rs_get_method_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsutils.c#L637), and frees the block after the iteration:

```c
/* drivers/acpi/acpica/rsxface.c:593 */
acpi_status
acpi_walk_resources(acpi_handle device_handle,
		    char *name,
		    acpi_walk_resource_callback user_function, void *context)
{
	acpi_status status;
	struct acpi_buffer buffer;

	ACPI_FUNCTION_TRACE(acpi_walk_resources);

	/* Parameter validation */

	if (!device_handle || !user_function || !name ||
	    (!ACPI_COMPARE_NAMESEG(name, METHOD_NAME__CRS) &&
	     !ACPI_COMPARE_NAMESEG(name, METHOD_NAME__PRS) &&
	     !ACPI_COMPARE_NAMESEG(name, METHOD_NAME__AEI) &&
	     !ACPI_COMPARE_NAMESEG(name, METHOD_NAME__DMA))) {
		return_ACPI_STATUS(AE_BAD_PARAMETER);
	}

	/* Get the _CRS/_PRS/_AEI/_DMA resource list */

	buffer.length = ACPI_ALLOCATE_LOCAL_BUFFER;
	status = acpi_rs_get_method_data(device_handle, name, &buffer);
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}

	/* Walk the resource list and cleanup */

	status = acpi_walk_resource_buffer(&buffer, user_function, context);
	ACPI_FREE(buffer.pointer);
	return_ACPI_STATUS(status);
}

ACPI_EXPORT_SYMBOL(acpi_walk_resources)
```

[`acpi_walk_resource_buffer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L506) iterates the decoded array with [`ACPI_NEXT_RESOURCE()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L694), sanity checks the per-record header, treats [`AE_CTRL_TERMINATE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L186) from the callback as a clean stop, and ends at the [`ACPI_RESOURCE_TYPE_END_TAG`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L616) record:

```c
/* drivers/acpi/acpica/rsxface.c:505 */
acpi_status
acpi_walk_resource_buffer(struct acpi_buffer *buffer,
			  acpi_walk_resource_callback user_function,
			  void *context)
{
	acpi_status status = AE_OK;
	struct acpi_resource *resource;
	struct acpi_resource *resource_end;
	...
	/* Buffer contains the resource list and length */

	resource = ACPI_CAST_PTR(struct acpi_resource, buffer->pointer);
	resource_end =
	    ACPI_ADD_PTR(struct acpi_resource, buffer->pointer, buffer->length);

	/* Walk the resource list until the end_tag is found (or buffer end) */

	while (resource < resource_end) {

		/* Sanity check the resource type */

		if (resource->type > ACPI_RESOURCE_TYPE_MAX) {
			status = AE_AML_INVALID_RESOURCE_TYPE;
			break;
		}

		/* Sanity check the length. It must not be zero, or we loop forever */

		if (!resource->length) {
			return_ACPI_STATUS(AE_AML_BAD_RESOURCE_LENGTH);
		}

		/* Invoke the user function, abort on any error returned */

		status = user_function(resource, context);
		if (ACPI_FAILURE(status)) {
			if (status == AE_CTRL_TERMINATE) {

				/* This is an OK termination by the user function */

				status = AE_OK;
			}
			break;
		}

		/* end_tag indicates end-of-list */

		if (resource->type == ACPI_RESOURCE_TYPE_END_TAG) {
			break;
		}

		/* Get the next resource descriptor */

		resource = ACPI_NEXT_RESOURCE(resource);
	}

	return_ACPI_STATUS(status);
}
```

The stepping macro adds each record's `length` to its own address, which works because the conversion stage stores the aligned record size there:

```c
/* include/acpi/acrestyp.h:692 */
/* Macro for walking resource templates with multiple descriptors */

#define ACPI_NEXT_RESOURCE(res) \
	ACPI_ADD_PTR (struct acpi_resource, (res), (res)->length)
```

### The AML parse: from byte stream to decoded records

[`acpi_rs_create_resource_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rscreate.c#L103) is the bridge between the interpreter's Buffer object and the decoded array. It computes the needed output size in a first pass, allocates, and then walks the bytes a second time with the converter as the per-descriptor callback:

```c
/* drivers/acpi/acpica/rscreate.c:102 */
acpi_status
acpi_rs_create_resource_list(union acpi_operand_object *aml_buffer,
			     struct acpi_buffer *output_buffer)
{

	acpi_status status;
	u8 *aml_start;
	acpi_size list_size_needed = 0;
	u32 aml_buffer_length;
	void *resource;
	...
	aml_buffer_length = aml_buffer->buffer.length;
	aml_start = aml_buffer->buffer.pointer;

	/*
	 * Pass the aml_buffer into a module that can calculate
	 * the buffer size needed for the linked list
	 */
	status = acpi_rs_get_list_length(aml_start, aml_buffer_length,
					 &list_size_needed);
	...
	/* Validate/Allocate/Clear caller buffer */

	status = acpi_ut_initialize_buffer(output_buffer, list_size_needed);
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}

	/* Do the conversion */

	resource = output_buffer->pointer;
	status = acpi_ut_walk_aml_resources(NULL, aml_start, aml_buffer_length,
					    acpi_rs_convert_aml_to_resources,
					    &resource);
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}
	...
}
```

[`acpi_ut_walk_aml_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utresrc.c#L141) is the loop that understands the small/large tag encoding. It validates each tag byte, derives the descriptor length from the encoding family, invokes the callback, and stops at the End Tag, even synthesizing one when broken firmware omits it:

```c
/* drivers/acpi/acpica/utresrc.c:140 */
acpi_status
acpi_ut_walk_aml_resources(struct acpi_walk_state *walk_state,
			   u8 *aml,
			   acpi_size aml_length,
			   acpi_walk_aml_callback user_function, void **context)
{
	acpi_status status;
	u8 *end_aml;
	u8 resource_index;
	u32 length;
	u32 offset = 0;
	u8 end_tag[2] = { 0x79, 0x00 };
	...
	/* The absolute minimum resource template is one end_tag descriptor */

	if (aml_length < sizeof(struct aml_resource_end_tag)) {
		return_ACPI_STATUS(AE_AML_NO_RESOURCE_END_TAG);
	}

	/* Point to the end of the resource template buffer */

	end_aml = aml + aml_length;

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
			/* Normal exit */

			return_ACPI_STATUS(AE_OK);
		}

		aml += length;
		offset += length;
	}

	/* Did not find an end_tag descriptor */

	if (user_function) {

		/* Insert an end_tag anyway. acpi_rs_get_list_length always leaves room */

		(void)acpi_ut_validate_resource(walk_state, end_tag,
						&resource_index);
		status =
		    user_function(end_tag, 2, offset, resource_index, context);
		if (ACPI_FAILURE(status)) {
			return_ACPI_STATUS(status);
		}
	}

	return_ACPI_STATUS(AE_AML_NO_RESOURCE_END_TAG);
}
```

The callback is the top of the conversion chain. [`acpi_rs_convert_aml_to_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rslist.c#L30) selects a conversion table by the validated resource index (serial-bus descriptors get a second-level dispatch on their bus type) and advances the output cursor by the size of the record it just produced; the table-driven copy itself happens one level deeper and is shared by every descriptor kind, so the per-type knowledge lives entirely in the dispatch tables:

```c
/* drivers/acpi/acpica/rslist.c:29 */
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

[`acpi_gbl_get_resource_dispatch[]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsinfo.c#L57) maps each validated index to a [`struct acpi_rsconvert_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acresrc.h#L32) opcode script executed by [`acpi_rs_convert_aml_to_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsmisc.c#L35), and the per-descriptor scripts are a catalog beyond this page's scope; the relevant outcome is that after the walk the output buffer holds one [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678) per stream cell, End Tag record included.

### Linux layer: acpi_dev_get_resources and its walk context

The Linux conversion layer wraps the ACPICA walk in [`__acpi_dev_get_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L947), which checks that the device actually has the method, packs the caller's list head and preprocessing hook into a [`struct res_proc_context`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L883), and unwinds the partially built list on failure:

```c
/* drivers/acpi/resource.c:883 */
struct res_proc_context {
	struct list_head *list;
	int (*preproc)(struct acpi_resource *, void *);
	void *preproc_data;
	int count;
	int error;
};
```

```c
/* drivers/acpi/resource.c:947 */
static int __acpi_dev_get_resources(struct acpi_device *adev,
				    struct list_head *list,
				    int (*preproc)(struct acpi_resource *, void *),
				    void *preproc_data, char *method)
{
	struct res_proc_context c;
	acpi_status status;

	if (!adev || !adev->handle || !list_empty(list))
		return -EINVAL;

	if (!acpi_has_method(adev->handle, method))
		return 0;

	c.list = list;
	c.preproc = preproc;
	c.preproc_data = preproc_data;
	c.count = 0;
	c.error = 0;
	status = acpi_walk_resources(adev->handle, method,
				     acpi_dev_process_resource, &c);
	if (ACPI_FAILURE(status)) {
		acpi_dev_free_resource_list(list);
		return c.error ? c.error : -EIO;
	}

	return c.count;
}
```

[`acpi_dev_get_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1000) is the exported `_CRS` instantiation of that core, and its kernel-doc defines the preproc contract, under which a positive preproc return skips the generic conversion for that record and a negative one aborts the whole walk:

```c
/* drivers/acpi/resource.c:976 */
/**
 * acpi_dev_get_resources - Get current resources of a device.
 * @adev: ACPI device node to get the resources for.
 * @list: Head of the resultant list of resources (must be empty).
 * @preproc: The caller's preprocessing routine.
 * @preproc_data: Pointer passed to the caller's preprocessing routine.
 *
 * Evaluate the _CRS method for the given device node and process its output by
 * (1) executing the @preproc() routine provided by the caller, passing the
 * resource pointer and @preproc_data to it as arguments, for each ACPI resource
 * returned and (2) converting all of the returned ACPI resources into struct
 * resource objects if possible.  If the return value of @preproc() in step (1)
 * is different from 0, step (2) is not applied to the given ACPI resource and
 * if that value is negative, the whole processing is aborted and that value is
 * returned as the final error code.
 *
 * The resultant struct resource objects are put on the list pointed to by
 * @list, that must be empty initially, as members of struct resource_entry
 * objects.  Callers of this routine should use %acpi_dev_free_resource_list() to
 * free that list.
 *
 * The number of resources in the output list is returned on success, an error
 * code reflecting the error condition is returned otherwise.
 */
int acpi_dev_get_resources(struct acpi_device *adev, struct list_head *list,
			   int (*preproc)(struct acpi_resource *, void *),
			   void *preproc_data)
{
	return __acpi_dev_get_resources(adev, list, preproc, preproc_data,
					METHOD_NAME__CRS);
}
```

[`acpi_dev_process_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L908) is the per-record callback. After the preproc hook it tries the four single-output converters as one short-circuit expression, and interrupts get a loop of their own because one legacy IRQ descriptor can carry multiple GSIs, each becoming its own entry:

```c
/* drivers/acpi/resource.c:908 */
static acpi_status acpi_dev_process_resource(struct acpi_resource *ares,
					     void *context)
{
	struct res_proc_context *c = context;
	struct resource_win win;
	struct resource *res = &win.res;
	int i;

	if (c->preproc) {
		int ret;

		ret = c->preproc(ares, c->preproc_data);
		if (ret < 0) {
			c->error = ret;
			return AE_ABORT_METHOD;
		} else if (ret > 0) {
			return AE_OK;
		}
	}

	memset(&win, 0, sizeof(win));

	if (acpi_dev_resource_memory(ares, res)
	    || acpi_dev_resource_io(ares, res)
	    || acpi_dev_resource_address_space(ares, &win)
	    || acpi_dev_resource_ext_address_space(ares, &win))
		return acpi_dev_new_resource_entry(&win, c);

	for (i = 0; acpi_dev_resource_interrupt(ares, i, res); i++) {
		acpi_status status;

		status = acpi_dev_new_resource_entry(&win, c);
		if (ACPI_FAILURE(status))
			return status;
	}

	return AE_OK;
}
```

A record that no converter recognizes, an End Tag or a GpioInt for example, falls through both branches and is silently skipped, which is what keeps the generic walk usable on templates that mix plain resources with connector descriptors.

### List management: resource_entry creation and teardown

Each successful conversion lands in [`acpi_dev_new_resource_entry()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L891), which allocates a [`struct resource_entry`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/resource_ext.h#L23), copies the converted [`struct resource`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L22) and the window offset into it, queues it with [`resource_list_add_tail()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/resource_ext.h#L40), and bumps the running count that becomes the walk's return value:

```c
/* drivers/acpi/resource.c:891 */
static acpi_status acpi_dev_new_resource_entry(struct resource_win *win,
					       struct res_proc_context *c)
{
	struct resource_entry *rentry;

	rentry = resource_list_create_entry(NULL, 0);
	if (!rentry) {
		c->error = -ENOMEM;
		return AE_NO_MEMORY;
	}
	*rentry->res = win->res;
	rentry->offset = win->offset;
	resource_list_add_tail(rentry, c->list);
	c->count++;
	return AE_OK;
}
```

The entry type and its companion window type live in the shared resource-extension header, where the embedded `__res` storage explains the `NULL` first argument above, and [`resource_list_create_entry()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/resource.c#L1936) points `res` at that embedded storage when the caller supplies no external resource:

```c
/* include/linux/resource_ext.h:13 */
/* Represent resource window for bridge devices */
struct resource_win {
	struct resource res;		/* In master (CPU) address space */
	resource_size_t offset;		/* Translation offset for bridge */
};

/*
 * Common resource list management data structure and interfaces to support
 * ACPI, PNP and PCI host bridge etc.
 */
struct resource_entry {
	struct list_head	node;
	struct resource		*res;	/* In master (CPU) address space */
	resource_size_t		offset;	/* Translation offset for bridge */
	struct resource		__res;	/* Default storage for res */
};
```

```c
/* kernel/resource.c:1936 */
struct resource_entry *resource_list_create_entry(struct resource *res,
						  size_t extra_size)
{
	struct resource_entry *entry;

	entry = kzalloc(sizeof(*entry) + extra_size, GFP_KERNEL);
	if (entry) {
		INIT_LIST_HEAD(&entry->node);
		entry->res = res ? res : &entry->__res;
	}

	return entry;
}
```

Teardown is symmetric. [`acpi_dev_free_resource_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L877) forwards to [`resource_list_free()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/resource.c#L1951), which unlinks and frees every entry:

```c
/* drivers/acpi/resource.c:873 */
/**
 * acpi_dev_free_resource_list - Free resource from %acpi_dev_get_resources().
 * @list: The head of the resource list to free.
 */
void acpi_dev_free_resource_list(struct list_head *list)
{
	resource_list_free(list);
}
```

```c
/* kernel/resource.c:1951 */
void resource_list_free(struct list_head *head)
{
	struct resource_entry *entry, *tmp;

	list_for_each_entry_safe(entry, tmp, head, node)
		resource_list_destroy_entry(entry);
}
```

### Converter: memory descriptors become IORESOURCE_MEM resources

[`acpi_dev_resource_memory()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L107) handles the three fixed-format memory descriptor kinds. For the example's Memory32Fixed entry it takes the [`ACPI_RESOURCE_TYPE_FIXED_MEMORY32`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L619) case, so `data.fixed_memory32.address` 0xFED40000 becomes `res->start` and the 0x1000 length defines `res->end`:

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

The payload structs it reads are the direct decoded image of the section 6.4.3 memory descriptors:

```c
/* include/acpi/acrestyp.h:227 */
struct acpi_resource_memory32 {
	u8 write_protect;
	u32 minimum;
	u32 maximum;
	u32 alignment;
	u32 address_length;
};

struct acpi_resource_fixed_memory32 {
	u8 write_protect;
	u32 address;
	u32 address_length;
};
```

[`acpi_dev_get_memresource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L85) computes start and end, and [`acpi_dev_memresource_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L73) sets [`IORESOURCE_MEM`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L41), marks zero-length or inverted ranges [`IORESOURCE_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L69) plus [`IORESOURCE_UNSET`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L70) through [`acpi_dev_resource_len_valid()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L53), and translates the descriptor's `write_protect` byte into [`IORESOURCE_MEM_WRITEABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L103):

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

[`acpi_dev_resource_io()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L180) follows the same shape for the IO and FixedIO small items, reading [`struct acpi_resource_io`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L173) or [`struct acpi_resource_fixed_io`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L181) and emitting [`IORESOURCE_IO`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L40) with [`IORESOURCE_IO_16BIT_ADDR`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L116) recording the descriptor's decode width via [`acpi_dev_ioresource_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L141):

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

### Converter: interrupt descriptors register GSIs and become IORESOURCE_IRQ

[`acpi_dev_resource_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L828) covers the legacy IRQ small item ([`struct acpi_resource_irq`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L138)) and the extended Interrupt large item ([`struct acpi_resource_extended_irq`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L333)). The `index` parameter selects one entry from the descriptor's interrupt array, which is why [`acpi_dev_process_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L908) calls it in a loop until it reports the index out of range:

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

According to the comment "Per spec, only one interrupt per descriptor is allowed in _CRS, but some firmware violates this, so parse them all", the loop deliberately tolerates over-populated legacy IRQ descriptors. [`acpi_dev_get_irqresource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L761) then folds the four mode bytes into resource flags with [`acpi_dev_irq_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L342) and registers the GSI with the interrupt core, storing the resulting Linux IRQ number as `start`/`end`:

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

For the example template, the `Interrupt (ResourceConsumer, Level, ActiveHigh, Exclusive) { 42 }` entry arrives with `triggering ==` [`ACPI_LEVEL_SENSITIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L58), `polarity ==` [`ACPI_ACTIVE_HIGH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L63), and `interrupts[0] == 42`, so the entry becomes an [`IORESOURCE_IRQ`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L43) resource flagged [`IORESOURCE_IRQ_HIGHLEVEL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L80) whose `start` is the Linux IRQ that [`acpi_register_gsi()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/irq.c#L56) mapped for GSI 42.

### Converter: address-space descriptors decode through acpi_decode_space

The WordIO/DWordMemory/QWordMemory family shares one decoded layout, so [`acpi_dev_resource_address_space()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L290) first normalizes any of the three sizes into a [`struct acpi_resource_address64`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L322) with ACPICA's [`acpi_resource_to_address64()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L332) and then defers to the shared decoder, while [`acpi_dev_resource_ext_address_space()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L319) feeds the ExtendedSpace variant to the same decoder directly:

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

[`acpi_decode_space()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L207) is where the section 6.4.3.5 semantics turn into [`struct resource`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L22) fields. It applies the producer-side `translation_offset` to minimum and maximum, dispatches on the descriptor's `resource_type` byte ([`ACPI_MEMORY_RANGE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L102), [`ACPI_IO_RANGE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L103), or [`ACPI_BUS_NUMBER_RANGE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L104)), and marks bridge windows with [`IORESOURCE_WINDOW`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L57):

```c
/* drivers/acpi/resource.c:207 */
static bool acpi_decode_space(struct resource_win *win,
			      struct acpi_resource_address *addr,
			      struct acpi_address64_attribute *attr)
{
	u8 iodec = attr->granularity == 0xfff ? ACPI_DECODE_10 : ACPI_DECODE_16;
	bool wp = addr->info.mem.write_protect;
	u64 len = attr->address_length;
	u64 start, end, offset = 0;
	struct resource *res = &win->res;

	/*
	 * Filter out invalid descriptor according to ACPI Spec 5.0, section
	 * 6.4.3.5 Address Space Resource Descriptors.
	 */
	if ((addr->min_address_fixed != addr->max_address_fixed && len) ||
	    (addr->min_address_fixed && addr->max_address_fixed && !len))
		pr_debug("ACPI: Invalid address space min_addr_fix %d, max_addr_fix %d, len %llx\n",
			 addr->min_address_fixed, addr->max_address_fixed, len);

	/*
	 * For bridges that translate addresses across the bridge,
	 * translation_offset is the offset that must be added to the
	 * address on the secondary side to obtain the address on the
	 * primary side. Non-bridge devices must list 0 for all Address
	 * Translation offset bits.
	 */
	if (addr->producer_consumer == ACPI_PRODUCER)
		offset = attr->translation_offset;
	else if (attr->translation_offset)
		pr_debug("ACPI: translation_offset(%lld) is invalid for non-bridge device.\n",
			 attr->translation_offset);
	start = attr->minimum + offset;
	end = attr->maximum + offset;

	win->offset = offset;
	res->start = start;
	res->end = end;
	if (sizeof(resource_size_t) < sizeof(u64) &&
	    (offset != win->offset || start != res->start || end != res->end)) {
		pr_warn("acpi resource window ([%#llx-%#llx] ignored, not CPU addressable)\n",
			attr->minimum, attr->maximum);
		return false;
	}

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

	return !(res->flags & IORESOURCE_DISABLED);
}
```

The nonzero `offset` it stores in [`struct resource_win`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/resource_ext.h#L14) survives into [`struct resource_entry`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/resource_ext.h#L23) `.offset`, which is how PCI host bridge code later recovers the CPU-to-bus translation for windows a bridge `_CRS` produces.

### Filtered fetches: memory-only and _DMA walks reuse the same core

[`acpi_dev_get_memory_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1058) and [`acpi_dev_get_dma_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1040) demonstrate the two parameterization axes of the shared core, the preproc filter and the method name:

```c
/* drivers/acpi/resource.c:1040 */
int acpi_dev_get_dma_resources(struct acpi_device *adev, struct list_head *list)
{
	return __acpi_dev_get_resources(adev, list, is_memory, NULL,
					METHOD_NAME__DMA);
}
```

```c
/* drivers/acpi/resource.c:1058 */
int acpi_dev_get_memory_resources(struct acpi_device *adev, struct list_head *list)
{
	return acpi_dev_get_resources(adev, list, is_memory, NULL);
}
```

[`is_memory()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1009) leans on [`acpi_dev_filter_resource_type()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1073), the reusable class filter that buckets every record type into an `IORESOURCE_*` class and returns 0 only for records in the wanted classes. The preproc contract makes the composition work, since returning 1 for records outside [`IORESOURCE_MEM`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L41) tells [`acpi_dev_process_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L908) to skip the generic conversion for them:

```c
/* drivers/acpi/resource.c:1009 */
static int is_memory(struct acpi_resource *ares, void *not_used)
{
	struct resource_win win;
	struct resource *res = &win.res;

	memset(&win, 0, sizeof(win));

	if (acpi_dev_filter_resource_type(ares, IORESOURCE_MEM))
		return 1;

	return !(acpi_dev_resource_memory(ares, res)
	       || acpi_dev_resource_address_space(ares, &win)
	       || acpi_dev_resource_ext_address_space(ares, &win));
}
```

```c
/* drivers/acpi/resource.c:1073 */
int acpi_dev_filter_resource_type(struct acpi_resource *ares,
				  unsigned long types)
{
	unsigned long type = 0;

	switch (ares->type) {
	case ACPI_RESOURCE_TYPE_MEMORY24:
	case ACPI_RESOURCE_TYPE_MEMORY32:
	case ACPI_RESOURCE_TYPE_FIXED_MEMORY32:
		type = IORESOURCE_MEM;
		break;
	case ACPI_RESOURCE_TYPE_IO:
	case ACPI_RESOURCE_TYPE_FIXED_IO:
		type = IORESOURCE_IO;
		break;
	case ACPI_RESOURCE_TYPE_IRQ:
	case ACPI_RESOURCE_TYPE_EXTENDED_IRQ:
		type = IORESOURCE_IRQ;
		break;
	case ACPI_RESOURCE_TYPE_DMA:
	case ACPI_RESOURCE_TYPE_FIXED_DMA:
		type = IORESOURCE_DMA;
		break;
	case ACPI_RESOURCE_TYPE_GENERIC_REGISTER:
		type = IORESOURCE_REG;
		break;
	case ACPI_RESOURCE_TYPE_ADDRESS16:
	case ACPI_RESOURCE_TYPE_ADDRESS32:
	case ACPI_RESOURCE_TYPE_ADDRESS64:
	case ACPI_RESOURCE_TYPE_EXTENDED_ADDRESS64:
		if (ares->data.address.resource_type == ACPI_MEMORY_RANGE)
			type = IORESOURCE_MEM;
		else if (ares->data.address.resource_type == ACPI_IO_RANGE)
			type = IORESOURCE_IO;
		else if (ares->data.address.resource_type ==
			 ACPI_BUS_NUMBER_RANGE)
			type = IORESOURCE_BUS;
		break;
	default:
		break;
	}

	return (type & types) ? 0 : 1;
}
```

The address-type cases read `data.address`, the union's common-fields member, which works for all four address descriptor layouts because [`struct acpi_resource_address`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L309) reproduces exactly the leading fields the four share through the [`ACPI_RESOURCE_ADDRESS_COMMON`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L277) macro.

### Consumer: acpi_create_platform_device turns the list into platform resources

The namespace scan reaches `_CRS` through [`acpi_default_enumeration()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2245), which creates a platform device for every regular device node that no scan handler or serial-bus parent claimed:

```c
/* drivers/acpi/scan.c:2245 */
static void acpi_default_enumeration(struct acpi_device *device)
{
	/*
	 * Do not enumerate devices with enumeration_by_parent flag set as
	 * they will be enumerated by their respective parents.
	 */
	if (device->flags.enumeration_by_parent) {
		blocking_notifier_call_chain(&acpi_reconfig_chain,
					     ACPI_RECONFIG_DEVICE_ADD, device);
		return;
	}
	if (match_string(acpi_system_dev_ids, -1, acpi_device_hid(device)) >= 0) {
		struct acpi_scan_system_dev *sd;
		...
	} else if (device->pnp.type.backlight) {
		...
	} else {
		/* For a regular device object, create a platform device. */
		acpi_create_platform_device(device, NULL);
	}
	acpi_device_set_enumerated(device);
}
```

According to the comment "Do not enumerate devices with enumeration_by_parent flag set as they will be enumerated by their respective parents", nodes claimed by a serial-bus controller (the I2C case later on this page) skip platform-device creation and only fire the reconfiguration notifier.

[`acpi_create_platform_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_platform.c#L110) runs the full `_CRS` pipeline with a `NULL` preproc, so every convertible descriptor becomes a [`struct resource_entry`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/resource_ext.h#L23), then flattens the list into a plain [`struct resource`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L22) array for [`platform_device_register_full()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/platform.c#L846):

```c
/* drivers/acpi/acpi_platform.c:110 */
struct platform_device *acpi_create_platform_device(struct acpi_device *adev,
						    const struct property_entry *properties)
{
	struct acpi_device *parent = acpi_dev_parent(adev);
	struct platform_device *pdev = NULL;
	struct platform_device_info pdevinfo;
	const struct acpi_device_id *match;
	struct resource *resources = NULL;
	int count = 0;

	/* If the ACPI node already has a physical device attached, skip it. */
	if (adev->physical_node_count && !adev->pnp.type.backlight)
		return NULL;

	match = acpi_match_acpi_device(forbidden_id_list, adev);
	if (match) {
		if (match->driver_data & ACPI_ALLOW_WO_RESOURCES) {
			bool has_resources = false;

			acpi_walk_resources(adev->handle, METHOD_NAME__CRS,
					    acpi_platform_resource_count, &has_resources);
			if (has_resources)
				return ERR_PTR(-EINVAL);
		} else {
			return ERR_PTR(-EINVAL);
		}
	}

	if (adev->device_type == ACPI_BUS_TYPE_DEVICE) {
		LIST_HEAD(resource_list);

		count = acpi_dev_get_resources(adev, &resource_list, NULL, NULL);
		if (count < 0)
			return ERR_PTR(-ENODATA);

		if (count > 0) {
			struct resource_entry *rentry;

			resources = kzalloc_objs(*resources, count);
			if (!resources) {
				acpi_dev_free_resource_list(&resource_list);
				return ERR_PTR(-ENOMEM);
			}
			count = 0;
			list_for_each_entry(rentry, &resource_list, node)
				acpi_platform_fill_resource(adev, rentry->res,
							    &resources[count++]);

			acpi_dev_free_resource_list(&resource_list);
		}
	}

	memset(&pdevinfo, 0, sizeof(pdevinfo));
	/*
	 * If the ACPI node has a parent and that parent has a physical device
	 * attached to it, that physical device should be the parent of the
	 * platform device we are about to create.
	 */
	pdevinfo.parent = parent ? acpi_get_first_physical_node(parent) : NULL;
	pdevinfo.name = dev_name(&adev->dev);
	pdevinfo.id = PLATFORM_DEVID_NONE;
	pdevinfo.res = resources;
	pdevinfo.num_res = count;
	pdevinfo.fwnode = acpi_fwnode_handle(adev);
	pdevinfo.properties = properties;

	if (acpi_dma_supported(adev))
		pdevinfo.dma_mask = DMA_BIT_MASK(32);
	else
		pdevinfo.dma_mask = 0;

	pdev = platform_device_register_full(&pdevinfo);
	...
	kfree(resources);

	return pdev;
}
```

The function exercises two of the fetch APIs at once. The forbidden-ID branch uses a raw [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) with [`acpi_platform_resource_count()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_platform.c#L90), a callback that flags the presence of any descriptor and stops the walk with [`AE_CTRL_TERMINATE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L186) on the first record, while the main path uses the converted-list API:

```c
/* drivers/acpi/acpi_platform.c:90 */
static unsigned int acpi_platform_resource_count(struct acpi_resource *ares, void *data)
{
	bool *has_resources = data;

	*has_resources = true;

	return AE_CTRL_TERMINATE;
}
```

[`acpi_platform_fill_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_platform.c#L74) copies each converted resource and, when the ACPI parent has a PCI physical node, anchors the copy under the matching PCI BAR with [`pci_find_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci.c#L777), so a memory window a `_CRS` carves out of a parent device's BAR stays attached to the resource tree:

```c
/* drivers/acpi/acpi_platform.c:74 */
static void acpi_platform_fill_resource(struct acpi_device *adev,
	const struct resource *src, struct resource *dest)
{
	struct device *parent;

	*dest = *src;

	/*
	 * If the device has parent we need to take its resources into
	 * account as well because this device might consume part of those.
	 */
	parent = acpi_get_first_physical_node(acpi_dev_parent(adev));
	if (parent && dev_is_pci(parent))
		dest->parent = pci_find_resource(to_pci_dev(parent), dest);
}
```

For the example template, the resulting platform device carries two resources, the 0xFED40000 memory window and the IRQ resource for GSI 42; the GpioInt cell falls through the converter cascade in [`acpi_dev_process_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L908) and gpiolib-acpi consumes it separately when the bound driver requests its interrupt.

### Consumer: the EC driver pulls its two ports from the raw walk

The EC driver shows the minimal raw-walk consumer. [`ec_parse_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1460) is invoked per candidate `PNP0C09` node, once from [`acpi_ec_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1680) when the EC's platform device probes and once per match from the boot-time namespace sweep in [`acpi_ec_dsdt_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1809), and it launches the `_CRS` walk before reading the EC's other objects:

```c
/* drivers/acpi/ec.c:1459 */
static acpi_status
ec_parse_device(acpi_handle handle, u32 Level, void *context, void **retval)
{
	acpi_status status;
	unsigned long long tmp = 0;
	struct acpi_ec *ec = context;

	/* clear addr values, ec_parse_io_ports depend on it */
	ec->command_addr = ec->data_addr = 0;

	status = acpi_walk_resources(handle, METHOD_NAME__CRS,
				     ec_parse_io_ports, ec);
	if (ACPI_FAILURE(status))
		return status;
	if (ec->data_addr == 0 || ec->command_addr == 0)
		return AE_OK;

	/* Get GPE bit assignment (EC events). */
	/* TODO: Add support for _GPE returning a package */
	status = acpi_evaluate_integer(handle, "_GPE", NULL, &tmp);
	if (ACPI_SUCCESS(status))
		ec->gpe = tmp;
	/*
	 * Errors are non-fatal, allowing for ACPI Reduced Hardware
	 * platforms which use GpioInt instead of GPE.
	 */

	/* Use the global lock for all EC transactions? */
	tmp = 0;
	acpi_evaluate_integer(handle, "_GLK", NULL, &tmp);
	ec->global_lock = tmp;
	ec->handle = handle;
	return AE_CTRL_TERMINATE;
}
```

[`ec_parse_io_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/ec.c#L1776) consumes the records positionally. The EC's `_CRS` lists two IO small items, data port first and status/command port second per the EC device definition, and the callback assigns `data.io.minimum` of the first record to `data_addr`, the second to `command_addr`, and terminates on any third IO record:

```c
/* drivers/acpi/ec.c:1775 */
static acpi_status
ec_parse_io_ports(struct acpi_resource *resource, void *context)
{
	struct acpi_ec *ec = context;

	if (resource->type != ACPI_RESOURCE_TYPE_IO)
		return AE_OK;

	/*
	 * The first address region returned is the data port, and
	 * the second address region returned is the status/command
	 * port.
	 */
	if (ec->data_addr == 0)
		ec->data_addr = resource->data.io.minimum;
	else if (ec->command_addr == 0)
		ec->command_addr = resource->data.io.minimum;
	else
		return AE_CTRL_TERMINATE;

	return AE_OK;
}
```

The two addresses land in the EC state object and feed every subsequent EC register access:

```c
/* drivers/acpi/internal.h:194 */
struct acpi_ec {
	acpi_handle handle;
	int gpe;
	int irq;
	unsigned long command_addr;
	unsigned long data_addr;
	bool global_lock;
	unsigned long flags;
	...
};
```

This consumer reads the [`struct acpi_resource_io`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L173) payload directly and skips the [`struct resource`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L22) conversion entirely, the appropriate shape when the descriptor fields themselves are the configuration.

### Consumer: the I2C core reads I2cSerialBus connectors via the preproc hook

When [`i2c_register_adapter()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-base.c#L1519) brings up an adapter with an ACPI companion, [`i2c_acpi_register_devices()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-acpi.c#L320) sweeps the whole namespace and offers every device node to [`i2c_acpi_add_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-acpi.c#L295):

```c
/* drivers/i2c/i2c-core-acpi.c:320 */
void i2c_acpi_register_devices(struct i2c_adapter *adap)
{
	struct acpi_device *adev;
	acpi_status status;

	if (!has_acpi_companion(&adap->dev))
		return;

	status = acpi_walk_namespace(ACPI_TYPE_DEVICE, ACPI_ROOT_OBJECT,
				     I2C_ACPI_MAX_SCAN_DEPTH,
				     i2c_acpi_add_device, NULL,
				     adap, NULL);
	...
}
```

```c
/* drivers/i2c/i2c-core-acpi.c:295 */
static acpi_status i2c_acpi_add_device(acpi_handle handle, u32 level,
				       void *data, void **return_value)
{
	struct i2c_adapter *adapter = data;
	struct acpi_device *adev = acpi_fetch_acpi_dev(handle);
	struct i2c_board_info info;

	if (!adev || i2c_acpi_get_info(adev, &info, adapter, NULL))
		return AE_OK;

	i2c_acpi_register_device(adapter, adev, &info);

	return AE_OK;
}
```

[`i2c_acpi_get_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-acpi.c#L232) delegates the `_CRS` reading to [`i2c_acpi_do_lookup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-acpi.c#L145) and then verifies the connector points at the adapter being registered, because the namespace sweep visits every node and only the slaves whose I2cSerialBus names this adapter belong to it:

```c
/* drivers/i2c/i2c-core-acpi.c:145 */
static int i2c_acpi_do_lookup(struct acpi_device *adev,
			      struct i2c_acpi_lookup *lookup)
{
	struct i2c_board_info *info = lookup->info;
	struct list_head resource_list;
	int ret;

	if (acpi_bus_get_status(adev))
		return -EINVAL;

	if (!acpi_dev_ready_for_enumeration(adev))
		return -ENODEV;

	if (acpi_match_device_ids(adev, i2c_acpi_ignored_device_ids) == 0)
		return -ENODEV;

	memset(info, 0, sizeof(*info));
	lookup->device_handle = acpi_device_handle(adev);

	/* Look up for I2cSerialBus resource */
	INIT_LIST_HEAD(&resource_list);
	ret = acpi_dev_get_resources(adev, &resource_list,
				     i2c_acpi_fill_info, lookup);
	acpi_dev_free_resource_list(&resource_list);

	if (ret < 0 || !info->addr)
		return -EINVAL;

	return 0;
}
```

The walk context is the file-local lookup struct pairing the board info under construction with the handles resolved along the way:

```c
/* drivers/i2c/i2c-core-acpi.c:33 */
struct i2c_acpi_lookup {
	struct i2c_board_info *info;
	acpi_handle adapter_handle;
	acpi_handle device_handle;
	acpi_handle search_handle;
	int n;
	int index;
	u32 speed;
	u32 min_speed;
	u32 force_speed;
};
```

[`i2c_acpi_fill_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-acpi.c#L104) is the serial-bus branch of the page's pipeline. As a preproc it always returns 1, so [`acpi_dev_process_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L908) never attempts the generic converters on any record and the resource list stays empty by design; the function filters for the I2C connector, resolves the `ResourceSource` controller path into a handle, and copies the slave address, speed, and addressing mode out of the descriptor:

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

The type filter and the payload it exposes pair the [`ACPI_RESOURCE_TYPE_SERIAL_BUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L628) record type with the [`ACPI_RESOURCE_SERIAL_TYPE_I2C`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L412) subtype, the same two-level dispatch [`acpi_rs_convert_aml_to_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rslist.c#L30) used when decoding:

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

```c
/* include/acpi/acrestyp.h:422 */
struct acpi_resource_i2c_serialbus {
	ACPI_RESOURCE_SERIAL_COMMON u8 access_mode;
	u16 slave_address;
	u32 connection_speed;
};
```

With the descriptor captured, [`i2c_acpi_get_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-acpi.c#L232) confirms the adapter match through [`device_match_acpi_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L5342) and [`i2c_acpi_register_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/i2c/i2c-core-acpi.c#L277) instantiates the client:

```c
/* drivers/i2c/i2c-core-acpi.c:251 */
	if (adapter) {
		/* The adapter must match the one in I2cSerialBus() connector */
		if (!device_match_acpi_handle(&adapter->dev, lookup.adapter_handle))
			return -ENODEV;
	} else {
		...
	}

	info->fwnode = acpi_fwnode_handle(adev);
```

```c
/* drivers/i2c/i2c-core-acpi.c:277 */
static void i2c_acpi_register_device(struct i2c_adapter *adapter,
				     struct acpi_device *adev,
				     struct i2c_board_info *info)
{
	/*
	 * Skip registration on boards where the ACPI tables are
	 * known to contain bogus I2C devices.
	 */
	if (acpi_quirk_skip_i2c_client_enumeration(adev))
		return;

	adev->power.flags.ignore_parent = true;
	acpi_device_set_enumerated(adev);

	if (IS_ERR(i2c_new_client_device(adapter, info)))
		adev->power.flags.ignore_parent = false;
}
```

The three consumers close the loop on the example template. The platform path consumes the memory and interrupt cells through the full conversion pipeline, the EC path shows positional raw access to IO cells, and the I2C path shows the preproc hook capturing a connector cell the generic converters cannot express, all of them downstream of the same `_CRS` Buffer fetch and the same decoded [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678) records.
