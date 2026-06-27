# _SRS

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

`_SRS` is the Set Resource Settings control method that configurable ACPI devices expose alongside `_CRS` and `_PRS`. It takes exactly one argument, a Buffer holding the same byte-encoded descriptor stream (including the trailing End Tag) that a `_CRS` evaluation returns, and programs the device to decode the resources the stream describes. The kernel writes that Buffer through [`acpi_set_current_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L248), which validates the caller's [`struct acpi_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978) of decoded [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678) records and hands it to [`acpi_rs_set_srs_method_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsutils.c#L691), where [`acpi_rs_create_aml_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rscreate.c#L404) encodes the records back into raw AML bytes and [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42) runs the method named by [`METHOD_NAME__SRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L40). Two vendor-neutral subsystems exercise this write path end to end. The PNP ACPI protocol's [`pnpacpi_set_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L49) rebuilds a descriptor template from `_CRS` with [`pnpacpi_build_resource_template()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L622) and fills it from the device's [`struct resource`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L22) table with [`pnpacpi_encode_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L877), and the PCI interrupt link driver's [`acpi_pci_link_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L277) hand-builds a two-record buffer to route a `PNP0C0F` link onto one IRQ chosen from the `_PRS` alternatives, then re-reads `_CRS` through [`acpi_pci_link_get_current()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L228) to confirm the setting took effect.

```
    Arg0 Buffer for _SRS, two views of the same descriptor stream
    ──────────────────────────────────────────────────────────────

    struct acpi_resource records given to acpi_set_current_resources()
    ┌─────────────────────┬─────────────────────┬────────────────────┐
    │ .type = ACPI_       │ .type = ACPI_       │ .type = ACPI_      │
    │  RESOURCE_TYPE_IRQ  │  RESOURCE_TYPE_IO   │  RESOURCE_TYPE_    │
    │ .data.irq           │ .data.io            │  END_TAG           │
    │   .interrupts[0]    │   .minimum/.maximum │ (stops the encode  │
    │   .triggering       │   .io_decode        │  loop)             │
    │   .polarity         │   .address_length   │                    │
    └──────────┬──────────┴──────────┬──────────┴──────────┬─────────┘
               │                     │                     │
         filled by             filled by             appended by
         pnpacpi_encode_irq()  pnpacpi_encode_io()   pnpacpi_build_
         via decode_irq_flags()                      resource_template()
               │                     │                     │
               ▼                     ▼                     ▼
    AML bytes produced by acpi_rs_create_aml_resources()
    ┌─────────────────────┬─────────────────────┬────────────────────┐
    │ 23 mm mm ff         │ 47 dd mn mn mx mx   │ 79 00              │
    │ IRQ small item      │  al ln              │ End Tag            │
    │ (tag family 0x20,   │ IO small item       │ (tag 0x78 plus     │
    │  IRQ mask word,     │ (tag 0x40 | len 7)  │  length 1,         │
    │  flags byte)        │                     │  checksum byte)    │
    └─────────────────────┴─────────────────────┴────────────────────┘
    |<───────────── Arg0 Buffer passed to the _SRS method ──────────>|
```

## SUMMARY

The ACPI specification defines `_SRS` in section 6.2.16 as an optional control method that "sets a device's resource allocation" and takes one Buffer argument formatted exactly like the byte stream a `_CRS` evaluation returns, section 6.4 descriptors terminated by an End Tag. Section 6.2 prescribes the surrounding protocol. OSPM evaluates `_PRS` (section 6.2.12) to learn the resource alternatives a device accepts, picks one, encodes it as a descriptor stream, evaluates `_SRS` with that stream, and afterwards reads `_CRS` (section 6.2.2) again to observe the active setting; `_DIS` (section 6.2.3) is the inverse operation that disables the device's decode entirely. The kernel carries the four method names as the string macros [`METHOD_NAME__SRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L40), [`METHOD_NAME__PRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L30), [`METHOD_NAME__CRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L21), and [`METHOD_NAME__DIS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L23).

The ACPICA write entry point is [`acpi_set_current_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L248). It rejects an empty buffer, resolves the handle to a device node through [`acpi_rs_validate_parameters()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L57), and calls [`acpi_rs_set_srs_method_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsutils.c#L691), which converts the caller's linked list of [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678) records into an AML byte stream via [`acpi_rs_create_aml_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rscreate.c#L404) (a two-pass size-then-convert pipeline over [`acpi_rs_get_aml_length()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rscalc.c#L154) and [`acpi_rs_convert_resources_to_aml()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rslist.c#L128)), wraps the bytes in an interpreter-internal Buffer object, and executes the method through [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42) on a [`struct acpi_evaluate_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acstruct.h#L152) whose `flags` carry [`ACPI_IGNORE_RETURN_VALUE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acstruct.h#L178), since `_SRS` returns nothing.

Both in-tree consumers are vendor neutral. The PNP ACPI protocol registers [`pnpacpi_set_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L49) as the `set` operation of [`pnpacpi_protocol`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L184), reached from [`pnp_activate_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L383) through [`pnp_start_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L337); it sizes a record array off the current `_CRS` ([`pnpacpi_build_resource_template()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L622)), copies the assigned [`struct resource`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L22) values back into the per-type descriptor payloads ([`pnpacpi_encode_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L877) with encoders such as [`pnpacpi_encode_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L659) and [`pnpacpi_encode_io()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L764)), and writes the result with [`acpi_set_current_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L248). The matching `disable` operation, [`pnpacpi_disable_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L90), evaluates `_DIS` through [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163). The PCI interrupt link driver in [`drivers/acpi/pci_link.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c) walks the full spec protocol on one device class. [`acpi_pci_link_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L715) reads the `_PRS` alternatives into [`struct acpi_pci_link_irq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L55), [`acpi_pci_link_allocate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L528) picks the IRQ with the lowest penalty, and [`acpi_pci_link_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L277) writes a one-descriptor buffer, checks `_STA` via [`acpi_bus_get_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L95), and re-reads `_CRS` through [`acpi_pci_link_get_current()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L228).

## SPECIFICATIONS

- ACPI Specification, section 6.2: Device Configuration Objects
- ACPI Specification, section 6.2.2: _CRS (Current Resource Settings)
- ACPI Specification, section 6.2.3: _DIS (Disable)
- ACPI Specification, section 6.2.12: _PRS (Possible Resource Settings)
- ACPI Specification, section 6.2.16: _SRS (Set Resource Settings)
- ACPI Specification, section 6.4: Resource Data Types for ACPI

## LINUX KERNEL

### ACPICA write path

- [`'\<acpi_set_current_resources\>':'drivers/acpi/acpica/rsxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L248): public entry point, validates the buffer and dispatches to the `_SRS` evaluator
- [`'\<acpi_rs_validate_parameters\>':'drivers/acpi/acpica/rsxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L57): shared handle and buffer validation for all resource interfaces
- [`'\<acpi_rs_set_srs_method_data\>':'drivers/acpi/acpica/rsutils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsutils.c#L691): builds the AML Buffer argument and executes `_SRS`
- [`'\<acpi_rs_create_aml_resources\>':'drivers/acpi/acpica/rscreate.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rscreate.c#L404): converts decoded records to the raw byte stream `_SRS` consumes
- [`'\<acpi_rs_get_aml_length\>':'drivers/acpi/acpica/rscalc.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rscalc.c#L154): sizing pass over the record list, stops at the End Tag
- [`'\<acpi_rs_convert_resources_to_aml\>':'drivers/acpi/acpica/rslist.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rslist.c#L128): per-record conversion through the [`acpi_gbl_set_resource_dispatch`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsinfo.c#L26) tables
- [`'\<acpi_ns_evaluate\>':'drivers/acpi/acpica/nseval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42): interpreter entry that runs the method with the packed argument
- [`'\<struct acpi_evaluate_info\>':'drivers/acpi/acpica/acstruct.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acstruct.h#L152): evaluation parameter block carrying node, pathname, and argument array
- [`ACPI_IGNORE_RETURN_VALUE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acstruct.h#L178): flag telling the interpreter to discard whatever `_SRS` returns
- [`METHOD_NAME__SRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L40): the `"_SRS"` name string macro
- [`'\<struct acpi_buffer\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978): length/pointer pair carrying the record list into the write path

### Decoded records and flag constants

- [`'\<struct acpi_resource\>':'include/acpi/acrestyp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678): decoded record, type/length header plus payload union
- [`'\<struct acpi_resource_irq\>':'include/acpi/acrestyp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L138): IRQ descriptor payload the encoders fill
- [`'\<struct acpi_resource_extended_irq\>':'include/acpi/acrestyp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L333): Extended Interrupt payload used by the PCI link writer
- [`'\<struct acpi_resource_io\>':'include/acpi/acrestyp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L173): IO descriptor payload with decode, range, and length fields
- [`ACPI_RESOURCE_TYPE_END_TAG`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L616): record type that terminates both encode loops
- [`ACPI_LEVEL_SENSITIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L58) / [`ACPI_EDGE_SENSITIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L59): descriptor triggering values
- [`ACPI_ACTIVE_HIGH`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L63) / [`ACPI_ACTIVE_LOW`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L64): descriptor polarity values
- [`ACPI_EXCLUSIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L69) / [`ACPI_SHARED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L70): descriptor sharing values
- [`ACPI_DECODE_10`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L49) / [`ACPI_DECODE_16`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L50): IO descriptor address decode values
- [`'\<struct resource\>':'include/linux/ioport.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L22): generic resource object whose start/end/flags the encoders translate back
- [`IORESOURCE_IRQ_HIGHEDGE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L78) and the sibling [`IORESOURCE_IRQ_LOWLEVEL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L81) family: Linux IRQ mode bits mapped onto descriptor fields
- [`IORESOURCE_IO_16BIT_ADDR`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L116): flag selecting 16-bit IO decode in the encoder

### PNP ACPI consumer

- [`'\<pnpacpi_set_resources\>':'drivers/pnp/pnpacpi/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L49): protocol `set` operation, template build, encode, `_SRS` write, D0 transition
- [`'\<pnpacpi_disable_resources\>':'drivers/pnp/pnpacpi/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L90): protocol `disable` operation, D3cold transition plus `_DIS` evaluation
- [`'\<pnpacpi_protocol\>':'drivers/pnp/pnpacpi/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L184): the [`struct pnp_protocol`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pnp.h#L411) instance wiring get/set/disable to ACPI methods
- [`'\<struct pnp_protocol\>':'include/linux/pnp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pnp.h#L411): protocol operations consumed by the PNP manager layer
- [`'\<pnpacpi_build_resource_template\>':'drivers/pnp/pnpacpi/rsparser.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L622): allocates the record array shaped like the device's `_CRS`
- [`'\<pnpacpi_count_resources\>':'drivers/pnp/pnpacpi/rsparser.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L596): `_CRS` walk callback counting encodable descriptors
- [`'\<pnpacpi_type_resources\>':'drivers/pnp/pnpacpi/rsparser.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L606): `_CRS` walk callback stamping each record's type into the template
- [`'\<pnpacpi_supported_resource\>':'drivers/pnp/pnpacpi/rsparser.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L573): filter selecting the descriptor types the encoder understands
- [`'\<pnpacpi_encode_resources\>':'drivers/pnp/pnpacpi/rsparser.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L877): per-type dispatch copying [`struct resource`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L22) values into descriptor payloads
- [`'\<pnpacpi_encode_irq\>':'drivers/pnp/pnpacpi/rsparser.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L659): IRQ descriptor encoder, translates flags through [`decode_irq_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L18)
- [`'\<pnpacpi_encode_io\>':'drivers/pnp/pnpacpi/rsparser.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L764): IO descriptor encoder, maps decode width and port range
- [`'\<decode_irq_flags\>':'drivers/pnp/pnpacpi/rsparser.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L18): `IORESOURCE_IRQ_*` bits to triggering/polarity/shareable conversion
- [`'\<pnp_start_dev\>':'drivers/pnp/manager.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L337): invokes the protocol `set` operation after resources are assigned
- [`'\<pnp_activate_dev\>':'drivers/pnp/manager.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L383): allocates resources then starts the device
- [`'\<pnp_disable_dev\>':'drivers/pnp/manager.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L409): stops the device and releases its resource table
- [`'\<pnp_stop_dev\>':'drivers/pnp/manager.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L361): invokes the protocol `disable` operation
- [`'\<pnp_get_resource\>':'drivers/pnp/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/resource.c#L483): fetches the n-th resource of a given type from the device table
- [`'\<pnp_resource_enabled\>':'include/linux/pnp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pnp.h#L44): guard the encoders use before reading a resource

### PCI interrupt link consumer

- [`'\<acpi_pci_link_set\>':'drivers/acpi/pci_link.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L277): builds the IRQ descriptor buffer, evaluates `_SRS`, verifies via `_STA` and `_CRS`
- [`'\<acpi_pci_link_get_current\>':'drivers/acpi/pci_link.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L228): re-reads `_CRS` and stores the active IRQ
- [`'\<acpi_pci_link_check_current\>':'drivers/acpi/pci_link.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L173): `_CRS` walk callback extracting the first interrupt number
- [`'\<acpi_pci_link_get_possible\>':'drivers/acpi/pci_link.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L155): reads the `_PRS` alternatives into the link state
- [`'\<acpi_pci_link_check_possible\>':'drivers/acpi/pci_link.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L84): `_PRS` walk callback recording IRQ candidates, triggering, polarity, and resource type
- [`'\<acpi_pci_link_allocate\>':'drivers/acpi/pci_link.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L528): chooses the IRQ from the possible list and calls the setter
- [`'\<acpi_pci_link_add\>':'drivers/acpi/pci_link.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L715): scan-handler attach, runs `_PRS` and `_CRS` reads then disables the link via `_DIS`
- [`'\<acpi_pci_link_resume\>':'drivers/acpi/pci_link.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L767): replays `_SRS` after suspend for referenced, initialized links
- [`'\<struct acpi_pci_link\>':'drivers/acpi/pci_link.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L66): per-link state pairing the ACPI device with its IRQ bookkeeping
- [`'\<struct acpi_pci_link_irq\>':'drivers/acpi/pci_link.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L55): active IRQ, descriptor flavor, and the `_PRS` candidate array
- [`ACPI_PCI_LINK_MAX_POSSIBLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L34): bound on the recorded `_PRS` alternatives (16)

### Shared evaluation helpers

- [`'\<acpi_walk_resources\>':'drivers/acpi/acpica/rsxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594): callback walk over `_CRS` or `_PRS` used by both consumers' read steps
- [`'\<acpi_evaluate_object\>':'drivers/acpi/acpica/nsxfeval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163): generic evaluator both `_DIS` callers use directly
- [`'\<acpi_has_method\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L668): existence probe guarding the optional `_SRS` write
- [`'\<acpi_evaluation_failure_warn\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L653): standard warning the link driver emits when `_SRS` or `_CRS` fails
- [`'\<acpi_bus_get_status\>':'drivers/acpi/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L95): `_STA` read used to confirm the device is enabled after `_SRS`
- [`'\<acpi_device_set_power\>':'drivers/acpi/device_pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162): D-state transitions bracketing the PNP set/disable operations
- [`'\<acpi_device_power_manageable\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L857): guard for those transitions

## KERNEL DOCUMENTATION

- [`Documentation/PCI/acpi-info.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/PCI/acpi-info.rst): quotes the spec's `_PRS`/`_CRS`/`_SRS` configuration protocol and where PCI host bridges rely on it
- [`Documentation/arch/arm64/acpi_object_usage.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/arch/arm64/acpi_object_usage.rst): per-object usage table confirming `_SRS` as section 6.2.16 ("Use as needed; see also _PRS")
- [`Documentation/driver-api/acpi/linuxized-acpica.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/acpi/linuxized-acpica.rst): maintenance model of the imported ACPICA code that implements the `_SRS` write path

## OTHER SOURCES

- [ACPI Specification 6.5, chapter 6: Device Configuration](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html)
- [Commit a8d22396302b ("PNP / ACPI: Do not return errors if _DIS or _SRS are not present")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=a8d22396302b6e042c6e478332a83370b5840c0d)
- [Commit 2cb9155d116c ("ACPI: pci_link: Clear the dependencies after probe")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=2cb9155d116c4d9dd7610139a876d123b75924ef)

## METHODS

### _SRS (set resource settings, 1 Buffer argument)

`_SRS` is a spec-defined name with no function definition in the kernel; the kernel addresses it through the [`METHOD_NAME__SRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L40) string macro. Section 6.2.16 defines the single argument as a resource buffer "in the same format as the return value of _CRS", a stream of section 6.4 descriptors closed by an End Tag, and requires OSPM to fill every field of every descriptor even when programming only one of them. The only kernel writer is [`acpi_set_current_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L248); its input is the decoded [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678) record form rather than raw bytes, and [`acpi_rs_set_srs_method_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsutils.c#L691) performs the encode to AML before evaluation, so callers build records exactly as [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) hands them out of `_CRS`. Both consumers gate the write on availability, [`pnpacpi_set_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L49) with [`acpi_has_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L668) because `_SRS` is optional, and [`acpi_pci_link_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L277) by only running for devices matched on the `PNP0C0F` link ID, for which the spec requires `_SRS`.

### _DIS (disable, 0 arguments)

Section 6.2.3 defines `_DIS` as the inverse of `_SRS`; evaluating it disables the device's resource decode, after which `_STA` reports the enabled bit clear until a later `_SRS` re-enables the device. Neither kernel caller routes through a dedicated ACPICA wrapper; [`pnpacpi_disable_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L90) and [`acpi_pci_link_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L715) both pass the literal `"_DIS"` string to [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) with a NULL argument list and a NULL return buffer, and the [`METHOD_NAME__DIS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L23) macro stays unused outside its definition. The PNP caller treats [`AE_NOT_FOUND`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L75) as success because `_DIS` is optional, the behavior introduced by commit a8d22396302b.

### _PRS (possible resource settings, 0 arguments, read before the write)

Section 6.2.12 defines `_PRS` as returning a buffer of the resource combinations a device can accept, with alternatives expressed through StartDependentFn/EndDependentFn groupings. The kernel reads it with [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) passing [`METHOD_NAME__PRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L30); [`acpi_pci_link_get_possible()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L155) is the consumer documented here, recording up to [`ACPI_PCI_LINK_MAX_POSSIBLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L34) candidate IRQs plus the descriptor flavor that a later `_SRS` buffer must reproduce.

### _CRS (current resource settings, 0 arguments, read after the write)

Section 6.2.2 requires `_CRS` to report the active settings, so a configuration cycle closes by reading it again. [`acpi_pci_link_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L277) calls [`acpi_pci_link_get_current()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L228) immediately after the `_SRS` evaluation and compares the reported IRQ with the one it wrote, overriding the firmware's answer when the two disagree. [`pnpacpi_build_resource_template()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L622) uses `_CRS` in the opposite direction, as the mold that determines how many descriptors of which types the `_SRS` buffer must contain.

## DETAILS

### A _PRS/_SRS pair in ASL and the buffer the kernel writes

The following ASL models a legacy-configurable serial port in the shape the spec's chapter 6 examples use, one preferred and one acceptable dependent function group in `_PRS`, plus a `_SRS` method that accepts the chosen encoding back:

```asl
Device (UAR1)
{
    Name (_HID, EISAID ("PNP0501"))         // 16550A-compatible UART
    Name (_UID, 1)

    Name (_PRS, ResourceTemplate ()
    {
        StartDependentFn (0, 0) {           // preferred alternative
            IRQ (Edge, ActiveHigh, Exclusive) {4}
            IO (Decode16, 0x03F8, 0x03F8, 0x08, 0x08)
        }
        StartDependentFn (2, 1) {           // acceptable alternative
            IRQ (Edge, ActiveHigh, Exclusive) {3}
            IO (Decode16, 0x02F8, 0x02F8, 0x08, 0x08)
        }
        EndDependentFn ()
    })

    Method (_CRS, 0, Serialized) { ... }    // reports the active setting

    Method (_SRS, 1, Serialized)
    {
        // Arg0 is a Buffer shaped like a _CRS return:
        // one IRQ descriptor, one IO descriptor, one End Tag.
        CreateWordField (Arg0, 0x01, IRQM)  // IRQ mask word of the IRQ item
        // ... program the device from IRQM and the IO range bytes ...
    }
}
```

Evaluating `_SRS` hands the method one Buffer whose bytes follow the section 6.4 small-item encoding, and the `CreateWordField` line shows the AML side reading it positionally, byte 0 is the IRQ item's tag and bytes 1 and 2 are the little-endian IRQ mask word where bit n means IRQ n. The kernel produces those bytes through one shared encoder. Consumers fill an array of [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678) records (one per descriptor, End Tag record last) and the ACPICA write path encodes them, emitting the tag values the kernel mirrors in [`ACPI_RESOURCE_NAME_IRQ`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1108) (0x20 family, so 0x23 for the three-byte form whose last byte carries the triggering/polarity/sharing flags), [`ACPI_RESOURCE_NAME_IO`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1112) (0x40 plus length 7 gives the 0x47 tag), and [`ACPI_RESOURCE_NAME_END_TAG`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1119) (0x78 plus length 1 gives the 0x79 byte followed by the checksum byte). The lead figure shows the two views side by side, and the rest of this section walks the code that performs the conversion and the two subsystems that drive it.

### acpi_set_current_resources validates and dispatches

[`acpi_set_current_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L248) is the only exported `_SRS` writer. Where the `_CRS` reader accepts an empty output buffer (to report the needed size), the writer demands a populated input up front:

```c
/* drivers/acpi/acpica/rsxface.c:247 */
acpi_status
acpi_set_current_resources(acpi_handle device_handle,
			   struct acpi_buffer *in_buffer)
{
	acpi_status status;
	struct acpi_namespace_node *node;

	ACPI_FUNCTION_TRACE(acpi_set_current_resources);

	/* Validate the buffer, don't allow zero length */

	if ((!in_buffer) || (!in_buffer->pointer) || (!in_buffer->length)) {
		return_ACPI_STATUS(AE_BAD_PARAMETER);
	}

	/* Validate parameters then dispatch to internal routine */

	status = acpi_rs_validate_parameters(device_handle, in_buffer, &node);
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}

	status = acpi_rs_set_srs_method_data(node, in_buffer);
	return_ACPI_STATUS(status);
}

ACPI_EXPORT_SYMBOL(acpi_set_current_resources)
```

The input travels as a [`struct acpi_buffer`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978), the same two-field carrier the read APIs use, except here `pointer` and `length` describe the caller's record array instead of receiving one:

```c
/* include/acpi/actypes.h:978 */
struct acpi_buffer {
	acpi_size length;	/* Length in bytes of the buffer */
	void *pointer;		/* pointer to buffer */
};
```

[`acpi_rs_validate_parameters()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L57) is shared with the `_CRS` and `_PRS` fetchers. It resolves the handle, insists the node is a Device, and runs the buffer sanity check:

```c
/* drivers/acpi/acpica/rsxface.c:56 */
static acpi_status
acpi_rs_validate_parameters(acpi_handle device_handle,
			    struct acpi_buffer *buffer,
			    struct acpi_namespace_node **return_node)
{
	acpi_status status;
	struct acpi_namespace_node *node;

	ACPI_FUNCTION_TRACE(rs_validate_parameters);

	/*
	 * Must have a valid handle to an ACPI device
	 */
	if (!device_handle) {
		return_ACPI_STATUS(AE_BAD_PARAMETER);
	}

	node = acpi_ns_validate_handle(device_handle);
	if (!node) {
		return_ACPI_STATUS(AE_BAD_PARAMETER);
	}

	if (node->type != ACPI_TYPE_DEVICE) {
		return_ACPI_STATUS(AE_TYPE);
	}

	/*
	 * Validate the user buffer object
	 *
	 * if there is a non-zero buffer length we also need a valid pointer in
	 * the buffer. If it's a zero buffer length, we'll be returning the
	 * needed buffer size (later), so keep going.
	 */
	status = acpi_ut_validate_buffer(buffer);
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}

	*return_node = node;
	return_ACPI_STATUS(AE_OK);
}
```

### acpi_rs_set_srs_method_data packs the Buffer argument

[`acpi_rs_set_srs_method_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsutils.c#L691) performs the three steps that turn a record list into a method invocation, encode the records to AML bytes, wrap the bytes in an interpreter-internal Buffer object, and evaluate `_SRS` with that object as the single argument:

```c
/* drivers/acpi/acpica/rsutils.c:690 */
acpi_status
acpi_rs_set_srs_method_data(struct acpi_namespace_node *node,
			    struct acpi_buffer *in_buffer)
{
	struct acpi_evaluate_info *info;
	union acpi_operand_object *args[2];
	acpi_status status;
	struct acpi_buffer buffer;

	ACPI_FUNCTION_TRACE(rs_set_srs_method_data);

	/* Allocate and initialize the evaluation information block */

	info = ACPI_ALLOCATE_ZEROED(sizeof(struct acpi_evaluate_info));
	if (!info) {
		return_ACPI_STATUS(AE_NO_MEMORY);
	}

	info->prefix_node = node;
	info->relative_pathname = METHOD_NAME__SRS;
	info->parameters = args;
	info->flags = ACPI_IGNORE_RETURN_VALUE;

	/*
	 * The in_buffer parameter will point to a linked list of
	 * resource parameters. It needs to be formatted into a
	 * byte stream to be sent in as an input parameter to _SRS
	 *
	 * Convert the linked list into a byte stream
	 */
	buffer.length = ACPI_ALLOCATE_LOCAL_BUFFER;
	status = acpi_rs_create_aml_resources(in_buffer, &buffer);
	if (ACPI_FAILURE(status)) {
		goto cleanup;
	}

	/* Create and initialize the method parameter object */

	args[0] = acpi_ut_create_internal_object(ACPI_TYPE_BUFFER);
	if (!args[0]) {
		/*
		 * Must free the buffer allocated above (otherwise it is freed
		 * later)
		 */
		ACPI_FREE(buffer.pointer);
		status = AE_NO_MEMORY;
		goto cleanup;
	}

	args[0]->buffer.length = (u32) buffer.length;
	args[0]->buffer.pointer = buffer.pointer;
	args[0]->common.flags = AOPOBJ_DATA_VALID;
	args[1] = NULL;

	/* Execute the method, no return value is expected */

	status = acpi_ns_evaluate(info);

	/* Clean up and return the status from acpi_ns_evaluate */

	acpi_ut_remove_reference(args[0]);

cleanup:
	ACPI_FREE(info);
	return_ACPI_STATUS(status);
}
```

The argument passing differs from the external API surface. Where Linux-side helpers marshal arguments as an external [`struct acpi_object_list`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L956) of [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) descriptors that [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) converts internally, this function already lives inside ACPICA, so it builds the interpreter's native operand form directly. [`acpi_ut_create_internal_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acutils.h#L446) allocates a `union acpi_operand_object` typed [`ACPI_TYPE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L649), the encoded bytes are attached as its `buffer.pointer`/`buffer.length`, and [`AOPOBJ_DATA_VALID`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acobject.h#L61) marks the object initialized so the interpreter consumes it without a second setup pass. The `args` array is NULL-terminated at index 1, which is how [`acpi_ns_evaluate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nseval.c#L42) learns the method receives exactly one argument, matching the spec's `_SRS` signature.

The evaluation parameters travel in a [`struct acpi_evaluate_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acstruct.h#L152) block, whose first three fields are the caller-supplied node, relative pathname, and argument vector, and whose `flags` field carries [`ACPI_IGNORE_RETURN_VALUE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acstruct.h#L178) because section 6.2.16 defines no return value for `_SRS`:

```c
/* drivers/acpi/acpica/acstruct.h:148 */
/*
 * Structure used to pass object evaluation information and parameters.
 * Purpose is to reduce CPU stack use.
 */
struct acpi_evaluate_info {
	/* The first 3 elements are passed by the caller to acpi_ns_evaluate */

	struct acpi_namespace_node *prefix_node;	/* Input: starting node */
	const char *relative_pathname;	/* Input: path relative to prefix_node */
	union acpi_operand_object **parameters;	/* Input: argument list */

	struct acpi_namespace_node *node;	/* Resolved node (prefix_node:relative_pathname) */
	union acpi_operand_object *obj_desc;	/* Object attached to the resolved node */
	char *full_pathname;	/* Full pathname of the resolved node */

	const union acpi_predefined_info *predefined;	/* Used if Node is a predefined name */
	union acpi_operand_object *return_object;	/* Object returned from the evaluation */
	union acpi_operand_object *parent_package;	/* Used if return object is a Package */

	u32 return_flags;	/* Used for return value analysis */
	u32 return_btype;	/* Bitmapped type of the returned object */
	u16 param_count;	/* Count of the input argument list */
	u16 node_flags;		/* Same as Node->Flags */
	u8 pass_number;		/* Parser pass number */
	u8 return_object_type;	/* Object type of the returned object */
	u8 flags;		/* General flags */
};

/* Values for Flags above */

#define ACPI_IGNORE_RETURN_VALUE    1
```

The pathname comes from the ACPICA method-name table, the same header that names the three sibling methods of the configuration protocol:

```c
/* include/acpi/acnames.h:21 */
#define METHOD_NAME__CRS        "_CRS"
...
#define METHOD_NAME__DIS        "_DIS"
...
#define METHOD_NAME__PRS        "_PRS"
...
#define METHOD_NAME__SRS        "_SRS"
```

### acpi_rs_create_aml_resources reverses the _CRS decode

[`acpi_rs_create_aml_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rscreate.c#L404) is the mirror image of the `acpi_rs_create_resource_list()` decode that `_CRS` reads go through. According to its header comment, it "Converts a list of device resources to an AML bytestream to be used as input for the _SRS control method", and like the decoder it makes a sizing pass before converting:

```c
/* drivers/acpi/acpica/rscreate.c:403 */
acpi_status
acpi_rs_create_aml_resources(struct acpi_buffer *resource_list,
			     struct acpi_buffer *output_buffer)
{
	acpi_status status;
	acpi_size aml_size_needed = 0;

	ACPI_FUNCTION_TRACE(rs_create_aml_resources);

	/* Params already validated, no need to re-validate here */

	ACPI_DEBUG_PRINT((ACPI_DB_INFO, "ResourceList Buffer = %p\n",
			  resource_list->pointer));

	/* Get the buffer size needed for the AML byte stream */

	status =
	    acpi_rs_get_aml_length(resource_list->pointer,
				   resource_list->length, &aml_size_needed);

	ACPI_DEBUG_PRINT((ACPI_DB_INFO, "AmlSizeNeeded=%X, %s\n",
			  (u32)aml_size_needed, acpi_format_exception(status)));
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}

	/* Validate/Allocate/Clear caller buffer */

	status = acpi_ut_initialize_buffer(output_buffer, aml_size_needed);
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}

	/* Do the conversion */

	status = acpi_rs_convert_resources_to_aml(resource_list->pointer,
						  aml_size_needed,
						  output_buffer->pointer);
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}

	ACPI_DEBUG_PRINT((ACPI_DB_INFO, "OutputBuffer %p Length %X\n",
			  output_buffer->pointer, (u32) output_buffer->length));
	return_ACPI_STATUS(AE_OK);
}
```

[`acpi_rs_get_aml_length()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rscalc.c#L154) walks the record array accumulating each descriptor's encoded size, and its End Tag case shows where the walk terminates and why every `_SRS` input must carry the terminal record:

```c
/* drivers/acpi/acpica/rscalc.c:153 */
acpi_status
acpi_rs_get_aml_length(struct acpi_resource *resource,
		       acpi_size resource_list_size, acpi_size *size_needed)
{
	acpi_size aml_size_needed = 0;
	struct acpi_resource *resource_end;
	acpi_rs_length total_size;

	ACPI_FUNCTION_TRACE(rs_get_aml_length);

	/* Traverse entire list of internal resource descriptors */

	resource_end =
	    ACPI_ADD_PTR(struct acpi_resource, resource, resource_list_size);
	while (resource < resource_end) {

		/* Validate the descriptor type */

		if (resource->type > ACPI_RESOURCE_TYPE_MAX) {
			return_ACPI_STATUS(AE_AML_INVALID_RESOURCE_TYPE);
		}
		...
		case ACPI_RESOURCE_TYPE_END_TAG:
			/*
			 * End Tag:
			 * We are done -- return the accumulated total size.
			 */
			*size_needed = aml_size_needed + total_size;

			/* Normal exit */

			return_ACPI_STATUS(AE_OK);
		...
	}
	...
}
```

[`acpi_rs_convert_resources_to_aml()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rslist.c#L128) then performs the conversion proper. Each record's `type` indexes the [`acpi_gbl_set_resource_dispatch`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsinfo.c#L26) table of conversion descriptors (serial-bus records take a second-level dispatch on the bus subtype), every freshly encoded descriptor is re-validated, and the End Tag record exits the loop:

```c
/* drivers/acpi/acpica/rslist.c:127 */
acpi_status
acpi_rs_convert_resources_to_aml(struct acpi_resource *resource,
				 acpi_size aml_size_needed, u8 * output_buffer)
{
	u8 *aml = output_buffer;
	u8 *end_aml = output_buffer + aml_size_needed;
	struct acpi_rsconvert_info *conversion_table;
	acpi_status status;

	ACPI_FUNCTION_TRACE(rs_convert_resources_to_aml);

	/* Walk the resource descriptor list, convert each descriptor */

	while (aml < end_aml) {

		/* Validate the (internal) Resource Type */

		if (resource->type > ACPI_RESOURCE_TYPE_MAX) {
			ACPI_ERROR((AE_INFO,
				    "Invalid descriptor type (0x%X) in resource list",
				    resource->type));
			return_ACPI_STATUS(AE_BAD_DATA);
		}

		/* Sanity check the length. It must not be zero, or we loop forever */

		if (!resource->length) {
			ACPI_ERROR((AE_INFO,
				    "Invalid zero length descriptor in resource list\n"));
			return_ACPI_STATUS(AE_AML_BAD_RESOURCE_LENGTH);
		}

		/* Perform the conversion */

		if (resource->type == ACPI_RESOURCE_TYPE_SERIAL_BUS) {
			...
		} else {
			conversion_table =
			    acpi_gbl_set_resource_dispatch[resource->type];
		}
		...
		status = acpi_rs_convert_resource_to_aml(resource,
						         ACPI_CAST_PTR(union
								       aml_resource,
								       aml),
							 conversion_table);
		...
		/* Perform final sanity check on the new AML resource descriptor */

		status =
		    acpi_ut_validate_resource(NULL,
					      ACPI_CAST_PTR(union aml_resource,
							    aml), NULL);
		if (ACPI_FAILURE(status)) {
			return_ACPI_STATUS(status);
		}

		/* Check for end-of-list, normal exit */

		if (resource->type == ACPI_RESOURCE_TYPE_END_TAG) {

			/* An End Tag indicates the end of the input Resource Template */

			return_ACPI_STATUS(AE_OK);
		}
		...
	}
	...
}
```

The records being encoded all share the fixed header plus payload union layout, and the End Tag record is recognized by the [`ACPI_RESOURCE_TYPE_END_TAG`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L616) value of that header:

```c
/* include/acpi/acrestyp.h:676 */
/* Common resource header */

struct acpi_resource {
	u32 type;
	u32 length;
	union acpi_resource_data data;
};
```

### pnp_start_dev reaches pnpacpi_set_resources through the protocol

The PNP core keeps bus-specific resource control behind [`struct pnp_protocol`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pnp.h#L411), a small operations table every PNP device points at:

```c
/* include/linux/pnp.h:411 */
struct pnp_protocol {
	struct list_head protocol_list;
	char *name;

	/* resource control functions */
	int (*get) (struct pnp_dev *dev);
	int (*set) (struct pnp_dev *dev);
	int (*disable) (struct pnp_dev *dev);

	/* protocol specific suspend/resume */
	bool (*can_wakeup) (struct pnp_dev *dev);
	int (*suspend) (struct pnp_dev *dev, pm_message_t state);
	int (*resume) (struct pnp_dev *dev);

	/* used by pnp layer only (look but don't touch) */
	unsigned char number;	/* protocol number */
	struct device dev;	/* link to driver model */
	struct list_head cards;
	struct list_head devices;
};
```

The ACPI implementation wires `set` to the `_SRS` writer and `disable` to the `_DIS` caller in the [`pnpacpi_protocol`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L184) instance:

```c
/* drivers/pnp/pnpacpi/core.c:184 */
struct pnp_protocol pnpacpi_protocol = {
	.name	 = "Plug and Play ACPI",
	.get	 = pnpacpi_get_resources,
	.set	 = pnpacpi_set_resources,
	.disable = pnpacpi_disable_resources,
#ifdef CONFIG_ACPI_SLEEP
	.can_wakeup = pnpacpi_can_wakeup,
	.suspend = pnpacpi_suspend,
	.resume = pnpacpi_resume,
#endif
};
EXPORT_SYMBOL(pnpacpi_protocol);
```

[`pnp_device_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/driver.c#L82) is the lifecycle point that triggers a `_SRS` write in practice. When a PNP driver binds to an inactive device and tolerates resource changes, the probe activates it; a driver flagged `PNP_DRIVER_RES_DISABLE` gets the opposite treatment:

```c
/* drivers/pnp/driver.c:82 */
static int pnp_device_probe(struct device *dev)
{
	int error;
	struct pnp_driver *pnp_drv;
	struct pnp_dev *pnp_dev;
	const struct pnp_device_id *dev_id = NULL;
	pnp_dev = to_pnp_dev(dev);
	pnp_drv = to_pnp_driver(dev->driver);

	error = pnp_device_attach(pnp_dev);
	if (error < 0)
		return error;

	if (pnp_dev->active == 0) {
		if (!(pnp_drv->flags & PNP_DRIVER_RES_DO_NOT_CHANGE)) {
			error = pnp_activate_dev(pnp_dev);
			if (error < 0)
				return error;
		}
	} else if ((pnp_drv->flags & PNP_DRIVER_RES_DISABLE)
		   == PNP_DRIVER_RES_DISABLE) {
		error = pnp_disable_dev(pnp_dev);
		if (error < 0)
			return error;
	}
	...
}
```

[`pnp_activate_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L383) first lets [`pnp_auto_config_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L308) assign concrete values into the device's resource table (choosing among the option sets the PNP layer parsed from `_PRS`), then [`pnp_start_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L337) pushes the assignment to the firmware through the protocol's `set` operation:

```c
/* drivers/pnp/manager.c:383 */
int pnp_activate_dev(struct pnp_dev *dev)
{
	int error;

	if (dev->active)
		return 0;

	/* ensure resources are allocated */
	if (pnp_auto_config_dev(dev))
		return -EBUSY;

	error = pnp_start_dev(dev);
	if (error)
		return error;

	dev->active = 1;
	return 0;
}
```

```c
/* drivers/pnp/manager.c:337 */
int pnp_start_dev(struct pnp_dev *dev)
{
	if (!pnp_can_write(dev)) {
		pnp_dbg(&dev->dev, "activation not supported\n");
		return -EINVAL;
	}

	dbg_pnp_show_resources(dev, "pnp_start_dev");
	if (dev->protocol->set(dev) < 0) {
		dev_err(&dev->dev, "activation failed\n");
		return -EIO;
	}

	dev_info(&dev->dev, "activated\n");
	return 0;
}
```

For an ACPI-backed device `dev->protocol->set` is [`pnpacpi_set_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L49), so the chain from a PNP driver probe down to the `_SRS` evaluation is fully generic, the protocol indirection being the only ACPI-specific seam.

### pnpacpi_set_resources rebuilds the template and writes it

[`pnpacpi_set_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L49) shows the complete consumer pattern in one screen, the [`ACPI_COMPANION()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L58) lookup, the [`acpi_has_method()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L668) guard with [`METHOD_NAME__SRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L40) (the write is skipped entirely for the common static-`_CRS` device), the template build, the encode, the [`acpi_set_current_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L248) call, and the [`acpi_device_set_power()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L162) transition to D0 that completes the activation:

```c
/* drivers/pnp/pnpacpi/core.c:49 */
static int pnpacpi_set_resources(struct pnp_dev *dev)
{
	struct acpi_device *acpi_dev;
	acpi_handle handle;
	int ret = 0;

	pnp_dbg(&dev->dev, "set resources\n");

	acpi_dev = ACPI_COMPANION(&dev->dev);
	if (!acpi_dev) {
		dev_dbg(&dev->dev, "ACPI device not found in %s!\n", __func__);
		return -ENODEV;
	}

	if (WARN_ON_ONCE(acpi_dev != dev->data))
		dev->data = acpi_dev;

	handle = acpi_dev->handle;
	if (acpi_has_method(handle, METHOD_NAME__SRS)) {
		struct acpi_buffer buffer;

		ret = pnpacpi_build_resource_template(dev, &buffer);
		if (ret)
			return ret;

		ret = pnpacpi_encode_resources(dev, &buffer);
		if (!ret) {
			acpi_status status;

			status = acpi_set_current_resources(handle, &buffer);
			if (ACPI_FAILURE(status))
				ret = -EIO;
		}
		kfree(buffer.pointer);
	}
	if (!ret && acpi_device_power_manageable(acpi_dev))
		ret = acpi_device_set_power(acpi_dev, ACPI_STATE_D0);

	return ret;
}
```

The [`acpi_device_power_manageable()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L857) check keeps the D0 transition conditional on the device actually exposing power resources or `_PSx` methods, and the same pairing of resource control with power control reappears inverted in the disable path below.

### pnpacpi_build_resource_template shapes the buffer from _CRS

The encoder needs a record array whose descriptor sequence matches what the device's `_SRS` expects, and per section 6.2.16 that sequence is the `_CRS` layout. [`pnpacpi_build_resource_template()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L622) therefore walks `_CRS` twice with [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594), once to count the encodable descriptors and once to stamp each record's type, then plants the End Tag record by hand:

```c
/* drivers/pnp/pnpacpi/rsparser.c:622 */
int pnpacpi_build_resource_template(struct pnp_dev *dev,
				    struct acpi_buffer *buffer)
{
	struct acpi_device *acpi_dev = dev->data;
	acpi_handle handle = acpi_dev->handle;
	struct acpi_resource *resource;
	int res_cnt = 0;
	acpi_status status;

	status = acpi_walk_resources(handle, METHOD_NAME__CRS,
				     pnpacpi_count_resources, &res_cnt);
	if (ACPI_FAILURE(status)) {
		dev_err(&dev->dev, "can't evaluate _CRS: %d\n", status);
		return -EINVAL;
	}
	if (!res_cnt)
		return -EINVAL;
	buffer->length = sizeof(struct acpi_resource) * (res_cnt + 1) + 1;
	buffer->pointer = kzalloc(buffer->length - 1, GFP_KERNEL);
	if (!buffer->pointer)
		return -ENOMEM;

	resource = (struct acpi_resource *)buffer->pointer;
	status = acpi_walk_resources(handle, METHOD_NAME__CRS,
				     pnpacpi_type_resources, &resource);
	if (ACPI_FAILURE(status)) {
		kfree(buffer->pointer);
		dev_err(&dev->dev, "can't evaluate _CRS: %d\n", status);
		return -EINVAL;
	}
	/* resource will pointer the end resource now */
	resource->type = ACPI_RESOURCE_TYPE_END_TAG;
	resource->length = sizeof(struct acpi_resource);

	return 0;
}
```

The two callbacks share the [`pnpacpi_supported_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L573) filter, so descriptors the encoder has no case for (GPIO and serial-bus connectors among them) are dropped from the template on both passes and the count stays consistent:

```c
/* drivers/pnp/pnpacpi/rsparser.c:573 */
static int pnpacpi_supported_resource(struct acpi_resource *res)
{
	switch (res->type) {
	case ACPI_RESOURCE_TYPE_IRQ:
	case ACPI_RESOURCE_TYPE_DMA:
	case ACPI_RESOURCE_TYPE_IO:
	case ACPI_RESOURCE_TYPE_FIXED_IO:
	case ACPI_RESOURCE_TYPE_MEMORY24:
	case ACPI_RESOURCE_TYPE_MEMORY32:
	case ACPI_RESOURCE_TYPE_FIXED_MEMORY32:
	case ACPI_RESOURCE_TYPE_ADDRESS16:
	case ACPI_RESOURCE_TYPE_ADDRESS32:
	case ACPI_RESOURCE_TYPE_ADDRESS64:
	case ACPI_RESOURCE_TYPE_EXTENDED_ADDRESS64:
	case ACPI_RESOURCE_TYPE_EXTENDED_IRQ:
		return 1;
	}
	return 0;
}
```

```c
/* drivers/pnp/pnpacpi/rsparser.c:596 */
static acpi_status pnpacpi_count_resources(struct acpi_resource *res,
					   void *data)
{
	int *res_cnt = data;

	if (pnpacpi_supported_resource(res))
		(*res_cnt)++;
	return AE_OK;
}

static acpi_status pnpacpi_type_resources(struct acpi_resource *res, void *data)
{
	struct acpi_resource **resource = data;

	if (pnpacpi_supported_resource(res)) {
		(*resource)->type = res->type;
		(*resource)->length = sizeof(struct acpi_resource);
		if (res->type == ACPI_RESOURCE_TYPE_IRQ)
			(*resource)->data.irq.descriptor_length =
					res->data.irq.descriptor_length;
		(*resource)++;
	}

	return AE_OK;
}
```

[`pnpacpi_type_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L606) copies one payload field along with the type, the IRQ record's `descriptor_length`. The legacy IRQ small item exists in a two-byte form (mask only, defaulting to edge/active-high/exclusive) and a three-byte form (mask plus flags byte), and preserving the length the firmware used in `_CRS` makes the encode stage re-emit the same small-item size, so a `_SRS` method that reads its argument with fixed `CreateWordField` offsets, as in the ASL example above, sees the bytes where it expects them.

### pnpacpi_encode_resources maps struct resource back onto descriptors

[`pnpacpi_encode_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L877) fills the typed template from the device's assigned resources. It keeps independent counters per resource class and pulls the n-th [`struct resource`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L22) of the matching type with [`pnp_get_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/resource.c#L483), so the i-th IRQ descriptor in the template receives the i-th IRQ resource of the device, mirroring the positional convention the `_CRS` parse used when it created those resources:

```c
/* drivers/pnp/pnpacpi/rsparser.c:877 */
int pnpacpi_encode_resources(struct pnp_dev *dev, struct acpi_buffer *buffer)
{
	int i = 0;
	/* pnpacpi_build_resource_template allocates extra mem */
	int res_cnt = (buffer->length - 1) / sizeof(struct acpi_resource) - 1;
	struct acpi_resource *resource = buffer->pointer;
	unsigned int port = 0, irq = 0, dma = 0, mem = 0;

	pnp_dbg(&dev->dev, "encode %d resources\n", res_cnt);
	while (i < res_cnt) {
		switch (resource->type) {
		case ACPI_RESOURCE_TYPE_IRQ:
			pnpacpi_encode_irq(dev, resource,
			       pnp_get_resource(dev, IORESOURCE_IRQ, irq));
			irq++;
			break;

		case ACPI_RESOURCE_TYPE_DMA:
			pnpacpi_encode_dma(dev, resource,
				pnp_get_resource(dev, IORESOURCE_DMA, dma));
			dma++;
			break;
		case ACPI_RESOURCE_TYPE_IO:
			pnpacpi_encode_io(dev, resource,
				pnp_get_resource(dev, IORESOURCE_IO, port));
			port++;
			break;
		case ACPI_RESOURCE_TYPE_FIXED_IO:
			pnpacpi_encode_fixed_io(dev, resource,
				pnp_get_resource(dev, IORESOURCE_IO, port));
			port++;
			break;
		case ACPI_RESOURCE_TYPE_MEMORY24:
			pnpacpi_encode_mem24(dev, resource,
				pnp_get_resource(dev, IORESOURCE_MEM, mem));
			mem++;
			break;
		case ACPI_RESOURCE_TYPE_MEMORY32:
			pnpacpi_encode_mem32(dev, resource,
				pnp_get_resource(dev, IORESOURCE_MEM, mem));
			mem++;
			break;
		case ACPI_RESOURCE_TYPE_FIXED_MEMORY32:
			pnpacpi_encode_fixed_mem32(dev, resource,
				pnp_get_resource(dev, IORESOURCE_MEM, mem));
			mem++;
			break;
		case ACPI_RESOURCE_TYPE_EXTENDED_IRQ:
			pnpacpi_encode_ext_irq(dev, resource,
				pnp_get_resource(dev, IORESOURCE_IRQ, irq));
			irq++;
			break;
		case ACPI_RESOURCE_TYPE_START_DEPENDENT:
		case ACPI_RESOURCE_TYPE_END_DEPENDENT:
		case ACPI_RESOURCE_TYPE_VENDOR:
		case ACPI_RESOURCE_TYPE_END_TAG:
		case ACPI_RESOURCE_TYPE_ADDRESS16:
		case ACPI_RESOURCE_TYPE_ADDRESS32:
		case ACPI_RESOURCE_TYPE_ADDRESS64:
		case ACPI_RESOURCE_TYPE_EXTENDED_ADDRESS64:
		case ACPI_RESOURCE_TYPE_GENERIC_REGISTER:
		default:	/* other type */
			dev_warn(&dev->dev,
				 "can't encode unknown resource type %d\n",
				 resource->type);
			return -EINVAL;
		}
		resource++;
		i++;
	}
	return 0;
}
```

The `res_cnt` arithmetic recovers the descriptor count from the buffer length that [`pnpacpi_build_resource_template()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L622) computed (one extra record slot for the End Tag plus one extra byte), and the loop stops short of the End Tag record so the terminal cell written by the template builder survives untouched into the AML encode.

### pnpacpi_encode_irq and pnpacpi_encode_io translate the flags back

[`pnpacpi_encode_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L659) is the representative interrupt encoder. It writes the [`struct acpi_resource_irq`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L138) payload, either an empty descriptor (`interrupt_count = 0`) when the resource slot is disabled or absent, or a one-interrupt descriptor whose mode fields come from the Linux flags:

```c
/* drivers/pnp/pnpacpi/rsparser.c:659 */
static void pnpacpi_encode_irq(struct pnp_dev *dev,
			       struct acpi_resource *resource,
			       struct resource *p)
{
	struct acpi_resource_irq *irq = &resource->data.irq;
	u8 triggering, polarity, shareable;

	if (!pnp_resource_enabled(p)) {
		irq->interrupt_count = 0;
		pnp_dbg(&dev->dev, "  encode irq (%s)\n",
			p ? "disabled" : "missing");
		return;
	}

	decode_irq_flags(dev, p->flags, &triggering, &polarity, &shareable);
	irq->triggering = triggering;
	irq->polarity = polarity;
	irq->shareable = shareable;
	irq->interrupt_count = 1;
	irq->interrupts[0] = p->start;

	pnp_dbg(&dev->dev, "  encode irq %d %s %s %s (%d-byte descriptor)\n",
		(int) p->start,
		triggering == ACPI_LEVEL_SENSITIVE ? "level" : "edge",
		polarity == ACPI_ACTIVE_LOW ? "low" : "high",
		irq->shareable == ACPI_SHARED ? "shared" : "exclusive",
		irq->descriptor_length);
}
```

The payload it fills is the decoded image of the legacy IRQ small item, including the `descriptor_length` the template stage preserved:

```c
/* include/acpi/acrestyp.h:138 */
struct acpi_resource_irq {
	u8 descriptor_length;
	u8 triggering;
	u8 polarity;
	u8 shareable;
	u8 wake_capable;
	u8 interrupt_count;
	union {
		u8 interrupt;
		 ACPI_FLEX_ARRAY(u8, interrupts);
	};
};
```

[`decode_irq_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L18) inverts the mapping that the `_CRS` parse applied in the other direction. The four [`IORESOURCE_IRQ_HIGHEDGE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L78) through [`IORESOURCE_IRQ_LOWLEVEL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L81) mode bits collapse into the descriptor's two fields, [`IORESOURCE_IRQ_SHAREABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L82) selects [`ACPI_SHARED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L70) over [`ACPI_EXCLUSIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L69), and an unrecognized combination falls back to edge/active-high with an error message:

```c
/* drivers/pnp/pnpacpi/rsparser.c:18 */
static void decode_irq_flags(struct pnp_dev *dev, int flags, u8 *triggering,
			     u8 *polarity, u8 *shareable)
{
	switch (flags & (IORESOURCE_IRQ_LOWLEVEL | IORESOURCE_IRQ_HIGHLEVEL |
			 IORESOURCE_IRQ_LOWEDGE  | IORESOURCE_IRQ_HIGHEDGE)) {
	case IORESOURCE_IRQ_LOWLEVEL:
		*triggering = ACPI_LEVEL_SENSITIVE;
		*polarity = ACPI_ACTIVE_LOW;
		break;
	case IORESOURCE_IRQ_HIGHLEVEL:
		*triggering = ACPI_LEVEL_SENSITIVE;
		*polarity = ACPI_ACTIVE_HIGH;
		break;
	case IORESOURCE_IRQ_LOWEDGE:
		*triggering = ACPI_EDGE_SENSITIVE;
		*polarity = ACPI_ACTIVE_LOW;
		break;
	case IORESOURCE_IRQ_HIGHEDGE:
		*triggering = ACPI_EDGE_SENSITIVE;
		*polarity = ACPI_ACTIVE_HIGH;
		break;
	default:
		dev_err(&dev->dev, "can't encode invalid IRQ mode %#x\n",
			flags);
		*triggering = ACPI_EDGE_SENSITIVE;
		*polarity = ACPI_ACTIVE_HIGH;
		break;
	}

	if (flags & IORESOURCE_IRQ_SHAREABLE)
		*shareable = ACPI_SHARED;
	else
		*shareable = ACPI_EXCLUSIVE;
}
```

The constants on the descriptor side live in the resource-type header and encode the field values section 6.4.2.1 defines for the IRQ item's flags byte:

```c
/* include/acpi/acrestyp.h:56 */
/* Triggering */

#define ACPI_LEVEL_SENSITIVE            (u8) 0x00
#define ACPI_EDGE_SENSITIVE             (u8) 0x01

/* Polarity */

#define ACPI_ACTIVE_HIGH                (u8) 0x00
#define ACPI_ACTIVE_LOW                 (u8) 0x01
...
#define ACPI_EXCLUSIVE                  (u8) 0x00
#define ACPI_SHARED                     (u8) 0x01
```

[`pnpacpi_encode_io()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L764) is the representative port encoder. The [`pnp_resource_enabled()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pnp.h#L44) guard repeats, the [`IORESOURCE_IO_16BIT_ADDR`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L116) flag picks [`ACPI_DECODE_16`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L50) over [`ACPI_DECODE_10`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L49) (the comment notes the flag arrived through `pnp_assign_port` copying the option flags into the resource), and start/end/size of the [`struct resource`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L22) land in the descriptor's minimum/maximum/length fields with the alignment fixed at zero since the value is already assigned:

```c
/* drivers/pnp/pnpacpi/rsparser.c:764 */
static void pnpacpi_encode_io(struct pnp_dev *dev,
			      struct acpi_resource *resource,
			      struct resource *p)
{
	struct acpi_resource_io *io = &resource->data.io;

	if (pnp_resource_enabled(p)) {
		/* Note: pnp_assign_port copies pnp_port->flags into p->flags */
		io->io_decode = (p->flags & IORESOURCE_IO_16BIT_ADDR) ?
		    ACPI_DECODE_16 : ACPI_DECODE_10;
		io->minimum = p->start;
		io->maximum = p->end;
		io->alignment = 0;	/* Correct? */
		io->address_length = resource_size(p);
	} else {
		io->minimum = 0;
		io->address_length = 0;
	}

	pnp_dbg(&dev->dev, "  encode io %#x-%#x decode %#x\n", io->minimum,
		io->minimum + io->address_length - 1, io->io_decode);
}
```

```c
/* include/acpi/acrestyp.h:173 */
struct acpi_resource_io {
	u8 io_decode;
	u8 alignment;
	u8 address_length;
	u16 minimum;
	u16 maximum;
};
```

```c
/* include/linux/pnp.h:44 */
static inline int pnp_resource_enabled(struct resource *res)
{
	if (res && !(res->flags & IORESOURCE_DISABLED))
		return 1;
	return 0;
}
```

The generic resource object both encoders read from carries the assigned range in `start`/`end` and the mode bits in `flags`:

```c
/* include/linux/ioport.h:22 */
struct resource {
	resource_size_t start;
	resource_size_t end;
	const char *name;
	unsigned long flags;
	unsigned long desc;
	struct resource *parent, *sibling, *child;
};
```

### The disable path evaluates _DIS

[`pnp_disable_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L409) is the manager-level inverse of activation. It stops the device, clears the active flag, and frees the resource assignments so other devices can claim them:

```c
/* drivers/pnp/manager.c:402 */
/**
 * pnp_disable_dev - disables device
 * @dev: pointer to the desired device
 *
 * inform the correct pnp protocol so that resources can be used by other devices
 */

int pnp_disable_dev(struct pnp_dev *dev)
{
	int error;

	if (!dev->active)
		return 0;

	error = pnp_stop_dev(dev);
	if (error)
		return error;

	dev->active = 0;

	/* release the resources so that other devices can use them */
	mutex_lock(&pnp_res_mutex);
	pnp_clean_resource_table(dev);
	mutex_unlock(&pnp_res_mutex);

	return 0;
}
```

[`pnp_stop_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L361) dispatches through the protocol's `disable` operation the same way [`pnp_start_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L337) dispatched through `set`:

```c
/* drivers/pnp/manager.c:361 */
int pnp_stop_dev(struct pnp_dev *dev)
{
	if (!pnp_can_disable(dev)) {
		pnp_dbg(&dev->dev, "disabling not supported\n");
		return -EINVAL;
	}
	if (dev->protocol->disable(dev) < 0) {
		dev_err(&dev->dev, "disable failed\n");
		return -EIO;
	}

	dev_info(&dev->dev, "disabled\n");
	return 0;
}
```

[`pnpacpi_disable_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L90) implements the operation by sending the device to D3cold first and then evaluating `_DIS` through plain [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163), with no argument list and no return buffer since section 6.2.3 defines `_DIS` as taking and returning nothing. [`AE_NOT_FOUND`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L75) passes through as success because the method is optional:

```c
/* drivers/pnp/pnpacpi/core.c:90 */
static int pnpacpi_disable_resources(struct pnp_dev *dev)
{
	struct acpi_device *acpi_dev;
	acpi_status status;

	dev_dbg(&dev->dev, "disable resources\n");

	acpi_dev = ACPI_COMPANION(&dev->dev);
	if (!acpi_dev) {
		dev_dbg(&dev->dev, "ACPI device not found in %s!\n", __func__);
		return 0;
	}

	/* acpi_unregister_gsi(pnp_irq(dev, 0)); */
	if (acpi_device_power_manageable(acpi_dev))
		acpi_device_set_power(acpi_dev, ACPI_STATE_D3_COLD);

	/* continue even if acpi_device_set_power() fails */
	status = acpi_evaluate_object(acpi_dev->handle, "_DIS", NULL, NULL);
	if (ACPI_FAILURE(status) && status != AE_NOT_FOUND)
		return -ENODEV;

	return 0;
}
```

After a successful `_DIS` the spec requires the device's `_STA` to report the enabled bit clear, and the next [`pnp_activate_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L383) cycle re-enables the device by writing `_SRS` again, which is exactly the disable/re-enable pairing section 6.2.3 describes.

### PCI interrupt links walk the whole protocol on one device class

The interrupt link device (`PNP0C0F`) exercises the configuration protocol in full because its single resource, the IRQ it routes legacy PCI interrupts onto, is chosen at run time. The driver claims those nodes through a [`struct acpi_scan_handler`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L131) whose `attach` operation is the add function, which is how [`acpi_pci_link_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L715) gets invoked for every matching device during the namespace scan:

```c
/* drivers/acpi/pci_link.c:40 */
static const struct acpi_device_id link_device_ids[] = {
	{"PNP0C0F", 0},
	{"", 0},
};

static struct acpi_scan_handler pci_link_handler = {
	.ids = link_device_ids,
	.attach = acpi_pci_link_add,
	.detach = acpi_pci_link_remove,
};
```

[`acpi_pci_link_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L715) reads `_PRS` and `_CRS`, and then evaluates `_DIS` so every link starts out disabled until a PCI device actually needs it:

```c
/* drivers/acpi/pci_link.c:715 */
static int acpi_pci_link_add(struct acpi_device *device,
			     const struct acpi_device_id *not_used)
{
	acpi_handle handle = device->handle;
	struct acpi_pci_link *link;
	int result;
	int i;

	link = kzalloc_obj(struct acpi_pci_link);
	if (!link)
		return -ENOMEM;

	link->device = device;
	strscpy(acpi_device_name(device), ACPI_PCI_LINK_DEVICE_NAME);
	strscpy(acpi_device_class(device), ACPI_PCI_LINK_CLASS);
	device->driver_data = link;

	mutex_lock(&acpi_link_lock);
	result = acpi_pci_link_get_possible(link);
	if (result)
		goto end;

	/* query and set link->irq.active */
	acpi_pci_link_get_current(link);

	pr_info("Interrupt link %s configured for IRQ %d\n",
		acpi_device_bid(device), link->irq.active);

	for (i = 0; i < link->irq.possible_count; i++) {
		if (link->irq.active != link->irq.possible[i])
			acpi_handle_debug(handle, "Possible IRQ %d\n",
					  link->irq.possible[i]);
	}

	if (!link->device->status.enabled)
		pr_info("Interrupt link %s disabled\n", acpi_device_bid(device));

	list_add_tail(&link->list, &acpi_link_list);

      end:
	/* disable all links -- to be activated on use */
	acpi_evaluate_object(handle, "_DIS", NULL, NULL);
	mutex_unlock(&acpi_link_lock);

	if (result)
		kfree(link);

	acpi_dev_clear_dependencies(device);

	return result < 0 ? result : 1;
}
```

The per-link state pairs the [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) with the IRQ bookkeeping that the `_PRS` read fills and the `_SRS` write consumes:

```c
/* drivers/acpi/pci_link.c:51 */
/*
 * If a link is initialized, we never change its active and initialized
 * later even the link is disable. Instead, we just repick the active irq
 */
struct acpi_pci_link_irq {
	u32 active;		/* Current IRQ */
	u8 triggering;		/* All IRQs */
	u8 polarity;		/* All IRQs */
	u8 resource_type;
	u8 possible_count;
	u32 possible[ACPI_PCI_LINK_MAX_POSSIBLE];
	u8 initialized:1;
	u8 reserved:7;
};

struct acpi_pci_link {
	struct list_head		list;
	struct acpi_device		*device;
	struct acpi_pci_link_irq	irq;
	int				refcnt;
};
```

[`acpi_pci_link_get_possible()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L155) runs the `_PRS` walk, and its callback records both the candidate IRQ numbers and the descriptor flavor (`resource_type`), because the buffer a later `_SRS` receives must use the same descriptor kind the firmware advertised:

```c
/* drivers/acpi/pci_link.c:155 */
static int acpi_pci_link_get_possible(struct acpi_pci_link *link)
{
	acpi_handle handle = link->device->handle;
	acpi_status status;

	status = acpi_walk_resources(handle, METHOD_NAME__PRS,
				     acpi_pci_link_check_possible, link);
	if (ACPI_FAILURE(status)) {
		acpi_handle_debug(handle, "_PRS not present or invalid");
		return 0;
	}

	acpi_handle_debug(handle, "Found %d possible IRQs\n",
			  link->irq.possible_count);

	return 0;
}
```

```c
/* drivers/acpi/pci_link.c:84 */
static acpi_status acpi_pci_link_check_possible(struct acpi_resource *resource,
						void *context)
{
	struct acpi_pci_link *link = context;
	acpi_handle handle = link->device->handle;
	u32 i;

	switch (resource->type) {
	case ACPI_RESOURCE_TYPE_START_DEPENDENT:
	case ACPI_RESOURCE_TYPE_END_TAG:
		return AE_OK;
	case ACPI_RESOURCE_TYPE_IRQ:
		{
			struct acpi_resource_irq *p = &resource->data.irq;
			if (!p->interrupt_count) {
				acpi_handle_debug(handle,
						  "Blank _PRS IRQ resource\n");
				return AE_OK;
			}
			for (i = 0;
			     (i < p->interrupt_count
			      && i < ACPI_PCI_LINK_MAX_POSSIBLE); i++) {
				if (!p->interrupts[i]) {
					acpi_handle_debug(handle,
							  "Invalid _PRS IRQ %d\n",
							  p->interrupts[i]);
					continue;
				}
				link->irq.possible[i] = p->interrupts[i];
				link->irq.possible_count++;
			}
			link->irq.triggering = p->triggering;
			link->irq.polarity = p->polarity;
			link->irq.resource_type = ACPI_RESOURCE_TYPE_IRQ;
			break;
		}
	case ACPI_RESOURCE_TYPE_EXTENDED_IRQ:
		{
			struct acpi_resource_extended_irq *p =
			    &resource->data.extended_irq;
			...
			link->irq.triggering = p->triggering;
			link->irq.polarity = p->polarity;
			link->irq.resource_type = ACPI_RESOURCE_TYPE_EXTENDED_IRQ;
			break;
		}
	default:
		acpi_handle_debug(handle, "_PRS resource type 0x%x is not IRQ\n",
				  resource->type);
		return AE_OK;
	}

	return AE_CTRL_TERMINATE;
}
```

The callback caps the recorded candidates at [`ACPI_PCI_LINK_MAX_POSSIBLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L34) (16 entries in the `possible` array) and skips the StartDependentFn marker records, since for a link device the alternatives appear as one multi-IRQ descriptor rather than dependent function groups.

### acpi_pci_link_allocate picks the IRQ and calls the setter

[`acpi_pci_link_allocate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L528) implements the OSPM "choose an assignment" step. It prefers the IRQ `_CRS` already reported when the `_PRS` list contains that IRQ, otherwise it scans the possible list against the ISA IRQ penalty table, and then it commits the choice through [`acpi_pci_link_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L277):

```c
/* drivers/acpi/pci_link.c:528 */
static int acpi_pci_link_allocate(struct acpi_pci_link *link)
{
	acpi_handle handle = link->device->handle;
	u32 irq;
	int i;

	if (link->irq.initialized) {
		if (link->refcnt == 0)
			/* This means the link is disabled but initialized */
			acpi_pci_link_set(link, link->irq.active);
		return 0;
	}

	/*
	 * search for active IRQ in list of possible IRQs.
	 */
	for (i = 0; i < link->irq.possible_count; ++i) {
		if (link->irq.active == link->irq.possible[i])
			break;
	}
	/*
	 * forget active IRQ that is not in possible list
	 */
	if (i == link->irq.possible_count) {
		if (acpi_strict)
			acpi_handle_warn(handle, "_CRS %d not found in _PRS\n",
					 link->irq.active);
		link->irq.active = 0;
	}

	/*
	 * if active found, use it; else pick entry from end of possible list.
	 */
	if (link->irq.active)
		irq = link->irq.active;
	else
		irq = link->irq.possible[link->irq.possible_count - 1];

	if (acpi_irq_balance || !link->irq.active) {
		/*
		 * Select the best IRQ.  This is done in reverse to promote
		 * the use of IRQs 9, 10, 11, and >15.
		 */
		for (i = (link->irq.possible_count - 1); i >= 0; i--) {
			if (acpi_irq_get_penalty(irq) >
			    acpi_irq_get_penalty(link->irq.possible[i]))
				irq = link->irq.possible[i];
		}
	}
	if (acpi_irq_get_penalty(irq) >= PIRQ_PENALTY_ISA_ALWAYS) {
		acpi_handle_err(handle,
				"No IRQ available. Try pci=noacpi or acpi=off\n");
		return -ENODEV;
	}

	/* Attempt to enable the link device at this IRQ. */
	if (acpi_pci_link_set(link, irq)) {
		acpi_handle_err(handle,
				"Unable to set IRQ. Try pci=noacpi or acpi=off\n");
		return -ENODEV;
	} else {
		if (link->irq.active < ACPI_MAX_ISA_IRQS)
			acpi_isa_irq_penalty[link->irq.active] +=
				PIRQ_PENALTY_PCI_USING;

		acpi_handle_info(handle, "Enabled at IRQ %d\n",
				 link->irq.active);
	}

	link->irq.initialized = 1;
	return 0;
}
```

The allocator runs when a PCI device's INTx pin actually gets routed. [`acpi_pci_irq_enable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_irq.c#L384) looks the device's pin up in the `_PRT` table and, when the entry points at a link device, calls the exported [`acpi_pci_link_allocate_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L615), which resolves the handle back to the [`struct acpi_pci_link`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L66) and drives the allocation under the link mutex:

```c
/* drivers/acpi/pci_link.c:615 */
int acpi_pci_link_allocate_irq(acpi_handle handle, int index, int *triggering,
			       int *polarity, char **name, u32 *gsi)
{
	struct acpi_device *device = acpi_fetch_acpi_dev(handle);
	struct acpi_pci_link *link;
	...
	mutex_lock(&acpi_link_lock);
	if (acpi_pci_link_allocate(link)) {
		mutex_unlock(&acpi_link_lock);
		return -ENODEV;
	}

	if (!link->irq.active) {
		mutex_unlock(&acpi_link_lock);
		acpi_handle_err(handle, "Link active IRQ is 0!\n");
		return -ENODEV;
	}
	link->refcnt++;
	mutex_unlock(&acpi_link_lock);
	...
}
```

### acpi_pci_link_set builds the buffer by resource type

[`acpi_pci_link_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L277) is the in-tree `_SRS` writer with the smallest buffer, exactly two [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678) records, the chosen IRQ descriptor and the End Tag, declared as an anonymous two-member struct so the layout matches what [`acpi_rs_get_aml_length()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rscalc.c#L154) walks. The function then runs every step of the spec protocol in order, write `_SRS`, check `_STA`, re-read `_CRS`, and reconcile:

```c
/* drivers/acpi/pci_link.c:277 */
static int acpi_pci_link_set(struct acpi_pci_link *link, int irq)
{
	struct {
		struct acpi_resource res;
		struct acpi_resource end;
	} *resource;
	struct acpi_buffer buffer = { 0, NULL };
	acpi_handle handle = link->device->handle;
	acpi_status status;
	int result;

	if (!irq)
		return -EINVAL;

	resource = kzalloc(sizeof(*resource) + 1, irqs_disabled() ? GFP_ATOMIC: GFP_KERNEL);
	if (!resource)
		return -ENOMEM;

	buffer.length = sizeof(*resource) + 1;
	buffer.pointer = resource;

	switch (link->irq.resource_type) {
	case ACPI_RESOURCE_TYPE_IRQ:
		resource->res.type = ACPI_RESOURCE_TYPE_IRQ;
		resource->res.length = sizeof(struct acpi_resource);
		resource->res.data.irq.triggering = link->irq.triggering;
		resource->res.data.irq.polarity =
		    link->irq.polarity;
		if (link->irq.triggering == ACPI_EDGE_SENSITIVE)
			resource->res.data.irq.shareable =
			    ACPI_EXCLUSIVE;
		else
			resource->res.data.irq.shareable = ACPI_SHARED;
		resource->res.data.irq.interrupt_count = 1;
		resource->res.data.irq.interrupts[0] = irq;
		break;

	case ACPI_RESOURCE_TYPE_EXTENDED_IRQ:
		resource->res.type = ACPI_RESOURCE_TYPE_EXTENDED_IRQ;
		resource->res.length = sizeof(struct acpi_resource);
		resource->res.data.extended_irq.producer_consumer =
		    ACPI_CONSUMER;
		resource->res.data.extended_irq.triggering =
		    link->irq.triggering;
		resource->res.data.extended_irq.polarity =
		    link->irq.polarity;
		if (link->irq.triggering == ACPI_EDGE_SENSITIVE)
			resource->res.data.extended_irq.shareable =
			    ACPI_EXCLUSIVE;
		else
			resource->res.data.extended_irq.shareable = ACPI_SHARED;
		resource->res.data.extended_irq.interrupt_count = 1;
		resource->res.data.extended_irq.interrupts[0] = irq;
		/* ignore resource_source, it's optional */
		break;
	default:
		acpi_handle_err(handle, "Invalid resource type %d\n",
				link->irq.resource_type);
		result = -EINVAL;
		goto end;

	}
	resource->end.type = ACPI_RESOURCE_TYPE_END_TAG;
	resource->end.length = sizeof(struct acpi_resource);

	/* Attempt to set the resource */
	status = acpi_set_current_resources(link->device->handle, &buffer);

	/* check for total failure */
	if (ACPI_FAILURE(status)) {
		acpi_evaluation_failure_warn(handle, "_SRS", status);
		result = -ENODEV;
		goto end;
	}

	/* Query _STA, set device->status */
	result = acpi_bus_get_status(link->device);
	if (result) {
		acpi_handle_err(handle, "Unable to read status\n");
		goto end;
	}
	if (!link->device->status.enabled)
		acpi_handle_warn(handle, "Disabled and referenced, BIOS bug\n");

	/* Query _CRS, set link->irq.active */
	result = acpi_pci_link_get_current(link);
	if (result) {
		goto end;
	}

	/*
	 * Is current setting not what we set?
	 * set link->irq.active
	 */
	if (link->irq.active != irq) {
		/*
		 * policy: when _CRS doesn't return what we just _SRS
		 * assume _SRS worked and override _CRS value.
		 */
		acpi_handle_warn(handle, "BIOS reported IRQ %d, using IRQ %d\n",
				 link->irq.active, irq);
		link->irq.active = irq;
	}

	acpi_handle_debug(handle, "Set IRQ %d\n", link->irq.active);

      end:
	kfree(resource);
	return result;
}
```

Several details in the descriptor build pair directly with the spec. The `resource_type` recorded from `_PRS` selects which payload union member is filled, [`struct acpi_resource_irq`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L138) for the legacy small item or [`struct acpi_resource_extended_irq`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L333) for the large Extended Interrupt item, so the encoded stream uses the descriptor kind the firmware's `_PRS` template advertised. The triggering and polarity come back unchanged from the `_PRS` read, since section 6.2.16 obliges OSPM to write every field, and the sharing field is derived (edge-triggered links are marked [`ACPI_EXCLUSIVE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L69), level-triggered ones [`ACPI_SHARED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L70)). The extended branch sets `producer_consumer` to [`ACPI_CONSUMER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L115) and leaves the optional `resource_source` zeroed by the [`kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h#L1190). The allocation switches to `GFP_ATOMIC` under [`irqs_disabled()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/irqflags.h#L191) because the resume path can reach this function before interrupts are back on.

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

On failure the function logs through [`acpi_evaluation_failure_warn()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L653), the shared helper that names the failing method and formats the status:

```c
/* drivers/acpi/utils.c:647 */
/**
 * acpi_evaluation_failure_warn - Log evaluation failure warning.
 * @handle: Parent object handle.
 * @name: Name of the object whose evaluation has failed.
 * @status: Status value returned by the failing object evaluation.
 */
void acpi_evaluation_failure_warn(acpi_handle handle, const char *name,
				  acpi_status status)
{
	acpi_handle_warn(handle, "%s evaluation failed: %s\n", name,
			 acpi_format_exception(status));
}
EXPORT_SYMBOL_GPL(acpi_evaluation_failure_warn);
```

### The post-write _CRS re-read closes the loop

[`acpi_pci_link_get_current()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L228) performs the verification read the spec protocol ends with. Under `acpi_strict` it first checks `_STA` through [`acpi_bus_get_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L95) and treats a disabled link as having no current IRQ; it then walks `_CRS` with the same callback shape the `_PRS` read used:

```c
/* drivers/acpi/pci_link.c:228 */
static int acpi_pci_link_get_current(struct acpi_pci_link *link)
{
	acpi_handle handle = link->device->handle;
	acpi_status status;
	int result = 0;
	int irq = 0;

	link->irq.active = 0;

	/* in practice, status disabled is meaningless, ignore it */
	if (acpi_strict) {
		/* Query _STA, set link->device->status */
		result = acpi_bus_get_status(link->device);
		if (result) {
			acpi_handle_err(handle, "Unable to read status\n");
			goto end;
		}

		if (!link->device->status.enabled) {
			acpi_handle_debug(handle, "Link disabled\n");
			return 0;
		}
	}

	/*
	 * Query and parse _CRS to get the current IRQ assignment.
	 */

	status = acpi_walk_resources(handle, METHOD_NAME__CRS,
				     acpi_pci_link_check_current, &irq);
	if (ACPI_FAILURE(status)) {
		acpi_evaluation_failure_warn(handle, "_CRS", status);
		result = -ENODEV;
		goto end;
	}

	if (acpi_strict && !irq) {
		acpi_handle_err(handle, "_CRS returned 0\n");
		result = -ENODEV;
	}

	link->irq.active = irq;

	acpi_handle_debug(handle, "Link at IRQ %d\n", link->irq.active);

      end:
	return result;
}
```

```c
/* drivers/acpi/pci_link.c:173 */
static acpi_status acpi_pci_link_check_current(struct acpi_resource *resource,
					       void *context)
{
	int *irq = context;

	switch (resource->type) {
	case ACPI_RESOURCE_TYPE_START_DEPENDENT:
	case ACPI_RESOURCE_TYPE_END_TAG:
		return AE_OK;
	case ACPI_RESOURCE_TYPE_IRQ:
		{
			struct acpi_resource_irq *p = &resource->data.irq;
			if (!p->interrupt_count) {
				/*
				 * IRQ descriptors may have no IRQ# bits set,
				 * particularly those w/ _STA disabled
				 */
				pr_debug("Blank _CRS IRQ resource\n");
				return AE_OK;
			}
			*irq = p->interrupts[0];
			break;
		}
	case ACPI_RESOURCE_TYPE_EXTENDED_IRQ:
		{
			struct acpi_resource_extended_irq *p =
			    &resource->data.extended_irq;
			if (!p->interrupt_count) {
				/*
				 * extended IRQ descriptors must
				 * return at least 1 IRQ
				 */
				pr_debug("Blank _CRS EXT IRQ resource\n");
				return AE_OK;
			}
			*irq = p->interrupts[0];
			break;
		}
		break;
	default:
		pr_debug("_CRS resource type 0x%x is not IRQ\n",
			 resource->type);
		return AE_OK;
	}

	return AE_CTRL_TERMINATE;
}
```

According to the comment "policy: when _CRS doesn't return what we just _SRS assume _SRS worked and override _CRS value" in [`acpi_pci_link_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L277), a mismatch between the written IRQ and the re-read one resolves in favor of the write, the driver trusting its own `_SRS` over a firmware `_CRS` that fails to reflect it.

### Suspend and resume replay _SRS

Because `_SRS` programs volatile routing hardware, the setting evaporates across a system sleep. [`acpi_pci_link_resume()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L767) re-issues the write for every link that is referenced, has an active IRQ, and was initialized, and the syscore resume hook iterates the global link list:

```c
/* drivers/acpi/pci_link.c:767 */
static int acpi_pci_link_resume(struct acpi_pci_link *link)
{
	if (link->refcnt && link->irq.active && link->irq.initialized)
		return (acpi_pci_link_set(link, link->irq.active));

	return 0;
}

static void irqrouter_resume(void *data)
{
	struct acpi_pci_link *link;

	list_for_each_entry(link, &acpi_link_list, list) {
		acpi_pci_link_resume(link);
	}
}
```

The same replay shape exists inside [`acpi_pci_link_allocate()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L528), whose `initialized && refcnt == 0` branch re-runs [`acpi_pci_link_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L277) with the previously chosen IRQ when a link that was disabled gets referenced again, so across the whole driver the `_SRS` buffer is rebuilt from [`struct acpi_pci_link_irq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L55) state rather than cached, and every write funnels through the single [`acpi_set_current_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L248) entry point this page documents.
