# USB3 device power management

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A SuperSpeed link between a device and the hub port above it can be parked while neither end has anything to send, and USB defines two depths of parking, a shallow one the link leaves quickly and a deeper one that costs more to leave. The saving is bought with time. Before the next packet can cross a parked link the link has to be brought back to full operation, and so does every link between that device and the host controller, which means the controller cannot schedule a transfer for the device without knowing what waking the whole path will cost. USB3 device power management is the arrangement that settles two numbers for one device. The first is how long the link may be idle before it is parked, and it is an idle timeout the parent hub counts down. The second is how long waking the path will take, and it is a field of the device's context in host memory, which the controller reads when it builds the bus schedule. The USB core decides when either number should change. The xHCI driver computes both from the endpoints the device has open and the exit latencies the device reported at enumeration, returns the first to the core to be written into the hub, and installs the second itself with a command on the controller's command ring.

Two driver functions carry the whole flow, and the USB core reaches both through the host-controller function pointer struct. [`xhci_enable_usb3_lpm_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5167) computes the idle timeout for one link state, updates the exit latency the controller knows about, and returns the timeout for the core to program into the hub. [`xhci_disable_usb3_lpm_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5209) recomputes the exit latency without that link state and installs the smaller value. Everything between them is arithmetic over one device's endpoint descriptors and one Evaluate Context command. The deeper suspend state, U3, is reached by a different request entirely and belongs to the port machinery rather than to this page.

```
    The four SuperSpeed link states and what moves a link between them
    ─────────────────────────────────────────────────────────────────

                    ┌──────────────────────────────────┐
                    │ U0                               │
                    │ link running, packets cross      │
                    │ in both directions               │
                    └──┬────────────┬────────────┬─────┘
                       │            │            │
      parent hub's     │            │            │  SetPortFeature
      U1 idle timer,   │            │            │  (LINK_STATE, U3)
      or the device    │            │            │  from the USB core
                       │            │            │
      parent hub's     │            │            │
      U2 idle timer,   │            │            │
      or the device    │            │            │
                       ▼            ▼            ▼
        ┌──────────────────┐ ┌────────────┐ ┌──────────────────┐
        │ U1               │ │ U2         │ │ U3               │
        │ shallow park,    │ │ deeper     │ │ device suspended │
        │ quick to leave   │ │ park       │ │                  │
        └────────┬─────────┘ └─────┬──────┘ └────────┬─────────┘
                 │                 │                 │
                 └────────┬────────┘                 │
                          │                          │
             traffic at   │                          │  SetPortFeature
             either end,  │                          │  (LINK_STATE, U0),
             costing the  │                          │  or a device
             path's exit  │                          │  remote wake
             latency      ▼                          ▼
                    ┌──────────────────────────────────┐
                    │ back to U0                       │
                    └──────────────────────────────────┘

    U1 and U2 are entered on a timer this page computes, or by the
    device once the core has permitted device-initiated entry.
    U3 is entered only on an explicit request from the USB core.
```

## SUMMARY

Link power management for a SuperSpeed device is a negotiation between three parties, and the kernel writes one value into each of two of them. The device reports, in its BOS descriptor, how long its own link takes to leave U1 and U2. From that the USB core derives three latencies for the whole path and sends two of them back to the device with a Set SEL request. The parent hub holds a per-port idle timer for each of U1 and U2, and the xHCI driver computes the timeout that timer counts, and the core writes it into the hub with a SetPortFeature request. The host controller holds a Max Exit Latency for the device in its slot context, and it is the driver that writes that one, because the controller uses it to leave room in the bus schedule for a link that has to wake before a transfer can start. Enabling a link state means both writes succeed, and the state counts as enabled only once the controller has been told the new latency and the hub has been given the new timeout.

The four states a SuperSpeed link moves through are named by [`enum usb3_link_state`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1236), and only two of them are this page's subject.

