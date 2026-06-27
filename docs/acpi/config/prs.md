# _PRS

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

`_PRS` is the Possible Resource Settings method that a configurable ACPI device carries next to `_CRS`. Evaluating it returns a Buffer in the same section 6.4 descriptor encoding as `_CRS`, except that the stream expresses alternatives, with StartDependentFn and StartDependentFnNoPri markers opening priority-rated groups of mutually dependent descriptors and EndDependentFn closing the grouped region. ACPICA decodes the markers into [`ACPI_RESOURCE_TYPE_START_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L611) and [`ACPI_RESOURCE_TYPE_END_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L612) records, with the priority pair carried in [`struct acpi_resource_start_dependent`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L162), and the kernel fetches the stream through [`acpi_get_possible_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L209) or [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) with [`METHOD_NAME__PRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L30). The main consumer is PNP ACPI, where [`pnpacpi_parse_resource_option_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L550) turns each dependent group into a numbered, prioritized set of [`struct pnp_option`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L65) records that [`pnp_assign_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L256) later tries set by set before programming the winner through `_SRS`, and a second reader is the interrupt link driver's [`acpi_pci_link_get_possible()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L155), which collects the candidate IRQs of a link device.

```
    _PRS dependent-function groups become prioritized option sets
    ──────────────────────────────────────────────────────────────

    Name (_PRS, ResourceTemplate () { ... })  (decoded record stream)
    ┌──────────────────────────────────────────────────────────────┐
    │  StartDependentFn (0, 0)  { IO 0x3F8/8, IRQ {4} }             │
    │  StartDependentFn (1, 1)  { IO 0x2F8/8, IRQ {3} }             │
    │  StartDependentFn (2, 2)  { IO 0x100..0x3F8/8, IRQ {1,3,..} } │
    │  EndDependentFn ()                                            │
    └───────────────────────────────┬──────────────────────────────┘
                                    │ pnpacpi_option_resource()
                                    │ one option list entry per
                                    │ descriptor, set per group
               ┌────────────────────┼────────────────────┐
               ▼                    ▼                    ▼
       dependent set 0      dependent set 1      dependent set 2
       PNP_RES_PRIORITY_    PNP_RES_PRIORITY_    PNP_RES_PRIORITY_
       PREFERRED            ACCEPTABLE           FUNCTIONAL
      ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
      │ pnp_option      │  │ pnp_option      │  │ pnp_option      │
      │  IORESOURCE_IO  │  │  IORESOURCE_IO  │  │  IORESOURCE_IO  │
      │  min 0x3F8      │  │  min 0x2F8      │  │  min 0x100      │
      │ pnp_option      │  │ pnp_option      │  │ pnp_option      │
      │  IORESOURCE_IRQ │  │  IORESOURCE_IRQ │  │  IORESOURCE_IRQ │
      │  map 0x0010     │  │  map 0x0008     │  │  map 0x1DFA     │
      └─────────────────┘  └─────────────────┘  └─────────────────┘

    (each StartDependentFn record opens a new set through
     pnp_new_dependent_set(); the compatibility_priority byte maps
     ACPI_GOOD/ACCEPTABLE/SUB_OPTIMAL_CONFIGURATION onto the three
     PNP_RES_PRIORITY_* values; EndDependentFn resets option_flags
     to 0 so later records register as independent options again)
```

## SUMMARY

