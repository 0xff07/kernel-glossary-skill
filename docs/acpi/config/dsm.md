# _DSM

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

`_DSM` is the Device Specific Method, a single control method that multiplexes any number of UUID-scoped functions behind one namespace object so vendors and standards bodies can add device functionality without colliding over reserved names. Its ABI is fixed by section 9.1.1 of the spec, four arguments (a 16-byte Buffer UUID, an Integer revision, an Integer function index, and a Package of function-specific arguments) plus the convention that function index 0 is a query returning a Buffer bitmask of supported functions. The kernel represents the UUID as a [`guid_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uuid.h#L15) built with [`GUID_INIT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uuid.h#L23) or parsed by [`guid_parse()`](https://elixir.bootlin.com/linux/v7.0/source/lib/uuid.c#L124), and it evaluates the method through three helpers in [`drivers/acpi/utils.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c), [`acpi_evaluate_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L771) which packs the four [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) slots and calls [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163), [`acpi_evaluate_dsm_typed()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L64) which adds a return-type check, and [`acpi_check_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L821) which runs the function-0 query and folds the returned mask. The vendor-neutral consumers documented here are the PCI firmware `_DSM` under [`pci_acpi_dsm_guid`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L30) in [`drivers/pci/pci-acpi.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c) and [`drivers/pci/pci-label.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-label.c), the USB3 port U1/U2 disable query in [`usb_acpi_port_lpm_incapable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/usb-acpi.c#L59), and the TPM Physical Presence Interface in [`drivers/char/tpm/tpm_ppi.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/char/tpm/tpm_ppi.c), which shows the Arg3 Package being filled through [`ACPI_INIT_DSM_ARGV4`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L80).

```
    _DSM argument strip, the four slots acpi_evaluate_dsm() packs
    ──────────────────────────────────────────────────────────────

    Arg0              Arg1              Arg2              Arg3
    ┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐
    │ ACPI_TYPE_      │ ACPI_TYPE_      │ ACPI_TYPE_      │ ACPI_TYPE_      │
    │  BUFFER         │  INTEGER        │  INTEGER        │  PACKAGE        │
    │ 16-byte UUID    │ revision ID     │ function index  │ function args   │
    │ (guid_t bytes)  │ (rev parameter) │ (func parameter)│ (argv4, or an   │
    │                 │                 │                 │  empty package) │
    └─────────────────┴─────────────────┴─────────────────┴─────────────────┘
      params[0]         params[1]         params[2]         params[3]

    Function-0 return bitmask as acpi_check_dsm() folds it
    ───────────────────────────────────────────────────────

    bit:     63 ...   9   8   7   6   5   4   3   2   1   0
            ┌───────┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
            │  ...  │f9 │f8 │f7 │f6 │f5 │f4 │f3 │f2 │f1 │ G │
            └───────┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘

    G    = gate bit, set when any function beyond 0 exists for this
           UUID + revision; acpi_check_dsm() tests it as (mask & 0x1)
    f(n) = function index n supported; the caller's funcs argument
           must be a subset of the mask ((mask & funcs) == funcs)

    For pci_acpi_dsm_guid the defined indexes are
      f5 = DSM_PCI_PRESERVE_BOOT_CONFIG
      f7 = DSM_PCI_DEVICE_NAME
      f8 = DSM_PCI_POWER_ON_RESET_DELAY
      f9 = DSM_PCI_DEVICE_READINESS_DURATIONS
```

## SUMMARY

Section 9.1.1 places `_DSM` under "Device Object Name Collision" because the method exists to give device vendors an expansion point with zero reserved-name footprint. A caller supplies Arg0 as a 16-byte Buffer holding the UUID that scopes the interface, Arg1 as an Integer revision of that interface, Arg2 as an Integer function index, and Arg3 as a Package of function-specific arguments, and the return type for nonzero indexes is whatever the UUID's owner defined. Function index 0 is reserved as the query. It returns a Buffer in which bit n set means function index n is callable for the given UUID and revision, and bit 0 reports whether any function beyond the query itself exists, so a `_DSM` that recognizes neither the UUID nor the revision answers with a buffer of one zero byte. The kernel addresses the method by its literal name; the `"_DSM"` string is written once, inside [`acpi_evaluate_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L771), and [`include/acpi/acnames.h`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acnames.h) carries the resource-method names while a `METHOD_NAME__DSM` entry is absent from it.

The helper layer is small and uniform. [`acpi_evaluate_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L771) fills a four-element [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) array (Buffer pointing at the caller's [`guid_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uuid.h#L15), two Integers, and either the caller's `argv4` or an empty Package), wraps it in a [`struct acpi_object_list`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L956), evaluates through [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) into an [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973) output, and returns the heap-allocated result object that the caller must release with [`ACPI_FREE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L350). Failures other than [`AE_NOT_FOUND`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L75) log a warning through [`acpi_handle_warn()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1262) that includes the UUID, revision, function, and status. [`acpi_evaluate_dsm_typed()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L64) frees and drops a result whose `type` differs from the expected one, which matters because, according to the kerneldoc, "Though ACPI defines the fourth parameter for _DSM should be a package, some old BIOSes do expect a buffer or an integer etc." and return types vary just as widely. [`acpi_check_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L821) evaluates function 0, accepts both the spec Buffer form and a legacy Integer form of the mask, and approves only when the gate bit and every requested bit in its `funcs` argument are set.

The consumers on this page cover the three calling patterns. The PCI core defines [`pci_acpi_dsm_guid`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L30) (e5c937d0-3553-4d7a-9117-ea4d19c3434d from the PCI Firmware Specification) and the function indexes [`DSM_PCI_PRESERVE_BOOT_CONFIG`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci-acpi.h#L121), [`DSM_PCI_DEVICE_NAME`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci-acpi.h#L122), [`DSM_PCI_POWER_ON_RESET_DELAY`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci-acpi.h#L123), and [`DSM_PCI_DEVICE_READINESS_DURATIONS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci-acpi.h#L124); [`pci_acpi_preserve_config()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L124) and [`acpi_pci_add_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1215) consume Integer returns, [`pci_acpi_optimize_delay()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1384) parses a five-element Package, and [`dsm_get_label()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-label.c#L155) shows the raw [`acpi_evaluate_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L771) call with hand-rolled type checking. The USB core's [`usb_acpi_port_lpm_incapable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/usb-acpi.c#L59) chains [`guid_parse()`](https://elixir.bootlin.com/linux/v7.0/source/lib/uuid.c#L124), [`acpi_check_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L821), and [`acpi_evaluate_dsm_typed()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L64) in one function, and the TPM PPI code demonstrates a populated Arg3 via [`ACPI_INIT_DSM_ARGV4`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L80) in [`tpm_store_ppi_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/char/tpm/tpm_ppi.c#L124).

## SPECIFICATIONS

- ACPI Specification, section 9.1: Device Object Name Collision
- ACPI Specification, section 9.1.1: _DSM (Device Specific Method)
- ACPI Specification, section 19.6: ASL Operator Reference (ToUUID compiles the Arg0 Buffer)

## LINUX KERNEL

### Evaluation helpers

- [`'\<acpi_evaluate_dsm\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L771): packs the four-argument ABI and returns the caller-owned result object
- [`'\<acpi_evaluate_dsm_typed\>':'include/acpi/acpi_bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L64): inline wrapper that frees and drops results of the wrong type
- [`'\<acpi_check_dsm\>':'drivers/acpi/utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L821): function-0 query, folds the Buffer or Integer mask and tests the requested bits
- [`ACPI_INIT_DSM_ARGV4`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L80): initializer building the Arg3 Package from a caller-side element array
- [`'\<acpi_evaluate_object\>':'drivers/acpi/acpica/nsxfeval.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163): the ACPICA evaluator underneath the helper
- [`acpi_handle_warn`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1262): path-prefixed warning emitted on evaluation failure
- [`ACPI_FREE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L350): release for the returned object (maps to [`acpi_os_free()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/platform/aclinuxex.h#L62))
- [`AE_NOT_FOUND`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L75): the one status the helper passes through silently (device without `_DSM`)

### GUID plumbing

- [`'\<guid_t\>':'include/linux/uuid.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uuid.h#L15): 16-byte wire-format GUID the helpers take by pointer
- [`GUID_INIT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uuid.h#L23): compile-time initializer producing the mixed-endian byte layout Arg0 needs
- [`'\<guid_parse\>':'lib/uuid.c'`](https://elixir.bootlin.com/linux/v7.0/source/lib/uuid.c#L124): runtime conversion from the canonical string form

### Marshalling types

- [`'\<union acpi_object\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908): tagged external object used for all four arguments and the return value
- [`'\<struct acpi_object_list\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L956): count/pointer pair carrying the argument array into the evaluator
- [`'\<struct acpi_buffer\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L978): output carrier holding the returned object
- [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973): length sentinel asking ACPICA to allocate the output block
- [`'\<acpi_handle\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424): opaque namespace-node cookie identifying the device, obtained via [`ACPI_HANDLE()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L61)

### PCI firmware _DSM consumers

- [`'\<pci_acpi_dsm_guid\>':'drivers/pci/pci-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L30): the PCI Firmware Specification `_DSM` UUID e5c937d0-3553-4d7a-9117-ea4d19c3434d
- [`DSM_PCI_PRESERVE_BOOT_CONFIG`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci-acpi.h#L121): function 5, "PCI Boot Configuration"
- [`DSM_PCI_DEVICE_NAME`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci-acpi.h#L122): function 7, firmware-assigned device name and index
- [`DSM_PCI_POWER_ON_RESET_DELAY`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci-acpi.h#L123): function 8, "Reset Delay" for the hierarchy below a host bridge
- [`DSM_PCI_DEVICE_READINESS_DURATIONS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci-acpi.h#L124): function 9, per-device readiness durations
- [`'\<pci_acpi_preserve_config\>':'drivers/pci/pci-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L124): Integer-typed call deciding whether firmware resource assignments stay
- [`'\<acpi_pci_add_bus\>':'drivers/pci/pci-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1215): root-bus hook evaluating the Reset Delay function
- [`'\<pci_acpi_optimize_delay\>':'drivers/pci/pci-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1384): Package-typed call trimming D3 delays per device
- [`'\<pci_acpi_setup\>':'drivers/pci/pci-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1433): companion-setup path that invokes the delay optimization
- [`'\<device_has_acpi_name\>':'drivers/pci/pci-label.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-label.c#L36): [`acpi_check_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L821) gate for the label sysfs attributes
- [`'\<dsm_get_label\>':'drivers/pci/pci-label.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-label.c#L155): raw [`acpi_evaluate_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L771) caller parsing a two-element Package

### USB port consumer

- [`'\<usb_acpi_port_lpm_incapable\>':'drivers/usb/core/usb-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/usb-acpi.c#L59): parse-check-evaluate chain for the USB controller `_DSM`
- [`'\<usb_get_hub_port_acpi_handle\>':'drivers/usb/core/hub.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L6557): resolves the port's [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424) the query runs against
- [`'\<xhci_find_lpm_incapable_ports\>':'drivers/usb/host/xhci-pci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-pci.c#L532): roothub loop consuming the per-port result

### TPM PPI Arg3 example

- [`'\<tpm_ppi_guid\>':'drivers/char/tpm/tpm_ppi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/char/tpm/tpm_ppi.c#L32): the TCG Physical Presence Interface GUID as a [`GUID_INIT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uuid.h#L23) constant
- [`'\<tpm_eval_dsm\>':'drivers/char/tpm/tpm_ppi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/char/tpm/tpm_ppi.c#L56): driver-local wrapper fixing the GUID and delegating to the typed helper
- [`'\<tpm_store_ppi_request\>':'drivers/char/tpm/tpm_ppi.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/char/tpm/tpm_ppi.c#L124): sysfs store handler packing one or two Integers into Arg3

## KERNEL DOCUMENTATION

- [`Documentation/arch/arm64/acpi_object_usage.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/arch/arm64/acpi_object_usage.rst): per-object table confirming `_DSM` as section 9.1.1 and warning that its return values are interface-defined rather than standardized
- [`Documentation/firmware-guide/acpi/osi.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/osi.rst): recommends a vendor `_DSM` as the supported way to give Linux OS-specific firmware hooks, replacing `_OSI("Linux")` strings
- [`Documentation/PCI/tph.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/PCI/tph.rst): documents a PCI Firmware Specification `_DSM` (TPH Steering Tag ECN) consumed by the PCI core
- [`Documentation/driver-api/acpi/linuxized-acpica.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/acpi/linuxized-acpica.rst): maintenance model of the imported ACPICA code providing the evaluator underneath the helpers

## OTHER SOURCES

- [ACPI Specification 6.5, chapter 9: ACPI-Defined Devices and Device-Specific Objects](https://uefi.org/specs/ACPI/6.5/09_ACPI_Defined_Devices_and_Device_Specific_Objects.html)
- [Commit a65ac52041cc ("ACPI: introduce helper interfaces for _DSM method")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=a65ac52041cccaf598995bc44340849027f1d79b)
- [Commit 94116f8126de ("ACPI: Switch to use generic guid_t in acpi_evaluate_dsm()")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=94116f8126de9762751fd92731581b73b56292e5)
- [Commit 06eb8dc097b3 ("ACPI: utils: include UUID in _DSM evaluation warning")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=06eb8dc097b3fcb2d02eb553b17af5fcc2952f96)
- [Commit 9fbdc0504244 ("ACPI: PCI: Switch to use acpi_evaluate_dsm_typed()")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=9fbdc0504244a3c958a0ef4f0ff7016072553f71)

## METHODS

### _DSM (device specific method, 4 arguments)

`_DSM` is a spec-defined name with no function definition in the kernel, and the kernel reaches it through a literal pathname; [`acpi_evaluate_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L771) passes the `"_DSM"` string to [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163). The argument ABI and the kernel packing line up slot for slot.

| Arg | ACPI type | Content per section 9.1.1 | Kernel packing in [`acpi_evaluate_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L771) |
|-----|-----------|---------------------------|------------------------------------------|
| Arg0 | Buffer | UUID identifying the interface, 16 bytes | `params[0].buffer.pointer = (u8 *)guid`, length 16 |
| Arg1 | Integer | Revision ID of the interface | `params[1].integer.value = rev` |
| Arg2 | Integer | Function index, 0 reserved for the query | `params[2].integer.value = func` |
| Arg3 | Package | Function-specific arguments, empty when unused | `params[3] = *argv4` or an empty `ACPI_TYPE_PACKAGE` |
| return | any | Defined by UUID + revision + index | [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) owned by the caller, freed with [`ACPI_FREE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L350) |

The spec requires new revisions of an interface to stay backward compatible with earlier ones, and it reserves the definition of new indexes, revisions, and argument layouts to the UUID's issuer, which is why the kernel helpers treat the (guid, rev, func) triple as one opaque key and leave all result interpretation to the caller. The adjacent `_OSC` object (section 6.2.11) also keys platform capability negotiation by UUID, and the kernel keeps an entirely separate code path for it, so everything on this page concerns `_DSM` alone.

### Function 0, the query

For every UUID and revision, Arg2 = 0 must return a Buffer bitmask in which bit n set means function index n is supported and bit 0 means at least one function besides the query exists for that UUID and revision. A `_DSM` that recognizes neither the UUID nor the revision returns a one-byte buffer holding 0x00, which clears every bit including the gate. [`acpi_check_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L821) is the kernel-side reader of this contract; it folds up to eight buffer bytes (or a legacy Integer return) into a `u64` mask and approves only when `(mask & 0x1) && (mask & funcs) == funcs`, so callers pass `funcs` as `BIT(n)` or `1 << n` of the indexes they intend to call, as [`device_has_acpi_name()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-label.c#L36) and [`usb_acpi_port_lpm_incapable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/usb-acpi.c#L59) do in DETAILS below.

## DETAILS

### The canonical ASL skeleton and what the kernel sees

The following `_DSM` skeleton follows the structure the spec's section 9.1.1 example uses, one UUID guarded by an outer comparison, a switch on the function index, a revision-dependent query answer, and the one-zero-byte buffer for unknown UUIDs:

```asl
Function (_DSM, {BuffObj}, {BuffObj, IntObj, IntObj, PkgObj})
{
    // Arg0=UUID, Arg1=Revision, Arg2=FunctionIndex, Arg3=Args
    If (LEqual (Arg0, ToUUID ("893f00a6-660c-494e-bcfd-3043f4fb67c0"))) {
        Switch (ToInteger (Arg2)) {
            Case (0) {                       // query
                Switch (ToInteger (Arg1)) {
                    Case (0) { Return (Buffer () {0x1F}) }  // rev0: fns 1-4
                    Case (1) { Return (Buffer () {0x3F}) }  // rev1: fns 1-5
                }
                Return (Buffer () {0xFF})
            }
            Case (1) { /* function 1 */ Return (Zero) }
        }
    }
    Return (Buffer () {0x00})   // unknown UUID: no functions
}
```

(`Function()` is iASL shorthand for a `Method` with declared argument and return types.) Each branch pairs with a specific kernel observation. A query against revision 0 produces mask 0x1F, so [`acpi_check_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L821) approves `funcs` values up to `BIT(4) | BIT(3) | BIT(2) | BIT(1)` because bit 0 (the gate) and all requested bits are set; the same call with `funcs = BIT(5)` fails until the caller raises Arg1 to revision 1, where the mask grows to 0x3F. The final `Return (Buffer () {0x00})` for a foreign UUID folds to mask 0, the gate test `mask & 0x1` fails, and [`acpi_check_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L821) reports false with no warning logged, since the evaluation itself succeeded. A device with no `_DSM` object at all surfaces differently, [`acpi_evaluate_object()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/nsxfeval.c#L163) returns [`AE_NOT_FOUND`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L75) and [`acpi_evaluate_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L771) returns NULL while suppressing the warning for exactly that status.

### guid_t carries the UUID in wire order

The 16 bytes of Arg0 are the UUID in its RFC 4122 wire layout with the first three fields stored little-endian, the GUID convention, and the kernel type for that layout is [`guid_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uuid.h#L15):

```c
/* include/linux/uuid.h:13 */
#define UUID_SIZE 16

typedef struct {
	__u8 b[UUID_SIZE];
} guid_t;
```

[`GUID_INIT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uuid.h#L23) performs the endianness shuffle at compile time, splitting the 32-bit and two 16-bit leading fields into little-endian bytes and appending the trailing eight bytes verbatim:

```c
/* include/linux/uuid.h:23 */
#define GUID_INIT(a, b, c, d0, d1, d2, d3, d4, d5, d6, d7)			\
((guid_t)								\
{{ (a) & 0xff, ((a) >> 8) & 0xff, ((a) >> 16) & 0xff, ((a) >> 24) & 0xff, \
   (b) & 0xff, ((b) >> 8) & 0xff,					\
   (c) & 0xff, ((c) >> 8) & 0xff,					\
   (d0), (d1), (d2), (d3), (d4), (d5), (d6), (d7) }})
```

The PCI core's GUID is the worked example, the canonical string e5c937d0-3553-4d7a-9117-ea4d19c3434d split into [`GUID_INIT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uuid.h#L23) arguments:

```c
/* drivers/pci/pci-acpi.c:25 */
/*
 * The GUID is defined in the PCI Firmware Specification available
 * here to PCI-SIG members:
 * https://members.pcisig.com/wg/PCI-SIG/document/15350
 */
const guid_t pci_acpi_dsm_guid =
	GUID_INIT(0xe5c937d0, 0x3553, 0x4d7a,
		  0x91, 0x17, 0xea, 0x4d, 0x19, 0xc3, 0x43, 0x4d);
```

[`guid_parse()`](https://elixir.bootlin.com/linux/v7.0/source/lib/uuid.c#L124) is the runtime equivalent for code that keeps the UUID as its canonical string. The shared [`__uuid_parse()`](https://elixir.bootlin.com/linux/v7.0/source/lib/uuid.c#L106) walks the fixed hex-digit positions of the string and an endianness index table maps each parsed byte to its position in the 16-byte array, [`guid_index`](https://elixir.bootlin.com/linux/v7.0/source/lib/uuid.c#L24) encoding the same first-three-fields-swapped layout [`GUID_INIT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uuid.h#L23) produces:

```c
/* lib/uuid.c:106 */
static int __uuid_parse(const char *uuid, __u8 b[16], const u8 ei[16])
{
	static const u8 si[16] = {0,2,4,6,9,11,14,16,19,21,24,26,28,30,32,34};
	unsigned int i;

	if (!uuid_is_valid(uuid))
		return -EINVAL;

	for (i = 0; i < 16; i++) {
		int hi = hex_to_bin(uuid[si[i] + 0]);
		int lo = hex_to_bin(uuid[si[i] + 1]);

		b[ei[i]] = (hi << 4) | lo;
	}

	return 0;
}

int guid_parse(const char *uuid, guid_t *u)
{
	return __uuid_parse(uuid, u->b, guid_index);
}
EXPORT_SYMBOL(guid_parse);
```

The USB consumer in a later section calls [`guid_parse()`](https://elixir.bootlin.com/linux/v7.0/source/lib/uuid.c#L124) on every invocation, and the commit that introduced the typed parameter, 94116f8126de, converted [`acpi_evaluate_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L771) and every caller from a raw `u8 *` UUID buffer to `const guid_t *`.

### acpi_evaluate_dsm packs the four slots

[`acpi_evaluate_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L771) is the complete ABI in one function, reproduced here with its kerneldoc because the ownership and compatibility notes are part of the contract:

```c
/* drivers/acpi/utils.c:755 */
/**
 * acpi_evaluate_dsm - evaluate device's _DSM method
 * @handle: ACPI device handle
 * @guid: GUID of requested functions, should be 16 bytes
 * @rev: revision number of requested function
 * @func: requested function number
 * @argv4: the function specific parameter
 *
 * Evaluate device's _DSM method with specified GUID, revision id and
 * function number. Caller needs to free the returned object.
 *
 * Though ACPI defines the fourth parameter for _DSM should be a package,
 * some old BIOSes do expect a buffer or an integer etc.
 */
union acpi_object *
acpi_evaluate_dsm(acpi_handle handle, const guid_t *guid, u64 rev, u64 func,
		  union acpi_object *argv4)
{
	acpi_status ret;
	struct acpi_buffer buf = {ACPI_ALLOCATE_BUFFER, NULL};
	union acpi_object params[4];
	struct acpi_object_list input = {
		.count = 4,
		.pointer = params,
	};

	params[0].type = ACPI_TYPE_BUFFER;
	params[0].buffer.length = 16;
	params[0].buffer.pointer = (u8 *)guid;
	params[1].type = ACPI_TYPE_INTEGER;
	params[1].integer.value = rev;
	params[2].type = ACPI_TYPE_INTEGER;
	params[2].integer.value = func;
	if (argv4) {
		params[3] = *argv4;
	} else {
		params[3].type = ACPI_TYPE_PACKAGE;
		params[3].package.count = 0;
		params[3].package.elements = NULL;
	}

	ret = acpi_evaluate_object(handle, "_DSM", &input, &buf);
	if (ACPI_SUCCESS(ret))
		return (union acpi_object *)buf.pointer;

	if (ret != AE_NOT_FOUND)
		acpi_handle_warn(handle,
				 "failed to evaluate _DSM %pUb rev:%lld func:%lld (0x%x)\n",
				 guid, rev, func, ret);

	return NULL;
}
EXPORT_SYMBOL(acpi_evaluate_dsm);
```

The `params` array is a stack-local `union acpi_object params[4]`; there is no `ACPI_NUM_DSM_ARGS` style constant in the tree, the count 4 is written out in the [`struct acpi_object_list`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L956) initializer. Slot 0 points straight at the caller's [`guid_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uuid.h#L15) storage with no copy, which is why the GUID constants in consumers are file-scope `const` objects that outlive the call. Slot 3 either copies the caller's prepared `argv4` object by value or synthesizes an empty Package, satisfying the spec rule that Arg3 is present even for functions that take no arguments. The marshalling types are the external ACPICA object forms:

```c
/* include/acpi/actypes.h:908 */
union acpi_object {
	acpi_object_type type;	/* See definition of acpi_ns_type for values */
	struct {
		acpi_object_type type;	/* ACPI_TYPE_INTEGER */
		u64 value;	/* The actual number */
	} integer;

	struct {
		acpi_object_type type;	/* ACPI_TYPE_STRING */
		u32 length;	/* # of bytes in string, excluding trailing null */
		char *pointer;	/* points to the string value */
	} string;

	struct {
		acpi_object_type type;	/* ACPI_TYPE_BUFFER */
		u32 length;	/* # of bytes in buffer */
		u8 *pointer;	/* points to the buffer */
	} buffer;

	struct {
		acpi_object_type type;	/* ACPI_TYPE_PACKAGE */
		u32 count;	/* # of elements in package */
		union acpi_object *elements;	/* Pointer to an array of ACPI_OBJECTs */
	} package;

	struct {
		acpi_object_type type;	/* ACPI_TYPE_LOCAL_REFERENCE */
		acpi_object_type actual_type;	/* Type associated with the Handle */
		acpi_handle handle;	/* object reference */
	} reference;
	...
};

/*
 * List of objects, used as a parameter list for control method evaluation
 */
struct acpi_object_list {
	u32 count;
	union acpi_object *pointer;
};
```

The union's leading `type` field discriminates which member is live, with the values the helper uses defined alongside, [`ACPI_TYPE_INTEGER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L647) (0x01), [`ACPI_TYPE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L649) (0x03), and [`ACPI_TYPE_PACKAGE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L650) (0x04). The device itself is named by an [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424), the opaque cookie drivers obtain with [`ACPI_HANDLE()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L61) from their [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565):

```c
/* include/acpi/actypes.h:424 */
typedef void *acpi_handle;	/* Actually a ptr to a NS Node */
```

The output side uses the allocate-buffer protocol. `buf` starts as `{ACPI_ALLOCATE_BUFFER, NULL}`, the sentinel telling ACPICA to allocate one block sized for the returned object, and on success the function returns `buf.pointer` cast to [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908), transferring ownership to the caller:

```c
/* include/acpi/actypes.h:973 */
#define ACPI_ALLOCATE_BUFFER        (acpi_size) (-1)	/* Let ACPICA allocate buffer */
#define ACPI_ALLOCATE_LOCAL_BUFFER  (acpi_size) (-2)	/* For internal use only (enables tracking) */

#endif				/* ACPI_NO_MEM_ALLOCATIONS */

struct acpi_buffer {
	acpi_size length;	/* Length in bytes of the buffer */
	void *pointer;		/* pointer to buffer */
};
```

Every consumer below ends its parse with [`ACPI_FREE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L350), which in a regular kernel build maps to [`acpi_os_free()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/platform/aclinuxex.h#L62) (a tracking variant exists for `ACPI_DBG_TRACK_ALLOCATIONS` builds):

```c
/* include/acpi/actypes.h:345 */
/*
 * Normal memory allocation directly via the OS services layer
 */
#define ACPI_ALLOCATE(a)                acpi_os_allocate ((acpi_size) (a))
#define ACPI_ALLOCATE_ZEROED(a)         acpi_os_allocate_zeroed ((acpi_size) (a))
#define ACPI_FREE(a)                    acpi_os_free (a)
#define ACPI_MEM_TRACKING(a)
```

On failure the helper distinguishes the absent-method case. [`AE_NOT_FOUND`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L75) means the device carries no `_DSM` at all and returns NULL silently, every other status logs through [`acpi_handle_warn()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L1262) with the `%pUb` format printing the GUID (added by commit 06eb8dc097b3 so dmesg lines identify which interface failed). The macro prefixes the message with the namespace path of the handle by expanding to [`acpi_handle_printk()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L596):

```c
/* include/linux/acpi.h:1262 */
#define acpi_handle_warn(handle, fmt, ...)				\
	acpi_handle_printk(KERN_WARNING, handle, fmt, ##__VA_ARGS__)
```

### acpi_evaluate_dsm_typed guards the return type

Because the return type of a nonzero function index is interface-defined and firmware quality varies, most callers want a result only when it has the type they are about to parse. [`acpi_evaluate_dsm_typed()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L64) folds that check into the helper, freeing the mismatched object so the caller's NULL test covers both failure modes:

```c
/* include/acpi/acpi_bus.h:63 */
static inline union acpi_object *
acpi_evaluate_dsm_typed(acpi_handle handle, const guid_t *guid, u64 rev,
			u64 func, union acpi_object *argv4,
			acpi_object_type type)
{
	union acpi_object *obj;

	obj = acpi_evaluate_dsm(handle, guid, rev, func, argv4);
	if (obj && obj->type != type) {
		ACPI_FREE(obj);
		obj = NULL;
	}

	return obj;
}
```

Commit 9fbdc0504244 converted the PCI core's open-coded `acpi_evaluate_dsm()` plus `obj->type` checks to this wrapper, the form the PCI consumers below now use.

### acpi_check_dsm folds the function-0 mask

[`acpi_check_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L821) implements the query convention. It calls [`acpi_evaluate_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L771) with `func = 0` and `argv4 = NULL`, then folds the result into a 64-bit mask, taking the spec Buffer form byte by byte (eight bytes bound the fold, matching the kerneldoc's "Currently only support 64 functions at maximum") and accepting an Integer for old firmware:

```c
/* drivers/acpi/utils.c:810 */
/**
 * acpi_check_dsm - check if _DSM method supports requested functions.
 * @handle: ACPI device handle
 * @guid: GUID of requested functions, should be 16 bytes at least
 * @rev: revision number of requested functions
 * @funcs: bitmap of requested functions
 *
 * Evaluate device's _DSM method to check whether it supports requested
 * functions. Currently only support 64 functions at maximum, should be
 * enough for now.
 */
bool acpi_check_dsm(acpi_handle handle, const guid_t *guid, u64 rev, u64 funcs)
{
	int i;
	u64 mask = 0;
	union acpi_object *obj;

	if (funcs == 0)
		return false;

	obj = acpi_evaluate_dsm(handle, guid, rev, 0, NULL);
	if (!obj)
		return false;

	/* For compatibility, old BIOSes may return an integer */
	if (obj->type == ACPI_TYPE_INTEGER)
		mask = obj->integer.value;
	else if (obj->type == ACPI_TYPE_BUFFER)
		for (i = 0; i < obj->buffer.length && i < 8; i++)
			mask |= (((u64)obj->buffer.pointer[i]) << (i * 8));
	ACPI_FREE(obj);

	/*
	 * Bit 0 indicates whether there's support for any functions other than
	 * function 0 for the specified GUID and revision.
	 */
	if ((mask & 0x1) && (mask & funcs) == funcs)
		return true;

	return false;
}
EXPORT_SYMBOL(acpi_check_dsm);
```

The buffer fold treats byte i as bits 8i through 8i+7, exactly the little-endian bit numbering the ASL `Buffer () {0x1F}` example produces, and the final test enforces both halves of the convention, the bit-0 gate from the comment "Bit 0 indicates whether there's support for any functions other than function 0 for the specified GUID and revision" and the subset relation over the caller's `funcs` bits. The lead figure annotates the same mask bit by bit.

### PCI host bridges: Integer results gate boot-config and reset-delay behavior

The PCI Firmware Specification defines the functions behind [`pci_acpi_dsm_guid`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L30), and the kernel names the four indexes it consumes in [`include/linux/pci-acpi.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci-acpi.h):

```c
/* include/linux/pci-acpi.h:118 */
extern const guid_t pci_acpi_dsm_guid;

/* _DSM Definitions for PCI */
#define DSM_PCI_PRESERVE_BOOT_CONFIG		0x05
#define DSM_PCI_DEVICE_NAME			0x07
#define DSM_PCI_POWER_ON_RESET_DELAY		0x08
#define DSM_PCI_DEVICE_READINESS_DURATIONS	0x09
```

[`pci_acpi_preserve_config()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L124) evaluates function 5 against the host bridge with revision 1, demanding an Integer result, and a returned 0 means firmware resource assignments below the bridge must stay untouched:

```c
/* drivers/pci/pci-acpi.c:124 */
bool pci_acpi_preserve_config(struct pci_host_bridge *host_bridge)
{
	bool ret = false;

	if (ACPI_HANDLE(&host_bridge->dev)) {
		union acpi_object *obj;

		/*
		 * Evaluate the "PCI Boot Configuration" _DSM Function.  If it
		 * exists and returns 0, we must preserve any PCI resource
		 * assignments made by firmware for this host bridge.
		 */
		obj = acpi_evaluate_dsm_typed(ACPI_HANDLE(&host_bridge->dev),
					      &pci_acpi_dsm_guid,
					      1, DSM_PCI_PRESERVE_BOOT_CONFIG,
					      NULL, ACPI_TYPE_INTEGER);
		if (obj && obj->integer.value == 0)
			ret = true;
		ACPI_FREE(obj);
	}

	return ret;
}
```

Its caller sits in the generic probe path, [`pci_preserve_config()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/probe.c#L976), which consults the ACPI answer first and falls back to the devicetree equivalent:

```c
/* drivers/pci/probe.c:976 */
static bool pci_preserve_config(struct pci_host_bridge *host_bridge)
{
	if (pci_acpi_preserve_config(host_bridge))
		return true;

	if (host_bridge->dev.parent && host_bridge->dev.parent->of_node)
		return of_pci_preserve_config(host_bridge->dev.parent->of_node);

	return false;
}
```

[`acpi_pci_add_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1215) evaluates function 8 ("Reset Delay") with revision 3 once per root bus and latches a 1 into the bridge's `ignore_reset_delay` bit, declaring that every device in the hierarchy has already completed its power-on reset delay:

```c
/* drivers/pci/pci-acpi.c:1215 */
void acpi_pci_add_bus(struct pci_bus *bus)
{
	union acpi_object *obj;
	struct pci_host_bridge *bridge;

	if (acpi_pci_disabled || !bus->bridge || !ACPI_HANDLE(bus->bridge))
		return;

	acpi_pci_slot_enumerate(bus);
	acpiphp_enumerate_slots(bus);

	/*
	 * For a host bridge, check its _DSM for function 8 and if
	 * that is available, mark it in pci_host_bridge.
	 */
	if (!pci_is_root_bus(bus))
		return;

	obj = acpi_evaluate_dsm_typed(ACPI_HANDLE(bus->bridge), &pci_acpi_dsm_guid, 3,
				      DSM_PCI_POWER_ON_RESET_DELAY, NULL, ACPI_TYPE_INTEGER);
	if (!obj)
		return;

	if (obj->integer.value == 1) {
		bridge = pci_find_host_bridge(bus);
		bridge->ignore_reset_delay = 1;
	}
	ACPI_FREE(obj);
}
```

The hook runs from the architecture's bus-add callback, here the x86 one:

```c
/* arch/x86/pci/common.c:173 */
void pcibios_add_bus(struct pci_bus *bus)
{
	acpi_pci_add_bus(bus);
}
```

### Per-device Package results trim the D3 delays

[`pci_acpi_optimize_delay()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1384) consumes function 9 ("Device Readiness Durations"), the Package-returning member of the set. Its kerneldoc records the interplay with function 8 and the provenance of both, "These _DSM functions are defined by the draft ECN of January 28, 2014, titled 'ACPI additions for FW latency optimizations'", and the body shows the standard Package parse, count check, per-element type check, then field extraction with the microsecond values divided down to the millisecond delays the PCI core uses:

```c
/* drivers/pci/pci-acpi.c:1384 */
static void pci_acpi_optimize_delay(struct pci_dev *pdev,
				    acpi_handle handle)
{
	struct pci_host_bridge *bridge = pci_find_host_bridge(pdev->bus);
	int value;
	union acpi_object *obj, *elements;

	if (bridge->ignore_reset_delay)
		pdev->d3cold_delay = 0;

	obj = acpi_evaluate_dsm_typed(handle, &pci_acpi_dsm_guid, 3,
				      DSM_PCI_DEVICE_READINESS_DURATIONS, NULL,
				      ACPI_TYPE_PACKAGE);
	if (!obj)
		return;

	if (obj->package.count == 5) {
		elements = obj->package.elements;
		if (elements[0].type == ACPI_TYPE_INTEGER) {
			value = (int)elements[0].integer.value / 1000;
			if (value < PCI_PM_D3COLD_WAIT)
				pdev->d3cold_delay = value;
		}
		if (elements[3].type == ACPI_TYPE_INTEGER) {
			value = (int)elements[3].integer.value / 1000;
			if (value < PCI_PM_D3HOT_WAIT)
				pdev->d3hot_delay = value;
		}
	}
	ACPI_FREE(obj);
}
```

Element 0 caps `d3cold_delay` below [`PCI_PM_D3COLD_WAIT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci.h#L259) (100 ms) and element 3 caps `d3hot_delay` below [`PCI_PM_D3HOT_WAIT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci.h#L258) (10 ms), and the earlier `ignore_reset_delay` latch from [`acpi_pci_add_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1215) zeroes the cold delay outright, so the two `_DSM` functions compose per the kerneldoc's precedence note. The call site is the ACPI companion setup path that runs when a PCI device binds to its namespace node:

```c
/* drivers/pci/pci-acpi.c:1433 */
void pci_acpi_setup(struct device *dev, struct acpi_device *adev)
{
	struct pci_dev *pci_dev = to_pci_dev(dev);

	pci_acpi_optimize_delay(pci_dev, adev->handle);
	pci_acpi_set_external_facing(pci_dev);
	pci_acpi_add_edr_notifier(pci_dev);
	...
}
```

[`pci_acpi_setup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-acpi.c#L1433) itself runs from the device-model glue. [`acpi_device_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/glue.c#L352) fires when a newly added [`struct device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L565) gets bound to its ACPI companion and branches on the bus type:

```c
/* drivers/acpi/glue.c:376 */
	} else {
		adev = ACPI_COMPANION(dev);

		if (dev_is_pci(dev)) {
			pci_acpi_setup(dev, adev);
			goto done;
		} else if (dev_is_platform(dev)) {
			acpi_configure_pmsi_domain(dev);
		}
	}
```

### pci-label shows the check-then-evaluate pairing on one index

The firmware device-name function (index 7) backs the `label` and `acpi_index` sysfs attributes, and [`drivers/pci/pci-label.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-label.c) splits the two helper roles cleanly. [`device_has_acpi_name()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-label.c#L36) is the attribute-visibility gate, a pure [`acpi_check_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L821) call with revision 0x2 and the single requested bit `1 << DSM_PCI_DEVICE_NAME`:

```c
/* drivers/pci/pci-label.c:36 */
static bool device_has_acpi_name(struct device *dev)
{
#ifdef CONFIG_ACPI
	acpi_handle handle = ACPI_HANDLE(dev);

	if (!handle)
		return false;

	return acpi_check_dsm(handle, &pci_acpi_dsm_guid, 0x2,
			      1 << DSM_PCI_DEVICE_NAME);
#else
	return false;
#endif
}
```

[`dsm_get_label()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-label.c#L155) then performs the actual call with raw [`acpi_evaluate_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L771) rather than the typed wrapper, because the function returns a two-element Package whose second element is a String on some platforms and a UTF-16 Buffer on others, so a single-type filter would reject valid firmware. The body is the template for manual result parsing, type and count checks on the Package, per-element type dispatch, and the unconditional [`ACPI_FREE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L350) at the end:

```c
/* drivers/pci/pci-label.c:155 */
static int dsm_get_label(struct device *dev, char *buf,
			 enum acpi_attr_enum attr)
{
	acpi_handle handle = ACPI_HANDLE(dev);
	union acpi_object *obj, *tmp;
	int len = 0;

	if (!handle)
		return -1;

	obj = acpi_evaluate_dsm(handle, &pci_acpi_dsm_guid, 0x2,
				DSM_PCI_DEVICE_NAME, NULL);
	if (!obj)
		return -1;

	tmp = obj->package.elements;
	if (obj->type == ACPI_TYPE_PACKAGE && obj->package.count == 2 &&
	    tmp[0].type == ACPI_TYPE_INTEGER &&
	    (tmp[1].type == ACPI_TYPE_STRING ||
	     tmp[1].type == ACPI_TYPE_BUFFER)) {
		/*
		 * The second string element is optional even when
		 * this _DSM is implemented; when not implemented,
		 * this entry must return a null string.
		 */
		if (attr == ACPI_ATTR_INDEX_SHOW) {
			len = sysfs_emit(buf, "%llu\n", tmp->integer.value);
		} else if (attr == ACPI_ATTR_LABEL_SHOW) {
			if (tmp[1].type == ACPI_TYPE_STRING)
				len = sysfs_emit(buf, "%s\n",
						 tmp[1].string.pointer);
			else if (tmp[1].type == ACPI_TYPE_BUFFER)
				len = dsm_label_utf16s_to_utf8s(tmp + 1, buf);
		}
	}

	ACPI_FREE(obj);

	return len > 0 ? len : -1;
}
```

Reading `tmp->integer.value` for the index and `tmp[1].string.pointer` for the label demonstrates how the [`union acpi_object`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L908) members are consumed once the `type` discriminator has been verified, and the single free covers the whole tree of package elements because ACPICA returns the object and its elements in the one [`ACPI_ALLOCATE_BUFFER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L973) block.

Both functions are wired into the device's sysfs group, [`dsm_get_label()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-label.c#L155) as the body of the two show callbacks and [`device_has_acpi_name()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/pci/pci-label.c#L36) as the visibility predicate that hides the attributes on devices whose firmware fails the function-0 check:

```c
/* drivers/pci/pci-label.c:196 */
static ssize_t label_show(struct device *dev, struct device_attribute *attr,
			  char *buf)
{
	return dsm_get_label(dev, buf, ACPI_ATTR_LABEL_SHOW);
}
static DEVICE_ATTR_RO(label);

static ssize_t acpi_index_show(struct device *dev,
			      struct device_attribute *attr, char *buf)
{
	return dsm_get_label(dev, buf, ACPI_ATTR_INDEX_SHOW);
}
static DEVICE_ATTR_RO(acpi_index);

static struct attribute *acpi_attrs[] = {
	&dev_attr_label.attr,
	&dev_attr_acpi_index.attr,
	NULL,
};

static umode_t acpi_attr_is_visible(struct kobject *kobj, struct attribute *a,
				    int n)
{
	struct device *dev = kobj_to_dev(kobj);

	if (!device_has_acpi_name(dev))
		return 0;

	return a->mode;
}
```

### USB ports: guid_parse, check, and typed evaluation in one walk

[`usb_acpi_port_lpm_incapable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/usb-acpi.c#L59) in the USB core queries the USB controller `_DSM` (UUID ce2ee385-00e6-48cb-9f05-2edb927c4899, function index 5) against an individual port's namespace node to learn whether U1/U2 link power management must stay off for that port. The function is the full client pattern in forty lines, the string UUID parsed at run time, the handle resolved per port, the function-0 gate, then the typed evaluation and Integer consumption:

```c
/* drivers/usb/core/usb-acpi.c:40 */
#define UUID_USB_CONTROLLER_DSM "ce2ee385-00e6-48cb-9f05-2edb927c4899"
#define USB_DSM_DISABLE_U1_U2_FOR_PORT	5

/**
 * usb_acpi_port_lpm_incapable - check if lpm should be disabled for a port.
 * @hdev: USB device belonging to the usb hub
 * @index: zero based port index
 *
 * Some USB3 ports may not support USB3 link power management U1/U2 states
 * due to different retimer setup. ACPI provides _DSM method which returns 0x01
 * if U1 and U2 states should be disabled. Evaluate _DSM with:
 * Arg0: UUID = ce2ee385-00e6-48cb-9f05-2edb927c4899
 * Arg1: Revision ID = 0
 * Arg2: Function Index = 5
 * Arg3: (empty)
 *
 * Return 1 if USB3 port is LPM incapable, negative on error, otherwise 0
 */

int usb_acpi_port_lpm_incapable(struct usb_device *hdev, int index)
{
	union acpi_object *obj;
	acpi_handle port_handle;
	int port1 = index + 1;
	guid_t guid;
	int ret;

	ret = guid_parse(UUID_USB_CONTROLLER_DSM, &guid);
	if (ret)
		return ret;

	port_handle = usb_get_hub_port_acpi_handle(hdev, port1);
	if (!port_handle) {
		dev_dbg(&hdev->dev, "port-%d no acpi handle\n", port1);
		return -ENODEV;
	}

	if (!acpi_check_dsm(port_handle, &guid, 0,
			    BIT(USB_DSM_DISABLE_U1_U2_FOR_PORT))) {
		dev_dbg(&hdev->dev, "port-%d no _DSM function %d\n",
			port1, USB_DSM_DISABLE_U1_U2_FOR_PORT);
		return -ENODEV;
	}

	obj = acpi_evaluate_dsm_typed(port_handle, &guid, 0,
				      USB_DSM_DISABLE_U1_U2_FOR_PORT, NULL,
				      ACPI_TYPE_INTEGER);
	if (!obj) {
		dev_dbg(&hdev->dev, "evaluate port-%d _DSM failed\n", port1);
		return -EINVAL;
	}

	if (obj->integer.value == 0x01)
		ret = 1;

	ACPI_FREE(obj);

	return ret;
}
```

[`usb_get_hub_port_acpi_handle()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L6557) supplies the [`acpi_handle`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L424) of the port device object underneath the hub's companion, showing that `_DSM` evaluations target whatever namespace node carries the method, here a port child rather than the device a driver bound to. The consuming end of the call lives in the xHCI roothub setup, which loops over the hub's children and stores the per-port answer:

```c
/* drivers/usb/host/xhci-pci.c:532 */
static void xhci_find_lpm_incapable_ports(struct usb_hcd *hcd, struct usb_device *hdev)
{
	struct xhci_hcd	*xhci = hcd_to_xhci(hcd);
	struct xhci_hub *rhub = &xhci->usb3_rhub;
	int ret;
	int i;

	/* This is not the usb3 roothub we are looking for */
	if (hcd != rhub->hcd)
		return;

	if (hdev->maxchild > rhub->num_ports) {
		dev_err(&hdev->dev, "USB3 roothub port number mismatch\n");
		return;
	}

	for (i = 0; i < hdev->maxchild; i++) {
		ret = usb_acpi_port_lpm_incapable(hdev, i);

		dev_dbg(&hdev->dev, "port-%d disable U1/U2 _DSM: %d\n", i + 1, ret);

		if (ret >= 0) {
			rhub->ports[i]->lpm_incapable = ret;
			continue;
		}
	}
}
```

That loop runs from the host controller's `update_hub_device` hook when the USB core registers the root hub, so the `_DSM` answers are cached before any downstream device negotiates link power management:

```c
/* drivers/usb/host/xhci-pci.c:597 */
static int xhci_pci_update_hub_device(struct usb_hcd *hcd, struct usb_device *hdev,
				      struct usb_tt *tt, gfp_t mem_flags)
{
	/* Check if acpi claims some USB3 roothub ports are lpm incapable */
	if (!hdev->parent)
		xhci_find_lpm_incapable_ports(hcd, hdev);

	return xhci_update_hub_device(hcd, hdev, tt, mem_flags);
}
```

### TPM PPI packs a populated Arg3 with ACPI_INIT_DSM_ARGV4

All the calls above pass `argv4 = NULL` and let the helper synthesize the empty Package. The TCG Physical Presence Interface needs real function arguments, and [`ACPI_INIT_DSM_ARGV4`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L80) is the designated-initializer macro that builds the Arg3 Package object around a caller-side element array:

```c
/* include/acpi/acpi_bus.h:80 */
#define	ACPI_INIT_DSM_ARGV4(cnt, eles)			\
	{						\
	  .package.type = ACPI_TYPE_PACKAGE,		\
	  .package.count = (cnt),			\
	  .package.elements = (eles)			\
	}
```

The PPI GUID is a file-scope [`GUID_INIT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uuid.h#L23) constant and the driver routes every call through a one-line wrapper over [`acpi_evaluate_dsm_typed()`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L64):

```c
/* drivers/char/tpm/tpm_ppi.c:32 */
static const guid_t tpm_ppi_guid =
	GUID_INIT(0x3DDDFAA6, 0x361B, 0x4EB4,
		  0xA4, 0x24, 0x8D, 0x10, 0x08, 0x9D, 0x16, 0x53);
```

```c
/* drivers/char/tpm/tpm_ppi.c:55 */
static inline union acpi_object *
tpm_eval_dsm(acpi_handle ppi_handle, int func, acpi_object_type type,
	     union acpi_object *argv4, u64 rev)
{
	BUG_ON(!ppi_handle);
	return acpi_evaluate_dsm_typed(ppi_handle, &tpm_ppi_guid,
				       rev, func, argv4, type);
}
```

[`tpm_store_ppi_request()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/char/tpm/tpm_ppi.c#L124) exercises the macro with a two-slot element array, and it also demonstrates both remaining ABI degrees of freedom, the revision parameter (PPI 1.3 requests use revision 2 with two Integer arguments, earlier versions revision 1 with one) and the function-0 capability probe steering which function index to call ([`acpi_check_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L821) selecting `SUBREQ2` over `SUBREQ` when bit 7 is set). The pre-1.2 branch overwrites the prepared Package with a Buffer-typed Arg3, matching the kerneldoc's note that old firmware expects Arg3 types beyond the Package the spec defines:

```c
/* drivers/char/tpm/tpm_ppi.c:124 */
static ssize_t tpm_store_ppi_request(struct device *dev,
				     struct device_attribute *attr,
				     const char *buf, size_t count)
{
	u32 req;
	u64 ret;
	int func = TPM_PPI_FN_SUBREQ;
	union acpi_object *obj, tmp[2];
	union acpi_object argv4 = ACPI_INIT_DSM_ARGV4(2, tmp);
	struct tpm_chip *chip = to_tpm_chip(dev);
	u64 rev = TPM_PPI_REVISION_ID_1;

	/*
	 * the function to submit TPM operation request to pre-os environment
	 * is updated with function index from SUBREQ to SUBREQ2 since PPI
	 * version 1.1
	 */
	if (acpi_check_dsm(chip->acpi_dev_handle, &tpm_ppi_guid,
			   TPM_PPI_REVISION_ID_1, 1 << TPM_PPI_FN_SUBREQ2))
		func = TPM_PPI_FN_SUBREQ2;

	/*
	 * PPI spec defines params[3].type as ACPI_TYPE_PACKAGE. Some BIOS
	 * accept buffer/string/integer type, but some BIOS accept buffer/
	 * string/package type. For PPI version 1.0 and 1.1, use buffer type
	 * for compatibility, and use package type since 1.2 according to spec.
	 */
	if (strcmp(chip->ppi_version, "1.3") == 0) {
		if (sscanf(buf, "%llu %llu", &tmp[0].integer.value,
			   &tmp[1].integer.value) != 2)
			goto ppi12;
		rev = TPM_PPI_REVISION_ID_2;
		tmp[0].type = ACPI_TYPE_INTEGER;
		tmp[1].type = ACPI_TYPE_INTEGER;
	} else if (strcmp(chip->ppi_version, "1.2") < 0) {
		if (sscanf(buf, "%d", &req) != 1)
			return -EINVAL;
		argv4.type = ACPI_TYPE_BUFFER;
		argv4.buffer.length = sizeof(req);
		argv4.buffer.pointer = (u8 *)&req;
	} else {
ppi12:
		argv4.package.count = 1;
		tmp[0].type = ACPI_TYPE_INTEGER;
		if (sscanf(buf, "%llu", &tmp[0].integer.value) != 1)
			return -EINVAL;
	}

	obj = tpm_eval_dsm(chip->acpi_dev_handle, func, ACPI_TYPE_INTEGER,
			   &argv4, rev);
	if (!obj) {
		return -ENXIO;
	} else {
		ret = obj->integer.value;
		ACPI_FREE(obj);
	}

	if (ret == 0)
		return (acpi_status)count;

	return (ret == 1) ? -EPERM : -EFAULT;
}
```

The store handler reaches userspace as the `request` attribute of the TPM's `ppi` sysfs group:

```c
/* drivers/char/tpm/tpm_ppi.c:386 */
static DEVICE_ATTR(request, S_IRUGO | S_IWUSR | S_IWGRP,
		   tpm_show_ppi_request, tpm_store_ppi_request);
```

The `argv4` object is passed to [`acpi_evaluate_dsm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/utils.c#L771) by pointer and copied by value into `params[3]`, so the element array `tmp[]` must stay alive across the call but needs no heap allocation, and the whole Arg3 construction stays on the caller's stack. Together with the PCI Integer and Package consumers and the USB gate-then-evaluate chain, this covers every slot of the ABI the lead figure draws, the UUID in slot 0 from [`GUID_INIT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uuid.h#L23) or [`guid_parse()`](https://elixir.bootlin.com/linux/v7.0/source/lib/uuid.c#L124), the revision and function Integers, the optional Package, and a caller-owned return object released with [`ACPI_FREE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L350) on every path.