| state | what the link is doing | entered by | left by | construct |
|---|---|---|---|---|
| U0 | running, packets cross in both directions | leaving U1, U2 or U3 | the entries below | [`USB3_LPM_U0`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1237), [`XDEV_U0`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-port.h#L18) |
| U1 | shallow park, quick to leave | the parent hub's U1 idle timer, or the device once [`usb_set_device_initiated_lpm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4171) has permitted it | traffic at either end, costing the path's exit latency | [`USB3_LPM_U1`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1238), [`XDEV_U1`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-port.h#L19) |
| U2 | deeper park | the parent hub's U2 idle timer, or the device once [`usb_set_device_initiated_lpm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4171) has permitted it | traffic at either end, costing the path's exit latency | [`USB3_LPM_U2`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1239), [`XDEV_U2`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-port.h#L20) |
| U3 | device suspended | a SetPortFeature request naming [`USB_PORT_FEAT_LINK_STATE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L90), issued by [`hub_set_port_link_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L1007) | the same request naming U0, or a device remote wake | [`USB3_LPM_U3`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1240), [`XDEV_U3`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-port.h#L21) |

The enable path runs in one direction. [`usb_enable_lpm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4503) calls [`usb_enable_link_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4327) once for U1 and once for U2 with [`hcd->bandwidth_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L185) held, and each call asks the host controller first. [`xhci_enable_usb3_lpm_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5167) checks three preconditions, runs [`xhci_calculate_lpm_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5059) over every endpoint the device has open, converts the largest candidate into the hub's encoding, recomputes the exit latency with [`calculate_max_exit_latency()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5123), and installs that latency with [`xhci_change_max_exit_latency()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4517). Only then does [`usb_set_lpm_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4225) send the timeout to the hub. The disable path reverses the order, clearing the hub's timeout first and shrinking the controller's exit latency after, so that at no moment does the hub allow a link state whose wake-up cost the controller has not budgeted.

## SPECIFICATIONS

- xHCI (eXtensible Host Controller Interface) Specification, section 6.2.1.1: Slot Context. Cited in the kerneldoc above [`struct xhci_slot_ctx`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L342), which names the Max Exit Latency field this page writes.
- xHCI Specification, section 5.4.8: Host Controller USB Port Register Set. Cited in the kerneldoc above [`struct xhci_port_regs`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L84), the register quad whose [`portpmsc`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L86) word carries the U1 and U2 timeouts on a root-hub port.
- USB 3.0 Specification, section 9.4.12: Set SEL. Cited in the comment above [`pel`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L560) in [`struct usb3_lpm_parameters`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L547).
- USB 3.0 Specification, Appendix C, section C.1.5.1: the four components of the System Exit Latency, cited in the comment above [`usb_set_lpm_sel()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L314).
- USB 3.0 Specification, Appendix C, section C.2.2.2, with hub-chapter sections 10.4.2.4 and 10.4.2.5: the port-to-port exit-latency delays, cited in the comment inside [`usb_set_lpm_parameters()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L337).
- USB 3.1 Specification, sections C.1.5.2 and C.2.2.1, and C.1.5.2.4: the terms summed into the Maximum Exit Latency, cited in the comments inside [`usb_set_lpm_mel()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L219).
- USB 3.2 Specification, section 9.4.9: the condition under which a device may initiate a transition, cited in the comment above [`usb_device_may_initiate_lpm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4273).
- USB 3.0 Specification, Table 10-7: the port feature selectors, cited in the comment above [`USB_PORT_FEAT_U1_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L91) in [`include/uapi/linux/usb/ch11.h`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h).

## LINUX KERNEL

### The two host-controller entry points (drivers/usb/host/xhci.c)

- [`'\<xhci_enable_usb3_lpm_timeout\>':'drivers/usb/host/xhci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5167): check the preconditions, compute the hub-encoded timeout, install the new exit latency, and return the timeout to the USB core
- [`'\<xhci_disable_usb3_lpm_timeout\>':'drivers/usb/host/xhci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5209): recompute the exit latency with the named link state removed and install it

### The per-endpoint timeout engine (drivers/usb/host/xhci.c)

- [`'\<xhci_calculate_lpm_timeout\>':'drivers/usb/host/xhci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5059): scan endpoint zero and every interface's current alternate setting, keeping the largest candidate timeout
- [`'\<xhci_update_timeout_for_interface\>':'drivers/usb/host/xhci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5014): run one alternate setting's endpoint descriptors through the per-endpoint step
- [`'\<xhci_update_timeout_for_endpoint\>':'drivers/usb/host/xhci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4989): raise the running maximum, or return `-E2BIG` when this endpoint forces the link state off entirely
- [`'\<xhci_call_host_update_timeout_for_endpoint\>':'drivers/usb/host/xhci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4975): pick the U1 or the U2 calculation from the requested [`enum usb3_link_state`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1236)
- [`'\<xhci_calculate_u1_timeout\>':'drivers/usb/host/xhci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4880): reject U1 for a periodic endpoint whose service interval is shorter than the exit latency, then encode the timeout in one-microsecond units against [`USB3_LPM_U1_MAX_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1262)
- [`'\<xhci_calculate_u2_timeout\>':'drivers/usb/host/xhci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4944): the same shape for U2, encoding in 256-microsecond units against [`USB3_LPM_U2_MAX_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1263)
- [`'\<xhci_get_timeout_no_hub_lpm\>':'drivers/usb/host/xhci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4792): the fallback when the hub cannot hold the timeout, returning [`USB3_LPM_DEVICE_INITIATED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1264) if the device's own latencies fit their fields
- [`'\<xhci_service_interval_to_ns\>':'drivers/usb/host/xhci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4786): turn an endpoint descriptor's [`bInterval`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L422) into nanoseconds
- [`'\<xhci_check_tier_policy\>':'drivers/usb/host/xhci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5030): count the hub tiers between the device and the root hub and refuse the link state past a host-specific depth

### The exit latency and the command that installs it (xhci.c, xhci.h, xhci-mem.c)

- [`'\<calculate_max_exit_latency\>':'drivers/usb/host/xhci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5123): take the larger of the U1 and U2 exit latencies that will be live after this change, in microseconds, and refuse a value past [`MAX_EXIT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L371)
- [`'\<xhci_change_max_exit_latency\>':'drivers/usb/host/xhci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4517): issue an Evaluate Context command that rewrites the slot context's Max Exit Latency, and cache the installed value
- [`'MAX_EXIT':'drivers/usb/host/xhci.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L371): the 16-bit Max Exit Latency field mask, `0xffff`, and the ceiling the calculation is checked against
- [`'\<struct xhci_slot_ctx\>':'drivers/usb/host/xhci.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L342): the per-device slot context whose [`dev_info2`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L344) word carries the Max Exit Latency
- [`'SLOT_FLAG':'drivers/usb/host/xhci.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L366): the add-flag bit that tells the controller to evaluate the slot context in the input context
- [`'\<struct xhci_input_control_ctx\>':'drivers/usb/host/xhci.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L513): the [`add_flags`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L515) and [`drop_flags`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L514) header of an input context
- [`'\<xhci_slot_copy\>':'drivers/usb/host/xhci-mem.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L1626): copy the output slot context into the input slot context so only the changed field differs
- [`'\<xhci_alloc_command_with_ctx\>':'drivers/usb/host/xhci-mem.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L1758): allocate a command with its own input context and completion
- [`'\<xhci_configure_endpoint\>':'drivers/usb/host/xhci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L2960): queue the Evaluate Context command, ring the doorbell, wait for the completion, and translate the completion code
- [`'\<xhci_evaluate_context_result\>':'drivers/usb/host/xhci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L2170): map each Evaluate Context completion code onto an error number
- [`'COMP_MAX_EXIT_LATENCY_TOO_LARGE_ERROR':'drivers/usb/host/xhci.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L861): completion code 29, the controller's own refusal of a latency it cannot accommodate

### The latency values the calculation reads (include/linux/usb.h, include/uapi/linux/usb/ch9.h)

- [`'\<struct usb3_lpm_parameters\>':'include/linux/usb.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L547): the per-state latency record holding [`mel`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L554), [`pel`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L560), [`sel`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L570) and [`timeout`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L576), instantiated twice per device as [`u1_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L739) and [`u2_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L740)
- [`'\<enum usb3_link_state\>':'include/uapi/linux/usb/ch9.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1236): the four link states, and the argument every function on this page is parameterized by
- [`'USB3_LPM_U1_MAX_TIMEOUT':'include/uapi/linux/usb/ch9.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1262): `0x7F`, the largest hub-initiated U1 timeout the hub protocol can carry
- [`'USB3_LPM_U2_MAX_TIMEOUT':'include/uapi/linux/usb/ch9.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1263): `0xFE`, the same limit for U2, in 256-microsecond units
- [`'USB3_LPM_DEVICE_INITIATED':'include/uapi/linux/usb/ch9.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1264): `0xFF`, the value that tells the hub to accept a transition it will never start itself
- [`'USB3_LPM_MAX_U1_SEL_PEL':'include/uapi/linux/usb/ch9.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1278): `0xFF`, the widest U1 SEL or PEL the Set SEL request can carry
- [`'USB3_LPM_MAX_U2_SEL_PEL':'include/uapi/linux/usb/ch9.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1279): `0xFFFF`, the same width for U2

### The USB core seam that drives both hooks (drivers/usb/core/hub.c, include/linux/usb/hcd.h)

- [`'\<usb_enable_lpm\>':'drivers/usb/core/hub.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4503): drop the per-device disable count and, at zero, enable each permitted link state
- [`'\<usb_disable_lpm\>':'drivers/usb/core/hub.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4440): raise the disable count and turn both link states off
- [`'\<usb_enable_link_state\>':'drivers/usb/core/hub.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4327): ask the host controller for a timeout, then program it into the hub
- [`'\<usb_disable_link_state\>':'drivers/usb/core/hub.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4398): zero the hub timeout, then tell the host controller
- [`'\<usb_set_lpm_timeout\>':'drivers/usb/core/hub.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4225): send the SetPortFeature request that writes one link state's idle timeout into the parent hub
- [`'\<usb_set_lpm_mel\>':'drivers/usb/core/hub.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L219): accumulate the path's Maximum Exit Latency from the parent's value, the slower of the two link partners, and the hub's decode and transmission delays
- [`'\<usb_req_set_sel\>':'drivers/usb/core/hub.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4106): send the computed SEL and PEL to the device, and set [`lpm_devinit_allow`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L703) when they fit their fields
- [`'\<usb_set_device_initiated_lpm\>':'drivers/usb/core/hub.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4171): set or clear the device feature that lets the device start a transition on its own
- [`'bandwidth_mutex':'include/linux/usb/hcd.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L185): the per-bus mutex every caller of [`usb_enable_lpm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4503) and [`usb_disable_lpm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4440) holds

### Per-port and per-device policy (xhci-pci.c, xhci.h, core/port.c, core/hub.h, include/linux/usb.h)

- [`'\<xhci_find_lpm_incapable_ports\>':'drivers/usb/host/xhci-pci.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-pci.c#L532): ask firmware, once per USB3 root hub, which of its ports must never use U1 or U2
- [`'\<struct xhci_port\>':'drivers/usb/host/xhci.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1474): the driver's per-port record, whose [`lpm_incapable`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1480) bit holds that answer
- [`'\<struct usb_port\>':'drivers/usb/core/hub.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.h#L101): the USB core's per-port device, carrying [`usb3_lpm_u1_permit`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.h#L119) and [`usb3_lpm_u2_permit`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.h#L120)
- [`'\<usb3_lpm_permit_store\>':'drivers/usb/core/port.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/port.c#L262): the sysfs write handler that sets those two bits and re-runs the enable path on the attached device
- [`'disable_hub_initiated_lpm':'include/linux/usb.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L1271): the interface-driver flag that forces hub-initiated entry off while the driver is bound
- [`'lpm_disable_count':'include/linux/usb.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L741): the per-device reference count that keeps link power management off while any caller needs it off

### The port register fields the timeout reaches (drivers/usb/host/xhci-port.h)

- [`'PORT_U1_TIMEOUT':'drivers/usb/host/xhci-port.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-port.h#L128): bits 7 to 0 of a SuperSpeed port's PORTPMSC word, the U1 inactivity timer value
- [`'PORT_U2_TIMEOUT':'drivers/usb/host/xhci-port.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-port.h#L131): bits 15 to 8 of the same word, the U2 inactivity timer value

## KERNEL DOCUMENTATION

- [`Documentation/driver-api/usb/power-management.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/usb/power-management.rst): the "xHCI hardware link PM" section describes the U1 and U2 states from the user's side and names the two sysfs files that report whether each is enabled
- [`Documentation/ABI/testing/sysfs-bus-usb`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-bus-usb): the stable definitions of `power/usb3_hardware_lpm_u1`, `power/usb3_hardware_lpm_u2` and the per-port `usb3_lpm_permit` file this page's policy inputs are written through
- [`Documentation/driver-api/usb/usb.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/usb/usb.rst): the host-controller driver API and the bus-bandwidth model the Max Exit Latency is a reservation against

## OTHER SOURCES

- [xhci: Add a flag to disable USB3 lpm on a xhci root port level. (commit 0522b9a16530)](https://lore.kernel.org/r/20230116142216.1141605-6-mathias.nyman@linux.intel.com)
- [usb: acpi: add helper to check port lpm capability using acpi _DSM (commit cd702d18c882)](https://lore.kernel.org/r/20230116142216.1141605-7-mathias.nyman@linux.intel.com)
- [xhci: Detect lpm incapable xHC USB3 roothub ports from ACPI tables (commit 74622f0a81d0)](https://lore.kernel.org/r/20230116142216.1141605-8-mathias.nyman@linux.intel.com)
- [xhci: Prevent device initiated U1/U2 link pm if exit latency is too long (commit cd9d9491e835)](https://lore.kernel.org/r/1570190373-30684-3-git-send-email-mathias.nyman@linux.intel.com)
- [xhci: Check all endpoints for LPM timeout (commit d500c63f80f2)](https://lore.kernel.org/r/1570190373-30684-4-git-send-email-mathias.nyman@linux.intel.com)
- [xhci: Allocate separate command structures for each LPM command (commit 5c2a380a5aa8)](https://lore.kernel.org/r/20220216095153.1303105-7-mathias.nyman@linux.intel.com)
- [xhci: show correct U1 and U2 timeout values in debug messages (commit b020761e8cbf)](https://lore.kernel.org/r/20250306144954.3507700-2-mathias.nyman@linux.intel.com)

## REGISTERS

The register surface of this flow is thin, because the value the controller acts on is a context field rather than a register field. One register is written on the way out, and only when the device's parent happens to be the root hub. That register is PORTPMSC, the second word of a port's register quad, whose low sixteen bits on a SuperSpeed port hold the two inactivity timer values. The header names them with a shift-and-mask macro and a matching mask, and the comment above them gives the unit and the meaning of the all-ones value:

```c
/* drivers/usb/host/xhci-port.h:124 */
/* Port Power Management Status and Control - port_power_base bitmasks */
/* Inactivity timer value for transitions into U1, in microseconds.
 * Timeout can be up to 127us.  0xFF means an infinite timeout.
 */
#define PORT_U1_TIMEOUT(p)	((p) & 0xff)
#define PORT_U1_TIMEOUT_MASK	0xff
/* Inactivity timer value for transitions into U2 */
#define PORT_U2_TIMEOUT(p)	(((p) & 0xff) << 8)
#define PORT_U2_TIMEOUT_MASK	(0xff << 8)
/* Bits 24:31 for port testing */
```

[`PORT_U1_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-port.h#L128) places a value in bits 7 to 0 and [`PORT_U1_TIMEOUT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-port.h#L129) clears them; [`PORT_U2_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-port.h#L131) and [`PORT_U2_TIMEOUT_MASK`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-port.h#L132) do the same for bits 15 to 8. According to the comment above them the U1 field is an "Inactivity timer value for transitions into U1, in microseconds", that "Timeout can be up to 127us", and that "0xFF means an infinite timeout", the three facts the encoding step in [`xhci_calculate_u1_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4880) is built around. The figure plots the word to scale.

```
    PORTPMSC on a SuperSpeed root-hub port, to scale
    ────────────────────────────────────────────────
    (a middle dot marks a bit this flow does not write)

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬───────────────┬───────────────┐
    DW1   │·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│·│  U2 Timeout   │  U1 Timeout   │
          └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴───────┬───────┴───────┬───────┘
                                                  │               │
                                                  │               └─ bits 7:0
                                                  │                  1us units
                                                  └─ bits 15:8
                                                     256us units

    The same word on a USB 2.0 port carries an entirely different set
    of fields, so the two layouts share only their address arithmetic.
```

The two fields hold different units, which is why the two calculation functions divide by different numbers before their ceiling check. A U1 value counts microseconds directly, so the largest value the field can express, [`USB3_LPM_U1_MAX_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1262), is 127 microseconds. A U2 value counts units of 256 microseconds, so [`USB3_LPM_U2_MAX_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1263) is 254 units, which the header's own comment works out as 65.024 milliseconds.

| field | bits | unit | macro | written at |
|---|---|---|---|---|
| U1 Timeout | 7:0 | 1 microsecond | [`PORT_U1_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-port.h#L128) | [`drivers/usb/host/xhci-hub.c:1525`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L1525) |
| U2 Timeout | 15:8 | 256 microseconds | [`PORT_U2_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-port.h#L131) | [`drivers/usb/host/xhci-hub.c:1533`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L1533) |

Neither field is written by any function on this page. They are written by the root hub's control-endpoint emulation, when the SetPortFeature request the USB core sends on the device's behalf happens to land on a root-hub port. Both cases refuse the request on a USB 2.0 root hub and then perform the same read-modify-write:

```c
/* drivers/usb/host/xhci-hub.c:1520 in xhci_hub_control() */
		case USB_PORT_FEAT_U1_TIMEOUT:
			if (hcd->speed < HCD_USB3)
				goto error;
			temp = readl(&port->port_reg->portpmsc);
			temp &= ~PORT_U1_TIMEOUT_MASK;
			temp |= PORT_U1_TIMEOUT(timeout);
			writel(temp, &port->port_reg->portpmsc);
			break;
		case USB_PORT_FEAT_U2_TIMEOUT:
			if (hcd->speed < HCD_USB3)
				goto error;
			temp = readl(&port->port_reg->portpmsc);
			temp &= ~PORT_U2_TIMEOUT_MASK;
			temp |= PORT_U2_TIMEOUT(timeout);
			writel(temp, &port->port_reg->portpmsc);
			break;
```

Each case reads [`port->port_reg->portpmsc`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L86), clears its own field with the mask, places the requested `timeout` value in it, and writes the word back. The value in `timeout` came out of the request's `wIndex` field, which is where [`usb_set_lpm_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4225) put the number this page's engine computed. When the device's parent is an external hub instead, the same request reaches that hub over the wire and this code never runs, which is why the register is a detail of one topology rather than the mechanism.

The one register field this flow reads is the port link state, PLS in PORTSC, and it reads it only indirectly, through the port status the root hub reports back to the USB core, which carries the link state and lets the core decide whether the device is where it thinks it is. The PLS encodings [`XDEV_U0`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-port.h#L18) through [`XDEV_U3`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-port.h#L21) name exactly the four states this page's model is built on:

```c
/* drivers/usb/host/xhci-port.h:17 */
#define PORT_PLS_MASK	(0xf << 5)
#define XDEV_U0		(0x0 << 5)
#define XDEV_U1		(0x1 << 5)
#define XDEV_U2		(0x2 << 5)
#define XDEV_U3		(0x3 << 5)
```

[`PORT_PLS_MASK`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-port.h#L17) selects bits 8 to 5, and the four state constants are already shifted into position, so a read of PORTSC masked with it compares directly against them. Writing that field is a different mechanism with a write strobe of its own, and `ports/port-registers-usb3.md` carries the full PORTSC and PORTPMSC layouts along with the compliance-mode bits this page has no use for.

## DETAILS

### The USB core asks the host controller before it asks the hub

Enabling a link state changes what the bus schedule has to allow for, so the USB core treats it as a bandwidth change and holds the per-bus [`bandwidth_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L185) across it. The mutex is a pointer shared by the two root hubs of one controller, and its comment lists the four moments it protects:

```c
/* include/linux/usb/hcd.h:173 */
	/* bandwidth_mutex should be taken before adding or removing
	 * any new bus bandwidth constraints:
	 *   1. Before adding a configuration for a new device.
	 *   2. Before removing the configuration to put the device into
	 *      the addressed state.
	 *   3. Before selecting a different configuration.
	 *   4. Before selecting an alternate interface setting.
	 *
	 * bandwidth_mutex should be dropped after a successful control message
	 * to the device, or resetting the bandwidth after a failed attempt.
	 */
	struct mutex		*address0_mutex;
	struct mutex		*bandwidth_mutex;
```

[`address0_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L184) is a different serializer for a different problem; [`bandwidth_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L185) is the one this page's callers hold. Adding a configuration, removing one, choosing a different one and choosing a different alternate setting all change the endpoint set the timeout calculation reads, so link power management has to be off across each of them and recomputed after.

The two hooks the core calls are members of the host-controller function pointer struct, and their comments say what each returns:

```c
/* include/linux/usb/hcd.h:391 */
	/* USB 3.0 Link Power Management */
		/* Returns the USB3 hub-encoded value for the U1/U2 timeout. */
	int	(*enable_usb3_lpm_timeout)(struct usb_hcd *,
			struct usb_device *, enum usb3_link_state state);
		/* The xHCI host controller can still fail the command to
		 * disable the LPM timeouts, so this can return an error code.
		 */
	int	(*disable_usb3_lpm_timeout)(struct usb_hcd *,
			struct usb_device *, enum usb3_link_state state);
```

Both declarations name the same three parameters, the host controller, the device and the link state, so one state of one device is the unit either hook operates on, and a caller that needs both states enabled makes two calls.

Both hooks take the link state as their third argument, and the enumeration that supplies it is the one the USB specification's own state names come from:

```c
/* include/uapi/linux/usb/ch9.h:1236 */
enum usb3_link_state {
	USB3_LPM_U0 = 0,
	USB3_LPM_U1,
	USB3_LPM_U2,
	USB3_LPM_U3
};
```

[`USB3_LPM_U0`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1237) is the running state and is never passed to either hook; [`USB3_LPM_U1`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1238) and [`USB3_LPM_U2`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1239) are the two this page computes for; [`USB3_LPM_U3`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1240) is accepted by neither and is reached by the port request the closing sections describe. The values are consecutive from zero, so the switch statements that dispatch on them compile to jump tables.

[`enable_usb3_lpm_timeout`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L393) returns a hub-encoded timeout value rather than a plain error, so the core has to distinguish three outcomes from one integer, a positive value to program, zero meaning the controller declines this link state, and a negative error. [`disable_usb3_lpm_timeout`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L398) returns only success or failure, and the comment above it warns that the failure is real, because turning a link state off still means issuing a command to the controller. The xHCI driver fills both members in its own template:

```c
/* drivers/usb/host/xhci.c:5620 */
	/*
	 * call back when device connected and addressed
	 */
	.update_device =        xhci_update_device,
	.set_usb2_hw_lpm =	xhci_set_usb2_hardware_lpm,
	.enable_usb3_lpm_timeout =	xhci_enable_usb3_lpm_timeout,
	.disable_usb3_lpm_timeout =	xhci_disable_usb3_lpm_timeout,
	.find_raw_port_number =	xhci_find_raw_port_number,
	.clear_tt_buffer_complete = xhci_clear_tt_buffer_complete,
};
```

The two entries at [`drivers/usb/host/xhci.c:5625`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5625) and [`drivers/usb/host/xhci.c:5626`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5626) are the only route into this page's code. [`update_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L389) beside them runs whenever a device is addressed, and [`set_usb2_hw_lpm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L390) is the USB 2.0 counterpart whose mechanism the closing section of this page contrasts with.

[`usb_enable_link_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4327) is the core function that calls the enable hook. It refuses outright for a device that reported no exit latency at all for the state being enabled, for the reason its comment gives, and then asks the controller before it touches the hub:

```c
/* drivers/usb/core/hub.c:4327 */
static int usb_enable_link_state(struct usb_hcd *hcd, struct usb_device *udev,
		enum usb3_link_state state)
{
	int timeout;
	__u8 u1_mel;
	__le16 u2_mel;

	/* Skip if the device BOS descriptor couldn't be read */
	if (!udev->bos)
		return -EINVAL;

	u1_mel = udev->bos->ss_cap->bU1devExitLat;
	u2_mel = udev->bos->ss_cap->bU2DevExitLat;

	/* If the device says it doesn't have *any* exit latency to come out of
	 * U1 or U2, it's probably lying.  Assume it doesn't implement that link
	 * state.
	 */
	if ((state == USB3_LPM_U1 && u1_mel == 0) ||
			(state == USB3_LPM_U2 && u2_mel == 0))
		return -EINVAL;

	/* We allow the host controller to set the U1/U2 timeout internally
	 * first, so that it can change its schedule to account for the
	 * additional latency to send data to a device in a lower power
	 * link state.
	 */
	timeout = hcd->driver->enable_usb3_lpm_timeout(hcd, udev, state);

	/* xHCI host controller doesn't want to enable this LPM state. */
	if (timeout == 0)
		return -EINVAL;

	if (timeout < 0) {
		dev_warn(&udev->dev, "Could not enable %s link state, "
				"xHCI error %i.\n", usb3_lpm_names[state],
				timeout);
		return timeout;
	}

	if (usb_set_lpm_timeout(udev, state, timeout)) {
		/* If we can't set the parent hub U1/U2 timeout,
		 * device-initiated LPM won't be allowed either, so let the xHCI
		 * host know that this link state won't be enabled.
		 */
		hcd->driver->disable_usb3_lpm_timeout(hcd, udev, state);
		return -EBUSY;
	}
```

The function takes the same three arguments the hook does, and the two exit-latency values it reads at the top come from the device's own BOS descriptor, and a zero in either is treated as a device that does not implement the state. Then [`hcd->driver->enable_usb3_lpm_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L393) runs, and the three outcomes are separated exactly as the hook's comment implies, with a returned zero giving `-EINVAL` and nothing written anywhere, a negative return logged and passed up, and a positive value going on to [`usb_set_lpm_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4225). According to the comment above the call, the controller is asked first "so that it can change its schedule to account for the additional latency to send data to a device in a lower power link state". If the hub write then fails, the controller is told to undo its side with [`hcd->driver->disable_usb3_lpm_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L398) before the function returns `-EBUSY`. Only after both writes have landed does the function record the state as enabled:

```c
/* drivers/usb/core/hub.c:4376 end of usb_enable_link_state() */
	if (state == USB3_LPM_U1)
		udev->usb3_lpm_u1_enabled = 1;
	else if (state == USB3_LPM_U2)
		udev->usb3_lpm_u2_enabled = 1;

	return 0;
}
```

[`usb3_lpm_u1_enabled`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L708) and [`usb3_lpm_u2_enabled`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L709) are single bits in [`struct usb_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L660), and they are what the two sysfs files further down this page report.

The two writes therefore happen in a fixed order, and the figure below puts them on one timeline. Read it downward. Each column is one of the three parties, each cell names the condition that party has reached at that moment, and each horizontal arrow is a value crossing from one party to the next.

```
    Enabling one link state: the controller is asked before the hub
    ──────────────────────────────────────────────────────────────
    (time runs down; each cell names the state that actor reaches)

    USB core                 │ xHCI driver           │ parent hub
    ─────────────────────────┼───────────────────────┼─────────────
    bandwidth_mutex held     │                       │
    BOS exit latencies read  │                       │
      enable hook ───────────┼─▶ endpoints scanned,  │
                             │   timeout encoded     │
                             │                       │
                             │   slot context now    │
                             │   carries the new     │
                             │   exit latency        │
      hub-encoded value ◀────┤                       │
                             │                       │
      SetPortFeature ────────┼───────────────────────┼─▶ idle timeout
                             │                       │   programmed
    state recorded enabled   │                       │
```

### Three preconditions decide whether a timeout is computed at all

Some devices can be answered before any arithmetic runs, because the controller, the topology or the platform has already ruled the link state out. [`xhci_enable_usb3_lpm_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5167) tests for those cases first and answers with [`USB3_LPM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1261) from any of three guards, each covering a different way the answer is already known:

```c
/* drivers/usb/host/xhci.c:5166 start of xhci_enable_usb3_lpm_timeout() */
/* Returns the USB3 hub-encoded value for the U1/U2 timeout. */
static int xhci_enable_usb3_lpm_timeout(struct usb_hcd *hcd,
			struct usb_device *udev, enum usb3_link_state state)
{
	struct xhci_hcd	*xhci;
	struct xhci_port *port;
	u16 hub_encoded_timeout;
	int mel;
	int ret;

	xhci = hcd_to_xhci(hcd);
	/* The LPM timeout values are pretty host-controller specific, so don't
	 * enable hub-initiated timeouts unless the vendor has provided
	 * information about their timeout algorithm.
	 */
	if (!xhci || !(xhci->quirks & XHCI_LPM_SUPPORT) ||
			!xhci->devs[udev->slot_id])
		return USB3_LPM_DISABLED;

	if (xhci_check_tier_policy(xhci, udev, state) < 0)
		return USB3_LPM_DISABLED;

	/* If connected to root port then check port can handle lpm */
	if (udev->parent && !udev->parent->parent) {
		port = xhci->usb3_rhub.ports[udev->portnum - 1];
		if (port->lpm_incapable)
			return USB3_LPM_DISABLED;
	}
```

The first guard rejects a controller whose quirk flags do not claim link power management support, and one whose slot for this device is missing from [`xhci->devs`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1554); the comment above it explains that the timeout arithmetic is host-specific and that a host whose algorithm the driver does not know gets no hub-initiated timeouts at all. The second guard is [`xhci_check_tier_policy()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5030). The third reads [`port->lpm_incapable`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1480) on the root-hub port, and it applies only to a device whose parent is the root hub, which the test `udev->parent && !udev->parent->parent` expresses.

The tier check counts how many hubs stand between the device and the controller by following the parent chain, then compares that depth against a limit:

```c
/* drivers/usb/host/xhci.c:5030 */
static int xhci_check_tier_policy(struct xhci_hcd *xhci,
		struct usb_device *udev,
		enum usb3_link_state state)
{
	struct usb_device *parent = udev->parent;
	int tier = 1; /* roothub is tier1 */

	while (parent) {
		parent = parent->parent;
		tier++;
	}

	if (xhci->quirks & XHCI_INTEL_HOST && tier > 3)
		goto fail;
	if (xhci->quirks & XHCI_ZHAOXIN_HOST && tier > 2)
		goto fail;

	return 0;
fail:
	dev_dbg(&udev->dev, "Tier policy prevents U1/U2 LPM states for devices at tier %d\n",
			tier);
	return -E2BIG;
}
```

The loop starts at 1 for the root hub and increments once per ancestor, so a device plugged directly into a root port is tier 2 and a device behind one external hub is tier 3. The two comparisons that follow are each conditional on a quirk flag, so a host that sets neither has no depth limit here at all and the function returns 0 for any tier. Where a limit does apply, exceeding it returns `-E2BIG`, which the caller turns into a flat refusal of the link state rather than a smaller timeout.

Where a device is attached in the tree decides which of the three guards can reach it, and the figure below draws the guards as places. The first guard is the controller itself, and it refuses every device outright when the quirk word does not claim link power management support or the slot for the device is missing. The second is depth, which [`xhci_check_tier_policy()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5030) counts from the root hub as tier 1 and one more per parent and compares against a limit the host sets through its quirk bits, drawn as the dashed line. The third is a root-hub port's [`lpm_incapable`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1480) bit, and it is read only for a device plugged straight into that port, so a device behind a hub on an incapable port is never tested against the bit. The guards are tried in that order and the first refusal answers the whole request, which the figure does not show and the paragraph above states.

```
    Where a device must sit for a timeout to be computed at all
    ────────────────────────────────────────────────────────────
    (tier counts from the root hub; a port's lpm_incapable bit is
     read only for the device plugged straight into that port)

    tier 1   ┌─────────────── host controller ────────────────┐
             │ guard 1: LPM support claimed, slot present     │
             │  port 0          port 1          port 2        │
             └─────┬───────────────┬───────────────┬──────────┘
                   │ lpm_incapable │ capable       │ capable
               ┌───┴───┐       ┌───┴───┐       ┌───┴───┐
    tier 2     │  dev  │       │  dev  │       │  hub  │
               └───────┘       └───────┘       └───┬───┘
               guard 3 refuses           computed  │
                                               ┌───┴───┐
    tier 3                                     │  dev  │ computed
                                               └───┬───┘
        ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┼─ ─  deepest tier
                                               ┌───┴───┐ this host permits
    tier 4                                     │  hub  │
                                               └───┬───┘
                                                   │
                                               ┌───┴───┐
    tier 5                                     │  dev  │ guard 2 refuses
                                               └───────┘
```

### Firmware can mark a root-hub port unable to use U1 or U2

Some hardware designs cannot carry U1 or U2 on a particular root-hub port even though the controller and the device both support them, and the platform describes that in its firmware tables. The driver reads the answer once, when the USB core registers the USB3 root hub, and caches it per port. The function is compiled only with [`CONFIG_ACPI`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/Kconfig#L9) set, and it is short:

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

It returns immediately unless the hub being registered is this controller's USB3 root hub, because the same callback fires for the USB 2.0 root hub and for every external hub. It then refuses a hub claiming more downstream ports than the driver's own USB3 port array holds, which would otherwise index past the end of `rhub->ports`. For each port it calls [`usb_acpi_port_lpm_incapable()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/usb-acpi.c#L59), the USB core's wrapper around a firmware device-specific method, and stores a non-negative answer into that port's [`lpm_incapable`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1480) bit. A negative return, meaning firmware said nothing, leaves the bit as it was. What the method itself evaluates is the USB core's business and this page reaches no further than that call.

The bit is one member of the driver's per-port record:

```c
/* drivers/usb/host/xhci.h:1474 */
struct xhci_port {
	struct xhci_port_regs __iomem	*port_reg;
	int			hw_portnum;
	int			hcd_portnum;
	struct xhci_hub		*rhub;
	struct xhci_port_cap	*port_cap;
	unsigned int		lpm_incapable:1;
	unsigned long		resume_timestamp;
	bool			rexit_active;
	/* Slot ID is the index of the device directly connected to the port */
	int			slot_id;
	struct completion	rexit_done;
	struct completion	u3exit_done;
};
```

[`port_reg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1475) is the port's register quad, the one whose [`portpmsc`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L86) word the REGISTERS section plots. [`hw_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1476) and [`hcd_portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1477) are the port's two numberings, flat across the controller and relative to the root hub that claimed it. [`rhub`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1478) points back at that root hub and [`port_cap`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1479) at the protocol capability that describes the port's speed. [`lpm_incapable`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1480) is the single bit this page cares about, written once from firmware and read on every enable. [`resume_timestamp`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1481), [`rexit_active`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1482), [`rexit_done`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1485) and [`u3exit_done`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1486) track a port on its way back out of a suspended or re-exiting state and belong to the resume and hot-plug paths rather than to this one, while [`slot_id`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1484) names the device directly attached to the port.

The read happens through a PCI-specific wrapper around the generic hub-update callback, so the ACPI query runs before the generic work:

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

The `!hdev->parent` test restricts the query to a root hub. Everything else about hub registration is [`xhci_update_hub_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5254)'s work, and this wrapper adds only the one call.

One bit per port carries the firmware answer, and the two moments that touch it are far apart in time. The figure below draws the port array of one USB3 root hub, with the registration query filling the cells from above and the enable path reading them from below, so the same cell serves a query made per root hub and a read made per enable request.

```
    One bit per root-hub port, written at registration, read at enable
    ─────────────────────────────────────────────────────────────────
    (a firmware answer below zero writes nothing and leaves the cell
     as the driver's memory setup left it)

    one firmware query per downstream port of this USB3 root hub
           │              │              │              │
           ▼              ▼              ▼              ▼
    ┌──────────────┬──────────────┬──────────────┬──────────────┐
    │ port 0       │ port 1       │ port 2       │ port 3       │
    │ incapable    │ capable      │ capable      │ incapable    │
    └──────┬───────┴──────────────┴──────────────┴──────┬───────┘
           │                                            │
           ▼                                            ▼
    a device on this port is answered USB3_LPM_DISABLED before any
    arithmetic runs for it
```

### The engine scans every open endpoint and keeps the largest timeout

A device may have many endpoints open at once and the hub holds only one idle timeout for it, so the timeout each endpoint would prefer has to be reduced to a single number. [`xhci_calculate_lpm_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5059) performs that reduction for one device and one link state. It starts from [`USB3_LPM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1261) and raises it, and it begins with the control endpoint that every device has:

```c
/* drivers/usb/host/xhci.c:5054 */
/* Returns the U1 or U2 timeout that should be enabled.
 * If the tier check or timeout setting functions return with a non-zero exit
 * code, that means the timeout value has been finalized and we shouldn't look
 * at any more endpoints.
 */
static u16 xhci_calculate_lpm_timeout(struct usb_hcd *hcd,
			struct usb_device *udev, enum usb3_link_state state)
{
	struct xhci_hcd *xhci = hcd_to_xhci(hcd);
	struct usb_host_config *config;
	char *state_name;
	int i;
	u16 timeout = USB3_LPM_DISABLED;

	if (state == USB3_LPM_U1)
		state_name = "U1";
	else if (state == USB3_LPM_U2)
		state_name = "U2";
	else {
		dev_warn(&udev->dev, "Can't enable unknown link state %i\n",
				state);
		return timeout;
	}

	/* Gather some information about the currently installed configuration
	 * and alternate interface settings.
	 */
	if (xhci_update_timeout_for_endpoint(xhci, udev, &udev->ep0.desc,
			state, &timeout))
		return timeout;

	config = udev->actconfig;
	if (!config)
		return timeout;
```

The comment above the function states the rule that governs the whole scan, that a non-zero return from the per-endpoint step means "the timeout value has been finalized and we shouldn't look at any more endpoints". The `state_name` switch also serves as the state validation, returning the initial [`USB3_LPM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1261) for anything that is neither U1 nor U2. Endpoint zero is fed through [`xhci_update_timeout_for_endpoint()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4989) first, and a device with no active configuration stops there with whatever endpoint zero produced.

The loop over the active configuration reads every interface's current alternate setting, and it also gives a bound interface driver a chance to veto hub-initiated entry:

```c
/* drivers/usb/host/xhci.c:5089 end of xhci_calculate_lpm_timeout() */
	for (i = 0; i < config->desc.bNumInterfaces; i++) {
		struct usb_driver *driver;
		struct usb_interface *intf = config->interface[i];

		if (!intf)
			continue;

		/* Check if any currently bound drivers want hub-initiated LPM
		 * disabled.
		 */
		if (intf->dev.driver) {
			driver = to_usb_driver(intf->dev.driver);
			if (driver && driver->disable_hub_initiated_lpm) {
				dev_dbg(&udev->dev, "Hub-initiated %s disabled at request of driver %s\n",
					state_name, driver->name);
				timeout = xhci_get_timeout_no_hub_lpm(udev,
								      state);
				if (timeout == USB3_LPM_DISABLED)
					return timeout;
			}
		}

		/* Not sure how this could happen... */
		if (!intf->cur_altsetting)
			continue;

		if (xhci_update_timeout_for_interface(xhci, udev,
					intf->cur_altsetting,
					state, &timeout))
			return timeout;
	}
	return timeout;
}
```

A driver that set [`disable_hub_initiated_lpm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L1271) collapses the timeout to whatever [`xhci_get_timeout_no_hub_lpm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4792) allows, which is either device-initiated entry or nothing, and the scan ends immediately when it is nothing. Otherwise each interface's endpoints go through [`xhci_update_timeout_for_interface()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5014), whose only job is the loop over one alternate setting's descriptors:

```c
/* drivers/usb/host/xhci.c:5014 */
static int xhci_update_timeout_for_interface(struct xhci_hcd *xhci,
		struct usb_device *udev,
		struct usb_host_interface *alt,
		enum usb3_link_state state,
		u16 *timeout)
{
	int j;

	for (j = 0; j < alt->desc.bNumEndpoints; j++) {
		if (xhci_update_timeout_for_endpoint(xhci, udev,
					&alt->endpoint[j].desc, state, timeout))
			return -E2BIG;
	}
	return 0;
}
```

The interface step keeps no state of its own and passes the same running value down to each endpoint in turn, and its one addition is the early exit, which turns a single endpoint's refusal into a refusal for the whole alternate setting and then for the whole device.

The per-endpoint step is where the running maximum is kept, and where a single hostile endpoint can end the scan:

```c
/* drivers/usb/host/xhci.c:4989 */
static int xhci_update_timeout_for_endpoint(struct xhci_hcd *xhci,
		struct usb_device *udev,
		struct usb_endpoint_descriptor *desc,
		enum usb3_link_state state,
		u16 *timeout)
{
	u16 alt_timeout;

	alt_timeout = xhci_call_host_update_timeout_for_endpoint(xhci, udev,
		desc, state, timeout);

	/* If we found we can't enable hub-initiated LPM, and
	 * the U1 or U2 exit latency was too high to allow
	 * device-initiated LPM as well, then we will disable LPM
	 * for this device, so stop searching any further.
	 */
	if (alt_timeout == USB3_LPM_DISABLED) {
		*timeout = alt_timeout;
		return -E2BIG;
	}
	if (alt_timeout > *timeout)
		*timeout = alt_timeout;
	return 0;
}
```

`alt_timeout` is this endpoint's candidate. When it comes back as [`USB3_LPM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1261) the function writes that into `*timeout` and returns `-E2BIG`, which unwinds through the interface loop and out of the engine, so the device's answer is a refusal whatever the other endpoints produced. Otherwise the candidate raises the running value when it is larger, and the scan continues. Keeping the largest is the safe direction, because the timeout is how long the hub waits before parking the link, and the endpoint that needs the link awake soonest is the one that decides.

The dispatch between the two link states is a separate two-line function, so the per-endpoint step itself is state-agnostic:

```c
/* drivers/usb/host/xhci.c:4975 */
static u16 xhci_call_host_update_timeout_for_endpoint(struct xhci_hcd *xhci,
		struct usb_device *udev,
		struct usb_endpoint_descriptor *desc,
		enum usb3_link_state state,
		u16 *timeout)
{
	if (state == USB3_LPM_U1)
		return xhci_calculate_u1_timeout(xhci, udev, desc);
	else if (state == USB3_LPM_U2)
		return xhci_calculate_u2_timeout(xhci, udev, desc);

	return USB3_LPM_DISABLED;
}
```

It returns [`USB3_LPM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1261) for any state other than U1 or U2, which is the same refusal an endpoint of an unknown transfer type produces further down. The `timeout` pointer it takes is unused in this version and is carried only to keep one signature across the two calculations.

The scan reduces many candidates to one number, and any single refusal wins over all of them.

```
    One scan over one device's endpoints yields one hub timeout
    ───────────────────────────────────────────────────────────
    (each endpoint contributes a candidate; the largest is kept,
     and one candidate of USB3_LPM_DISABLED ends the scan at once)

      endpoint zero      interface 0            interface n-1
      (control)          cur_altsetting         cur_altsetting
    ┌────────────────┐ ┌────────────────┐     ┌────────────────┐
    │ candidate from │ │ candidate per  │ ... │ candidate per  │
    │ its own type   │ │ endpoint       │     │ endpoint       │
    └───────┬────────┘ └───────┬────────┘     └───────┬────────┘
            │                  │                      │
            └──────────┬───────┴──────────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────┐
        │ candidate is USB3_LPM_DISABLED  │ ──▶ return -E2BIG,
        │ ?                               │     answer is DISABLED
        └────────────────┬────────────────┘
                         │ no
                         ▼
        ┌──────────────────────────────────┐
        │ timeout = max(timeout, candidate)│
        └────────────────┬─────────────────┘
                         ▼
             one hub-encoded value per device
             (1us units for U1, 256us units for U2)
```

The same scan drawn along its own order shows what the running maximum does with each candidate and where a refusal cuts it short. The heights are the U1 tiers the next section derives, in multiples of SEL, so a bulk endpoint stands at five and a control endpoint at three, and the value kept is the tallest bar seen before the scan stops. A candidate the fallback returns as [`USB3_LPM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1261) is drawn hatched because it has no height; the scan ends there with `-E2BIG`, and every endpoint after it is never examined.

```
    The scan in order, the candidate it keeps, and the one that ends it
    ───────────────────────────────────────────────────────────────────
    (heights in multiples of SEL, the U1 tiers the next section derives;
     a candidate the fallback returns as USB3_LPM_DISABLED ends the scan)

    5 × SEL       ██          ██     ◀ largest so far, the value kept
    4             ██          ██
    3 × SEL  ██   ██   ██     ██     ▒▒  USB3_LPM_DISABLED, so the
    2        ██   ██   ██     ██     ▒▒  scan stops with -E2BIG and
    1        ██   ██   ██     ██     ▒▒  every endpoint after it is
    0   ─────██───██───██─────██─────▒▒──────────▶  never examined
             ctrl bulk intr   bulk   isoc  …          scan order
                      (notif)
```

### The U1 timeout is one tier per endpoint type

How long a link may idle before it is parked depends on what the endpoint above it is doing, so the U1 answer is worked out per endpoint, in two stages. The outer function guards against a periodic endpoint whose service interval is shorter than the wake-up itself, chooses between two formulas, converts to the hub's unit, and applies the field ceiling:

```c
/* drivers/usb/host/xhci.c:4879 */
/* Returns the hub-encoded U1 timeout value. */
static u16 xhci_calculate_u1_timeout(struct xhci_hcd *xhci,
		struct usb_device *udev,
		struct usb_endpoint_descriptor *desc)
{
	unsigned long long timeout_ns;

	/* Prevent U1 if service interval is shorter than U1 exit latency */
	if (usb_endpoint_xfer_int(desc) || usb_endpoint_xfer_isoc(desc)) {
		if (xhci_service_interval_to_ns(desc) <= udev->u1_params.mel) {
			dev_dbg(&udev->dev, "Disable U1, ESIT shorter than exit latency\n");
			return USB3_LPM_DISABLED;
		}
	}

	if (xhci->quirks & (XHCI_INTEL_HOST | XHCI_ZHAOXIN_HOST))
		timeout_ns = xhci_calculate_intel_u1_timeout(udev, desc);
	else
		timeout_ns = udev->u1_params.sel;

	/* The U1 timeout is encoded in 1us intervals.
	 * Don't return a timeout of zero, because that's USB3_LPM_DISABLED.
	 */
	if (timeout_ns == USB3_LPM_DISABLED)
		timeout_ns = 1;
	else
		timeout_ns = DIV_ROUND_UP_ULL(timeout_ns, 1000);

	/* If the necessary timeout value is bigger than what we can set in the
	 * USB 3.0 hub, we have to disable hub-initiated U1.
	 */
	if (timeout_ns <= USB3_LPM_U1_MAX_TIMEOUT)
		return timeout_ns;
	dev_dbg(&udev->dev, "Hub-initiated U1 disabled due to long timeout %lluus\n",
		timeout_ns);
	return xhci_get_timeout_no_hub_lpm(udev, USB3_LPM_U1);
}
```

The first block computes the endpoint's service interval with [`xhci_service_interval_to_ns()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4786) and compares it against [`udev->u1_params.mel`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L554), the Maximum Exit Latency of the whole path. An interrupt or isochronous endpoint whose interval is no longer than that exit latency would spend its entire period waking up, so U1 is refused for the device outright. The quirk test that follows picks between a host-specific tiered formula and the plain [`sel`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L570) value; the tiered formula is at [`drivers/usb/host/xhci.c:4842`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4842) and is shown below. The conversion then divides nanoseconds by 1000 to reach the field's microsecond unit, with the guard that a computed zero is bumped to 1, because zero in this encoding is the value that means disabled. The last block compares against [`USB3_LPM_U1_MAX_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1262) and, when the needed timeout will not fit the hub's eight-bit field, hands over to the device-initiated fallback.

The tiered formula is a switch on the endpoint's transfer type, and the comment above it states the tiers before the code implements them:

```c
/* drivers/usb/host/xhci.c:4834 */
/* The U1 timeout should be the maximum of the following values:
 *  - For control endpoints, U1 system exit latency (SEL) * 3
 *  - For bulk endpoints, U1 SEL * 5
 *  - For interrupt endpoints:
 *    - Notification EPs, U1 SEL * 3
 *    - Periodic EPs, max(105% of bInterval, U1 SEL * 2)
 *  - For isochronous endpoints, max(105% of bInterval, U1 SEL * 2)
 */
static unsigned long long xhci_calculate_intel_u1_timeout(
		struct usb_device *udev,
		struct usb_endpoint_descriptor *desc)
{
	unsigned long long timeout_ns;
	int ep_type;
	int intr_type;

	ep_type = usb_endpoint_type(desc);
	switch (ep_type) {
	case USB_ENDPOINT_XFER_CONTROL:
		timeout_ns = udev->u1_params.sel * 3;
		break;
	case USB_ENDPOINT_XFER_BULK:
		timeout_ns = udev->u1_params.sel * 5;
		break;
	case USB_ENDPOINT_XFER_INT:
		intr_type = usb_endpoint_interrupt_type(desc);
		if (intr_type == USB_ENDPOINT_INTR_NOTIFICATION) {
			timeout_ns = udev->u1_params.sel * 3;
			break;
		}
		/* Otherwise the calculation is the same as isoc eps */
		fallthrough;
	case USB_ENDPOINT_XFER_ISOC:
		timeout_ns = xhci_service_interval_to_ns(desc);
		timeout_ns = DIV_ROUND_UP_ULL(timeout_ns * 105, 100);
		if (timeout_ns < udev->u1_params.sel * 2)
			timeout_ns = udev->u1_params.sel * 2;
		break;
	default:
		return 0;
	}

	return timeout_ns;
}
```

A control endpoint takes three times the System Exit Latency and a bulk endpoint five times, which are the two multipliers the comment above the function states and the code applies; the tree gives no reason for the choice of 3 and 5, so this page states the values rather than a rationale. An interrupt endpoint splits in two. A notification endpoint, identified by [`usb_endpoint_interrupt_type()`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L674) reporting [`USB_ENDPOINT_INTR_NOTIFICATION`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L456), takes three times SEL like a control endpoint, and every other interrupt endpoint falls through to the isochronous case. That shared case takes 105 percent of the service interval, so the link is left awake slightly past one period, and raises the result to twice SEL when that is larger. An endpoint of any other transfer type returns 0, which the caller reads as [`USB3_LPM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1261) and turns into a refusal.

| endpoint type | candidate timeout | code |
|---|---|---|
| control | three times [`sel`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L570) | [`drivers/usb/host/xhci.c:4853`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4853) |
| bulk | five times [`sel`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L570) | [`drivers/usb/host/xhci.c:4856`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4856) |
| interrupt, notification | three times [`sel`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L570) | [`drivers/usb/host/xhci.c:4861`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4861) |
| interrupt, periodic | the larger of 105 percent of the service interval and twice [`sel`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L570) | [`drivers/usb/host/xhci.c:4865`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4865) |
| isochronous | the larger of 105 percent of the service interval and twice [`sel`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L570) | [`drivers/usb/host/xhci.c:4867`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4867) |
| any other | 0, read as [`USB3_LPM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1261) | [`drivers/usb/host/xhci.c:4873`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4873) |

The service interval that two of those rows use is an exponential of the descriptor's [`bInterval`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L422), expressed in nanoseconds:

```c
/* drivers/usb/host/xhci.c:4785 */
/* Service interval in nanoseconds = 2^(bInterval - 1) * 125us * 1000ns / 1us */
static unsigned long long xhci_service_interval_to_ns(
		struct usb_endpoint_descriptor *desc)
{
	return (1ULL << (desc->bInterval - 1)) * 125 * 1000;
}
```

The comment states the derivation the single expression performs, that a SuperSpeed periodic endpoint's interval is `2^(bInterval - 1)` microframes of 125 microseconds each, and the multiplication by 1000 carries the result from microseconds to nanoseconds, the unit every latency in this calculation is stored in.

The table above names the candidate for each endpoint type; the figure below places those candidates on the scale they share, because every one of them is a multiple of the same System Exit Latency except where a long service interval takes over. The axis counts multiples of SEL, and each labelled position is where one group of endpoints lands.

```
    Where each endpoint type's U1 candidate lands
    ─────────────────────────────────────────────
    (the two periodic rows share one formula whose floor is twice
     SEL, which a long service interval lifts above every other tier)

    0        1        2        3        4        5   multiples of SEL
    ├─────────────────┬────────┬─────────────────┬─────────────▶
                      │        │                 │
                      │        │                 └─ bulk
                      │        └─ control, and an interrupt endpoint
                      │           of notification type
                      └─ the floor for a periodic interrupt or an
                         isochronous endpoint, raised to 105% of the
                         service interval when that is larger

    the winning candidate is divided into 1us units and compared with
    USB3_LPM_U1_MAX_TIMEOUT (0x7F); a larger one is handed to the
    device-initiated fallback
```

### The U2 timeout starts from a ten-millisecond floor

The U2 timeout is encoded in units 256 times coarser than the U1 timeout, so it can express a far longer idle period, and the U2 calculation fills that range with a different formula inside the same two-stage shape. The outer function repeats the service-interval guard against [`udev->u2_params.mel`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L554), then divides by a larger unit:

```c
/* drivers/usb/host/xhci.c:4943 */
/* Returns the hub-encoded U2 timeout value. */
static u16 xhci_calculate_u2_timeout(struct xhci_hcd *xhci,
		struct usb_device *udev,
		struct usb_endpoint_descriptor *desc)
{
	unsigned long long timeout_ns;

	/* Prevent U2 if service interval is shorter than U2 exit latency */
	if (usb_endpoint_xfer_int(desc) || usb_endpoint_xfer_isoc(desc)) {
		if (xhci_service_interval_to_ns(desc) <= udev->u2_params.mel) {
			dev_dbg(&udev->dev, "Disable U2, ESIT shorter than exit latency\n");
			return USB3_LPM_DISABLED;
		}
	}

	if (xhci->quirks & (XHCI_INTEL_HOST | XHCI_ZHAOXIN_HOST))
		timeout_ns = xhci_calculate_intel_u2_timeout(udev, desc);
	else
		timeout_ns = udev->u2_params.sel;

	/* The U2 timeout is encoded in 256us intervals */
	timeout_ns = DIV_ROUND_UP_ULL(timeout_ns, 256 * 1000);
	/* If the necessary timeout value is bigger than what we can set in the
	 * USB 3.0 hub, we have to disable hub-initiated U2.
	 */
	if (timeout_ns <= USB3_LPM_U2_MAX_TIMEOUT)
		return timeout_ns;
	dev_dbg(&udev->dev, "Hub-initiated U2 disabled due to long timeout %lluus\n",
		timeout_ns * 256);
	return xhci_get_timeout_no_hub_lpm(udev, USB3_LPM_U2);
}
```

The division at [`drivers/usb/host/xhci.c:4964`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4964) is by `256 * 1000` rather than 1000, which converts nanoseconds into the field's 256-microsecond units in one step. There is no bump-away-from-zero here, because the U2 formula never produces zero. The ceiling comparison against [`USB3_LPM_U2_MAX_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1263) and the fallback to [`xhci_get_timeout_no_hub_lpm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4792) are the same two steps as for U1.

The tiered formula for U2 takes a maximum of three terms rather than switching on endpoint type, and its comment names all three:

```c
/* drivers/usb/host/xhci.c:4917 */
/* The U2 timeout should be the maximum of:
 *  - 10 ms (to avoid the bandwidth impact on the scheduler)
 *  - largest bInterval of any active periodic endpoint (to avoid going
 *    into lower power link states between intervals).
 *  - the U2 Exit Latency of the device
 */
static unsigned long long xhci_calculate_intel_u2_timeout(
		struct usb_device *udev,
		struct usb_endpoint_descriptor *desc)
{
	unsigned long long timeout_ns;
	unsigned long long u2_del_ns;

	timeout_ns = 10 * 1000 * 1000;

	if ((usb_endpoint_xfer_int(desc) || usb_endpoint_xfer_isoc(desc)) &&
			(xhci_service_interval_to_ns(desc) > timeout_ns))
		timeout_ns = xhci_service_interval_to_ns(desc);

	u2_del_ns = le16_to_cpu(udev->bos->ss_cap->bU2DevExitLat) * 1000ULL;
	if (u2_del_ns > timeout_ns)
		timeout_ns = u2_del_ns;

	return timeout_ns;
}
```

The starting value is ten milliseconds written out in nanoseconds, and the comment gives its purpose, to avoid the bandwidth impact on the scheduler that a short U2 timeout would cause. A periodic endpoint whose service interval is longer than that raises the timeout to the interval, so the link stays awake between one period and the next. The device's own reported U2 exit latency, read from [`bU2DevExitLat`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L952) in the SuperSpeed capability of its BOS descriptor and scaled from microseconds to nanoseconds, raises it again when it is larger still. Unlike the U1 formula this one has no default case, and its ten-millisecond starting value keeps the result above zero, which is why its caller needs no bump.

The U2 formula reads as a floor and two terms that can raise it, and the field the result has to fit puts a ceiling above all three. The figure below plots those numbers on one millisecond scale, so the room the U2 encoding buys over the U1 encoding is visible as the distance between the floor and the ceiling.

```
    The U2 candidate between its floor and the field's ceiling
    ──────────────────────────────────────────────────────────
    (the candidate is the largest of three terms, and is then
     divided into 256us units)

    0 ms          10 ms                              65.024 ms
    ├─────────────┬────────────────────────────────────┬─────▶
                  │                                    │
                  │                                    └─ 0xFE, the
                  │                                       widest value
                  │                                       the field holds
                  └─ the starting term, ten milliseconds; a longer
                     service interval or a larger reported U2 exit
                     latency raises the candidate above it

    a candidate past the ceiling is handed to the same device-initiated
    fallback the U1 candidate uses
```

### A timeout the hub cannot hold falls back to device-initiated entry

When the computed timeout will not fit its field, the link state has a fallback. The hub can be told to accept a transition without ever starting one, which leaves the decision to the device, and whether that is possible depends on whether the device's own latency values fit the fields of the Set SEL request:

```c
/* drivers/usb/host/xhci.c:4792 */
static u16 xhci_get_timeout_no_hub_lpm(struct usb_device *udev,
		enum usb3_link_state state)
{
	unsigned long long sel;
	unsigned long long pel;
	unsigned int max_sel_pel;
	char *state_name;

	switch (state) {
	case USB3_LPM_U1:
		/* Convert SEL and PEL stored in nanoseconds to microseconds */
		sel = DIV_ROUND_UP(udev->u1_params.sel, 1000);
		pel = DIV_ROUND_UP(udev->u1_params.pel, 1000);
		max_sel_pel = USB3_LPM_MAX_U1_SEL_PEL;
		state_name = "U1";
		break;
	case USB3_LPM_U2:
		sel = DIV_ROUND_UP(udev->u2_params.sel, 1000);
		pel = DIV_ROUND_UP(udev->u2_params.pel, 1000);
		max_sel_pel = USB3_LPM_MAX_U2_SEL_PEL;
		state_name = "U2";
		break;
	default:
		dev_warn(&udev->dev, "%s: Can't get timeout for non-U1 or U2 state.\n",
				__func__);
		return USB3_LPM_DISABLED;
	}

	if (sel <= max_sel_pel && pel <= max_sel_pel)
		return USB3_LPM_DEVICE_INITIATED;

	if (sel > max_sel_pel)
		dev_dbg(&udev->dev, "Device-initiated %s disabled "
				"due to long SEL %llu ms\n",
				state_name, sel);
	else
		dev_dbg(&udev->dev, "Device-initiated %s disabled "
				"due to long PEL %llu ms\n",
				state_name, pel);
	return USB3_LPM_DISABLED;
}
```

The switch reads [`sel`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L570) and [`pel`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L560) from the requested state's parameters, rounds each from nanoseconds up to microseconds, and picks the matching ceiling, [`USB3_LPM_MAX_U1_SEL_PEL`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1278) for U1 and [`USB3_LPM_MAX_U2_SEL_PEL`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1279) for U2. When both fit it returns [`USB3_LPM_DEVICE_INITIATED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1264), the all-ones timeout value the hub reads as "accept, but never initiate". When either is too wide it returns [`USB3_LPM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1261) and logs which of the two overflowed, and that refusal propagates all the way out of the scan.

Three tests in sequence decide what a device gets when its computed timeout will fit nowhere in the hub's field, and each test either produces the answer or hands the question to the next. A timeout within the field's ceiling is the answer itself, a real idle timer the hub counts down. A wider one is handed to the fallback, which reads the same state's SEL and PEL, rounded up to microseconds, against one ceiling per state; both within it make the state [`USB3_LPM_DEVICE_INITIATED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1264), a transition the hub accepts and leaves to the device, and either past it makes the state [`USB3_LPM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1261), which also ends the scan at that endpoint.

Both outcomes of that fallback are values from one small reserved set, and every value in that set has a meaning the hub obeys. The three constants the hub protocol reserves are defined together, with a comment that gives the semantics of each end of the range:

```c
/* include/uapi/linux/usb/ch9.h:1243 */
/*
 * A U1 timeout of 0x0 means the parent hub will reject any transitions to U1.
 * 0xff means the parent hub will accept transitions to U1, but will not
 * initiate a transition.
 *
 * A U1 timeout of 0x1 to 0x7F also causes the hub to initiate a transition to
 * U1 after that many microseconds.  Timeouts of 0x80 to 0xFE are reserved
 * values.
 *
 * A U2 timeout of 0x0 means the parent hub will reject any transitions to U2.
 * 0xff means the parent hub will accept transitions to U2, but will not
 * initiate a transition.
 *
 * A U2 timeout of 0x1 to 0xFE also causes the hub to initiate a transition to
 * U2 after N*256 microseconds.  Therefore a U2 timeout value of 0x1 means a U2
 * idle timer of 256 microseconds, 0x2 means 512 microseconds, 0xFE means
 * 65.024ms.
 */
#define USB3_LPM_DISABLED		0x0
#define USB3_LPM_U1_MAX_TIMEOUT		0x7F
#define USB3_LPM_U2_MAX_TIMEOUT		0xFE
#define USB3_LPM_DEVICE_INITIATED	0xFF
```

[`USB3_LPM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1261) is zero and makes the hub reject transitions; [`USB3_LPM_U1_MAX_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1262) and [`USB3_LPM_U2_MAX_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1263) are the largest values that mean a real timer, and everything between those and [`USB3_LPM_DEVICE_INITIATED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1264) is reserved, which is why the U1 range stops at `0x7F` while the U2 range runs to `0xFE`. The two SEL and PEL ceilings are defined a few lines later with a comment naming the field widths that produce them:

```c
/* include/uapi/linux/usb/ch9.h:1273 */
/*
 * The Set System Exit Latency control transfer provides one byte each for
 * U1 SEL and U1 PEL, so the max exit latency is 0xFF.  U2 SEL and U2 PEL each
 * are two bytes long.
 */
#define USB3_LPM_MAX_U1_SEL_PEL		0xFF
#define USB3_LPM_MAX_U2_SEL_PEL		0xFFFF
```

The Set SEL request carries one byte each for U1 SEL and U1 PEL, hence `0xFF`, and two bytes each for the U2 pair, hence `0xFFFF`. Those are the same two constants [`usb_req_set_sel()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4106) checks before it sends the request at all.

### SEL, PEL and MEL measure three spans of the same wake-up

Every number in the calculation above comes out of one record, held twice per device, once for each of the two link states:

```c
/* include/linux/usb.h:540 */
/*
 * USB 3.0 Link Power Management (LPM) parameters.
 *
 * PEL and SEL are USB 3.0 Link PM latencies for device-initiated LPM exit.
 * MEL is the USB 3.0 Link PM latency for host-initiated LPM exit.
 * All three are stored in nanoseconds.
 */
struct usb3_lpm_parameters {
	/*
	 * Maximum exit latency (MEL) for the host to send a packet to the
	 * device (either a Ping for isoc endpoints, or a data packet for
	 * interrupt endpoints), the hubs to decode the packet, and for all hubs
	 * in the path to transition the links to U0.
	 */
	unsigned int mel;
```

The comment above the struct states the division of labour, that PEL and SEL describe device-initiated exit while MEL describes host-initiated exit, and that all three are stored in nanoseconds. [`mel`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L554) is the span the host controller has to allow for, covering the time to send a packet, the time for every hub in the path to decode it, and the time for every link in the path to reach U0. That is the number this page installs in the slot context.

```c
/* include/linux/usb.h:555 */
	/*
	 * Maximum exit latency for a device-initiated LPM transition to bring
	 * all links into U0.  Abbreviated as "PEL" in section 9.4.12 of the USB
	 * 3.0 spec, with no explanation of what "P" stands for.  "Path"?
	 */
	unsigned int pel;

	/*
	 * The System Exit Latency (SEL) includes PEL, and three other
	 * latencies.  After a device initiates a U0 transition, it will take
	 * some time from when the device sends the ERDY to when it will finally
	 * receive the data packet.  Basically, SEL should be the worse-case
	 * latency from when a device starts initiating a U0 transition to when
	 * it will get data.
	 */
	unsigned int sel;
```

[`pel`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L560) covers the other direction, the time for a transition the device starts to bring every link in the path up to U0, and its comment records that the USB 3.0 specification abbreviates it without ever saying what the P stands for. [`sel`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L570) is the larger figure that contains PEL, because after the device starts a transition it still has to send an ERDY, the host has to process it, and the first data packet has to travel back; SEL is the worst case over all of that. SEL is the value both timeout formulas multiply.

```c
/* include/linux/usb.h:571 */
	/*
	 * The idle timeout value that is currently programmed into the parent
	 * hub for this device.  When the timer counts to zero, the parent hub
	 * will initiate an LPM transition to either U1 or U2.
	 */
	int timeout;
};
```

[`timeout`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L576) is the fourth member and the only one this page writes back. It holds the hub-encoded value currently programmed into the parent hub for this state, which [`usb_set_lpm_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4225) stores after a successful SetPortFeature and which [`calculate_max_exit_latency()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5123) reads to tell whether a state is currently live.

The three spans differ in which part of one wake-up they cover.

```
    SEL, PEL and MEL measure three spans of one wake-up
    ──────────────────────────────────────────────────
    (each row of phases runs left to right in time, and the bar
     beneath a row marks the span the named latency covers)

    a transition the device starts
    ┌────────────┬────────────────┬─────────────────────────────┐
    │ the device │ every link in  │ the ERDY reaches the host,  │
    │ drives an  │ the path       │ the host takes its own      │
    │ LFPS onto  │ reaches U0     │ delay, and the first packet │
    │ its link   │                │ arrives back at the device  │
    └────────────┴────────────────┴─────────────────────────────┘
    ├─────────────────────────────┬─────────────────────────────┤ SEL
    ├─────────────────────────────┤ PEL

    a packet the host sends
    ┌────────────────┬──────────────────┬──────────────────────┐
    │ the host sends │ every link in    │ the hubs decode and  │
    │ a PING or a    │ the path reaches │ the device answers   │
    │ data packet    │ U0               │                      │
    └────────────────┴──────────────────┴──────────────────────┘
    ├──────────────────────────────────────────────────────────┤ MEL

    PEL and SEL reach the device in a Set SEL request and bound the
    hub timeout this page computes.  MEL reaches the host controller
    in the slot context and bounds the bus schedule.
```

Those two rows fix where each measurement begins and ends, and that is why only the third of them reaches the controller. The other two describe a wake-up the device starts, and they bound the hub timeout this page computes.

All three are computed once per device, at enumeration, from the BOS descriptors of the device and its parent:

```c
/* drivers/usb/core/hub.c:5206 in hub_port_init() */
	if (le16_to_cpu(udev->descriptor.bcdUSB) >= 0x0201) {
		retval = usb_get_bos_descriptor(udev);
		if (!retval) {
			udev->lpm_capable = usb_device_supports_lpm(udev);
			udev->lpm_disable_count = 1;
			usb_set_lpm_parameters(udev);
			usb_req_set_sel(udev);
		}
	}
```

[`lpm_capable`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L702) is decided first, [`lpm_disable_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L741) is seeded at 1 so link power management starts off, then [`usb_set_lpm_parameters()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L337) fills all three latencies and [`usb_req_set_sel()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4106) tells the device two of them. The four exit latencies the calculation starts from are read straight out of the two BOS descriptors, and [`usb_set_lpm_mel()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L219) is then called once per link state:

```c
/* drivers/usb/core/hub.c:360 in usb_set_lpm_parameters() */
	udev_u1_del = udev->bos->ss_cap->bU1devExitLat;
	udev_u2_del = le16_to_cpu(udev->bos->ss_cap->bU2DevExitLat);
	hub_u1_del = udev->parent->bos->ss_cap->bU1devExitLat;
	hub_u2_del = le16_to_cpu(udev->parent->bos->ss_cap->bU2DevExitLat);

	usb_set_lpm_mel(udev, &udev->u1_params, udev_u1_del,
			hub, &udev->parent->u1_params, hub_u1_del);

	usb_set_lpm_mel(udev, &udev->u2_params, udev_u2_del,
			hub, &udev->parent->u2_params, hub_u2_del);
```

Each call is given the device's own reported exit latency for that state, the parent hub, and the parent's already-computed parameters for the same state, which is how one call extends the path by exactly one link. The accumulation itself is the part this page follows, because MEL is the term that reaches the controller:

```c
/* drivers/usb/core/hub.c:214 */
/*
 * Set the Maximum Exit Latency (MEL) for the host to wakup up the path from
 * U1/U2, send a PING to the device and receive a PING_RESPONSE.
 * See USB 3.1 section C.1.5.2
 */
static void usb_set_lpm_mel(struct usb_device *udev,
		struct usb3_lpm_parameters *udev_lpm_params,
		unsigned int udev_exit_latency,
		struct usb_hub *hub,
		struct usb3_lpm_parameters *hub_lpm_params,
		unsigned int hub_exit_latency)
{
	unsigned int total_mel;

	/*
	 * tMEL1. time to transition path from host to device into U0.
	 * MEL for parent already contains the delay up to parent, so only add
	 * the exit latency for the last link (pick the slower exit latency),
	 * and the hub header decode latency. See USB 3.1 section C 2.2.1
	 * Store MEL in nanoseconds
	 */
	total_mel = hub_lpm_params->mel +
		max(udev_exit_latency, hub_exit_latency) * 1000 +
		hub->descriptor->u.ss.bHubHdrDecLat * 100;
```

The comment names the term, tMEL1, and the code adds two things to the parent's already-computed MEL. The first is the exit latency of the last link, taking the slower of the device and the hub and scaling it from microseconds to nanoseconds. The second is the hub's header decode latency, whose descriptor field is in units of 100 nanoseconds. Building on `hub_lpm_params->mel` makes the value cumulative down the topology, so a device two hubs deep inherits both hubs' contributions.

```c
/* drivers/usb/core/hub.c:239 */
	/*
	 * tMEL2. Time to submit PING packet. Sum of tTPTransmissionDelay for
	 * each link + wHubDelay for each hub. Add only for last link.
	 * tMEL4, the time for PING_RESPONSE to traverse upstream is similar.
	 * Multiply by 2 to include it as well.
	 */
	total_mel += (__le16_to_cpu(hub->descriptor->u.ss.wHubDelay) +
		      USB_TP_TRANSMISSION_DELAY) * 2;

	/*
	 * tMEL3, tPingResponse. Time taken by device to generate PING_RESPONSE
	 * after receiving PING. Also add 2100ns as stated in USB 3.1 C 1.5.2.4
	 * to cover the delay if the PING_RESPONSE is queued behind a Max Packet
	 * Size DP.
	 * Note these delays should be added only once for the entire path, so
	 * add them to the MEL of the device connected to the roothub.
	 */
	if (!hub->hdev->parent)
		total_mel += USB_PING_RESPONSE_TIME + 2100;

	udev_lpm_params->mel = total_mel;
}
```

The next term covers the packet's own travel time, the hub delay plus a fixed transmission delay, doubled because the response travels back the same way. The last term, the device's own time to answer a PING plus a fixed allowance the comment attributes to the possibility of the response being queued behind a maximum-sized data packet, is added only when the hub has no parent, so it is counted once for the whole path rather than once per hub. The result is written into [`mel`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L554).

SEL is derived from PEL by adding the two travel terms the comment enumerates:

```c
/* drivers/usb/core/hub.c:314 */
static void usb_set_lpm_sel(struct usb_device *udev,
		struct usb3_lpm_parameters *udev_lpm_params)
{
	struct usb_device *parent;
	unsigned int num_hubs;
	unsigned int total_sel;

	/* t1 = device PEL */
	total_sel = udev_lpm_params->pel;
	/* How many external hubs are in between the device & the root port. */
	for (parent = udev->parent, num_hubs = 0; parent->parent;
			parent = parent->parent)
		num_hubs++;
	/* t2 = 2.1us + 250ns * (num_hubs - 1) */
	if (num_hubs > 0)
		total_sel += 2100 + 250 * (num_hubs - 1);

	/* t4 = 250ns * num_hubs */
	total_sel += 250 * num_hubs;

	udev_lpm_params->sel = total_sel;
}
```

It starts from [`pel`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L560), counts the external hubs between the device and the root port by following the parent chain, and adds a fixed 2100 nanoseconds plus 250 per additional hub for the ERDY travelling up, and 250 nanoseconds per hub for the first packet travelling back down. A device directly on a root port has `num_hubs` of zero, so its SEL equals its PEL exactly.

### The exit latency the controller is told is the larger of the two live values

The controller holds one Max Exit Latency per device, and the device may have both link states enabled, so the value installed has to cover whichever of them is live. [`calculate_max_exit_latency()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5123) works out which of U1 and U2 will be live after the change being made, and takes the larger of their exit latencies:

```c
/* drivers/usb/host/xhci.c:5123 */
static int calculate_max_exit_latency(struct usb_device *udev,
		enum usb3_link_state state_changed,
		u16 hub_encoded_timeout)
{
	unsigned long long u1_mel_us = 0;
	unsigned long long u2_mel_us = 0;
	unsigned long long mel_us = 0;
	bool disabling_u1;
	bool disabling_u2;
	bool enabling_u1;
	bool enabling_u2;

	disabling_u1 = (state_changed == USB3_LPM_U1 &&
			hub_encoded_timeout == USB3_LPM_DISABLED);
	disabling_u2 = (state_changed == USB3_LPM_U2 &&
			hub_encoded_timeout == USB3_LPM_DISABLED);

	enabling_u1 = (state_changed == USB3_LPM_U1 &&
			hub_encoded_timeout != USB3_LPM_DISABLED);
	enabling_u2 = (state_changed == USB3_LPM_U2 &&
			hub_encoded_timeout != USB3_LPM_DISABLED);

	/* If U1 was already enabled and we're not disabling it,
	 * or we're going to enable U1, account for the U1 max exit latency.
	 */
	if ((udev->u1_params.timeout != USB3_LPM_DISABLED && !disabling_u1) ||
			enabling_u1)
		u1_mel_us = DIV_ROUND_UP(udev->u1_params.mel, 1000);
	if ((udev->u2_params.timeout != USB3_LPM_DISABLED && !disabling_u2) ||
			enabling_u2)
		u2_mel_us = DIV_ROUND_UP(udev->u2_params.mel, 1000);

	mel_us = max(u1_mel_us, u2_mel_us);

```

The four booleans separate the state being changed from the state that is not. A state counts toward the result when it is already enabled and is not the one being disabled, which the test on [`timeout`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L576) expresses, or when it is the one being enabled. Each surviving state contributes its [`mel`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L554), rounded from nanoseconds up to microseconds, because the slot-context field counts microseconds. The maximum of the two is the answer, so disabling U1 while U2 stays enabled leaves the controller with U2's latency rather than zero.

The result is then bounded by the width of the field it has to occupy:

```c
/* drivers/usb/host/xhci.c:5157 */
	/* xHCI host controller max exit latency field is only 16 bits wide. */
	if (mel_us > MAX_EXIT) {
		dev_warn(&udev->dev, "Link PM max exit latency of %lluus "
				"is too big.\n", mel_us);
		return -E2BIG;
	}
	return mel_us;
}
```

The comment states the constraint the check enforces, that the field is 16 bits wide, and [`MAX_EXIT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L371) is the mask that expresses it. A path whose wake-up cost exceeds 65535 microseconds cannot be described to the controller at all, so the function returns `-E2BIG` and the caller turns the whole request into a refusal. The mask is defined with the other fields of the same context word:

```c
/* drivers/usb/host/xhci.h:369 */
/* dev_info2 bitmasks */
/* Max Exit Latency (ms) - worst case time to wake up all links in dev path */
#define MAX_EXIT	(0xffff)
/* Root hub port number that is needed to access the USB device */
#define ROOT_HUB_PORT(p)	(((p) & 0xff) << 16)
#define DEVINFO_TO_ROOT_HUB_PORT(p)	(((p) >> 16) & 0xff)
/* Maximum number of ports under a hub device */
#define XHCI_MAX_PORTS(p)	(((p) & 0xff) << 24)
#define DEVINFO_TO_MAX_PORTS(p)	(((p) & (0xff << 24)) >> 24)
```

[`MAX_EXIT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L371) occupies bits 15 to 0 of the word and its comment names the unit as milliseconds, while the code that fills it and the code that checks it both work in microseconds; the ceiling is derived from the field's width either way. [`ROOT_HUB_PORT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L373) occupies bits 23 to 16 and [`XHCI_MAX_PORTS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L376) bits 31 to 24, and neither is touched by this flow; they are carried across unchanged when the input context is built. [`DEVINFO_TO_ROOT_HUB_PORT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L374) and [`DEVINFO_TO_MAX_PORTS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L377) are the matching readers that recover those two fields from a word the controller wrote.

```
    The slot-context word that carries Max Exit Latency, to scale
    ─────────────────────────────────────────────────────────────
    (dev_info2, the second dword of the slot context)

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌───────────────┬───────────────┬───────────────────────────────┐
    DW1   │   Max Ports   │ Root Hub Port │        Max Exit Latency       │
          └───────┬───────┴───────┬───────┴───────────────┬───────────────┘
                  │               │                       │
                  │               │                       └─ MAX_EXIT, 15:0
                  │               └─ ROOT_HUB_PORT, 23:16
                  └─ XHCI_MAX_PORTS, 31:24

    Only the low half moves on this path.  The other two fields are
    copied from the output context and written back unchanged, which
    is why the input context is built by copying rather than by
    filling in fields one at a time.
```

### An Evaluate Context command writes the new latency into the slot context

The Max Exit Latency is a field the controller owns, so changing it means asking the controller to change it. [`xhci_change_max_exit_latency()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4517) builds an input context that differs from the device's current context in that one field and issues an Evaluate Context command over it. It opens by allocating the command and taking the driver lock:

```c
/* drivers/usb/host/xhci.c:4513 */
/*
 * Issue an Evaluate Context command to change the Maximum Exit Latency in the
 * slot context.  If that succeeds, store the new MEL in the xhci_virt_device.
 */
static int __maybe_unused xhci_change_max_exit_latency(struct xhci_hcd *xhci,
			struct usb_device *udev, u16 max_exit_latency)
{
	struct xhci_virt_device *virt_dev;
	struct xhci_command *command;
	struct xhci_input_control_ctx *ctrl_ctx;
	struct xhci_slot_ctx *slot_ctx;
	unsigned long flags;
	int ret;

	command = xhci_alloc_command_with_ctx(xhci, true, GFP_KERNEL);
	if (!command)
		return -ENOMEM;

	spin_lock_irqsave(&xhci->lock, flags);

	virt_dev = xhci->devs[udev->slot_id];

	/*
	 * virt_dev might not exists yet if xHC resumed from hibernate (S4) and
	 * xHC was re-initialized. Exit latency will be set later after
	 * hub_port_finish_reset() is done and xhci->devs[] are re-allocated
	 */

	if (!virt_dev || max_exit_latency == virt_dev->current_mel) {
		spin_unlock_irqrestore(&xhci->lock, flags);
		xhci_free_command(xhci, command);
		return 0;
	}
```

The comment above the function states both halves of its job, the command and the caching. [`xhci_alloc_command_with_ctx()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L1758) is called with [`GFP_KERNEL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/gfp_types.h#L377) before the lock is taken, because it sleeps. Under the lock the function looks up [`xhci->devs[udev->slot_id]`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1554), and the comment beside that lookup records why a missing entry is a silent success, since after a resume from hibernation the controller is re-initialized and its device array is rebuilt, so the exit latency will be set again once the device is re-enumerated. The same test also short-circuits a repeat of a latency already installed, by comparing against [`virt_dev->current_mel`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L762), which makes a redundant enable free.

```c
/* drivers/usb/host/xhci.h:761 */
	/* The current max exit latency for the enabled USB3 link states. */
	u16				current_mel;
	/* Used for the debugfs interfaces. */
	void				*debugfs_private;
	/* set if this endpoint is controlled via sideband access*/
	struct xhci_sideband	*sideband;
};
```

[`current_mel`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L762) is a plain `u16` cache of the value the controller last accepted, and its comment names it as the latency for the enabled USB3 link states. It is written only on success, which keeps the cache honest if a command fails. [`debugfs_private`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L764) and [`sideband`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L766) close the structure and belong to the debugfs interface and to sideband access rather than to this flow.

With the device present and the value new, the function builds the input context:

```c
/* drivers/usb/host/xhci.c:4547 */
	/* Attempt to issue an Evaluate Context command to change the MEL. */
	ctrl_ctx = xhci_get_input_control_ctx(command->in_ctx);
	if (!ctrl_ctx) {
		spin_unlock_irqrestore(&xhci->lock, flags);
		xhci_free_command(xhci, command);
		xhci_warn(xhci, "%s: Could not get input context, bad type.\n",
				__func__);
		return -ENOMEM;
	}

	xhci_slot_copy(xhci, command->in_ctx, virt_dev->out_ctx);
	spin_unlock_irqrestore(&xhci->lock, flags);

	ctrl_ctx->add_flags |= cpu_to_le32(SLOT_FLAG);
	slot_ctx = xhci_get_slot_ctx(xhci, command->in_ctx);
	slot_ctx->dev_info2 &= cpu_to_le32(~((u32) MAX_EXIT));
	slot_ctx->dev_info2 |= cpu_to_le32(max_exit_latency);
	slot_ctx->dev_state = 0;

	xhci_dbg_trace(xhci, trace_xhci_dbg_context_change,
			"Set up evaluate context for LPM MEL change.");

	/* Issue and wait for the evaluate context command. */
	ret = xhci_configure_endpoint(xhci, udev, command,
			true, true);

	if (!ret) {
		spin_lock_irqsave(&xhci->lock, flags);
		virt_dev->current_mel = max_exit_latency;
		spin_unlock_irqrestore(&xhci->lock, flags);
	}

	xhci_free_command(xhci, command);

	return ret;
}
```

[`xhci_get_input_control_ctx()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L516) returns the header of the input context, and a null return means the container was built with the wrong type, which the function reports and turns into `-ENOMEM`. [`xhci_slot_copy()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L1626) then copies the device's current output slot context into the input slot context, so every field except the one being changed already holds the value the controller last wrote. The lock is dropped at that point, because everything that follows touches only the command's own memory.

The three writes after the lock are the whole edit. [`SLOT_FLAG`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L366) is set in [`ctrl_ctx->add_flags`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L515) to tell the controller that the slot context in this input context is to be evaluated. [`slot_ctx->dev_info2`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L344) has its low sixteen bits cleared with the complement of [`MAX_EXIT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L371) and the new value placed there, leaving the root-hub port and maximum-ports fields as the copy left them. [`slot_ctx->dev_state`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L346) is zeroed, because the slot state and device address in it are the controller's to report rather than software's to set. Then [`xhci_configure_endpoint()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L2960) is called with `ctx_change` true, which selects an Evaluate Context command over a Configure Endpoint one, and `must_succeed` true. On a zero return the new value is cached under the lock, and the command is freed on every path.

The header of the input context is two words:

```c
/* drivers/usb/host/xhci.h:513 */
struct xhci_input_control_ctx {
	__le32	drop_flags;
	__le32	add_flags;
	__le32	rsvd2[6];
};
```

[`drop_flags`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L514) names contexts the controller should stop using and is left at zero here, since nothing is being removed. [`add_flags`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L515) names the contexts to evaluate, and bit 0 of it is [`SLOT_FLAG`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L366); [`rsvd2`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L516) is the reserved remainder that pads the header out to the 32-byte context size. The two flag bits this page's command can set are defined beside the slot-context field masks:

```c
/* drivers/usb/host/xhci.h:366 */
#define SLOT_FLAG	(1 << 0)
#define EP0_FLAG	(1 << 1)
```

[`SLOT_FLAG`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L366) is bit 0 and selects the slot context, which is the only bit this flow sets; [`EP0_FLAG`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L367) is bit 1 and selects the default control endpoint's context, which a latency change leaves alone. The wider input-context layout and the other flags belong to `device/input-context.md`.

The copy that precedes the edit is a four-word assignment:

```c
/* drivers/usb/host/xhci-mem.c:1621 */
/* Copy output xhci_slot_ctx to the input xhci_slot_ctx.
 * Useful when you want to change one particular aspect of the endpoint and then
 * issue a configure endpoint command.  Only the context entries field matters,
 * but we'll copy the whole thing anyway.
 */
void xhci_slot_copy(struct xhci_hcd *xhci,
		struct xhci_container_ctx *in_ctx,
		struct xhci_container_ctx *out_ctx)
{
	struct xhci_slot_ctx *in_slot_ctx;
	struct xhci_slot_ctx *out_slot_ctx;

	in_slot_ctx = xhci_get_slot_ctx(xhci, in_ctx);
	out_slot_ctx = xhci_get_slot_ctx(xhci, out_ctx);

	in_slot_ctx->dev_info = out_slot_ctx->dev_info;
	in_slot_ctx->dev_info2 = out_slot_ctx->dev_info2;
	in_slot_ctx->tt_info = out_slot_ctx->tt_info;
	in_slot_ctx->dev_state = out_slot_ctx->dev_state;
}
```

It resolves both containers to their slot contexts with [`xhci_get_slot_ctx()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L525) and assigns [`dev_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L343), [`dev_info2`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L344), [`tt_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L345) and [`dev_state`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L346) one for one; the reserved words at the end of the structure are left alone. Copying rather than constructing lets the route string, the speed, the hub bits and the root-hub port survive a latency change untouched. The structure itself, and the meaning of every field in it, belong to `device/slot-context.md`; this page uses one field of it:

```c
/* drivers/usb/host/xhci.h:331 */
/**
 * struct xhci_slot_ctx
 * @dev_info:	Route string, device speed, hub info, and last valid endpoint
 * @dev_info2:	Max exit latency for device number, root hub port number
 * @tt_info:	tt_info is used to construct split transaction tokens
 * @dev_state:	slot state and device address
 *
 * Slot Context - section 6.2.1.1.  This assumes the HC uses 32-byte context
 * structures.  If the HC uses 64-byte contexts, there is an additional 32 bytes
 * reserved at the end of the slot context for HC internal use.
 */
struct xhci_slot_ctx {
	__le32	dev_info;
	__le32	dev_info2;
	__le32	tt_info;
	__le32	dev_state;
	/* offset 0x10 to 0x1f reserved for HC internal use */
	__le32	reserved[4];
};
```

[`dev_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L343) holds the route string, the device speed, the hub bits and the last valid endpoint index. [`dev_info2`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L344) is the word this page writes, and the kerneldoc names its contents as the max exit latency together with the root hub port number. [`tt_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L345) carries split-transaction data that a SuperSpeed device does not use, and [`dev_state`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L346) carries the slot state and device address that this flow zeroes on the way in. The kerneldoc also notes that the reserved words assume 32-byte contexts, and that a controller using 64-byte contexts reserves another 32 bytes past the end.

The command allocation gives the command both a completion to wait on and an input context to describe:

```c
/* drivers/usb/host/xhci-mem.c:1758 */
struct xhci_command *xhci_alloc_command_with_ctx(struct xhci_hcd *xhci,
		bool allocate_completion, gfp_t mem_flags)
{
	struct xhci_command *command;

	command = xhci_alloc_command(xhci, allocate_completion, mem_flags);
	if (!command)
		return NULL;

	command->in_ctx = xhci_alloc_container_ctx(xhci, XHCI_CTX_TYPE_INPUT,
						   mem_flags);
	if (!command->in_ctx) {
		kfree(command->completion);
		kfree(command);
		return NULL;
	}
	return command;
}
```

It layers on [`xhci_alloc_command()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L1730), which stamps [`command->timeout_ms`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L541) with [`XHCI_CMD_DEFAULT_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1322), and then attaches an input container of type [`XHCI_CTX_TYPE_INPUT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L323) through [`xhci_alloc_container_ctx()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L452), unwinding the completion and the command itself if that allocation fails. Giving each command its own context lets an enable for U1 and an enable for U2 be in flight without sharing memory.

One command changes one field, and the controller writes the accepted value back into the device's output context.

```
    The device context before and after one Evaluate Context command
    ────────────────────────────────────────────────────────────────

    before the command                     after the command
    ┌──────────────────────────────┐       ┌──────────────────────────────┐
    │ output slot context          │       │ output slot context          │
    │  route, speed, hub bits      │       │  route, speed, hub bits      │
    │  Max Exit Latency = old      │       │  Max Exit Latency = new      │
    │  Root Hub Port    = p        │       │  Root Hub Port    = p        │
    │  slot state, device address  │       │  slot state, device address  │
    └───────────────┬──────────────┘       └──────────────▲───────────────┘
                    │ copied whole                        │ written by the
                    │ by xhci_slot_copy                   │ controller
                    ▼                                     │
    ┌──────────────────────────────┐       ┌──────────────┴───────────────┐
    │ input slot context           │       │ Evaluate Context command TRB │
    │  Max Exit Latency = new      │ ────▶ │ pointing at the input context│
    │  slot state, address = 0     │       │ then a Command Completion    │
    │ input control context        │       │ Event carrying a code        │
    │  add_flags carries SLOT_FLAG │       │                              │
    └──────────────────────────────┘       └──────────────────────────────┘

    virt_dev->current_mel caches the accepted value, so a second
    request for the same latency returns before any of this happens.
```

### The command is queued on the command ring and answered by a completion code

The edited input context still has to reach the controller and come back with an answer, and one function carries both of the driver's context commands to the ring and waits for them. [`xhci_configure_endpoint()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L2960) is shared between Configure Endpoint and Evaluate Context, and it opens by refusing to queue anything on a controller that has already been declared dead:

```c
/* drivers/usb/host/xhci.c:2960 */
static int xhci_configure_endpoint(struct xhci_hcd *xhci,
		struct usb_device *udev,
		struct xhci_command *command,
		bool ctx_change, bool must_succeed)
{
	int ret;
	unsigned long flags;
	struct xhci_input_control_ctx *ctrl_ctx;
	struct xhci_virt_device *virt_dev;
	struct xhci_slot_ctx *slot_ctx;

	if (!command)
		return -EINVAL;

	spin_lock_irqsave(&xhci->lock, flags);

	if (xhci->xhc_state & XHCI_STATE_DYING) {
		spin_unlock_irqrestore(&xhci->lock, flags);
		return -ESHUTDOWN;
	}
```

The `command` argument carries the input context the caller edited, `ctx_change` selects which of the two commands to queue, and `must_succeed` tells the completion handling that a failure is not expected. The [`XHCI_STATE_DYING`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1581) test under the lock returns `-ESHUTDOWN` without touching the ring, which is the answer a latency change gets once the controller has been given up on. The `ctx_change` argument then picks between the two commands at the point of queueing:

```c
/* drivers/usb/host/xhci.c:3013 in xhci_configure_endpoint() */
	if (!ctx_change)
		ret = xhci_queue_configure_endpoint(xhci, command,
				command->in_ctx->dma,
				udev->slot_id, must_succeed);
	else
		ret = xhci_queue_evaluate_context(xhci, command,
				command->in_ctx->dma,
				udev->slot_id, must_succeed);
	if (ret < 0) {
		if ((xhci->quirks & XHCI_EP_LIMIT_QUIRK))
			xhci_free_host_resources(xhci, ctrl_ctx);
		spin_unlock_irqrestore(&xhci->lock, flags);
		xhci_dbg_trace(xhci,  trace_xhci_dbg_context_change,
				"FIXME allocate a new ring segment");
		return -ENOMEM;
	}
	xhci_ring_cmd_db(xhci);
	spin_unlock_irqrestore(&xhci->lock, flags);

	/* Wait for the configure endpoint command to complete */
	wait_for_completion(command->completion);

	if (!ctx_change)
		ret = xhci_configure_endpoint_result(xhci, udev,
						     &command->status);
	else
		ret = xhci_evaluate_context_result(xhci, udev,
						   &command->status);

```

With `ctx_change` true the command goes on the ring as an Evaluate Context TRB through [`xhci_queue_evaluate_context()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ring.c#L4450), addressed by the input context's DMA address and the device's slot number. A failure to queue is reported as `-ENOMEM`, since the only reason the queue step fails here is a full ring segment. [`xhci_ring_cmd_db()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ring.c#L422) then rings the command doorbell and the lock is dropped before the wait. The wait itself is unbounded, because the command ring runs its own timer. [`xhci_alloc_command()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L1730) stamped the command with a 5000-millisecond [`XHCI_CMD_DEFAULT_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1322), the ring code schedules a delayed work item against it at [`drivers/usb/host/xhci-ring.c:439`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ring.c#L439), and [`xhci_handle_command_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ring.c#L1717) aborts the command and completes it. The full lifecycle of a command from queueing to completion event belongs to `ring/command/command-lifecycle.md`.

Everything the command touches is in host memory except the controller's own reading of it, and the figure below follows one command around that loop. Each edge carries a value, the input context's address on the way out and a completion code on the way back, and the driver is blocked for the whole of the middle.

```
    One Evaluate Context command, from the input context to the code
    ────────────────────────────────────────────────────────────────
    (the driver holds no deadline of its own; the ring's delayed
     work ends a command the controller leaves unanswered)

    ┌────────────────────────────┐
    │ input context in memory,   │
    │ one field changed,         │
    │ SLOT_FLAG in add_flags     │
    └──────────────┬─────────────┘
                   │ the TRB carries its DMA address
                   ▼
    ┌────────────────────────────┐   doorbell   ┌────────────────────┐
    │ an Evaluate Context TRB on ├─────────────▶│ the controller     │
    │ the command ring           │              │ reads the context  │
    └────────────────────────────┘              │ and accepts or     │
                                                │ refuses the value  │
    ┌────────────────────────────┐              └─────────┬──────────┘
    │ the completion code, then  │                        │
    │ an error number, or zero   │◀───────────────────────┘
    │ and a newly cached latency │   a Command Completion Event
    └────────────────────────────┘   carrying a completion code
```

The event that ends the wait carries a completion code, and the driver keeps the codes an Evaluate Context command can produce separate from the ones a Configure Endpoint command produces. The completion code is turned into an error number by a switch dedicated to this command type:

```c
/* drivers/usb/host/xhci.c:2170 */
static int xhci_evaluate_context_result(struct xhci_hcd *xhci,
		struct usb_device *udev, u32 *cmd_status)
{
	int ret;

	switch (*cmd_status) {
	case COMP_COMMAND_ABORTED:
	case COMP_COMMAND_RING_STOPPED:
		xhci_warn(xhci, "Timeout while waiting for evaluate context command\n");
		ret = -ETIME;
		break;
	case COMP_PARAMETER_ERROR:
		dev_warn(&udev->dev,
			 "WARN: xHCI driver setup invalid evaluate context command.\n");
		ret = -EINVAL;
		break;
	case COMP_SLOT_NOT_ENABLED_ERROR:
		dev_warn(&udev->dev,
			"WARN: slot not enabled for evaluate context command.\n");
		ret = -EINVAL;
		break;
	case COMP_CONTEXT_STATE_ERROR:
		dev_warn(&udev->dev,
			"WARN: invalid context state for evaluate context command.\n");
		ret = -EINVAL;
		break;
	case COMP_INCOMPATIBLE_DEVICE_ERROR:
		dev_warn(&udev->dev,
			"ERROR: Incompatible device for evaluate context command.\n");
		ret = -ENODEV;
		break;
	case COMP_MAX_EXIT_LATENCY_TOO_LARGE_ERROR:
		/* Max Exit Latency too large error */
		dev_warn(&udev->dev, "WARN: Max Exit Latency too large\n");
		ret = -EINVAL;
		break;
	case COMP_SUCCESS:
		xhci_dbg_trace(xhci, trace_xhci_dbg_context_change,
				"Successful evaluate context command");
		ret = 0;
		break;
	default:
		xhci_err(xhci, "ERROR: unexpected command completion code 0x%x.\n",
			*cmd_status);
		ret = -EINVAL;
		break;
	}
```

An aborted command or a stopped ring, which the timeout path produces, becomes `-ETIME` with a message naming the timeout. A parameter error, a slot that is not enabled and a context state the command is illegal in all become `-EINVAL`, and an incompatible device becomes `-ENODEV`. [`COMP_MAX_EXIT_LATENCY_TOO_LARGE_ERROR`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L861) has its own case, because it is the controller refusing the exact value this page computed:

```c
/* drivers/usb/host/xhci.h:860 */
#define COMP_STOPPED_SHORT_PACKET		28
#define COMP_MAX_EXIT_LATENCY_TOO_LARGE_ERROR	29
#define COMP_ISOCH_BUFFER_OVERRUN		31
```

It is completion code 29, one of the codes the controller returns in a Command Completion Event, and it means the controller cannot schedule around the latency it was given even though the value fits the field. Its neighbours in the list, [`COMP_STOPPED_SHORT_PACKET`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L860) at 28 and [`COMP_ISOCH_BUFFER_OVERRUN`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L862) at 31, show that the driver defines no name for code 30. The driver reports it and returns `-EINVAL`, which travels back out through [`xhci_change_max_exit_latency()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4517) and [`xhci_enable_usb3_lpm_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5167) to the USB core, which logs it and leaves the link state off.

### The hub timeout is written last, and a failure unwinds the controller's side

Once the controller has accepted the new latency, the timeout goes to the parent hub as a SetPortFeature request:

```c
/* drivers/usb/core/hub.c:4225 */
static int usb_set_lpm_timeout(struct usb_device *udev,
		enum usb3_link_state state, int timeout)
{
	int ret;
	int feature;

	switch (state) {
	case USB3_LPM_U1:
		feature = USB_PORT_FEAT_U1_TIMEOUT;
		break;
	case USB3_LPM_U2:
		feature = USB_PORT_FEAT_U2_TIMEOUT;
		break;
	default:
		dev_warn(&udev->dev, "%s: Can't set timeout for non-U1 or U2 state.\n",
				__func__);
		return -EINVAL;
	}

	if (state == USB3_LPM_U1 && timeout > USB3_LPM_U1_MAX_TIMEOUT &&
			timeout != USB3_LPM_DEVICE_INITIATED) {
		dev_warn(&udev->dev, "Failed to set %s timeout to 0x%x, "
				"which is a reserved value.\n",
				usb3_lpm_names[state], timeout);
		return -EINVAL;
	}

	ret = set_port_feature(udev->parent,
			USB_PORT_LPM_TIMEOUT(timeout) | udev->portnum,
			feature);
	if (ret < 0) {
		dev_warn(&udev->dev, "Failed to set %s timeout to 0x%x,"
				"error code %i\n", usb3_lpm_names[state],
				timeout, ret);
		return -EBUSY;
	}
	if (state == USB3_LPM_U1)
		udev->u1_params.timeout = timeout;
	else
		udev->u2_params.timeout = timeout;
	return 0;
}
```

The switch picks the feature selector, [`USB_PORT_FEAT_U1_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L91) or [`USB_PORT_FEAT_U2_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L92), and rejects any other state. The check that follows refuses a U1 value in the reserved range, above [`USB3_LPM_U1_MAX_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1262) and below [`USB3_LPM_DEVICE_INITIATED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1264), which is the caller's error rather than the device's; the U2 range has no such gap and needs no equivalent test. [`set_port_feature()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L464) then sends the request with the timeout packed into the upper byte of `wIndex` by [`USB_PORT_LPM_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L100) and the port number in the lower byte. Any failure becomes `-EBUSY`, and only a success records the new value in [`u1_params.timeout`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L576) or [`u2_params.timeout`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L576), which is the field [`calculate_max_exit_latency()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5123) will read next time to decide which states are live.

The hub is the second of the two holders to be written and the only one whose refusal has to be undone, so the figure below draws both outcomes of that write side by side. The three rows in each box name the same three holders, and the difference between the two boxes is the whole of what a refusal costs.

```
    The order of the two writes, and what a refused hub write undoes
    ───────────────────────────────────────────────────────────────
    (the same three holders drawn in each of the two outcomes)

    ┌───────────────────────────────────────────────────────┐
    │ first   the slot context takes the new exit latency   │
    └────────────────────────────┬──────────────────────────┘
                                 ▼
    ┌───────────────────────────────────────────────────────┐
    │ second  the parent hub is sent the new idle timeout   │
    └────────────────────────────┬──────────────────────────┘
                                 │
              ┌──────────────────┴──────────────────┐
              │ accepted                            │ refused
              ▼                                     ▼
    ┌──────────────────────────┐        ┌──────────────────────────┐
    │ slot   the new latency   │        │ slot   the old latency   │
    │ hub    the new timeout   │        │ hub    untouched         │
    │ flag   state enabled     │        │ flag   state left off    │
    └──────────────────────────┘        └────────────┬─────────────┘
                                                     ▼
                                                  -EBUSY

    the right-hand box costs a second Evaluate Context command, the
    one that puts the old latency back
```

The request itself is built from two numbers, a feature selector naming which of the two timers is meant and an index word carrying both the value and the port, and the eight-bit timeout occupies the upper half of that index. The two feature selectors and the packing macro are defined together in the hub protocol header:

```c
/* include/uapi/linux/usb/ch11.h:86 */
/*
 * Port feature selectors added by USB 3.0 spec.
 * See USB 3.0 spec Table 10-7
 */
#define USB_PORT_FEAT_LINK_STATE		5
#define USB_PORT_FEAT_U1_TIMEOUT		23
#define USB_PORT_FEAT_U2_TIMEOUT		24
#define USB_PORT_FEAT_C_PORT_LINK_STATE		25
#define USB_PORT_FEAT_C_PORT_CONFIG_ERROR	26
#define USB_PORT_FEAT_REMOTE_WAKE_MASK		27
#define USB_PORT_FEAT_BH_PORT_RESET		28
#define USB_PORT_FEAT_C_BH_PORT_RESET		29
#define USB_PORT_FEAT_FORCE_LINKPM_ACCEPT	30

#define USB_PORT_LPM_TIMEOUT(p)			(((p) & 0xff) << 8)
```

The comment cites Table 10-7 of the USB 3.0 specification as the source of the selector numbers. [`USB_PORT_FEAT_LINK_STATE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L90) is selector 5, the one U3 entry uses; [`USB_PORT_FEAT_U1_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L91) and [`USB_PORT_FEAT_U2_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L92) are 23 and 24. [`USB_PORT_LPM_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L100) shifts the eight-bit timeout into bits 15 to 8 of `wIndex`, which is where the root hub's emulation and a real hub alike expect it.

### Disabling a link state reverses the two writes

Turning a state off runs the same two writes in the opposite order, so the hub stops permitting the state before the controller stops budgeting for it:

```c
/* drivers/usb/core/hub.c:4383 */
/*
 * Disable the hub-initiated U1/U2 idle timeouts, and disable device-initiated
 * U1/U2 entry.
 *
 * If this function returns -EBUSY, the parent hub will still allow U1/U2 entry.
 * If zero is returned, the parent will not allow the link to go into U1/U2.
 *
 * If zero is returned, device-initiated U1/U2 entry may still be enabled, but
 * it won't have an effect on the bus link state because the parent hub will
 * still disallow device-initiated U1/U2 entry.
 *
 * If zero is returned, the xHCI host controller may still think U1/U2 entry is
 * possible.  The result will be slightly more bus bandwidth will be taken up
 * (to account for U1/U2 exit latency), but it should be harmless.
 */
static int usb_disable_link_state(struct usb_hcd *hcd, struct usb_device *udev,
		enum usb3_link_state state)
{
	switch (state) {
	case USB3_LPM_U1:
	case USB3_LPM_U2:
		break;
	default:
		dev_warn(&udev->dev, "%s: Can't disable non-U1 or U2 state.\n",
				__func__);
		return -EINVAL;
	}

	if (usb_set_lpm_timeout(udev, state, 0))
		return -EBUSY;

	if (hcd->driver->disable_usb3_lpm_timeout(hcd, udev, state))
		dev_warn(&udev->dev, "Could not disable xHCI %s timeout, "
				"bus schedule bandwidth may be impacted.\n",
				usb3_lpm_names[state]);

	/* As soon as usb_set_lpm_timeout(0) return 0, hub initiated LPM
	 * is disabled. Hub will disallows link to enter U1/U2 as well,
	 * even device is initiating LPM. Hence LPM is disabled if hub LPM
	 * timeout set to 0, no matter device-initiated LPM is disabled or
	 * not.
	 */
	if (state == USB3_LPM_U1)
		udev->usb3_lpm_u1_enabled = 0;
	else if (state == USB3_LPM_U2)
		udev->usb3_lpm_u2_enabled = 0;

	return 0;
}
```

The comment above the function is explicit about what a partial failure leaves behind, and the two failure modes differ in direction. A failed hub write returns `-EBUSY` with the hub still allowing entry, while a failed controller call is only logged, because it leaves the controller reserving bandwidth for a state that will never be entered. According to the comment at the end, once the hub timeout is zero the hub disallows the link state whether or not device-initiated entry is still permitted, which is why both [`usb3_lpm_u1_enabled`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L708) and [`usb3_lpm_u2_enabled`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L709) can be cleared at that point.

The two directions write the same two holders, and the order protects one invariant. At every instant the Max Exit Latency in the slot context has to cover every state the parent hub is permitted to park the link in, so enabling raises the budget before it grants the permission and disabling withdraws the permission before it lowers the budget. The figure below draws the two as pulses on one timeline, the budget above and the permission below, and the containment reads straight off the picture, because the upper pulse rises first and falls last.

```
    The controller's budget encloses the hub's permission
    ─────────────────────────────────────────────────────
    (two traces on one timeline; the upper pulse rises first and
     falls last, so there is no instant at which the hub may park
     the link in a state the controller has not budgeted for)

    time ────────────────────────────────────────────────────────▶

    Max Exit Latency          ┌───────────────────────────────┐
    in the slot context    ───┘ raised                lowered └─────

    hub idle timeout               ┌───────────────────┐
    for the state          ────────┘ set          zero └──────────────
                              ╎    ╎                   ╎      ╎
                              1    2                   3      4

    1 budget raised, then 2 permission granted             (enable)
    3 permission withdrawn, then 4 budget lowered          (disable)
```

The same asymmetry runs across the two directions. On the enable side a refused hub write is fatal and the budget is unwound at [`drivers/usb/core/hub.c:4372`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4372), because the permission never arrived and a raised latency would describe a state the hub will not allow. On the disable side a failed lowering is only the warning the excerpt above prints, because the permission is already gone by then, the link is safe whatever the slot context still holds, and the bus schedule is left reserving more room than the device needs.

Only the second of the two steps reaches the xHCI driver, and it arrives with the link state already decided and the hub already refusing every transition into it. The driver side of the disable is shorter than the enable, because there is nothing to compute per endpoint:

```c
/* drivers/usb/host/xhci.c:5209 */
static int xhci_disable_usb3_lpm_timeout(struct usb_hcd *hcd,
			struct usb_device *udev, enum usb3_link_state state)
{
	struct xhci_hcd	*xhci;
	u16 mel;

	xhci = hcd_to_xhci(hcd);
	if (!xhci || !(xhci->quirks & XHCI_LPM_SUPPORT) ||
			!xhci->devs[udev->slot_id])
		return 0;

	mel = calculate_max_exit_latency(udev, state, USB3_LPM_DISABLED);
	return xhci_change_max_exit_latency(xhci, udev, mel);
}
```

It repeats the quirk and slot guards, then calls [`calculate_max_exit_latency()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5123) with [`USB3_LPM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1261) as the hub-encoded timeout for the named state, which is exactly the input that makes the `disabling_u1` or `disabling_u2` boolean true and drops that state out of the maximum. The result goes straight to [`xhci_change_max_exit_latency()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4517), and its return is the function's return, so a failed command is a failed disable. Neither the tier policy nor the port's [`lpm_incapable`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1480) bit is consulted here, since turning a state off is always allowed.

### Device-initiated entry is a separate permission with its own ceilings

Hub-initiated entry and device-initiated entry are two permissions, and the second one is granted with control transfers to the device rather than to the hub. It is prepared once at enumeration, when the device is told the latencies it must respect:

```c
/* drivers/usb/core/hub.c:4097 */
/*
 * Send a Set SEL control transfer to the device, prior to enabling
 * device-initiated U1 or U2.  This lets the device know the exit latencies from
 * the time the device initiates a U1 or U2 exit, to the time it will receive a
 * packet from the host.
 *
 * This function will fail if the SEL or PEL values for udev are greater than
 * the maximum allowed values for the link state to be enabled.
 */
static int usb_req_set_sel(struct usb_device *udev)
{
	struct usb_set_sel_req *sel_values;
	unsigned long long u1_sel;
	unsigned long long u1_pel;
	unsigned long long u2_sel;
	unsigned long long u2_pel;
	int ret;

	if (!udev->parent || udev->speed < USB_SPEED_SUPER || !udev->lpm_capable)
		return 0;

	/* Convert SEL and PEL stored in ns to us */
	u1_sel = DIV_ROUND_UP(udev->u1_params.sel, 1000);
	u1_pel = DIV_ROUND_UP(udev->u1_params.pel, 1000);
	u2_sel = DIV_ROUND_UP(udev->u2_params.sel, 1000);
	u2_pel = DIV_ROUND_UP(udev->u2_params.pel, 1000);

	/*
	 * Make sure that the calculated SEL and PEL values for the link
	 * state we're enabling aren't bigger than the max SEL/PEL
	 * value that will fit in the SET SEL control transfer.
	 * Otherwise the device would get an incorrect idea of the exit
	 * latency for the link state, and could start a device-initiated
	 * U1/U2 when the exit latencies are too high.
	 */
	if (u1_sel > USB3_LPM_MAX_U1_SEL_PEL ||
	    u1_pel > USB3_LPM_MAX_U1_SEL_PEL ||
	    u2_sel > USB3_LPM_MAX_U2_SEL_PEL ||
	    u2_pel > USB3_LPM_MAX_U2_SEL_PEL) {
		dev_dbg(&udev->dev, "Device-initiated U1/U2 disabled due to long SEL or PEL\n");
		return -EINVAL;
	}
```

The four values are converted from the nanoseconds the kernel stores to the microseconds the request carries, and each is checked against the ceiling of the field it must fit, [`USB3_LPM_MAX_U1_SEL_PEL`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1278) for the two U1 values and [`USB3_LPM_MAX_U2_SEL_PEL`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1279) for the two U2 values. The comment explains the consequence of skipping that check, that a device given a truncated latency would form an incorrect idea of the exit cost and could start a transition when the real cost is higher.

```c
/* drivers/usb/core/hub.c:4145 */
	sel_values = kmalloc_obj(*(sel_values), GFP_NOIO);
	if (!sel_values)
		return -ENOMEM;

	sel_values->u1_sel = u1_sel;
	sel_values->u1_pel = u1_pel;
	sel_values->u2_sel = cpu_to_le16(u2_sel);
	sel_values->u2_pel = cpu_to_le16(u2_pel);

	ret = usb_control_msg(udev, usb_sndctrlpipe(udev, 0),
			USB_REQ_SET_SEL,
			USB_RECIP_DEVICE,
			0, 0,
			sel_values, sizeof *(sel_values),
			USB_CTRL_SET_TIMEOUT);
	kfree(sel_values);

	if (ret > 0)
		udev->lpm_devinit_allow = 1;

	return ret;
}
```

The allocation uses [`GFP_NOIO`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/gfp_types.h#L380) for the reason the comment gives, that this path can run inside a failed device reset started from a storage driver's error handling. The four values are packed into a [`struct usb_set_sel_req`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1266), with the U2 pair converted to little-endian because they are two bytes each, and sent as a [`USB_REQ_SET_SEL`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L89) control transfer. A positive return sets [`lpm_devinit_allow`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L703), the flag every later device-initiated decision is gated on.

Granting the permission at enable time then has one further condition, on the relationship between the exit latency and the shortest periodic service interval the device has open:

```c
/* drivers/usb/core/hub.c:4268 */
/*
 * Don't allow device intiated U1/U2 if device isn't in the configured state,
 * or the system exit latency + one bus interval is greater than the minimum
 * service interval of any active periodic endpoint. See USB 3.2 section 9.4.9
 */
static bool usb_device_may_initiate_lpm(struct usb_device *udev,
					enum usb3_link_state state)
{
	unsigned int sel;		/* us */
	int i, j;

	if (!udev->lpm_devinit_allow || !udev->actconfig)
		return false;

	if (state == USB3_LPM_U1)
		sel = DIV_ROUND_UP(udev->u1_params.sel, 1000);
	else if (state == USB3_LPM_U2)
		sel = DIV_ROUND_UP(udev->u2_params.sel, 1000);
	else
		return false;

	for (i = 0; i < udev->actconfig->desc.bNumInterfaces; i++) {
		struct usb_interface *intf;
		struct usb_endpoint_descriptor *desc;
		unsigned int interval;

		intf = udev->actconfig->interface[i];
		if (!intf)
			continue;

		for (j = 0; j < intf->cur_altsetting->desc.bNumEndpoints; j++) {
			desc = &intf->cur_altsetting->endpoint[j].desc;

			if (usb_endpoint_xfer_int(desc) ||
			    usb_endpoint_xfer_isoc(desc)) {
				interval = (1 << (desc->bInterval - 1)) * 125;
				if (sel + 125 > interval)
					return false;
			}
		}
	}
	return true;
}
```

The comment cites section 9.4.9 of the USB 3.2 specification for the rule the loop implements. Every interrupt and isochronous endpoint of every current alternate setting has its interval computed in microseconds from [`bInterval`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L422), and the function refuses if the state's SEL plus one bus interval of 125 microseconds exceeds it. A device whose link would still be waking when its next service is due is left without the permission.

The permission itself is one control transfer per state:

```c
/* drivers/usb/core/hub.c:4168 */
/*
 * Enable or disable device-initiated U1 or U2 transitions.
 */
static int usb_set_device_initiated_lpm(struct usb_device *udev,
		enum usb3_link_state state, bool enable)
{
	int ret;
	int feature;

	switch (state) {
	case USB3_LPM_U1:
		feature = USB_DEVICE_U1_ENABLE;
		break;
	case USB3_LPM_U2:
		feature = USB_DEVICE_U2_ENABLE;
		break;
	default:
		dev_warn(&udev->dev, "%s: Can't %s non-U1 or U2 state.\n",
				__func__, str_enable_disable(enable));
		return -EINVAL;
	}

	if (udev->state != USB_STATE_CONFIGURED) {
		dev_dbg(&udev->dev, "%s: Can't %s %s state "
				"for unconfigured device.\n",
				__func__, str_enable_disable(enable),
				usb3_lpm_names[state]);
		return -EINVAL;
	}

```

The feature selector is [`USB_DEVICE_U1_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L152) or [`USB_DEVICE_U2_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L153), and an unconfigured device is refused outright, because the feature is only meaningful once a configuration is selected. Both selectors address the device itself, which is why the request is a control transfer to endpoint zero and carries no data stage in either direction, and the same function sends the clearing request when the permission is withdrawn.

```c
/* drivers/usb/core/hub.c:4198 */
	if (enable) {
		/*
		 * Now send the control transfer to enable device-initiated LPM
		 * for either U1 or U2.
		 */
		ret = usb_control_msg(udev, usb_sndctrlpipe(udev, 0),
				USB_REQ_SET_FEATURE,
				USB_RECIP_DEVICE,
				feature,
				0, NULL, 0,
				USB_CTRL_SET_TIMEOUT);
	} else {
		ret = usb_control_msg(udev, usb_sndctrlpipe(udev, 0),
				USB_REQ_CLEAR_FEATURE,
				USB_RECIP_DEVICE,
				feature,
				0, NULL, 0,
				USB_CTRL_SET_TIMEOUT);
	}
	if (ret < 0) {
		dev_warn(&udev->dev, "%s of device-initiated %s failed.\n",
			 str_enable_disable(enable), usb3_lpm_names[state]);
		return -EBUSY;
	}
	return 0;
}
```

Enabling sends [`USB_REQ_SET_FEATURE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L80) and disabling sends [`USB_REQ_CLEAR_FEATURE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L79), with the same selector and no data stage in either direction. Any failure becomes `-EBUSY` after a warning naming the state, which makes [`usb_enable_lpm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4503) stop after U1 rather than go on to U2.

Hub-initiated entry needs the hub to hold a timeout and nothing else; device-initiated entry needs that same timeout and then two further conditions the device itself has to satisfy, so the second permission is contained in the first. The hub's timeout has its own ceiling, `0x7F` for U1 and `0xFE` for U2. An accepted Set SEL request means the device's SEL and PEL fit the request's fields, whose ceiling is `0xFF` for the U1 pair and `0xFFFF` for U2. The last condition is that SEL plus one 125 us bus interval fits inside every periodic service interval the device has, and only then is the SetFeature request sent to the device itself.

### An enabled link state adds a precondition to eight paths in the USB core

With a state enabled, the parking and unparking happen in the link hardware and in the hub, so no kernel code starts running that was not running before and none stops. What changes is a precondition on a set of paths elsewhere in the USB core, all of which reach the same two functions. The membership test is a call to [`usb_disable_lpm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4440) or [`usb_unlocked_disable_lpm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4479) outside those two functions' own definitions and outside the stubs compiled when [`CONFIG_PM`](https://elixir.bootlin.com/linux/v7.0/source/kernel/power/Kconfig#L216) is clear. A grep for both call forms across the whole tree at this version, headers included, finds eight such sites, all in `drivers/usb/core/`.

| site | what it is about to do | re-enabled at |
|---|---|---|
| [`drivers/usb/core/driver.c:378`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/driver.c#L378) | bind an interface driver that set [`disable_hub_initiated_lpm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L1271) | [`drivers/usb/core/driver.c:404`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/driver.c#L404) and [`drivers/usb/core/driver.c:416`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/driver.c#L416) on the failure paths |
| [`drivers/usb/core/driver.c:449`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/driver.c#L449) | unbind such a driver | [`drivers/usb/core/driver.c:504`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/driver.c#L504) |
| [`drivers/usb/core/message.c:1488`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/message.c#L1488) | tear the device's configuration down in [`usb_disable_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/message.c#L1450) | nowhere; the device leaves the configured state |
| [`drivers/usb/core/message.c:1626`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/message.c#L1626) | change an alternate setting in [`usb_set_interface()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/message.c#L1585) | [`drivers/usb/core/message.c:1639`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/message.c#L1639), [`drivers/usb/core/message.c:1664`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/message.c#L1664) and [`drivers/usb/core/message.c:1686`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/message.c#L1686) |
| [`drivers/usb/core/message.c:1772`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/message.c#L1772) | reinstall the configuration in [`usb_reset_configuration()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/message.c#L1750) | [`drivers/usb/core/message.c:1781`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/message.c#L1781), [`drivers/usb/core/message.c:1791`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/message.c#L1791) and [`drivers/usb/core/message.c:1824`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/message.c#L1824) |
| [`drivers/usb/core/message.c:2138`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/message.c#L2138) | select a configuration in [`usb_set_configuration()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/message.c#L2054) | [`drivers/usb/core/message.c:2147`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/message.c#L2147) and [`drivers/usb/core/message.c:2241`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/message.c#L2241) |
| [`drivers/usb/core/port.c:297`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/port.c#L297) | apply a new per-port policy written through sysfs | [`drivers/usb/core/port.c:298`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/port.c#L298) |
| [`drivers/usb/core/port.c:461`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/port.c#L461) | shut the port device down | nowhere; the port is going away |

Every one of them has to disable first for the same reason. Each is about to change the endpoint set or the configuration that [`xhci_calculate_lpm_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5059) scans, so the timeout in the hub and the latency in the slot context would describe a device that no longer exists. The comment at [`drivers/usb/core/message.c:1623`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/message.c#L1623) states it directly for the alternate-setting case, that link power management is disabled and re-enabled around the change "so that the xHCI driver can recalculate the U1/U2 timeouts":

```c
/* drivers/usb/core/message.c:1620 in usb_set_interface() */
	 * Remove the current alt setting and add the new alt setting.
	 */
	mutex_lock(hcd->bandwidth_mutex);
	/* Disable LPM, and re-enable it once the new alt setting is installed,
	 * so that the xHCI driver can recalculate the U1/U2 timeouts.
	 */
	if (usb_disable_lpm(dev)) {
		dev_err(&iface->dev, "%s Failed to disable LPM\n", __func__);
		mutex_unlock(hcd->bandwidth_mutex);
		return -ENOMEM;
	}
	/* Changing alt-setting also frees any allocated streams */
	for (i = 0; i < iface->cur_altsetting->desc.bNumEndpoints; i++)
		iface->cur_altsetting->endpoint[i].streams = 0;

	ret = usb_hcd_alloc_bandwidth(dev, NULL, iface->cur_altsetting, alt);
	if (ret < 0) {
		dev_info(&dev->dev, "Not enough bandwidth for altsetting %d\n",
				alternate);
		usb_enable_lpm(dev);
		mutex_unlock(hcd->bandwidth_mutex);
		return ret;
	}
```

The disable happens with [`hcd->bandwidth_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L185) already held, which is why the plain [`usb_disable_lpm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4440) is used here rather than the locking wrapper, and a failure aborts the whole alternate-setting change with `-ENOMEM` before any bandwidth is allocated.

Nesting is handled by a count rather than a flag, so overlapping requests compose:

```c
/* drivers/usb/core/hub.c:4433 */
/*
 * Disable hub-initiated and device-initiated U1 and U2 entry.
 * Caller must own the bandwidth_mutex.
 *
 * This will call usb_enable_lpm() on failure, which will decrement
 * lpm_disable_count, and will re-enable LPM if lpm_disable_count reaches zero.
 */
int usb_disable_lpm(struct usb_device *udev)
{
	struct usb_hcd *hcd;
	int err;

	if (!udev || !udev->parent ||
			udev->speed < USB_SPEED_SUPER ||
			!udev->lpm_capable ||
			udev->state < USB_STATE_CONFIGURED)
		return 0;

	hcd = bus_to_hcd(udev->bus);
	if (!hcd || !hcd->driver->disable_usb3_lpm_timeout)
		return 0;

	udev->lpm_disable_count++;
	if ((udev->u1_params.timeout == 0 && udev->u2_params.timeout == 0))
		return 0;

	/* If LPM is enabled, attempt to disable it. */
	if (usb_disable_link_state(hcd, udev, USB3_LPM_U1))
		goto disable_failed;
	if (usb_disable_link_state(hcd, udev, USB3_LPM_U2))
		goto disable_failed;

	err = usb_set_device_initiated_lpm(udev, USB3_LPM_U1, false);
	if (!err)
		usb_set_device_initiated_lpm(udev, USB3_LPM_U2, false);

	return 0;

disable_failed:
	udev->lpm_disable_count--;

	return -EBUSY;
}
```

The body has two returns that leave the count raised, the early one taken when both timeouts already read zero and the ordinary one at the end. The two writes can therefore happen only at the rise from zero, because a later rise finds both timeouts already at zero and takes that early return before reaching either of them.

The count and the two per-state parameter records are neighbours in the device structure:

```c
/* include/linux/usb.h:737 */
	int slot_id;
	struct usb2_lpm_parameters l1_params;
	struct usb3_lpm_parameters u1_params;
	struct usb3_lpm_parameters u2_params;
	unsigned lpm_disable_count;
```

[`slot_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L737) is the controller's slot number for this device, [`l1_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L738) holds the USB 2.0 link-power parameters that `pm/usb2-device-pm.md` covers, [`u1_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L739) and [`u2_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L740) are the two records this page reads and writes, and [`lpm_disable_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L741) is the reference count that gates both of them.

[`lpm_disable_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L741) is incremented before anything is turned off, and the early return that follows it covers the case where both timeouts are already zero, so the count still rises for a device whose link power management was never on. Both states are then disabled in turn, and device-initiated entry is cleared for U1 and, if that succeeded, for U2. The `disable_failed` label decrements the count again, so a failed disable leaves the count where it was.

Every one of the eight paths puts the same bracket around the change it is about to make, and the figure below draws those brackets as three nested spans on one timeline. The two rows beneath them are the holders this page has followed throughout, the idle timeout in the parent hub and the Max Exit Latency in the slot context, and both read zero across the whole of the middle span. Neither holder is an actor, so a swimlane has no lane to put them in; a span figure does, because a holder's row can carry the value it holds at each instant.

```
    What the two holders read while link power management is off
    ────────────────────────────────────────────────────────────

    time ─────────────────────────────────────────────────────▶
    bandwidth_mutex   ├───────────────────────────────────────┤
    both states off       ├───────────────────────────────┤
    the change itself         ├───────────────────────┤
                          ╎                               ╎
    hub idle timeout  old ╎ 0  0  0  0  0  0  0  0  0  0  ╎ recomputed
    slot exit latency old ╎ 0                             ╎ new

    two of the eight paths never close the bracket, because the
    device or the port is gone by the time it would be re-enabled
```

The table at the head of this section carries the same two facts for each of the eight paths, the change it is about to make and where it re-enables, and the two rows whose re-enable cell reads nowhere are the two spans that never close. The closing half of the bracket is the enable side, and it mirrors the function above. It lowers the count first, returns while any other caller still holds link power management off, and only then looks up the parent port and asks for each state that port permits:

```c
/* drivers/usb/core/hub.c:4495 */
/*
 * Attempt to enable device-initiated and hub-initiated U1 and U2 entry.  The
 * xHCI host policy may prevent U1 or U2 from being enabled.
 *
 * Other callers may have disabled link PM, so U1 and U2 entry will be disabled
 * until the lpm_disable_count drops to zero.  Caller must own the
 * bandwidth_mutex.
 */
void usb_enable_lpm(struct usb_device *udev)
{
	struct usb_hcd *hcd;
	struct usb_hub *hub;
	struct usb_port *port_dev;

	if (!udev || !udev->parent ||
			udev->speed < USB_SPEED_SUPER ||
			!udev->lpm_capable ||
			udev->state < USB_STATE_CONFIGURED)
		return;

	udev->lpm_disable_count--;
	hcd = bus_to_hcd(udev->bus);
	/* Double check that we can both enable and disable LPM.
	 * Device must be configured to accept set feature U1/U2 timeout.
	 */
	if (!hcd || !hcd->driver->enable_usb3_lpm_timeout ||
			!hcd->driver->disable_usb3_lpm_timeout)
		return;

	if (udev->lpm_disable_count > 0)
		return;

	hub = usb_hub_to_struct_hub(udev->parent);
	if (!hub)
		return;

	port_dev = hub->ports[udev->portnum - 1];

	if (port_dev->usb3_lpm_u1_permit)
		if (usb_enable_link_state(hcd, udev, USB3_LPM_U1))
			return;

	if (port_dev->usb3_lpm_u2_permit)
		if (usb_enable_link_state(hcd, udev, USB3_LPM_U2))
			return;

```

The enable side decrements first and returns while the count is still positive, so the last caller to release is the one that re-enables. The device has to be a SuperSpeed device below a real parent, marked [`lpm_capable`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L702) and configured, and the host controller has to offer both hooks, since a controller that can enable a state but not disable it again would be unusable here. The parent's [`struct usb_port`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.h#L101) then gates each state separately through [`usb3_lpm_u1_permit`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.h#L119) and [`usb3_lpm_u2_permit`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.h#L120), and a failure to enable U1 returns without attempting U2.

```c
/* drivers/usb/core/hub.c:4541 end of usb_enable_lpm() */
	/*
	 * Enable device initiated U1/U2 with a SetFeature(U1/U2_ENABLE) request
	 * if system exit latency is short enough and device is configured
	 */
	if (usb_device_may_initiate_lpm(udev, USB3_LPM_U1)) {
		if (usb_set_device_initiated_lpm(udev, USB3_LPM_U1, true))
			return;

		if (usb_device_may_initiate_lpm(udev, USB3_LPM_U2))
			usb_set_device_initiated_lpm(udev, USB3_LPM_U2, true);
	}
}
```

Device-initiated entry is attempted only after the hub-initiated side is done, and only for U1 first, with U2 offered exclusively when U1 was granted, which the nesting of the two conditions expresses.

An interface driver that cannot tolerate the parent hub parking its link says so once, in its [`struct usb_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L1244):

```c
/* include/linux/usb.h:1269 */
	unsigned int no_dynamic_id:1;
	unsigned int supports_autosuspend:1;
	unsigned int disable_hub_initiated_lpm:1;
	unsigned int soft_unbind:1;
};
```

[`disable_hub_initiated_lpm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L1271) is a single bit in the run of driver flags that closes the structure, beside [`no_dynamic_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L1269), [`supports_autosuspend`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L1270) and [`soft_unbind`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L1272), and its kerneldoc at [`include/linux/usb.h:1225`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L1225) says exactly what it costs the driver, that hubs will not initiate a transition on an idle timeout while device-initiated entry stays available. A tree-wide grep for the initializer form `.disable_hub_initiated_lpm = 1` across every `.c` file at this version finds 67 files setting it, one per file, spread over five subsystem areas.

| area | files setting the bit |
|---|---|
| `drivers/net/usb/` | 34 |
| `drivers/net/wireless/` | 24 |
| `drivers/bluetooth/` | 5 |
| `drivers/usb/class/` | 2 |
| `drivers/nfc/` | 1 |
| `drivers/isdn/` | 1 |

One of them is the USB Ethernet driver in [`drivers/net/usb/r8152.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/net/usb/r8152.c), whose file carries substantive changes as recently as February 2026. It sets the bit in its driver structure:

```c
/* drivers/net/usb/r8152.c:10066 */
	.probe =	rtl8152_probe,
	.disconnect =	rtl8152_disconnect,
	.suspend =	rtl8152_suspend,
	.resume =	rtl8152_resume,
	.reset_resume =	rtl8152_reset_resume,
	.pre_reset =	rtl8152_pre_reset,
	.post_reset =	rtl8152_post_reset,
	.supports_autosuspend = 1,
	.disable_hub_initiated_lpm = 1,
};
```

and then re-enables link power management itself at five points where its own power-state routines have finished reconfiguring the device, the first of them at [`drivers/net/usb/r8152.c:7165`](https://elixir.bootlin.com/linux/v7.0/source/drivers/net/usb/r8152.c#L7165), calling [`usb_enable_lpm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4503) directly. The bit and the calls do different jobs. The bit removes hub-initiated entry for as long as the driver is bound, and the calls release the reference count the driver's own reset and resume handling took.

### Two sysfs files and one firmware method refuse link power management

Policy can refuse a link state whatever the arithmetic produces, and three separate inputs carry such a refusal. The first is per port and writable from userspace. [`usb3_lpm_permit_store()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/port.c#L262) parses one of four strings into the port's two permit bits:

```c
/* drivers/usb/core/port.c:262 */
static ssize_t usb3_lpm_permit_store(struct device *dev,
			       struct device_attribute *attr,
			       const char *buf, size_t count)
{
	struct usb_port *port_dev = to_usb_port(dev);
	struct usb_device *udev = port_dev->child;
	struct usb_hcd *hcd;

	if (!strncmp(buf, "u1_u2", 5)) {
		port_dev->usb3_lpm_u1_permit = 1;
		port_dev->usb3_lpm_u2_permit = 1;

	} else if (!strncmp(buf, "u1", 2)) {
		port_dev->usb3_lpm_u1_permit = 1;
		port_dev->usb3_lpm_u2_permit = 0;

	} else if (!strncmp(buf, "u2", 2)) {
		port_dev->usb3_lpm_u1_permit = 0;
		port_dev->usb3_lpm_u2_permit = 1;

	} else if (!strncmp(buf, "0", 1)) {
		port_dev->usb3_lpm_u1_permit = 0;
		port_dev->usb3_lpm_u2_permit = 0;
	} else
		return -EINVAL;

```

The four accepted strings map onto the four combinations of the two bits, and anything else is `-EINVAL`. The matching read handler at [`drivers/usb/core/port.c:241`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/port.c#L241) renders the same four strings back. Because the bits are consulted only when a state is being enabled, a write has to force a re-evaluation to take effect on a device already attached:

```c
/* drivers/usb/core/port.c:288 */
	/* If device is connected to the port, disable or enable lpm
	 * to make new u1 u2 setting take effect immediately.
	 */
	if (udev) {
		hcd = bus_to_hcd(udev->bus);
		if (!hcd)
			return -EINVAL;
		usb_lock_device(udev);
		mutex_lock(hcd->bandwidth_mutex);
		if (!usb_disable_lpm(udev))
			usb_enable_lpm(udev);
		mutex_unlock(hcd->bandwidth_mutex);
		usb_unlock_device(udev);
	}

	return count;
}
static DEVICE_ATTR_RW(usb3_lpm_permit);
```

The comment says why the round trip is there, to make the new setting take effect immediately. It takes the device lock and [`hcd->bandwidth_mutex`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L185), disables link power management, and re-enables it only if the disable succeeded, which runs the whole enable path again with the new permit bits in place. The [`DEVICE_ATTR_RW`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device.h#L180) line at the end of the block is where the two handlers are bound, because the macro pastes `_show` and `_store` onto the file name, so [`usb3_lpm_permit_show()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/port.c#L241) and [`usb3_lpm_permit_store()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/port.c#L262) become the read and write handlers of a file called `usb3_lpm_permit`. The file exists only on a SuperSpeed port, because it is in a separate attribute group:

```c
/* drivers/usb/core/port.c:322 */
static const struct attribute_group *port_dev_group[] = {
	&port_dev_attr_grp,
	NULL,
};

static struct attribute *port_dev_usb3_attrs[] = {
	&dev_attr_usb3_lpm_permit.attr,
	NULL,
};

static const struct attribute_group port_dev_usb3_attr_grp = {
	.attrs = port_dev_usb3_attrs,
};

static const struct attribute_group *port_dev_usb3_group[] = {
	&port_dev_attr_grp,
	&port_dev_usb3_attr_grp,
	NULL,
};
```

[`port_dev_group`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/port.c#L322) is the group list every port device gets, holding the attribute group common to both speeds. [`port_dev_usb3_attrs`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/port.c#L327) is a one-entry attribute array holding the permit file, wrapped by [`port_dev_usb3_attr_grp`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/port.c#L332), and [`port_dev_usb3_group`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/port.c#L336) is the same common group with that extra one appended. The choice between the two lists is made when the port device is created, in the same block that gives the two permit bits their default of enabled:

```c
/* drivers/usb/core/port.c:755 */
	set_bit(port1, hub->power_bits);
	port_dev->dev.parent = hub->intfdev;
	if (hub_is_superspeed(hdev)) {
		port_dev->is_superspeed = 1;
		port_dev->usb3_lpm_u1_permit = 1;
		port_dev->usb3_lpm_u2_permit = 1;
		port_dev->dev.groups = port_dev_usb3_group;
	} else
		port_dev->dev.groups = port_dev_group;
```

The speed test does two jobs in the same place, choosing which attribute list the port device carries and seeding the two permit bits, so the file and the bits it writes appear on a port together. Both bits default to 1, so a SuperSpeed port permits both states until userspace says otherwise. The bits are the last two members of the port device:

```c
/* drivers/usb/core/hub.h:101 */
struct usb_port {
	struct usb_device *child;
	struct device dev;
...
/* drivers/usb/core/hub.h:114 */
	u8 portnum;
...
/* drivers/usb/core/hub.h:118 */
	unsigned int is_superspeed:1;
	unsigned int usb3_lpm_u1_permit:1;
	unsigned int usb3_lpm_u2_permit:1;
};
```

[`child`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.h#L102) is the device attached to the port, which is how [`usb3_lpm_permit_store()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/port.c#L262) finds a device to re-evaluate. [`dev`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.h#L103) is the embedded device that carries the sysfs files. [`portnum`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.h#L114) is the port's one-based number within its hub, the index [`usb_enable_lpm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4503) uses in reverse to find the port from the device. [`is_superspeed`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.h#L118) selects the attribute group, and [`usb3_lpm_u1_permit`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.h#L119) and [`usb3_lpm_u2_permit`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.h#L120) are this page's two policy bits. The two elisions drop thirteen members that carry port ownership and the peer link, the Type-C connector, the PM QoS request, the connect type and device state, the location and its status lock, the over-current count, the quirks word and its two behavioural bits, all of which belong to port power and hot-plug and are covered by `pm/port-power-management.md` and `ports/port-hotplug.md`.

The second input is per device and read-only. Two files report whether each state ended up enabled, and they read the bits [`usb_enable_link_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4327) set:

```c
/* drivers/usb/core/sysfs.c:574 */
static ssize_t usb3_hardware_lpm_u1_show(struct device *dev,
				      struct device_attribute *attr, char *buf)
{
	struct usb_device *udev = to_usb_device(dev);
	const char *p;
	int rc;

	rc = usb_lock_device_interruptible(udev);
	if (rc < 0)
		return -EINTR;

	if (udev->usb3_lpm_u1_enabled)
		p = "enabled";
	else
		p = "disabled";

	usb_unlock_device(udev);

	return sysfs_emit(buf, "%s\n", p);
}
static DEVICE_ATTR_RO(usb3_hardware_lpm_u1);
```

The device lock is taken interruptibly around the read, so the value cannot change under a concurrent enable, and the file renders the single bit as `enabled` or `disabled`. Those bits are two of a run of link-power flags in the device structure:

```c
/* include/linux/usb.h:702 */
	unsigned lpm_capable:1;
	unsigned lpm_devinit_allow:1;
	unsigned usb2_hw_lpm_capable:1;
	unsigned usb2_hw_lpm_besl_capable:1;
	unsigned usb2_hw_lpm_enabled:1;
	unsigned usb2_hw_lpm_allowed:1;
	unsigned usb3_lpm_u1_enabled:1;
	unsigned usb3_lpm_u2_enabled:1;
```

[`lpm_capable`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L702) is the device's overall eligibility, decided at enumeration. [`lpm_devinit_allow`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L703) is the Set SEL outcome. The four bits from [`usb2_hw_lpm_capable`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L704) down to [`usb2_hw_lpm_allowed`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L707) belong to the other generation and to `pm/usb2-device-pm.md`. [`usb3_lpm_u1_enabled`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L708) and [`usb3_lpm_u2_enabled`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L709) are this page's two, one per state.

The third input is firmware, through [`port->lpm_incapable`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1480), and it differs from the other two in being invisible to userspace and applying only to a device on a root port. It is also the only one of the three that the xHCI driver evaluates itself; the two sysfs inputs are read entirely inside the USB core, and the driver never sees them.

The three inputs are read at three different points of one enable request, and two of them can end it. The parent port's permit bit for the state, kept per port and set from sysfs, is read first, inside the USB core, and a clear bit skips the state so that the request ends there. The root-hub port's [`lpm_incapable`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1480) bit, kept per port and set from firmware, is read next, inside the driver's hook, and a set bit answers [`USB3_LPM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1261) with nothing written anywhere. Past both, the arithmetic runs and both writes land, after which the two per-device enabled bits are written and read back through sysfs, where they record what the request achieved.

### U3 is entered by a request rather than a timer

U3 has no idle timer and no timeout to compute, which is why nothing on this page touches it. It is entered when the USB core suspends a device, where [`usb_port_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L3501) calls [`hub_set_port_link_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L1007) at [`drivers/usb/core/hub.c:3540`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L3540) with [`USB_SS_PORT_LS_U3`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L159), which becomes a SetPortFeature request naming [`USB_PORT_FEAT_LINK_STATE`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch11.h#L90). On a root-hub port that request reaches [`xhci_set_link_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L798), which writes the PLS field behind its write strobe. That function and the port machinery around it, from the write strobe through the resume handshake to the ACPI power hand-off, are `pm/port-power-management.md`'s subject, and this page reaches no further into them than naming the seam.

The two mechanisms differ in what the kernel supplies and in when the parking happens. The figure below puts one link's traffic on a time axis, so that the hub-initiated case reads as a stretch of idleness as long as the timeout this page computes, and the U3 request reads as a single point that parks the link the moment it arrives.

```
    A timer parks a link in U1 or U2; a request parks it in U3
    ──────────────────────────────────────────────────────────
    (one link's traffic against time; the parked state begins where
     each arrow lands)

    time ────────────────────────────────────────────────────▶
    link      ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
                          ├── hub idle timeout ──┤
    U1 or U2                                     ▲ the hub parks the link
                                                   when the timer runs out
    U3                          ▲ SetPortFeature(LINK_STATE, U3)
                                  parks it at once, timer or no timer
```

### USB3 device power management is programmed through the device context and USB2 through the port registers

The two generations put the idle timer in different places, and the tree says why. USB 2.0 hardware link power management is offered only to a device whose parent is the root hub, which the guards at the top of [`xhci_set_usb2_hardware_lpm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4647) enforce:

```c
/* drivers/usb/host/xhci.c:4659 in xhci_set_usb2_hardware_lpm() */
	if (xhci->quirks & XHCI_HW_LPM_DISABLE)
		return -EPERM;

	if (hcd->speed >= HCD_USB3 || !xhci->hw_lpm_support ||
			!udev->lpm_capable)
		return -EPERM;

	if (!udev->parent || udev->parent->parent ||
			udev->descriptor.bDeviceClass == USB_CLASS_HUB)
		return -EPERM;

	if (udev->usb2_hw_lpm_capable != 1)
		return -EPERM;
```

The test `!udev->parent || udev->parent->parent` rejects the root hub itself and any device below an external hub, and the class test rejects hubs. The same three conditions appear again in [`xhci_update_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4741) at [`drivers/usb/host/xhci.c:4765`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4765), where the capability is first advertised. For such a device the host controller is the parent hub, so the timer belongs to the controller and the driver writes it into the controller's own port register directly:

```c
/* drivers/usb/host/xhci.c:4714 in xhci_set_usb2_hardware_lpm() */
		pm_val &= ~PORT_HIRD_MASK;
		pm_val |= PORT_HIRD(hird) | PORT_RWE | PORT_L1DS(udev->slot_id);
		writel(pm_val, &port_reg->portpmsc);
		pm_val = readl(&port_reg->portpmsc);
		pm_val |= PORT_HLE;
		writel(pm_val, &port_reg->portpmsc);
		/* flush write */
		readl(&port_reg->portpmsc);
```

Those writes and the encoding behind `hird` are `pm/usb2-device-pm.md`'s subject; this page needs only that they are [`writel()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/io.h#L67) calls into the port's PORTPMSC word, with no hub protocol and no command ring involved.

USB3 link power management has no such restriction. [`xhci_check_tier_policy()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5030) permits any tier at all on a host that sets neither depth-limiting quirk, and permits two or three tiers of hubs on a host that sets one, so the device's parent may be an external hub several links away. The kernel cannot write a register inside an external hub, and the only thing it can do is send that hub a request. That is why the U1 and U2 timeouts travel as SetPortFeature requests rather than as register writes, and why the root-hub case in [`xhci_hub_control()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-hub.c#L1205) is an emulation of what a real hub would do with the same request.

The exit latency goes the other way for the same reason. The bus schedule is built by the host controller and by nothing else, so the number that reserves room in it has to reach the controller, and the controller's per-device state is the slot context. Both generations agree on that. The USB 2.0 path calls the same [`xhci_change_max_exit_latency()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4517) at [`drivers/usb/host/xhci.c:4700`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4700) when it enables a BESL-encoded L1 timeout and at [`drivers/usb/host/xhci.c:4729`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4729) when it clears one, exactly as the USB3 path does at [`drivers/usb/host/xhci.c:5203`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5203) and [`drivers/usb/host/xhci.c:5221`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5221).

```
    Where each generation's idle timer is programmed
    ────────────────────────────────────────────────

              the USB core permits link power management
              for one device on one port
                              │
              ┌───────────────┴────────────────┐
              ▼                                ▼
      SuperSpeed device                high-speed device whose
      at any permitted tier            parent is the root hub
    ┌──────────────────────────┐    ┌──────────────────────────────┐
    │ the timer belongs to the │    │ the timer belongs to the     │
    │ PARENT HUB, which may be │    │ HOST CONTROLLER, the only    │
    │ an external hub          │    │ parent this case allows      │
    └────────────┬─────────────┘    └──────────────┬───────────────┘
                 │ SetPortFeature                  │ writel into the
                 │ U1_TIMEOUT, U2_TIMEOUT          │ port's registers
                 ▼                                 ▼
    ┌──────────────────────────┐    ┌──────────────────────────────┐
    │ that hub's own port      │    │ PORTPMSC and PORTHLPMC of    │
    │ registers, reached over  │    │ the port, reached over MMIO  │
    │ the wire; PORTPMSC only  │    │                              │
    │ when the parent is the   │    │                              │
    │ root hub                 │    │                              │
    └─────────┴────────────────┘    └──────────────┴───────────────┘
              │                                    │
              └──────────────┬─────────────────────┘
                             ▼
              ┌──────────────────────────────────────┐
              │ both then take the same second step: │
              │ the exit latency goes into the slot  │
              │ context by Evaluate Context, because │
              │ the bus schedule is the controller's │
              └──────────────────────────────────────┘
```

### Error handling along the enable and disable paths

A failure anywhere on this path leaves the link state disabled and the device running in U0. Four places can produce one, and where it arises decides what the caller sees.

The first group is the arithmetic refusing to produce a usable number, and it uses one error code throughout. [`xhci_check_tier_policy()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5030) returns `-E2BIG` for a device too deep in the hub topology, [`xhci_update_timeout_for_endpoint()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4989) returns it for an endpoint whose candidate came back as [`USB3_LPM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1261), and [`calculate_max_exit_latency()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5123) returns it for a wake-up cost past [`MAX_EXIT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L371). None of the three reaches the USB core as an error. The first two make the engine return [`USB3_LPM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1261), which [`usb_enable_link_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4327) reads as the controller declining the state and turns into `-EINVAL` with nothing written. The third is absorbed inside [`xhci_enable_usb3_lpm_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5167), which turns the `-E2BIG` into a zero exit latency and a [`USB3_LPM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1261) return:

```c
/* drivers/usb/host/xhci.c:5195 end of xhci_enable_usb3_lpm_timeout() */
	hub_encoded_timeout = xhci_calculate_lpm_timeout(hcd, udev, state);
	mel = calculate_max_exit_latency(udev, state, hub_encoded_timeout);
	if (mel < 0) {
		/* Max Exit Latency is too big, disable LPM. */
		hub_encoded_timeout = USB3_LPM_DISABLED;
		mel = 0;
	}

	ret = xhci_change_max_exit_latency(xhci, udev, mel);
	if (ret)
		return ret;
	return hub_encoded_timeout;
}
```

A negative `mel` forces the timeout to [`USB3_LPM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1261) and the latency to zero, and the Evaluate Context command still runs, so a device whose exit latency became too large has both its hub timeout refused and its cached latency cleared in the controller. Only after that does the function return the timeout.

The second group is the Evaluate Context command failing, and every one of its outcomes propagates. [`xhci_change_max_exit_latency()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4517) itself returns `-ENOMEM` when the command allocation fails or when the input container has the wrong type. [`xhci_configure_endpoint()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L2960) returns `-ESHUTDOWN` when the controller is already marked dying, and `-ENOMEM` when the command cannot be queued. [`xhci_evaluate_context_result()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L2170) turns the completion code into `-ETIME`, `-EINVAL` or `-ENODEV`. Whichever it is, [`xhci_enable_usb3_lpm_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5167) returns it in place of a timeout, which is the negative return [`usb_enable_link_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4327) logs and passes up. Because [`virt_dev->current_mel`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L762) is written only on success, a failed command leaves the cache agreeing with the controller.

| where it fails | error | what is left behind |
|---|---|---|
| [`xhci_check_tier_policy()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5030) | `-E2BIG`, converted to [`USB3_LPM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1261) | nothing written anywhere |
| [`xhci_update_timeout_for_endpoint()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4989) | `-E2BIG`, converted to [`USB3_LPM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1261) | nothing written anywhere |
| [`calculate_max_exit_latency()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5123) | `-E2BIG`, handled in place | latency set to 0 by a real command, state refused |
| [`xhci_alloc_command_with_ctx()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L1758) | `-ENOMEM` | nothing written anywhere |
| [`xhci_configure_endpoint()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L2960), dying controller | `-ESHUTDOWN` | nothing written anywhere |
| [`xhci_handle_command_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-ring.c#L1717) after 5000 ms | `-ETIME` | command aborted, latency unchanged |
| [`COMP_MAX_EXIT_LATENCY_TOO_LARGE_ERROR`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L861) | `-EINVAL` | controller refused the value, latency unchanged |
| [`usb_set_lpm_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4225) | `-EBUSY` | the controller's side is undone by the caller |

The third group is the hub write failing after the controller has already accepted the new latency, and it is the one case with an unwind. [`usb_enable_link_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4327) calls [`disable_usb3_lpm_timeout`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb/hcd.h#L398) at [`drivers/usb/core/hub.c:4372`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4372) before returning `-EBUSY`, which issues a second Evaluate Context command shrinking the latency back. Neither [`usb3_lpm_u1_enabled`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L708) nor [`usb3_lpm_u2_enabled`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L709) is set on that path, so the two sysfs files agree with the hub. One level up, [`usb_enable_lpm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4503) returns on any failure, leaving the states it did enable enabled and the rest off, and [`usb_disable_lpm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4440) restores [`lpm_disable_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/usb.h#L741) at its `disable_failed` label so a caller that could not disable does not hold a reference it never took.

The fourth group is not an error at all but a state the caches have to survive. A resume that finds the controller lost power tears the driver's memory down and rebuilds it, and [`xhci_mem_cleanup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci-mem.c#L1898) at [`drivers/usb/host/xhci.c:1186`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L1186) frees every entry of [`xhci->devs`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L1554), so every cached [`current_mel`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.h#L762) goes with it and is not restored until the device is enumerated again; the comment inside [`xhci_change_max_exit_latency()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4517) explains why the missing entry is a silent success rather than a failure. That teardown and the resume fork it is part of are `pm/host-controller-pm.md`'s subject.

The four groups differ in where the failure arises and in the number the caller finally sees, and they agree on everything after that. The figure below collects them, with the code or codes each group produces on its own edge and the single outcome they all reach on the right.

```
    Four origins of failure, converging on one outcome
    ──────────────────────────────────────────────────
    (the codes differ by origin; the outcome is one and the same)

    ┌──────────────────────┐
    │ the arithmetic       │ -E2BIG, absorbed
    │ refuses a number     ├──────────────────────┐
    └──────────────────────┘                      │
    ┌──────────────────────┐                      │
    │ the Evaluate Context │ -ENOMEM -ESHUTDOWN   │
    │ command fails        ├─ -ETIME -EINVAL ─────┤
    └──────────────────────┘ -ENODEV              │    ┌──────────────┐
    ┌──────────────────────┐                      ├──▶ │ the state is │
    │ the hub write fails  │ -EBUSY, and the      │    │ left off and │
    │ after the controller ├─ controller's side ──┤    │ the device   │
    │ accepted             │ is put back          │    │ runs in U0   │
    └──────────────────────┘                      │    └──────────────┘
    ┌──────────────────────┐                      │
    │ the controller lost  │ no error at all;     │
    │ power and its memory ├─ the cached latency ─┘
    │ was rebuilt          │ went with it
    └──────────────────────┘
```

Those four origins cover what the running paths produce, and one more condition decides whether the paths exist at all. Finally, none of this code exists in a kernel built without [`CONFIG_PM`](https://elixir.bootlin.com/linux/v7.0/source/kernel/power/Kconfig#L216). The whole block from [`drivers/usb/host/xhci.c:4584`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4584) to [`drivers/usb/host/xhci.c:5247`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5247) is conditional on it, and the alternative branch supplies stubs that answer as though the controller declined everything:

```c
/* drivers/usb/host/xhci.c:5223 */
#else /* CONFIG_PM */

static int xhci_set_usb2_hardware_lpm(struct usb_hcd *hcd,
				struct usb_device *udev, int enable)
{
	return 0;
}

static int xhci_update_device(struct usb_hcd *hcd, struct usb_device *udev)
{
	return 0;
}

static int xhci_enable_usb3_lpm_timeout(struct usb_hcd *hcd,
			struct usb_device *udev, enum usb3_link_state state)
{
	return USB3_LPM_DISABLED;
}

static int xhci_disable_usb3_lpm_timeout(struct usb_hcd *hcd,
			struct usb_device *udev, enum usb3_link_state state)
{
	return 0;
}
#endif	/* CONFIG_PM */
```

The stub for [`xhci_enable_usb3_lpm_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5236) returns [`USB3_LPM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/usb/ch9.h#L1261), which [`usb_enable_link_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/core/hub.c#L4327) reads as a refusal, and the stub for [`xhci_disable_usb3_lpm_timeout()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L5242) returns success without doing anything, so a disable never fails. [`xhci_change_max_exit_latency()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/host/xhci.c#L4517) is defined outside the block and carries [`__maybe_unused`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/compiler_attributes.h#L343) for exactly that reason, since with [`CONFIG_PM`](https://elixir.bootlin.com/linux/v7.0/source/kernel/power/Kconfig#L216) clear it has no callers left, and without the attribute the compiler would warn. Link power management on this driver is therefore compile-gated rather than only runtime-gated, and everything this page describes assumes the option is set.
