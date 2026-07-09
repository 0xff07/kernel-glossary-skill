# Subsystem Map

Each entry maps a subsystem to its tag, output directory, primary kernel source paths, specification name(s), and the heading to use for section 6. All entries live in this one file; a page-production task reads exactly the one entry it needs.

Entry schema (every entry carries these five fields):

- `tag`: the subsystem tag, used when composing the commit message for the page
- `dir`: the output directory under `docs/`
- `kernel_paths`: directories in the kernel source tree to search first
- `spec`: specification name(s) for the SPECIFICATIONS section
- `section6_heading`: the heading to use for section 6 (REGISTERS, METHODS, PRIMITIVES, INTERFACES, or omit)

Each entry's heading is the subsystem name and its `dir` field maps one-to-one onto its output directory under `docs/`. When adding a subsystem, add an entry with all five fields and a row in the table below.

| subsystem | dir | tag |
|---|---|---|
| PCIe | `pci` | `pcie` |
| xHCI | `xhci` | `usb` (secondary: `xhci`) |
| USB | `usb` | `usb` |
| ACPI | `acpi` | `acpi` |
| USB4 | `usb4` | `usb4` |
| V4L2 | `v4l2` | `v4l2` |
| DisplayPort | `dp` | `display-port` |
| DRM | `drm` | `graphics` |
| Sound | `sound` | `sound` |
| Power Management | `pm` | `power-management` |
| Concurrency | `concurrency` | `concurrency` |
| Drivers | `drivers` | `drivers` |
| Debugging | `debug` | `debugging` |
| ARM64 | `arm64` | `arm64` |
| Workflows | `workflows` | `workflows` |
| Networking | `net` | `networking` |
| Ethernet | `ethernet` | `ethernet` |
| Bluetooth | `bluetooth` | `bluetooth` |
| Memory Management | `mm` | `mm` |

## PCIe

- tag: `pcie`
- dir: `pci`
- kernel_paths: `drivers/pci/`, `include/linux/pci.h`, `include/uapi/linux/pci_regs.h`
- spec: PCI Express Base Specification
- section6_heading: REGISTERS

## xHCI

- tag: `usb` (secondary: `xhci`)
- dir: `xhci`
- kernel_paths: `drivers/usb/host/xhci*`, `include/linux/usb/hcd.h`
- spec: xHCI (eXtensible Host Controller Interface) Specification
- section6_heading: REGISTERS

## USB

- tag: `usb`
- dir: `usb`
- kernel_paths: `drivers/usb/core/`, `drivers/usb/common/`, `include/linux/usb.h`, `include/linux/usb/ch9.h`
- spec: USB 2.0 Specification, USB 3.2 Specification
- section6_heading: REGISTERS

## ACPI

- tag: `acpi`
- dir: `acpi`
- kernel_paths: `drivers/acpi/`, `include/acpi/`, `include/linux/acpi.h`
- spec: ACPI Specification
- section6_heading: METHODS

## USB4

- tag: `usb4`
- dir: `usb4`
- kernel_paths: `drivers/thunderbolt/`, `include/linux/thunderbolt.h`
- spec: USB4 Specification, Thunderbolt 3/4 Specification
- section6_heading: REGISTERS

## V4L2

- tag: `v4l2`
- dir: `v4l2`
- kernel_paths: `drivers/media/`, `include/media/`, `include/uapi/linux/videodev2.h`
- spec: (none; refer to V4L2 subsystem documentation)
- section6_heading: INTERFACES

## DisplayPort

- tag: `display-port`
- dir: `dp`
- kernel_paths: `drivers/gpu/drm/display/drm_dp*`, `include/drm/display/drm_dp*`
- spec: VESA DisplayPort Standard, VESA eDP Standard
- section6_heading: REGISTERS

## DRM

- tag: `graphics`
- dir: `drm`
- kernel_paths: `drivers/gpu/drm/`, `include/drm/`, `include/uapi/drm/`
- spec: (none; refer to DRM subsystem documentation)
- section6_heading: INTERFACES

## Sound

- tag: `sound`
- dir: `sound`
- kernel_paths: `sound/`, `include/sound/`, `include/uapi/sound/`
- spec: Intel High Definition Audio Specification, USB Audio Class Specification
- section6_heading: REGISTERS

