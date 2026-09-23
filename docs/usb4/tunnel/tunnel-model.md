# The tunnel object

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A USB4 domain tunnels the traffic of several protocols over shared links, and the connection manager sets up and removes each tunneled flow on its own. A flow is one reference-counted tunnel object that names its two end adapters and owns the paths programmed between them. Above the object the connection manager decides which device gets a tunnel, and below it path code programs the routers while protocol callbacks program the adapters.

Work that differs by protocol rides on the object as optional callbacks its allocator installs, so one activation sequence serves every protocol. This page follows one tunnel from the allocation that creates it through activation and its uevents to the last reference drop that frees it.

```
    One DisplayPort tunnel from its allocation to its release
    ─────────────────────────────────────────────────────────

    time ────────────────────────────────────────────────────────────────────────────────────────────────────►

    event        allocate   listed     activate       poll done      deactivate      unlisted     last put
                  ▼            ▼           ▼              ▼               ▼              ▼            ▼
                 ┌───────────────────────────────────────────────────────────────────────────────────┐
    type         │ TB_TUNNEL_DP for the whole life of the object                                     │ freed
                 └───────────────────────────────────────────────────────────────────────────────────┘
                 ┌───────────────────────────────────────────────────────────────────────────────────┐
    npaths       │ 3, the length of paths[]                                                          │ freed
                 └───────────────────────────────────────────────────────────────────────────────────┘
                 ┌─────────────────────────┬──────────────┬───────────────┬──────────────────────────┐
    state        │ INACTIVE, zeroed        │ ACTIVATING   │ ACTIVE        │ INACTIVE                 │ freed
                 └─────────────────────────┴──────────────┴───────────────┴──────────────────────────┘
                  ① ②                       ③              ④               ⑤

    ① tb_tunnel_alloc       tunnel.c:187   npaths ← the path count the DisplayPort allocator passes
    ② tb_tunnel_alloc       tunnel.c:191   type ← the protocol the allocator passes
    ③ tb_tunnel_activate    tunnel.c:2422  state ← ACTIVATING, before any protocol code runs
    ④ tb_tunnel_set_active  tunnel.c:277   state ← ACTIVE, handed on as an "activated" uevent
    ⑤ tb_tunnel_set_active  tunnel.c:281   state ← INACTIVE, handed on as a "deactivated" uevent

    The object holds one reference from allocate to the last put, and one more while the queued
    poll holds it; listed and unlisted are its list node joining and leaving the domain's tunnel_list.
    A PCIe, USB 3.x or DMA tunnel the connection manager creates reaches ④ before activation
    returns, and is listed after it.
```

## SUMMARY

A tunnel carries a protocol's traffic between the adapters at its ends, held as a [`struct tb_tunnel`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L73) with a flexible array of paths. The protocol, an [`enum tb_tunnel_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L14) value, decides which of ten optional callback slots the object's allocator fills. An [`enum tb_tunnel_state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L27) value records how far activation has reached, and a reference count decides when the object is freed.

The journey opens where a protocol allocator returns an object holding one reference, and closes where the last [`tb_tunnel_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220) frees the object and its paths. Between those ends the connection manager links the object onto the domain's [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65), and [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) and [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) move its state. Only [`tb_tunnel_set_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274) writes [`TB_TUNNEL_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L30) or [`TB_TUNNEL_INACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L28), and it hands each write to [`tb_tunnel_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L241) as a uevent from the domain device.

## SPECIFICATIONS

No specification section defines this object. The USB4 Specification and the Thunderbolt 3/4 Specification define the protocol adapters a tunnel joins and the paths it programs, while [`struct tb_tunnel`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L73) with its states, callback slots and reference count is a Linux driver model with no normative encoding. This page is a disclosed synthesis over [`drivers/thunderbolt/tunnel.h`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h), [`drivers/thunderbolt/tunnel.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c) and [`drivers/thunderbolt/tb.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c) at v7.2, and the uevent strings are the Linux userspace interface that the admin guide listed under DOCUMENTATION describes.

## COVERAGE

### The object and the enumerations that classify it (drivers/thunderbolt/tunnel.h)