The ACPI specification defines `_PRS` in section 6.2.12 as a zero-argument object returning a byte stream of possible resource settings, encoded exactly like a `_CRS` template and read by OSPM before it picks a configuration to program with `_SRS` (section 6.2.16). Dependency between descriptors is expressed with the Start Dependent Functions and End Dependent Functions small items of section 6.4.2, whose AML tags the kernel carries as [`ACPI_RESOURCE_NAME_START_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1110) (0x30) and [`ACPI_RESOURCE_NAME_END_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1111) (0x38). Every descriptor between one StartDependentFn and the next belongs to one alternative configuration, descriptors before the first marker or after EndDependentFn apply unconditionally, and the optional priority byte of the one-byte StartDependentFn form rates the group with two 2-bit fields, compatibility priority and performance/robustness, each taking [`ACPI_GOOD_CONFIGURATION`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L95) (0), [`ACPI_ACCEPTABLE_CONFIGURATION`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L96) (1), or [`ACPI_SUB_OPTIMAL_CONFIGURATION`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L97) (2). ACPICA decodes the markers into [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678) records of type [`ACPI_RESOURCE_TYPE_START_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L611) and [`ACPI_RESOURCE_TYPE_END_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L612), the former carrying [`struct acpi_resource_start_dependent`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L162) with both priority fields, and the fetch APIs are [`acpi_get_possible_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L209) calling [`acpi_rs_get_prs_method_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsutils.c#L534) for a decoded block and [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) with [`METHOD_NAME__PRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L30) for callback iteration.

The PNP ACPI protocol is the consumer that uses the full dependent-group semantics. [`pnpacpi_add_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L209) marks a device [`PNP_CONFIGURABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pnp.h#L305) when it has `_SRS` and then runs [`pnpacpi_parse_resource_option_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L550), whose per-record callback [`pnpacpi_option_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L454) opens a new dependent set on every [`ACPI_RESOURCE_TYPE_START_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L611) record by mapping the ACPI priority onto [`PNP_RES_PRIORITY_PREFERRED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L60), [`PNP_RES_PRIORITY_ACCEPTABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L61), or [`PNP_RES_PRIORITY_FUNCTIONAL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L62) and encoding set number plus priority into the option flags with [`pnp_new_dependent_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L107). The per-descriptor parsers ([`pnpacpi_parse_irq_option()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L306), [`pnpacpi_parse_port_option()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L347), and siblings) register one [`struct pnp_option`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L65) per descriptor on the device's options list through [`pnp_register_irq_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/resource.c#L52) and friends, all funneling into [`pnp_build_option()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/resource.c#L36). The options later drive automatic configuration, where [`pnp_auto_config_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L308) tries [`pnp_assign_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L256) for set 0 through `num_dependent_sets - 1` until one assignment succeeds, and [`pnp_start_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L337) programs the chosen configuration through the protocol's set hook, which for ACPI is [`pnpacpi_set_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L49) ending in `_SRS`. The parsed sets are user visible in the `options` sysfs attribute rendered by [`options_show()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/interface.c#L208).

Beyond PNP, the ACPI interrupt link driver reads `_PRS` through the same walk to learn the candidate IRQs of a `PNP0C0F` link device, with [`acpi_pci_link_check_possible()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L84) skipping the dependent markers and harvesting the IRQ descriptor payloads into `link->irq.possible[]`. The platform-device path reads `_CRS` alone; [`acpi_create_platform_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_platform.c#L110) fetches its resources through [`acpi_dev_get_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1000), which hardwires [`METHOD_NAME__CRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L21), so the platform path leaves a `_PRS` unevaluated, and the dependent-group machinery documented here is consumed by the PNP protocol and the interrupt link driver.

## SPECIFICATIONS

- ACPI Specification, section 6.2: Device Configuration Objects
- ACPI Specification, section 6.2.12: _PRS (Possible Resource Settings)
- ACPI Specification, section 6.2.16: _SRS (Set Resource Settings)
- ACPI Specification, section 6.2.2: _CRS (Current Resource Settings)
- ACPI Specification, section 6.4: Resource Data Types for ACPI
- ACPI Specification, section 6.4.2: Small Resource Data Type (Start Dependent Functions and End Dependent Functions descriptors)
- ACPI Specification, section 19.6: ASL Operator Reference (StartDependentFn, StartDependentFnNoPri, EndDependentFn macros)

## LINUX KERNEL

### ACPICA fetch and decoded types

- [`'\<acpi_get_possible_resources\>':'drivers/acpi/acpica/rsxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L209): public block fetch of the decoded `_PRS` list
- [`'\<acpi_rs_get_prs_method_data\>':'drivers/acpi/acpica/rsutils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsutils.c#L534): evaluates `_PRS` and builds the decoded list
- [`'\<acpi_walk_resources\>':'drivers/acpi/acpica/rsxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594): per-descriptor walk accepting `_PRS` alongside `_CRS`, `_AEI`, and `_DMA`
- [`METHOD_NAME__PRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L30): the `"_PRS"` name string macro
- [`'\<struct acpi_resource_start_dependent\>':'include/acpi/acrestyp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L162): decoded group marker with both priority fields
- [`ACPI_RESOURCE_TYPE_START_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L611): decoded type value 2, opens a dependent group
- [`ACPI_RESOURCE_TYPE_END_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L612): decoded type value 3, closes the grouped region
- [`ACPI_GOOD_CONFIGURATION`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L95) / [`ACPI_ACCEPTABLE_CONFIGURATION`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L96) / [`ACPI_SUB_OPTIMAL_CONFIGURATION`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L97): spec priority values 0, 1, 2
- [`ACPI_RESOURCE_NAME_START_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1110): AML small-item tag 0x30 of the StartDependentFn descriptor

### PNP ACPI option parsing

- [`'\<pnpacpi_parse_resource_option_data\>':'drivers/pnp/pnpacpi/rsparser.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L550): walks `_PRS` and registers every option
- [`'\<pnpacpi_option_resource\>':'drivers/pnp/pnpacpi/rsparser.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L454): per-record dispatch, opens and closes dependent sets
- [`'\<struct acpipnp_parse_option_s\>':'drivers/pnp/pnpacpi/rsparser.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L449): walk context carrying the device and the current option flags
- [`'\<pnpacpi_parse_irq_option\>':'drivers/pnp/pnpacpi/rsparser.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L306): legacy IRQ descriptor to IRQ bitmap option
- [`'\<pnpacpi_parse_ext_irq_option\>':'drivers/pnp/pnpacpi/rsparser.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L323): extended Interrupt descriptor to IRQ bitmap option
- [`'\<pnpacpi_parse_port_option\>':'drivers/pnp/pnpacpi/rsparser.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L347): IO descriptor to port-range option
- [`'\<pnpacpi_parse_dma_option\>':'drivers/pnp/pnpacpi/rsparser.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L292): DMA descriptor to channel-mask option
- [`'\<pnpacpi_parse_mem32_option\>':'drivers/pnp/pnpacpi/rsparser.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L379): Memory32 descriptor to memory-range option
- [`'\<pnpacpi_parse_address_option\>':'drivers/pnp/pnpacpi/rsparser.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L403): address-space descriptor to port or memory option

### PNP option storage

- [`'\<struct pnp_option\>':'drivers/pnp/base.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L65): one allocation possibility, flags plus a typed payload union
- [`'\<struct pnp_irq\>':'drivers/pnp/base.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L36) / [`'\<struct pnp_port\>':'drivers/pnp/base.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L25): IRQ bitmap and port-range payloads
- [`'\<pnp_build_option\>':'drivers/pnp/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/resource.c#L36): allocates an option and appends it to the device's options list
- [`'\<pnp_register_irq_resource\>':'drivers/pnp/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/resource.c#L52): IRQ option registration used by both IRQ parsers
- [`'\<pnp_register_port_resource\>':'drivers/pnp/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/resource.c#L98): port option registration
- [`'\<pnp_register_mem_resource\>':'drivers/pnp/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/resource.c#L121): memory option registration
- [`'\<pnp_register_dma_resource\>':'drivers/pnp/resource.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/resource.c#L80): DMA option registration
- [`'\<pnp_new_dependent_set\>':'drivers/pnp/base.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L107): encodes set number and priority into option flags
- [`PNP_OPTION_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L54): flag bit separating dependent options from independent ones
- [`PNP_RES_PRIORITY_PREFERRED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L60) / [`PNP_RES_PRIORITY_ACCEPTABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L61) / [`PNP_RES_PRIORITY_FUNCTIONAL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L62): PNP-side priority values
- [`'\<pnp_option_is_dependent\>':'drivers/pnp/base.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L91) / [`'\<pnp_option_set\>':'drivers/pnp/base.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L96) / [`'\<pnp_option_priority\>':'drivers/pnp/base.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L101): flag decoding helpers
- [`'\<struct pnp_dev\>':'include/linux/pnp.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pnp.h#L243): device object holding the options list and `num_dependent_sets`

### Configuration flow and sysfs

- [`'\<pnpacpi_add_device\>':'drivers/pnp/pnpacpi/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L209): builds the PNP device, gates option parsing on `_SRS` presence
- [`'\<pnp_auto_config_dev\>':'drivers/pnp/manager.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L308): tries each dependent set in order until one fits
- [`'\<pnp_assign_resources\>':'drivers/pnp/manager.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L256): assigns from independent options plus one chosen set
- [`'\<pnp_assign_irq\>':'drivers/pnp/manager.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L132): picks a free IRQ from one option's bitmap
- [`'\<pnp_activate_dev\>':'drivers/pnp/manager.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L383): driver-facing entry that auto-configures and starts the device
- [`'\<pnp_start_dev\>':'drivers/pnp/manager.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L337): pushes the assigned resources to the protocol set hook
- [`'\<pnpacpi_set_resources\>':'drivers/pnp/pnpacpi/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L49): encodes the assignment and evaluates `_SRS`
- [`'\<pnpacpi_get_resources\>':'drivers/pnp/pnpacpi/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L43): protocol get hook re-reading `_CRS`
- [`'\<pnpacpi_parse_allocated_resource\>':'drivers/pnp/pnpacpi/rsparser.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L271): `_CRS` walk filling the current resource table
- [`'\<pnpacpi_protocol\>':'drivers/pnp/pnpacpi/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L184): protocol pairing the get/set/disable hooks
- [`'\<options_show\>':'drivers/pnp/interface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/interface.c#L208): renders the parsed option sets in the `options` sysfs attribute
- [`'\<pnp_option_priority_name\>':'drivers/pnp/support.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/support.c#L92): maps the encoded priority back to its name
- [`'\<pnp_dev_groups\>':'drivers/pnp/interface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/interface.c#L467): attribute group exposing `options` on every PNP device

### Interrupt link consumer

- [`'\<acpi_pci_link_get_possible\>':'drivers/acpi/pci_link.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L155): walks the link device's `_PRS` for candidate IRQs
- [`'\<acpi_pci_link_check_possible\>':'drivers/acpi/pci_link.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L84): callback harvesting IRQ descriptors and skipping group markers
- [`'\<struct acpi_pci_link\>':'drivers/acpi/pci_link.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L66) / [`'\<struct acpi_pci_link_irq\>':'drivers/acpi/pci_link.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L55): link state holding `possible[]` and `possible_count`

## KERNEL DOCUMENTATION

- [`Documentation/admin-guide/pnp.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/admin-guide/pnp.rst): the PNP layer whose option machinery `_PRS` feeds, including the sysfs interface
- [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst): ACPI enumeration paths surrounding the PNP ACPI protocol
- [`Documentation/driver-api/acpi/linuxized-acpica.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/acpi/linuxized-acpica.rst): maintenance model of the ACPICA code that evaluates and decodes `_PRS`

## OTHER SOURCES

- [ACPI Specification 6.5, chapter 6: Device Configuration](https://uefi.org/specs/ACPI/6.5/06_Device_Configuration.html)
- [ACPI Specification 6.5, chapter 19: ASL Reference](https://uefi.org/specs/ACPI/6.5/19_ASL_Reference.html)
- [Commit 1f32ca31e740 ("PNP: convert resource options to single linked list")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=1f32ca31e7409d37c1b25e5f81840fb184380cdf)
- [Commit 046d9ce6820e ("ACPI: Move device resources interpretation code from PNP to ACPI core")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=046d9ce6820e99087e81511284045eada94950e8)

## METHODS

### _PRS (possible resource settings, 0 arguments)

`_PRS` is a spec-defined object name with no function definition in the kernel; the kernel addresses it through the [`METHOD_NAME__PRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L30) string macro. Section 6.2.12 requires a Buffer in the section 6.4 descriptor encoding, and ACPICA enforces the Buffer type inside [`acpi_rs_get_prs_method_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsutils.c#L534) exactly as it does for `_CRS`. The semantic difference from `_CRS` lives in the content, where StartDependentFn/StartDependentFnNoPri and EndDependentFn group descriptors into rated alternatives, decoded as [`ACPI_RESOURCE_TYPE_START_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L611) and [`ACPI_RESOURCE_TYPE_END_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L612) records. The kernel evaluates `_PRS` once per device at PNP registration time, when [`pnpacpi_add_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L209) calls [`pnpacpi_parse_resource_option_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L550) for every device that carries `_SRS`, and once per interrupt link device in [`acpi_pci_link_get_possible()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L155). Both consumers fetch through [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594); the block API [`acpi_get_possible_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L209) is the exported ACPICA entry point wrapping the same evaluator.

### _CRS and _SRS as the adjacent steps of the PNP flow

`_PRS` is the middle of a three-method protocol. [`pnpacpi_get_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L43) reads the current assignment by walking `_CRS` through [`pnpacpi_parse_allocated_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L271) with [`METHOD_NAME__CRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L21), `_PRS` supplies the menu of alternatives parsed into options, and [`pnpacpi_set_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L49) writes the chosen configuration back by encoding the assigned resource table into a template and evaluating `_SRS` ([`METHOD_NAME__SRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L40)) through [`acpi_set_current_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L248). The three hooks are wired together in [`pnpacpi_protocol`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L184), and the DETAILS section below shows the set side as far as the `_SRS` evaluation; the template encoding behind [`pnpacpi_build_resource_template()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L622) and [`pnpacpi_encode_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L877) belongs to the `_SRS` write path and stays outside this page.

## DETAILS

### A _PRS template with three dependent groups

The following ASL declares a serial-port-style device with three alternative configurations, modeled on the classic COM-port example the dependent-function descriptors were designed for and on the `PNP0501` identity example in the spec; the priorities differ per group so the walkthrough exercises all three priority mappings:

```asl
Device (\_SB.UAR1)
{
    Name (_HID, EISAID ("PNP0501"))     // 16550A-compatible UART
    Name (_UID, 1)
    Name (_PRS, ResourceTemplate ()
    {
        StartDependentFn (0, 0)         // good / good
        {
            IO (Decode16, 0x03F8, 0x03F8, 0x01, 0x08)
            IRQ (Edge, ActiveHigh, Exclusive) {4}
        }
        StartDependentFn (1, 1)         // acceptable / acceptable
        {
            IO (Decode16, 0x02F8, 0x02F8, 0x01, 0x08)
            IRQ (Edge, ActiveHigh, Exclusive) {3}
        }
        StartDependentFn (2, 2)         // sub-optimal / sub-optimal
        {
            IO (Decode16, 0x0100, 0x03F8, 0x08, 0x08)
            IRQ (Edge, ActiveHigh, Exclusive) {1, 3, 4, 5, 6, 7, 8, 10, 11, 12}
        }
        EndDependentFn ()
    })
    Method (_SRS, 1, NotSerialized) { /* programs the device */ }
    Name (_CRS, ResourceTemplate ()
    {
        IO (Decode16, 0x03F8, 0x03F8, 0x01, 0x08)
        IRQ (Edge, ActiveHigh, Exclusive) {4}
    })
}
```

The braces after each `StartDependentFn` are ASL syntax only; in the compiled AML the group marker is a small item (tag byte 0x31 with the one-byte priority payload, or 0x30 with none for `StartDependentFnNoPri`) followed by the member descriptors as ordinary stream cells, and `EndDependentFn` is the bare 0x38 tag. The kernel's tag constants record the type bits of those bytes:

```c
/* drivers/acpi/acpica/aclocal.h:1104 */
/*
 * Small resource descriptor "names" as defined by the ACPI specification.
 * Note: Bits 2:0 are used for the descriptor length
 */
#define ACPI_RESOURCE_NAME_IRQ                  0x20
#define ACPI_RESOURCE_NAME_DMA                  0x28
#define ACPI_RESOURCE_NAME_START_DEPENDENT      0x30
#define ACPI_RESOURCE_NAME_END_DEPENDENT        0x38
#define ACPI_RESOURCE_NAME_IO                   0x40
```

The priority argument pair of `StartDependentFn` is (compatibility, performance/robustness), each one of the three spec values that the kernel carries next to the other descriptor field constants:

```c
/* include/acpi/acrestyp.h:92 */
/*
 * Start Dependent Functions Priority definitions
 */
#define ACPI_GOOD_CONFIGURATION         (u8) 0x00
#define ACPI_ACCEPTABLE_CONFIGURATION   (u8) 0x01
#define ACPI_SUB_OPTIMAL_CONFIGURATION  (u8) 0x02
```

### ACPICA fetch: acpi_get_possible_resources and the _PRS evaluator

[`acpi_get_possible_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L209) is the exported block-fetch API, structurally identical to its `_CRS` sibling and dispatching to the `_PRS`-specific evaluator:

```c
/* drivers/acpi/acpica/rsxface.c:208 */
acpi_status
acpi_get_possible_resources(acpi_handle device_handle,
			    struct acpi_buffer *ret_buffer)
{
	acpi_status status;
	struct acpi_namespace_node *node;

	ACPI_FUNCTION_TRACE(acpi_get_possible_resources);

	/* Validate parameters then dispatch to internal routine */

	status = acpi_rs_validate_parameters(device_handle, ret_buffer, &node);
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}

	status = acpi_rs_get_prs_method_data(node, ret_buffer);
	return_ACPI_STATUS(status);
}

ACPI_EXPORT_SYMBOL(acpi_get_possible_resources)
```

[`acpi_rs_get_prs_method_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsutils.c#L534) is the callee end of that dispatch. It evaluates the object with a required Buffer type and feeds the returned bytes to the same [`acpi_rs_create_resource_list()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rscreate.c#L103) decode that `_CRS` uses, so dependent-group markers come out as ordinary [`struct acpi_resource`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L678) records in the stream:

```c
/* drivers/acpi/acpica/rsutils.c:533 */
acpi_status
acpi_rs_get_prs_method_data(struct acpi_namespace_node *node,
			    struct acpi_buffer *ret_buffer)
{
	union acpi_operand_object *obj_desc;
	acpi_status status;

	ACPI_FUNCTION_TRACE(rs_get_prs_method_data);

	/* Parameters guaranteed valid by caller */

	/* Execute the method, no parameters */

	status =
	    acpi_ut_evaluate_object(node, METHOD_NAME__PRS, ACPI_BTYPE_BUFFER,
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

The in-tree consumers reach `_PRS` through the walk API instead of the block API. [`acpi_walk_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L594) admits `_PRS` as one of its four legal names and runs the caller's callback over each decoded record:

```c
/* drivers/acpi/acpica/rsxface.c:605 */
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
```

### The decoded group markers and their priority fields

A StartDependentFn cell decodes to a record of type [`ACPI_RESOURCE_TYPE_START_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L611) whose payload is the `start_dpf` member of [`union acpi_resource_data`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L639), and an EndDependentFn cell decodes to [`ACPI_RESOURCE_TYPE_END_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L612) with an empty payload:

```c
/* include/acpi/acrestyp.h:162 */
struct acpi_resource_start_dependent {
	u8 descriptor_length;
	u8 compatibility_priority;
	u8 performance_robustness;
};

/*
 * The END_DEPENDENT_FUNCTIONS_RESOURCE struct is not
 * needed because it has no fields
 */
```

```c
/* include/acpi/acrestyp.h:609 */
#define ACPI_RESOURCE_TYPE_IRQ                  0
#define ACPI_RESOURCE_TYPE_DMA                  1
#define ACPI_RESOURCE_TYPE_START_DEPENDENT      2
#define ACPI_RESOURCE_TYPE_END_DEPENDENT        3
#define ACPI_RESOURCE_TYPE_IO                   4
```

`descriptor_length` records which of the two AML encodings appeared, the zero-payload `StartDependentFnNoPri` form or the one-byte priority form, and `compatibility_priority` plus `performance_robustness` hold the two rating fields the ASL macro arguments populate. For the example template, the first marker arrives with `compatibility_priority ==` [`ACPI_GOOD_CONFIGURATION`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L95), the second with [`ACPI_ACCEPTABLE_CONFIGURATION`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L96), and the third with [`ACPI_SUB_OPTIMAL_CONFIGURATION`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L97).

### pnpacpi_add_device gates option parsing on _SRS presence

The PNP ACPI protocol registers a [`struct pnp_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pnp.h#L243) for every namespace node with a PNP-style ID, and the `_PRS` parse runs only for devices that can also be reprogrammed, which the code expresses through the [`PNP_CONFIGURABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pnp.h#L305) capability derived from `_SRS` presence:

```c
/* drivers/pnp/pnpacpi/core.c:209 */
static int __init pnpacpi_add_device(struct acpi_device *device)
{
	struct pnp_dev *dev;
	const char *pnpid;
	struct acpi_hardware_id *id;
	int error;

	/* Skip devices that are already bound */
	if (device->physical_node_count)
		return 0;

	/*
	 * If a PnPacpi device is not present , the device
	 * driver should not be loaded.
	 */
	if (!acpi_has_method(device->handle, "_CRS"))
		return 0;

	pnpid = pnpacpi_get_id(device);
	if (!pnpid)
		return 0;

	if (!device->status.present)
		return 0;

	dev = pnp_alloc_dev(&pnpacpi_protocol, num, pnpid);
	if (!dev)
		return -ENOMEM;

	ACPI_COMPANION_SET(&dev->dev, device);
	dev->data = device;
	/* .enabled means the device can decode the resources */
	dev->active = device->status.enabled;
	if (acpi_has_method(device->handle, "_SRS"))
		dev->capabilities |= PNP_CONFIGURABLE;
	dev->capabilities |= PNP_READ;
	if (device->flags.dynamic_status && (dev->capabilities & PNP_CONFIGURABLE))
		dev->capabilities |= PNP_WRITE;
	if (device->flags.removable)
		dev->capabilities |= PNP_REMOVABLE;
	if (acpi_has_method(device->handle, "_DIS"))
		dev->capabilities |= PNP_DISABLE;

	if (strlen(acpi_device_name(device)))
		strscpy(dev->name, acpi_device_name(device), sizeof(dev->name));
	else
		strscpy(dev->name, acpi_device_bid(device), sizeof(dev->name));

	if (dev->active)
		pnpacpi_parse_allocated_resource(dev);

	if (dev->capabilities & PNP_CONFIGURABLE)
		pnpacpi_parse_resource_option_data(dev);
	...
	error = pnp_add_device(dev);
	...
}
```

The pairing with `_CRS` is visible in the same function. An active device first fills its current resource table from `_CRS` through [`pnpacpi_parse_allocated_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L271), and a configurable device then loads its option menu from `_PRS`:

```c
/* drivers/pnp/pnpacpi/rsparser.c:271 */
int pnpacpi_parse_allocated_resource(struct pnp_dev *dev)
{
	struct acpi_device *acpi_dev = dev->data;
	acpi_handle handle = acpi_dev->handle;
	acpi_status status;

	pnp_dbg(&dev->dev, "parse allocated resources\n");

	pnp_init_resources(dev);

	status = acpi_walk_resources(handle, METHOD_NAME__CRS,
				     pnpacpi_allocated_resource, dev);

	if (ACPI_FAILURE(status)) {
		if (status != AE_NOT_FOUND)
			dev_err(&dev->dev, "can't evaluate _CRS: %d", status);
		return -EPERM;
	}
	return 0;
}
```

The relevant [`struct pnp_dev`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pnp.h#L243) fields are the option list every parser appends to and the running count of dependent sets:

```c
/* include/linux/pnp.h:243 */
struct pnp_dev {
	struct device dev;		/* Driver Model device interface */
	u64 dma_mask;
	unsigned int number;		/* used as an index, must be unique */
	int status;
	...
	int active;
	int capabilities;
	unsigned int num_dependent_sets;
	struct list_head resources;
	struct list_head options;

	char name[PNP_NAME_LEN];	/* contains a human-readable name */
	int flags;			/* used by protocols */
	struct proc_dir_entry *procent;	/* device entry in /proc/bus/isapnp */
	void *data;
};
```

### pnpacpi_parse_resource_option_data walks _PRS into option sets

[`pnpacpi_parse_resource_option_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L550) seeds the walk context with `option_flags = 0`, meaning records encountered before any StartDependentFn register as independent options, and hands the per-record work to the callback:

```c
/* drivers/pnp/pnpacpi/rsparser.c:449 */
struct acpipnp_parse_option_s {
	struct pnp_dev *dev;
	unsigned int option_flags;
};
```

```c
/* drivers/pnp/pnpacpi/rsparser.c:550 */
int __init pnpacpi_parse_resource_option_data(struct pnp_dev *dev)
{
	struct acpi_device *acpi_dev = dev->data;
	acpi_handle handle = acpi_dev->handle;
	acpi_status status;
	struct acpipnp_parse_option_s parse_data;

	pnp_dbg(&dev->dev, "parse resource options\n");

	parse_data.dev = dev;
	parse_data.option_flags = 0;

	status = acpi_walk_resources(handle, METHOD_NAME__PRS,
				     pnpacpi_option_resource, &parse_data);

	if (ACPI_FAILURE(status)) {
		if (status != AE_NOT_FOUND)
			dev_err(&dev->dev, "can't evaluate _PRS: %d", status);
		return -EPERM;
	}
	return 0;
}
```

[`pnpacpi_option_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L454) is the dispatch over every decoded record. The two group-marker cases mutate the context's `option_flags` while the descriptor cases pass the current flags into a per-type parser, so set membership is purely positional, exactly matching the spec's stream semantics:

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

The [`ACPI_RESOURCE_TYPE_START_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L611) case is the priority mapping the page's figure annotates. [`ACPI_GOOD_CONFIGURATION`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L95) becomes [`PNP_RES_PRIORITY_PREFERRED`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L60), [`ACPI_ACCEPTABLE_CONFIGURATION`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L96) becomes [`PNP_RES_PRIORITY_ACCEPTABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L61), [`ACPI_SUB_OPTIMAL_CONFIGURATION`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L97) becomes [`PNP_RES_PRIORITY_FUNCTIONAL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L62), and anything else becomes [`PNP_RES_PRIORITY_INVALID`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L63). The mapping reads `performance_robustness` from [`struct acpi_resource_start_dependent`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L162) nowhere in the kernel; only the compatibility field steers the PNP priority. The [`ACPI_RESOURCE_TYPE_END_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L612) case resets `option_flags` to 0, returning subsequent records to independent registration.

### Dependent-set flags encode set number and priority

[`pnp_new_dependent_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L107) packs the dependent marker, the set index, and the priority into one `unsigned int` that every option of the group will carry, and bumps the device's set counter that the assignment loop later iterates:

```c
/* drivers/pnp/base.h:54 */
#define PNP_OPTION_DEPENDENT		0x80000000
#define PNP_OPTION_SET_MASK		0xffff
#define PNP_OPTION_SET_SHIFT		12
#define PNP_OPTION_PRIORITY_MASK	0xfff
#define PNP_OPTION_PRIORITY_SHIFT	0

#define PNP_RES_PRIORITY_PREFERRED	0
#define PNP_RES_PRIORITY_ACCEPTABLE	1
#define PNP_RES_PRIORITY_FUNCTIONAL	2
#define PNP_RES_PRIORITY_INVALID	PNP_OPTION_PRIORITY_MASK
```

```c
/* drivers/pnp/base.h:107 */
static inline unsigned int pnp_new_dependent_set(struct pnp_dev *dev,
						 int priority)
{
	unsigned int flags;

	if (priority > PNP_RES_PRIORITY_FUNCTIONAL) {
		dev_warn(&dev->dev, "invalid dependent option priority %d "
			 "clipped to %d", priority,
			 PNP_RES_PRIORITY_INVALID);
		priority = PNP_RES_PRIORITY_INVALID;
	}

	flags = PNP_OPTION_DEPENDENT |
	    ((dev->num_dependent_sets & PNP_OPTION_SET_MASK) <<
		PNP_OPTION_SET_SHIFT) |
	    ((priority & PNP_OPTION_PRIORITY_MASK) <<
		PNP_OPTION_PRIORITY_SHIFT);

	dev->num_dependent_sets++;

	return flags;
}
```

The decoding helpers recover the three pieces wherever options are consumed, and the option record itself is a flags word, a resource class, and a payload union:

```c
/* drivers/pnp/base.h:91 */
static inline int pnp_option_is_dependent(struct pnp_option *option)
{
	return option->flags & PNP_OPTION_DEPENDENT ? 1 : 0;
}

static inline unsigned int pnp_option_set(struct pnp_option *option)
{
	return (option->flags >> PNP_OPTION_SET_SHIFT) & PNP_OPTION_SET_MASK;
}

static inline unsigned int pnp_option_priority(struct pnp_option *option)
{
	return (option->flags >> PNP_OPTION_PRIORITY_SHIFT) &
	    PNP_OPTION_PRIORITY_MASK;
}
```

```c
/* drivers/pnp/base.h:65 */
struct pnp_option {
	struct list_head list;
	unsigned int flags;	/* independent/dependent, set, priority */

	unsigned long type;	/* IORESOURCE_{IO,MEM,IRQ,DMA} */
	union {
		struct pnp_port port;
		struct pnp_irq irq;
		struct pnp_dma dma;
		struct pnp_mem mem;
	} u;
};
```

[`pnp_build_option()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/resource.c#L36) is the single allocation point all four `pnp_register_*_resource()` helpers call, stamping the flags and class and appending to the device's options list in stream order, which preserves the per-set grouping for every later traversal:

```c
/* drivers/pnp/resource.c:36 */
static struct pnp_option *pnp_build_option(struct pnp_dev *dev, unsigned long type,
				    unsigned int option_flags)
{
	struct pnp_option *option;

	option = kzalloc_obj(struct pnp_option);
	if (!option)
		return NULL;

	option->flags = option_flags;
	option->type = type;

	list_add_tail(&option->list, &dev->options);
	return option;
}
```

### Representative descriptor parsers: IRQ and IO options

[`pnpacpi_parse_irq_option()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L306) converts one legacy IRQ descriptor into a bitmap of acceptable lines, reusing the shared [`acpi_dev_irq_flags()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L342) mapping for the trigger and wake attributes; for the example's third group, `{1, 3, 4, 5, 6, 7, 8, 10, 11, 12}` becomes map bits 0x1DFA:

```c
/* drivers/pnp/pnpacpi/rsparser.c:306 */
static __init void pnpacpi_parse_irq_option(struct pnp_dev *dev,
					    unsigned int option_flags,
					    struct acpi_resource_irq *p)
{
	int i;
	pnp_irq_mask_t map;
	unsigned char flags;

	bitmap_zero(map.bits, PNP_IRQ_NR);
	for (i = 0; i < p->interrupt_count; i++)
		if (p->interrupts[i])
			__set_bit(p->interrupts[i], map.bits);

	flags = acpi_dev_irq_flags(p->triggering, p->polarity, p->shareable, p->wake_capable);
	pnp_register_irq_resource(dev, option_flags, &map, flags);
}
```

[`pnp_register_irq_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/resource.c#L52) stores the bitmap into the option's [`struct pnp_irq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L36) payload and, with PCI enabled, penalizes the listed ISA IRQs so the PCI IRQ router avoids lines a PNP device wants:

```c
/* drivers/pnp/resource.c:52 */
int pnp_register_irq_resource(struct pnp_dev *dev, unsigned int option_flags,
			      pnp_irq_mask_t *map, unsigned char flags)
{
	struct pnp_option *option;
	struct pnp_irq *irq;

	option = pnp_build_option(dev, IORESOURCE_IRQ, option_flags);
	if (!option)
		return -ENOMEM;

	irq = &option->u.irq;
	irq->map = *map;
	irq->flags = flags;

#ifdef CONFIG_PCI
	{
		int i;

		for (i = 0; i < 16; i++)
			if (test_bit(i, irq->map.bits))
				pcibios_penalize_isa_irq(i, 0);
	}
#endif

	dbg_pnp_show_option(dev, option);
	return 0;
}
```

[`pnpacpi_parse_port_option()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L347) is the IO-descriptor counterpart, carrying the [`struct acpi_resource_io`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L173) min/max/alignment/length quadruple into a [`struct pnp_port`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L25) range rule, with the descriptor's decode width recorded as [`IORESOURCE_IO_16BIT_ADDR`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ioport.h#L116):

```c
/* drivers/pnp/pnpacpi/rsparser.c:347 */
static __init void pnpacpi_parse_port_option(struct pnp_dev *dev,
					     unsigned int option_flags,
					     struct acpi_resource_io *io)
{
	unsigned char flags = 0;

	if (io->io_decode == ACPI_DECODE_16)
		flags = IORESOURCE_IO_16BIT_ADDR;
	pnp_register_port_resource(dev, option_flags, io->minimum, io->maximum,
				   io->alignment, io->address_length, flags);
}
```

The sibling parsers follow the same one-descriptor-one-option shape, with [`pnpacpi_parse_ext_irq_option()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L323) bounds-checking GSI numbers against the [`PNP_IRQ_NR`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L33) bitmap width, [`pnpacpi_parse_dma_option()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L292) folding [`struct acpi_resource_dma`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L151) channels into the 8-bit mask of [`pnp_register_dma_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/resource.c#L80), [`pnpacpi_parse_mem32_option()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L379) carrying [`struct acpi_resource_memory32`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L227) ranges into [`pnp_register_mem_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/resource.c#L121), and [`pnpacpi_parse_address_option()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L403) normalizing address-space descriptors through [`acpi_resource_to_address64()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L332) before registering a fixed port or memory rule. The DMA and Memory32 bodies show how compact the shape stays across descriptor kinds:

```c
/* drivers/pnp/pnpacpi/rsparser.c:292 */
static __init void pnpacpi_parse_dma_option(struct pnp_dev *dev,
					    unsigned int option_flags,
					    struct acpi_resource_dma *p)
{
	int i;
	unsigned char map = 0, flags;

	for (i = 0; i < p->channel_count; i++)
		map |= 1 << p->channels[i];

	flags = dma_flags(dev, p->type, p->bus_master, p->transfer);
	pnp_register_dma_resource(dev, option_flags, map, flags);
}
```

```c
/* drivers/pnp/pnpacpi/rsparser.c:379 */
static __init void pnpacpi_parse_mem32_option(struct pnp_dev *dev,
					      unsigned int option_flags,
					      struct acpi_resource_memory32 *p)
{
	unsigned char flags = 0;

	if (p->write_protect == ACPI_READ_WRITE_MEMORY)
		flags = IORESOURCE_MEM_WRITEABLE;
	pnp_register_mem_resource(dev, option_flags, p->minimum, p->maximum,
				  p->alignment, p->address_length, flags);
}
```

### Options drive automatic assignment toward _SRS

The options sit unused until something activates the device. PNP drivers call [`pnp_activate_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L383) from their probe paths, and the `resources` sysfs attribute's store handler [`resources_store()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/interface.c#L336) reaches [`pnp_auto_config_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L308) directly when userspace writes `auto`:

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

[`pnp_auto_config_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L308) iterates the dependent sets that [`pnp_new_dependent_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L107) counted, trying set 0 first; because [`pnpacpi_option_resource()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L454) numbered the sets in stream order, set 0 is the first group in `_PRS`, which section 6.2.12 semantics make the firmware's most preferred alternative:

```c
/* drivers/pnp/manager.c:308 */
int pnp_auto_config_dev(struct pnp_dev *dev)
{
	int i, ret;

	if (!pnp_can_configure(dev)) {
		pnp_dbg(&dev->dev, "configuration not supported\n");
		return -ENODEV;
	}

	ret = pnp_assign_resources(dev, 0);
	if (ret == 0)
		return 0;

	for (i = 1; i < dev->num_dependent_sets; i++) {
		ret = pnp_assign_resources(dev, i);
		if (ret == 0)
			return 0;
	}

	dev_err(&dev->dev, "unable to assign resources\n");
	return ret;
}
```

[`pnp_assign_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L256) walks the options list once per attempt, processing every independent option plus exactly the dependent options whose set number matches, dispatching on the option's resource class:

```c
/* drivers/pnp/manager.c:256 */
static int pnp_assign_resources(struct pnp_dev *dev, int set)
{
	struct pnp_option *option;
	int nport = 0, nmem = 0, nirq = 0;
	int ndma __maybe_unused = 0;
	int ret = 0;

	pnp_dbg(&dev->dev, "pnp_assign_resources, try dependent set %d\n", set);
	mutex_lock(&pnp_res_mutex);
	pnp_clean_resource_table(dev);

	list_for_each_entry(option, &dev->options, list) {
		if (pnp_option_is_dependent(option) &&
		    pnp_option_set(option) != set)
				continue;

		switch (option->type) {
		case IORESOURCE_IO:
			ret = pnp_assign_port(dev, &option->u.port, nport++);
			break;
		case IORESOURCE_MEM:
			ret = pnp_assign_mem(dev, &option->u.mem, nmem++);
			break;
		case IORESOURCE_IRQ:
			ret = pnp_assign_irq(dev, &option->u.irq, nirq++);
			break;
#ifdef CONFIG_ISA_DMA_API
		case IORESOURCE_DMA:
			ret = pnp_assign_dma(dev, &option->u.dma, ndma++);
			break;
#endif
		default:
			ret = -EINVAL;
			break;
		}
		if (ret < 0)
			break;
	}

	mutex_unlock(&pnp_res_mutex);
	if (ret < 0) {
		pnp_dbg(&dev->dev, "pnp_assign_resources failed (%d)\n", ret);
		pnp_clean_resource_table(dev);
	} else
		dbg_pnp_show_resources(dev, "pnp_assign_resources succeeded");
	return ret;
}
```

[`pnp_assign_irq()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L132) shows one option payload being consumed. It searches the [`struct pnp_irq`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/base.h#L36) bitmap for a usable line, preferring lines 16 and up and falling back to a hardcoded preference order over the ISA range, validating each candidate against current allocations:

```c
/* drivers/pnp/manager.c:132 */
static int pnp_assign_irq(struct pnp_dev *dev, struct pnp_irq *rule, int idx)
{
	struct resource *res, local_res;
	int i;

	/* IRQ priority: this table is good for i386 */
	static unsigned short xtab[16] = {
		5, 10, 11, 12, 9, 14, 15, 7, 3, 4, 13, 0, 1, 6, 8, 2
	};

	res = pnp_find_resource(dev, rule->flags, IORESOURCE_IRQ, idx);
	if (res) {
		pnp_dbg(&dev->dev, "  irq %d already set to %d flags %#lx\n",
			idx, (int) res->start, res->flags);
		return 0;
	}

	res = &local_res;
	res->flags = rule->flags | IORESOURCE_AUTO;
	res->start = -1;
	res->end = -1;

	if (bitmap_empty(rule->map.bits, PNP_IRQ_NR)) {
		res->flags |= IORESOURCE_DISABLED;
		pnp_dbg(&dev->dev, "  irq %d disabled\n", idx);
		goto __add;
	}

	/* TBD: need check for >16 IRQ */
	res->start = find_next_bit(rule->map.bits, PNP_IRQ_NR, 16);
	if (res->start < PNP_IRQ_NR) {
		res->end = res->start;
		goto __add;
	}
	for (i = 0; i < 16; i++) {
		if (test_bit(xtab[i], rule->map.bits)) {
			res->start = res->end = xtab[i];
			if (pnp_check_irq(dev, res))
				goto __add;
		}
	}
	...
__add:
	pnp_add_irq_resource(dev, res->start, res->flags);
	return 0;
}
```

A successful assignment is then programmed into the hardware. [`pnp_start_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/manager.c#L337) calls the protocol's set hook, which the ACPI protocol binds to [`pnpacpi_set_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L49), and that function encodes the assigned resource table back into a descriptor template and evaluates `_SRS` through [`acpi_set_current_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/rsxface.c#L248):

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

The hooks are bound in the protocol object that [`pnpacpi_add_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/core.c#L209) passed to [`pnp_alloc_dev()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/core.c#L119), completing the `_CRS`/`_PRS`/`_SRS` triangle:

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
```

### The options sysfs attribute prints the parsed sets

The parsed `_PRS` content is user visible. [`options_show()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/interface.c#L208) renders the options list grouped by dependent set, printing a `Dependent: NN - Priority <name>` header whenever the set number changes and indenting the member options beneath it:

```c
/* drivers/pnp/interface.c:208 */
static ssize_t options_show(struct device *dmdev, struct device_attribute *attr,
			    char *buf)
{
	struct pnp_dev *dev = to_pnp_dev(dmdev);
	pnp_info_buffer_t *buffer;
	struct pnp_option *option;
	int ret, dep = 0, set = 0;
	char *indent;

	buffer = kzalloc_obj(*buffer);
	if (!buffer)
		return -ENOMEM;

	buffer->len = PAGE_SIZE;
	buffer->buffer = buf;
	buffer->curr = buffer->buffer;

	list_for_each_entry(option, &dev->options, list) {
		if (pnp_option_is_dependent(option)) {
			indent = "  ";
			if (!dep || pnp_option_set(option) != set) {
				set = pnp_option_set(option);
				dep = 1;
				pnp_printf(buffer, "Dependent: %02i - "
					   "Priority %s\n", set,
					   pnp_option_priority_name(option));
			}
		} else {
			dep = 0;
			indent = "";
		}
		pnp_print_option(buffer, indent, option);
	}

	ret = (buffer->curr - buf);
	kfree(buffer);
	return ret;
}
static DEVICE_ATTR_RO(options);
```

[`pnp_option_priority_name()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/support.c#L92) translates the encoded priority back into the words shown in sysfs, closing the loop from the `StartDependentFn` priority byte to user-visible text:

```c
/* drivers/pnp/support.c:92 */
char *pnp_option_priority_name(struct pnp_option *option)
{
	switch (pnp_option_priority(option)) {
	case PNP_RES_PRIORITY_PREFERRED:
		return "preferred";
	case PNP_RES_PRIORITY_ACCEPTABLE:
		return "acceptable";
	case PNP_RES_PRIORITY_FUNCTIONAL:
		return "functional";
	}
	return "invalid";
}
```

The attribute is registered on every PNP device through the bus-level attribute group, so the example device surfaces its three sets at `/sys/bus/pnp/devices/.../options` with the first group printed under `Dependent: 00 - Priority preferred`:

```c
/* drivers/pnp/interface.c:456 */
static struct attribute *pnp_dev_attrs[] = {
	&dev_attr_resources.attr,
	&dev_attr_options.attr,
	&dev_attr_id.attr,
	NULL,
};

static const struct attribute_group pnp_dev_group = {
	.attrs = pnp_dev_attrs,
};

const struct attribute_group *pnp_dev_groups[] = {
	&pnp_dev_group,
	NULL,
};
```

### The interrupt link driver reads _PRS for candidate IRQs

The second vendor-neutral `_PRS` consumer is the ACPI interrupt link driver, which manages `PNP0C0F` link devices whose `_PRS` lists the IRQs the link can be routed to. [`acpi_pci_link_get_possible()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L155) runs at link enumeration from [`acpi_pci_link_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L715):

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
/* drivers/acpi/pci_link.c:732 */
	mutex_lock(&acpi_link_lock);
	result = acpi_pci_link_get_possible(link);
	if (result)
		goto end;
```

The callback treats the dependent markers as transparent, accepting [`ACPI_RESOURCE_TYPE_START_DEPENDENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acrestyp.h#L611) records with a plain [`AE_OK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L60) and harvesting the first IRQ-bearing descriptor it sees, since a link's `_PRS` wraps a single IRQ or extended IRQ descriptor in one dependent group and the interesting data is the interrupt list itself:

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

The harvested candidates land in the link state, where `possible[]` and `possible_count` later limit the IRQs eligible for the link's `_SRS` programming:

```c
/* drivers/acpi/pci_link.c:55 */
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

### The platform-device path reads _CRS alone

Modern ACPI-enumerated platform devices ignore `_PRS`. [`acpi_create_platform_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpi_platform.c#L110) gathers its resources exclusively through [`acpi_dev_get_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1000), and that helper hardwires [`METHOD_NAME__CRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L21) into the shared walk core:

```c
/* drivers/acpi/acpi_platform.c:138 */
	if (adev->device_type == ACPI_BUS_TYPE_DEVICE) {
		LIST_HEAD(resource_list);

		count = acpi_dev_get_resources(adev, &resource_list, NULL, NULL);
		if (count < 0)
			return ERR_PTR(-ENODATA);
```

```c
/* drivers/acpi/resource.c:1000 */
int acpi_dev_get_resources(struct acpi_device *adev, struct list_head *list,
			   int (*preproc)(struct acpi_resource *, void *),
			   void *preproc_data)
{
	return __acpi_dev_get_resources(adev, list, preproc, preproc_data,
					METHOD_NAME__CRS);
}
```

The two method-name instantiations of [`__acpi_dev_get_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L947) in the tree are [`METHOD_NAME__CRS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L21) here and [`METHOD_NAME__DMA`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h#L24) in [`acpi_dev_get_dma_resources()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/resource.c#L1040), so the platform-device path reads `_CRS` alone, and within the ACPI core and the PNP subsystem the `_PRS` walks are exactly the two shown above, [`pnpacpi_parse_resource_option_data()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pnp/pnpacpi/rsparser.c#L550) and [`acpi_pci_link_get_possible()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/pci_link.c#L155). A firmware author who wants a device handled by the platform bus therefore describes its final configuration directly in `_CRS`, and the `_PRS`/`_SRS` pair stays a PNP-protocol mechanism for the legacy-style reconfigurable devices that ship both methods.