## Power Management

- tag: `power-management`
- dir: `pm`
- kernel_paths: `drivers/base/power/`, `kernel/power/`, `include/linux/pm.h`, `include/linux/suspend.h`
- spec: ACPI Specification (power management chapters), PCI PM Specification
- section6_heading: none

## Concurrency

- tag: `concurrency`
- dir: `concurrency`
- kernel_paths: `kernel/locking/`, `include/linux/spinlock.h`, `include/linux/mutex.h`, `include/linux/rwsem.h`
- spec: (none)
- section6_heading: PRIMITIVES

## Drivers

- tag: `drivers`
- dir: `drivers`
- kernel_paths: `drivers/base/`, `include/linux/device.h`, `include/linux/platform_device.h`
- spec: (none)
- section6_heading: INTERFACES

## Debugging

- tag: `debugging`
- dir: `debug`
- kernel_paths: `kernel/trace/`, `lib/dynamic_debug.c`, `include/linux/ftrace.h`
- spec: (none)
- section6_heading: none

## ARM64

- tag: `arm64`
- dir: `arm64`
- kernel_paths: `arch/arm64/`, `include/asm-generic/`
- spec: Arm Architecture Reference Manual (Arm ARM)
- section6_heading: REGISTERS

## Workflows

- tag: `workflows`
- dir: `workflows`
- kernel_paths: (none; workflow pages describe development processes)
- spec: (none)
- section6_heading: none

## Networking

- tag: `networking`
- dir: `net`
- kernel_paths: `net/core/`, `net/netfilter/`, `net/sched/`, `net/dsa/`, `net/bridge/`, `net/switchdev/`, `net/netlink/`, `drivers/net/`, `include/linux/netdevice.h`, `include/linux/skbuff.h`, `include/net/`
- spec: (none; linux network subsystem constructs)
- section6_heading: INTERFACES

## Ethernet

- tag: `ethernet`
- dir: `ethernet`
- kernel_paths: `drivers/net/ethernet/`, `drivers/net/phy/`, `drivers/net/mdio/`, `net/ethtool/`, `include/linux/etherdevice.h`, `include/linux/ethtool.h`, `include/linux/phylink.h`, `include/linux/phy.h`, `include/linux/mdio.h`, `include/linux/mii.h`, `include/linux/of_mdio.h`, `include/uapi/linux/ethtool.h`, `include/uapi/linux/ethtool_netlink.h`, `include/uapi/linux/mii.h`
- spec: IEEE 802.3 (Ethernet)
- section6_heading: REGISTERS

## Bluetooth

- tag: `bluetooth`
- dir: `bluetooth`
- kernel_paths: `net/bluetooth/`, `drivers/bluetooth/`, `include/net/bluetooth/`
- spec: Bluetooth Core Specification
- section6_heading: INTERFACES

## Memory Management

- tag: `mm`
- dir: `mm`
- kernel_paths: `mm/`, `include/linux/mm.h`, `include/linux/mm_types.h`, `include/linux/mm_types_task.h`, `include/linux/mmzone.h`, `include/linux/gfp.h`, `include/linux/gfp_types.h`, `include/linux/page-flags.h`, `include/linux/page-flags-layout.h`, `include/linux/page_ref.h`, `include/linux/pageblock-flags.h`, `include/linux/page-isolation.h`, `include/linux/pagemap.h`, `include/linux/pfn.h`, `include/linux/memblock.h`, `include/linux/memremap.h`, `include/linux/slab.h`, `include/linux/nodemask.h`, `include/linux/numa.h`, `include/linux/percpu.h`, `include/linux/mmdebug.h`, `include/linux/poison.h`, `include/linux/highmem-internal.h`, `include/linux/hugetlb.h`, `include/linux/rmap.h`, `include/linux/sched/mm.h`, `include/vdso/page.h`, `include/asm-generic/memory_model.h`, `include/asm-generic/pgalloc.h`, `include/net/page_pool/types.h`, `arch/x86/include/asm/page.h`, `arch/x86/include/asm/page_types.h`, `arch/x86/include/asm/sparsemem.h`
- spec: (none)
- section6_heading: none