- [`'\<struct tb_tunnel\>':'drivers/thunderbolt/tunnel.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L73): the tunnel object, holding its reference count, its domain, its two end adapters, ten callback slots, its list node, its type and state, the bandwidth limits, the DisplayPort completion fields and a flexible array of paths
- [`'\<enum tb_tunnel_type\>':'drivers/thunderbolt/tunnel.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L14): the four protocols a tunnel can carry, fixed when the object is allocated
- [`'\<enum tb_tunnel_state\>':'drivers/thunderbolt/tunnel.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L27): the three activation states the object moves through
- [`'\<enum tb_tunnel_event\>':'drivers/thunderbolt/tunnel.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L209): the five tunneling events a uevent can report

### Tests and log macros over the object (drivers/thunderbolt/tunnel.h)

- [`'\<tb_tunnel_is_active\>':'drivers/thunderbolt/tunnel.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L152): the test for a tunnel whose activation has finished
- [`'\<tb_tunnel_is_pci\>':'drivers/thunderbolt/tunnel.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L173): the test for a PCIe tunnel
- [`'\<tb_tunnel_is_dp\>':'drivers/thunderbolt/tunnel.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L178): the test for a DisplayPort tunnel
- [`'\<tb_tunnel_is_dma\>':'drivers/thunderbolt/tunnel.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L183): the test for a host-to-host DMA tunnel
- [`'\<tb_tunnel_is_usb3\>':'drivers/thunderbolt/tunnel.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L188): the test for a USB 3.x tunnel
- [`'\<tb_tunnel_direction_downstream\>':'drivers/thunderbolt/tunnel.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L193): the test that tells whether the tunnel's source adapter is its upstream end
- [`'\<__TB_TUNNEL_PRINT\>':'drivers/thunderbolt/tunnel.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L224): the log wrapper that prefixes a message with both ends of the tunnel and its type name
- [`'\<tb_tunnel_WARN\>':'drivers/thunderbolt/tunnel.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L236): the wrapper at the level that also prints a backtrace
- [`'\<tb_tunnel_warn\>':'drivers/thunderbolt/tunnel.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L238): the wrapper at the warning level
- [`'\<tb_tunnel_info\>':'drivers/thunderbolt/tunnel.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L240): the wrapper at the informational level
- [`'\<tb_tunnel_dbg\>':'drivers/thunderbolt/tunnel.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L242): the wrapper at the debug level

### Allocation, references and release (drivers/thunderbolt/tunnel.c)

- [`'\<tb_tunnel_alloc\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178): allocate the object together with its path array and hand it back holding one reference
- [`'\<tb_tunnel_lock\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L112): the one mutex held around every reference take and drop in the driver
- [`'\<tb_tunnel_get\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L197): take a further reference on a tunnel
- [`'\<tb_tunnel_put\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220): drop a reference, releasing the object when it was the last
- [`'\<tb_tunnel_destroy\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L204): the release function, which runs the destroy slot, frees every path and frees the object

### Activation and the state writers (drivers/thunderbolt/tunnel.c)

- [`'\<tb_tunnel_activate\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405): clear any programmed path, mark the tunnel as activating, run the protocol's preparation, program every path and let the protocol finish or defer the transition
- [`'\<tb_tunnel_deactivate\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458): run the activation stages backwards and leave the tunnel inactive
- [`'\<tb_tunnel_set_active\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274): write the active or the inactive state and report it as a uevent
- [`'\<tb_tunnel_changed\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L287): report a change to a tunnel whose state stays as it was
- [`'\<tb_tunnel_is_activated\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2503): the wider state test that also accepts a tunnel whose activation has started

### The uevent and the name tables (drivers/thunderbolt/tunnel.c)

- [`'\<tb_tunnel_event\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L241): build the event and details strings and send them as a change uevent of the domain
- [`'\<tb_event_names\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L103): the five event strings userspace reads, one per event value
- [`'\<tb_tunnel_names\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L101): the four type names printed into log lines and uevents
- [`'\<tb_tunnel_type_name\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2680): the accessor that returns a tunnel's type name for the log wrapper

### Queries over the tunnel's paths (drivers/thunderbolt/tunnel.c)

- [`'\<tb_tunnel_is_invalid\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2382): tell whether any path of the tunnel crosses a router that has been unplugged
- [`'\<tb_tunnel_port_on_path\>':'drivers/thunderbolt/tunnel.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2486): tell whether any path of the tunnel passes through a given adapter

### The domain's list of tunnels (drivers/thunderbolt/tb.c)

- [`'\<tb_find_tunnel\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L490): find a listed tunnel by its type and one of its two end adapters
- [`'\<tb_deactivate_and_free_tunnel\>':'drivers/thunderbolt/tb.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722): deactivate and unlink a listed tunnel, give back what its type claimed and drop the domain's reference

## DOCUMENTATION

- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst#L319): the "Tunneling events" section, which documents the change uevent of the domain device, its TUNNEL_EVENT and TUNNEL_DETAILS variables and the five event values
- [`Documentation/ABI/testing/sysfs-bus-thunderbolt`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/ABI/testing/sysfs-bus-thunderbolt): the sysfs interface of the bus, which carries no attribute per tunnel; the domain's deauthorization and security attributes and each device's authorized attribute decide which PCIe tunnels the connection manager creates

## OTHER SOURCES

### Added by Claude Opus 5.5

- [thunderbolt: Add support for USB 3.x tunnels (commit e6f818585713)](https://lore.kernel.org/r/20191217123345.31850-9-mika.westerberg@linux.intel.com)

## REGISTERS

The tunnel object holds no register, and its generic code reads and writes none. Every register a tunnel reaches is written beneath it, by [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) and [`tb_path_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L466) for the hop entries each path programs in the routers it crosses, and by the callbacks in the object's slots for the two protocol adapters. [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) and [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) decide the order of those writes and perform none themselves, so this section draws no register.

## DETAILS

The subsections follow a tunnel in the order its life runs, starting with the layout of [`struct tb_tunnel`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L73) and the allocation that creates it. Next come the protocol type, the installed callbacks and the activation states, and then activation and deactivation with the deferred DisplayPort completion between them. The state writer and its uevents lead to the readers of that state and to the reference count that decides when the object is freed. The domain's [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) with its lookup and teardown follows, and the queries, tests and log macros over a tunnel close on what an active tunnel changes.

### The object joins two adapters through an array of paths

A tunnel is an object that joins a source adapter to a destination adapter through a flexible array of paths, and it carries the protocol's own work in callback slots. The table names the members of [`struct tb_tunnel`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L73) with what they hold and which code writes them. The definition follows, then [`tb_test_tunnel_pcie()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/test.c#L1334) reads the members back, and a figure draws the pointers that leave the object.

| members | what they hold | written by |
|---|---|---|
| [`kref`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L74) | the reference count that decides when the object is freed | [`tb_tunnel_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178) starts it at one, [`tb_tunnel_get()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L197) and [`tb_tunnel_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220) move it |
| [`tb`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L75) | the domain, a [`struct tb`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L82) whose device sends the tunnel's uevents and log lines | [`tb_tunnel_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178) |
| [`src_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L76), [`dst_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L77) | the two protocol adapters, each a [`struct tb_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L280) | the protocol's allocator, or [`tb_path_discover()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L101) for a discovered destination |
| [`npaths`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L78) | the number of entries in [`paths`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L110) | [`tb_tunnel_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178) |
| [`pre_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L79) to [`reclaim_available_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L92) | ten optional protocol callbacks, `NULL` where the protocol adds nothing | the protocol's allocator |
| [`list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L95) | the node that joins the domain's [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) | [`tb_tunnel_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178) initializes it, the connection manager links and unlinks it |
| [`type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L96) | the protocol, an [`enum tb_tunnel_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L14) value | [`tb_tunnel_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178) |
| [`state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L97) | how far activation has reached, an [`enum tb_tunnel_state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L27) value | [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) and [`tb_tunnel_set_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274) |
| [`max_up`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L98), [`max_down`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L99) | a bandwidth ceiling in Mb/s, set only where the tunnel is limited | [`tb_tunnel_alloc_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1690) and [`tb_tunnel_alloc_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2310) |
| [`allocated_up`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L100), [`allocated_down`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L101) | the bandwidth a USB 3.x tunnel currently holds | [`tb_tunnel_discover_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2205), [`tb_tunnel_alloc_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2310) and the USB 3.x bandwidth callbacks |
| [`bw_mode`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L102) | whether the DisplayPort bandwidth allocation mode registers report this tunnel | [`tb_dp_alloc_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1301) sets it, [`tb_handle_dp_bandwidth_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2736) clears it |
| [`dprx_started`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L103), [`dprx_canceled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L104), [`dprx_timeout`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L105), [`dprx_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L106), [`callback`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L107), [`callback_data`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L108) | the DisplayPort receiver poll, with its two flags, deadline, work item, completion callback and callback argument | [`tb_tunnel_alloc_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1690), [`tb_dp_dprx_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1114) and [`tb_dp_dprx_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1134) |
| [`paths`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L110) | the flexible array of [`struct tb_path`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L430) pointers, one per path | the protocol's allocator |

[`struct tb_tunnel`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L73) declares the members in that order, with the ten slots between the adapters and the list node and the path array last:

```c
/* drivers/thunderbolt/tunnel.h:73 */
struct tb_tunnel {
	struct kref kref;
	struct tb *tb;
	struct tb_port *src_port;
	struct tb_port *dst_port;
	size_t npaths;
	int (*pre_activate)(struct tb_tunnel *tunnel);
	int (*activate)(struct tb_tunnel *tunnel, bool activate);
	void (*post_deactivate)(struct tb_tunnel *tunnel);
	void (*destroy)(struct tb_tunnel *tunnel);
	int (*maximum_bandwidth)(struct tb_tunnel *tunnel, int *max_up,
				 int *max_down);
	int (*allocated_bandwidth)(struct tb_tunnel *tunnel, int *allocated_up,
				   int *allocated_down);
	int (*alloc_bandwidth)(struct tb_tunnel *tunnel, int *alloc_up,
			       int *alloc_down);
	int (*consumed_bandwidth)(struct tb_tunnel *tunnel, int *consumed_up,
				  int *consumed_down);
	int (*release_unused_bandwidth)(struct tb_tunnel *tunnel);
	void (*reclaim_available_bandwidth)(struct tb_tunnel *tunnel,
					    int *available_up,
					    int *available_down);
	struct list_head list;
	enum tb_tunnel_type type;
	enum tb_tunnel_state state;
	int max_up;
	int max_down;
	int allocated_up;
	int allocated_down;
	bool bw_mode;
	bool dprx_started;
	bool dprx_canceled;
	ktime_t dprx_timeout;
	struct delayed_work dprx_work;
	void (*callback)(struct tb_tunnel *tunnel, void *data);
	void *callback_data;

	struct tb_path *paths[] __counted_by(npaths);
};
```

[`struct tb_tunnel`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L73) gives each slot the tunnel itself as its first argument, so a callback reaches its adapters and paths through the object it receives. Five bandwidth slots add a pair of output pointers for the upstream and the downstream direction, while [`release_unused_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L91) takes the tunnel alone. The [`__counted_by()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/compiler_types.h#L376) annotation names [`npaths`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L78) as the length of [`paths`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L110), an array that commit 498c05821bb4 ("thunderbolt: tunnel: Simplify allocation") made a flexible member, first shipped in v7.1.

[`tb_test_tunnel_pcie()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/test.c#L1334) builds a PCIe tunnel between a host router and a device router of a synthetic topology and reads the members back, including the entry and exit adapters of both paths:

```c
/* drivers/thunderbolt/test.c:1357 */
	tunnel1 = tb_tunnel_alloc_pci(NULL, up, down);
	KUNIT_ASSERT_NOT_NULL(test, tunnel1);
	KUNIT_EXPECT_EQ(test, tunnel1->type, TB_TUNNEL_PCI);
	KUNIT_EXPECT_PTR_EQ(test, tunnel1->src_port, down);
	KUNIT_EXPECT_PTR_EQ(test, tunnel1->dst_port, up);
	KUNIT_ASSERT_EQ(test, tunnel1->npaths, 2);
	KUNIT_ASSERT_EQ(test, tunnel1->paths[0]->path_length, 2);
	KUNIT_EXPECT_PTR_EQ(test, tunnel1->paths[0]->hops[0].in_port, down);
	KUNIT_EXPECT_PTR_EQ(test, tunnel1->paths[0]->hops[1].out_port, up);
	KUNIT_ASSERT_EQ(test, tunnel1->paths[1]->path_length, 2);
	KUNIT_EXPECT_PTR_EQ(test, tunnel1->paths[1]->hops[0].in_port, up);
	KUNIT_EXPECT_PTR_EQ(test, tunnel1->paths[1]->hops[1].out_port, down);
```

[`tb_test_tunnel_pcie()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/test.c#L1334) expects [`src_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L76) to be the downstream adapter it passed and [`dst_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L77) the upstream one, with [`paths[0]`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L110) running from the downstream adapter to the upstream one and [`paths[1]`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L110) running back. The suite is built under [`CONFIG_USB4_KUNIT_TEST`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/Kconfig#L49) and passes `NULL` for the domain, so this case touches no hardware.

The same PCIe tunnel is drawn with its neighbours, the list node joined to the domain's [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) and both paths spanning the adapters:

```
    What one tunnel object points at, drawn for a PCIe tunnel
    ─────────────────────────────────────────────────────────

    struct tb_cm (the manager's private area)            struct tb (the domain)
    ┌──────────────────────────────────────┐            ┌─────────────────────────────────┐
    │ tunnel_list ◀──▶ the other tunnels   │            │ dev, the domainN device         │
    └──────────────────┬───────────────────┘            └────────────────▲────────────────┘
                       │ links the node                                  │
    struct tb_tunnel   │                                                 │
    ┌──────────────────┼─────────────────────────────────────────────────┼────────────────┐
    │ list ◀───────────┘                                       tb ───────┘                │
    │ kref (one count per holder), type = TB_TUNNEL_PCI, state, npaths = 2                │
    │ ten callback slots, pre_activate and activate filled and the other eight NULL       │
    │ src_port ──────────┐                              dst_port ──────────┐              │
    │ paths[0] ──┐       │                 paths[1] ──┐                    │              │
    └────────────┼───────┼────────────────────────────┼────────────────────┼──────────────┘
                 │       ▼                            │                    ▼
                 │     struct tb_port                 │                  struct tb_port
                 │     PCIe downstream adapter        │                  PCIe upstream adapter
                 ▼                                    ▼
    struct tb_path "PCIe Down"                  struct tb_path "PCIe Up"
    hops[0] enters at the downstream adapter    hops[0] enters at the upstream adapter
    and the last hop leaves at the upstream     and the last hop leaves at the downstream
    adapter                                     adapter
```

Code holding a tunnel reaches its domain, its adapters and its paths through pointers in the object itself. The object joins its end adapters, the paths between them and the protocol's callbacks.

### Allocation creates the object together with its path array

The object and its array of path pointers come from the same zeroed allocation, so members the allocator leaves alone start out empty and the slots start out `NULL`. [`tb_tunnel_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178) is that allocation, and [`tb_tunnel_alloc_dma()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1903) follows as the caller whose path count depends on its arguments.

[`tb_tunnel_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178) is file-static in [`drivers/thunderbolt/tunnel.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c), so only the protocol allocators in that file can create a tunnel:

```c
/* drivers/thunderbolt/tunnel.c:178 */
static struct tb_tunnel *tb_tunnel_alloc(struct tb *tb, size_t npaths,
					 enum tb_tunnel_type type)
{
	struct tb_tunnel *tunnel;

	tunnel = kzalloc_flex(*tunnel, paths, npaths);
	if (!tunnel)
		return NULL;

	tunnel->npaths = npaths;

	INIT_LIST_HEAD(&tunnel->list);
	tunnel->tb = tb;
	tunnel->type = type;
	kref_init(&tunnel->kref);

	return tunnel;
}
```

[`tb_tunnel_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178) sizes the object with [`kzalloc_flex()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/slab.h#L1156), which adds room for [`npaths`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L78) entries of [`paths`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L110) to the object and zeroes the result. It records the count at [tunnel.c:187](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L187) and the protocol at [tunnel.c:191](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L191), marks ① and ② of the model figure, then makes [`list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L95) an empty node with [`INIT_LIST_HEAD()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/list.h#L43) and sets the reference count to one with [`kref_init()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kref.h#L29).

The remaining members reach the caller as zero, so the slots read `NULL` until the protocol's allocator fills them. [`state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L97) already holds [`TB_TUNNEL_INACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L28) because that value is zero. A failed allocation returns `NULL` before any write, and the seven callers then return `NULL` themselves.

[`tb_tunnel_alloc_dma()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1903) counts its paths from the ring numbers it was given before it calls the allocator:

```c
/* drivers/thunderbolt/tunnel.c:1913 */
	/* Ring 0 is reserved for control channel */
	if (WARN_ON(!receive_ring || !transmit_ring))
		return NULL;

	if (receive_ring > 0)
		npaths++;
	if (transmit_ring > 0)
		npaths++;

	if (WARN_ON(!npaths))
		return NULL;

	tunnel = tb_tunnel_alloc(tb, npaths, TB_TUNNEL_DMA);
	if (!tunnel)
		return NULL;
```

[`tb_tunnel_alloc_dma()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1903) adds one path per positive ring number, so a caller that needs a single direction passes a negative ring for the other and gets a tunnel with one path. A zero ring is refused first, since according to the comment ring 0 is reserved for the control channel. Two negative rings leave the count at zero, which the second [`WARN_ON()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bug.h#L109) refuses.

Whatever the count, the path array is part of the object's zeroed allocation, so a new tunnel has empty slots and empty path entries until its allocator fills them.

### The protocol type is fixed when the object is allocated

The protocol a tunnel carries is fixed by its allocator, and later readers take it from [`type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L96), which no code rewrites. The excerpt shows [`enum tb_tunnel_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L14), and a table then lists the allocation sites that fix the value, with the path count they ask for.

```c
/* drivers/thunderbolt/tunnel.h:14 */
enum tb_tunnel_type {
	TB_TUNNEL_PCI,
	TB_TUNNEL_DP,
	TB_TUNNEL_DMA,
	TB_TUNNEL_USB3,
};
```

[`enum tb_tunnel_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L14) names PCIe, DisplayPort, host-to-host DMA and USB 3.x tunnels as [`TB_TUNNEL_PCI`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L15), [`TB_TUNNEL_DP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L16), [`TB_TUNNEL_DMA`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L17) and [`TB_TUNNEL_USB3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L18), with no explicit values, so they count up from zero in the order [`tb_tunnel_names`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L101) prints them. The type reaches the object as the third argument of [`tb_tunnel_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178) at seven allocation sites.

| allocation site | type passed | paths |
|---|---|---|
| [`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452) at [tunnel.c:461](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L461) | [`TB_TUNNEL_PCI`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L15) | 2 |
| [`tb_tunnel_alloc_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L532) at [tunnel.c:538](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L538) | [`TB_TUNNEL_PCI`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L15) | 2 |
| [`tb_tunnel_discover_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1589) at [tunnel.c:1599](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1599) | [`TB_TUNNEL_DP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L16) | 3 |
| [`tb_tunnel_alloc_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1690) at [tunnel.c:1704](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1704) | [`TB_TUNNEL_DP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L16) | 3 |
| [`tb_tunnel_alloc_dma()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1903) at [tunnel.c:1925](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1925) | [`TB_TUNNEL_DMA`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L17) | 1 or 2 |
| [`tb_tunnel_discover_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2205) at [tunnel.c:2214](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2214) | [`TB_TUNNEL_USB3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L18) | 2 |
| [`tb_tunnel_alloc_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2310) at [tunnel.c:2333](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2333) | [`TB_TUNNEL_USB3`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L18) | 2 |

Discovery functions exist for PCIe, DisplayPort and USB 3.x, while a DMA tunnel comes only from [`tb_tunnel_alloc_dma()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1903). The type is written at allocation, and the tests and names later on this page read that value.

### Each protocol's allocator installs the callbacks it needs

The generic functions test a slot before calling through it, so the slots an allocator fills carry its protocol's additions to the object's behavior. The table gives the entry point that invokes a slot and the function a protocol installs in it. Three excerpts then show the installing lines for PCIe, for DisplayPort, and for DMA with USB 3.x.

| slot | invoked by | PCIe | DisplayPort | DMA | USB 3.x |
|---|---|---|---|---|---|
| [`pre_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L79) | [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405), before any path | [`tb_pci_pre_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L312), allocation only | [`tb_dp_pre_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1016) | · | [`tb_usb3_pre_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2044), host router only |
| [`activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L80) | [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) with true, [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) with false | [`tb_pci_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L361) | [`tb_dp_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1144) | · | [`tb_usb3_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2054) |
| [`post_deactivate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L81) | [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458), after the paths | · | [`tb_dp_post_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1042) | · | · |
| [`destroy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L82) | [`tb_tunnel_destroy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L204), before the paths are freed | · | · | [`tb_dma_destroy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1878) | · |
| [`maximum_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L83) | [`tb_tunnel_maximum_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2520) | · | [`tb_dp_maximum_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1368) | · | · |
| [`allocated_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L85) | [`tb_tunnel_allocated_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2545) | · | [`tb_dp_allocated_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1263) | · | · |
| [`alloc_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L87) | [`tb_tunnel_alloc_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2570) | · | [`tb_dp_alloc_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1301) | · | · |
| [`consumed_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L89) | [`tb_tunnel_consumed_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2603) | · | [`tb_dp_consumed_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1391) | · | [`tb_usb3_consumed_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2068), host router only |
| [`release_unused_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L91) | [`tb_tunnel_release_unused_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2641) | · | · | · | [`tb_usb3_release_unused_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2091), host router only |
| [`reclaim_available_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L92) | [`tb_tunnel_reclaim_available_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2668) | · | · | · | [`tb_usb3_reclaim_available_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2106), host router only |

[`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452) installs only the activate callback, while [`tb_tunnel_alloc_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L532) also installs the preparation step:

```c
/* drivers/thunderbolt/tunnel.c:461 */
	tunnel = tb_tunnel_alloc(tb, 2, TB_TUNNEL_PCI);
	if (!tunnel)
		return NULL;

	tunnel->activate = tb_pci_activate;
	tunnel->src_port = down;
/* drivers/thunderbolt/tunnel.c:538 */
	tunnel = tb_tunnel_alloc(tb, 2, TB_TUNNEL_PCI);
	if (!tunnel)
		return NULL;

	tunnel->pre_activate = tb_pci_pre_activate;
	tunnel->activate = tb_pci_activate;
	tunnel->src_port = down;
	tunnel->dst_port = up;
```

[`tb_tunnel_alloc_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L532) installs [`tb_pci_pre_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L312) and [`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452) does not, so only a PCIe tunnel the connection manager creates runs that preparation before its paths are programmed. Commit 69a7b98770b7 ("thunderbolt: Verify PCIe adapter in detect state before tunnel setup") added the step, first shipped in v7.2, and both functions name the downstream adapter as the source.

[`tb_tunnel_discover_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1589) and [`tb_tunnel_alloc_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1690) install the same seven callbacks, and the allocation also stores the bandwidth ceilings and the completion callback:

```c
/* drivers/thunderbolt/tunnel.c:1599 */
	tunnel = tb_tunnel_alloc(tb, 3, TB_TUNNEL_DP);
	if (!tunnel)
		return NULL;

	tunnel->pre_activate = tb_dp_pre_activate;
	tunnel->activate = tb_dp_activate;
	tunnel->post_deactivate = tb_dp_post_deactivate;
	tunnel->maximum_bandwidth = tb_dp_maximum_bandwidth;
	tunnel->allocated_bandwidth = tb_dp_allocated_bandwidth;
	tunnel->alloc_bandwidth = tb_dp_alloc_bandwidth;
	tunnel->consumed_bandwidth = tb_dp_consumed_bandwidth;
	tunnel->src_port = in;
/* drivers/thunderbolt/tunnel.c:1704 */
	tunnel = tb_tunnel_alloc(tb, 3, TB_TUNNEL_DP);
	if (!tunnel)
		return NULL;

	tunnel->pre_activate = tb_dp_pre_activate;
	tunnel->activate = tb_dp_activate;
	tunnel->post_deactivate = tb_dp_post_deactivate;
	tunnel->maximum_bandwidth = tb_dp_maximum_bandwidth;
	tunnel->allocated_bandwidth = tb_dp_allocated_bandwidth;
	tunnel->alloc_bandwidth = tb_dp_alloc_bandwidth;
	tunnel->consumed_bandwidth = tb_dp_consumed_bandwidth;
	tunnel->src_port = in;
	tunnel->dst_port = out;
	tunnel->max_up = max_up;
	tunnel->max_down = max_down;
	tunnel->callback = callback;
	tunnel->callback_data = callback_data;
	INIT_DELAYED_WORK(&tunnel->dprx_work, tb_dp_dprx_work);
```

[`tb_tunnel_alloc_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1690) is the one function that stores a [`callback`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L107) or initializes [`dprx_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L106), so a discovered DisplayPort tunnel carries neither. Both DisplayPort functions leave [`destroy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L82), [`release_unused_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L91) and [`reclaim_available_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L92) empty.

[`tb_tunnel_alloc_dma()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1903) installs only the release hook, while [`tb_tunnel_discover_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2205) and [`tb_tunnel_alloc_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2310) install activation always and four more callbacks only behind a route test:

```c
/* drivers/thunderbolt/tunnel.c:1925 */
	tunnel = tb_tunnel_alloc(tb, npaths, TB_TUNNEL_DMA);
	if (!tunnel)
		return NULL;

	tunnel->src_port = nhi;
	tunnel->dst_port = dst;
	tunnel->destroy = tb_dma_destroy;
/* drivers/thunderbolt/tunnel.c:2214 */
	tunnel = tb_tunnel_alloc(tb, 2, TB_TUNNEL_USB3);
	if (!tunnel)
		return NULL;

	tunnel->activate = tb_usb3_activate;
	tunnel->src_port = down;
/* drivers/thunderbolt/tunnel.c:2276 */
		tunnel->pre_activate = tb_usb3_pre_activate;
		tunnel->consumed_bandwidth = tb_usb3_consumed_bandwidth;
		tunnel->release_unused_bandwidth =
			tb_usb3_release_unused_bandwidth;
		tunnel->reclaim_available_bandwidth =
			tb_usb3_reclaim_available_bandwidth;
/* drivers/thunderbolt/tunnel.c:2333 */
	tunnel = tb_tunnel_alloc(tb, 2, TB_TUNNEL_USB3);
	if (!tunnel)
		return NULL;

	tunnel->activate = tb_usb3_activate;
	tunnel->src_port = down;
	tunnel->dst_port = up;
	tunnel->max_up = max_up;
	tunnel->max_down = max_down;
/* drivers/thunderbolt/tunnel.c:2357 */
	if (!tb_route(down->sw)) {
		tunnel->allocated_up = min(max_rate, max_up);
		tunnel->allocated_down = min(max_rate, max_down);

		tunnel->pre_activate = tb_usb3_pre_activate;
		tunnel->consumed_bandwidth = tb_usb3_consumed_bandwidth;
		tunnel->release_unused_bandwidth =
			tb_usb3_release_unused_bandwidth;
		tunnel->reclaim_available_bandwidth =
			tb_usb3_reclaim_available_bandwidth;
	}
```

[`tb_tunnel_alloc_dma()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1903) leaves the activation slots empty, so activating a DMA tunnel programs its paths and reports the state, and [`tb_dma_destroy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1878) runs when the object is freed. [`tb_tunnel_alloc_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2310) tests [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) of the downstream adapter's router, so the four callbacks exist only when that router is the host router at route 0. [`tb_tunnel_discover_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2205) makes the same test at [tunnel.c:2261](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2261).

So far, the object holds the allocator's reference and everything its protocol fixed at allocation, and it is still inactive in the allocate column of the model figure. The slots its allocator filled carry what the protocol adds to the generic sequence that follows.

### The state records how far activation has reached

The state records how far [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) has taken a tunnel. It separates a tunnel never activated from one whose activation has started and from one its protocol reported as finished. The excerpt shows [`enum tb_tunnel_state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L27) with its kerneldoc, a table gives each value's meaning and writer, and a graph draws the moves between the values.

```c
/* drivers/thunderbolt/tunnel.h:21 */
/**
 * enum tb_tunnel_state - State of a tunnel
 * @TB_TUNNEL_INACTIVE: tb_tunnel_activate() is not called for the tunnel
 * @TB_TUNNEL_ACTIVATING: tb_tunnel_activate() returned successfully for the tunnel
 * @TB_TUNNEL_ACTIVE: The tunnel is fully active
 */
enum tb_tunnel_state {
	TB_TUNNEL_INACTIVE,
	TB_TUNNEL_ACTIVATING,
	TB_TUNNEL_ACTIVE,
};
```

[`enum tb_tunnel_state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L27) makes [`TB_TUNNEL_INACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L28) the value zero, so a new object is inactive before any write. Its kerneldoc describes [`TB_TUNNEL_ACTIVATING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L29) as the state after a successful return of activation, and [`TB_TUNNEL_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L30) as a tunnel that is fully active. The table adds where the driver writes the values.

| state | meaning on this page | written at |
|---|---|---|
| [`TB_TUNNEL_INACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L28) | activation never ran, or the last deactivation finished | zero from [`tb_tunnel_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178), then [`tb_tunnel_set_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274) at [tunnel.c:281](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L281) |
| [`TB_TUNNEL_ACTIVATING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L29) | activation has started and the protocol has not reported success | [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) at [tunnel.c:2422](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2422) |
| [`TB_TUNNEL_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L30) | the protocol reported success | [`tb_tunnel_set_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274) at [tunnel.c:277](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L277) |

Two functions write the member, at three lines between them, and the graph gives the moves with the code that drives them:

```
    Moves between the three activation states
    ─────────────────────────────────────────

                ┌─────────────────────────────────┐
                │ TB_TUNNEL_INACTIVE              │◀───────────────────────────┐
                │  zero from the allocation, or   │                            │
                │  written by the last            │                            │
                │  deactivation                   │                            │
                └────────────────┬────────────────┘                            │
                                 │ ❶ activation starts                         │
                                 ▼                                             │
                ┌─────────────────────────────────┐                            │
      ┌────────▶│ TB_TUNNEL_ACTIVATING            ├──── ❸ a path or the ──────┤
      │         │  kept when preparation fails    │     callback failed        │
      │         │  or the callback answers        │                            │
      │         │  -EINPROGRESS                   │                            │
      │         └────────────────┬────────────────┘                            │
      │ ❶ activation             │ ❷ callback empty or answering 0             │
      │   runs again             │ ❹ the queued poll finds the receiver done   │
      │                          ▼                                             │
      │         ┌─────────────────────────────────┐                            │
      └─────────┤ TB_TUNNEL_ACTIVE                ├──── ❺ deactivation ────────┘
                │  the protocol reported success  │
                └─────────────────────────────────┘

    ❶ tb_tunnel_activate    tunnel.c:2422  state ← ACTIVATING from any state, before protocol code runs
    ❷ tb_tunnel_activate    tunnel.c:2445  asks for ACTIVE once the paths and the callback succeed
    ❸ tb_tunnel_activate    tunnel.c:2450  deactivates the tunnel after a failed path or callback
    ❹ tb_dp_dprx_work       tunnel.c:1104  asks for ACTIVE when the queued poll finds the receiver done
    ❺ tb_tunnel_deactivate  tunnel.c:2475  asks for INACTIVE from any state
```

Mark ❶ is the write at the head of [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405), which moves any state to [`TB_TUNNEL_ACTIVATING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L29) before the protocol runs. Mark ❷ is the request `tb_tunnel_activate()` makes for [`TB_TUNNEL_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L30) once the paths and the activate callback have succeeded. Mark ❸ is the error label of `tb_tunnel_activate()`, which deactivates the tunnel after a path or the callback failed. Mark ❹ is the request for [`TB_TUNNEL_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L30) made by [`tb_dp_dprx_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1088) when the queued DisplayPort poll finds the receiver done. Mark ❺ is the last line of [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458), which asks for [`TB_TUNNEL_INACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L28) from any state.

The member therefore records the progress of activation, and these five moves are the ones that change it.

### Activation starts by clearing the paths already programmed

Activation starts from a known hardware condition, so it deactivates the paths still marked as programmed before it records that activation has started. The outline divides [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) into four pieces, and this subsection reads piece Ⓐ.

| piece | lines | stage |
|---|---|---|
| Ⓐ | [tunnel.c:2405-2423](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) | clears the programmed paths and writes [`TB_TUNNEL_ACTIVATING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L29), below its kerneldoc |
| Ⓑ | [tunnel.c:2424-2435](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2424) | runs the preparation callback, then activates the paths |
| Ⓒ | [tunnel.c:2436-2447](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2436) | lets the activate callback finish, defer or fail the transition |
| Ⓓ | [tunnel.c:2448-2452](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2448) | logs the failure and deactivates the tunnel |

Piece Ⓐ of [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) logs the attempt, deactivates the paths whose flag says they are programmed, and writes the new state:

```c
/* drivers/thunderbolt/tunnel.c:2395 */
/**
 * tb_tunnel_activate() - activate a tunnel
 * @tunnel: Tunnel to activate
 *
 * Return:
 * * %0 - On success.
 * * %-EINPROGRESS - If the tunnel activation is still in progress (that's
 *   for DP tunnels to complete DPRX capabilities read).
 * * Negative errno - Another error occurred.
 */
int tb_tunnel_activate(struct tb_tunnel *tunnel)
{
	int res, i;

	tb_tunnel_dbg(tunnel, "activating\n");

	/*
	 * Make sure all paths are properly disabled before enabling
	 * them again.
	 */
	for (i = 0; i < tunnel->npaths; i++) {
		if (tunnel->paths[i]->activated) {
			tb_path_deactivate(tunnel->paths[i]);
			tunnel->paths[i]->activated = false;
		}
	}

	tunnel->state = TB_TUNNEL_ACTIVATING;

```

[`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) tests [`activated`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L441) on the entries of [`paths`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L110), hands a programmed path to [`tb_path_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L466) and clears the flag itself afterwards. The loop reads the entries without a `NULL` test, which holds because every allocator returns a tunnel only after filling all of its entries. The kerneldoc lists the results the function can return. The write at [tunnel.c:2422](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2422) is mark ③ of the model figure and comes before the first callback.

Activation therefore begins with no path marked as programmed and the state at [`TB_TUNNEL_ACTIVATING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L29), which the tunnel holds until a later piece moves it.

### The preparation and the paths can each refuse activation

A protocol can refuse activation before a hop entry is written, and a path can fail while it is being programmed. The two refusals leave the tunnel in different states. Piece Ⓑ of [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) shows the two stages, the PCIe preparation shows a refusal, and the tail of [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) shows the flag a programmed path records.

Piece Ⓑ of [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) runs the preparation callback and then activates the paths in array order:

```c
/* drivers/thunderbolt/tunnel.c:2424 */
	if (tunnel->pre_activate) {
		res = tunnel->pre_activate(tunnel);
		if (res)
			return res;
	}

	for (i = 0; i < tunnel->npaths; i++) {
		res = tb_path_activate(tunnel->paths[i]);
		if (res)
			goto err;
	}

```

[`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) returns a failed preparation result at once, so the tunnel keeps [`TB_TUNNEL_ACTIVATING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L29) with no path touched and nothing to roll back. A failing path instead jumps to the error label of piece Ⓓ. A PCIe tunnel from [`tb_tunnel_alloc_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L532) can be refused at preparation, where [`tb_pci_pre_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L312) waits through [`tb_pci_port_ltssm_state_detect()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L293) for each end to reach the Detect link state:

```c
/* drivers/thunderbolt/tunnel.c:293 */
static int tb_pci_port_ltssm_state_detect(struct tb_port *port)
{
	ktime_t timeout = ktime_add_ms(ktime_get(), 500);

	do {
		int ret;

		ret = usb4_pci_port_ltssm_state(port);
		if (ret < 0)
			return ret;
		if (ret == USB4_PCIE_LTSSM_DETECT)
			return 0;

		fsleep(50);
	} while (ktime_before(ktime_get(), timeout));

	return -ETIMEDOUT;
}
/* drivers/thunderbolt/tunnel.c:312 */
static int tb_pci_pre_activate(struct tb_tunnel *tunnel)
{
	struct tb_port *down = tunnel->src_port;
	struct tb_port *up = tunnel->dst_port;
	int ret;

	ret = tb_switch_is_usb4(down->sw) ?
		tb_pci_port_ltssm_state_detect(down) : 0;
	if (ret)
		return ret;

	return tb_switch_is_usb4(up->sw) ?
		tb_pci_port_ltssm_state_detect(up) : 0;
}
```

[`tb_pci_port_ltssm_state_detect()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L293) reads the adapter's link state until it reads Detect, and answers `-ETIMEDOUT` once 500 ms have passed without it. [`tb_pci_pre_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L312) applies the wait to each end whose router is USB4, so a PCIe activation can fail before any hop entry is written.

[`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) programs a path's hop entries and ends in the lines below, which set the flag after the last entry was written:

```c
/* drivers/thunderbolt/path.c:576 */
		res = tb_port_write(path->hops[i].in_port, &hop, TB_CFG_HOPS,
				    2 * path->hops[i].in_hop_index, 2);
		if (res) {
			__tb_path_deactivate_hops(path, 0);
			__tb_path_deallocate_nfc(path, 0);
			goto err;
		}
	}
	path->activated = true;
	tb_dbg(path->tb, "%s path activation complete\n", path->name);
	return 0;
err:
	tb_warn(path->tb, "%s path activation failed: %d\n", path->name, res);
	return res;
}
```

[`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) rolls back from hop 0 when a hop write fails and sets [`activated`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L441) on success, so a failed path does not carry the flag that the tunnel code tests. The paths activated before it do carry the flag, and the deactivation behind the error label takes those down.

A refused preparation therefore leaves the tunnel [`TB_TUNNEL_ACTIVATING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L29) with no path touched, while a failed path sends it through the error label and a full deactivation.

### The activate callback decides how activation ends

With the paths programmed, the protocol's activate callback decides how activation ends. Success makes the tunnel active, `-EINPROGRESS` leaves it activating, and another error deactivates it. The two pieces Ⓒ and Ⓓ of [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) show these outcomes, and a table gathers the ways out of the function.

Piece Ⓒ of [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) calls the activate callback with true and sorts its answer:

```c
/* drivers/thunderbolt/tunnel.c:2436 */
	if (tunnel->activate) {
		res = tunnel->activate(tunnel, true);
		if (res) {
			if (res == -EINPROGRESS)
				return res;
			goto err;
		}
	}

	tb_tunnel_set_active(tunnel, true);
	return 0;

```

[`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) reaches [`tb_tunnel_set_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274) when the slot is empty or the callback answers zero, and that call writes [`TB_TUNNEL_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L30), mark ④ of the model figure. An answer of `-EINPROGRESS` returns without rollback and leaves the state that the head of the function wrote.

Piece Ⓓ of [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) is the error label that a failed path or callback reaches:

```c
/* drivers/thunderbolt/tunnel.c:2448 */
err:
	tb_tunnel_warn(tunnel, "activation failed\n");
	tb_tunnel_deactivate(tunnel);
	return res;
}
```

[`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) logs the failure through [`tb_tunnel_warn`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L238) and calls [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458), which takes down the paths already programmed and ends at [`TB_TUNNEL_INACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L28). The error goes back to the caller after that rollback, and the table sets the ways out of the function side by side.

| how it ends | state afterwards | rollback |
|---|---|---|
| slot empty, or its callback answering 0 | [`TB_TUNNEL_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L30), written at [tunnel.c:277](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L277) | none needed |
| callback answering `-EINPROGRESS` | [`TB_TUNNEL_ACTIVATING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L29), written at [tunnel.c:2422](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2422) | none |
| [`pre_activate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L79) failing | [`TB_TUNNEL_ACTIVATING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L29), written at [tunnel.c:2422](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2422) | none, the function returns at [tunnel.c:2427](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2427) |
| a path or the callback failing | [`TB_TUNNEL_INACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L28), written at [tunnel.c:281](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L281) | [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) at [tunnel.c:2450](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2450) |

So far, the tunnel has left the allocate column of the model figure with its paths programmed or rolled back. The activate callback's answer decides whether activation ends active, still activating or back at inactive.

### A DisplayPort tunnel finishes activating on the domain workqueue

A DisplayPort tunnel allocated with a completion callback returns from activation before it is active, and its move to [`TB_TUNNEL_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L30) happens later on the domain workqueue. Excerpts follow the handoff in order, [`tb_dp_dprx_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1114) queueing the poll, [`tb_tunnel_one_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1971) keeping the listed tunnel and [`tb_dp_dprx_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1088) writing the state. A swimlane then lines the steps up.

[`tb_dp_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1144) ends by calling [`tb_dp_dprx_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1114) at [tunnel.c:1182](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1182) once both adapters are enabled, and that helper takes a second reference before it starts the poll against the limits [`TB_DPRX_TIMEOUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L81) and [`dprx_timeout`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L85) define:

```c
/* drivers/thunderbolt/tunnel.c:81 */
#define TB_DPRX_TIMEOUT			12000
#define TB_DPRX_WAIT_TIMEOUT		25
#define TB_DPRX_POLL_DELAY		50

static int dprx_timeout = TB_DPRX_TIMEOUT;
module_param(dprx_timeout, int, 0444);
MODULE_PARM_DESC(dprx_timeout,
		 "DPRX capability read timeout in ms, -1 waits forever (default: "
		 __MODULE_STRING(TB_DPRX_TIMEOUT) ")");
/* drivers/thunderbolt/tunnel.c:1114 */
static int tb_dp_dprx_start(struct tb_tunnel *tunnel)
{
	/*
	 * Bump up the reference to keep the tunnel around. It will be
	 * dropped in tb_dp_dprx_stop() once the tunnel is deactivated.
	 */
	tb_tunnel_get(tunnel);

	tunnel->dprx_started = true;

	if (tunnel->callback) {
		tunnel->dprx_timeout = dprx_timeout_to_ktime(dprx_timeout);
		queue_delayed_work(tunnel->tb->wq, &tunnel->dprx_work, 0);
		return -EINPROGRESS;
	}

	return tb_dp_is_usb4(tunnel->src_port->sw) ?
		tb_dp_wait_dprx(tunnel, dprx_timeout) : 0;
}
/* drivers/thunderbolt/tunnel.c:1172 */
	ret = tb_dp_port_enable(tunnel->src_port, active);
	if (ret)
		return ret;

	if (tb_port_is_dpout(tunnel->dst_port)) {
		ret = tb_dp_port_enable(tunnel->dst_port, active);
		if (ret)
			return ret;
	}

	return active ? tb_dp_dprx_start(tunnel) : 0;
```

[`tb_dp_dprx_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1114) takes the reference with [`tb_tunnel_get()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L197) whether or not it queues anything, and then sets [`dprx_started`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L103). With a [`callback`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L107) stored, it computes the deadline from [`dprx_timeout`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L85), queues [`dprx_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L106) on the domain workqueue and answers `-EINPROGRESS`. The parameter is 12000 ms by default and waits forever at -1 according to its description, and that return is the one place in the driver that produces the value. [`tb_tunnel_one_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1971) is the connection manager's caller, and it links the tunnel before activating it and keeps it listed on that answer:

```c
/* drivers/thunderbolt/tb.c:2036 */
	list_add_tail(&tunnel->list, &tcm->tunnel_list);

	ret = tb_tunnel_activate(tunnel);
	if (ret && ret != -EINPROGRESS) {
		tb_port_info(out, "DP tunnel activation failed, aborting\n");
		list_del(&tunnel->list);
		goto err_free;
	}

	return;
```

[`tb_tunnel_one_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1971) treats `-EINPROGRESS` like success, so the tunnel stays on the domain's list in [`TB_TUNNEL_ACTIVATING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L29) and the hotplug handler returns. The five other callers of [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) never test for the value. [`tb_dp_dprx_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1088) later runs on the workqueue, polls the receiver under the domain lock, and writes the state once the receiver is done:

```c
/* drivers/thunderbolt/tunnel.c:1088 */
static void tb_dp_dprx_work(struct work_struct *work)
{
	struct tb_tunnel *tunnel = container_of(work, typeof(*tunnel), dprx_work.work);
	struct tb *tb = tunnel->tb;

	if (!tunnel->dprx_canceled) {
		mutex_lock(&tb->lock);
		if (tb_dp_is_usb4(tunnel->src_port->sw) &&
		    tb_dp_wait_dprx(tunnel, TB_DPRX_WAIT_TIMEOUT)) {
			if (ktime_before(ktime_get(), tunnel->dprx_timeout)) {
				queue_delayed_work(tb->wq, &tunnel->dprx_work,
						   msecs_to_jiffies(TB_DPRX_POLL_DELAY));
				mutex_unlock(&tb->lock);
				return;
			}
		} else {
			tb_tunnel_set_active(tunnel, true);
		}
		mutex_unlock(&tb->lock);
	}

	if (tunnel->callback)
		tunnel->callback(tunnel, tunnel->callback_data);
	tb_tunnel_put(tunnel);
}
```

[`tb_dp_dprx_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1088) polls the receiver for up to [`TB_DPRX_WAIT_TIMEOUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L82) of 25 ms per run, and it queues itself again after [`TB_DPRX_POLL_DELAY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L83) of 50 ms while the deadline lies ahead. A run that finds the read finished reaches [`tb_tunnel_set_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274) with true, while a run past the deadline leaves the state at [`TB_TUNNEL_ACTIVATING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L29).

A cancelled poll skips both the read and the write. Whatever the outcome, the completion [`callback`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L107) then runs without the domain lock, and the reference taken at the start is dropped with [`tb_tunnel_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220). The swimlane puts the three functions on one time axis, with the tunnel's state and reference count between the caller and the workqueue:

```
    DisplayPort activation handed from the caller to the domain workqueue
    ─────────────────────────────────────────────────────────────────────
    time ↓
    connection manager          │ tunnel object                     │ domain workqueue
    ────────────────────────────┼───────────────────────────────────┼─────────────────────────────────
    links the tunnel ⓐ ────────▶│ listed, INACTIVE, 1 reference     │
    asks for activation ───────▶│ ACTIVATING, paths programmed      │
                                │ 2 references, poll queued ⓑ ─────▶│ poll armed with its deadline
    gets -EINPROGRESS ◀─────────│ no rollback ⓒ                     │
    keeps the tunnel listed     │                                   │
                                │                                   │ re-queued after 50 ms while
                                │                                   │ the receiver is not done
                                │ ACTIVE, "activated" sent ◀────────│ receiver done ⓓ
                                │ 1 reference ◀─────────────────────│ completion callback ran,
                                │                                   │ reference dropped ⓔ

    ⓐ tb_tunnel_one_dp    tb.c:2036      links the tunnel onto tunnel_list before activating it
    ⓑ tb_dp_dprx_start    tunnel.c:1127  answers -EINPROGRESS after taking a reference and queueing the poll
    ⓒ tb_tunnel_activate  tunnel.c:2440  returns that answer to the caller without rolling anything back
    ⓓ tb_dp_dprx_work     tunnel.c:1104  moves state to ACTIVE once the receiver reports done
    ⓔ tb_dp_dprx_work     tunnel.c:1111  drops the poll's reference after the completion callback
```

Mark ⓐ is the link [`tb_tunnel_one_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1971) makes before it asks for activation. Mark ⓑ is the `-EINPROGRESS` answer of [`tb_dp_dprx_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1114), given after the second reference is taken and the poll is queued. Mark ⓒ is the return in [`tb_tunnel_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2405) that passes the answer to the caller with no rollback, which keeps the tunnel listed. Mark ⓓ is the call in [`tb_dp_dprx_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1088) that moves the state to [`TB_TUNNEL_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L30) once the receiver is done. Mark ⓔ is the drop at the end of `tb_dp_dprx_work()`, made after the completion callback has run.

Activation of such a tunnel therefore ends in two places, the caller's return with the tunnel still activating and the worker's later write of the active state.

### Deactivation runs the stages backwards and always ends inactive

Deactivation undoes the activation stages in reverse order and always finishes by writing [`TB_TUNNEL_INACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L28), so a caller can rely on the final state whatever failed before. [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) is shown, followed by the discovery unwind that relies on its tolerance of a half-filled path array.

[`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) is short enough to read in one piece:

```c
/* drivers/thunderbolt/tunnel.c:2458 */
void tb_tunnel_deactivate(struct tb_tunnel *tunnel)
{
	int i;

	tb_tunnel_dbg(tunnel, "deactivating\n");

	if (tunnel->activate)
		tunnel->activate(tunnel, false);

	for (i = 0; i < tunnel->npaths; i++) {
		if (tunnel->paths[i] && tunnel->paths[i]->activated)
			tb_path_deactivate(tunnel->paths[i]);
	}

	if (tunnel->post_deactivate)
		tunnel->post_deactivate(tunnel);

	tb_tunnel_set_active(tunnel, false);
}
```

[`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) calls the activate callback with false and ignores its answer, deactivates the paths that are present and carry [`activated`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L441), and then runs [`post_deactivate`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L81). The last line is unconditional, so every one of its eight call sites leaves [`state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L97) at [`TB_TUNNEL_INACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L28) and hands a deactivation event to the uevent code. The `NULL` test on the entries of [`paths`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L110) lets a discovery function abandon a tunnel whose second path was never found.

[`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452) fills the upstream path first, and a missing return path sends it to the unwind with the other entry still `NULL`:

```c
/* drivers/thunderbolt/tunnel.c:480 */
	tunnel->paths[TB_PCI_PATH_UP] = path;
	if (tb_pci_init_path(tunnel->paths[TB_PCI_PATH_UP]))
		goto err_free;

	path = tb_path_discover(tunnel->dst_port, -1, down, TB_PCI_HOPID, NULL,
				"PCIe Down", alloc_hopid);
	if (!path)
		goto err_deactivate;
	tunnel->paths[TB_PCI_PATH_DOWN] = path;
	if (tb_pci_init_path(tunnel->paths[TB_PCI_PATH_DOWN]))
		goto err_deactivate;
/* drivers/thunderbolt/tunnel.c:513 */
err_deactivate:
	tb_tunnel_deactivate(tunnel);
err_free:
	tb_tunnel_put(tunnel);

	return NULL;
```

[`tb_tunnel_discover_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L452) stores the path it found as the upstream entry of [`paths`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L110) and jumps to `err_deactivate` when the second lookup fails, so [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) skips the empty entry and [`tb_tunnel_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220) frees the object. That unwind reports a deactivation for a tunnel that was never reported as activated, because the final write runs whatever state it replaces.

Deactivation therefore ends with the tunnel at [`TB_TUNNEL_INACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L28) and its programmed paths taken down, whatever state it started from.

### The state writer hands every write to the uevent code

The writes of [`TB_TUNNEL_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L30) and [`TB_TUNNEL_INACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L28) pass through a helper that reports them in the same branch, so userspace hears of a tunnel becoming active or inactive when the state changes. [`tb_tunnel_set_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274) and [`tb_tunnel_changed()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L287) are shown together, and the caller of the second follows them.

[`tb_tunnel_set_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274) and [`tb_tunnel_changed()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L287) are neighbours in the file and share their argument list:

```c
/* drivers/thunderbolt/tunnel.c:274 */
static inline void tb_tunnel_set_active(struct tb_tunnel *tunnel, bool active)
{
	if (active) {
		tunnel->state = TB_TUNNEL_ACTIVE;
		tb_tunnel_event(tunnel->tb, TB_TUNNEL_ACTIVATED, tunnel->type,
				tunnel->src_port, tunnel->dst_port);
	} else {
		tunnel->state = TB_TUNNEL_INACTIVE;
		tb_tunnel_event(tunnel->tb, TB_TUNNEL_DEACTIVATED, tunnel->type,
				tunnel->src_port, tunnel->dst_port);
	}
}

static inline void tb_tunnel_changed(struct tb_tunnel *tunnel)
{
	tb_tunnel_event(tunnel->tb, TB_TUNNEL_CHANGED, tunnel->type,
			tunnel->src_port, tunnel->dst_port);
}
```

[`tb_tunnel_set_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274) writes [`TB_TUNNEL_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L30) at [tunnel.c:277](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L277) and [`TB_TUNNEL_INACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L28) at [tunnel.c:281](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L281), marks ④ and ⑤ of the model figure, and both branches then pass the matching event to [`tb_tunnel_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L241). [`tb_tunnel_changed()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L287) passes [`TB_TUNNEL_CHANGED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L211) with the same arguments and writes no member, so it reports a tunnel whose state stays as it was.

[`tb_tunnel_alloc_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2570) is the one caller of [`tb_tunnel_changed()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L287), and it reports only after the protocol accepted the new allocation:

```c
/* drivers/thunderbolt/tunnel.c:2576, inside tb_tunnel_alloc_bandwidth() */
	if (tunnel->alloc_bandwidth) {
		int ret;

		ret = tunnel->alloc_bandwidth(tunnel, alloc_up, alloc_down);
		if (ret)
			return ret;

		tb_tunnel_changed(tunnel);
		return 0;
	}

	return -EOPNOTSUPP;
```

[`tb_tunnel_alloc_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2570) returns a refused allocation without a report, and an empty [`alloc_bandwidth`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L87) slot answers `-EOPNOTSUPP` without one, which covers every tunnel but DisplayPort. The state writer and this reallocation path are the only reporters inside the tunnel code, and each hands its event to the uevent code at the moment the change is made.

### Each event value maps to one string userspace reads

Userspace reads strings while the driver stores enumerations, so tables indexed by the event and the type values produce the text of a tunnel uevent. The excerpts show [`enum tb_tunnel_event`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L209), then [`tb_tunnel_names`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L101) and [`tb_event_names`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L103), and a table maps the events to their strings and to the code that reports them.

```c
/* drivers/thunderbolt/tunnel.h:209 */
enum tb_tunnel_event {
	TB_TUNNEL_ACTIVATED,
	TB_TUNNEL_CHANGED,
	TB_TUNNEL_DEACTIVATED,
	TB_TUNNEL_LOW_BANDWIDTH,
	TB_TUNNEL_NO_BANDWIDTH,
};
```

[`enum tb_tunnel_event`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L209) separates [`TB_TUNNEL_ACTIVATED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L210), [`TB_TUNNEL_CHANGED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L211) and [`TB_TUNNEL_DEACTIVATED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L212), which describe a tunnel's state, from [`TB_TUNNEL_LOW_BANDWIDTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L213) and [`TB_TUNNEL_NO_BANDWIDTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L214), which describe a shortage of bandwidth. [`tb_tunnel_names`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L101) and [`tb_event_names`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L103) follow the enumerations they are indexed with:

```c
/* drivers/thunderbolt/tunnel.c:101 */
static const char * const tb_tunnel_names[] = { "PCI", "DP", "DMA", "USB3" };

static const char * const tb_event_names[] = {
	[TB_TUNNEL_ACTIVATED] = "activated",
	[TB_TUNNEL_CHANGED] = "changed",
	[TB_TUNNEL_DEACTIVATED] = "deactivated",
	[TB_TUNNEL_LOW_BANDWIDTH] = "low bandwidth",
	[TB_TUNNEL_NO_BANDWIDTH] = "insufficient bandwidth",
};
```

[`tb_tunnel_names`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L101) lists the four type names in the order of [`enum tb_tunnel_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L14), and [`tb_event_names`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L103) pairs the events with their strings through designated initializers, so that table cannot drift from its enumeration. The strings are the values that the admin guide lists for userspace.

| event | string | reported at |
|---|---|---|
| [`TB_TUNNEL_ACTIVATED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L210) | activated | [tunnel.c:278](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L278) in [`tb_tunnel_set_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274) |
| [`TB_TUNNEL_CHANGED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L211) | changed | [tunnel.c:289](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L289) in [`tb_tunnel_changed()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L287) |
| [`TB_TUNNEL_DEACTIVATED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L212) | deactivated | [tunnel.c:282](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L282) in [`tb_tunnel_set_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L274) |
| [`TB_TUNNEL_LOW_BANDWIDTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L213) | low bandwidth | [tb.c:965](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L965) in [`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) |
| [`TB_TUNNEL_NO_BANDWIDTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L214) | insufficient bandwidth | [tb.c:2021](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2021) in [`tb_tunnel_one_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1971) and [tb.c:2730](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2730) in [`tb_alloc_dp_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2538) |

Outside those six sites only the firmware connection manager reports tunnel events, and its code is out of scope here. A listener receives one of these five strings, followed by the details of the tunnel it concerns.

So far, the tunnel has been through allocation and activation, and its moves to active and to inactive have gone to userspace as these strings. The event value picks the string, and the type value picks the name printed beside the two ends.

### The domain device sends every tunnel event as a uevent

Tunnel events leave the driver as change uevents of the domain device, each carrying a variable that names the event and a variable that names the tunnel. [`tb_tunnel_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L241) builds both variables and is shown in full, then [`tb_domain_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L818) sends them. A caller that reports a tunnel before it exists closes the subsection.

[`tb_tunnel_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L241) takes the domain with a type and two adapters, so a caller can report about a tunnel that does not exist yet:

```c
/* drivers/thunderbolt/tunnel.c:241 */
void tb_tunnel_event(struct tb *tb, enum tb_tunnel_event event,
		     enum tb_tunnel_type type,
		     const struct tb_port *src_port,
		     const struct tb_port *dst_port)
{
	char *envp[3] = { NULL };

	if (WARN_ON_ONCE(event >= ARRAY_SIZE(tb_event_names)))
		return;
	if (WARN_ON_ONCE(type >= ARRAY_SIZE(tb_tunnel_names)))
		return;

	envp[0] = kasprintf(GFP_KERNEL, "TUNNEL_EVENT=%s", tb_event_names[event]);
	if (!envp[0])
		return;

	if (src_port != NULL && dst_port != NULL) {
		envp[1] = kasprintf(GFP_KERNEL, "TUNNEL_DETAILS=%llx:%u <-> %llx:%u (%s)",
				    tb_route(src_port->sw), src_port->port,
				    tb_route(dst_port->sw), dst_port->port,
				    tb_tunnel_names[type]);
	} else {
		envp[1] = kasprintf(GFP_KERNEL, "TUNNEL_DETAILS=(%s)",
				    tb_tunnel_names[type]);
	}

	if (envp[1])
		tb_domain_event(tb, envp);

	kfree(envp[1]);
	kfree(envp[0]);
}
```

[`tb_tunnel_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L241) bounds both indexes with [`WARN_ON_ONCE()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bug.h#L119) against [`ARRAY_SIZE()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/array_size.h#L11) of the table it indexes, so an out-of-range value returns before a string is built. The array of three holds the event string, the details string and the terminating `NULL` that [`kobject_uevent_env()`](https://elixir.bootlin.com/linux/v7.2/source/lib/kobject_uevent.c#L476) expects, and a failed [`kasprintf()`](https://elixir.bootlin.com/linux/v7.2/source/lib/kasprintf.c#L53) for the event string returns with nothing sent.

The details string names both ends as the [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) of the router and the [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L290) number of the adapter, followed by the type name, and it falls back to the type name alone when either adapter is `NULL`. [`tb_domain_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L818) runs after both strings were built, so a failed allocation drops the event entirely, and [`kfree()`](https://elixir.bootlin.com/linux/v7.2/source/mm/slub.c#L6671) releases both strings on the way out. That helper sends the strings from the domain's own device, and [`tb_domain_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L818) is short:

```c
/* drivers/thunderbolt/tb.h:810 */
/**
 * tb_domain_event() - Notify userspace about an event in domain
 * @tb: Domain where event occurred
 * @envp: Array of uevent environment strings (can be %NULL)
 *
 * This function provides a way to notify userspace about any events
 * that take place in the domain.
 */
static inline void tb_domain_event(struct tb *tb, char *envp[])
{
	kobject_uevent_env(&tb->dev.kobj, KOBJ_CHANGE, envp);
}
```

[`tb_domain_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L818) calls [`kobject_uevent_env()`](https://elixir.bootlin.com/linux/v7.2/source/lib/kobject_uevent.c#L476) on the kobject of the domain's [`dev`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L83) with [`KOBJ_CHANGE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kobject.h#L56), so a listener sees the event on the `domainN` device that [domain.c:412](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L412) names. The tunnel has no sysfs directory or attribute of its own, and the admin guide documents the two variables and the five event values. Commit 785da9e6a1bd ("thunderbolt: Notify userspace about software CM tunneling events") added the function and commit 36f6f7e2d4d0 ("Documentation/admin-guide: Document Thunderbolt/USB4 tunneling events") added that section, both first shipped in v6.16.

[`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) reports a shortage before it allocates anything, naming the adapters of the tunnel it is about to create:

```c
/* drivers/thunderbolt/tb.c:959, inside tb_tunnel_usb3() */
	/*
	 * If the available bandwidth is less than 1.5 Gb/s notify
	 * userspace that the connected isochronous device may not work
	 * properly.
	 */
	if (available_up < 1500 || available_down < 1500)
		tb_tunnel_event(tb, TB_TUNNEL_LOW_BANDWIDTH, TB_TUNNEL_USB3,
				down, up);
```

[`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) sends [`TB_TUNNEL_LOW_BANDWIDTH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L213) when either direction has less than 1500 Mb/s available and then creates the tunnel all the same, so the event describes a tunnel that exists a few lines later. A tunnel event from the state writer or from a bandwidth decision therefore reaches userspace as a change uevent of the domain device, carrying the same two variables.

### The state readers separate finished from started activations

Code that acts on a tunnel asks either whether its activation has finished or whether it has at least started, and a DisplayPort tunnel waiting on its receiver answers the two differently. [`tb_tunnel_is_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L152) and [`tb_tunnel_is_activated()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2503) are shown together, then the caller of the wider test.

[`tb_tunnel_is_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L152) is inline in the header and [`tb_tunnel_is_activated()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2503) is file-static in the implementation:

```c
/* drivers/thunderbolt/tunnel.h:142 */
/**
 * tb_tunnel_is_active() - Is tunnel fully activated
 * @tunnel: Tunnel to check
 *
 * Return: %true if @tunnel is fully activated.
 *
 * Note for DP tunnels this returns %true only once the DPRX capabilities
 * read has been issued successfully. For other tunnels, this function
 * returns %true pretty much once tb_tunnel_activate() returns successfully.
 */
static inline bool tb_tunnel_is_active(const struct tb_tunnel *tunnel)
{
	return tunnel->state == TB_TUNNEL_ACTIVE;
}
/* drivers/thunderbolt/tunnel.c:2502 */
// Is tb_tunnel_activate() called for the tunnel
static bool tb_tunnel_is_activated(const struct tb_tunnel *tunnel)
{
	return tunnel->state == TB_TUNNEL_ACTIVATING || tb_tunnel_is_active(tunnel);
}
```

[`tb_tunnel_is_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L152) compares [`state`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L97) with [`TB_TUNNEL_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L30), and its kerneldoc notes that a DisplayPort tunnel passes only once the receiver capabilities read is done. [`tb_tunnel_is_activated()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2503) also accepts [`TB_TUNNEL_ACTIVATING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L29) and falls back on the narrower test for the finished value, so it answers whether activation was ever started. [`tb_tunnel_consumed_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2603) is the one caller of the wider test, and its comment gives the reason:

```c
/* drivers/thunderbolt/tunnel.c:2608, inside tb_tunnel_consumed_bandwidth() */
	/*
	 * Here we need to distinguish between not active tunnel from
	 * tunnels that are either fully active or activation started.
	 * The latter is true for DP tunnels where we must report the
	 * consumed to be the maximum we gave it until DPRX capabilities
	 * read is done by the graphics driver.
	 */
	if (tb_tunnel_is_activated(tunnel) && tunnel->consumed_bandwidth) {
		int ret;

		ret = tunnel->consumed_bandwidth(tunnel, &up_bw, &down_bw);
		if (ret)
			return ret;
	}
```

[`tb_tunnel_consumed_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2603) asks the protocol once activation has started, which according to the comment reports the maximum a DisplayPort tunnel was given until its receiver read is done. A tunnel that fails the wider test, or has an empty slot, reports zero in both directions and the function still returns 0. The narrow test answers whether activation finished, and the wide one whether it started.

### A mutex serializes every reference take and drop

A tunnel can be held by the domain's list and by a queued DisplayPort poll at the same time, so its lifetime is a reference count behind a driver-wide mutex. The excerpt shows [`tb_tunnel_lock`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L112), then [`tb_tunnel_get()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L197), [`tb_tunnel_destroy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L204) and [`tb_tunnel_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220) in file order.

```c
/* drivers/thunderbolt/tunnel.c:111 */
/* Synchronizes kref_get()/put() of struct tb_tunnel */
static DEFINE_MUTEX(tb_tunnel_lock);
/* drivers/thunderbolt/tunnel.c:197 */
static void tb_tunnel_get(struct tb_tunnel *tunnel)
{
	mutex_lock(&tb_tunnel_lock);
	kref_get(&tunnel->kref);
	mutex_unlock(&tb_tunnel_lock);
}

static void tb_tunnel_destroy(struct kref *kref)
{
	struct tb_tunnel *tunnel = container_of(kref, typeof(*tunnel), kref);
	int i;

	if (tunnel->destroy)
		tunnel->destroy(tunnel);

	for (i = 0; i < tunnel->npaths; i++) {
		if (tunnel->paths[i])
			tb_path_free(tunnel->paths[i]);
	}

	kfree(tunnel);
}

void tb_tunnel_put(struct tb_tunnel *tunnel)
{
	mutex_lock(&tb_tunnel_lock);
	kref_put(&tunnel->kref, tb_tunnel_destroy);
	mutex_unlock(&tb_tunnel_lock);
}
```

[`tb_tunnel_lock`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L112) is one [`DEFINE_MUTEX()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/mutex.h#L86) for every tunnel of every domain, and according to its comment it synchronizes the take and the drop of the count. [`tb_tunnel_get()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L197) wraps [`kref_get()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kref.h#L43) in the mutex and is file-static, which leaves [`tb_dp_dprx_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1114) as its one caller, while [`tb_tunnel_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220) wraps [`kref_put()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kref.h#L62) the same way and is declared in the header for the rest of the driver.

[`tb_tunnel_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220) holds the mutex across [`kref_put()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kref.h#L62), so [`tb_tunnel_destroy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L204) runs with it held and a take never runs beside a drop. The release function recovers the object with [`container_of()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/container_of.h#L19), runs [`destroy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L82) where the protocol filled it, frees the present paths with [`tb_path_free()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L345) and then calls [`kfree()`](https://elixir.bootlin.com/linux/v7.2/source/mm/slub.c#L6671), which also releases the path array.

Commit d6d458d42e1e ("thunderbolt: Handle DisplayPort tunnel activation asynchronously") introduced the count and the mutex together with [`TB_TUNNEL_ACTIVATING`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L29), first shipped in v6.14, and it renamed the free function to `tb_tunnel_put()`. Every take and every drop of a tunnel reference in the driver therefore runs under that one mutex.

### The count reaches zero only when the last holder drops

Only the drop that takes the count from one to zero releases anything, and the DisplayPort receiver poll takes the one reference beyond the allocator's. The figure draws the count with its holders, and [`tb_dp_dprx_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1134) shows the drop that pairs with a cancelled poll.

The count climbs on the left of the rungs and descends on the right, and the release happens only at the bottom crossing:

```
    The reference count of one tunnel and the drop that frees it
    ─────────────────────────────────────────────────────────────
    (takes climb on the left, drops descend on the right)

      2  ──────────────────────────────────────────────────────────────────────────
            ▲  a DisplayPort activation starts         │  one holder drops, the poll once
            │  its receiver poll ⓶                     │  it has run ⓷ or when cancelled
            │                                          │  while pending ⓸, or the domain ⓹
            │                                          ▼
      1  ──────────────────────────────────────────────────────────────────────────
            ▲  the allocator returns the object ⓵      │  the last holder drops, the domain
            │                                          │  ⓹ or a poll that outlived it ⓷
            │                                          ▼
      0  ──────────────────────────────────────────────────────────────────────────
                                                          the release function runs the
                                                          destroy callback, frees every
                                                          path and frees the object

    ⓵ tb_tunnel_alloc                tunnel.c:192   starts the count at 1
    ⓶ tb_dp_dprx_start               tunnel.c:1120  takes the poll's reference under tb_tunnel_lock
    ⓷ tb_dp_dprx_work                tunnel.c:1111  drops the poll's reference as its last step
    ⓸ tb_dp_dprx_stop                tunnel.c:1140  drops it when the cancel removed a pending poll
    ⓹ tb_deactivate_and_free_tunnel  tb.c:1769      drops the reference the domain's list carried
```

Mark ⓵ is the [`kref_init()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kref.h#L29) call in [`tb_tunnel_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L178), which starts a tunnel at one reference. Mark ⓶ is the [`tb_tunnel_get()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L197) call in [`tb_dp_dprx_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1114), made whenever a DisplayPort activation reaches its last step. Mark ⓷ is the [`tb_tunnel_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220) at the end of [`tb_dp_dprx_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1088), the drop that pairs with a poll that ran. Mark ⓸ is the conditional drop in [`tb_dp_dprx_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1134), taken when the cancel removed a pending poll. Mark ⓹ is the final drop in [`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722), after which [`tb_tunnel_destroy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L204) runs unless a poll still holds the object.

[`tb_dp_dprx_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1134) runs first in [`tb_dp_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1144) when that callback is called with false, and it drops the poll's reference if it removed a pending item:

```c
/* drivers/thunderbolt/tunnel.c:1134 */
static void tb_dp_dprx_stop(struct tb_tunnel *tunnel)
{
	if (tunnel->dprx_started) {
		tunnel->dprx_started = false;
		tunnel->dprx_canceled = true;
		if (cancel_delayed_work(&tunnel->dprx_work))
			tb_tunnel_put(tunnel);
	}
}
/* drivers/thunderbolt/tunnel.c:1165 */
		tb_dp_dprx_stop(tunnel);
		tb_dp_port_hpd_clear(tunnel->src_port);
		tb_dp_port_set_hops(tunnel->src_port, 0, 0, 0);
		if (tb_port_is_dpout(tunnel->dst_port))
			tb_dp_port_set_hops(tunnel->dst_port, 0, 0, 0);
```

[`tb_dp_dprx_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1134) clears [`dprx_started`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L103), sets [`dprx_canceled`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L104) and drops the reference when [`cancel_delayed_work()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/workqueue.c#L4551) reports that it removed a pending poll. A poll that is already running is left to finish and makes the drop itself at the end of [`tb_dp_dprx_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1088). Commit 67600ccfc4f3 ("thunderbolt: Fix use-after-free in tb_dp_dprx_work") split the drop that way, first shipped in v6.18.

So far, the tunnel holds the reference of the domain's list, plus the poll's while a DisplayPort poll is pending. The last put column of the model figure is the drop that reaches zero, and whichever holder drops last releases the paths and the object.

### The domain keeps every tunnel it owns on one list

A tunnel outlives the function that built it, so the software connection manager keeps every tunnel it owns on a list in its private area and reaches them from there. The excerpt shows [`struct tb_cm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L64) with its list head. A table then gives every site that initializes, links or unlinks an entry, and the discovery pass that links tunnels at domain start follows it.

[`struct tb_cm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L64) is the private area of the software connection manager, and its first member heads the list:

```c
/* drivers/thunderbolt/tb.c:52 */
/**
 * struct tb_cm - Simple Thunderbolt connection manager
 * @tunnel_list: List of active tunnels
 * @dp_resources: List of available DP resources for DP tunneling
 * @hotplug_active: tb_handle_hotplug will stop progressing plug
 *		    events and exit if this is not set (it needs to
 *		    acquire the lock one more time). Used to drain wq
 *		    after cfg has been paused.
 * @remove_work: Work used to remove any unplugged routers after
 *		 runtime resume
 * @groups: Bandwidth groups used in this domain.
 */
struct tb_cm {
	struct list_head tunnel_list;
	struct list_head dp_resources;
	bool hotplug_active;
	struct delayed_work remove_work;
	struct tb_bandwidth_group groups[MAX_GROUPS];
};
```

[`struct tb_cm`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L64) heads the list with [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65), which its kerneldoc calls the list of active tunnels, and a tunnel's [`list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L95) node joins it. [`dp_resources`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L66), [`hotplug_active`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L67), [`remove_work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L68) and [`groups`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L69) hold the free DisplayPort adapters, the gate on the hotplug handler, the removal work and the bandwidth groups. The table lists the sites that change the list.

| operation on the list | site | function |
|---|---|---|
| initialize the head | [tb.c:3391](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3391) | [`tb_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3374) |
| link each discovered tunnel | [tb.c:405](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L405) | [`tb_switch_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L376) |
| link a USB 3.x tunnel after its activation | [tb.c:982](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L982) | [`tb_tunnel_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L905) |
| link a DisplayPort tunnel before its activation | [tb.c:2036](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2036) | [`tb_tunnel_one_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1971) |
| link a PCIe tunnel after its activation | [tb.c:2315](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2315) | [`tb_tunnel_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2275) |
| link a DMA tunnel after its activation | [tb.c:2355](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2355) | [`tb_approve_xdomain_paths()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2319) |
| unlink during the teardown | [tb.c:1731](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1731) | [`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722) |
| unlink after a failed DisplayPort activation | [tb.c:2041](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2041) | [`tb_tunnel_one_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1971) |
| unlink a PCIe tunnel being disconnected | [tb.c:2270](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2270) | [`tb_disconnect_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2254) |

[`tb_switch_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L376) links the tunnels that discovery returns for a router, then repeats for the routers below it, and [`tb_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1694) hands it the domain's list:

```c
/* drivers/thunderbolt/tb.c:383, inside tb_switch_discover_tunnels() */
	tb_switch_for_each_port(sw, port) {
		struct tb_tunnel *tunnel = NULL;

		switch (port->config.type) {
		case TB_TYPE_DP_HDMI_IN:
			tunnel = tb_tunnel_discover_dp(tb, port, alloc_hopids);
			tb_increase_tmu_accuracy(tunnel);
			break;

		case TB_TYPE_PCIE_DOWN:
			tunnel = tb_tunnel_discover_pci(tb, port, alloc_hopids);
			break;

		case TB_TYPE_USB3_DOWN:
			tunnel = tb_tunnel_discover_usb3(tb, port, alloc_hopids);
			break;

		default:
			break;
		}

		if (tunnel)
			list_add_tail(&tunnel->list, list);
	}
/* drivers/thunderbolt/tb.c:1699, inside tb_discover_tunnels() */
	tb_switch_discover_tunnels(tb->root_switch, &tcm->tunnel_list, true);
```

[`tb_switch_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L376) adds the tunnels to the list it was given, and at domain start [`tb_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1694) passes [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) as that list. No activation runs on the way, so a discovered tunnel is listed at [`TB_TUNNEL_INACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L28) while the hop entries it was found through are programmed. The list therefore holds every tunnel the connection manager owns, in any state, from its link until an unlink.

### The lookup matches a listed tunnel by type and end

The connection manager finds a listed tunnel again from its protocol and either of its adapters, and an adapter passed as `NULL` never matches. [`tb_find_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L490) is shown in full, and a caller that tears down what it finds follows it.

[`tb_find_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L490) returns the first listed tunnel whose type matches and whose source or destination is the adapter asked for:

```c
/* drivers/thunderbolt/tb.c:490 */
static struct tb_tunnel *tb_find_tunnel(struct tb *tb, enum tb_tunnel_type type,
					struct tb_port *src_port,
					struct tb_port *dst_port)
{
	struct tb_cm *tcm = tb_priv(tb);
	struct tb_tunnel *tunnel;

	list_for_each_entry(tunnel, &tcm->tunnel_list, list) {
		if (tunnel->type == type &&
		    ((src_port && src_port == tunnel->src_port) ||
		     (dst_port && dst_port == tunnel->dst_port))) {
			return tunnel;
		}
	}

	return NULL;
}
```

[`tb_find_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L490) reaches the private area with [`tb_priv()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L545) and goes through [`tunnel_list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L65) with [`list_for_each_entry()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/list.h#L818), comparing [`type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L96) first. Both sides test their adapter argument before comparing it, so a `NULL` adapter matches no tunnel and a call with both `NULL` returns `NULL`. Each of the six call sites names a protocol and at least one adapter.

[`tb_dp_resource_unavailable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2178) looks the tunnel up by whichever DisplayPort adapter it was given and tears it down when one exists:

```c
/* drivers/thunderbolt/tb.c:2194, inside tb_dp_resource_unavailable() */
	tunnel = tb_find_tunnel(tb, TB_TUNNEL_DP, in, out);
	if (tunnel)
		tb_deactivate_and_free_tunnel(tunnel);
	else
		tb_enter_redrive(port);
	list_del_init(&port->list);
```

[`tb_dp_resource_unavailable()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2178) hands a found tunnel to [`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722), and in either case it takes the adapter off the domain's free DisplayPort resources with [`list_del_init()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/list.h#L316). A listed tunnel is therefore found by its protocol and one of its ends, and the first match wins.

### Teardown deactivates and unlinks a tunnel before returning claims

The domain removes a listed tunnel by deactivating and unlinking it before it returns what the protocol claimed and drops the list's reference. The outline divides [`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722) into three pieces, and this subsection reads pieces ① and ②.

| piece | lines | stage |
|---|---|---|
| ① | [tb.c:1722-1736](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722) | tolerates `NULL`, deactivates, unlinks and saves the domain and both adapters |
| ② | [tb.c:1737-1756](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1737) | returns the DisplayPort claims and falls into the USB 3.x case |
| ③ | [tb.c:1757-1770](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1757) | reclaims USB 3.x bandwidth, leaves PCIe and DMA alone and drops the reference |

Piece ① of [`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722) takes the tunnel out of service and off the list:

```c
/* drivers/thunderbolt/tb.c:1722 */
static void tb_deactivate_and_free_tunnel(struct tb_tunnel *tunnel)
{
	struct tb_port *src_port, *dst_port;
	struct tb *tb;

	if (!tunnel)
		return;

	tb_tunnel_deactivate(tunnel);
	list_del(&tunnel->list);

	tb = tunnel->tb;
	src_port = tunnel->src_port;
	dst_port = tunnel->dst_port;

```

[`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722) returns at once for a `NULL` argument, then calls [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) and unlinks the node with [`list_del()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/list.h#L258), so from here the domain's list no longer reaches the tunnel. It saves the domain and both adapters in locals for the cases that follow.

Piece ② of [`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722) is the DisplayPort case, which returns four things the DisplayPort tunneling path claimed:

```c
/* drivers/thunderbolt/tb.c:1737 */
	switch (tunnel->type) {
	case TB_TUNNEL_DP:
		tb_detach_bandwidth_group(src_port);
		/*
		 * In case of DP tunnel make sure the DP IN resource is
		 * deallocated properly.
		 */
		tb_switch_dealloc_dp_resource(src_port->sw, src_port);
		/*
		 * If bandwidth on a link is < asym_threshold
		 * transition the link to symmetric.
		 */
		tb_configure_sym(tb, src_port, dst_port, true);
		/* Now we can allow the domain to runtime suspend again */
		pm_runtime_mark_last_busy(&dst_port->sw->dev);
		pm_runtime_put_autosuspend(&dst_port->sw->dev);
		pm_runtime_mark_last_busy(&src_port->sw->dev);
		pm_runtime_put_autosuspend(&src_port->sw->dev);
		fallthrough;

```

[`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722) removes the input adapter from its bandwidth group with [`tb_detach_bandwidth_group()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1676), returns the DisplayPort input resource with [`tb_switch_dealloc_dp_resource()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3735) and lets [`tb_configure_sym()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1147) move the links back to symmetric where bandwidth allows. The two [`pm_runtime_put_autosuspend()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L599) calls release a runtime PM reference on each router, and [`fallthrough`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/compiler_attributes.h#L214) sends the DisplayPort case into the USB 3.x case.

The teardown therefore takes a tunnel out of service and off the list first, and by the end of piece ② a DisplayPort tunnel has also returned its DisplayPort claims.

### The teardown ends by dropping the list's reference

The teardown ends by returning the guaranteed bandwidth a tunnel held and then dropping the reference the domain's list carried. Piece ③ closes [`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722), and the other ways a listed tunnel is dropped follow it.

Piece ③ of [`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722) handles USB 3.x, leaves PCIe and DMA alone, and drops the reference:

```c
/* drivers/thunderbolt/tb.c:1757 */
	case TB_TUNNEL_USB3:
		tb_reclaim_usb3_bandwidth(tb, src_port, dst_port);
		break;

	default:
		/*
		 * PCIe and DMA tunnels do not consume guaranteed
		 * bandwidth.
		 */
		break;
	}

	tb_tunnel_put(tunnel);
}
```

[`tb_deactivate_and_free_tunnel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1722) calls [`tb_reclaim_usb3_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L876) for a USB 3.x tunnel and for a DisplayPort tunnel that fell through. According to the comment "PCIe and DMA tunnels do not consume guaranteed bandwidth", the default case leaves them alone. The final [`tb_tunnel_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L220) is mark ⓹ of the reference figure, and it reaches [`tb_tunnel_destroy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L204) unless a DisplayPort poll still holds the object.

Five call sites use this teardown, and three other sites drop a listed tunnel in their own way. [`tb_tunnel_one_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1971) gives its claims back inline in the unwind ladder at [tb.c:2047-2060](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2047) when an activation fails, without entering this function, and [`tb_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2941) drops every listed tunnel when the domain stops. [`tb_disconnect_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2254) is the third, and it tears a PCIe tunnel down without the type switch:

```c
/* drivers/thunderbolt/tb.c:2263, inside tb_disconnect_pci() */
	tunnel = tb_find_tunnel(tb, TB_TUNNEL_PCI, NULL, up);
	if (WARN_ON(!tunnel))
		return -ENODEV;

	tb_switch_xhci_disconnect(sw);

	tb_tunnel_deactivate(tunnel);
	list_del(&tunnel->list);
	tb_tunnel_put(tunnel);
	return 0;
```

[`tb_disconnect_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2254) finds the tunnel by its upstream adapter, then deactivates, unlinks and drops it in the teardown's order. A PCIe tunnel reaches the empty default case of the teardown's switch anyway, so the two routes leave the same state behind.

So far, a tunnel that joined the domain's list has left it through the teardown or one of those three sites, and the model figure's last put column is reached. The teardown returns the claims the tunnel's type made before the list's reference goes.

### A router that goes away invalidates the tunnels through it

When a router is marked unplugged, the tunnels whose paths cross it are condemned, and a tunnel finds out by asking its paths in turn. [`tb_tunnel_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2382) is shown in full, then the path test it applies, then the sweep that removes the tunnels it condemns.

[`tb_tunnel_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2382) asks the paths of the tunnel in order and stops at the first bad one:

```c
/* drivers/thunderbolt/tunnel.c:2376 */
/**
 * tb_tunnel_is_invalid - check whether an activated path is still valid
 * @tunnel: Tunnel to check
 *
 * Return: %true if path is valid, %false otherwise.
 */
bool tb_tunnel_is_invalid(struct tb_tunnel *tunnel)
{
	int i;

	for (i = 0; i < tunnel->npaths; i++) {
		WARN_ON(!tunnel->paths[i]->activated);
		if (tb_path_is_invalid(tunnel->paths[i]))
			return true;
	}

	return false;
}
```

[`tb_tunnel_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2382) answers true as soon as [`tb_path_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L598) reports a path, so one bad path condemns the tunnel. The [`WARN_ON()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bug.h#L109) in the loop records that the function expects programmed paths, and it neither skips nor stops at an entry that fails the test. The kerneldoc's return line calls true the valid answer, while the code returns true for an invalid tunnel, and the name and both callers follow the code.

[`tb_path_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L598) looks at the routers on both sides of the path's hops:

```c
/* drivers/thunderbolt/path.c:598 */
bool tb_path_is_invalid(struct tb_path *path)
{
	int i = 0;
	for (i = 0; i < path->path_length; i++) {
		if (path->hops[i].in_port->sw->is_unplugged)
			return true;
		if (path->hops[i].out_port->sw->is_unplugged)
			return true;
	}
	return false;
}
```

[`tb_path_is_invalid()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L598) reports a path when a hop enters or leaves a router whose [`is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L193) is set, so the question needs no hardware access. [`tb_free_invalid_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1775) applies the tunnel query to the listed tunnels and tears down those it condemns:

```c
/* drivers/thunderbolt/tb.c:1781, inside tb_free_invalid_tunnels() */
	list_for_each_entry_safe(tunnel, n, &tcm->tunnel_list, list) {
		if (tb_tunnel_is_invalid(tunnel))
			tb_deactivate_and_free_tunnel(tunnel);
	}
```

[`tb_free_invalid_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1775) uses [`list_for_each_entry_safe()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/list.h#L905) because the teardown unlinks the entry it is holding. A tunnel through a router that went away is therefore condemned by its first path that touches that router, and the unplug sweep removes it.

### The port query answers for any path in either direction

Policy code needs to know whether an adapter carries any of a tunnel's traffic in either direction, and the tunnel answers by asking its paths in turn. [`tb_tunnel_port_on_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2486) is shown in full, then the bandwidth loop that applies it next to the validity and type tests.

[`tb_tunnel_port_on_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2486) tolerates an empty entry of the path array as it goes:

```c
/* drivers/thunderbolt/tunnel.c:2478 */
/**
 * tb_tunnel_port_on_path() - Does the tunnel go through port
 * @tunnel: Tunnel to check
 * @port: Port to check
 *
 * Return: %true if @tunnel goes through @port (direction does not matter),
 * %false otherwise.
 */
bool tb_tunnel_port_on_path(const struct tb_tunnel *tunnel,
			    const struct tb_port *port)
{
	int i;

	for (i = 0; i < tunnel->npaths; i++) {
		if (!tunnel->paths[i])
			continue;

		if (tb_path_port_on_path(tunnel->paths[i], port))
			return true;
	}

	return false;
}
```

[`tb_tunnel_port_on_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2486) skips a `NULL` entry of [`paths`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L110), hands the other entries to [`tb_path_port_on_path()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L620) and returns true at the first path through the adapter. Its kerneldoc says the answer holds in either direction, which follows from asking the tunnel's paths in both directions.

[`tb_consumed_dp_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L605) applies the validity, type and port tests in turn before it counts a DisplayPort tunnel against a port:

```c
/* drivers/thunderbolt/tb.c:624, inside tb_consumed_dp_bandwidth() */
	list_for_each_entry(tunnel, &tcm->tunnel_list, list) {
		const struct tb_bandwidth_group *group;
		int dp_consumed_up, dp_consumed_down;

		if (tb_tunnel_is_invalid(tunnel))
			continue;

		if (!tb_tunnel_is_dp(tunnel))
			continue;

		if (!tb_tunnel_port_on_path(tunnel, port))
			continue;
```

[`tb_consumed_dp_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L605) skips a tunnel through an unplugged router, a tunnel of another protocol and a tunnel whose paths avoid the port, so only DisplayPort tunnels crossing the port add to the total. The link-power gate at [tb.c:213](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L213) is the other caller in the driver. One path through the adapter is enough for the query to answer for the tunnel, in both directions.

### Inline type tests pick one protocol out of the list

Code that goes through the domain's list is after the tunnels of one protocol, and inline tests answer from the type the allocator fixed. The excerpt shows [`tb_tunnel_is_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L173) with the other type tests, and the users [`tb_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1694), [`tb_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2941) and [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) follow them.

[`tb_tunnel_is_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L173) and the other type tests are neighbours in the header:

```c
/* drivers/thunderbolt/tunnel.h:173 */
static inline bool tb_tunnel_is_pci(const struct tb_tunnel *tunnel)
{
	return tunnel->type == TB_TUNNEL_PCI;
}

static inline bool tb_tunnel_is_dp(const struct tb_tunnel *tunnel)
{
	return tunnel->type == TB_TUNNEL_DP;
}

static inline bool tb_tunnel_is_dma(const struct tb_tunnel *tunnel)
{
	return tunnel->type == TB_TUNNEL_DMA;
}

static inline bool tb_tunnel_is_usb3(const struct tb_tunnel *tunnel)
{
	return tunnel->type == TB_TUNNEL_USB3;
}
```

[`tb_tunnel_is_pci()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L173), [`tb_tunnel_is_dp()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L178), [`tb_tunnel_is_dma()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L183) and [`tb_tunnel_is_usb3()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L188) each compare [`type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L96) with one value of [`enum tb_tunnel_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L14), and every call of the four is in [`drivers/thunderbolt/tb.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c). [`tb_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1694) applies the first two to the tunnels it has just listed at domain start:

```c
/* drivers/thunderbolt/tb.c:1701, inside tb_discover_tunnels() */
	list_for_each_entry(tunnel, &tcm->tunnel_list, list) {
		if (tb_tunnel_is_pci(tunnel)) {
			struct tb_switch *parent = tunnel->dst_port->sw;

			while (parent != tunnel->src_port->sw) {
				parent->boot = true;
				parent = tb_switch_parent(parent);
			}
		} else if (tb_tunnel_is_dp(tunnel)) {
			struct tb_port *in = tunnel->src_port;
			struct tb_port *out = tunnel->dst_port;

			/* Keep the domain from powering down */
			pm_runtime_get_sync(&in->sw->dev);
			pm_runtime_get_sync(&out->sw->dev);

			tb_discover_bandwidth_group(tcm, in, out);
		}
	}
```

[`tb_discover_tunnels()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1694) marks the routers from the destination of a discovered PCIe tunnel up to its source as booted, and takes a runtime PM reference on both routers of a discovered DisplayPort tunnel with [`pm_runtime_get_sync()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/pm_runtime.h#L511). [`tb_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2941) applies the DMA test to the listed tunnels when the domain stops:

```c
/* drivers/thunderbolt/tb.c:2949, inside tb_stop() */
	list_for_each_entry_safe(tunnel, n, &tcm->tunnel_list, list) {
		/*
		 * DMA tunnels require the driver to be functional so we
		 * tear them down. Other protocol tunnels can be left
		 * intact.
		 */
		if (tb_tunnel_is_dma(tunnel))
			tb_tunnel_deactivate(tunnel);
		tb_tunnel_put(tunnel);
	}
```

[`tb_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2941) deactivates a DMA tunnel alone, whose traffic needs the driver according to the comment, and leaves the other tunnels programmed while it drops the domain's reference on them. It unlinks no entry on the way. [`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) applies the USB 3.x test in both of its passes over tunnels at resume:

```c
/* drivers/thunderbolt/tb.c:3169, inside tb_resume_noirq() */
	tb_switch_discover_tunnels(tb->root_switch, &tunnels, false);
	list_for_each_entry_safe_reverse(tunnel, n, &tunnels, list) {
		if (tb_tunnel_is_usb3(tunnel))
			usb3_delay = 500;
		tb_tunnel_deactivate(tunnel);
		tb_tunnel_put(tunnel);
	}

	/* Re-create our tunnels now */
	list_for_each_entry_safe(tunnel, n, &tcm->tunnel_list, list) {
		/* USB3 requires delay before it can be re-activated */
		if (tb_tunnel_is_usb3(tunnel)) {
			msleep(usb3_delay);
			/* Only need to do it once */
			usb3_delay = 0;
		}
		tb_tunnel_activate(tunnel);
	}
```

[`tb_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3141) tears down the tunnels found on a local list after resume and sets a 500 ms delay when one of them is USB 3.x. It spends that delay before re-activating the first USB 3.x tunnel of the domain's list, and it re-activates every listed tunnel without looking at the result. A type test is how each of these callers picks its protocol out of the list.

### The direction test picks which bandwidth ceiling applies

A tunnel's two adapters have no fixed up or down, so code that chooses between the upstream and the downstream ceiling asks the direction test. The excerpt shows [`tb_tunnel_direction_downstream()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L193) with the helper it forwards to, and the DisplayPort capability exchange uses it.

[`tb_tunnel_direction_downstream()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L193) forwards both adapters to [`tb_port_path_direction_downstream()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1122):

```c
/* drivers/thunderbolt/tunnel.h:193 */
static inline bool tb_tunnel_direction_downstream(const struct tb_tunnel *tunnel)
{
	return tb_port_path_direction_downstream(tunnel->src_port,
						 tunnel->dst_port);
}
/* drivers/thunderbolt/tb.h:1113 */
/**
 * tb_port_path_direction_downstream() - Checks if path is directed downstream
 * @src: Source adapter
 * @dst: Destination adapter
 *
 * Return: %true only if the specified path from source adapter (@src)
 * to destination adapter (@dst) is directed downstream.
 */
static inline bool
tb_port_path_direction_downstream(const struct tb_port *src,
				  const struct tb_port *dst)
{
	return src->sw->config.depth < dst->sw->config.depth;
}
```

[`tb_tunnel_direction_downstream()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L193) passes the source adapter and then the destination adapter, and [`tb_port_path_direction_downstream()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L1122) answers true when the source router's depth is smaller than the destination router's. [`tb_dp_xchg_caps()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L815) uses the answer to pick which ceiling limits a DisplayPort tunnel:

```c
/* drivers/thunderbolt/tunnel.c:871, inside tb_dp_xchg_caps() */
	if (tb_tunnel_direction_downstream(tunnel))
		max_bw = tunnel->max_down;
	else
		max_bw = tunnel->max_up;

	if (max_bw && bw > max_bw) {
		u32 new_rate, new_lanes, new_bw;

		ret = tb_dp_reduce_bandwidth(max_bw, in_rate, in_lanes,
					     out_rate, out_lanes, &new_rate,
					     &new_lanes);
		if (ret) {
			tb_tunnel_info(tunnel, "not enough bandwidth\n");
			return ret;
		}
```

[`tb_dp_xchg_caps()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L815) takes [`max_down`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L99) when the tunnel runs downstream and [`max_up`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L98) otherwise, and it reports a ceiling it cannot meet through [`tb_tunnel_info`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L240). Every caller of the direction test is DisplayPort bandwidth code, seven in the tunnel code and three in the connection manager.

So far, the page has followed the tunnel from allocation to teardown, and callers have read its type and direction off the object whenever they needed them. The direction test answers from the two adapters the allocator stored, with no hardware access.

### Each tunnel log line starts with both ends and type

Several tunnels can be set up at once, so a tunnel message starts with the route and adapter of both ends and the type name. The excerpt shows [`__TB_TUNNEL_PRINT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L224) with its four wrappers, then the domain's level macros with [`tb_tunnel_type_name()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2680), and a warning from the DisplayPort code closes the subsection.

[`__TB_TUNNEL_PRINT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L224) builds the prefix from the object, and the wrappers hand it a level macro:

```c
/* drivers/thunderbolt/tunnel.h:224 */
#define __TB_TUNNEL_PRINT(level, tunnel, fmt, arg...)                   \
	do {                                                            \
		struct tb_tunnel *__tunnel = (tunnel);                  \
		level(__tunnel->tb, "%llx:%u <-> %llx:%u (%s): " fmt,   \
		      tb_route(__tunnel->src_port->sw),                 \
		      __tunnel->src_port->port,                         \
		      tb_route(__tunnel->dst_port->sw),                 \
		      __tunnel->dst_port->port,                         \
		      tb_tunnel_type_name(__tunnel),			\
		      ## arg);                                          \
	} while (0)

#define tb_tunnel_WARN(tunnel, fmt, arg...) \
	__TB_TUNNEL_PRINT(tb_WARN, tunnel, fmt, ##arg)
#define tb_tunnel_warn(tunnel, fmt, arg...) \
	__TB_TUNNEL_PRINT(tb_warn, tunnel, fmt, ##arg)
#define tb_tunnel_info(tunnel, fmt, arg...) \
	__TB_TUNNEL_PRINT(tb_info, tunnel, fmt, ##arg)
#define tb_tunnel_dbg(tunnel, fmt, arg...) \
	__TB_TUNNEL_PRINT(tb_dbg, tunnel, fmt, ##arg)
```

[`__TB_TUNNEL_PRINT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L224) copies its argument into a local before its uses, so a caller may pass an expression with side effects, and prints both ends as the [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) of the router and the [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L290) number of the adapter. [`tb_tunnel_WARN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L236), [`tb_tunnel_warn`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L238), [`tb_tunnel_info`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L240) and [`tb_tunnel_dbg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L242) pass their level macro as the first argument. The domain's own level macros start with [`tb_err`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L728), and [`tb_tunnel_type_name()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2680) is the accessor the wrapper calls for the name:

```c
/* drivers/thunderbolt/tb.h:728 */
#define tb_err(tb, fmt, arg...) dev_err((tb)->nhi->dev, fmt, ## arg)
#define tb_WARN(tb, fmt, arg...) dev_WARN((tb)->nhi->dev, fmt, ## arg)
#define tb_warn(tb, fmt, arg...) dev_warn((tb)->nhi->dev, fmt, ## arg)
#define tb_info(tb, fmt, arg...) dev_info((tb)->nhi->dev, fmt, ## arg)
#define tb_dbg(tb, fmt, arg...) dev_dbg((tb)->nhi->dev, fmt, ## arg)
/* drivers/thunderbolt/tunnel.c:2680 */
const char *tb_tunnel_type_name(const struct tb_tunnel *tunnel)
{
	return tb_tunnel_names[tunnel->type];
}
```

[`tb_WARN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L729), [`tb_warn`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L730), [`tb_info`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L731) and [`tb_dbg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L732) print through the device of the domain's host interface, so a tunnel message appears under that device, and [`tb_err`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L728) has no tunnel wrapper. [`tb_tunnel_type_name()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2680) indexes [`tb_tunnel_names`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L101) with [`type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L96) without a range check, and the wrapper is its one caller. Commit 8c3ff7c5ae15 ("thunderbolt: Move pci_device out of tb_nhi") gave the five level macros that device argument, first shipped in v7.2.

[`tb_dp_read_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1337) is the one user of the backtrace wrapper, which it reaches for a capability index it does not know:

```c
/* drivers/thunderbolt/tunnel.c:1344, inside tb_dp_read_cap() */
	switch (cap) {
	case DP_LOCAL_CAP:
	case DP_REMOTE_CAP:
	case DP_COMMON_CAP:
		break;

	default:
		tb_tunnel_WARN(tunnel, "invalid capability index %#x\n", cap);
		return -EINVAL;
	}
```

[`tb_dp_read_cap()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1337) warns through [`tb_tunnel_WARN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L236), which adds a backtrace to the prefixed message, and returns `-EINVAL`. The admin guide states that the details variable of a tunnel uevent matches the driver's logging format, and the two format strings on this page agree.

The prefix, shared with the uevent details, is how a reader of the kernel log tells one tunnel from another.

### Activation opens the state guards of the bandwidth code

Turning a tunnel on programs its paths in the routers and opens the state guards that the bandwidth code keeps on the tunnel. A table lists the guarded call sites, and the guard of [`tb_tunnel_maximum_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2520) and the DisplayPort completion callback show the two kinds.

While a tunnel is active, the routers forward its traffic along the programmed hop entries without any code of this object running. While a DisplayPort tunnel is still activating, its poll queues itself again after 50 ms until the receiver is done or the deadline passes, which [`dprx_timeout`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L85) sets to 12000 ms through [`TB_DPRX_TIMEOUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L81) by default. When the state reaches active that poll stops queueing itself, and the write of the state does nothing beyond recording it and reporting it.

A call site gains a precondition when it reads the tunnel's state through [`tb_tunnel_is_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L152) or [`tb_tunnel_is_activated()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2503) before acting, and seven sites do so.

| site | function | when the test fails |
|---|---|---|
| [tunnel.c:2523](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2523) | [`tb_tunnel_maximum_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2520) | returns `-ENOTCONN` |
| [tunnel.c:2548](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2548) | [`tb_tunnel_allocated_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2545) | returns `-ENOTCONN` |
| [tunnel.c:2573](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2573) | [`tb_tunnel_alloc_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2570) | returns `-ENOTCONN` |
| [tunnel.c:2615](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2615) | [`tb_tunnel_consumed_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2603) | reports zero, and a started activation is enough to pass |
| [tunnel.c:2643](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2643) | [`tb_tunnel_release_unused_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2641) | returns `-ENOTCONN` |
| [tunnel.c:2672](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2672) | [`tb_tunnel_reclaim_available_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2668) | returns without reclaiming |
| [tb.c:1913](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1913) | [`tb_dp_tunnel_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1906) | takes the other branch, which removes the tunnel |

[`tb_tunnel_maximum_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2520) shows the shape of the narrow guards:

```c
/* drivers/thunderbolt/tunnel.c:2520 */
int tb_tunnel_maximum_bandwidth(struct tb_tunnel *tunnel, int *max_up,
				int *max_down)
{
	if (!tb_tunnel_is_active(tunnel))
		return -ENOTCONN;

	if (tunnel->maximum_bandwidth)
		return tunnel->maximum_bandwidth(tunnel, max_up, max_down);
	return -EOPNOTSUPP;
}
```

[`tb_tunnel_maximum_bandwidth()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2520) answers `-ENOTCONN` before it looks at the slot, so a tunnel that is not active gets no bandwidth answer at all. A tunnel found by discovery is listed at [`TB_TUNNEL_INACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L28), so these guards treat it as not connected until something activates it. [`tb_dp_tunnel_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1906), the completion callback of a DisplayPort tunnel, reads the state under the domain lock to learn whether the poll succeeded:

```c
/* drivers/thunderbolt/tb.c:1912, inside tb_dp_tunnel_active() */
	mutex_lock(&tb->lock);
	if (tb_tunnel_is_active(tunnel)) {
		int consumed_up, consumed_down, ret;

		tb_tunnel_dbg(tunnel, "DPRX capabilities read completed\n");

		/* If fail reading tunnel's consumed bandwidth, tear it down */
		ret = tb_tunnel_consumed_bandwidth(tunnel, &consumed_up,
						   &consumed_down);
		if (ret) {
			tb_tunnel_warn(tunnel,
				       "failed to read consumed bandwidth, tearing down\n");
			tb_deactivate_and_free_tunnel(tunnel);
```

[`tb_dp_tunnel_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1906) reads the consumption of an active tunnel and tears the tunnel down if that read fails, while a tunnel whose poll timed out takes the branch at [tb.c:1945-1964](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L1945) and is removed there. The callback therefore runs either way, and the state picks its branch.

The return to [`TB_TUNNEL_INACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.h#L28) is driven by [`tb_tunnel_deactivate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L2458) from its eight call sites, the error label of activation among them, and no other code writes that value after allocation. This object hands off at [`tb_path_activate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/path.c#L492) for the hop entries, at the slot callbacks for the adapters and at [`tb_dp_dprx_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tunnel.c#L1088) for the DisplayPort poll. An active tunnel gains answers from the bandwidth code and keeps them until deactivation writes the inactive state.
