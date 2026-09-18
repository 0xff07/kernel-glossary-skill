# USB4 host interface device links

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A PCI Express port whose traffic crosses a USB4 tunnel depends on a host controller the PCI topology does not show, because the tunnel is carried by a separate device the kernel powers down on its own schedule. Platform firmware records that dependency by pointing the port's ACPI device object at the host interface's ACPI device object. The USB4 driver reads those pointers once per domain and turns each into a device link, so the driver core knows which port depends on which controller before either device is suspended or resumed. This page traces one reference from the namespace walk that finds it to the link it produces, and says what that link changes.

## SUMMARY

Firmware and the driver core describe the same dependency in different terms, and this mechanism translates the first into the second. A tunneled port appears in firmware as an ACPI device object carrying a `usb4-host-interface` reference to the host interface's object, and in the driver core as a consumer joined to a supplier by a device link. The translation runs once, while the software connection manager's domain is probed.

The journey starts at the ACPI namespace root and ends at one [`device_link_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L800) call per qualifying port, and it begins only when the host interface has an ACPI companion. Between them the walk offers every device object under the root, to a depth of 32, to a callback that tests the reference and the device behind it. A port qualifies only when that device is a PCI device reporting itself as a Root Port or a Downstream Port, which leaves USB3 ports named by the same property to the USB core.

## SPECIFICATIONS

No specification in the documented tree defines the `usb4-host-interface` property name or its semantics, so the model on this page is a disclosed synthesis over drivers/thunderbolt/acpi.c, the driver core's device-link interface and the commit history, and every fact under it is cited to one of those. The ACPI machinery that carries the property is specified.

- `_DSD` (Device Specific Data) Implementation Guide, section "Well-Known _DSD UUIDs and Data Structure Formats", sub-section "Device Properties UUID": the package format a device-properties property takes and the UUID that marks it, named in [`Documentation/firmware-guide/acpi/DSD-properties-rules.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/firmware-guide/acpi/DSD-properties-rules.rst#L24) and cited again from [drivers/acpi/property.c:37](https://elixir.bootlin.com/linux/v7.2/source/drivers/acpi/property.c#L37) beside the device-properties UUID the ACPI core matches at [drivers/acpi/property.c:41](https://elixir.bootlin.com/linux/v7.2/source/drivers/acpi/property.c#L41).

## COVERAGE

### drivers/thunderbolt/

- [`'\<tb_acpi_add_link\>':'drivers/thunderbolt/acpi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L14): the namespace callback, which tests one ACPI device object and creates the device link for a port that passes every test.
- [`'\<tb_acpi_add_links\>':'drivers/thunderbolt/acpi.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L91): the entry point, which searches the namespace on behalf of one host interface and reports whether any link came out of it.

## DOCUMENTATION

- [`Documentation/ABI/testing/sysfs-class-devlink`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-class-devlink): the directory every device link gets and the attributes it carries, including the one that says whether the link affects runtime power management.
- [`Documentation/firmware-guide/acpi/DSD-properties-rules.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/firmware-guide/acpi/DSD-properties-rules.rst): the rules a device-properties package follows and the guide that defines the UUID marking it.

## OTHER SOURCES

- [thunderbolt: Don't create device link from USB4 Host Interface to USB3 xHC host (commit f20998f23a8c)](https://lore.kernel.org/r/20240830152630.3943215-5-mathias.nyman@linux.intel.com)

## REGISTERS

This mechanism reads no USB4 configuration space and no host-interface register. Its decisions come from the ACPI namespace and from the driver model. The one hardware-defined value it consults belongs to PCI Express. [`pci_pcie_type()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pci.h#L2678) returns the Device/Port Type field of the PCI Express Capabilities Register, which the PCI core caches in [`pdev->pcie_flags_reg`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pci.h#L385) at enumeration time, and the callback compares that value against [`PCI_EXP_TYPE_ROOT_PORT`](https://elixir.bootlin.com/linux/v7.2/source/include/uapi/linux/pci_regs.h#L488) and [`PCI_EXP_TYPE_DOWNSTREAM`](https://elixir.bootlin.com/linux/v7.2/source/include/uapi/linux/pci_regs.h#L490).

## DETAILS

### Firmware points a tunneled port at the host interface

The dependency this mechanism records is invisible to the PCI topology, because nothing in the port's configuration space names the host controller that carries its tunnel. Platform firmware supplies the missing edge as a property on the port's ACPI device object, a `_DSD` device-properties package holding one named reference to the host interface's own ACPI device object. The commit that added the first reader, b2be2b05cf3b "thunderbolt: Create device links from ACPI description", sketches the shape firmware is expected to take.

```
    Scope (\_SB.PCI0)
    {
        Device (NHI0) { } // Thunderbolt NHI

        Device (DSB0) // Hotplug downstream port
        {
            Name (_DSD, Package () {
                ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
                Package () {
                    Package () {"usb4-host-interface", \_SB.PCI0.NHI0},
                    ...
                }
            })
        }
    }
```

The sketch puts the host interface and the port in one scope and gives the port a `_DSD` package whose device-properties UUID introduces a property named `usb4-host-interface` with the host interface object as its value. Firmware marks the objects of the ports whose traffic is tunneled this way, and this walk matches on that property. The same property is also written on tunneled USB3 ports, which is the reason the callback below carries a test that a port reference alone would not need.

The property is a shared firmware convention and not this driver's private one, which is why a reader has to establish that a reference resolves to the host interface it is working for. Five places in the tree read it, at [drivers/thunderbolt/acpi.c:26](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L26), [drivers/thunderbolt/usb4_port.c:136](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L136), [drivers/usb/core/usb-acpi.c:173](https://elixir.bootlin.com/linux/v7.2/source/drivers/usb/core/usb-acpi.c#L173), [drivers/usb/typec/port-mapper.c:71](https://elixir.bootlin.com/linux/v7.2/source/drivers/usb/typec/port-mapper.c#L71) and, on x86, [arch/x86/pci/acpi.c:304](https://elixir.bootlin.com/linux/v7.2/source/arch/x86/pci/acpi.c#L304).

| reader | what it does with the reference |
|---|---|
| [`tb_acpi_add_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L14) | creates the device link this page traces |
| [`usb4_usb3_port_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L118) | pairs a USB4 port device with the USB 3.x port that names the same host interface |
| [`usb_acpi_add_usb4_devlink()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/usb/core/usb-acpi.c#L158) | gives a tunneled USB3 device its own device link to the host interface |
| [`typec_link_ports()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/usb/typec/port-mapper.c#L79) | adds a component match so a Type-C connector can be bound to its USB4 port |
| [`pcie_has_usb4_host_interface()`](https://elixir.bootlin.com/linux/v7.2/source/arch/x86/pci/acpi.c#L294) | reports to the x86 PCI code that a device behind the port arrived over a tunnel |

The first row is the mechanism this page follows, and the rest are named here so the property is not mistaken for a private convention. Four of the five resolve the reference to a device, and the Type-C port mapper only tests that the property is present. The match it queues for a USB4 port device can bind only after [`usb4_port_device_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4_port.c#L303) has registered that device as a component, so that reader depends on this subsystem having run.

### The walk offers every device object under the root

Finding the ports means searching the whole ACPI namespace, because firmware may place a port object anywhere and the driver knows only the host interface it is probing. [`tb_acpi_add_links()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L91) runs that search once per host interface and answers one question for its caller, whether any link came out of it.

```c
/* drivers/thunderbolt/acpi.c:81 */
/**
 * tb_acpi_add_links() - Add device links based on ACPI description
 * @nhi: Pointer to NHI
 *
 * Goes over ACPI namespace finding tunneled ports that reference to
 * @nhi ACPI node. For each reference a device link is added. The link
 * is automatically removed by the driver core.
 *
 * Returns %true if at least one link was created, %false otherwise.
 */
bool tb_acpi_add_links(struct tb_nhi *nhi)
{
	acpi_status status;
	bool ret = false;

	if (!has_acpi_companion(nhi->dev))
		return false;

	/*
	 * Find all devices that have usb4-host-controller interface
	 * property that references to this NHI.
	 */
	status = acpi_walk_namespace(ACPI_TYPE_DEVICE, ACPI_ROOT_OBJECT, 32,
				     tb_acpi_add_link, NULL, nhi, (void **)&ret);
	if (ACPI_FAILURE(status)) {
		dev_warn(nhi->dev, "failed to enumerate tunneled ports\n");
		return false;
	}

	return ret;
}
```

[`tb_acpi_add_links()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L91) declines to search at all when the host interface device carries no ACPI companion, since a reference can only resolve to a device the ACPI scan has attached to a namespace object. [`has_acpi_companion()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/acpi.h#L86) is that test and it reads [`nhi->dev`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L520), the device the host controller driver registered, which at v7.2 stands where earlier kernels kept a PCI device pointer.

[`acpi_walk_namespace()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/acpi/acpica/nsxfeval.c#L554) then descends from [`ACPI_ROOT_OBJECT`](https://elixir.bootlin.com/linux/v7.2/source/include/acpi/actypes.h#L458) through objects of type [`ACPI_TYPE_DEVICE`](https://elixir.bootlin.com/linux/v7.2/source/include/acpi/actypes.h#L652), to the depth of 32 given at [drivers/thunderbolt/acpi.c:103](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L103), calling [`tb_acpi_add_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L14) on the way down and nothing on the way up. The `nhi` pointer travels as the walk's context and the address of `ret` as its return slot, which is how a callback that sees no caller reports its result. A walk that ends in failure leaves the host interface's warning about enumerating tunneled ports and makes the function answer false, the same answer a namespace with no reference produces.

```
Which objects the walk reaches, and which of them earn a link
────────────────────────────────────────────────────────────
(depth counts from ACPI_ROOT_OBJECT; ◉ marks an object whose
 usb4-host-interface property resolves to the NHI0 object)

depth 0    ┌──────────────── ACPI_ROOT_OBJECT ────────────────┐
           │  every ACPI_TYPE_DEVICE object below is offered  │
           │  to the callback, and nothing above it           │
           └────────────────────────┬─────────────────────────┘
                                    │
depth 2                       ┌─────┴──────┐
                 ┌────────────┤    PCI0    ├────────────┐
                 │            └─────┬──────┘            │
                 │                  │                   │
depth 3    ┌─────┴──────┐    ┌──────┴─────┐    ┌────────┴───┐
           │    NHI0    │    │ ◉   DSB0   │    │ ◉   XHC0   │
           └────────────┘    └──────┬─────┘    └────────────┘
           the supplier             │          a USB3 port with
                                    │          no PCI device:
                                    │          refused
depth 4                      ┌──────┴─────┐
                             │ ◉   DSB1   │    a Downstream Port:
                             └──────┬─────┘    linked
                                    │
     ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┼─ ─ ─ ─   depth 32, the deepest
                                    │          the walk descends
depth 33                     ┌──────┴─────┐
                             │ ◉   DSB2   │    never offered to the
                             └────────────┘    callback

DSB0 is a Root Port and is linked; the objects marked ◉ all carry the
same property, and depth alone decides whether the callback ever sees
one.
```

Depth is the first thing that decides the outcome, because an object below the limit is never offered to the callback, whatever property it carries. The limit is a literal in the call and not a tunable, so a firmware description that buries a port deeper than 32 levels below the root produces no link for that port, and whether anything reaches the log then depends on the other ports, since the probe's warning fires only when no port at all produced one. Within the limit the outcome is the callback's to decide, on the object's own reference and on the device behind it.

### The callback tests the reference and the port behind it

A reference on an object proves only that firmware wrote one, and the callback still has to establish that it names this host interface and that the device behind the object is one the driver core can usefully link. [`tb_acpi_add_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L14) settles both questions before it creates anything, and it leaves the namespace unchanged whenever either answer is no.

```c
/* drivers/thunderbolt/acpi.c:14 */
static acpi_status tb_acpi_add_link(acpi_handle handle, u32 level, void *data,
				    void **ret)
{
	struct acpi_device *adev = acpi_fetch_acpi_dev(handle);
	struct fwnode_handle *fwnode;
	struct tb_nhi *nhi = data;
	struct pci_dev *pdev;
	struct device *dev;

	if (!adev)
		return AE_OK;

	fwnode = fwnode_find_reference(acpi_fwnode_handle(adev), "usb4-host-interface", 0);
	if (IS_ERR(fwnode))
		return AE_OK;

	/* It needs to reference this NHI */
	if (dev_fwnode(nhi->dev) != fwnode)
		goto out_put;
```

[`tb_acpi_add_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L14) turns the handle the walk gives it into an ACPI device and asks [`fwnode_find_reference()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/property.c#L645) for index 0 of the property on that device's firmware node. An object without the property yields an error pointer, and the callback answers [`AE_OK`](https://elixir.bootlin.com/linux/v7.2/source/include/acpi/acexcep.h#L60) so that the walk carries on to the next object. The identity test at [drivers/thunderbolt/acpi.c:31](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L31) compares the resolved node against the firmware node of [`nhi->dev`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L520), so a port naming a different host interface on a machine that has two of them drops out here with its reference released at the `out_put` label.

The device behind the object is the second question, and the answer decides between two different link owners. According to the comment above the test, "USB core will set up device links between tunneled USB3 devices and NHI host during USB device creation", and a USB3 port "might not even have a physical device yet if xHCI driver isn't bound yet"; commit f20998f23a8c removed the link this callback once made to the USB3 host controller for exactly that reason.

```c
/* drivers/thunderbolt/acpi.c:14 */
static acpi_status tb_acpi_add_link(acpi_handle handle, u32 level, void *data,
				    void **ret)
/* drivers/thunderbolt/acpi.c:34 */
	/*
	 * Ignore USB3 ports here as USB core will set up device links between
	 * tunneled USB3 devices and NHI host during USB device creation.
	 * USB3 ports might not even have a physical device yet if xHCI driver
	 * isn't bound yet.
	 */
	dev = acpi_get_first_physical_node(adev);
	if (!dev || !dev_is_pci(dev))
		goto out_put;

	/* Check that this matches a PCIe root/downstream port. */
	pdev = to_pci_dev(dev);
	if (pci_is_pcie(pdev) &&
	    (pci_pcie_type(pdev) == PCI_EXP_TYPE_ROOT_PORT ||
	     pci_pcie_type(pdev) == PCI_EXP_TYPE_DOWNSTREAM)) {
```

[`acpi_get_first_physical_node()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/acpi/bus.c#L810) returns the device the ACPI scan attached to the object, and the null check beside it rejects an object the scan attached nothing to. [`dev_is_pci()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pci.h#L1282) rejects an object whose device is on another bus, which is how a USB3 port carrying the same property leaves this path. The port-type test then narrows what remains to the two values the tunnel can terminate at, [`PCI_EXP_TYPE_ROOT_PORT`](https://elixir.bootlin.com/linux/v7.2/source/include/uapi/linux/pci_regs.h#L488) and [`PCI_EXP_TYPE_DOWNSTREAM`](https://elixir.bootlin.com/linux/v7.2/source/include/uapi/linux/pci_regs.h#L490), read through [`pci_pcie_type()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pci.h#L2678) after [`pci_is_pcie()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pci.h#L2660) confirms the device has the capability at all, and a device that fails it falls past the whole branch to the same `out_put` label, so every exit that holds a reference releases it there.

### The link makes the host interface the port's supplier

A device link is the driver core's record that one device needs another, and it is the only lasting thing this mechanism produces. [`tb_acpi_add_link()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L14) creates it with the port as the consumer and the host interface as the supplier, inside a bracket that holds the port resumed while the link is being established.

```c
/* drivers/thunderbolt/acpi.c:14 */
static acpi_status tb_acpi_add_link(acpi_handle handle, u32 level, void *data,
				    void **ret)
...
		const struct device_link *link;

		/*
		 * Make them both active first to make sure the NHI does
		 * not runtime suspend before the consumer. The
		 * pm_runtime_put() below then allows the consumer to
		 * runtime suspend again (which then allows NHI runtime
		 * suspend too now that the device link is established).
		 */
		pm_runtime_get_sync(&pdev->dev);

		link = device_link_add(&pdev->dev, nhi->dev,
				       DL_FLAG_AUTOREMOVE_SUPPLIER |
				       DL_FLAG_RPM_ACTIVE |
				       DL_FLAG_PM_RUNTIME);
		if (link) {
			dev_dbg(nhi->dev, "created link from %s\n",
				dev_name(&pdev->dev));
			*(bool *)ret = true;
		} else {
			dev_warn(nhi->dev, "device link creation from %s failed\n",
				 dev_name(&pdev->dev));
		}

		pm_runtime_put(&pdev->dev);
	}

out_put:
	fwnode_handle_put(fwnode);
	return AE_OK;
}
```

[`pm_runtime_get_sync()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L511) at [drivers/thunderbolt/acpi.c:58](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L58) resumes the port and holds a usage reference across the call, and [`pm_runtime_put()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L549) at [drivers/thunderbolt/acpi.c:73](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L73) drops it once the link exists. According to the comment above the bracket the pair makes "them both active first to make sure the NHI does not runtime suspend before the consumer", and the put afterwards "allows the consumer to runtime suspend again". Success sets the shared flag through the walk's return slot, and a refused link is reported against the host interface's device with the consumer's name in the message.

Three flags travel with the call, and each of them settles one question about the pair of devices the link joins. The driver core reads them at link creation and keeps them for the life of the link.

| flag | what it settles for this consumer and this supplier |
|---|---|
| [`DL_FLAG_PM_RUNTIME`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L439) | runtime PM takes the link into account, so the host interface counts as a supplier of the port |
| [`DL_FLAG_RPM_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L440) | the host interface is forced active and reference-counted as the link is created |
| [`DL_FLAG_AUTOREMOVE_SUPPLIER`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L441) | the driver core owns the link and deletes it when the host interface's driver unbinds |

Those three readings come from two places, the driver core's own documentation for the first two rows and this driver's kerneldoc for the third. The kerneldoc of [`device_link_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/base/core.c#L800) states the runtime-PM pair together and makes one of them conditional on the other.

```c
/* drivers/base/core.c:741 */
/**
 * device_link_add - Create a link between two devices.
...
 * The caller is responsible for the proper synchronization of the link creation
 * with runtime PM.  First, setting the DL_FLAG_PM_RUNTIME flag will cause the
 * runtime PM framework to take the link into account.  Second, if the
 * DL_FLAG_RPM_ACTIVE flag is set in addition to it, the supplier devices will
 * be forced into the active meta state and reference-counted upon the creation
 * of the link.  If DL_FLAG_PM_RUNTIME is not set, DL_FLAG_RPM_ACTIVE will be
 * ignored.
```

The kerneldoc makes [`DL_FLAG_RPM_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L440) conditional on [`DL_FLAG_PM_RUNTIME`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L439), which this call sets, so the host interface is forced active and reference-counted as the link is created. The kerneldoc of [`tb_acpi_add_links()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L91) describes the third flag when it says the link is automatically removed by the driver core, which is why nothing in this driver ever calls a delete.

### The probe warns when no port claimed the host interface

The links order a resume, and the message of commit b2be2b05cf3b describes what a machine without them risks, the tunnels not being established before the port resumes and the USB and PCI cores starting to tear down the device stack. The probe reports their absence once. [`tb_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3374) asks for the links as it finishes building the software connection manager's domain and treats a negative answer as worth a line in the log.

```c
/* drivers/thunderbolt/tb.c:3374 */
struct tb *tb_probe(struct tb_nhi *nhi)
...
	tb_dbg(tb, "using software connection manager\n");

	/*
	 * Device links are needed to make sure we establish tunnels
	 * before the PCIe/USB stack is resumed so complain here if we
	 * found them missing.
	 */
	if (!tb_apple_add_links(nhi) && !tb_acpi_add_links(nhi))
		tb_warn(tb, "device links to tunneled native ports are missing!\n");

	return tb;
}
```

[`tb_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3374) tries an earlier link helper first and reaches [`tb_acpi_add_links()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L91) only when that helper added no link, so the ACPI walk runs on every machine the earlier helper does not serve. Neither answer is an error and the domain is returned either way; the warning at [drivers/thunderbolt/tb.c:3404](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3404) reaches the log only when both answered false. According to the comment above the pair, the links exist so that tunnels are established before the PCIe and USB stacks are resumed, which is the reason a missing link is worth complaining about at all.

The call at [drivers/thunderbolt/tb.c:3403](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3403) is also the only one in the tree. Nothing re-runs the walk on hotplug, on resume or when a tunnel is established later, so the set of links a host interface has is the set its probe produced, minus any the driver core has since removed.

### A linked port holds the host interface awake

What a link changes shows up in the driver core and, once per domain, in this driver's own log, and this driver keeps no state about the links it asked for beyond the true or false it returned. Each difference below is something a reader can check on a running machine.

| what differs | a port that got its link | a port that did not |
|---|---|---|
| sysfs | a directory under /sys/class/devlink named for the supplier and consumer pair | no directory for the pair |
| the host interface's runtime PM | held out of runtime suspend while the port is active | nothing in this mechanism holds it awake for that port |
| the domain's log, once per domain | no line about missing links | the probe's warning, when no port on the machine produced a link |

The sysfs directory carries the flags as readable attributes, its `runtime_pm` attribute reading 1 exactly when [`DL_FLAG_PM_RUNTIME`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L439) is set and its `auto_remove_on` attribute reading supplier unbind exactly when [`DL_FLAG_AUTOREMOVE_SUPPLIER`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L441) is. The comment in the callback gives the runtime-power-management row as the purpose of the active bracket, and the same comment records that the host interface is free to suspend again only once the link exists and the port itself suspends. Under a port with no link this mechanism contributes no such reference, and the host interface's own callbacks [`nhi_runtime_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1079) and [`nhi_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/nhi.c#L1097), which stop and restart the domain's control traffic, run whenever the rest of the driver's runtime-PM accounting allows.

No call site inside this driver gains a precondition from a link, because the precondition is added in the driver core's runtime-PM paths, which consider every link carrying [`DL_FLAG_PM_RUNTIME`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L439). The return to the unlinked state is driven by [`DL_FLAG_AUTOREMOVE_SUPPLIER`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/device.h#L441), which is where this driver hands off. The driver core deletes the link when the host interface's driver unbinds, after it has called this driver's own remove callback, and nothing in this driver acts on the link.

### Without ACPI the walk is a stub that answers false

The walk exists only in a kernel built with ACPI support, because the file holding it is compiled under that option. [drivers/thunderbolt/Makefile:8](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Makefile#L8) adds acpi.o to the thunderbolt module under [`CONFIG_ACPI`](https://elixir.bootlin.com/linux/v7.2/source/drivers/acpi/Kconfig#L9), and the header splits its declarations on the same option, so [`tb_acpi_add_links()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/acpi.c#L91) is a prototype under the option and an inline without it, and callers compile either way.

```c
/* drivers/thunderbolt/tb.h:1510 */
#ifdef CONFIG_ACPI
bool tb_acpi_add_links(struct tb_nhi *nhi);

bool tb_acpi_is_native(void);
bool tb_acpi_may_tunnel_usb3(void);
bool tb_acpi_may_tunnel_dp(void);
bool tb_acpi_may_tunnel_pcie(void);
bool tb_acpi_is_xdomain_allowed(void);

int tb_acpi_init(void);
void tb_acpi_exit(void);
int tb_acpi_power_on_retimers(struct tb_port *port);
int tb_acpi_power_off_retimers(struct tb_port *port);
#else
static inline bool tb_acpi_add_links(struct tb_nhi *nhi) { return false; }
```

[`tb_acpi_add_links()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1524) in that build is an inline returning false, and the declarations above it are the driver's other ACPI helpers, each given its own inline default further down the same block. A kernel built this way behaves as a kernel whose firmware carries no reference does. No link is created, the earlier helper decides the outcome on its own, and the warning in the probe reaches the log whenever it too returns false.

The bracket around the link creation carries a second build condition, [`CONFIG_PM`](https://elixir.bootlin.com/linux/v7.2/source/kernel/power/Kconfig#L217). Without it [`pm_runtime_get_sync()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L511) and [`pm_runtime_put()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L549) reach the inline stubs [`__pm_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L269) and [`__pm_runtime_idle()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L261), which return without touching the usage counter, so the bracket has no effect and the link's two runtime-PM flags have nothing to act on. The link is still created and still appears in sysfs, so the record of the dependency survives a build that cannot act on it.
