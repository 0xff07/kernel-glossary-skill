# Bluetooth knowledge-base campaign: plan

> MIGRATED 2026-07-18 to the campaigns/ layout (SKILL.md, "The three artifacts and the three states"): this file is now the committed, execution-free campaign SPEC. Its former Status section moved to the machine-local run log `progress/bluetooth/log.md` on the machine that ran it; execution state is derived (catalog vs `docs/`), and runs happen only as user-invoked slices under the overwrite guard. This spec predates the machine-portability rule — any absolute path remaining in it is historical record to re-derive from the local environment at dispatch time, and where its older wording conflicts with current `guidelines/`, the guidelines govern.

## Context

Campaign short name: `bluetooth`. Campaign file: `campaigns/bluetooth.md`; artifact directory: `progress/bluetooth/` (dossiers and other agent intermediates land there; nothing outside it).

Request source: `prompt.md` at the documented tree's root, amended by the user in conversation on 2026-07-18. Every constraint that governs this campaign is recorded VERBATIM under Scope decisions below, so this file stands alone: neither `prompt.md` nor the originating conversation is needed to resume it.

Two user amendments (2026-07-18) shape everything below:

1. **Stale-material rule** (near-verbatim): "The materials contains staled information. You may reuse high-level concept but must take great care with its details." The topic list and every technical claim in `prompt.md` are treated as high-level guidance only. No symbol name, file path, protocol claim, or behavior description from the prompt lands in a page or in this plan as fact; everything is researched against the documented tree. One concrete staleness specimen is recorded under Scope decisions ("known-stale specimens").
2. **Portability rule** (near-verbatim): "make the plan file so that it doesn't include any information about the local environments (e.g. absolute paths), so that an agent with this agent skill on another machine can start the plan independently." This file therefore contains no absolute paths and no machine-local facts. Every path is relative to one of two roots, named explicitly: the **skill root** (the directory holding `SKILL.md`; e.g. `docs/bluetooth/`, `progress/bluetooth/`, `guidelines/...`) or the **tree root** (the kernel checkout; e.g. `net/bluetooth/hci_core.c`). A resuming agent resolves the skill root per SKILL.md ("Skill layout") and the tree by the pin below. Sub-agent briefs composed FROM this file get the locally-resolved absolute paths at dispatch time; the briefs recorded here keep the `<SKILL_ROOT>`/`<TREE_ROOT>` placeholders.

Documented tree: Linux tag `v7.0`, commit `028ef9c96e96197026887c0f092424679298aae8` ("Linux 7.0"); `git describe --tags` at the tree root must print `v7.0`. All Elixir links use `https://elixir.bootlin.com/linux/v7.0/source/...`. Research tooling: semcode where an index for this commit exists, Grep/Read otherwise; the on-disk tree at the pin is always ground truth (7e, 7o), so absence of semcode on a resuming machine changes cost, not correctness.

Subsystem Map entry Bluetooth (`guidelines/reference/subsystems.md`): dir `bluetooth`, tag `bluetooth`, kernel_paths `net/bluetooth/`, `drivers/bluetooth/`, `include/net/bluetooth/`, spec "Bluetooth Core Specification", section6_heading INTERFACES.

NOT inputs: the other campaigns' entries under `progress/` (other runs; isolation per SKILL.md, "The three artifacts and the three states"); `guidelines/reference/samples/` (style/structure/depth calibration only, never kernel facts); `prompt.md`'s technical details (stale by declaration — its instructions and topic list govern scope, its implied facts do not).

Output root: `docs/bluetooth/`. No `SUMMARY.md`/`mkdocs.yml` edits. No git commits without an explicit user go.

## Re-entry contract (retrofitted 2026-07-18)

Standing instructions to any executor, on any machine, cold or warm:

1. Confirm the tree: a Linux kernel checkout at tag `v7.0`, commit `028ef9c96e96` (`git describe --tags` at the tree root prints `v7.0`). A different tree voids every anchor in this spec — stop and surface it.
2. Derive campaign state: diff this catalog's 73 rows against their output paths under `docs/bluetooth/`. A page on disk is done (presumed to have completed its writing run's check pass); a missing page is open. There is no shared execution log to consult.
3. Create or reuse the machine-local workspace `progress/bluetooth/` (run log `log.md`, dossiers). It is never committed.
4. Execute ONLY the slice the invoker named — a batch from this spec's batch order (its recommended slicing), or an explicit page list. Given a bare "run bluetooth" with no slice: report the derived state and ask; never pick a slice autonomously. Overwrite guard: a catalog page that already exists on disk is never overwritten silently — stop and surface it.
5. Run the slice per SKILL.md "Modes": one writer per page, briefed per `guidelines/passes/02-write.md` with the page's catalog row, its cluster's boundary rules, and the project-specific bans and write-time cautions from this spec's Execution & verification section; then the orchestrator check per page (`guidelines/passes/03-check.md`); events go to the run log.
6. Promote anything durable — a spec claim the tree refuted, a user amendment, a settled adjudication — into this spec as a dated amendment (or surface it for the 7r registry). The run log does not travel.
7. Verification: on demand only (Scope decision 2) — run `bluetooth-verify` only when the user asks (`guidelines/passes/04-verify.md`); CERTIFIED stamps land in the verify run's log.

## Scope decisions

### Hard constraints from prompt.md (instructions, verbatim or near-verbatim; the stale-details caveat applies to the prompt's technical claims, never to these instructions)

1. "The pages you're going to create should focus on how Linux kernel internally tracking / representing some of the major constructs. Make sure major construct under net/bluetooth are covered."
2. "Also make sure you find examples in drivers/bluetooth/ for how drivers briddges the core bluetooth layer. For drivers, focus on btusb, btintel, and btmtk, and vhci. make sure for every major bluetooth construct, you find at least one example in the driver."
3. "You can decide the granularity of pages. Prefer finer granularity whenever possible."
4. "Make sure you provide enough context when cross-referencing between source code. Make sure each page is self-contained."
5. "!!!IMPORTANT!!!: Don't limit yourself to 100-400 lines per page. There's no bound to how long a page is. Do as detailed as you can."
6. "Use semcode tools for planning and research, but do note that semcode isn't always accurate. So when writing final pages, verify things on disk."
7. "This topic list is very rough. Curate new pages where you see fit."
8. "Make sure to cover all the possible state transitions and semantics of callbacks of each ops structure."
9. "For all the behaviors mentioned in the topic list, you must point out all the places in the linux kernel that match the behavior, and cite the source code accordingly. Cite as many and as complete as possible." (rule 7j)
10. "Make sure to cover as many kernel's internal data structures and helper functions … to access/maintain those architectural constructs."
11. "Also, pay extra attention to things about the life cycle of these objects, like allocation, freeing, locking and reference count for all these objects."
12. "Pay extra attention to any asynchronous behaviors, like notifications, work deferring, sleeps, completion, deferring by marking things dirty and processing later. Lazy processing etc."
13. "Pay extra attention for state transitions."
14. "Ground yourself with local kernel source code. This is from 7.0 and some of the information may have drifted."
15. "Do a detailed explanation to the lifecycle of relevant objects in the kernel. If you mention any kernel functions, make sure also cite example usage in the drivers for them."
16. "Cite kernel code as markdown code blocks for illustration purpose as much as you can. If you have knowledge to the packet format, draw them in ASCII diagram and put them in the pages as well. Also use ASCII diragram to visualize relationship between kernel constructs (e.g. what structs are defined? how structs are maintained? what are their relationship between each other? state machine.) Provide as many examples as possible." (7g-7i govern figure form)
17. "Make sure that every inline markdown code blocks are properly linked" (7m governs).

### Topic list from prompt.md (verbatim; rough by its own declaration — each bullet maps to catalog rows or recorded fold-ins)

- BR/EDR overview in Linux kernel
- BLE overview in Linux kernel
- LL: this should include: Bluetooth advertising; Bluetooth scanning; Bluetooth pairing process. "Note that there part of those feature are directory controlled by upper ATT/GATT/GAP protocols. Point them out."
- mgmt socket and framework
- BLE host: GAP protocol; GATT protocol; ATT protocol. "Note that GAP/GATT/ATT are implemented in user space"
- Bluetooth HCI protocol — "Point out vendor-specific implementations (e.g. those in btusb) in separate pages."
- Bluetooth L2CAP
- RFCOMM
- SDP
- LE-Audio

### Known-stale specimens (evidence for the stale-material rule)

- prompt.md carries the bullet "Pay extra attention to synchronization, mechanism to prevent/avoid race conditions, and locking between page cache and its backing block devices" — a leftover from a memory-management prompt, inapplicable to Bluetooth. Adjudication: read it as the generic instruction "cover synchronization and race-avoidance between cooperating layers" (core↔driver, socket↔connection, workqueue↔event paths); the page-cache wording itself maps to nothing here.
- (Further specimens land here as inventory digests surface them, e.g. topic-list constructs that no longer exist at v7.0.)

### User-confirmed decisions (checkpoint answers, 2026-07-18)

1. Catalog: APPROVED, writing HELD. The user approved the catalog but chose "Approve catalog, hold writing" — no writer is dispatched until an explicit later go (e.g. "continue the bluetooth campaign" / "start batch B1"). Once writing starts, pages save without per-page asks (campaign mode); git commits always require a separate explicit go.
2. Verification cadence: ON DEMAND ONLY. No scheduled `bluetooth-verify` run after B1 or at campaign end; the user triggers certification explicitly.
3. Driver scope: hci_uart family OPTED IN as two curated rows — drivers/hci-uart-core.md and drivers/hci-uart-h4.md (transport core + H:4/serdev framing), anchored by the Area G mini-scout below. Vendor UART protocol drivers (hci_bcm/hci_qca/hci_h5/hci_ll/hci_intel/…) remain out of scope. Catalog 71 → 73.
4. Boundary rule 14 rescope CONFIRMED: driver examples bind core↔driver-seam constructs; upper-layer pages state that the seam is at HCI and cite the driver pages rather than inventing examples.

Explicit go for page generation: NOT YET GIVEN (decision 1). The plan itself is approved.

## Inventory findings

(One compact digest per area, recorded verbatim from the inventory agents as each completes; line numbers are hints to re-verify at write time, never citations.)

### Area A: HCI core object & socket infrastructure — COMPLETE (recorded 2026-07-18)

#### 1. Core structs

- **`struct hci_dev`** — `include/net/bluetooth/hci_core.h:355-664`. The controller object. Field groups:
  - Identity/index: `list, srcu, lock, id, name, bus, bdaddr*, dev_name, short_name, eir` (355-379)
  - Capabilities/version: `features[3][8], le_features[248], le_states, commands[64], hci_ver/rev, lmp_ver/subver` (380-398)
  - BR/EDR+LE timing params (scan/adv/conn intervals, timeouts) (399-471)
  - Quirks/flags bitmaps: `quirk_flags` (`__HCI_NUM_QUIRKS`), `dev_flags` (`__HCI_NUM_FLAGS`), `conn_flags` (473, 590-591)
  - Counters/MTUs: `cmd_cnt` (atomic_t), `acl/sco/le/iso_cnt|mtu|pkts`, `*_last_tx` (475-492)
  - Async machinery: `workqueue, req_workqueue, power_on, power_off, error_reset, cmd_sync_work(+list+lock), unregister_lock, cmd_sync_cancel_work, discov_off, service_cache, cmd_timer, ncmd_timer, rx_work, cmd_work, tx_work, le_scan_disable` (497-522)
  - Queues/legacy req state: `rx_q, raw_q, cmd_q, sent_cmd, recv_event, req_lock, req_wait_q, req_status, req_result, req_skb, req_rsp` (524-536) — still used by hci_sync.c's blocking waiter
  - Discovery/suspend state: `discovery, suspend_notifier, suspend_state(_next), scanning_paused, suspended, wake_*` (541-554)
  - Object lists: `conn_hash, mgmt_pending(+lock), reject/accept_list, uuids, link_keys, long_term_keys, identity_resolving_keys, remote_oob_data, le_accept/resolv_list, le_conn_params, pend_le_*, blocked_keys, local_codecs` (556-574)
  - Sysfs/stats/refcount base: `stat, promisc, hw_info, fw_info, debugfs, dump, dev (embedded struct device — the kobject hci_dev_hold/put refcount on), rfkill` (576-588)
  - Advertising: `adv_data*, adv_instances(+cnt+cur+timeout+expire work), adv_monitors_idr(+cnt)` (593-608)
  - Privacy/mesh/interleave: `irk, rpa_timeout, rpa_expired, rpa, mesh_send_done, interleave_scan_state, interleave_scan, monitored_devices` (610-627)
  - Optional ext modules: `hci_drv, power_led, msft_*, aosp_*` (628-643)
  - **Driver callback vtable** (17 fns) (645-663) — see §2 "Driver seam" below.
- **`struct hci_conn`** — `hci_core.h:679-789`. Per-link object: dual refcounting (`atomic_t refcnt` for hold/drop + embedded `struct device dev` for get/put), state/type/role, timers (`disc_work, idle_work, auto_accept_work, le_conn_timeout`), `hdev` backpointer, `cleanup`/`*_cfm_cb` callbacks.
- **`struct hci_conn_hash`** — `hci_core.h:128-137`. Per-type link counters + RCU list head; mutated via `hci_conn_hash_add/del` (1014-1073, `list_add_tail_rcu`/`list_del_rcu`+`synchronize_rcu`).
- **`struct discovery_state`** — `hci_core.h:72-99`. Inquiry/LE-scan cache + its own `spinlock_t lock` (98) guarding `uuids`.
- **`struct hci_cb`** — `hci_core.h:2119-2130`. Global upper-layer callback record (connect/disconn/security/key_change/role_switch cfm), list = `hci_cb_list` + `hci_cb_list_lock` (hci_core.c:59-60).
- **`struct hci_mgmt_chan` / `hci_mgmt_handler`** — `hci_core.h:2364-2377`. mgmt-style channel registration record + per-opcode handler table; list = `mgmt_chan_list` (hci_sock.c:39-40).
- **`struct bt_sock`** — `bluetooth.h:398-405`. Common socket wrapper (`sock sk, accept_q, parent, flags, skb_msg_name/skb_put_cmsg`). `struct bt_sock_list` — `bluetooth.h:414-420` (hlist + rwlock + optional procfs seq_show).
- **`struct hci_pinfo`** — `hci_sock.c:51-61`. HCI-socket private data: `hdev, filter, cmsg_mask, channel, flags, cookie, comm, mtu`.
- **`struct hci_sec_filter`** — `hci_sock.c:134-159`. Default event/OGF/OCF allow-mask applied to unprivileged RAW sockets; bound by `HCI_SFLT_MAX_OGF=5` (132).
- **`struct sockaddr_hci`** — `hci_sock.h:37-41` (`hci_family, hci_dev, hci_channel`). `struct hci_filter`/`hci_ufilter` — `hci_sock.h:50-60`. Ioctl payload structs `hci_dev_info/_stats/_req/_list_req, hci_conn_info(_req), hci_auth_info_req, hci_inquiry_req` — `hci_sock.h:95-173`.

#### 2. API families (file:line, one-line role)

- **Alloc/register/teardown**: `hci_alloc_dev_priv` hci_core.c:2438 (alloc+init defaults+embedded work/queues); `hci_alloc_dev` hci_core.h:1761 (inline, priv=0); `hci_register_dev` hci_core.c:2585; `hci_unregister_dev` hci_core.c:2691; `hci_release_dev` hci_core.c:2744; `hci_free_dev` hci_core.c:2577 (just `put_device`).
- **Refcounting**: `hci_dev_hold/hci_dev_put` hci_core.h:1726/1718 (get_device/put_device on `hdev->dev`); `hci_conn_get/put` hci_core.h:1665/1671 (device refcount); `hci_conn_hold/drop` hci_core.h:1676/1686 (atomic_t refcnt, schedules `disc_work`).
- **Lookup/index**: `hci_dev_get`/`__hci_dev_get` hci_core.c:89/67 (walks `hci_dev_list` under `hci_dev_list_lock`); `hci_dev_get_srcu`/`hci_dev_put_srcu` hci_core.c:94/99 (SRCU-protected variant); `hci_get_route` (declared hci_core.h:1757).
- **Power/open-close**: `hci_dev_open`/`hci_dev_do_open` hci_core.c:439/423; `hci_dev_close`/`hci_dev_do_close` hci_core.c:509/494; `hci_power_on` hci_core.c:944; `hci_power_off` hci_core.c:1013; `hci_error_reset` hci_core.c:1023; `hci_dev_do_poweroff` hci_core.c:888; `hci_rfkill_set_block` hci_core.c:903 (rfkill → `hci_dev_do_poweroff`/`hci_dev_do_close`).
- **Suspend/resume/reset**: `hci_suspend_dev` hci_core.c:2831; `hci_resume_dev` hci_core.c:2862; `hci_reset_dev` hci_core.c:2890 (injects synthetic HW-error event); `hci_dev_reset`/`hci_dev_do_reset` hci_core.c:587/(≈540); `hci_register/unregister_suspend_notifier` hci_core.c:2781/2794.
- **RX/TX pumps**: `hci_recv_frame` hci_core.c:2918 (driver→core, queues `rx_q`+`rx_work`); `hci_recv_diag` hci_core.c:2976; `hci_rx_work` hci_core.c:4027; `hci_cmd_work` hci_core.c:4138; `hci_tx_work` hci_core.c:3806; `hci_send_frame` hci_core.c:3039 (core→driver, calls `hdev->send`, intercepts `HCI_DRV_PKT`); `hci_send_cmd`/`__hci_cmd_send` hci_core.c:3092/3116; `hci_send_acl/sco/iso` hci_core.c:3275/3287/3371.
- **Legacy request completion glue**: `hci_req_cmd_complete` hci_core.c:3960 (declared bluetooth.h:465); `hci_sent_cmd_data`/`hci_recv_event_data` hci_core.c:3164/3178; `hci_cmd_timeout`/`hci_ncmd_timeout` hci_core.c:1462/1485 (drive `cmd_timer`/`ncmd_timer`).
- **ioctl helpers**: `hci_get_dev_list/_info` hci_core.c:786/833; `hci_dev_cmd` hci_core.c:680; `hci_get_conn_list` (hci_core.c decl), `hci_get_conn_info/_auth_info` in `hci_conn.c:2730/2758`; `hci_inquiry` hci_core.c:326.
- **Sub-object families** (each: add/find/remove/clear, `hdev->lock`-protected list): link keys `hci_add/find/remove_link_key` hci_core.c:1276/1108/1375; LTKs `hci_add/find/remove_ltk` hci_core.c:1323/…/1391; IRKs `hci_add/find_irk_by_*/remove_irk` hci_core.c:1352/…/1410; OOB `hci_add/find/remove_remote_oob_data` hci_core.c:1545/1502/1518; adv instances `hci_add_adv_instance/hci_remove_adv_instance/hci_adv_instances_clear` hci_core.c:1702/1635/1672; adv monitors `hci_add_adv_monitor/hci_remove_(single|all)_adv_monitor/hci_adv_monitors_clear` hci_core.c:1921/2003/2014/1881; generic `bdaddr_list` `hci_bdaddr_list_add/del/clear(+_with_irk/_flags)` hci_core.c:2100/2175/2090; `hci_conn_params_add/del/lookup/clear_disabled` hci_core.c:2270/2316/…/2332.
- **Accessor macros**: `hci_dev_{set,clear,change,test,test_and_set,test_and_clear,test_and_change}_flag` hci_core.h:837-843 (dev_flags bitmap); `hci_{set,clear,test}_quirk` hci_core.h:666-668 (quirk_flags bitmap); `hci_dev_lock/unlock` hci_core.h:1735-1736 (`mutex_lock/unlock(&d->lock)`); `to_hci_dev`/`to_hci_conn` hci_core.h:1738-1739; `hci_get_priv/hci_get_drvdata/hci_set_drvdata` hci_core.h:1751/1741/1746; `SET_HCIDEV_DEV/GET_HCIDEV_DEV` hci_core.h:1923-1924; LMP/LE capability predicates hci_core.h:1927-2081 (e.g. `le_enabled`, `ll_privacy_capable`, `iso_capable`).
- **Bluetooth socket core (`af_bluetooth.c`)**: `bt_sock_register/unregister` :85/105 (fills `bt_proto[BTPROTO_*]`, rwlock `bt_proto_lock` :46); `bt_sock_create` :116 (`request_module("bt-proto-%d")` :128); `bt_sock_alloc` :146; `bt_sock_link/unlink/linked` :175/183/191; `bt_accept_enqueue/unlink/dequeue` :213/255/266; `bt_sock_recvmsg`/`bt_sock_stream_recvmsg` :323/414; `bt_sock_poll` :535; `bt_sock_ioctl` :656; `bt_sock_wait_state/_ready` :702/738; `bt_procfs_init/cleanup` :846/857; module entry `bt_init`/`bt_exit` :888/948 (registers PF_BLUETOOTH once, then `hci_sock_init`, `l2cap_init`, `sco_init`, `mgmt_init`).
- **`lib.c`**: `baswap` :42; `bt_to_errno`/`bt_status` :66/173 (BT error-code ⟷ errno mapping tables); `bt_info/warn/err/dbg(_ratelimited)` :246-383.
- **`hci_sysfs.c`**: `hci_init_sysfs`/`bt_host` type :117/111 (release → `hci_release_dev` or `kfree`); `hci_conn_init/add/del_sysfs` :24/37/52 (`bt_link` type, release → `kfree(conn)`); `reset` sysfs attribute :93-103 (calls `hdev->reset`); `bt_sysfs_init/cleanup` :128/133 (registers/unregisters class `"bluetooth"`).

#### 3. Lifecycle and locking

- **hci_dev alloc→free**: `hci_alloc_dev_priv` (kzalloc+`init_srcu_struct`, defaults, `INIT_WORK`/`INIT_DELAYED_WORK` for every work item, `hci_init_sysfs` device_initialize) → `hci_register_dev` (id via `ida_alloc_max(&hci_index_ida, HCI_MAX_ID-1,...)` hci_core.c:2592, alloc `workqueue`/`req_workqueue`, `device_add`, rfkill register, `list_add` into `hci_dev_list` under `hci_dev_list_lock`, queues `power_on`) → `hci_unregister_dev` (sets `HCI_UNREGISTER` under `unregister_lock`, `list_del`, `synchronize_srcu`+`cleanup_srcu_struct`, `disable_work_sync` on rx/cmd/tx/power_on/error_reset, `hci_dev_do_close`, `device_del`, final `hci_dev_put`) → device-model release (`bt_host_release` hci_sysfs.c:82) → `hci_release_dev` (frees all sub-lists, `ida_free(&hci_index_ida,...)`, `kfree(hdev)`). Anchors: hci_core.c:2438,2585,2691,2744; hci_sysfs.c:86-91.
- **Refcounting model**: `hci_dev` has **no separate atomic refcnt** — sole refcount is the embedded `struct device dev` kobject (`hci_dev_hold`/`hci_dev_put` = `get_device`/`put_device`, hci_core.h:1718-1733); numeric `id` is only returned to `hci_index_ida` at final `hci_release_dev`, not at unregister. `hci_conn` instead layers a hot-path `atomic_t refcnt` (hold/drop) on top of the same device-kobject scheme (get/put).
- **Index/id allocation**: global `hci_index_ida` (hci_core.c:63) bounded by `HCI_MAX_ID=10000` (hci_core.h:45); `hci_dev_list`+`hci_dev_list_lock` (rwlock_t, hci_core.c:55-56, extern hci_core.h:832-834) is the enumerable registry walked by `hci_dev_get`, `hci_get_dev_list`, `send_monitor_replay`.
- **Serializing locks**: `hdev->lock` (mutex, hci_core.h:358) via `hci_dev_lock/unlock` — guards mutable sub-lists (keys, adv instances/monitors, discovery, conn-param lists); `hdev->req_lock` (mutex, hci_core.h:531) via `hci_req_sync_lock/unlock` (hci_sync.h:15-16) — serializes one "synchronous request" (open/close/reset/suspend/resume/inquiry) at a time; `hdev->cmd_sync_work_lock`/`unregister_lock`/`mgmt_pending_lock` (hci_core.h:505,506,559) — narrow-purpose mutexes; `hci_dev_list_lock` (rwlock) and `hci_cb_list_lock` (mutex, hci_core.c:56/60) — global registries; `hci_sk_list.lock` (rwlock, hci_sock.c:161-163) and `bt_proto_lock` (rwlock, af_bluetooth.c:46) — socket-side registries; `discovery.lock` (spinlock_t, hci_core.h:98) — protects `discovery.uuids`.
- **State fields/transitions**: `hdev->flags` bits `HCI_UP/HCI_INIT/HCI_RUNNING/HCI_PSCAN/HCI_ISCAN/HCI_AUTH/HCI_ENCRYPT/HCI_INQUIRY/HCI_RAW/HCI_RESET` (hci.h:385-399) — set/cleared exclusively in `hci_sync.c` (`hci_dev_open_sync`/`close_sync`), only read (`test_bit`) in the files here (hci_core.c:596,951,2922). `hdev->dev_flags` bitmap `HCI_SETUP…HCI_MESH_SENDING`/`__HCI_NUM_FLAGS` (hci.h:420-480) drives the power/config state machine (`HCI_SETUP`→cleared+`mgmt_index_added` in `hci_power_on` hci_core.c:983-1010; `HCI_AUTO_OFF` grace period → `power_off` delayed work at `HCI_AUTO_OFF_TIMEOUT`; `HCI_UNREGISTER` gates teardown). Socket state: generic `enum bt_sock_state` `BT_CONNECTED..BT_CLOSED` (bluetooth.h:307-317); HCI sockets: `BT_OPEN`(alloc, af_bluetooth.c:161)→`BT_BOUND`(hci_sock.c:1483).
- **Async machinery**: `hdev->workqueue` (ordered, `WQ_HIGHPRI`, alloc hci_core.c:2605) runs `rx_work/cmd_work/tx_work`, `cmd_timer/ncmd_timer`, `disc_work`(hci_conn) — the data-path pump; `hdev->req_workqueue` (alloc hci_core.c:2611) runs `power_on` and the delayed `power_off`, plus is flushed by `hci_dev_open` (hci_core.c:475) to guarantee setup completion before re-open. `hci_cmd_sync_init/clear` (hci_sync.c, hooked hci_core.c:2554/2712) own `cmd_sync_work`+`cmd_sync_work_list` (deferred command batches) and `req_wait_q`/`req_status` (`HCI_REQ_DONE/PEND/CANCELED`, hci_sync.h:11-13) completion-style waiter reused from the old request API.

#### 4. Hard-coded limits

- `HCI_MAX_ID = 10000` — hci_core.h:45 (id-space bound, `ida_alloc_max`).
- `HCI_PRIO_MAX = 7` — hci_core.h:42.
- `HCI_MAX_PAGES = 3` — hci_core.h:353 (`features[3][8]`).
- `HCI_MAX_NAME_LENGTH = 248`, `HCI_MAX_SHORT_NAME_LENGTH = 10` — hci.h:1180, hci_core.h:336.
- `HCI_MAX_EIR_LENGTH = 240` — hci.h:1261.
- `HCI_MAX_AD_LENGTH = 31`, `HCI_MAX_EXT_AD_LENGTH = 251`, `HCI_MAX_PER_AD_LENGTH = 252`, `HCI_MAX_PER_AD_TOT_LEN = 1650` — hci.h:1672,2002,2037,2038.
- `HCI_LINK_KEY_SIZE = 16`, `HCI_MAX_ISO_BIS = 31` — hci.h:36,32.
- `HCI_MAX_ADV_INSTANCES = 5`, `HCI_MIN_ADV_MONITOR_HANDLE = 1`, `HCI_MAX_ADV_MONITOR_NUM_HANDLES = 32`, `HCI_MAX_ADV_MONITOR_NUM_PATTERNS = 16` — hci_core.h:279,330-332.
- `HCI_CONN_HANDLE_MAX = 0x0eff` — hci_core.h:338.
- Timeouts: `HCI_DISCONN_TIMEOUT=2s, HCI_PAIRING_TIMEOUT=60s, HCI_INIT_TIMEOUT=10s, HCI_CMD_TIMEOUT=2s, HCI_NCMD_TIMEOUT=4s, HCI_ACL_TX_TIMEOUT=45s, HCI_AUTO_OFF_TIMEOUT=2s, HCI_ACL/LE_CONN_TIMEOUT=20s` — hci.h:483-492.
- `HCI_MAX_ACL_SIZE=1024, HCI_MAX_SCO_SIZE=255, HCI_MAX_EVENT_SIZE=260, HCI_MAX_FRAME_SIZE=1028` — hci.h:29-34 (default HCI-socket `mtu`, hci_sock.c:1481).
- `BT_MAX_PROTO = BTPROTO_LAST+1 = 9` (`BTPROTO_L2CAP..BTPROTO_ISO`) — af_bluetooth.c:44, bluetooth.h:52-61.
- `HCI_SFLT_MAX_OGF = 5` — hci_sock.c:132 (RAW-socket default security filter bound).
- `HCI_FLT_TYPE_BITS=31, HCI_FLT_EVENT_BITS=63, HCI_FLT_OGF_BITS=63, HCI_FLT_OCF_BITS=127` — hci_sock.h:62-65.
- `HCI_CHANNEL_RAW/USER/MONITOR/CONTROL/LOGGING = 0..4` — hci_sock.h:44-48.
- `BT_SUBSYS_VERSION=2, BT_SUBSYS_REVISION=22` — bluetooth.h:34-35.

#### 5. Version-specific facts (verified in-tree)

- **`hci_request.c`/`.h` are gone.** No such files exist anywhere in the tree (`find` confirms); removed by commit `936daee9cf08 "Bluetooth: Remove hci_request.{c,h}"` (2024-07-15, first in v6.11-rc1). All request serialization now lives in `net/bluetooth/hci_sync.c` + `include/net/bluetooth/hci_sync.h`: `hci_req_sync_lock/unlock` are just `mutex_lock/unlock(&hdev->req_lock)` macros (hci_sync.h:15-16), and `hci_dev_open()/hci_dev_close()` in hci_core.c (439,509) are thin wrappers that take `req_lock` and call `hci_dev_open_sync`/`hci_dev_close_sync` (defined in hci_sync.c, not in this file set). All `HCI_DEV_{SETUP,OPEN,UP,CLOSE,DOWN}` monitor notifications (`hci_sock_dev_event`) now originate from `hci_sync.c` (grep hit lines ~5030-5415), whereas only `HCI_DEV_REG/UNREG/SUSPEND/RESUME` still fire from `hci_core.c` (2665,2730,2856,2884).
- **`le_features` grew from 8 to 248 bytes** (`hci_core.h:381,705`) to support "LE Read All Local Supported Features" (`HCI_OP_LE_READ_ALL_LOCAL_FEATURES=0x2087`, hci.h:2270) — added by commit `a106e50be74b "Bluetooth: HCI: Add support for LL Extended Feature Set"`, an ancestor of v6.19-rc1, i.e. very recent relative to older docs that describe an 8-byte LE-features page.
- **New "HCI Driver" protocol/channel**: `struct hci_dev.hci_drv` (hci_core.h:628), `HCI_DRV_PKT=0xf1` (hci.h:501), and interception in `hci_send_frame` (hci_core.c:3065-3072, calls `hci_drv_process_cmd`) plus `HCI_DRV_PKT` handling in `hci_send_to_sock`/`hci_sock_sendmsg` (hci_sock.c:238,1873) are new — `include/net/bluetooth/hci_drv.h` is Copyright 2025 Google, introduced by `04425292a62c "Bluetooth: Introduce HCI Driver protocol"` (2025-05-21, in v6.16). Not present in older widely-documented kernels.
- **`classify_pkt_type` callback** (hci_core.h:663, used hci_core.c:2909-2929) — added for vendor ISO/ACL packet-type disambiguation (`f25b7fd36cc3`, 2024-07-14, v6.11); absent from older struct-hci_dev references that list only `open/close/flush/setup/shutdown/send/notify/hw_error/post_init/set_diag/set_bdaddr/reset` (the pre-`wakeup`/`set_quality_report`/`get_data_path_id`/`get_codec_config_data` set some older docs still cite).
- **`hci_conn_hash` is RCU-protected** (`list_add_tail_rcu`/`list_del_rcu`+`synchronize_rcu`, hci_core.h:1014-1073; all lookups use `list_for_each_entry_rcu`), not a plain `hdev->lock`-only list as older documentation/tutorials often depict.
- The legacy `hdev->destruct` callback found in very old (~pre-2014) documentation does **not** exist in v7.0's `struct hci_dev` — device teardown is entirely device-model-driven via `bt_host_release` (hci_sysfs.c:82-91).

#### 6. Suggested documentation page topics

1. **"Anatomy of `struct hci_dev`"** — field-group tour anchored on hci_core.h:355-664; the natural index page for the whole area.
2. **"hci_dev lifecycle: alloc → register → power-on → unregister → release"** — `hci_alloc_dev_priv`, `hci_register_dev`, `hci_power_on/off`, `hci_unregister_dev`, `hci_release_dev`, `bt_host_release` (hci_core.c:2438,2585,944,1013,2691,2744; hci_sysfs.c:82).
3. **"The driver seam: 17 callbacks in `struct hci_dev`"** — full open/close/flush/setup/shutdown/send/notify/hw_error/post_init/set_diag/set_bdaddr/reset/wakeup/set_quality_report/get_data_path_id/get_codec_config_data/classify_pkt_type table (hci_core.h:645-663) with real call sites in hci_sync.c/hci_conn.c/mgmt.c/hci_debugfs.c.
4. **"Locks of the HCI core"** — `hdev->lock` vs `hdev->req_lock` vs `hci_dev_list_lock`/`hci_cb_list_lock` vs `hci_sk_list.lock`, why each exists and what it protects (hci_core.h:358,531,834-835; hci_sock.c:161-163).
5. **"Two workqueues, three work items: `workqueue` vs `req_workqueue`"** — rx_work/cmd_work/tx_work/timers vs power_on/power_off, plus why `hci_dev_open()` flushes `req_workqueue` (hci_core.h:497-522; hci_core.c:475,2605-2617).
6. **"Power state machine: HCI_UP, HCI_AUTO_OFF, rfkill"** — `hci_power_on/off`, `hci_rfkill_set_block`, the `dev_flags` bits (hci.h:420-480; hci_core.c:903-1021).
7. **"From `hci_request.c` to `hci_sync.c`"** — a migration-focused page explaining the removal (commit 936daee9cf08) and the new `req_lock`/`hci_cmd_sync_queue` model, for readers of older BlueZ/kernel internals write-ups.
8. **"Bluetooth socket family core"** — `bt_sock_register`, `BTPROTO_*`, `struct bt_sock`, the generic `bt_sock_*` helpers shared by L2CAP/RFCOMM/SCO/ISO/HCI (bluetooth.h:52-61,398-440; af_bluetooth.c:44-321).
9. **"HCI socket channels: RAW, USER, MONITOR, CONTROL, LOGGING"** — `hci_sock_bind` per-channel rules, `HCI_USER_CHANNEL` exclusivity via `hci_dev_test_and_set_flag` (hci_sock.c:1188-1477).
10. **"Inside the Bluetooth monitor protocol (btmon)"** — `create_monitor_event/_ctrl_open/_close/_command`, `hci_send_to_monitor`, `send_monitor_replay` (hci_sock.c:359-782).
11. **"HCI Driver protocol and HCI_DRV_PKT"** — the newest addition (2025), for currency (hci_drv.h; hci.h:501; hci_core.c:3065-3072).
### Area B: HCI connection & command/event machinery — COMPLETE (recorded 2026-07-18)

#### 1. Core structs

- `struct hci_conn` — include/net/bluetooth/hci_core.h:679 — the connection object: identity (dst/src/type/role/state/handle), features/PHY/LE-adv/ISO qos+bis[], security (key_type/sec_level/io_capability), timers (disc_timeout/conn_timeout/auth_payload_timeout), `flags` bitmap, `data_q`/`tx_q`/`chan_list`, 4 delayed_works, embedded `struct device dev` + `debugfs`, `hdev` back-ptr, `link_list`/`parent`/`link` (multi-link topology), `codec`, 3 cfm callback fn-ptrs, `cleanup()` vtable slot.
- `struct hci_conn_hash` — hci_core.h:128 — RCU list_head + live counters `acl_num/sco_num/cis_num/bis_num/pa_num/le_num/le_num_peripheral`; embedded in hci_dev at hci_core.h:556.
- `struct hci_dev` — hci_core.h:355 — adapter; groups relevant here: cmd/tx workqueues+works (`cmd_work/tx_work/rx_work/cmd_sync_work/cmd_sync_cancel_work/error_reset/power_on/power_off`), `cmd_q/raw_q/rx_q`, `sent_cmd/recv_event/req_skb/req_rsp`, `req_lock/req_wait_q/req_status/req_result`, `cmd_cnt` atomic + `acl_cnt/sco_cnt/le_cnt/iso_cnt` quotas + matching `*_pkts/*_mtu`, `cmd_timer/ncmd_timer`, `conn_hash`, `lock` mutex.
- `struct hci_chan` — hci_core.h:795 — per-L2CAP-channel TX queue muxed onto one hci_conn (`list/handle/conn/data_q/sent/state`).
- `struct hci_link` — hci_core.h:790 — list node binding a child conn (SCO/CIS/BIS) into a parent ACL/LE conn's `link_list`.
- `struct tx_queue` — hci_core.h:273 — completion-timestamp shadow queue (`queue/extra/tracked`), embedded as `conn->tx_q`.
- `struct hci_cb` — hci_core.h:2119 — global subscriber record (`connect_cfm/disconn_cfm/security_cfm/key_change_cfm/role_switch_cfm`) on `hci_cb_list`.
- `struct hci_ctrl` (aka `bt_cb(skb)->hci`) — include/net/bluetooth/bluetooth.h:475 — per-cmd-skb control block: `sk/opcode/req_flags(HCI_REQ_START,HCI_REQ_SKB)/req_event`, union `req_complete/req_complete_skb`; embedded in `struct bt_skb_cb` at bluetooth.h:491, `bt_cb()` macro at 505.
- `struct hci_request` — include/net/bluetooth/hci_sync.h:18 — vestigial one-shot `{hdev, cmd_q, err}`, used only inside hci_sync.c.
- `struct hci_cmd_sync_work_entry` — hci_sync.h:32 — queued cmd_sync item (`list/func/data/destroy`).
- Event/cmd dispatch descriptors (net/bluetooth/hci_event.c, all `static const`, X-macro built): `struct hci_ev{bool req; union{func,func_req}; min_len; max_len;}` :7601, table `hci_ev_table[U8_MAX+1]` :7613; `struct hci_cc{op,func,min_len,max_len}` :4077, table :4082; `struct hci_cs{op,func}` :4373, table :4376; `struct hci_le_ev{func,min_len,max_len}` :7363, table `hci_le_ev_table[U8_MAX+1]` :7367.

#### 2. API families

**Conn alloc/free**: `hci_conn_add`/`hci_conn_add_unset` hci_core.h:1576/1578, defs hci_conn.c:1093/1079 → `__hci_conn_add` (static) hci_conn.c:925 (real allocator); `hci_conn_del` hci_core.h:1580, def hci_conn.c:1170; `hci_conn_cleanup` (static) hci_conn.c:140; `hci_conn_unlink` (static) hci_conn.c:1128; `hci_conn_failed` hci_conn.c:1320 / `hci_le_conn_failed` (static) hci_conn.c:1307; `hci_conn_set_handle` hci_conn.c:1347.
**Refcounting (two independent axes)**: `hci_conn_get`/`hci_conn_put` hci_core.h:1665/1671 (struct device kobj — existence only); `hci_conn_hold`/`hci_conn_drop` hci_core.h:1676/1686 (atomic_t `refcnt` — usage count, arms `disc_work`); doc block at hci_core.h:1644-1663.
**hci_conn_hash family** (all `static inline`, hci_core.h): `hci_conn_hash_add`/`_del` :1014/:1043; `hci_conn_num` :1075, `hci_conn_count` :1097, `hci_iso_count` :1105; `hci_conn_valid` :1112; `hci_conn_lookup_type` :1130; lookup helpers `_lookup_bis` :1150, `_lookup_create_pa_sync` :1172, `_lookup_per_adv_bis` :1196, `_lookup_handle` :1222, `_lookup_ba` :1241, `_lookup_role` :1261, `_lookup_le` :1282, `_lookup_cis` :1306, `_lookup_cig` :1341, `_lookup_big` :1364, `_lookup_big_sync_pend` :1387, `_lookup_big_state` :1411, `_lookup_pa_sync_big_handle` :1435, `_lookup_pa_sync_handle` :1458; iterators `hci_conn_hash_list_state` :1488, `_list_flag` :1508; `hci_lookup_le_connect` :1528.
**hci_cmd_sync engine** (net/bluetooth/hci_sync.c): `hci_cmd_sync_alloc` :51; `hci_cmd_sync_add`(static):85, `hci_req_sync_run`(static):115, `hci_request_init`(static):148 (internal single-cmd builder); `__hci_cmd_sync_sk`:156/`__hci_cmd_sync`:220/`hci_cmd_sync`:228/`__hci_cmd_sync_ev`:247/`__hci_cmd_sync_status[_sk]`:256,284/`hci_cmd_sync_status`:292; `hci_cmd_sync_work`(static, the worker):305; `hci_cmd_sync_cancel_work`(static):342; `hci_cmd_sync_init`:626; `hci_cmd_sync_clear`:651; `hci_cmd_sync_cancel`:664 vs `hci_cmd_sync_cancel_sync`:682 (workqueue-deferred vs immediate/event-context cancel); `hci_cmd_sync_submit`:702, `hci_cmd_sync_queue`:739, `_queue_once`:779, `hci_cmd_sync_run`:794, `_run_once`:824, `hci_cmd_sync_lookup_entry`:839/`_hci_cmd_sync_lookup_entry`(static):752, `hci_cmd_sync_cancel_entry`:854, `hci_cmd_sync_dequeue_once`:867, `hci_cmd_sync_dequeue`:894.
**Legacy immediate path** (net/bluetooth/hci_core.c): `hci_send_cmd` :3092 (hci_core.h:2335); `__hci_cmd_send` :3116 (vendor-OGF unresponded only); `hci_cmd_data`(static):3148, `hci_sent_cmd_data`:3164, `hci_recv_event_data`:3178; `hci_req_is_complete`(static):3927, `hci_resend_last`(static):3938, `hci_req_cmd_complete`:3960; `hci_send_cmd_sync`(static):4102 (sets `sent_cmd`/clones into `req_skb`, calls `hdev->send`); `hci_cmd_work`(static):4138; `hci_cmd_timeout`(static):1462, `hci_ncmd_timeout`(static):1485; `handle_cmd_cnt_and_timer`(static) hci_event.c:3771; hardware-error: `hci_hardware_error_evt`(static) hci_event.c:4446 → `hci_error_reset`(static) hci_core.c:1023 → `hci_reset_dev` hci_core.c:2890.
**Event dispatch** (hci_event.c): `hci_event_packet`:7769 (top entry) → `hci_event_func`(static):7732 (table index+len-check+dispatch); `hci_cmd_complete_evt`(static):4273/`hci_cc_func`(static):4247 walk `hci_cc_table`; `hci_cmd_status_evt`(static):4404 walks `hci_cs_table`; `hci_le_meta_evt`(static):7458 walks `hci_le_ev_table`; `hci_get_cmd_complete`(static):7502.
**TX/flow control** (hci_core.c unless noted): `hci_tx_work`(static):3806; `hci_sched_acl`:3719/`_acl_pkt`:3677, `hci_sched_le`:3730, `hci_sched_sco`:3636, `hci_sched_iso`:3776; `hci_low_sent`(static):3422, `hci_chan_sent`(static):3486, `hci_quote_sent`(static inline):3385, `hci_prio_recalculate`(static):3549, `__check_timeout`/`hci_link_tx_to`(static):3599/3465; `hci_num_comp_pkts_evt`(static) hci_event.c:4481; `hci_chan_create`/`_del`/`_list_flush`/`__lookup_handle`/`lookup_handle` hci_conn.c:2778/2803/2823/2833/2846; `hci_conn_tx_queue`/`_tx_dequeue` hci_conn.c:3160/3223; `hci_send_conn_frame`(static):3084, `hci_send_frame`(static):3039.
**Callback semantics**: `struct hci_cb` list (`hci_cb_list`/`hci_cb_list_lock`, hci_core.c:59-60, extern'd hci_core.h:833/835), registered via `hci_register_cb` hci_core.c:3015 / `hci_unregister_cb` :3027; dispatchers `hci_connect_cfm`/`hci_disconn_cfm`/`hci_auth_cfm`/`hci_encrypt_cfm`/`hci_key_change_cfm`/`hci_role_switch_cfm` hci_core.h:2132/2147/2162/2183/2223/2235 — each walks the global list under `hci_cb_list_lock`, then invokes the single per-conn `conn->connect_cfm_cb`/`security_cfm_cb`/`disconn_cfm_cb` (fields at hci_core.h:783-785).

#### 3. Lifecycle & locking

- Alloc: `__hci_conn_add` (hci_conn.c:925) `kzalloc_obj`, `state=BT_OPEN`(:982), inits `disc_work→hci_conn_timeout`, `auto_accept_work→hci_conn_auto_accept`, `idle_work→hci_conn_idle`, `le_conn_timeout→le_conn_timeout` (all hci_conn.c:559-666), `refcnt=0`, `hci_dev_hold(hdev)`, `hci_conn_hash_add`, `hci_conn_init_sysfs` (hci_sysfs.c:24, out-of-scope file).
- Free: `hci_conn_del` (hci_conn.c:1170) → `hci_conn_unlink` → `disable_delayed_work_sync` on disc/auto_accept/idle works (:1178-1180, permanently disarms) → `hci_conn_hash_del` → per-type unacked-buffer credit restore → purge `data_q`/`tx_q` → `hci_conn_cleanup` (:140: flush link key/params, `hci_chan_list_flush`, `ida_free` handle, `conn->cleanup()` = `cis_cleanup`/`bis_cleanup`, `debugfs_remove_recursive`, `hci_conn_del_sysfs`, `hci_dev_put`) → `hci_cmd_sync_dequeue(hdev,NULL,conn,NULL)`.
- Timers on conn: `disc_work` (disc_timeout, doubled if `!conn->out`, hci_core.h:1698-1700) → `hci_conn_timeout`(hci_conn.c:559)→`hci_abort_conn`; `auto_accept_work`→`hci_conn_auto_accept`(:617) sends `HCI_OP_USER_CONFIRM_REPLY`; `idle_work`→`hci_conn_idle`(:583) triggers sniff mode; `le_conn_timeout`(HCI_LE_CONN_TIMEOUT)→`le_conn_timeout`(:643) aborts/disables adv.
- Locking: `hdev->lock` mutex via `hci_dev_lock`/`unlock` (hci_core.h:1735-1736) serializes conn_hash mutation + conn field writes from event-handler context; `hci_conn_hash.list` itself is lock-free RCU (`list_add_tail_rcu`/`list_del_rcu`+`synchronize_rcu`, hci_core.h:1017/1047-1048) so TX scheduler walks it without hdev->lock; `hdev->req_lock` via `hci_req_sync_lock`/`unlock` (hci_sync.h:15-16) serializes the whole sync-cmd machinery (one in-flight `__hci_cmd_sync`/`cmd_sync_work` per adapter); `hdev->cmd_sync_work_lock` mutex guards `cmd_sync_work_list`; `hdev->unregister_lock` guards submit-vs-teardown race (hci_sync.c:708).
- `conn->state` set (enum `bt_sock_state`, bluetooth.h:307-317, shared with sockets/L2CAP): `BT_CONNECTED=1, BT_OPEN, BT_BOUND, BT_LISTEN, BT_CONNECT, BT_CONNECT2, BT_CONFIG, BT_DISCONN, BT_CLOSED`. Grep-verified: hci_conn only ever uses **8** of these — `BT_DISCONN` is never assigned to `conn->state` in hci_conn.c/hci_event.c/hci_sync.c (only to socket/L2CAP-chan state in iso.c/l2cap_core.c).
- ACL transitions: alloc→`BT_OPEN`; `hci_connect_acl`/`hci_cs_create_conn`(hci_event.c:2248)→`BT_CONNECT`; `HCI_EV_CONN_REQUEST`→`hci_conn_request_evt`(:3271) incoming sets `BT_CONNECT`(:3348,3360) or defers to `BT_CONNECT2`(:3374); `HCI_EV_CONN_COMPLETE`→`hci_conn_complete_evt`(:3108) sets `BT_CONFIG`(:3188) then holds conn; auth/enc/features complete (`hci_auth_complete_evt`:3491→:3526, `hci_remote_features_evt`:3721→:3762, `hci_remote_ext_features_evt`:4945→:5001) finish →`BT_CONNECTED`; `HCI_EV_DISCONN_COMPLETE`→`hci_disconn_complete_evt`(:3399)→`BT_CLOSED`(:3422); failures via `hci_conn_failed`(hci_conn.c:1320)→`BT_CLOSED`.
- SCO/eSCO: `hci_add_sco`(hci_conn.c:200,:207)/`hci_setup_sync_conn`(:407,:415)/`hci_enhanced_setup_sync`(:281,:298) set `BT_CONNECT`; `HCI_EV_SYNC_CONN_COMPLETE`→`hci_sync_conn_complete_evt`(hci_event.c:5010) sets `BT_CONNECTED`(:5073) or `BT_CLOSED`(:5069,5097); command-status failure paths `hci_cs_create_conn`(:2267)/`hci_cs_add_sco`(:2310)→`BT_CLOSED`.
- LE: `hci_connect_le_scan`(hci_conn.c:1620,:1663)/`hci_connect_le`→`BT_CONNECT`; `HCI_EV_LE_CONN_COMPLETE`/`HCI_EV_LE_ENHANCED_CONN_COMPLETE`→shared `le_conn_complete_evt`(hci_event.c:5713)→`BT_CONFIG`(:5839; or direct `BT_CONNECTED`:5857 if feature read not needed); `hci_le_remote_feat_complete_evt`(:6641,:6686) and `hci_le_read_all_remote_features_evt`(:7289, sets :7337 via le_ev-table handler)→`BT_CONNECTED`; `hci_key_refresh_complete_evt`(:5196,:5230) also closes out `BT_CONFIG`→`BT_CONNECTED` for LE.
- ISO CIS: `hci_bind_cis`(hci_conn.c:1962,:2024→`BT_BOUND`), `hci_connect_cis`(:2349,:2390→`BT_CONNECT`), incoming `hci_le_cis_req_evt`(hci_event.c:7030,:7073→`BT_CONNECT2` when deferred); `HCI_EVT_LE_CIS_ESTABLISHED`→`hci_le_cis_established_evt`(:6911)→`BT_CONNECTED`(:6993) or `BT_CLOSED`+`hci_conn_del`(:7000); status failure `hci_cs_le_create_cis`(:4325,:4354)→`BT_CLOSED`.
- ISO BIG/BIS/PA: `hci_pa_create_sync`(hci_conn.c:2152,:2166→`BT_LISTEN`), `hci_bind_bis`(:2214,:2255→`BT_BOUND`; reuse path :2224/:2228→`BT_CONNECTED`); `hci_le_create_big_complete_evt`(hci_event.c:7089,:7118)/`hci_le_big_sync_established_evt`(:7137,:7196)→`BT_CONNECTED`; whole-hdev teardown `hci_conn_hash_flush`(hci_conn.c:2635,:2649)→`BT_CLOSED` for every conn.

#### 4. Hard-coded limits

- `HCI_CONN_HANDLE_MAX` 0x0eff — hci_core.h:338 (+`HCI_CONN_HANDLE_UNSET()` :339).
- `HCI_MAX_PAGES` 3 — hci_core.h:353 (bounds `features[][8]`).
- `HCI_MAX_SHORT_NAME_LENGTH` 10 — hci_core.h:336; `DEFAULT_AUTH_PAYLOAD_TIMEOUT` 0x0bb8 — hci_core.h:351; `HCI_DEFAULT_RPA_TIMEOUT` 15*60s — hci_core.h:345.
- `DISCOV_INTERLEAVED_INQUIRY_LEN` 0x04, `DISCOV_LE_TIMEOUT` 10240ms, `DISCOV_INTERLEAVED_TIMEOUT` 5120ms — hci_core.h:2411/2409/2410; `SUSPEND_NOTIFIER_TIMEOUT` 2s — hci_core.h:101.
- Timeouts, include/net/bluetooth/hci.h:483-492: `HCI_DISCONN_TIMEOUT` 2s, `HCI_PAIRING_TIMEOUT` 60s, `HCI_INIT_TIMEOUT` 10s, `HCI_CMD_TIMEOUT` 2s, `HCI_NCMD_TIMEOUT` 4s, `HCI_ACL_TX_TIMEOUT` 45s, `HCI_AUTO_OFF_TIMEOUT` 2s, `HCI_ACL_CONN_TIMEOUT` 20s, `HCI_LE_CONN_TIMEOUT` 20s, `HCI_ISO_TX_TIMEOUT` ~8.3886s.
- Packet/buffer sizes, hci.h:29-38: `HCI_MAX_ACL_SIZE` 1024, `HCI_MAX_SCO_SIZE` 255, `HCI_MAX_ISO_SIZE` 251, `HCI_MAX_ISO_BIS` 31, `HCI_MAX_EVENT_SIZE` 260 (event-table `max_len` bound), `HCI_MAX_FRAME_SIZE` = ACL+4, `HCI_MAX_CPB_DATA_SIZE` 252.
- AD/name/EIR sizes: `HCI_MAX_NAME_LENGTH` 248 (hci.h:1180), `HCI_MAX_EIR_LENGTH` 240 (:1261), `HCI_MAX_AD_LENGTH` 31 (:1672), `HCI_MAX_EXT_AD_LENGTH` 251 (:2002), `HCI_MAX_PER_AD_LENGTH` 252 (:2037), `HCI_MAX_PER_AD_TOT_LEN` 1650 (:2038).
- `ISO_MAX_NUM_BIS` 0x1f — include/net/bluetooth/iso.h:13 (checked in `hci_conn_big_create_sync`, hci_conn.c:2182).
- Invalid-value sentinels, hci.h:733-737: `HCI_TX_POWER_INVALID`/`HCI_RSSI_INVALID` 127, `HCI_SYNC_HANDLE_INVALID` 0xffff, `HCI_SID_INVALID` 0xff.
- HCI_REQ flags: `HCI_REQ_START` BIT(0), `HCI_REQ_SKB` BIT(1) — bluetooth.h:472-473; sync-req status codes `HCI_REQ_DONE`0/`HCI_REQ_PEND`1/`HCI_REQ_CANCELED`2 — hci_sync.h:11-13.

#### 5. Version-specific facts

- `hci_request.c`/`hci_request.h` are **fully removed** (commit `936daee9cf08` "Bluetooth: Remove hci_request.{c,h}", 2024-07-01, confirmed ancestor of v7.0); `find` for `hci_request*` under net/bluetooth returns nothing — the old async multi-command request-builder API (`hci_req_add()`, `hci_req_run()`) no longer exists anywhere in the tree.
- `struct hci_request` (hci_sync.h:18) survives only as a tiny internal single-shot skb-queue shim, used exclusively by three `static` functions in hci_sync.c (`hci_cmd_sync_add`:85, `hci_req_sync_run`:115, `hci_request_init`:148) to implement `__hci_cmd_sync_sk`; it is not the old builder.
- Remaining `hci_req_*` identifiers are semantically repurposed: `hci_req_sync_lock`/`unlock` macros (hci_sync.h:15-16) now guard the synchronous-cmd critical section, and `hci_req_complete_t`/`hci_req_complete_skb_t`/`hci_req_cmd_complete` (bluetooth.h:461-467, hci_core.c:3960) belong to the legacy-immediate-path completion plumbing, not a request builder.
- `msft_req_add_set_filter_enable` (net/bluetooth/msft.h:24 decl, :56 stub) still takes a `struct hci_request *req` but has **zero callers** anywhere in the tree — a dead vestige left behind by the hci_request.c deletion.
- Event/command dispatch is fully **table-driven** (`hci_ev_table`/`hci_cc_table`/`hci_cs_table`/`hci_le_ev_table`, X-macro builders `HCI_EV()`/`HCI_CC()`/`HCI_CS()`/`HCI_LE_EV()` with C99 designated initializers, hci_event.c:7571-7730 / 4063-4082 / 4367-4402 / 7345-7456) rather than a big `switch(event)`; `hci_event_func` (hci_event.c:7732) is just index+length-check+dispatch.
- `hci_conn_hash` traversal is lock-free **RCU** (`list_add_tail_rcu`/`list_del_rcu`+`synchronize_rcu`, hci_core.h:1017,1047-1048); all 15+ lookup helpers use `list_for_each_entry_rcu`.
- `disable_delayed_work_sync()`/`disable_work_sync()` (Linux 6.9+ workqueue API) are used in `hci_conn_del` (hci_conn.c:1178-1180) and hdev teardown (hci_core.c:2706-2710, 2818-2819) to *permanently* disarm per-conn/per-hdev delayed works — a stronger guarantee than the `cancel_delayed_work_sync()` pattern it complements, closing re-arm races.
- `hci_dev` carries a dedicated `srcu_struct` (`hdev->srcu`, init hci_core.c:2453, teardown :2703-2704) for SRCU-protected `hci_dev_get`-by-index lookups (`hci_dev_get_srcu`/`hci_dev_put_srcu`, hci_core.c:94-103) — a distinct RCU domain from the conn_hash one.
- The hold/drop-vs-get/put refcount split is explicitly documented in-tree (hci_core.h:1644-1663) including an acknowledged FIXME that the hold/drop count "is known to drop below 0 sometimes."
- `conn->debugfs` is touched in exactly two files subsystem-wide (hci_debugfs.c:1272 create, hci_conn.c:171 remove) — `hci_debugfs_create_conn` (hci_debugfs.c:1263) only creates an empty per-handle directory in this tree; no per-connection attribute files are registered under it in the searched scope.

#### 6. Suggested page topics

1. **struct hci_conn lifecycle** — `hci_conn_add`/`hci_conn_add_unset`/`__hci_conn_add`/`hci_conn_del`/`hci_conn_cleanup`/`hci_conn_failed`, the 4 per-conn delayed_works.
2. **hci_conn refcounting: hold/drop vs get/put** — `hci_conn_get/put/hold/drop`, hci_core.h:1644 doc comment, the disc_work re-arm on drop-to-zero.
3. **hci_conn_hash and connection lookup** — `hci_conn_hash_add/del`, the 15 `hci_conn_hash_lookup_*` helpers, RCU list semantics.
4. **The hci_conn state machine per link type** — `bt_sock_state` subset used by hci_conn, and the driving events/functions for ACL, SCO/eSCO, LE, CIS, BIG/BIS/PA enumerated in §3.
5. **hci_cmd_sync: the synchronous command engine** — queue/submit/run/dequeue family, `cmd_sync_work`, cancel vs cancel_sync, and its replacement of hci_request.c (removal commit `936daee9cf08`).
6. **Legacy immediate command path & hardware-error recovery** — `hci_send_cmd`/`cmd_work`/`sent_cmd`/`req_skb`, `cmd_timer`/`ncmd_timer`, `hci_hardware_error_evt`→`hci_error_reset`→`hci_reset_dev`.
7. **HCI event/command dispatch tables** — `hci_ev_table`/`hci_cc_table`/`hci_cs_table`/`hci_le_ev_table`, the `HCI_EV()`/`HCI_CC()`/`HCI_CS()`/`HCI_LE_EV()` macro family, `req_complete`/`req_complete_skb` plumbing.
8. **TX scheduling and flow control** — `hci_tx_work`, `hci_sched_{acl,sco,le,iso}`, `hci_chan_sent`/`hci_low_sent`/`hci_quote_sent`, quota fields, `hci_num_comp_pkts_evt`.
9. **hci_chan and per-channel priority scheduling** — `hci_chan_create/del/list_flush/lookup_handle`, `hci_prio_recalculate`, `skb->priority`.
10. **Connection confirmation callbacks** — `struct hci_cb`/`hci_register_cb`, the `hci_*_cfm` dispatchers, and the parallel per-conn `connect_cfm_cb/security_cfm_cb/disconn_cfm_cb` hooks.
11. **hci_conn locking model** — `hdev->lock` vs RCU conn_hash vs `req_lock`/`cmd_sync_work_lock`/`unregister_lock`.
12. **ISO topology: hci_link and parent/child conns** — `struct hci_link`, `conn->link_list/parent/link`, `hci_conn_link`, `hci_bind_cis`/`hci_bind_bis`/`hci_connect_cis`.
13. **hci_codec.c: local codec capability discovery** — `hci_read_supported_codecs[_v2]`, `hci_codec_list_add/clear`, `hdev->local_codecs`.
14. **hci_debugfs.c connection & adapter instrumentation** — `hci_debugfs_create_conn`, `conn_info_min_age/max_age`, the `DEFINE_DEBUGFS_ATTRIBUTE` knobs for LE conn params.
### Area C: LE advertising/scanning/connections/privacy + ISO/LE-Audio — COMPLETE (recorded 2026-07-18, after the plan review caught the omission; see Status CORRECTION)

#### 1. Core structs

- `struct adv_info` — include/net/bluetooth/hci_core.h:243-271 — one advertising-set node: enabled/pending/periodic flags, AD/SR/periodic-AD payloads (`adv_data`, `scan_rsp_data`, `per_adv_data`), timing (`timeout`/`duration`/`remaining_time`), RPA state (`random_addr`,`rpa_expired`,`rpa_expired_cb`).
- `struct adv_monitor` — hci_core.h:318-328 — one AdvMon: `patterns` list, embedded `adv_rssi_thresholds`, idr `handle`, state enum `NOT_REGISTERED/REGISTERED/OFFLOADED`.
- `struct adv_pattern` — hci_core.h:302-308 — one AD-type/offset/length/value node linked into `adv_monitor.patterns`.
- `struct adv_rssi_thresholds` — hci_core.h:310-316 — hi/lo RSSI thresholds+timeouts+sampling period, embedded in `adv_monitor`.
- `struct discovery_state` — hci_core.h:72-99 — discovery FSM (`state` enum below), inquiry cache lists (`all/unknown/resolve`), last-adv cache, RSSI/UUID filter fields, dynamic `uuids` array guarded by its own `spinlock_t lock`.
- `struct hci_conn_params` — hci_core.h:804-830 — per-peer LE params: `conn_min/max_interval`,`latency`,`supervision_timeout`, `auto_connect` FSM (enum below), back-pointer `conn`, `explicit_connect`, lock-free `flags`/`privacy_mode`.
- `struct bdaddr_list` / `_with_irk` / `_with_flags` — hci_core.h:139-178 — accept/resolve/reject-list nodes; three variants add IRK pair or `hci_conn_flags_t`.
- `struct hci_conn_hash` — hci_core.h:128-137 — per-hdev connection list + per-type/role live counters (`le_num`, `le_num_peripheral`, `cis_num`, `bis_num`, `pa_num`).
- `struct hci_conn` — hci_core.h:679-777 — connection object: `atomic_t refcnt`, state/type/role, LE timing fields, `iso_qos`+`num_bis`+`bis[]`, per-purpose delayed works (`disc_work`,`auto_accept_work`,`idle_work`,`le_conn_timeout`), `link`/`parent`/`link_list` (CIS↔ACL binding).
- `struct hci_link` — hci_core.h:790-793 — link_list node binding a child conn (e.g. CIS) to a `parent` hci_conn.
- `enum hci_conn_flags`/`hci_conn_flags_t` — hci_core.h:165-171 — `HCI_CONN_FLAG_{REMOTE_WAKEUP,DEVICE_PRIVACY,ADDRESS_RESOLUTION,PAST}`.
- `struct smp_irk` — hci_core.h:214-221 — IRK/identity record (`rpa`,`bdaddr`,`addr_type`,`val`) used by privacy resolution.
- `struct iso_conn` — net/bluetooth/iso.c:26-39 — ISO transport binder (`hcon`↔`sk`), own `spinlock_t lock`, `struct kref ref`, `timeout_work`.
- `struct iso_pinfo` — iso.c:60-76 — ISO socket private data: src/dst, `bc_sid`/`bc_num_bis`/`bc_bis[]`, `sync_handle`, `bt_iso_qos qos`, BASE buffer, back-pointer `conn`.
- `struct bt_iso_qos`/`bt_iso_ucast_qos`/`bt_iso_bcast_qos`/`bt_iso_io_qos` — include/net/bluetooth/bluetooth.h:181-222 — tagged-union CIG/CIS vs BIG/BIS QoS block (uapi, `setsockopt(BT_ISO_QOS)`).
- `struct iso_list_data` — net/bluetooth/hci_conn.c:668-678 — transient cig/big+cis/bis/sync_handle union used while walking `conn_hash` to size CIG/BIG.
- `struct conn_params` (hci_sync-local) — net/bluetooth/hci_sync.c:2360-2365 — lockless snapshot of `hci_conn_params` (addr/type/flags/privacy_mode) used to walk `pend_le_conns/reports` while issuing HCI commands.
- `struct msft_data` / `msft_monitor_advertisement_handle_data` / `msft_monitor_addr_filter_data` — net/bluetooth/msft.c:123-134 / 90-99 / 109-121 — MSFT vendor-extension state: handle map, address filters, resuming/suspending flags.
- `struct mgmt_pending_cmd` — net/bluetooth/mgmt_util.h:33-42 — generic async mgmt request tracker (opcode/hdev/param/sk/user_data) backing every async LE mgmt op.
- Advertising/discovery fields live in `struct hci_dev` — hci_core.h:355-664: `adv_instances`/`adv_instance_cnt`/`cur_adv_instance`/`adv_instance_timeout`/`adv_instance_expire` (601-605); `adv_monitors_idr`/`adv_monitors_cnt` (607-608); `irk`/`rpa_timeout`/`rpa_expired`/`rpa` (610-613); `interleave_scan_state` enum + `interleave_scan` work (617-623); `discovery` (541); `le_accept_list`/`le_resolv_list`/`le_conn_params`/`pend_le_conns`/`pend_le_reports` (568-572).

#### 2. API families (entry points, helpers, accessors)

**Adv-instance object lifecycle** (hci_core.c, "requires hdev->lock"): `hci_find_adv_instance`/`hci_find_adv_sid`/`hci_get_next_instance` — 1592/1605/1618; `hci_add_adv_instance`/`hci_add_per_instance`/`hci_set_adv_instance_data` — 1702/1769/1792; `hci_remove_adv_instance`/`hci_adv_instances_clear`/`hci_adv_instances_set_rpa_expired` — 1635/1672/1663; `hci_adv_instance_flags`/`hci_adv_instance_is_scannable` — 1827/1861.

**Adv-instance HCI programming & scheduling** (hci_sync.c): `hci_schedule_adv_instance_sync` — 1961 (legacy round-robin driver); `adv_timeout_expire`/`adv_timeout_expire_sync`/`cancel_adv_timeout` — 553/539/464; `hci_setup_ext_adv_instance_sync`/`hci_set_ext_adv_data_sync`/`hci_set_ext_scan_rsp_data_sync`/`hci_enable_ext_advertising_sync`/`hci_start_ext_adv_sync` — 1337/1264/1479/1549/1595; `hci_disable_ext_adv_instance_sync`/`hci_remove_ext_adv_instance_sync`/`hci_clear_adv_sets_sync`/`hci_clear_adv_sync`/`hci_remove_adv_sync`/`hci_remove_advertising_sync`/`hci_disable_advertising_sync` — 1159/1928/2017/2033/2064/2098/2167; `hci_pause_advertising_sync`/`hci_resume_advertising_sync` — 2534/2582; periodic-adv: `hci_set_per_adv_params_sync`/`hci_set_per_adv_data_sync`/`hci_enable_per_advertising_sync`/`hci_disable_per_advertising_sync`/`hci_start_per_adv_sync` — 1629/1651/1675/1610/1735.

**Advertisement monitor** (hci_core.c, idr-keyed, range `[HCI_MIN_ADV_MONITOR_HANDLE, +HCI_MAX_ADV_MONITOR_NUM_HANDLES)`): `hci_add_adv_monitor` (hdev->lock for idr_alloc only) — 1921; `hci_remove_single_adv_monitor`/`hci_remove_all_adv_monitor` (require hci_req_sync_lock) — 2005/2016; `hci_free_adv_monitor`/`hci_adv_monitors_clear` — 1895/1881; `hci_get_adv_monitor_offload_ext`/`hci_is_adv_monitoring` — 2041/2036. MSFT offload: `msft_add_monitor_pattern`/`msft_remove_monitor`/`msft_monitor_supported` — msft.c:1152/1166/136.

**Scanning/discovery** (hci_sync.c): `hci_passive_scan_sync` (background, accept-list driven) — 3047; `hci_update_passive_scan(_sync)` — 3263/3177; `hci_active_scan_sync`/`hci_start_discovery_sync`/`hci_start_interleaved_discovery_sync` — 5996/6080/6067; `hci_stop_discovery_sync`/`hci_pause_discovery_sync`/`hci_resume_discovery_sync` — 5512/6142/6302; `hci_start_scan_sync`/`hci_le_set_scan_param_sync`/`hci_le_set_ext_scan_param_sync`/`hci_le_set_scan_enable_sync`/`hci_le_set_ext_scan_enable_sync`/`hci_scan_disable_sync` — 3028/3006/2926/2199/2182/2232; accept-list: `hci_update_accept_list_sync`/`hci_le_add_accept_list_sync`/`hci_le_del_accept_list_sync`/`hci_le_clear_accept_list_sync` — 2753/2473/2329/2727; resolve-list & privacy mode: `hci_le_add_resolve_list_sync`/`hci_le_del_resolve_list_sync`/`hci_le_set_privacy_mode_sync`/`hci_le_set_addr_resolution_enable_sync` — 2370/2307/2433/2219; interleaving: `hci_start_interleave_scan`/`cancel_interleave_scan`/`hci_update_interleaved_scan_sync`/`interleave_scan_work` — 2259/2266/2278/586 (alternates `INTERLEAVE_SCAN_ALLOWLIST`↔`INTERLEAVE_SCAN_NO_FILTER` each call, 605-616).

**Discovery state machine** — `hci_discovery_active`/`hci_discovery_set_state` — net/bluetooth/hci_core.c:107/122 (`DISCOVERY_STOPPED→STARTING→FINDING/RESOLVING→STOPPING→STOPPED`; only STOPPED/FINDING transitions fire `mgmt_discovering`).

**LE connection establishment**: `hci_connect_le`/`hci_connect_le_scan`/`hci_explicit_conn_params_set` — hci_conn.c:1376/1620/1467 (explicit connect vs background-scan auto-connect); `hci_le_create_conn_sync`/`hci_le_ext_create_conn_sync`/`hci_le_directed_advertising_sync`/`hci_le_ext_directed_advertising_sync` — hci_sync.c:6581/6530/6461/6393; `hci_connect_le_sync`/`hci_cancel_connect_sync`/`hci_le_connect_cancel_sync` — hci_sync.c:7009/7018/5600; `hci_conn_params_add`/`_lookup`/`_del`/`_free`/`_clear_disabled`/`_clear_all` — hci_core.c:2270/2214/2316/2302/2332/2355; `hci_conn_params_set` (mgmt-only wrapper) — mgmt.c:5156; `hci_pend_le_list_add`/`_del_init`/`hci_pend_le_action_lookup` — hci_core.c:2263/2252/2231 (RCU list splice between `pend_le_conns`/`pend_le_reports`).

**Privacy/RPA**: `hci_update_random_address_sync`/`hci_get_random_address`/`hci_set_random_addr_sync` — hci_sync.c:1069/6824/1045; `rpa_valid()`/`adv_rpa_valid()` macros — hci_core.h:1971/1973; `rpa_expired` work fn (mgmt.c:1038) vs `adv_instance_rpa_expired` work fn (hci_core.c:1691) — per-hdev RPA vs per-instance RPA.

**Capability/accessor macros** — hci_core.h:1978-2064: `scan_1m/scan_2m/scan_coded`, `le_2m_capable/le_coded_capable`, `ll_privacy_capable`/`ll_privacy_enabled`, `privacy_mode_capable`, `use_ext_scan`/`use_ext_conn`, `ext_adv_capable`, `max_adv_len(dev)` (2026-2027, `ext_adv_capable ? HCI_MAX_EXT_AD_LENGTH : HCI_MAX_AD_LENGTH`), `use_enhanced_conn_complete`, `per_adv_capable`, `iso_capable/cis_capable/cis_central_capable/cis_peripheral_capable/bis_capable/sync_recv_capable/past_sender_capable/past_receiver_capable` — 2043-2064.

**EIR/AD builders** (eir.c/eir.h): `eir_create` — eir.c:175; `eir_create_adv_data`/`eir_create_scan_rsp`/`eir_create_per_adv_data` — eir.c:245/343/224; `eir_append_local_name`/`eir_append_appearance`/`eir_append_service_data` — eir.c:16/49/54; inline `eir_precalc_len`/`eir_append_data`/`eir_append_le16`/`eir_skb_put_data`/`eir_get_data` — eir.h:21/26/37/47/62; `eir_get_service_data` — eir.c:368.

**ISO socket layer** (iso.c): `iso_sock_create`/`iso_sock_bind`/`iso_sock_connect`/`iso_sock_listen`/`iso_sock_accept` — 944/1109/1166/1295/1340; `iso_sock_setsockopt`/`_getsockopt` — 1753/1852; `iso_sock_sendmsg`/`iso_send_frame`/`iso_recv_frame`/`iso_sock_recvmsg` — 1468/539/570/1597; `iso_connect_bis`/`iso_connect_cis` — 335/432; `check_ucast_qos`/`check_bcast_qos`/`check_io_qos` — 1680/1706/1662; `iso_conn_defer_accept` (issues `HCI_OP_LE_ACCEPT_CIS`) — 1550; `iso_conn_big_sync` — 1564.

**ISO HCI-facing (CIG/CIS)** (hci_conn.c/hci_sync.c): `hci_bind_cis`/`hci_connect_cis` — hci_conn.c:1962/2349; `hci_le_set_cig_params` (CIG/CIS auto-allocation, 0x00-0xef) — hci_conn.c:1901; `hci_le_create_cis_sync`/`hci_le_remove_cig_sync` — hci_sync.c:6694/6791; `hci_le_create_cis_pending`/`hci_conn_check_create_cis` — hci_conn.c:2078/2061; `cis_cleanup` (auto-removes CIG when last CIS drops) — hci_conn.c:894.

**ISO HCI-facing (BIG/BIS)**: `hci_bind_bis`/`hci_connect_bis` — hci_conn.c:2214/2298; `hci_conn_big_create_sync`/`hci_connect_big_sync` — hci_conn.c:2176 / hci_sync.c:7287; `hci_le_big_create_sync`/`hci_le_terminate_big_sync` — hci_sync.c:7242/6802; `hci_le_pa_create_sync`/`hci_connect_pa_sync`/`hci_le_pa_terminate_sync` — hci_sync.c:7119/7220/6813; `bis_cleanup` (broadcaster: removes adv+terminates BIG; receiver: terminates BIG/PA sync) — hci_conn.c:823.

**cmd_sync queue plumbing**: `hci_cmd_sync_queue`/`hci_cmd_sync_queue_once`/`hci_cmd_sync_submit`/`hci_cmd_sync_work` — hci_sync.c:739/779/702/305; `hci_req_sync_lock`/`_unlock` macros — include/net/bluetooth/hci_sync.h:15-16.

**mgmt LE-facing command surface** (mgmt.c, `mgmt_handlers[]` at 9344-9477): advertising: `set_advertising`/`add_advertising`/`add_ext_adv_params`/`add_ext_adv_data`/`remove_advertising`/`get_adv_size_info`/`read_adv_features` — 6524/8751/8944/9103/9260/9308/8515; adv-monitor: `read_adv_mon_features`/`add_adv_patterns_monitor(_rssi)`/`remove_adv_monitor` — 5305/5514,5551/5630; discovery: `start_discovery`/`start_service_discovery`/`start_limited_discovery`/`stop_discovery`/`set_scan_params` — 6069/6084/6076/6221/6653; privacy/keys: `set_privacy`/`load_irks` — 7110/7183; device/params: `add_device`/`remove_device`/`load_conn_param` — 7684/7812/7948; experimental-feature gated: `set_exp_feature` dispatch table `exp_features[]` (5034-5053) → `set_le_simultaneous_roles_func`/`set_iso_socket_func` — 4925/4984.

#### 3. Lifecycle & locking

- **adv_info**: alloc `kzalloc_obj(*adv)` in `hci_add_adv_instance` (hci_core.c:1721, caller holds `hdev->lock`); free via `hci_remove_adv_instance` (1635-1661, `kfree`+`cancel_delayed_work_sync(&adv->rpa_expired_cb)`) or bulk `hci_adv_instances_clear` (1672-1689, uses `disable_delayed_work_sync`). No refcount — ownership is the `hdev->adv_instances` list under `hdev->lock`.
- **Duration vs timeout semantics**: `adv->duration` = per-rotation slice (default `hdev->def_multi_adv_rotation_duration`=`HCI_DEFAULT_ADV_DURATION`=2s, hci_core.h:280, set at hci_core.c:1756-1759); `adv->timeout`/`remaining_time` = overall instance lifetime, decremented each scheduling round in `hci_schedule_adv_instance_sync` (hci_sync.c:1985-1994); legacy (non-ext) advertising arms `hdev->adv_instance_expire` delayed work (hci_sync.c:1997-2002) whose handler `adv_timeout_expire`→`adv_timeout_expire_sync` (hci_sync.c:553/539) calls `hci_clear_adv_instance_sync`. Extended-adv controllers instead pass per-set duration directly to `HCI_OP_LE_SET_EXT_ADV_ENABLE` (hci_sync.c:1582-1587) — controller owns rotation.
- **adv_monitor**: alloc `kzalloc_obj(*m)` in mgmt.c `add_adv_patterns_monitor(_rssi)` (5535/5572) before handle assignment; `hci_add_adv_monitor` (hci_dev_lock only around `idr_alloc`, hci_core.c:1929-1936) then dispatches to controller under `hci_req_sync_lock`; free in `hci_free_adv_monitor` (hci_core.c:1895, "requires hdev->lock") which also frees each `adv_pattern` node.
- **discovery_state**: single `state` field transitions driven exclusively through `hci_discovery_set_state` (hci_core.c:122); its dynamic `uuids` buffer is the only field with its own lock (`discovery.lock` spinlock, hci_core.h:98, taken in `hci_discovery_filter_clear` hci_core.h:918-929) — the rest of the struct is serialized by `hdev->lock`.
- **hci_conn_params**: alloc `kzalloc_obj(*params)` in `hci_conn_params_add` (hci_core.c:2279, "requires hdev->lock"); free in `hci_conn_params_free` (hci_core.c:2302) which first calls `hci_pend_le_list_del_init` then drops/puts any bound `hci_conn`. The `action` list membership (`pend_le_conns`/`pend_le_reports`) is RCU-protected independent of `hdev->lock`: `hci_pend_le_list_add` uses `list_add_rcu`, `hci_pend_le_list_del_init` uses `list_del_rcu`+`synchronize_rcu` (hci_core.c:2252-2267); `conn_params_copy` (hci_sync.c:2680) snapshots the list under `rcu_read_lock` before issuing blocking HCI commands.
- **auto_connect FSM** — enum at hci_core.h:816-823: `HCI_AUTO_CONN_DISABLED→REPORT→DIRECT→ALWAYS→LINK_LOSS→EXPLICIT`; transition logic centralized in `hci_conn_params_set` (mgmt.c:5156-5199, moves params between `pend_le_conns`/`pend_le_reports`/neither per new value).
- **hci_conn**: alloc in `__hci_conn_add` (hci_conn.c:925, `kzalloc_obj(*conn)`, `atomic_set(&conn->refcnt,0)`, `hci_dev_hold`, 4 `INIT_DELAYED_WORK`s); two independent refcounts — logical `hold()/drop()` via `atomic_t refcnt` (hci_core.h:1676/1686, drop-to-zero arms `disc_work` with `disc_timeout`) and existence `get()/put()` via embedded `struct device` (hci_core.h:1665/1671); full teardown `hci_conn_del` (hci_conn.c:1170) does `disable_delayed_work_sync` on `disc_work`/`auto_accept_work`/`idle_work`, `hci_conn_hash_del`, then `hci_conn_cleanup` (hci_conn.c:140, frees ida handle, calls `conn->cleanup()` — `cis_cleanup`/`bis_cleanup`).
- **CIS/BIG parent-child linking**: `hci_conn_link`/`hci_conn_unlink` (hci_conn.c:1728/1128) maintain RCU list `parent->link_list` of `struct hci_link` nodes; linking takes an extra `hci_conn_hold`+`hci_conn_get` on both ends, unlink does `synchronize_rcu` before dropping them.
- **iso_conn**: alloc `kzalloc_obj(*conn)` + `kref_init` in `iso_conn_add` (iso.c:200-229, reuses `hcon->iso_data` if a hold-able ref already exists via `iso_conn_hold_unless_zero`); freed via `kref_put(&conn->ref, iso_conn_free)` from `iso_conn_put` (iso.c:120/98) — `iso_conn_free` drops the `hcon` ref and does `disable_delayed_work_sync(&conn->timeout_work)`. `iso_conn.lock` spinlock serializes `sk`/`hcon` field swaps independent of `hci_dev`/socket locks.
- **ISO socket states**: `BT_OPEN→BT_BOUND→BT_CONNECT/BT_CONNECT2→BT_CONFIG→BT_CONNECTED→BT_DISCONN→BT_CLOSED` (bluetooth.h:308-316); `BT_SK_DEFER_SETUP`/`BT_SK_BIG_SYNC`/`BT_SK_PA_SYNC` bits (iso.c:55-58) gate whether `iso_sock_recvmsg` (iso.c:1611-1657) must first drive `iso_conn_defer_accept`, `iso_conn_big_sync`, or `iso_connect_cis` before user data flows — this is the userspace-visible "defer setup" half of CIS/BIG accept.
- **Serializing locks (global)**: `hdev->lock` (mutex) guards adv_instances/adv_monitors_idr/conn_hash/le_* lists (annotated per-function as "requires hdev->lock"); `hdev->req_lock` aliased `hci_req_sync_lock` (hci_sync.h:15) serializes one `hci_cmd_sync_work_entry` at a time off `hdev->cmd_sync_work_list` (itself protected by `hdev->cmd_sync_work_lock`) inside `hci_cmd_sync_work` (hci_sync.c:305-340) — this is the single point of serialization for *every* `*_sync` LE/adv/scan/ISO function in this digest; `hdev->mgmt_pending_lock` (mutex) guards `hdev->mgmt_pending` list (mgmt_util.c:260/300/316); `hdev->unregister_lock` gates new submissions vs `HCI_UNREGISTER` (hci_sync.c:709-715).
- **RPA rotation**: `hdev->rpa_expired` delayed work is only initialized in `mgmt_init_hdev` (mgmt.c:1147, gated on first `HCI_MGMT` use) with handler `rpa_expired` (mgmt.c:1038) that sets `HCI_RPA_EXPIRED` and re-queues `rpa_expired_sync`; per-instance `adv->rpa_expired_cb` is initialized unconditionally in `hci_add_adv_instance` (hci_core.c:1761) with in-kernel handler `adv_instance_rpa_expired` (hci_core.c:1691) — i.e. the *global* RPA-timeout mechanism is mgmt/userspace-wired while the *per-instance* one is pure kernel state.

#### 4. Hard-coded limits

- `HCI_MAX_ADV_INSTANCES` = 5 — hci_core.h:279 (legacy cap; ext-adv cap is `hdev->le_num_of_adv_sets`, read from controller).
- `HCI_DEFAULT_ADV_DURATION` = 2 (sec, legacy rotation slice) — hci_core.h:280.
- `HCI_MAX_EXT_AD_LENGTH` = 251, `HCI_MAX_AD_LENGTH` = 31, `HCI_MAX_PER_AD_LENGTH` = 252, `HCI_MAX_PER_AD_TOT_LEN` = 1650 — include/net/bluetooth/hci.h:2002/1672/2037/2038.
- `HCI_MAX_EIR_LENGTH` = 240, `HCI_MAX_NAME_LENGTH` = 248 — hci.h:1261/1180; `HCI_MAX_SHORT_NAME_LENGTH` = 10 — hci_core.h:336.
- `HCI_MIN_ADV_MONITOR_HANDLE` = 1, `HCI_MAX_ADV_MONITOR_NUM_HANDLES` = 32, `HCI_MAX_ADV_MONITOR_NUM_PATTERNS` = 16 — hci_core.h:330-332.
- `HCI_MAX_ISO_BIS` = 31 — hci.h:32; `ISO_MAX_NUM_BIS` = 0x1f (31) — include/net/bluetooth/iso.h:13; `ISO_DEFAULT_MTU` = 251 — iso.h:12.
- `BASE_MAX_LENGTH` = `HCI_MAX_PER_AD_LENGTH - EIR_SERVICE_DATA_LENGTH` = 252-4 = 248 — net/bluetooth/iso.c:50-51.
- `BT_ISO_QOS_{CIG,CIS,BIG,BIS}_UNSET` = 0xff each — include/net/bluetooth/bluetooth.h:173-177; `BT_ISO_SYNC_TIMEOUT` = 0x07d0 (20s) — bluetooth.h:179.
- CIG id range 0x00-0xef, CIS id range 0x00-0xef (0xf0 = allocation-exhausted sentinel) — hci_conn.c:1901-1960 (`hci_le_set_cig_params`).
- `ISO_CONN_TIMEOUT` = 20s, `ISO_DISCONN_TIMEOUT` = 2s — iso.c:95-96; `DEFAULT_IO_QOS` interval=10000us/latency=10ms/sdu=40/phys=2M/rtn=2 — iso.c:893-900.
- `HCI_DISCONN_TIMEOUT` = 2s, `HCI_LE_CONN_TIMEOUT` = 20s — hci.h:483/491.
- `HCI_DEFAULT_RPA_TIMEOUT` = 15*60s — hci_core.h:345.
- `HCI_CONN_HANDLE_MAX` = 0x0eff — hci_core.h:338.
- Scan-window/interval defaults — hci_core.h:2393-2419: `DISCOV_LE_SCAN_INT/WIN` 0x0012, `_FAST` 0x0060/0x0030, `_CONN` 0x0060/0x0060, `_SLOW1` 0x0800/0x0012, `_SLOW2` 0x1000/0x0024; `DISCOV_LE_TIMEOUT`=10240ms, `DISCOV_INTERLEAVED_TIMEOUT`=5120ms, `DISCOV_LE_RESTART_DELAY`=200ms, `DISCOV_LE_PER_ADV_INT_MIN/MAX`=0x00A0.
- `hdev->advmon_allowlist_duration`=300ms, `advmon_no_filter_duration`=500ms (interleave-scan cadence) — hci_core.c:2470-2471.
- Adv-monitor pattern bound check: `offset < HCI_MAX_AD_LENGTH`, `length <= HCI_MAX_AD_LENGTH` — mgmt.c:5493-5495 (`parse_adv_monitor_pattern`).

#### 5. Version-specific facts (verified in-tree)

- **`net/bluetooth/hci_request.{c,h}` no longer exist** — removed by commit `936daee9cf08` ("Bluetooth: Remove hci_request.{c,h}", 2024-07-01). All LE control flow (adv, scan, connect, CIS/BIG) now goes through `hci_sync.c`'s `hci_cmd_sync_queue`/`__hci_cmd_sync*` machinery — the older `hci_req_add`/`hci_req_run` API described in most pre-6.11 documentation is gone.
- **`kzalloc_obj`/`kzalloc_objs`/`kvzalloc_objs`/`kmalloc_flex`** (include/linux/slab.h:1035-1044) are brand-new: introduced by `2932ba8d9c99` ("slab: Introduce kmalloc_obj() and family", 2025-12-03) and Bluetooth was treewide-converted immediately before this tag by `69050f8d6d07` (2026-02-20) and `bf4afc53b77a`. Every alloc site cited above (`hci_add_adv_instance`, `hci_conn_params_add`, `__hci_conn_add`, `mgmt_pending_new`, `add_adv_patterns_monitor`, `iso_conn_add`, `hci_conn_link`) now reads `kzalloc_obj(*x)` instead of the `kzalloc(sizeof(*x), GFP_KERNEL)` shown in essentially all older documentation/tutorials.
- **`disable_delayed_work()`/`disable_delayed_work_sync()`** (workqueue API added by `86898fa6b8cd`, 2024-03-25) replace `cancel_delayed_work_sync` in teardown paths that must guarantee no re-arm: `hci_adv_instances_clear` (hci_core.c:1677,1682) and `hci_conn_del` (hci_conn.c:1180-1182), wired in by `989fa5171f00` ("Bluetooth: hci_core: Disable works on hci_unregister_dev", 2024-10-22); `iso_conn_free` (iso.c:113) does the same for `timeout_work`.
- **`iso_conn` refcounting switched to `struct kref`** — commit `dc26097bdb86` ("Bluetooth: ISO: Use kref to track lifetime of iso_conn", 2024-10-01); the original 2020 introduction of ISO sockets (`ccf74f2390d6`) had no refcount on `iso_conn` at all, so older ISO write-ups will not mention `iso_conn_hold_unless_zero`/`iso_conn_put`.
- **`hci_le_ev_table[]` function-table dispatch** for `HCI_EV_LE_META` subevents (hci_event.c:7363-7456) replaced the older per-subevent `switch` — commit `95118dd4edfe` (2021-12-01); still frequently absent from older public write-ups of `hci_event.c`.
- **ISO socket family is opt-in, not auto-registered**: `BTPROTO_ISO`/`iso_proto` are only wired up when userspace toggles the `iso_socket_uuid` feature via `MGMT_OP_SET_EXP_FEATURE` (`set_iso_socket_func`, mgmt.c:4984-5031 → `iso_init()`/`iso_exit()`, iso.c:2673/2716); the only unconditional caller of `iso_exit()` is module-exit cleanup in `af_bluetooth.c:950`. Any doc describing ISO sockets as always-on kernel functionality is wrong for this tree.
- `struct hci_conn.iso_qos`/`num_bis`/`bis[]` and `CIS_LINK`/`BIS_LINK`/`PA_LINK` connection types (hci_core.h:748-750) are ISO/LE-Audio additions layered onto the pre-existing `hci_conn` used since 2.6.12 (`atomic_t refcnt` itself is unchanged since then) — worth flagging that hci_conn keeps the old atomic refcount while the newer `iso_conn` object uses `kref`, an intentional inconsistency to note in docs.

#### 6. Suggested page topics

1. **"Advertising instance lifecycle"** — `struct adv_info`, `hci_add_adv_instance`/`hci_remove_adv_instance`/`hci_adv_instances_clear`, duration-vs-timeout semantics and `hdev->adv_instance_expire`/`adv_timeout_expire` — alloc/free, the software-rotation delayed work, the legacy-vs-extended split (`ext_adv_capable`).
2. **"Extended advertising HCI programming"** — `hci_setup_ext_adv_instance_sync`→`hci_set_ext_adv_data_sync`→`hci_enable_ext_advertising_sync` (`hci_start_ext_adv_sync`) chain, contrasted with legacy path; `MGMT_ADV_FLAG_*` → `eir_create_adv_data`.
3. **"Advertisement monitor (AdvMon) and MSFT offload"** — `struct adv_monitor`, its idr, add/remove, dispatch via `hci_get_adv_monitor_offload_ext` to software filtering or `msft_add_monitor_pattern`; tie into interleaved scanning as the software fallback.
4. **"Passive vs active scanning and the accept/resolve list dance"** — `hci_passive_scan_sync` vs `hci_active_scan_sync`, `hci_update_accept_list_sync`'s command sequence, resolve-list programming and privacy-mode setting, why advertising pauses (`hci_pause_advertising_sync`) during list reprogramming on LL-Privacy controllers.
5. **"Discovery state machine"** — `struct discovery_state`, `hci_discovery_set_state`'s five states and every call site, `DISCOV_TYPE_BREDR/LE/INTERLEAVED`, interleaved-inquiry timeout logic — a state-diagram candidate.
6. **"hci_conn_params and auto-connect"** — `struct hci_conn_params`, `pend_le_conns`/`pend_le_reports` RCU lists, `auto_connect` enum transitions from mgmt vs kernel-internal `hci_explicit_conn_params_set`; the mgmt-driven vs in-kernel boundary.
7. **"LE connection establishment"** — `hci_connect_le` (explicit) vs `hci_connect_le_scan` (background auto-connect) vs the `*_sync` HCI issuance, `le_conn_timeout`/`hci_conn_failed` cleanup.
8. **"RPA and LE privacy"** — `hci_update_random_address_sync`, `rpa_valid`/`adv_rpa_valid`, the two independent RPA-timeout delayed works (mgmt-wired global vs unconditional per-instance) — an explicit userspace-vs-kernel boundary page.
9. **"CIG/CIS setup for unicast LE-Audio"** — `hci_bind_cis`/`hci_connect_cis`, `hci_le_set_cig_params` auto-allocation, `hci_le_create_cis_sync`'s one-pending rule, established/req events, `cis_cleanup`.
10. **"BIG/BIS broadcast (broadcaster and receiver)"** — `hci_bind_bis`/`hci_connect_bis` vs PA-sync + BIG-sync receiver path, the create/established/lost events, `bis_cleanup`.
11. **"ISO socket layer and defer-setup"** — `struct iso_conn`/`iso_pinfo` lifecycle (kref), QoS validation, `BT_SK_DEFER_SETUP`/`BIG_SYNC`/`PA_SYNC` recvmsg-driven accept, the exp-feature opt-in gate.
12. **"EIR/AD helper library"** — eir.c/eir.h as the shared builder for classic EIR and LE AD/SR/periodic-AD.
13. **"cmd_sync queue and locking model"** — `hci_cmd_sync_work`/`hci_cmd_sync_submit`/`hci_req_sync_lock` as the single serialization point behind every `*_sync` function; a foundational page others link to instead of re-explaining locking.
### Area D: L2CAP, SCO, RFCOMM (+ SDP kernel touchpoint) — COMPLETE (recorded 2026-07-18)

File tags (paths relative to the tree root; the digest's original absolute-root note redacted per the portability rule):
**L2H**=include/net/bluetooth/l2cap.h · **L2C**=net/bluetooth/l2cap_core.c · **L2S**=net/bluetooth/l2cap_sock.c · **BTH**=include/net/bluetooth/bluetooth.h · **SCOC**=net/bluetooth/sco.c · **SCOH**=include/net/bluetooth/sco.h · **RFH**=include/net/bluetooth/rfcomm.h · **RFC**=net/bluetooth/rfcomm/core.c · **RFS**=net/bluetooth/rfcomm/sock.c · **RFT**=net/bluetooth/rfcomm/tty.c · **SMP**=net/bluetooth/smp.c (context only, supports fixed-channel findings)

#### 1. Core structs

- `struct l2cap_conn` L2H:643-676 — hcon/hchan pointers, mtu, feat_mask, local/remote_fixed_chan, info_state+info_ident+info_timer, rx reassembly (rx_skb/rx_len), tx_ida+tx_ident, pending_rx+pending_rx_work, id_addr_timer, chan_l list, lock (mutex), ref (kref), users list. Per-hci_conn L2CAP multiplexer context.
- `struct l2cap_chan` L2H:514-617 — identity (conn,kref,state,dst/src+types,psm,scid/dcid), MTU/mode/policy, conf_req[64]+conf_len+num_conf_req/rsp, ERTM tx/rx state+seq counters+srej/retrans lists, LE/ECRED credits+rx_avail, 4 delayed_work timers, tx_q/srej_q, list (per-conn) + global_l (global), ops+data, lock. One channel = one L2CAP endpoint in any mode.
- `struct l2cap_ops` L2H:619-641 — 14-callback vtable (new_connection, recv, teardown, close, state_change, ready, defer, resume, suspend, set_shutdown, get_sndtimeo, get_peer_pid, alloc_skb, filter); no-op stub impls at L2H:886-939.
- `struct l2cap_user` L2H:678-682 — probe/remove hooks external modules register on an l2cap_conn (list at conn->users).
- `struct l2cap_seq_list` L2H:504-509 — head/tail/mask + array, O(1) ordered set used for ERTM srej_list/retrans_list.
- `struct l2cap_pinfo` L2H:701-705 (used by L2S) — bt_sock + chan pointer + rx_busy list (ERTM/LE backpressure queue).
- `enum bt_sock_state` BTH:307-317 — shared BT_CONNECTED/OPEN/BOUND/LISTEN/CONNECT/CONNECT2/CONFIG/DISCONN/CLOSED used verbatim by l2cap_chan, rfcomm_dlc, rfcomm_session, sco sk.
- `struct l2cap_ctrl` BTH:443-457 — per-skb control-block (bt_cb(skb)->l2cap): sframe/poll/final/fcs/sar/super bits, reqseq/txseq, chan backpointer.
- `struct sco_conn` SCOC:45-55 — hcon, spinlock, sk, timeout_work (delayed_work), mtu, ref (kref). Per-hci_conn SCO/eSCO context, mirrors l2cap_conn but far simpler (single sk, no signaling).
- `struct sco_pinfo` SCOC:66-74 — bt_sock + src/dst + flags + setting (air-mode bits) + bt_codec + conn pointer.
- `struct rfcomm_session` RFH:154-167 — list, socket* (the underlying L2CAP socket), timer_list, state/flags (unsigned long, reuses BT_* enum), initiator, default cfc/mtu, dlcs list. Represents one RFCOMM multiplexer over one L2CAP channel.
- `struct rfcomm_dlc` RFH:169-200 — list, session backpointer, tx_queue, timer_list, lock(mutex), state/flags, refcnt (refcount_t), dlci/addr/priority/v24_sig, cfc/mtu/rx_credits/tx_credits, owner(void*), 3 callbacks (data_ready/state_change/modem_status). One RFCOMM logical channel (DLCI).
- `struct rfcomm_dev` RFT:45-69 — tty_port (embeds its own kref), list, name/id/flags/err/status, src/dst/channel, modem_status, dlc*, tty_dev, wmem_alloc, pending skb queue. TTY↔DLC binding object.
- `struct rfcomm_pinfo` RFH:303-311 — bt_sock + src/dst + dlc* + channel/sec_level/role_switch.

#### 2. API families

**L2CAP chan lifecycle** (L2C): l2cap_chan_create 441, l2cap_chan_destroy(kref release) 481, l2cap_chan_hold 494, l2cap_chan_hold_unless_zero 502, l2cap_chan_put 512, l2cap_chan_set_defaults 520, __l2cap_chan_add/l2cap_chan_add 587/640, l2cap_chan_del 647, l2cap_chan_close 809, l2cap_chan_connect 7075, l2cap_chan_send 2559, l2cap_chan_reconfigure 7275.
**L2CAP conn lifecycle** (L2C): l2cap_conn_add 6984, l2cap_conn_del 1764, l2cap_conn_free 1818, l2cap_conn_get/put 1826/1833, l2cap_conn_hold_unless_zero 7609, l2cap_conn_start 1518, l2cap_conn_ready 1627, l2cap_le_conn_ready 1594, l2cap_register_user/unregister_user 1702/1738.
**ERTM/streaming TX SM** (L2C): l2cap_tx 2929 (dispatch), l2cap_tx_state_xmit 2780, l2cap_tx_state_wait_f 2852, l2cap_ertm_send 1972, l2cap_ertm_resend 2039, l2cap_streaming_send 1936, l2cap_pass_to_tx/_fbit 2948/2955.
**ERTM RX SM** (L2C): l2cap_rx 6448 (dispatch, validates reqseq via __valid_reqseq 6439), l2cap_rx_state_recv 6062, l2cap_rx_state_srej_sent 6214, l2cap_rx_state_wait_p 6367, l2cap_rx_state_wait_f 6405, l2cap_classify_txseq 5976, l2cap_handle_rej/srej 5939/5881, l2cap_finish_move 6357, l2cap_stream_rx 6485 (streaming-mode path, bypasses SM).
**Timers** (L2C): l2cap_chan_timeout 405, l2cap_retrans_timeout 1916, l2cap_monitor_timeout 1895, l2cap_ack_timeout 3151, l2cap_info_timeout 1676, l2cap_conn_update_id_addr 739; helpers __set_retrans_timer 280, __set_monitor_timer 289, macros __set_chan_timer/__clear_*_timer L2H:865-871.
**Signaling dispatch/response-matching** (L2C): l2cap_recv_frame 6913 (CID switch), l2cap_sig_channel 5623 / l2cap_le_sig_channel 5574 (cmd-loop), l2cap_bredr_sig_cmd 4823 / l2cap_le_sig_cmd (grep — near 5509) (opcode switch), l2cap_get_ident 927 / l2cap_put_ident 4803 (ida-based), __l2cap_get_chan_by_ident 152 (ident-matched only for LE_CONN_RSP/reject), __l2cap_get_chan_by_scid/dcid 90/102 (scid/dcid-matched for everything else).
**LE credit-based (CoC)** (L2C): l2cap_le_connect 1282, l2cap_le_start 1383, l2cap_le_flowctl_init 563, l2cap_le_rx_credits 541, l2cap_le_flowctl_send 2518, l2cap_chan_le_send_credits 6630, l2cap_chan_rx_avail 6657, l2cap_le_connect_req 4884, l2cap_le_connect_rsp 4723, l2cap_le_credits(cmd) 5029.
**Enhanced credit-based (ECRED)** (L2C): l2cap_ecred_init 576, l2cap_ecred_connect 1350, l2cap_ecred_defer_connect 1318 (batches up to 5 chans under one ident), l2cap_ecred_conn_req(cmd) 5076, l2cap_ecred_conn_rsp(cmd) 5246, l2cap_ecred_reconf_req/rsp(cmd) 5356/5454, l2cap_ecred_reconfigure 7260, l2cap_chan_reconfigure 7275, l2cap_ecred_recv/data_rcv 6670/6691.
**Fixed channels** (L2C/L2S/SMP): l2cap_add_scid 227, l2cap_global_fixed_chan 7324 (walks global chan_list for BT_LISTEN+FIXED templates), l2cap_global_chan_by_psm 1844; smp_add_cid SMP:3285, smp_register/unregister SMP:3405/3455 (called from hci_sync.c:3542/5370).
**l2cap_sock glue** (L2S): l2cap_chan_ops table 1792 with 14 `*_cb` impls 1497-1790; l2cap_sock_ops (proto_ops) 1976; l2cap_proto 1913; l2cap_sock_create/alloc/init 1949/1919/1845.
**SCO** (SCOC): sco_conn_add 193, sco_conn_del 254, sco_conn_free 80/sco_conn_put 100/sco_conn_hold(_unless_zero) 110/118, sco_chan_add/__sco_chan_add 295/283, sco_chan_del 231, sco_connect 310, sco_conn_ready 1365 (accept path), sco_connect_ind 1426, sco_connect_cfm/sco_disconn_cfm 1453/1472 (hci_cb), sco_recv_scodata 1482→sco_recv_frame 410, sco_sock_setsockopt(BT_VOICE/BT_CODEC) 930.
**RFCOMM DLC** (RFC): rfcomm_dlc_alloc/free 303/323, __rfcomm_dlc_open/rfcomm_dlc_open 371/425, __rfcomm_dlc_close/rfcomm_dlc_close 451/503, rfcomm_dlc_accept 1320, rfcomm_dlc_send/_frag 571/556, rfcomm_dlc_hold/put RFH:249-258 (inline), rfcomm_dlc_link/unlink 331/341.
**RFCOMM session** (RFC): rfcomm_session_add/del/get/close/create 681/712/730/744/763, rfcomm_l2sock_create 197 (opens an in-kernel L2CAP SOCK_SEQPACKET socket to PSM 0x0003).
**RFCOMM MCC (control channel)** (RFC): rfcomm_recv_mcc 1645 (dispatch) + rfcomm_recv_pn/rpn/rls/msc 1432/1484/1590/1609; rfcomm_send_pn/rpn/rls/msc/fcoff/fcon/test/nsc/credits 954/996/1034/1061/1088/1110/1132/929/1164.
**RFCOMM kthread loop** (RFC): rfcomm_run 2114, rfcomm_schedule 106 (wake_up_all), rfcomm_process_sessions 2016, rfcomm_process_rx 1933, rfcomm_process_connect 1806, rfcomm_process_tx 1828, rfcomm_process_dlcs 1876, rfcomm_init 2214 (`kthread_run(rfcomm_run,...,"krfcommd")`).
**RFCOMM sock glue** (RFS): rfcomm_sk_data_ready/state_change 50/64, rfcomm_sock_alloc 271 (wires dlc callbacks), rfcomm_connect_ind 933.
**RFCOMM TTY/dev** (RFT): __rfcomm_dev_add/rfcomm_dev_add 217/318, __rfcomm_create_dev/__rfcomm_release_dev 391/437, rfcomm_dev_ioctl 573 (RFCOMMCREATEDEV/RELEASEDEV/GETDEVLIST/GETDEVINFO), rfcomm_dev_data_ready/state_change/modem_status 595/617/634, rfcomm_tty_install/open/close 700/738/764, tty_port_ops (rfcomm_port_ops) 141.

#### 3. Lifecycle & locking

- **l2cap_chan kref**: init `kref_init` L2C:470 in l2cap_chan_create; every hold via l2cap_chan_hold/hold_unless_zero (L2C:494/502) mirrors a real reference (global list membership, per-conn list membership, in-flight timer, socket pointer); l2cap_chan_put→l2cap_chan_destroy (L2C:481-492) unlinks from global `chan_list` and kfrees — no callback fires here (teardown/close already ran earlier in l2cap_chan_del/close).
- **l2cap_conn kref**: init L2C:7002 in l2cap_conn_add; l2cap_conn_del (L2C:1764) does the real teardown (cancels info_timer/id_addr_timer via `disable_delayed_work_sync`, purges pending_rx, `ida_destroy(tx_ida)`, kills every chan on chan_l, `hci_chan_del`, clears `hcon->l2cap_data`) then drops one ref; l2cap_conn_free (L2C:1818) does `hci_conn_put(conn->hcon)` + kfree — this is the conn↔hcon lifetime tie (conn holds one hci_conn ref for its whole life via `hci_conn_get` at L2C:7004).
- **Global vs per-conn chan lists**: EVERY l2cap_chan (raw/connless/CO/fixed) lives on `global_l`/`chan_list` (L2C:50-51, rwlock `chan_list_lock`) for its whole life (added in l2cap_chan_create L2C:459-461); only chans bound to a connection are additionally on `conn->chan_l` (`list` field, added in __l2cap_chan_add L2C:637). Global list backs PSM/CID lookup for listening sockets and fixed-channel templates (l2cap_global_chan_by_psm L2C:1844, l2cap_global_fixed_chan L2C:7324).
- **Locking order** (explicit in comment at L2S:1405): `hci_dev_lock(hdev)` → `mutex_lock(&conn->lock)` → `l2cap_chan_lock(chan)` (mutex, nested via `atomic_read(&chan->nesting)`, L2H:827-829). Nesting levels: NORMAL (default, L2C:454), PARENT (listening sockets, L2S:319 / 6lowpan.c:954), SMP (L2C via SMP:3260) — prevents lockdep false positives when a normal chan locks the SMP chan or a listening parent locks a child.
- **chan->state** transitions (BR/EDR CO, driven by signaling in L2C): BT_OPEN(create)→BT_BOUND(bind)→BT_CONNECT(l2cap_chan_connect 7075, sends CONN_REQ)→{BT_CONFIG (CONN_RSP success, l2cap_connect_create_rsp 4199) | BT_CONNECT2 (pending/responder, l2cap_connect 4083-4098)}→BT_CONNECTED (l2cap_chan_ready 1256, once both CONF_INPUT_DONE+CONF_OUTPUT_DONE)→BT_DISCONN (l2cap_send_disconn_req 1514)→BT_CLOSED (l2cap_chan_del via DISCONN_RSP/REQ, L2C:4513/4550). BT_LISTEN entered directly for listening sockets.
- **CONFIG substates** = `chan->conf_state` bits (enum L2H:707-720): CONF_REQ_SENT, CONF_INPUT_DONE, CONF_OUTPUT_DONE (gate BT_CONFIG→BT_CONNECTED, checked L2C:4333-4351/4463-4476), CONF_MTU_DONE/CONF_MODE_DONE (per-option completion), CONF_CONNECT_PEND, CONF_RECV_NO_FCS, CONF_EWS_RECV, CONF_LOC/REM_CONF_PEND (EFS "pending" handshake), CONF_NOT_COMPLETE (set at create L2C:473, cleared in l2cap_chan_ready L2C:1266, gates whether l2cap_chan_del does mode-specific cleanup L2C:675).
- **info-request state**: `conn->info_state` bits L2H:684-686 (CL_MTU_REQ_SENT unused/dead, FEAT_MASK_REQ_SENT, FEAT_MASK_REQ_DONE) + `conn->info_ident`+`info_timer` (delayed_work, L2CAP_INFO_TIMEOUT=4s). l2cap_request_info (L2C:1412) sends INFO_REQ(FEAT_MASK), schedules info_timer; l2cap_information_rsp (L2C:4608) matches by `cmd->ident==conn->info_ident` (conn-wide, not per-chan), chains a second INFO_REQ(FIXED_CHAN) if remote advertises L2CAP_FEAT_FIXED_CHAN, else marks DONE and calls l2cap_conn_start; l2cap_info_timeout (L2C:1676) force-marks DONE on timeout so connect isn't stuck forever.
- **id_addr_timer**: scheduled only from SMP:1072-1074 (`queue_delayed_work(hdev->workqueue,...,ID_ADDR_TIMEOUT)`) after identity-resolution completes on an LE link; handler l2cap_conn_update_id_addr (L2C:739) refreshes `chan->dst/dst_type` for every chan on the conn from `hcon->dst`.
- **sco_conn kref**: init SCOC:211 in sco_conn_add; sco_conn_free (SCOC:80) detaches `sco_pi(sk)->conn`, drops `hci_conn_drop`, then `disable_delayed_work_sync(&timeout_work)`. Per-socket teardown path is sco_chan_del (SCOC:231, must be called with sk locked) which just clears cross-pointers and puts the conn ref — no chan-level refcount, only conn is kref'd.
- **rfcomm_dlc refcount_t** (RFH:178, RFH:249-258 inline hold/put): held once per session membership (rfcomm_dlc_link RFC:331-339 / unlink RFC:341-353), once per owning socket (RFS:290-291) or tty dev (RFT:298 + destruct at RFT:87-93), once transiently by rfcomm_dlc_set_timer (RFC:272-278, mirrors l2cap's timer-hold pattern) — free happens in rfcomm_dlc_free (RFC:323, plain kfree, no dedicated destroy callback list).
- **rfcomm_dlc.state** transitions (BT_* enum reused): BT_OPEN(alloc/clear)→BT_CONFIG(__rfcomm_dlc_open RFC:405, PN negotiation)→BT_CONNECT (outgoing, RFC:1455, after PN acked)→BT_CONNECTED (SABM/UA exchange: rfcomm_recv_ua RFC:1221 outgoing accept / rfcomm_dlc_accept RFC:1332 incoming accept)→BT_DISCONN(__rfcomm_dlc_disconn RFC:441)→BT_CLOSED. BT_CONNECT2 is the "deferred accept" wait state (rfcomm_check_accept RFC:1350, RFCOMM_DEFER_SETUP flag).
- **rfcomm_session.state**: BT_BOUND(session_create, outgoing socket bound)→BT_CONNECT(L2CAP connected, rfcomm_check_connection RFC:2000, sends SABM dlci0)→BT_CONNECTED(UA on dlci0, rfcomm_recv_ua RFC:1244)→BT_DISCONN→BT_CLOSED(rfcomm_session_close RFC:744, cascades to close every dlc). BT_LISTEN/BT_OPEN used for the passive-listener and freshly-accepted-socket sessions respectively.
- **RFCOMM locking**: single global `rfcomm_mutex` (RFC:48-50) serializes `session_list`/`dlcs` membership and the kthread's whole processing pass; `rfcomm_dlc.lock` (mutex, `rfcomm_dlc_lock/unlock` RFH:246-247) only brackets state_change/data_ready/modem_status callback invocation, not the state machine itself (that runs already-serialized inside the kthread or under rfcomm_mutex from ioctl/socket paths).
- **rfcomm_dev refcounting**: no own kref — piggybacks on embedded `tty_port` kref (`tty_port_get/put`, e.g. RFT:167,331-334,368,452-471,693,732); one-shot release gated by `RFCOMM_DEV_RELEASED` bit in `dev->status` (RFT:457, test_and_set_bit in __rfcomm_release_dev).

#### 4. Hard-coded limits

- L2CAP: DEFAULT_MTU=672, DEFAULT_MIN_MTU=48, LE_MIN_MTU=23 — L2H:34-49. DEFAULT_TX_WINDOW=63, DEFAULT_EXT_WINDOW=0x3FFF(16383), DEFAULT_MAX_TX=3 — L2H:38-40. DEFAULT_RETRANS_TO=2000ms, DEFAULT_MONITOR_TO=12000ms, DEFAULT_ACK_TO=200ms — L2H:41-44,60. BREDR_MAX_PAYLOAD=1019 — L2H:48. ECRED_CONN_SCID_MAX=5 (L2H:50) / ECRED_MAX_CID=5 (L2H:463, duplicate constant) / ECRED_MIN_MTU=64 / ECRED_MIN_MPS=64 — L2H:461-463. conf_req buffer = 64 bytes (`chan->conf_req[64]`, L2H:541); CONF_MAX_CONF_REQ/RSP=2 — L2H:722-723; CONF_MAX_SIZE=22 — L2H:337. CID ranges: DYN_START=0x0040, LE_DYN_END=0x007f, DYN_END=0xffff — L2H:265-267. PSM ranges: LE_DYN_START/END=0x0080/0x00ff, DYN_START/END=0x1001/0xffff — L2H:252-256. LE_FLOWCTL_MAX_CREDITS=65535 — L2C:43.
- SCO: DEFAULT_MTU=500 — SCOH:29. CONN_TIMEOUT=40s, DISCONN_TIMEOUT=2s — SCOC:77-78.
- RFCOMM: CONN_TIMEOUT=30s, DISC_TIMEOUT=20s, AUTH_TIMEOUT=25s, IDLE_TIMEOUT=2s — RFH:29-32. DEFAULT_MTU=127, DEFAULT_CREDITS=7, MAX_CREDITS=40 (also = RFCOMM_CFC_ENABLED sentinel) — RFH:34-37,225. MAX_DEV=256 — RFH:320. Channel number valid range [1,30] — rfcomm_check_channel RFC:366-369. `sk_sndbuf/rcvbuf = RFCOMM_MAX_CREDITS*RFCOMM_DEFAULT_MTU*10` (=50800) — RFS:296-297. `rfcomm_room()` caps outstanding unsent packets at 40 — RFT:352-360.

#### 5. Version-specific facts (v7.0 vs older/widely-documented kernels)

- **A2MP/AMP fully removed**: no `a2mp.c`/`amp.c`/headers anywhere in tree; removed by commit `e7b02296fb40` "Bluetooth: Remove BT_HS" (first released in v6.10, well before v7.0). `CONFIG_BT_HS` absent from Kconfig entirely.
- L2CAP command-code list (L2H:99-118) has **no Create-Channel (0x0c/0x0d) or Move-Channel (0x0e-0x11) opcodes** — these AMP-only PDUs were deleted; `l2cap_bredr_sig_cmd` (L2C:4823) switch has no cases for them (would hit the "Unknown BR/EDR signaling command" default at L2C:4875).
- **Channel-move state machine is dead code**: `L2CAP_RX_STATE_WAIT_P`/`L2CAP_RX_STATE_WAIT_F` (L2H:768-774) and their handlers `l2cap_rx_state_wait_p`/`_wait_f` (L2C:6367/6405) remain, and `l2cap_rx()` (L2C:6448) still dispatches to them, but grepping every writer of `chan->rx_state` in L2C shows it is **never set** to WAIT_P/WAIT_F — only RECV and SREJ_SENT are reachable. `L2CAP_MOVE_ROLE_*`/`L2CAP_MOVE_*` enums (L2H:804-821) and `l2cap_move_chan_cfm(_rsp)` wire structs (L2H:404-414) are likewise unreferenced in L2C — pure vestige of the AMP era.
- `chan->chan_policy` / `BT_CHANNEL_POLICY` sockopt (BTH:93-118, L2S:637-640,1018) is stored/returned but has **no runtime effect** (its purpose — BR/EDR↔AMP channel migration — no longer exists).
- `L2CAP_MODE_RETRANS`(0x01)/`L2CAP_MODE_FLOWCTL`(0x02) (L2H:349-350, pre-ERTM Bluetooth 1.2 modes) are defined but **never referenced** in L2C/L2S — only BASIC/ERTM/STREAMING/LE_FLOWCTL/EXT_FLOWCTL are live.
- `l2cap_get_ident`/`l2cap_put_ident` use a per-conn **IDA** (`conn->tx_ida`, `ida_alloc_range`/`ida_free`, L2C:927,4803,7025) rather than a bare wrapping counter; `conn->tx_ident` is now just a "last-used" hint for the allocator's start point.
- `L2CAP_FC_ATT`(0x10)/`L2CAP_FC_SIG_LE`(0x20)/`L2CAP_FC_SMP_LE`(0x40) (L2H:139-141) are defined but **never OR'd into `conn->local_fixed_chan`** (only SIG_BREDR|CONNLESS, +SMP_BREDR conditionally, L2C:7012-7017) — the Fixed-Channels Information exchange is BR/EDR-signaling-only, so LE fixed channels are never advertised/negotiated this way.
- Enhanced Credit-Based Flow Control (ECRED, `L2CAP_MODE_EXT_FLOWCTL`, `L2CAP_ECRED_*`) is present and on by default (`enable_ecred = IS_ENABLED(CONFIG_BT_LE_L2CAP_ECRED)`, default `y`, L2C:46, Kconfig:73-80) — a Bluetooth 5.2-era feature, overridable via `bluetooth.enable_ecred=`.
- **RFCOMM is still kthread-based**, not workqueue-based: single `krfcommd` kthread (`kthread_run(rfcomm_run,...)`, RFC:2220) woken via `wake_up_all(&rfcomm_wq)`/`wait_woken` (RFC:106-108,2114-2136) — confirmed no workqueue conversion has landed through v7.0.
- **No SDP protocol in-kernel**: grep for "sdp" across net/bluetooth turns up only `L2CAP_PSM_SDP`(0x0001) used to relax default `sec_level` to `BT_SECURITY_SDP` (L2S:146-154, L2C:877-888,4032); there is no SDP PDU parser/struct anywhere — SDP is exclusively a normal dynamic L2CAP channel implemented in userspace (bluetoothd), exactly as expected.

#### 6. Suggested page topics

- **"l2cap_chan lifecycle & the global vs per-connection lists"** — anchors: l2cap_chan_create/destroy/hold/put (L2C:441-518), `chan_list`/`chan_list_lock` (L2C:50-51), `global_l` vs `list` fields (L2H:611-612).
- **"l2cap_conn and its hci_conn tether"** — l2cap_conn_add/del/free/get/put (L2C:6984,1764,1818,1826,1833), hci_conn_get/put pairing, info_state/info_timer machinery (L2C:1412,4608,1676).
- **"L2CAP BR/EDR channel state machine (BT_OPEN…BT_CLOSED + CONFIG substates)"** — l2cap_chan_connect/close/ready (L2C:7075,809,1256), l2cap_connect/l2cap_connect_create_rsp (L2C:4008,4149), l2cap_config_req/rsp (L2C:4266,4377), `conf_state` enum (L2H:707-720).
- **"l2cap_ops contract reference"** — struct + all 14 callbacks (L2H:619-641), invocation sites via `chan->ops->*` in L2C (grep list gathered), l2cap_chan_ops impl in L2S:1792-1808 as the canonical example.
- **"ERTM tx/rx state machines"** — l2cap_tx/_state_xmit/_wait_f (L2C:2929,2780,2852), l2cap_rx/_state_recv/srej_sent/wait_p/wait_f (L2C:6448,6062,6214,6367,6405), retrans/monitor/ack timers (L2C:1916,1895,3151), seq-list bookkeeping (L2C:298-405).
- **"LE Credit-Based and Enhanced Credit-Based (ECRED) Connection-Oriented Channels"** — l2cap_le_connect/_credits (L2C:1282,5029), l2cap_ecred_connect/conn_req/reconfigure (L2C:1350,5076,7260), credit accounting (L2C:541,2518,6630).
- **"L2CAP signaling command dispatch and ident allocation"** — l2cap_recv_frame/sig_channel/bredr_sig_cmd (L2C:6913,5623,4823), ida-based idents (L2C:927,4803), response-matching by scid/dcid vs ident (L2C:90-162).
- **"Fixed channels in Linux BT: what's actually wired up"** — CID list (L2H:259-267), SMP root/per-conn chans (SMP:3220-3450), l2cap_global_fixed_chan (L2C:7324), ATT/6LoWPAN as ordinary sockets not kernel fixed chans (L2S:106-112,226-245).
- **"l2cap_sock: proto_ops/l2cap_ops glue"** — l2cap_sock_ops/l2cap_proto/l2cap_chan_ops (L2S:1976,1913,1792), per-callback bodies (L2S:1497-1790), BT_MODE mapping (L2S:417,840).
- **"SCO/eSCO connection setup, accept, and codec/air-mode selection"** — sco_connect/sco_conn_ready/connect_ind/cfm (SCOC:310,1365,1426,1453), BT_VOICE/BT_CODEC setsockopt (SCOC:930-1056), sco_conn kref (SCOC:80-129).
- **"RFCOMM session & DLC state machines"** — full BT_* transition tables in RFC (rfcomm_recv_ua/dm/disc/sabm, RFC:1204-1401), rfcomm_dlc refcount_t (RFH:178,249-258).
- **"RFCOMM krfcommd processing model and credit-based flow control"** — rfcomm_run/process_* (RFC:2114-1957), PN/credits negotiation (RFC:1403-1484,1828-1874), RFCOMM_CFC_* states (RFH:222-225).
- **"RFCOMM multiplexer control channel (MCC)"** — rfcomm_recv_mcc dispatch + all RFCOMM_PN/RPN/RLS/MSC/FC*/TEST/NSC handlers (RFC:1645-1736).
- **"rfcomm_dev / TTY binding lifecycle"** — rfcomm_dev_add/__rfcomm_release_dev (RFT:318,437), tty_port-based refcounting (RFT:80-107,159-173), RFCOMMCREATEDEV/RELEASEDEV ioctls (RFT:573-592).
- **"Locking hierarchy across the Bluetooth data plane"** — hci_dev_lock→conn->lock→chan->lock order (L2C:7090-7212, comment at L2S:1404-1406), lock-nesting levels (L2H:757-761, set at L2C:454, L2S:319, SMP:3260/3357), rfcomm_mutex vs dlc->lock (RFC:48-50, RFH:246-247).
- **"Dead/vestigial code from the AMP era"** — a documentation-hygiene page: BT_HS removal commit, unreachable WAIT_P/WAIT_F rx-states, unused L2CAP_MOVE_* enums/structs, inert chan_policy field — anchors as listed in section 5.
### Area E: mgmt framework + SMP and key management — COMPLETE (recorded 2026-07-18)

#### 1. Core structs

- `struct hci_mgmt_chan` — include/net/bluetooth/hci_core.h:2371-2377 — registration record for an mgmt-style ioctl channel: list linkage, channel#, handler table+count, optional per-hdev init hook.
- `struct hci_mgmt_handler` — hci_core.h:2364-2369 — one opcode's `{func, data_len, flags}`; flags are the `HCI_MGMT_*` bits.
- `struct mgmt_pending_cmd` — net/bluetooth/mgmt_util.h:33-43 — queued async mgmt command: list, opcode, hdev, param/param_len (kmemdup'd copy of the request), sk, skb, `user_data` (opaque, e.g. `hci_conn*`), `cmd_complete` fn ptr. No refcount field.
- `struct mgmt_mesh_tx` — mgmt_util.h:23-31 — queued Mesh `mesh_send` tx awaiting HCI completion; `param[]` sized `sizeof(mgmt_cp_mesh_send)+31`.
- `struct smp_chan` — net/bluetooth/smp.c:96-132 — per-`l2cap_conn` SMP session: preq/prsp/prnd/rrnd/pcnf/tk/rr/lr byte buffers, enc_key_size, remote_key_dist, id_addr(+type), irk, csrk/responder_csrk/ltk/responder_ltk/remote_irk pointers, link_key, `flags` (SMP_FLAG_*), method, passkey_round, SC fields (local_pk/remote_pk/dhkey/mackey), tfm_cmac/tfm_ecdh.
- `struct smp_dev` — smp.c:85-94 — per-hdev SMP **root** channel data (OOB/ECDH cache): local_oob, local_pk, local_rand, debug_key, tfm_cmac/tfm_ecdh. Backs `hdev->smp_data`/`smp_bredr_data`.
- `struct link_key` — hci_core.h:223-230 — persisted BR/EDR key: list+rcu, bdaddr, type (`HCI_LK_*`), val[`HCI_LINK_KEY_SIZE`], pin_len. Lives on `hdev->link_keys`.
- `struct smp_ltk` — hci_core.h:201-212 — persisted LE long-term key: bdaddr/type, authenticated, type (`SMP_STK`/`SMP_LTK`/`SMP_LTK_RESPONDER`/`SMP_LTK_P256`/`SMP_LTK_P256_DEBUG`), enc_size, ediv, rand, val[16]. Lives on `hdev->long_term_keys`.
- `struct smp_irk` — hci_core.h:214-221 — identity resolving key: rpa, bdaddr, addr_type, val[16]. Lives on `hdev->identity_resolving_keys`.
- `struct smp_csrk` — hci_core.h:194-199 — ATT signing key: bdaddr/type, type (`MGMT_CSRK_*`), val[16]. **No hdev list exists for this type** (see §5).
- `struct blocked_key` — hci_core.h:187-192 — denylisted key value: list+rcu, type (`HCI_BLOCKED_KEY_TYPE_*`), val[16]. Lives on `hdev->blocked_keys`.
- `struct oob_data` — hci_core.h:232-239(ish) — cached remote OOB data: bdaddr/type, present, hash192/rand192/hash256/rand256. Lives on `hdev->remote_oob_data`.
- `struct cmd_lookup` — net/bluetooth/mgmt.c:1460-1464 — `{sk, hdev, mgmt_status}` accumulator threaded through `mgmt_pending_foreach()` callbacks (`settings_rsp`, `cmd_complete_rsp`).
- `struct hci_conn` (security-relevant fields only) — hci_core.h:679-788 — `sec_level`/`pending_sec_level` (:710-711), `auth_type`, `io_capability`, `passkey_notify`/`passkey_entered`, `remote_cap`/`remote_auth`, `flags` (HCI_CONN_* bits), `connect_cfm_cb`/`security_cfm_cb`/`disconn_cfm_cb`, atomic `refcnt`.

#### 2. API families

**A. Channel registration/dispatch (hci_sock.c)**
- `hci_mgmt_chan_register()`/`unregister()` — hci_sock.c:874-890 / 893-898 — add/remove a `hci_mgmt_chan` on the global `mgmt_chan_list`; rejects `channel < HCI_CHANNEL_CONTROL`. Both `EXPORT_SYMBOL`.
- `__hci_mgmt_chan_find()` / `hci_mgmt_chan_find()` — hci_sock.c:851-861 / 863-872 — linear list scan by channel id (unlocked/locked variants).
- `hci_mgmt_cmd()` — hci_sock.c:1619-1732 — validates `mgmt_hdr`, opcode range, `HCI_MGMT_UNTRUSTED`, hdev resolution vs `HCI_MGMT_NO_HDEV/UNCONFIGURED/HDEV_OPTIONAL`, `HCI_MGMT_VAR_LEN` length check, calls `handler->func`, mirrors the raw command to `HCI_CHANNEL_MONITOR`.
- `hci_sock_sendmsg()` — hci_sock.c:1800-1846 — dispatch switch on `hci_pi(sk)->channel`: RAW/USER → HCI path; MONITOR → rejected; LOGGING → `hci_logging_frame`; default → `__hci_mgmt_chan_find` + `hci_mgmt_cmd` under `mgmt_chan_list_lock`.

**B. mgmt_handlers table (mgmt.c)**
- `mgmt_handlers[]` — mgmt.c:9344-9477 — **92 array slots**: index 0 = `{NULL}` placeholder (opcode 0x0000), then `MGMT_OP_READ_VERSION` 0x0001 … `MGMT_OP_HCI_CMD_SYNC` 0x005B ⇒ **91 real commands**.
- Flag usage in the table: `HCI_MGMT_VAR_LEN` ×18, `HCI_MGMT_UNTRUSTED` ×12, `HCI_MGMT_NO_HDEV` ×5, `HCI_MGMT_UNCONFIGURED` ×3, `HCI_MGMT_HDEV_OPTIONAL` ×2 (the last two gate `read_exp_features_info`/`set_exp_feature`).
- `static struct hci_mgmt_chan chan` — mgmt.c:9596-9601 — the sole registrant: `channel=HCI_CHANNEL_CONTROL`, `handlers=mgmt_handlers`, `hdev_init=mgmt_init_hdev`.
- `mgmt_init()`/`mgmt_exit()` — mgmt.c:9603-9611 — call `hci_mgmt_chan_register/unregister(&chan)`.
- `mgmt_init_hdev()` — mgmt.c:1138-1158 — `hdev_init` callback: arms `discov_off`/`service_cache`/`rpa_expired`/`mesh_send_done` delayed work, clears `HCI_BONDABLE` (must be opted in via mgmt), sets `HCI_MGMT`.

**C. mgmt_pending_cmd lifecycle (mgmt_util.c)**
- `mgmt_pending_new()` — mgmt_util.c:263-288 — `kzalloc_obj` + `kmemdup(param)` + `sock_hold(sk)`; not yet linked into any list.
- `mgmt_pending_add()` — mgmt_util.c:290-305 — `new()` + `list_add_tail` under `hdev->mgmt_pending_lock`.
- `mgmt_pending_find()` — mgmt_util.c:217-237 — scan by `(channel via hci_sock_get_channel(cmd->sk), opcode)`.
- `mgmt_pending_foreach()` — mgmt_util.c:239-261 — walk filtered by opcode (0 = all), optional remove+free per entry via callback; used to mass-complete on power-off/index-removed.
- `mgmt_pending_remove()`/`mgmt_pending_free()` — mgmt_util.c:314-321 / 307-312 — `list_del` + `sock_put(sk)` + `kfree(param)` + `kfree(cmd)`.
- `mgmt_pending_listed()`/`__mgmt_pending_listed()`/`mgmt_pending_valid()` — mgmt_util.c:323-338 / 340-349 / 351-367 — membership checks; `valid()` atomically removes-if-still-listed (defends against stale `cmd` pointers).

**D. Event emission helpers**
- `mgmt_alloc_skb()`/`mgmt_send_event_skb()`/`mgmt_send_event()` — mgmt_util.c:59-73 / 75-109 / 111-124 — build `mgmt_hdr`+payload skb, mirror to `HCI_CHANNEL_MONITOR`, `hci_send_to_channel()`.
- `mgmt_event()`/`mgmt_index_event()`/`mgmt_limited_event()`/`mgmt_event_skb()` — mgmt.c:337-342 / 323-328 / 330-335 / 344-347 — thin wrappers fixing `channel=HCI_CHANNEL_CONTROL` + a flag (`HCI_SOCK_TRUSTED` or a feature-class bit) + optional `skip_sk`.
- `mgmt_cmd_status()`/`mgmt_cmd_complete()` — mgmt_util.c:126-167 / 169-215 — build `MGMT_EV_CMD_STATUS`/`_COMPLETE` reply skb, `sock_queue_rcv_skb` to the requester, mirrored to monitor.
- `mgmt_status()`/`mgmt_errno_status()` — mgmt.c:312-321 / 286-310 — map HCI status / `-errno` to wire `MGMT_STATUS_*` (48 `MGMT_EV_*` events defined in mgmt.h).
- skb-based variable-length events (device found/connected, mesh device found) build via `mgmt_alloc_skb()` + `skb_put_data()`/`eir_skb_put_data()` + `mgmt_event_skb()`, e.g. mgmt.c:9773-9810, 10485-10556.

**E. Pairing command/event family (mgmt.c)**
- `pair_device()` — mgmt.c:3598-3732 — `MGMT_OP_PAIR_DEVICE`: `hci_connect_acl`/`hci_connect_le_scan`, arms `connect_cfm_cb=security_cfm_cb=disconn_cfm_cb=pairing_complete_cb` (BR/EDR) or `le_pairing_complete_cb` (LE), `cmd->user_data=hci_conn_get(conn)`.
- `cancel_pair_device()` — mgmt.c:3734-3789 — finds the pending `PAIR_DEVICE` cmd, force-completes it (`CANCELLED`), removes link key/SMP context, `hci_abort_conn()`.
- `find_pairing()`/`pairing_complete()`/`pairing_complete_cb()`/`le_pairing_complete_cb()` — mgmt.c:3504-3520 / 3522-3549 / 3563-3577 / 3579-3596 — locate the pending cmd by `cmd->user_data==conn`.
- `mgmt_smp_complete()` — mgmt.c:3551-3561 — called from `smp_chan_destroy()` to finish an in-flight `pair_device` when SMP ends (success or fail).
- `set_io_capability()` — mgmt.c:3481-3502 — sets `hdev->io_capability` (bounded ≤ `SMP_IO_KEYBOARD_DISPLAY`).
- `user_pairing_resp()` — mgmt.c:3791-3860 — shared body for `user_confirm_reply`/`_neg_reply`, `user_passkey_reply`/`_neg_reply`, `pin_code_neg_reply`: LE address → `smp_user_confirm_reply()` (synchronous reply); BR/EDR → `mgmt_pending_add` + `hci_send_cmd(HCI_OP_USER_*_REPLY)` (async, completed later by an HCI event).
- `mgmt_user_confirm_request()`/`mgmt_user_passkey_request()`/`mgmt_user_passkey_notify()` — mgmt.c:9951-9966 / 9968-9980 / 10028-10042 — emit `MGMT_EV_USER_CONFIRM_REQUEST`/`_PASSKEY_REQUEST`/`_PASSKEY_NOTIFY`.
- `mgmt_user_{confirm,passkey}_{reply,neg_reply}_complete()` (4 fns) — mgmt.c:9998-10026 via `user_pairing_resp_complete()` (9982-9996) — called from hci_event.c reply-status handlers to complete the matching BR/EDR pending cmd.
- `mgmt_auth_failed()` — mgmt.c:10044-10063 — emits `MGMT_EV_AUTH_FAILED`, completes+removes any pending `pair_device` cmd for that conn.

**F. Key load/persist family**
- `load_link_keys()`/`load_long_term_keys()`/`load_irks()` — mgmt.c:2974-3065 / 7276-7367 / 7183-7252 — bulk-replace hdev key lists at boot (bluetoothd → kernel): `hci_link_keys_clear`/`hci_smp_ltks_clear`/`hci_smp_irks_clear` then per-entry `hci_add_link_key`/`hci_add_ltk`/`hci_add_irk`, each screened by `hci_is_blocked_key()`.
- `set_blocked_keys()` — mgmt.c:4353-4400 — `hci_blocked_keys_clear` + repopulate `hdev->blocked_keys` (e.g. CVE-flagged debug/weak keys).
- `hci_add_link_key()`/`hci_add_ltk()`/`hci_add_irk()` — hci_core.c:1276-1321 / 1323-1350 / 1352-1373 — find-or-alloc (`kzalloc_obj`) + `list_add_rcu`.
- `hci_find_link_key()`/`hci_find_ltk()`/`hci_find_irk_by_addr()` — hci_core.c:1108-1132 / 1182-1209 / 1245-1274 — RCU-read lookups used during connection setup, each screened by `hci_is_blocked_key()` (hci_core.c:1091-1106).
- `hci_remove_link_key()`/`hci_remove_ltk()` — hci_core.c:1375-1389 / 1391-1408 — `list_del_rcu`+`kfree_rcu`; used by `unpair_device`/`cancel_pair_device`/`smp_cancel_and_remove_pairing` (smp.c:2441-2486).
- `mgmt_new_link_key()`/`mgmt_new_ltk()`/`mgmt_new_irk()`/`mgmt_new_csrk()` — mgmt.c:9614-9629 / 9650-9691 / 9693-9707 / 9709-… — persistence notifications with a `store_hint` (0 for RPA-derived/debug/no-bonding keys).

**G. SMP L2CAP registration (smp.c)**
- `smp_register()`/`smp_unregister()` — smp.c:3405-3453 / 3455-3470 — create/destroy per-hdev SMP root chans: `hdev->smp_data` (CID 6, if `lmp_le_capable`) and `hdev->smp_bredr_data` (CID 7, if `lmp_sc_capable` or `HCI_FORCE_BREDR_SMP`).
- `smp_add_cid()` — smp.c:3285-3360 — allocs `smp_dev` (LE root only) + `tfm_cmac`/`tfm_ecdh`, `l2cap_chan_create()`+`l2cap_add_scid(cid)`, `ops=smp_root_chan_ops`.
- `smp_force_bredr()` — smp.c:3379-3403 — runtime toggle of the CID-7 root channel.
- `smp_root_chan_ops`/`smp_chan_ops`/`smp_new_conn_cb()` — smp.c:3267-3283 / 3220-3235 / 3237-3265 — root chan spawns a per-connection chan (`smp_chan_ops`) on incoming L2CAP connect; nesting level `L2CAP_NESTING_SMP` (include/net/bluetooth/l2cap.h:758) vs `L2CAP_NESTING_PARENT` (:760) for the root.
- CID constants — l2cap.h:263-264 — `L2CAP_CID_SMP 0x0006`, `L2CAP_CID_SMP_BREDR 0x0007` (confirmed).

**H. SMP crypto toolkit (smp.c)**
- `aes_cmac()` — smp.c:169-207 — wraps `crypto_shash` `tfm_cmac` ("cmac(aes)"), MSB byte-swap per spec.
- `smp_f4/f5/f6/g2/h6/h7()` — smp.c:209-230 / 232-283 / 285-311 / 313-337 / 339-353 / 355-369 — SC confirm/mackey+ltk/dhkey-check-mac/numeric-compare/CTKD, all built on `aes_cmac()`.
- `smp_e/c1/s1/ah()` — smp.c:375-404 / 406-453 / 455-469 / 471-495 — legacy toolkit; `smp_e` is bare AES-128-ECB via the in-kernel AES **library** (`struct aes_enckey`/`aes_prepareenckey`/`aes_encrypt`), not a `crypto_cipher` tfm.
- ECDH — `smp->tfm_ecdh`/`smp_dev->tfm_ecdh = crypto_alloc_kpp("ecdh-nist-p256",0,0)` (smp.c:1398, 3308); `generate_ecdh_keys`/`compute_ecdh_secret`/`set_ecdh_privkey` wrap it via `ecdh_helper.h`.

**I. BR/EDR SSP + security escalation (hci_event.c, hci_conn.c)**
- `hci_io_capa_request_evt()` — hci_event.c:5306-5377 — accept/reject decision (bondable/initiator/no-bonding-remote), replies `HCI_OP_IO_CAPABILITY_{REPLY,NEG_REPLY}`.
- `hci_io_capa_reply_evt()` — hci_event.c:5379-5398 — records `conn->remote_cap`/`remote_auth`.
- `hci_user_confirm_request_evt()` — hci_event.c:5400-5480 — local auto-accept / `auto_accept_delay` work / defers to `mgmt_user_confirm_request()`.
- `hci_user_passkey_request_evt()`/`_notify_evt()`/`hci_keypress_notify_evt()` — hci_event.c:5482-5491 / 5493-5511 / 5514-5551 — forward to mgmt; track `passkey_notify`/`passkey_entered`.
- `hci_simple_pair_complete_evt()` — hci_event.c:5553-5582 — SSP done; `mgmt_auth_failed()` on failure unless already reported by auth-complete.
- `hci_link_key_request_evt()`/`hci_link_key_notify_evt()` — hci_event.c:4670-4726 / 4728-4796 — `HCI_OP_LINK_KEY_{REPLY,NEG_REPLY}` from `hci_find_link_key()`; notify path `hci_add_link_key()`+`mgmt_new_link_key()`, rejects all-zero key (CVE-2020-26555 guard, line 4746).
- `hci_auth_complete_evt()`/`hci_encrypt_change_evt()`/`hci_change_link_key_complete_evt()` — hci_event.c:3491-3553 / 3596-3696 / 3698-3719 — `conn->sec_level = conn->pending_sec_level` on success; drives `BT_CONFIG→BT_CONNECTED` and key-size follow-up.
- `hci_conn_security()` — net/bluetooth/hci_conn.c:2487-2568 — LE → `smp_conn_security()`; BR/EDR → key-type-vs-sec_level table decides "sufficient" / `hci_conn_auth()` / `hci_conn_encrypt()`.

#### 3. Lifecycle and locking

- `hci_dev_lock`/`hci_dev_unlock` = `mutex_lock/unlock(&hdev->lock)` — hci_core.h:1735-1736 — serializes key-list writers and most mgmt.c handler bodies.
- `hdev->mgmt_pending_lock` (mutex) + `hdev->mgmt_pending` (list_head) — hci_core.h:559-560 — **dedicated** lock (not `hci_dev_lock`) serializing all `mgmt_pending_*` ops.
- `mgmt_chan_list_lock` (static mutex) + `mgmt_chan_list` — hci_sock.c:39-40 — guards register/unregister/find and is held across `hci_mgmt_cmd()` dispatch.
- Key lists (`link_keys`/`long_term_keys`/`identity_resolving_keys`/`blocked_keys`/`remote_oob_data`) — `list_head`+`rcu_head` per entry; writers hold `hci_dev_lock` and use `list_add_rcu`/`list_del_rcu`+`kfree_rcu`; readers (`hci_find_*`) use `rcu_read_lock()` only.
- `smp_chan` lifetime = `l2cap_chan->data` on the per-connection SMP channel: alloc in `smp_chan_create()` (smp.c:1382-1420, `kzalloc_obj(*smp, GFP_ATOMIC)`) + `hci_conn_hold()`; freed in `smp_chan_destroy()` (smp.c:742-794) which calls `mgmt_smp_complete()`, frees csrk/responder_csrk/link_key/tfms, purges just-made LTK/IRK on failed pairing, `hci_conn_drop()`. All access is under `l2cap_chan_lock()/unlock()` (nesting class `L2CAP_NESTING_SMP`).
- `smp_timeout()` — smp.c:1371-1380 — 30s `delayed_work` (`SMP_TIMEOUT`); fires `hci_disconnect(HCI_ERROR_AUTH_FAILURE)` if the next expected PDU never arrives.
- `smp->allow_cmd` bitmask + `SMP_ALLOW_CMD()` (smp.c:53) — the literal "next legal PDU" state; `smp_sig_channel()` (smp.c:2940-3068) enforces it and converts violations/errors into `smp_failure()`.
- `smp->flags` (13 `SMP_FLAG_*` bits, smp.c:69-83: TK_VALID, CFM_PENDING, MITM_AUTH, COMPLETE, INITIATOR, SC, REMOTE_PK, DEBUG_KEY, WAIT_USER, DHKEY_PENDING, REMOTE_OOB, LOCAL_OOB, CT2) is the SMP phase/mode state machine.
- `hci_conn` refcounting — atomic `refcnt` + `hci_conn_hold()`/`hci_conn_drop()` (arm/disarm `disc_work` idle timer, hci_core.h:1676-1684) **vs.** `hci_conn_get()`/`hci_conn_put()` (embedded `struct device` get/put, pure existence ref, hci_core.h:1665-1669, doc comment explains the split). `pair_device()` uses both simultaneously.
- `mgmt_pending_cmd` is **not itself refcounted**: lifetime = membership on `hdev->mgmt_pending`; safety = single-owner removal (`mgmt_pending_remove`/`foreach(remove=true)`) under `mgmt_pending_lock`; only the owning `sk` is refcounted (`sock_hold`/`sock_put`).
- Cancel-on-power-off — `mgmt_index_removed()` (mgmt.c:9502-9534) and `__mgmt_power_off()` (mgmt.c:9560-9593) both call `mgmt_pending_foreach(0, hdev, true, cmd_complete_rsp, &match)` (opcode filter 0 = drain **all** pending cmds) plus a targeted `MGMT_OP_SET_POWERED` pass via `settings_rsp`.
- `hci_conn` state: `BT_CONNECT`/`BT_CONFIG`/`BT_CONNECTED` transitions driven by `hci_auth_complete_evt`/`hci_encrypt_change_evt`; `HCI_CONN_AUTH`/`_ENCRYPT`/`_ENCRYPT_PEND`/`_AUTH_PEND`/`_SECURE`/`_AES_CCM`/`_STK_ENCRYPT`/`_NEW_LINK_KEY`/`_FLUSH_KEY` flag bits sequence SSP/CTKD.

#### 4. Hard-coded limits

- `SMP_MIN_ENC_KEY_SIZE=7`, `SMP_MAX_ENC_KEY_SIZE=16` — smp.h:143-144.
- `SMP_CMD_MAX=0x0e` (14 opcodes, 0x01-0x0e) — smp.h:125; enforced in `smp_sig_channel()`.
- `SMP_TIMEOUT=secs_to_jiffies(30)` — smp.c:58; `ID_ADDR_TIMEOUT=msecs_to_jiffies(200)` — smp.c:60.
- `CMAC_MSG_MAX=80` bytes — smp.c:67 (largest `aes_cmac` input is `smp_g2`'s 80-byte buffer).
- Passkey-round hard cap **20** rounds (0..19) — `sc_passkey_round()` smp.c:1508-1509.
- `KEY_DIST_MASK=0x07` — smp.c:64; `AUTH_REQ_MASK(dev)` = `0x3f` if `HCI_SC_ENABLED` else `0x07` — smp.c:62-63.
- `HCI_LINK_KEY_SIZE=16` — include/net/bluetooth/hci.h:36.
- `HCI_MAX_NAME_LENGTH=248` / `MGMT_MAX_NAME_LENGTH=249` — hci.h:1180, mgmt.h:96.
- `mgmt_handlers[]` fixed **92** slots (opcodes 0x0000-0x005B) — mgmt.c:9344-9477, `ARRAY_SIZE` at mgmt.c:9598.
- `HCI_MGMT_VAR_LEN/NO_HDEV/UNTRUSTED/UNCONFIGURED/HDEV_OPTIONAL = BIT(0..4)` — hci_core.h:2358-2362.
- `load_link_keys`/`load_long_term_keys`/`load_irks`/`set_blocked_keys` bound `key_count` by `(U16_MAX - sizeof(header)) / sizeof(entry)` (computed, not literal) plus an exact `struct_size()` match — mgmt.c:2978-2999, 7187-7207, 7280-7300, 4358-4378.
- `HCI_CHANNEL_*`: RAW=0, USER=1, MONITOR=2, CONTROL=3, LOGGING=4 — include/net/bluetooth/hci_sock.h:44-48; `hci_mgmt_chan_register()` rejects `channel<3`.
- `BT_SECURITY_*`: SDP=0, LOW=1, MEDIUM=2, HIGH=3, FIPS=4 — include/net/bluetooth/bluetooth.h:73-77.
- `HCI_LK_*` link-key type space 0x00-0x08 (9 values) — hci.h:697-705.

#### 5. Version-specific facts (verified against this tree's history)

- `hdev->mgmt_pending_lock` is a **new dedicated mutex** — commit 6fe26f694c82 "MGMT: Protect mgmt_pending list with its own lock" (2025-05-20), hardened by 302a1f674c00 "Fix possible UAFs" (2025-08-25). Older write-ups describing the pending-cmd list as protected solely by `hci_dev_lock` are stale for this tree.
- `kzalloc_obj()`/`kmalloc_obj()` (include/linux/slab.h) — **new allocator idiom**: treewide conversion 69050f8d6d07 + default-GFP change bf4afc53b77a (~Dec 2025–Feb 2026) replace the classic `kzalloc(sizeof(*x), GFP_KERNEL)` seen throughout `mgmt.c`/`mgmt_util.c`/`smp.c` (e.g. `mgmt_pending_new()`, `hci_add_link_key()`, `smp_chan_create()`).
- `MGMT_OP_HCI_CMD_SYNC` (0x005B) / `mgmt_hci_cmd_sync()` — **newest mgmt opcode**, added 827af4787e74 (2024-10-23): a test/debug hook straight into the `hci_cmd_sync` queue; absent from all mgmt-api documentation predating ~6.13.
- `smp_e()`'s key schedule is `struct aes_enckey`/`aes_prepareenckey` — switched from `struct crypto_aes_ctx`/`aes_expandkey` by 7f6dfeb943bf "SMP: Use new AES library API" (2026-01-12), i.e. essentially at the tip of history for this release. Note the deeper fact (not new, but often undocumented): `smp_chan`/`smp_dev` have carried **no AES-cipher tfm** since 28a220aac596 (2019-07-02, "switch to AES library") — only `tfm_cmac` (shash/CMAC) and `tfm_ecdh` (KPP) remain crypto-API objects.
- Very recent SMP correctness fixes visible at the top of `smp.c`'s log: "derive legacy responder STK authentication from MITM state", "force responder MITM requirements before building the pairing response", "make SM/PER/KDU/BI-04-C happy" — the MITM/auth-bit logic in `tk_request()`/`smp_cmd_pairing_req()` is an active, SIG-test-driven area right up to this tag.
- `struct smp_csrk` has **no hdev-wide storage or lookup** — grep across `net/bluetooth/*.c` and `include/net/bluetooth/*.h` finds no `hci_add_csrk()`/`hci_find_csrk()`/hdev csrk list (unlike link_key/smp_ltk/smp_irk). CSRKs live only transiently in `smp_chan`, are reported once via `mgmt_new_csrk()`, then freed in `smp_chan_destroy()` — persistence is entirely userspace's responsibility.
- `HCI_MGMT_HDEV_OPTIONAL` (d5cc6626b337, 2020-05-06) and the whole `HCI_MGMT_UNCONFIGURED` handler class predate this tag by years but postdate the "classic" (~2012-2016) BlueZ mgmt-api documentation most tutorials still cite — worth flagging as commonly-undocumented rather than actually new.
- `SMP_FLAG_CT2`/H7 cross-transport key derivation (a62da6f14db7, 2016-12-08) is likewise long-established, **not** new to v7.0, despite being absent from many older SMP write-ups.
- Recent `mgmt.c` hardening at the tip of history: "Fix list corruption and UAF in command complete handlers", "Fix dangling pointer on mgmt_add_adv_patterns_monitor_complete", "validate LTK enc_size on load" (matches the `ltk_is_valid()` bound check), "validate mesh send advertising payload length" — active UAF/bounds-hardening wave on the pending-cmd/event-emission paths.

#### 6. Suggested page topics

1. **The mgmt control channel: registration and dispatch** — `struct hci_mgmt_chan`, `hci_mgmt_chan_register/unregister`, `__hci_mgmt_chan_find`, `hci_mgmt_cmd`, `mgmt_chan_list`/`_lock`, `HCI_CHANNEL_CONTROL`.
2. **mgmt_handlers[]: the 91-command surface and its access-control flags** — `mgmt_handlers[]`, `struct hci_mgmt_handler`, `HCI_MGMT_VAR_LEN/NO_HDEV/UNTRUSTED/UNCONFIGURED/HDEV_OPTIONAL`, `HCI_SOCK_TRUSTED`.
3. **Pending mgmt commands: async completion and cancel-on-power-off** — `struct mgmt_pending_cmd`, `mgmt_pending_add/find/remove/foreach/valid`, `mgmt_pending_lock`, `mgmt_index_removed`, `__mgmt_power_off`.
4. **Emitting mgmt events and replies: the skb plumbing** — `mgmt_cmd_status/complete`, `mgmt_event/_skb/_index_event/_limited_event`, `mgmt_send_event/_skb`, `mgmt_alloc_skb`, `mgmt_status/_errno_status`.
5. **Pairing over mgmt: pair_device, cancel, and the user-response commands** — `pair_device`, `cancel_pair_device`, `find_pairing`, `pairing_complete[_cb]`, `user_pairing_resp`, `user_confirm_reply` family, `set_io_capability`.
6. **Kernel key storage: link_key/smp_ltk/smp_irk/blocked_key and their hdev lists** — the four structs, `hci_add_*`/`hci_find_*`/`hci_remove_*`, `load_link_keys/load_long_term_keys/load_irks/set_blocked_keys`, `hci_is_blocked_key`.
7. **Notifying userspace of new keys: mgmt_new_link_key/ltk/irk/csrk and store_hint** — those four functions, `hci_persistent_key`/`smp_notify_keys`, and the CSRK-has-no-kernel-storage fact.
8. **SMP fixed channels: CID 6/7 and per-hdev root channels** — `L2CAP_CID_SMP`/`_BREDR`, `smp_register/unregister/_add_cid/_force_bredr`, `smp_root_chan_ops` vs `smp_chan_ops`, `hdev->smp_data`/`smp_bredr_data`.
9. **The smp_chan state machine: SMP_FLAG_* and allow_cmd** — `struct smp_chan`, the 13 flag bits, `SMP_ALLOW_CMD`, `smp_sig_channel` dispatcher, `smp_chan_create/destroy`.
10. **Legacy pairing phase-by-phase** — `smp_cmd_pairing_req/rsp`, `tk_request`, `smp_confirm/smp_random`, `smp_c1/s1/e`.
11. **LE Secure Connections pairing phase-by-phase** — `smp_cmd_public_key`, `sc_select_method`, `sc_passkey_round`, SC branches of `smp_cmd_pairing_confirm/random`, `smp_cmd_dhkey_check`, `smp_f4/f5/f6/g2`.
12. **IO-capability method-selection matrix** — `gen_method`/`sc_method` tables, `get_auth_method`, `JUST_WORKS/JUST_CFM/REQ_PASSKEY/CFM_PASSKEY/REQ_OOB/DSP_PASSKEY/OVERLAP`.
13. **Cross-Transport Key Derivation (h6/h7, CT2)** — `smp_h6/smp_h7`, `sc_generate_link_key/sc_generate_ltk`, `SMP_FLAG_CT2`, `bredr_pairing`, `SMP_AUTH_CT2`.
14. **BR/EDR Secure Simple Pairing through hci_event.c** — `hci_io_capa_request/reply_evt`, `hci_user_confirm_request_evt`, `hci_simple_pair_complete_evt`, `hci_link_key_request/notify_evt`, `hci_auth_complete_evt`, `hci_encrypt_change_evt`.
15. **hci_conn security escalation: pending_sec_level and hci_conn_security** — `hci_conn_security`, `conn->sec_level/pending_sec_level`, `BT_SECURITY_*`, `HCI_LK_*` key-type table.
16. **The kernel/userspace split: what mgmt delegates to bluetoothd (GAP policy)** — `confirm_hint` semantics in `mgmt_user_confirm_request`, auto-accept-vs-defer branching in `hci_user_confirm_request_evt`, CSRK non-persistence, the `load_*_keys` round-trip at power-on as the canonical "kernel is just a cache, userspace owns policy+storage" example.
### Area F: drivers btusb/btintel/btmtk/vhci + core↔driver seam — COMPLETE (recorded 2026-07-18)

**Scope note**: btusb.c is one file (4675 lines), not split. It delegates to companion libraries: btintel.c (Intel, in scope), btmtk.c (MediaTek, in scope), **btrtl.c** (Realtek) and **btbcm.c** (Broadcom) — both out of scope but structurally identical delegation pattern (`hdev->setup = btusb_setup_realtek`→`btrtl_setup_realtek()` btusb.c:2727; `hdev->setup = btbcm_setup_patchram/apple` btusb.c:4199,4210). QCA/Qualcomm is the odd one out: **no** companion library — its WMT-like download flow lives inline in btusb.c (`btusb_setup_qca*` btusb.c:3398-3709). btintel.c's PCIe sibling `btintel_pcie.c` is out of scope (per prompt). btmtk.c has two unnamed transport siblings, `btmtksdio.c`/`btmtkuart.c`, that consume the same exported `btmtk_*` API — noted, not explored.

#### 1. Core structs
- `struct hci_dev` — include/net/bluetooth/hci_core.h:355-664. Groups: identity/addr (363-380), feature/version caps (380-461), LE params (404-460), quirk bitmap `quirk_flags` (473), counters/MTUs (475-495), workqueues+work_struct/delayed_work zoo (497-522), rx/cmd/raw skb queues (524-526), request state `req_lock/req_wait_q/req_skb/req_rsp` (531-536), discovery/suspend state (541-554), conn hash + mgmt lists (556-574), `dump` devcoredump state (584), `dev_flags` bitmap (590), adv instance state (593-609), optional MSFT/AOSP ext blocks (630-643), **driver callback vtable** (645-663).
- Callback vtable, hci_core.h:645-663: `open,close,flush,setup,shutdown,send,notify,hw_error,post_init,set_diag,set_bdaddr,reset,wakeup,set_quality_report,get_data_path_id,get_codec_config_data,classify_pkt_type` — 17 pointers total.
- `struct btusb_data` — drivers/bluetooth/btusb.c:914-980. Groups: usb handles (915-920), `flags` bitmap + `poll_sync`/`intr_interval` (922-925), 3 work items (926-928), `acl_q` (930), TX anchors `deferred/tx_anchor/tx_in_flight/txlock` (932-935), RX anchors `intr/bulk/isoc/diag/ctrl_anchor` + `rxlock` (937-942), reassembly skbs `evt_skb/acl_skb/sco_skb` (944-946), endpoint descriptors (948-954), `reset_gpio` (956), cmd request type (958-959), SCO/isoc state (961-965), vendor-swappable fn ptrs `recv_event/recv_acl/recv_bulk/setup_on_usb/suspend/resume/disconnect` (967-975), `qca_dump` (979).
- `struct vhci_data` — drivers/bluetooth/hci_vhci.c:34-49: hdev ptr, `read_wait`/`readq`, `open_mutex`, `open_timeout` delayed work, `suspend_work`, `suspended/wakeup` bools, `msft_opcode`, `aosp_capable`, `initialized` atomic.
- `struct btintel_data` — drivers/bluetooth/btintel.h:215-218: `DECLARE_BITMAP(flags, __INTEL_NUM_FLAGS)` + `acpi_reset_method` fn ptr. Flags enum (INTEL_BOOTLOADER…INTEL_WAIT_FOR_D0) btintel.h:199-213.
- `struct btmtk_data` — drivers/bluetooth/btmtk.h:161-180: drv/dev id, `flags`, `reset_sync` fn ptr, coredump info, usb udev/intf/ctrl_anchor, ISO-over-INTR fields (`isopkt_*`, `isorxlock`). Flags enum btmtk.h:144-150.
- `struct hci_devcoredump` — include/net/bluetooth/coredump.h:34: `supported`, `state` (enum devcoredump_state: IDLE/ACTIVE/DONE/ABORT/TIMEOUT), `timeout`, dump buffer `head/tail/end`, `dump_q`/`dump_rx` work/`dump_timeout`, and the 3 registered fn ptrs `coredump/dmp_hdr/notify_change`.
- `struct hci_drv` (**new**) — include/net/bluetooth/hci_drv.h:68: `common_handler_count/common_handlers`, `specific_handler_count/specific_handlers`, arrays of `struct hci_drv_handler{func,data_len}` (hci_drv.h:63).
- `struct bt_skb_cb` — include/net/bluetooth/bluetooth.h:491-504: `pkt_type/expect/pkt_seqnum/incoming/pkt_status` + union incl. `hci.opcode`; accessed via `bt_cb(skb)` (bluetooth.h:505) and `hci_skb_pkt_type/expect/opcode/event/sk` macros (bluetooth.h:507-513).

#### 2. API families (callback surface + libraries)
Core-called driver callbacks (semantics + one concrete example each, all file:line Read-confirmed):
- `open` — called by `hci_dev_open_sync` hci_sync.c:5187, before HCI init sequence. Ex: `btusb_open` btusb.c:1946 (autopm get, `setup_on_usb`, arms intr/bulk/diag URBs); `vhci_open_dev` hci_vhci.c:51 (no-op).
- `close` — called by `hci_dev_open_sync` (rollback, hci_sync.c:5244) and `hci_dev_close_sync` hci_sync.c:5418, last step of teardown. Ex: `btusb_close` btusb.c:2009 (cancels works, kills anchors, `btusb_free_frags`); `vhci_close_dev` hci_vhci.c:56.
- `flush` — called from `hci_dev_do_reset` hci_core.c:571 and both open/close sync paths (hci_sync.c:5228,5381). Ex: `btusb_flush` btusb.c:2047 (kills `tx_anchor`); `vhci_flush` hci_vhci.c:65.
- `setup` — called by `hci_dev_setup_sync` hci_sync.c:5032, only if `HCI_SETUP` or `HCI_QUIRK_NON_PERSISTENT_SETUP` set. Ex: `btintel_setup_combined` btintel.c:3386 (installed via `btintel_configure_setup` btintel.c:3678, called from `btusb_probe` btusb.c:4219); `btusb_mtk_setup`→`btmtk_usb_setup` btmtk.c:1271; `vhci_setup` hci_vhci.c:272.
- `shutdown` — called by `hci_dev_shutdown` hci_sync.c:5284, while `HCI_UP` still set, before flush/close. Ex: `btintel_shutdown_combined` btintel.c:3642; `btusb_mtk_shutdown`→`btmtk_usb_shutdown` btmtk.c:1458/btusb.c:2914; `btusb_shutdown_qca` btusb.c:3836.
- `send` — called by `hci_send_frame` hci_core.c:3074 (skipped for `HCI_DRV_PKT`, see below). Ex: `btusb_send_frame` btusb.c:2196 (dispatch by `hci_skb_pkt_type`→ctrl/bulk/isoc URB); vendor overrides `btusb_send_frame_intel` btusb.c:2654, `btusb_send_frame_mtk` btusb.c:2874; `vhci_send_frame` hci_vhci.c:74 (pushes to `readq`, wakes reader).
- `notify` — called on SCO/connection lifecycle events, 6 sites incl. `hci_conn_complete_evt` hci_event.c:3251, `__hci_conn_add` hci_conn.c:1072. Ex: `btusb_notify` btusb.c:2242 (detects SCO count/air-mode change, schedules `data->work`→alt-setting switch).
- `hw_error` — called by `hci_error_reset` work hci_core.c:1030 (queued whenever driver injects HW-error event). Ex: `btintel_hw_error` btintel.c:247 (installed via `btintel_configure_setup`); `btusb_rtl_hw_error` btusb.c:1109 (triggers RTL devcoredump).
- `post_init` — called by `hci_dev_init_sync` hci_sync.c:5120, after std HCI init sequence. **No example among the 4 in-scope drivers** — only user in tree is `btnxpuart.c:1889` (out of scope).
- `set_diag` — called from debugfs `vendor_diag_write` hci_debugfs.c:1365 and `hci_dev_init_sync` hci_sync.c:5138 (re-arm after `HCI_QUIRK_NON_PERSISTENT_DIAG`). Ex: `btintel_set_diag_combined` btintel.c:230; `btusb_bcm_set_diag` (BCM path, btusb.c:4200).
- `set_bdaddr` — called by `hci_dev_init_sync`/`hci_dev_setup_sync` (hci_sync.c:5117,5059) when a public addr is programmed. Ex: `btintel_set_bdaddr` btintel.c:142; `btmtk_set_bdaddr` btmtk.c:344; `vhci` does not set it.
- `reset` — called by core's own `hci_cmd_timeout()` work hci_core.c:1477 (**replaces old driver-visible `cmd_timeout`**, see §5) and by sysfs `reset_store` hci_sysfs.c:99. Ex: `btusb_intel_reset` btusb.c:999 (ACPI method or GPIO toggle or `usb_queue_reset_device`); `btmtk_reset_sync` btmtk.c:362; `btusb_qca_reset` btusb.c:1121; `btusb_rtl_reset` btusb.c:1077 (also fires a coredump).
- `wakeup` — called by `hci_suspend_sync` hci_sync.c:6293 to decide remote-wakeup capability. Ex: `btusb_wakeup` (installed btusb.c:4172); `vhci_wakeup` hci_vhci.c:105 (returns `data->wakeup`, toggled via debugfs `force_wakeup`).
- `set_quality_report` — called from mgmt `set_quality_report_func`/`read_exp_features_info` mgmt.c:4833,4593. Ex: `btintel_set_quality_report` btintel.c:1435 (installed inside `btintel_setup_combined` btintel.c:3450).
- `get_data_path_id` / `get_codec_config_data` — called from `configure_datapath_sync` hci_conn.c:245-259 and `sco_sock_get/setsockopt` sco.c:1026,1221,1267. Ex: `vhci_get_data_path_id`/`vhci_get_codec_config_data` hci_vhci.c:87,93 (trivial reference impl); `btintel_get_data_path_id`/`btintel_get_codec_config_data` btintel.c:2437,2388.
- `classify_pkt_type` — called by `hci_dev_classify_pkt_type` hci_core.c:2909→`hci_recv_frame` hci_core.c:2931 (reclassify before queuing). Ex: `btusb_classify_qca_pkt_type` btusb.c:1155 (relabels a QCA debug ACL handle 0x2EDC as `HCI_DIAG_PKT`); `btintel_classify_pkt_type` btintel.c:2673 (ACL→ISO reclass above `BTINTEL_ISODATA_HANDLE_BASE` 0x900, btintel.c:2671).
- `hci_drv` (new alt-channel, bypasses `send`) — `hci_send_frame` hci_core.c:3065-3072 intercepts `HCI_DRV_PKT` and calls `hci_drv_process_cmd()` net/bluetooth/hci_drv.c:65, dispatching to `hdev->hci_drv->common_handlers`/`specific_handlers` by opcode OGF/OCF. Only btusb populates it: `hdev->hci_drv = &btusb_hci_drv` btusb.c:4173, handlers `btusb_hci_drv_read_info/_supported_altsettings/_switch_altsetting` btusb.c:3920,3955,3987.

**Lifecycle/ingestion core API**: `hci_alloc_dev_priv` hci_core.c:2438 · `hci_register_dev` hci_core.c:2585 (requires `open/close/send` set, refuses otherwise) · `hci_unregister_dev` hci_core.c:2691 · `hci_release_dev` hci_core.c:2744 · `hci_free_dev` hci_core.c:2577 · `hci_recv_frame` hci_core.c:2918 · `hci_reset_dev` hci_core.c:2890 (synthesizes a Hardware-Error event) · `hci_suspend_dev`/`hci_resume_dev` hci_core.c:2831,2862 · `hci_get_priv`/`hci_set_drvdata`/`hci_get_drvdata` hci_core.h:1751,1746,1741.

**Coredump API family** (include/net/bluetooth/coredump.h): `hci_devcd_register` net/bluetooth/coredump.c:421 (stores 3 fn ptrs into `hdev->dump`) · `hci_devcd_init`:450 · `hci_devcd_append`:471 · `hci_devcd_complete`:515 · `hci_devcd_abort`:535. Registrants: `btintel_register_devcoredump_support` btintel.c:1491 (`btintel_coredump`/`btintel_dmp_hdr` btintel.c:1459,1472, notify_change=NULL); `btmtk_register_coredump` btmtk.c:377 (`btmtk_coredump`/`_hdr`/`_notify` btmtk.c:62,71,92 — MTK is the only one wiring notify_change); `btusb_probe` btusb.c:4287 (QCA path) and inline RTL path `btusb_rtl_alloc_devcoredump` btusb.c:1055; `vhci` registers a synthetic test harness `vhci_coredump`/`_hdr` hci_vhci.c:285,290 driven by debugfs `force_devcoredump` hci_vhci.c:323-381.

**btintel.c exported families** (btintel.h:246-281): bdaddr/mfg (`btintel_check_bdaddr`:61,`_enter_mfg`:100,`_exit_mfg`:117,`_set_bdaddr`:142), diag (`_set_diag`:180), version (`_version_info`:286,`_read_version`:438,`_version_info_tlv`:463,`_parse_version_tlv`:557), boot/DDC (`_load_ddc_config`:375,`_regmap_init`:871,`_send_intel_reset`:891,`_read_boot_params`:911), firmware (`_download_firmware`:1117,`_bootloader_setup_tlv`:3139), event path (`_recv_event`:3722,`_bootup`:3768,`_secure_send_result`:3780), install points (`_configure_setup`:3678,`_shutdown_combined`:3642), quality/MSFT (`_set_quality_report`:1435,`_set_msft_opcode`:3243).
**btmtk.c exported families** (btmtk.h:187-218): `btmtk_set_bdaddr`:344, firmware `btmtk_setup_firmware[_79xx]`:130,251, `btmtk_reset_sync`:362, coredump `btmtk_register_coredump`/`_process_coredump`:377,394, USB glue `btmtk_usb_recv_acl`:936,`alloc_mtk_intr_urb`:1027,`btmtk_usb_resume/suspend/setup/shutdown`:1239,1256,1271,1458, ID/reset `btmtk_usb_subsys_reset`:819.

#### 3. Lifecycle and locking
- **hdev alloc→register→unregister→release/free**: `hci_alloc_dev_priv` hci_core.c:2438 (kzalloc `sizeof(*hdev)+sizeof_priv`, inits srcu, all sub-locks/lists/works) → `hci_register_dev` hci_core.c:2585 (allocs `hdev->workqueue`/`req_workqueue` as `WQ_HIGHPRI` ordered queues, adds to global `hci_dev_list` under `hci_dev_list_lock` hci_core.c:2649, sets `HCI_SETUP|HCI_AUTO_OFF|HCI_BREDR_ENABLED`, queues `power_on` work) → `hci_unregister_dev` hci_core.c:2691 (sets `HCI_UNREGISTER` under `hdev->unregister_lock`, `synchronize_srcu`, disables rx/cmd/tx/power_on/error_reset works, calls `hci_dev_do_close`) → `hci_release_dev` hci_core.c:2744 (frees keys/lists under `hci_dev_lock`, destroys workqueues, `kfree(hdev)`) triggered via `put_device` from `hci_free_dev` hci_core.c:2577.
- **btusb probe/disconnect vs hci_dev registration**: `btusb_probe` btusb.c:4024 allocates `btusb_data` and `hdev` (`hci_alloc_dev_priv` with vendor `priv_size`) *before* `hci_register_dev` btusb.c:4408; endpoint scan loop btusb.c:4069-4086; `hci_register_dev` failure path frees gpio+hdev+data (btusb.c:4419). `btusb_disconnect` btusb.c:4427 calls vendor `data->disconnect()`, then `hci_unregister_dev`, then `hci_free_dev`+`kfree(data)` — driver object outlives `hdev` registration window on both ends.
- **hci_dev_open_sync / close_sync order** (net/bluetooth/hci_sync.c, serialized under `hci_req_sync_lock`=`mutex_lock(&hdev->req_lock)` include/net/bluetooth/hci_sync.h:15, itself run from the single-threaded `req_workqueue`): open = `hdev->open()`5187 → `hci_devcd_reset`5192 → set `HCI_RUNNING`5194 → `hci_dev_init_sync`5092 (`hdev->setup` inside `hci_dev_setup_sync`5018/5032, `hdev->set_bdaddr`5111, HCI cmd init, `hdev->post_init`5121, `hdev->set_diag`5132) → set `HCI_UP`5202. Close = `hci_dev_shutdown`5269/5284 (**while `HCI_UP` still set**) → flush tx/rx work → optional `HCI_QUIRK_RESET_ON_CLOSE` HCI reset5386 → clear `HCI_RUNNING`5414 → `hdev->close()`5418 (last).
- **URB lifecycle (btusb)**: alloc+anchor+submit triads `btusb_submit_intr_urb`/`_bulk_urb`/`_isoc_urb`/`_diag_urb` btusb.c:1473,1595,1755,1847 anchor into `data->{intr,bulk,isoc,diag}_anchor` before `usb_submit_urb`; completion handlers `btusb_{intr,bulk,isoc,diag}_complete` btusb.c:1428,1552,1641,1806 re-anchor+resubmit unless `-ENOENT`/state-bit cleared. TX: `alloc_ctrl/bulk/isoc_urb` btusb.c:2063,2096,2119 → `submit_or_queue_tx_urb` btusb.c:2174 (increments `tx_in_flight` under `data->txlock` unless `BTUSB_SUSPENDING`, else anchors to `data->deferred` + `schedule_work(&data->waker)`) → `btusb_tx_complete`/`_isoc_tx_complete` btusb.c:1893,1924 decrement `tx_in_flight`. `btusb_stop_traffic` btusb.c:2000 kills all 5 anchors (used by close and suspend).
- **Firmware-download completion machinery is bitmap-flag + `wait_on_bit_timeout`, not `struct completion`, in both vendor libs**: btintel — `btintel_download_wait`/`_boot_wait`/`_boot_wait_d0` btintel.c:1797,1834,1864 wait on `INTEL_DOWNLOADING`/`INTEL_BOOTING`/`INTEL_WAIT_FOR_D0` via `btintel_wait_on_flag_timeout` btintel.h:243; woken by `btintel_bootup`/`btintel_secure_send_result` btintel.c:3768,3780 (called from `btintel_recv_event` btintel.c:3722, demuxing vendor evt 0xff subcodes 0x02/0x06) via `btintel_wake_up_flag`→`wake_up_bit`. btmtk — `btmtk_usb_hci_wmt_sync` btmtk.c:580 sets `BTMTK_TX_WAIT_VND_EVT`, sends cmd 0xfc6f, polls a control-IN URB (`btmtk_usb_submit_wmt_recv_urb` btmtk.c:527), waits `wait_on_bit_timeout(...,HCI_INIT_TIMEOUT)` btmtk.c:644; woken from `btmtk_usb_wmt_recv` completion btmtk.c:445,492 (`wake_up_bit`).
- **Locks**: `hdev->lock` (general mutex, macro `hci_dev_lock` hci_core.h:1735) guards conn/key lists+mgmt; `hdev->req_lock` guards HCI request/sync sequencing (`hci_req_sync_lock` hci_sync.h:15); `data->txlock`/`data->rxlock` spinlocks (btusb.c:935,942) guard `tx_in_flight`/reassembly skbs; `btmtk_data.isorxlock` spinlock (btmtk.h:179) guards ISO reassembly; `vhci_data.open_mutex` (hci_vhci.c:40) serializes `__vhci_create_device`.
- **State flags**: `hdev->flags` bits `HCI_UP/HCI_INIT/HCI_RUNNING` hci.h:386-388; `hdev->dev_flags` bitmap (`HCI_SETUP`421,`HCI_CONFIG`422,`HCI_AUTO_OFF`425,`HCI_RFKILLED`426,`HCI_USER_CHANNEL`434,`HCI_VENDOR_DIAG`464,`HCI_UNREGISTER`432, `__HCI_NUM_FLAGS`479) via `hci_dev_test/set_flag` hci_core.h:840. btusb `data->flags` bit indices btusb.c:895-912 (`BTUSB_INTR_RUNNING…BTUSB_HW_SSR_ACTIVE`, 18 bits) — e.g. `BTUSB_BULK_RUNNING`=1 gates resubmission in `btusb_resume` btusb.c:4592 and `btusb_bulk_complete` btusb.c:1577.

#### 4. Hard-coded limits
- `BTUSB_MAX_ISOC_FRAMES` = 10 — btusb.c:893 (isoc URB frame-descriptor count).
- `HCI_MAX_EVENT_SIZE`=260, `HCI_MAX_ACL_SIZE`=1024, `HCI_MAX_FRAME_SIZE`=ACL+4=1028, `HCI_MAX_SCO_SIZE`=255, `HCI_MAX_ISO_SIZE`=251 — include/net/bluetooth/hci.h:29-34 (reassembly buffer sizes used throughout btusb_recv_*/btmtk_recv_isopkt).
- `HCI_MAX_ID` = 10000 — hci_core.h:45 (`ida_alloc_max` bound in `hci_register_dev`).
- `HCI_INIT_TIMEOUT`=10000ms, `HCI_CMD_TIMEOUT`=2000ms — hci.h:485-486 (used by WMT sync, Intel HCI_OP_RESET, etc).
- `DEVCOREDUMP_TIMEOUT` = 10000ms — include/net/bluetooth/coredump.h:9.
- `VHCI_MINOR` = 137 — include/linux/miscdevice.h:29 (`/dev/vhci` misc minor).
- `HCI_WMT_MAX_EVENT_SIZE` = 64 — btmtk.h:12 (WMT event skb alloc size).
- `MTK_ISO_IFNUM` = 2 — btmtk.h:44 (hardcoded MTK ISO USB interface number).
- `MTK_COREDUMP_SIZE` = 1024000, `MTK_COREDUMP_NUM` = 255 — btmtk.h:26,29.
- `BTINTEL_ISODATA_HANDLE_BASE` = 0x900 — btintel.c:2671 (ACL vs ISO handle split point).
- `__HCI_NUM_QUIRKS` (37 named `HCI_QUIRK_*` bits) — hci.h:80-381; `__INTEL_NUM_FLAGS` btintel.h:212; MTK flags enum btmtk.h:144-150 (5 bits).
- id/quirk tables: `btusb_table` = 30 entries btusb.c:71-176; `quirks_table` = 337 entries btusb.c:180-852 (≈367 USB_DEVICE entries total in btusb.c).

#### 5. Version-specific facts (verified via `git log -S` / `git describe --contains` against full history)
- **`hdev->cmd_timeout` driver callback is GONE.** Introduced v5.1 (e2bef3847e3d, 2019, "Allow driver specific cmd timeout handling"), removed by f07d478090b0 "Bluetooth: Get rid of cmd_timeout and use the reset callback" (2025-01-15, first in v6.14). At v7.0 `struct hci_dev` has no `cmd_timeout` field (hci_core.h:645-663) — the core's own `hci_cmd_timeout()` work (hci_core.c:1462) now calls `hdev->reset()` directly (hci_core.c:1477) instead of a driver `cmd_timeout` hook. Any doc referencing `hdev->cmd_timeout = btusb_cmd_timeout` is stale.
- **`hdev->classify_pkt_type` is new** (f25b7fd36cc3 "vendor-specific packet classification for ISO data", first in v6.11) — not present in pre-6.11 docs. Anchored at hci_core.h:663, driven from `hci_recv_frame` via `hci_dev_classify_pkt_type` hci_core.c:2909.
- **`struct hci_drv` / `net/bluetooth/hci_drv.c` / `include/net/bluetooth/hci_drv.h` are new** (04425292a62c "Introduce HCI Driver protocol", first in v6.16, © 2025 Google) — an entire alt vendor-command channel (`HCI_DRV_PKT`) bypassing `hdev->send`, intercepted in `hci_send_frame` hci_core.c:3065. btusb is the only one of the 4 in-scope drivers that populates `hdev->hci_drv` (btusb.c:4173/4017).
- **`hdev->dump`/devcoredump API is not new-at-v7.0** but still fairly recent — `net/bluetooth/coredump.c` first appears in v6.4 (9695ef876fd1); worth flagging to readers used to 5.x docs, but it predates the other two items.
- **Intel setup is now a single library call**: `btusb_setup_intel`/`btusb_setup_intel_new`/`btusb_shutdown_intel`-style functions (documented for older kernels) do **not exist** in btusb.c at v7.0 (grep-confirmed absent); the entire hw-variant switch lives in `btintel_setup_combined` btintel.c:3386, reached via one call `btintel_configure_setup()` btintel.c:3678 from `btusb_probe` btusb.c:4219. Any page describing "btusb_setup_intel" call chains needs rewriting around this collapsed API.
- `hci_get_data_path_id`/`get_codec_config_data`/`set_quality_report`/`classify_pkt_type` callbacks (offload/SAR/quality/ISO-classification) are all comparatively young additions layered onto the classic open/close/send/notify/hw_error/set_diag/set_bdaddr/flush core — a documentation "callback surface" page should date-stamp these rather than presenting all 17 as a flat, uniformly-old list.

#### 6. Suggested page topics
- **"struct hci_dev driver callback surface"** — own page; built around hci_core.h:645-663, one subsection per callback with its core call-site (hci_sync.c/hci_core.c anchors above) and the vhci **and** one USB-vendor example each (vhci is the cleanest minimal reference impl for nearly every callback in one 725-line file).
- **"btusb: probe, ID matching, and object lifecycle"** — btusb.c:4024 probe, id/quirk tables btusb.c:41-69,71-176,180-852, `btusb_data` btusb.c:914, endpoint discovery loop 4069-4086, disconnect 4427; pairs with the generic hci_register_dev/unregister_dev lifecycle page.
- **"btusb: anchored-URB TX/RX engine"** — its own page given the density: submit/complete quads for intr/bulk/isoc/diag/ctrl (btusb.c:1428-1892, 2063-2240), `tx_in_flight`/`txlock` accounting, `submit_or_queue_tx_urb` deferred-anchor pattern (2174), the 3 works `work/waker/rx_work` (2357-2441), recv reassembly via `hci_skb_expect` (1201,1283,1369) — a good template also for btmtk's `btmtk_recv_isopkt` (btmtk.c:1057).
- **"btusb: suspend/resume, runtime PM, and reset mechanisms"** — btusb_suspend/resume (4475,4564), `btusb_stop_traffic` (2000), OOB wake IRQ (btusb.c:3785, `marvell_config_oob_wake` 2928), and the 4 divergent `*_reset` implementations (btusb_reset/_intel_reset/_rtl_reset/_qca_reset, 982-1173) — worth contrasting GPIO-toggle vs `usb_queue_reset_device` vs ACPI DSM.
- **"Vendor integration: Intel bootloader/firmware flow"** — btintel_setup_combined hw-variant switch (btintel.c:3386), legacy vs TLV paths, and the bitmap-flag+`wait_on_bit_timeout` boot/download completion machinery (1797-1939, 3722-3795) — flag as the "how does a driver wait for a firmware event" canonical example.
- **"Vendor integration: MediaTek WMT protocol and ISO interface"** — `btmtk_usb_hci_wmt_sync` (btmtk.c:580) as the second, independently-implemented wait-on-bit pattern, plus the ISO-over-separate-USB-interface machinery unique to MTK (`btusb_mtk_claim_iso_intf` btusb.c:2754, `btmtk_usb_isointf_init` btmtk.c:1210) — good contrast page against btusb's own isoc/SCO alt-setting path.
- **"btintel.c / btmtk.c as libraries"** — one page mapping exported symbol families to the `hdev` callbacks they install (table format), emphasizing the shared `hci_get_priv`-based private-data convention (btintel.h:220-244, btmtk.h) and the devcoredump registration asymmetry (Intel has no `notify_change`, MTK does).
- **"hci_vhci: the software reference driver"** — small page, but valuable precisely because it's minimal-but-complete: `/dev/vhci` open→delayed device creation (hci_vhci.c:631,405), the write-path pkt_type switch that creates the hci_dev on first `HCI_VENDOR_PKT` write (474-544), debugfs force_suspend/force_wakeup/force_devcoredump (112-381) as a live testbed for the coredump and suspend APIs.
- **"Core↔driver seam: hci_recv_frame, classify_pkt_type, hci_drv, and devcoredump"** — one page tying together hci_core.c:2918 ingestion, the new `classify_pkt_type`/`hci_drv` mechanisms (§5), and the `hci_devcd_*` API, since all three are best explained together as "how the core lets a driver influence packet handling outside of send/recv".

### Area G: hci_uart transport family — planner mini-scout (recorded 2026-07-18)

Targeted scout run at checkpoint time to anchor the two rows the user opted in (Scope decision 3); NOT a full area inventory — the writers of these two pages run the full research pass as usual. Anchors confirmed on disk at v7.0:

- `struct hci_uart` — drivers/bluetooth/hci_uart.h:64; `struct hci_uart_proto` (the ops vtable) — hci_uart.h:48; protocol id `HCI_UART_H4`=0 — hci_uart.h:25; state bit `HCI_UART_PROTO_SET` — hci_uart.h:89.
- Line-discipline core (drivers/bluetooth/hci_ldisc.c): `hci_uart_register_proto`/`_unregister_proto` :42/:57; `hci_uart_tx_wakeup` :117 (EXPORT :145); `hci_uart_init_ready` :208; `hci_uart_send_frame` :274 installed as `hdev->send` at :665; `hci_uart_tty_open` :479; `hci_uart_tty_receive` :608; `hci_uart_set_proto` :706 (HCIUARTSETPROTO ioctl path :771); N_HCI ldisc ops table :832-838.
- serdev variant (drivers/bluetooth/hci_serdev.c): `hci_uart_register_device_priv` :303 (EXPORT :393; inline wrapper `hci_uart_register_device` hci_uart.h:106), `hdev->send = hci_uart_send_frame` :354 (serdev's own :164), `hci_uart_unregister_device` :395.
- H:4 framing (drivers/bluetooth/hci_h4.c): proto table `h4p` :130 (`.enqueue`/`.dequeue` :136-137), `h4_recv` :108, `h4_enqueue` :87, `h4_dequeue` :124, `h4_init` :141 (decl hci_uart.h:162), shared reassembly engine `h4_recv_buf` :151 (EXPORT :271, decl hci_uart.h:165) consumed by other UART protocol drivers.
- Out-of-scope siblings confirmed present (fold-out stands): hci_bcm.c, hci_qca.c, hci_h5.c, hci_ll.c, hci_intel.c, hci_bcsp.c, hci_ath.c, hci_ag6xx.c, hci_aml.c, hci_mrvl.c, hci_nokia.c, hci_bcm4377.c.

## Directory organization

All pages under `docs/bluetooth/`, ten groups:

```
docs/bluetooth/
├── overview/  BR/EDR + BLE stack tours, the userspace GAP/GATT/ATT boundary, SDP (4)
├── core/      hci_dev object, power, locks, workqueues, socket family, hci_sock channels, monitor (8)
├── hci/       HCI protocol machinery: packets, cmd paths, event dispatch, hci_conn, TX scheduling, hci_cb (9)
├── le/        advertising, scanning/discovery, conn params, LE connections, privacy, EIR/AD (9)
├── l2cap/     l2cap_conn/chan, state machines, ops contract, modes, signaling, fixed channels, sockets (9)
├── rfcomm/    session/DLC objects + state machines, krfcommd, MCC, TTY binding (5)
├── audio/     SCO/eSCO + ISO/LE-Audio transports and codec offload (5)
├── mgmt/      the mgmt control channel framework (4)
├── security/  SMP pairing, SSP, keys, security levels (10)
└── drivers/   the 17-callback seam, btusb, btintel, btmtk, vhci, hci_uart core + H:4 (10)
```

Rationale: the prompt's own headings map onto overview/ (the two overview bullets + BLE-host + SDP), mgmt/, l2cap/, rfcomm/, audio/ (LE-Audio), security/ (the pairing bullet), and drivers/ (the vendor-implementations bullet); core/ and hci/ split Area A/B machinery every other page presumes (object+infrastructure vs protocol machinery); le/ holds the LL bullet's advertising/scanning plus the LE constructs they depend on. audio/ pairs SCO with ISO because both are synchronous audio transports riding hci_conn with socket front-ends and shared codec-offload plumbing. security/ merges SMP, BR/EDR SSP, and key storage because pairing spans transports (CTKD) and both transports land keys in the same hdev lists. overview/ is written last so its narratives cite verified anchors.

## Page catalog

Tags: [prompt] = maps to a prompt.md bullet (or a granularity split of one, marked "split"); [curated] = gap-fill under the prompt's "curate new pages where you see fit" mandate. Line numbers are digest hints to re-verify at write time.

### overview/

| page | scope (anchor symbols) | tag |
|---|---|---|
| bredr-overview.md | BR/EDR stack tour: hci_dev+ACL hci_conn path, inquiry/page (hci_inquiry hci_core.c:326, hci_connect_acl), L2CAP over ACL, RFCOMM/SDP on top, SCO beside, BR/EDR SSP entry points; each mechanism recapped ≤1 paragraph + owning-page cite | [prompt] |
| ble-overview.md | BLE stack tour: advertising/scanning/connection establishment, SMP on CID 6, ATT CID 4 as a userspace L2CAP socket, LE CoC, ISO/LE-Audio; LE meta-event flow (hci_le_meta_evt hci_event.c:7458); owning-page cites throughout | [prompt] |
| ble-host-userspace.md | the kernel/userspace split for GAP/GATT/ATT: what the kernel provides (L2CAP fixed-CID 4 via l2cap sockets, LE CoC/ECRED for EATT, mgmt as the GAP policy surface, io_capability + user_confirm round-trips, load_*_keys at power-on, CSRK non-persistence smp.c evidence), what bluetoothd owns | [prompt] |
| sdp.md | the SDP kernel touchpoint: L2CAP_PSM_SDP 0x0001, BT_SECURITY_SDP relaxation (l2cap_sock.c:146-154, l2cap_core.c:877-888), evidence that no in-kernel SDP parser exists, the userspace server over an ordinary dynamic L2CAP channel | [prompt] |

### core/

| page | scope (anchor symbols) | tag |
|---|---|---|
| hci-dev-anatomy.md | struct hci_dev field-group tour (hci_core.h:355-664): identity, capabilities (le_features[248]), quirk/dev_flags bitmaps + accessor macros (hci_core.h:837-843, 666-668), counters/MTUs, queues, sub-lists, embedded device, capability predicate macros; index page for core/ | [curated] |
| hci-dev-lifecycle.md | alloc→register→unregister→release: hci_alloc_dev_priv hci_core.c:2438, hci_register_dev :2585, hci_unregister_dev :2691, hci_release_dev :2744, bt_host_release hci_sysfs.c:82, hci_index_ida + HCI_MAX_ID, hci_dev_list, hci_dev_hold/put = device kobject, hci_dev_get_srcu/put_srcu + hdev->srcu domain | [curated] |
| hci-dev-power.md | power state machine: hci_dev_open/close hci_core.c:439/509 → hci_dev_open_sync/close_sync ordering (hci_sync.c:5187-5418), HCI_UP/HCI_RUNNING/HCI_SETUP/HCI_AUTO_OFF/HCI_UNREGISTER flags, power_on/power_off works, hci_rfkill_set_block :903, suspend/resume (hci_suspend_dev :2831, suspend_notifier), hci_dev_do_reset | [curated] |
| hci-core-locks.md | the lock census: hdev->lock vs req_lock vs cmd_sync_work_lock/unregister_lock/mgmt_pending_lock, hci_dev_list_lock, hci_cb_list_lock, discovery.lock, the two RCU domains (conn_hash RCU vs hdev srcu), bt_proto_lock/hci_sk_list.lock; who takes what and why | [curated] |
| hci-workqueues.md | hdev->workqueue (WQ_HIGHPRI ordered, rx/cmd/tx works + timers) vs req_workqueue (power works, cmd_sync), alloc hci_core.c:2605/2611, the hci_dev_open flush :475, disable_work_sync teardown pattern :2706-2710 | [curated] |
| bt-sockets.md | AF_BLUETOOTH family core: bt_sock_register/bt_proto[] af_bluetooth.c:85/44, BTPROTO_* set (bluetooth.h:52-61), struct bt_sock/bt_sock_list, bt_sock_alloc/link/graft, bt_accept_enqueue/dequeue, bt_sock_wait_state, bt_sock_recvmsg/poll/ioctl, bt_init/bt_exit module wiring, lib.c error mapping (bt_to_errno/bt_status) | [curated] |
| hci-sock-channels.md | HCI socket channels: struct hci_pinfo hci_sock.c:51, hci_sock_bind per-channel rules (RAW/USER/MONITOR/CONTROL/LOGGING hci_sock.h:44-48), HCI_USER_CHANNEL exclusivity, struct hci_filter/hci_sec_filter (hci_sock.c:134), cmsg, legacy ioctls (hci_dev_info family), sendmsg dispatch :1800 | [curated] |
| hci-monitor.md | the monitor protocol (btmon): create_monitor_event/_ctrl_open/_close/_command hci_sock.c:359-782, hci_send_to_monitor, send_monitor_replay, monitor mirroring of mgmt and HCI traffic, cookie/comm identity | [curated] |

### hci/

| page | scope (anchor symbols) | tag |
|---|---|---|
| hci-packets.md | HCI wire formats: command/event/ACL/SCO/ISO packet headers (hci.h structs + 7h byte figures), pkt_type taxonomy incl. HCI_DRV_PKT/HCI_DIAG_PKT, size limits hci.h:29-38, struct bt_skb_cb + hci_skb_pkt_type/expect/opcode macros (bluetooth.h:491-513); hci_send_frame/hci_recv_frame named only as the wire entry/exit points, walkthroughs owned by drivers/driver-seam.md | [prompt] |
| hci-cmd-sync.md | the synchronous command engine: hci_cmd_sync_queue/submit/run/dequeue family (hci_sync.c:626-894), cmd_sync_work :305, cancel vs cancel_sync :664/682, req_lock serialization + req_wait_q/req_status waiter, __hci_cmd_sync_sk :156, the hci_request.c removal (936daee9cf08) and the vestigial struct hci_request shim | [prompt, split] |
| hci-cmd-legacy.md | the immediate command path: hci_send_cmd hci_core.c:3092, cmd_q/cmd_work/cmd_cnt, hci_send_cmd_sync :4102, sent_cmd/req_skb tracking, hci_req_cmd_complete :3960, cmd_timer/ncmd_timer + hci_cmd_timeout :1462 → hdev->reset(), hardware-error chain (hci_hardware_error_evt → hci_error_reset → hci_reset_dev) | [prompt, split] |
| hci-event-dispatch.md | table-driven event dispatch: hci_ev_table/hci_cc_table/hci_cs_table/hci_le_ev_table + HCI_EV/HCI_CC/HCI_CS/HCI_LE_EV macros (hci_event.c:4063-7730), length clamping, hci_event_packet :7769, req_complete/req_complete_skb plumbing, hci_get_cmd_complete | [prompt, split] |
| hci-conn-object.md | struct hci_conn anatomy (hci_core.h:679-789) + struct hci_conn_hash :128 with per-type counters, the 15 hci_conn_hash_lookup_* helpers (:1150-1528), RCU list semantics, hci_conn_valid, conn types ACL/SCO/ESCO/LE/CIS/BIS/PA | [curated] |
| hci-conn-lifecycle.md | __hci_conn_add hci_conn.c:925 / hci_conn_del :1170 / hci_conn_cleanup :140 / hci_conn_failed :1320, the 4 delayed works (disc/auto_accept/idle/le_conn_timeout, :559-666), dual refcounting hold/drop vs get/put (hci_core.h:1644-1691 doc block), handle ida, sysfs bt_link release, disable_delayed_work_sync pattern | [curated] |
| hci-conn-state-machine.md | conn->state transitions per link type with driving events — ACL (conn_request/complete/auth/features evts), SCO/eSCO (sync_conn_complete), LE (le_conn_complete → BT_CONFIG → features), CIS (cis_req/established), BIG/BIS/PA (create_big/big_sync) — full tables + 7i diagram; the verified 8-of-9 BT_* states fact | [curated] |
| hci-tx-scheduling.md | hci_tx_work hci_core.c:3806, hci_sched_acl/sco/le/iso, quota fields + hci_quote_sent, hci_chan (create/del/lookup hci_conn.c:2778-2846) + hci_prio_recalculate, Number-of-Completed-Packets handling (hci_num_comp_pkts_evt), tx_q timestamp tracking (hci_conn_tx_queue/dequeue), __check_timeout | [curated] |
| hci-cb-notifiers.md | struct hci_cb hci_core.h:2119 + hci_register_cb, the hci_connect/disconn/auth/encrypt/key_change/role_switch_cfm dispatchers (:2132-2235), per-conn connect_cfm_cb/security_cfm_cb/disconn_cfm_cb fields, L2CAP/SCO/ISO as registered subscribers | [curated] |

### le/

| page | scope (anchor symbols) | tag |
|---|---|---|
| adv-instances.md | struct adv_info hci_core.h:243 lifecycle (hci_add/remove_adv_instance hci_core.c:1702/1635, hci_adv_instances_clear), adv_instances list + cur_adv_instance, duration vs timeout semantics, adv_instance_expire work + adv_timeout_expire hci_sync.c:553, HCI_MAX_ADV_INSTANCES=5 legacy cap vs le_num_of_adv_sets, hci_schedule_adv_instance_sync :1961 | [prompt] |
| ext-advertising.md | extended/periodic advertising HCI programming: hci_setup_ext_adv_instance_sync/hci_set_ext_adv_data_sync/hci_enable_ext_advertising_sync chain (hci_sync.c:1337-1595), per-adv family (:1610-1735), legacy fallback path, pause/resume (:2534/2582), per-instance RPA (adv_instance_rpa_expired hci_core.c:1691) | [prompt, split] |
| adv-monitor.md | struct adv_monitor/adv_pattern hci_core.h:302-328, adv_monitors_idr, hci_add/remove/free_adv_monitor hci_core.c:1881-2016, mgmt add_adv_patterns_monitor(_rssi), MSFT offload (msft_add_monitor_pattern msft.c:1152) vs software fallback, monitored_devices | [curated] |
| scanning.md | scan programming: hci_passive_scan_sync hci_sync.c:3047 vs hci_active_scan_sync :5996, ext vs legacy scan param/enable, hci_update_accept_list_sync :2753 + resolve-list programming + privacy mode (:2307-2473), why advertising pauses during list updates, interleave scan state machine (:586-616, 2259-2297) | [prompt] |
| discovery.md | struct discovery_state hci_core.h:72 + hci_discovery_set_state hci_core.c:122 (5-state FSM), DISCOV_TYPE_BREDR/LE/INTERLEAVED, hci_start/stop_discovery_sync hci_sync.c:6080/5512, inquiry + inquiry cache lists, hci_inquiry ioctl, discovery filters + mgmt_discovering | [prompt, split] |
| conn-params-autoconnect.md | struct hci_conn_params hci_core.h:804, hci_conn_params_add/del/free hci_core.c:2270-2332, pend_le_conns/pend_le_reports RCU lists (hci_pend_le_list_add/del :2252-2267), auto_connect FSM (DISABLED/REPORT/DIRECT/ALWAYS/LINK_LOSS/EXPLICIT), hci_conn_params_set mgmt.c:5156, add_device/remove_device/load_conn_param | [curated] |
| le-connection.md | LE connection establishment: hci_connect_le hci_conn.c:1376 (explicit) vs hci_connect_le_scan :1620 (background auto-connect), hci_le_create_conn_sync/ext variant hci_sync.c:6581/6530, directed advertising fallback, le_conn_timeout, le_conn_complete_evt path, hci_le_connect_cancel_sync | [curated] |
| le-privacy-rpa.md | RPA/privacy: local RPA generation (hci_update_random_address_sync hci_sync.c:1069, hci_get_random_address :6824), rpa_valid/adv_rpa_valid macros, the two RPA-expiry works (hdev->rpa_expired via mgmt.c:1038 vs per-instance hci_core.c:1691), IRK semantics in resolution, ll_privacy_capable/enabled, HCI_DEFAULT_RPA_TIMEOUT, set_privacy/load_irks mgmt surface; controller resolving-list programming owned by scanning.md (cited via hci_le_add_resolve_list_sync) | [curated] |
| eir-ad-builders.md | the EIR/AD builder library: eir_create eir.c:175, eir_create_adv_data/scan_rsp/per_adv_data :245/343/224, append helpers (eir.c:16-54, eir.h inlines), length precalc, max_adv_len() split 31 vs 251, consumers across mgmt/hci_sync | [curated] |

### l2cap/

| page | scope (anchor symbols) | tag |
|---|---|---|
| l2cap-conn.md | struct l2cap_conn l2cap.h:643 lifecycle + hci_conn tether (hci_conn_get at l2cap_core.c:7004, put in l2cap_conn_free :1818), l2cap_conn_add/del :6984/1764, kref, info_state/info_ident/info_timer machinery (:1412/4608/1676), pending_rx work, id_addr_timer, l2cap_user probe/remove | [prompt, split] |
| l2cap-chan.md | struct l2cap_chan l2cap.h:514, l2cap_chan_create/destroy/hold/hold_unless_zero/put l2cap_core.c:441-518, global chan_list vs per-conn chan_l, lock nesting levels (NORMAL/PARENT/SMP, l2cap.h:757-761), l2cap_chan_set_defaults, PSM/CID spaces + l2cap_global_chan_by_psm :1844 | [prompt, split] |
| l2cap-chan-state-machine.md | chan->state transitions (BT_OPEN…BT_CLOSED, l2cap_chan_connect :7075, l2cap_connect :4008, connect_create_rsp :4199, l2cap_chan_ready :1256, send_disconn_req :1514, chan_del :647) + conf_state substates (l2cap.h:707-720) gating BT_CONFIG→BT_CONNECTED, chan_timeout :405; notes the unreachable AMP-era WAIT_P/WAIT_F rx states | [prompt, split] |
| l2cap-ops.md | struct l2cap_ops l2cap.h:619-641 — all 14 callback contracts (when called, locks held, obligations), invocation sites in l2cap_core.c, implementations compared: l2cap_chan_ops l2cap_sock.c:1792, smp_chan_ops/smp_root_chan_ops smp.c:3220/3267, no-op stubs l2cap.h:886-939 | [prompt, split] |
| l2cap-modes-ertm.md | ERTM + streaming: tx SM (l2cap_tx/_state_xmit/_state_wait_f l2cap_core.c:2929/2780/2852), rx SM (l2cap_rx/_state_recv/_state_srej_sent :6448/6062/6214), l2cap_classify_txseq :5976, seq_list structure :298, retrans/monitor/ack timers :1916/1895/3151, FCS, ews | [prompt, split] |
| l2cap-credit-modes.md | LE CoC + ECRED: l2cap_le_connect/le_start :1282/1383, credit accounting (l2cap_le_rx_credits :541, le_send_credits :6630, le_flowctl_send :2518), l2cap_ecred_connect/defer_connect :1350/1318 (5-chan batching), ecred reconfigure :7260, enable_ecred toggle, rx_busy backpressure | [prompt, split] |
| l2cap-signaling.md | signaling dispatch: l2cap_recv_frame :6913 CID switch, l2cap_sig_channel/le_sig_channel :5623/5574, bredr_sig_cmd :4823, ident allocation via per-conn IDA (l2cap_get/put_ident :927/4803), response matching by scid/dcid vs ident (:90-162), echo/info handling, the LE connection-parameter-update exchange (l2cap_conn_param_update_req :4673, dispatched from l2cap_le_sig_cmd :5509); removed AMP opcodes noted | [prompt, split] |
| l2cap-fixed-channels.md | the fixed-CID map (l2cap.h:259-267) and what is actually wired at v7.0: signaling 1/5, connless 2, ATT 4 as an ordinary userspace socket (evidence), SMP 6/7 present in the map with the registration walkthrough cited to security/smp-fixed-channels.md (seam smp_add_cid), l2cap_add_scid :227, l2cap_global_fixed_chan :7324, local_fixed_chan advertising (:7012, LE FC bits dead) | [curated] |
| l2cap-sockets.md | l2cap_sock glue: l2cap_proto/l2cap_sock_ops :1913/1976, sock_create/alloc/init, the 14 *_cb bodies :1497-1790 mapping proto_ops onto chan ops, BT_MODE/sockopt mapping, defer-setup, rx_busy list, sec_level defaults incl. SDP PSM | [prompt, split] |

### rfcomm/

| page | scope (anchor symbols) | tag |
|---|---|---|
| rfcomm-session-dlc.md | struct rfcomm_session rfcomm.h:154 + struct rfcomm_dlc :169 objects and lifecycles: dlc_alloc/free core.c:303/323, __rfcomm_dlc_open/close :371/451, dlc refcount_t + link/unlink :331/341, session add/del/get/close/create :681-763, the in-kernel L2CAP socket to PSM 3 (:197), sock glue callbacks (sock.c:50/64/271, rfcomm_connect_ind :933) | [prompt, split] |
| rfcomm-state-machines.md | both BT_* state machines with every transition: rfcomm_session FSM (BOUND/CONNECT/CONNECTED/DISCONN + listener states, rfcomm_check_connection core.c:2000, session_close :744 cascade) and rfcomm_dlc FSM (OPEN→CONFIG→CONNECT→CONNECTED→DISCONN→CLOSED plus CONNECT2 deferred accept, __rfcomm_dlc_open :405, rfcomm_dlc_accept :1320, rfcomm_check_accept :1350), driven by the SABM/UA/DM/DISC receivers :1204-1401; 7i state diagrams | [prompt, split] |
| rfcomm-krfcommd.md | the kthread processing model: rfcomm_run/schedule core.c:2114/106, process_sessions/rx/connect/tx/dlcs :2016-1876, rfcomm_mutex scope vs dlc->lock, credit-based flow control (rx/tx_credits, send_credits :1164, RFCOMM_CFC_*), timers (CONN/DISC/AUTH/IDLE timeouts) | [prompt, split] |
| rfcomm-mcc.md | multiplexer control channel: rfcomm_recv_mcc dispatch core.c:1645, PN negotiation :1432 (mtu/credits), RPN/RLS/MSC handlers :1484-1609, send family :929-1164, DLCI 0 semantics, test/NSC | [prompt, split] |
| rfcomm-tty.md | struct rfcomm_dev tty.c:45 + TTY binding: rfcomm_dev_add/__rfcomm_release_dev :318/437, tty_port kref piggyback (:80-107,159-173), RFCOMMCREATEDEV/RELEASEDEV/GETDEVLIST/GETDEVINFO ioctls :573, dlc callback bridging :595-634, tty_install/open/close :700-764, wmem accounting/rfcomm_room :352 | [prompt, split] |

### audio/

| page | scope (anchor symbols) | tag |
|---|---|---|
| sco.md | SCO/eSCO transport: struct sco_conn/sco_pinfo sco.c:45/66, sco_conn_add/del + kref :193/254/80-129, sco_connect/sco_conn_ready/connect_ind/cfm :310/1365/1426/1453, BT_VOICE/BT_CODEC sockopts :930-1056, air-mode/transparent data, timeout_work, hci_setup_sync_conn/enhanced variant seam (hci_conn.c:407/281) | [curated] |
| iso-sockets.md | ISO socket layer: struct iso_conn (kref) / iso_pinfo iso.c:26/60, iso_conn_add/free :200/98-120, BT_SK_DEFER_SETUP/BIG_SYNC/PA_SYNC bits :55-58 and how iso_sock_recvmsg :1597 drives defer accept (iso_conn_defer_accept :1550 → HCI_OP_LE_ACCEPT_CIS)/big_sync, BT_ISO_QOS validation :1662-1706, the exp-feature opt-in gate (set_iso_socket_func mgmt.c:4984 → iso_init) | [prompt, split] |
| cig-cis.md | unicast LE-Audio: hci_bind_cis/hci_connect_cis hci_conn.c:1962/2349, hci_le_set_cig_params :1901 (CIG/CIS id allocation 0x00-0xef), hci_le_create_cis_sync hci_sync.c:6694 + one-pending rule (hci_le_create_cis_pending hci_conn.c:2078), cis_req/cis_established events, cis_cleanup :894, hci_link parent/child topology (hci_conn_link :1728) | [prompt, split] |
| big-bis-pa.md | broadcast LE-Audio: broadcaster hci_bind_bis/hci_connect_bis hci_conn.c:2214/2298 + BIG create; receiver PA sync (hci_pa_create_sync :2152, hci_connect_pa_sync hci_sync.c:7220) + BIG sync (hci_conn_big_create_sync hci_conn.c:2176, hci_le_big_create_sync hci_sync.c:7242), create_big_complete/big_sync_established/lost events, bis_cleanup :823, ISO_MAX_NUM_BIS | [prompt, split] |
| codec-offload.md | codec discovery + offload plumbing: hci_codec.c (hci_read_supported_codecs[_v2] hci_codec.c:120/189, hci_codec_list_add/clear, hdev->local_codecs), the datapath flow configure_datapath_sync hci_conn.c:235, BT_CODEC sockopt surface in sco.c/iso paths; invokes the get_data_path_id/get_codec_config_data driver callbacks whose contracts drivers/hci-driver-callbacks.md owns (cited, not re-documented) | [curated] |

### mgmt/

| page | scope (anchor symbols) | tag |
|---|---|---|
| mgmt-channel.md | the control channel: struct hci_mgmt_chan/hci_mgmt_handler hci_core.h:2364-2377, hci_mgmt_chan_register/unregister hci_sock.c:874/893, hci_mgmt_cmd dispatch + validation :1619-1732, sendmsg channel switch :1800, monitor mirroring, mgmt_init_hdev mgmt.c:1138 (delayed works armed, HCI_MGMT flag) | [prompt, split] |
| mgmt-handlers.md | the command surface: mgmt_handlers[] mgmt.c:9344-9477 (91 commands through MGMT_OP_HCI_CMD_SYNC 0x005B), HCI_MGMT_VAR_LEN/NO_HDEV/UNTRUSTED/UNCONFIGURED/HDEV_OPTIONAL flag classes, trusted vs untrusted sockets, settings bitmap round-trip, exp_features[] sub-table :5034, and the mgmt_config.c sub-surface (read/set_def_system_config, read/set_def_runtime_config mgmt_config.c:56/143/351/360, wired mgmt.c:9449-9455 — hdev tunable get/set) | [prompt, split] |
| mgmt-pending.md | async command tracking: struct mgmt_pending_cmd mgmt_util.h:33, mgmt_pending_new/add/find/foreach/remove/free/valid mgmt_util.c:217-367, the dedicated hdev->mgmt_pending_lock (new, 6fe26f694c82), completion by HCI events, cancel-on-power-off drains (mgmt_index_removed :9502, __mgmt_power_off :9560), sock_hold ownership | [prompt, split] |
| mgmt-events.md | reply/event plumbing: mgmt_cmd_status/complete mgmt_util.c:126/169, mgmt_alloc_skb/send_event(_skb) :59-124, mgmt_event/index/limited wrappers mgmt.c:323-347, mgmt_status/errno mapping :286-321, skb-built variable events (device_found/connected), monitor mirroring | [prompt, split] |

### security/

| page | scope (anchor symbols) | tag |
|---|---|---|
| smp-fixed-channels.md | SMP registration: smp_register/unregister smp.c:3405/3455, smp_add_cid :3285 (CID 6 LE root + CID 7 BR/EDR root, hdev->smp_data/smp_bredr_data), struct smp_dev :85, smp_root_chan_ops vs smp_chan_ops :3267/3220, smp_new_conn_cb :3237, L2CAP_NESTING_SMP, smp_force_bredr :3379 | [prompt, split] |
| smp-chan-state.md | struct smp_chan smp.c:96 lifecycle (smp_chan_create :1382 + hci_conn_hold, smp_chan_destroy :742 + key purge on failure), the 13 SMP_FLAG_* bits :69-83, allow_cmd next-legal-PDU gating (SMP_ALLOW_CMD :53), smp_sig_channel dispatch :2940, smp_timeout 30s :1371, smp_failure | [prompt, split] |
| smp-legacy-pairing.md | legacy pairing phases: smp_cmd_pairing_req/rsp, tk_request, smp_confirm/smp_random, the c1/s1/e primitives :375-469 (AES library, not crypto_cipher), STK generation, PIN/TK entry via mgmt, JUST_WORKS fallbacks | [prompt, split] |
| smp-secure-connections.md | LE Secure Connections: smp_cmd_public_key, sc_select_method, ECDH (tfm_ecdh "ecdh-nist-p256" :1398/3308), f4/f5/f6/g2 :209-337, sc_passkey_round (20 rounds :1508), DHKey check, debug-key handling, OOB | [prompt, split] |
| pairing-methods.md | method selection: gen_method/sc_method matrices, get_auth_method, JUST_WORKS/JUST_CFM/REQ_PASSKEY/CFM_PASSKEY/REQ_OOB/DSP_PASSKEY/OVERLAP, MITM/bonding bits, io_capability sources (set_io_capability mgmt.c:3481), AUTH_REQ_MASK | [prompt, split] |
| cross-transport-keys.md | key distribution + CTKD: key-distribution phase (KEY_DIST_MASK), smp_h6/smp_h7 :339-369, sc_generate_link_key/sc_generate_ltk, SMP_FLAG_CT2/SMP_AUTH_CT2, bredr_pairing path, smp_notify_keys/smp_distribute_keys | [curated] |
| key-storage.md | hdev key lists: struct link_key/smp_ltk/smp_irk/blocked_key/oob_data (hci_core.h:187-239), hci_add/find/remove families hci_core.c:1091-1410 (RCU readers, hdev->lock writers), load_link_keys/load_long_term_keys/load_irks/set_blocked_keys mgmt.c, hci_is_blocked_key screening, mgmt_new_link_key/ltk/irk/csrk + store_hint, CSRK-has-no-kernel-storage evidence | [curated] |
| bredr-ssp.md | BR/EDR SSP via hci_event.c: hci_io_capa_request/reply_evt :5306/5379, hci_user_confirm_request_evt :5400 (auto-accept vs mgmt defer), passkey evts :5482-5551, hci_simple_pair_complete_evt :5553, hci_link_key_request/notify_evt :4670/4728 (zero-key CVE guard), hci_auth_complete/encrypt_change evts :3491/3596 | [prompt, split] |
| conn-security-levels.md | security escalation: hci_conn_security hci_conn.c:2487 (LE → smp_conn_security, BR/EDR key-type table), sec_level/pending_sec_level, BT_SECURITY_SDP..FIPS (bluetooth.h:73-77), HCI_LK_* types, hci_conn_auth/encrypt, HCI_CONN_* security flag bits, enc key size checks | [curated] |
| pairing-over-mgmt.md | the mgmt pairing surface: pair_device mgmt.c:3598 (cfm-callback wiring + dual conn refs), cancel_pair_device :3734, find_pairing/pairing_complete family :3504-3596, mgmt_smp_complete :3551, user_pairing_resp :3791 (LE sync vs BR/EDR async), mgmt_user_confirm/passkey_request events :9951-10042, mgmt_auth_failed :10044 | [prompt, split] |

### drivers/

| page | scope (anchor symbols) | tag |
|---|---|---|
| hci-driver-callbacks.md | the 17-callback contract (hci_core.h:645-663): per callback — when the core calls it (hci_sync.c/hci_core.c call sites), obligations, and ≥1 example among the four drivers (vhci as minimal reference); date-stamped young callbacks (classify_pkt_type, wakeup, quality/codec hooks); the removed cmd_timeout (f07d478090b0); hci_register_dev's open/close/send requirement | [prompt] |
| btusb-probe.md | probe/id matching/lifecycle: btusb_probe btusb.c:4024, btusb_table/quirks_table :71-852 + driver_info flags, endpoint discovery loop :4069, struct btusb_data :914, vendor fn-ptr swapping (recv_event/recv_acl/setup_on_usb…), hci_register_dev wiring :4408, btusb_disconnect :4427 | [prompt] |
| btusb-urb-engine.md | anchored-URB engine: submit/complete quads for intr/bulk/isoc/diag/ctrl :1428-1892, TX alloc/submit_or_queue :2063-2240 + tx_in_flight/txlock + deferred anchor + waker work, RX reassembly via hci_skb_expect :1201-1369, btusb_stop_traffic :2000, BTUSB_* flag bits :895-912, acl_q/rx_work | [prompt, split] |
| btusb-pm-reset.md | PM + reset: btusb_suspend/resume :4475/4564, runtime PM/autopm, BTUSB_SUSPENDING deferral, OOB wake IRQ :3785, the divergent reset impls (btusb_reset/_intel_reset/_rtl_reset/_qca_reset :982-1173: GPIO vs usb_queue_reset_device vs ACPI), wakeup callback | [prompt, split] |
| btintel.md | the Intel library: btintel_setup_combined btintel.c:3386 hw-variant switch (legacy vs TLV), bootloader firmware download (btintel_download_firmware :1117, _bootloader_setup_tlv :3139), bitmap-flag + wait_on_bit_timeout completion machinery (:1797-1939) woken from btintel_recv_event/bootup/secure_send_result :3722-3795, callbacks installed (set_bdaddr/hw_error/set_diag/classify_pkt_type…), btintel_data/hci_get_priv convention | [prompt] |
| btmtk.md | the MediaTek library: WMT protocol (btmtk_usb_hci_wmt_sync btmtk.c:580, wmt_recv :445), firmware download (btmtk_setup_firmware[_79xx] :130/251), ISO-over-separate-interface machinery (btusb_mtk_claim_iso_intf btusb.c:2754, isointf_init btmtk.c:1210, isorxlock), coredump with notify_change :62-92/377, btmtk_reset_sync :362, subsys reset :819 | [prompt] |
| vhci.md | the software reference driver: struct vhci_data hci_vhci.c:34, /dev/vhci open → delayed device creation (:631/405), hci_dev creation on first write (:474-544), vhci_send_frame → readq loopback :74, debugfs force_suspend/force_wakeup/force_devcoredump :112-381, minimal impls of nearly every callback, use as the pure-software contract example | [prompt] |
| driver-seam.md | core↔driver ingestion + side channels — owns the frame-path walkthroughs: hci_recv_frame hci_core.c:2918 (+hci_recv_diag :2976) and hci_send_frame :3039 (monitor mirror, HCI_DRV_PKT interception :3065, hdev->send dispatch), classify_pkt_type hook :2909, the HCI Driver protocol (hci_drv.c:65, btusb_hci_drv handlers btusb.c:3920-3987), devcoredump API (hci_devcd_register/init/append/complete/abort coredump.c:421-535 + state machine) with all four registrant styles | [curated] |
| hci-uart-core.md | the UART transport core: struct hci_uart hci_uart.h:64 + struct hci_uart_proto ops vtable :48 (every callback's contract), the N_HCI line-discipline path (hci_uart_tty_open hci_ldisc.c:479, tty_receive :608, HCIUARTSETPROTO → hci_uart_set_proto :706, ldisc ops :832), proto registry (hci_uart_register_proto :42), TX pump hci_uart_tx_wakeup :117 + hci_uart_send_frame :274 installed as hdev->send :665, the serdev path (hci_uart_register_device_priv hci_serdev.c:303, unregister :395); vendor UART protocol drivers out of scope (named once) | [curated] |
| hci-uart-h4.md | H:4 framing: the h4p proto instance hci_h4.c:130 (h4_recv :108, h4_enqueue :87, h4_dequeue :124, h4_init :141), the shared h4_recv_buf reassembly engine :151 (decl hci_uart.h:165) and its pkt_type-prefix framing (ties to hci/hci-packets.md's taxonomy), HCI_UART_H4 id hci_uart.h:25, consumers of h4_recv_buf across the UART family (enumerated, not documented) | [curated] |

### Fold-in adjudications (topics that do NOT get pages)

hci_debugfs.c adapter knobs → core/hci-dev-anatomy; per-conn debugfs dir → hci/hci-conn-lifecycle; vendor_diag → drivers/hci-driver-callbacks (set_diag). hci_sysfs.c bt_host/bt_link release → core/hci-dev-lifecycle + hci/hci-conn-lifecycle. lib.c (baswap, bt_to_errno/bt_status, logging macros) → core/bt-sockets. HCI Driver protocol (hci_drv.c) → drivers/driver-seam (core/hci-sock-channels cites HCI_DRV_PKT passing only). hci_request.c→hci_sync migration history → hci/hci-cmd-sync (section, not a page). rfcomm sock.c glue → rfcomm/rfcomm-session-dlc. 6lowpan (l2cap_user/ops consumer) → one-line mentions in l2cap/l2cap-ops + l2cap/l2cap-conn. msft.c/aosp.c vendor extensions → le/adv-monitor owns MSFT monitor offload; remaining msft/aosp surface = one-paragraph mention in core/hci-dev-anatomy. Inquiry cache internals → le/discovery. Dead AMP-era code → sections in l2cap/l2cap-chan-state-machine (WAIT_P/WAIT_F) and l2cap/l2cap-signaling (removed opcodes) + inert chan_policy in l2cap/l2cap-sockets. Bluetooth Mesh (mesh_send/mgmt mesh cmds) → noted in mgmt/mgmt-handlers, no page. hci_conn TX timestamping (tx_q) → hci/hci-tx-scheduling. hci_codec.c → audio/codec-offload. Suspend wake-reason/wake_* fields → core/hci-dev-power (core side) + drivers/btusb-pm-reset (driver side).

Fold-OUTs (out of campaign scope, recorded so nobody re-litigates): btrtl/btbcm/btqca vendor paths inside btusb (named once in drivers/btusb-probe as dispatch peers; prompt fixes the four drivers); btintel_pcie.c, btmtksdio.c/btmtkuart.c; the vendor UART protocol drivers (hci_bcm/hci_qca/hci_h5/hci_ll/hci_intel/hci_bcsp/…) — the hci_uart CORE and H:4 are IN per Scope decision 3 (2026-07-18 checkpoint), the vendor protocols atop it stay out, named once in drivers/hci-uart-core.md; other drivers/bluetooth/ drivers; bnep/, cmtp/, hidp/, 6lowpan.c as subsystems (mentioned only as consumers where they appear); GAP/GATT/ATT protocol internals (userspace; overview/ble-host-userspace documents the boundary only); SDP protocol internals (userspace; overview/sdp documents the touchpoint only); Bluetooth Mesh beyond the mgmt-command mention.

### Projected total and tag census

73 pages: overview/ 4, core/ 8, hci/ 9, le/ 9, l2cap/ 9, rfcomm/ 5, audio/ 5, mgmt/ 4, security/ 10, drivers/ 10.
Tag census: 46 [prompt] (including splits), 27 [curated]. (Amended at the 2026-07-18 checkpoint: +2 hci_uart rows per Scope decision 3.)

### Overlap boundary rules (seam symbols named)

1. core/hci-dev-anatomy owns the struct hci_dev field tour; every other page cites fields without re-touring. Seam: the struct definition (hci_core.h:355).
2. hci/hci-cmd-sync owns the cmd_sync engine and req_lock semantics; every `*_sync` consumer page (le/, audio/, core/hci-dev-power) cites hci_cmd_sync_queue in one line instead of re-explaining serialization. Seam: hci_cmd_sync_queue/hci_cmd_sync_work.
3. hci_conn triple: hci-conn-object owns the struct + hash/lookups; hci-conn-lifecycle owns alloc/free/refcounts/works; hci-conn-state-machine owns the transition tables. Seams: hci_conn_hash_add (object), __hci_conn_add/hci_conn_del (lifecycle), conn->state writes (state machine).
4. hci/hci-event-dispatch owns the tables and dispatch mechanics; per-area pages own their handlers' semantics (LE meta handlers → le/ and audio/ pages; security handlers → security/bredr-ssp). Seam: hci_event_packet/hci_le_meta_evt.
5. core/hci-dev-power owns hci_dev_open_sync/close_sync ordering; drivers/hci-driver-callbacks owns when each driver hook fires inside that order. Seam: hci_dev_open_sync.
6. L2CAP cluster: l2cap-conn owns the conn↔hci_conn tether; l2cap-chan owns the chan object; the state-machine page owns transitions; l2cap-ops owns callback contracts; l2cap-signaling owns PDU dispatch; the two modes pages own their flow-control machinery; l2cap-sockets owns the socket glue. Seams: l2cap_conn_add, l2cap_chan_create, chan->ops, l2cap_recv_frame.
7. LE cluster: scanning owns scan/list programming — including the controller accept/resolve-list and privacy-mode programming (seam hci_le_add_resolve_list_sync), which le-privacy-rpa cites while owning local RPA generation and IRK semantics; discovery owns the discovery_state FSM and mgmt discovery flow; conn-params-autoconnect owns the pend lists; le-connection owns establishment. Seams: hci_update_passive_scan_sync, hci_le_add_resolve_list_sync, hci_discovery_set_state, hci_pend_le_list_add, hci_connect_le.
8. Advertising: adv-instances owns adv_info lifecycle and scheduling; ext-advertising owns the HCI programming chains; both cite eir-ad-builders for payload construction. Seams: hci_schedule_adv_instance_sync, eir_create_adv_data.
9. mgmt/ owns the framework (channel, table, pending, events); pages elsewhere own the semantics of the commands they implement (le/ pages for adv/scan/device commands, security/pairing-over-mgmt for pairing commands, audio/iso-sockets for the ISO exp-feature). Seam: hci_mgmt_cmd/mgmt_pending_add.
10. Security cluster: smp-fixed-channels owns registration; smp-chan-state owns the session object and PDU gating; legacy/SC pages own their phase flows; pairing-methods owns the method matrix; cross-transport-keys owns distribution+CTKD; key-storage owns the hdev lists; bredr-ssp owns the hci_event.c side; conn-security-levels owns the escalation API; pairing-over-mgmt owns the mgmt surface. Seams: smp_register, smp_chan_create, smp_sig_channel, hci_conn_security, pair_device.
11. Audio cluster: iso-sockets owns the socket layer + defer setup; cig-cis and big-bis-pa own the HCI/hci_conn paths; hci/hci-conn-state-machine owns the raw state tables all three cite; codec-offload owns codec discovery + the datapath flow, while the get_data_path_id/get_codec_config_data callback contracts belong to drivers/hci-driver-callbacks (codec-offload cites them in one line). Seams: hci_bind_cis, hci_bind_bis, iso_conn_defer_accept, configure_datapath_sync, get_data_path_id.
12. Drivers cluster: hci-driver-callbacks owns the 17-callback contract; the four driver pages own their implementations; driver-seam owns ingestion/classify/hci_drv/devcoredump AND the hci_recv_frame/hci_send_frame walkthroughs (hci/hci-packets names them only as wire entry/exit points). hci-uart-core owns struct hci_uart/hci_uart_proto and both registration paths (ldisc + serdev); hci-uart-h4 owns H:4 framing and h4_recv_buf; vendor UART protocols stay out. Seams: the hci_dev callback fields, hci_recv_frame, hci_send_frame, hci_uart_proto ops (hci-uart-core owns the vtable contract; hci-uart-h4 implements it).
13. House rule: overview/ pages recap any owned mechanism in ≤1 short paragraph and cite the owning page's anchor; the same rule binds every narrative section inside non-overview pages.
14. Driver-example rule (prompt constraints 2/15, rescoped by review amendment 4): the rule binds every page documenting a construct at the core↔driver seam — hci_dev and its callbacks, hci_conn as the driver-visible connection, packet ingestion/classification/framing, codec offload, coredump, suspend/wakeup — each such page carries at least one btusb/btintel/btmtk/vhci example, with the four driver pages as the canonical anchor pool (writers may take anchors from the Area F digest; on-disk re-verification still required, 7e/7o). Constructs no driver code touches (l2cap_chan/l2cap_conn, rfcomm_session/dlc, smp_chan, mgmt_pending_cmd, the sco/iso socket layers) instead state explicitly that the driver seam is at HCI and cite the relevant hci/ or drivers/ page — writers must not invent driver examples that do not exist. Rationale: no drivers/bluetooth code references any upper-layer object; the prompt's intent (constraint 2: "how drivers bridges the core bluetooth layer") is the bridge itself.
15. RFCOMM cluster: rfcomm-session-dlc owns the objects/lifecycle/refcounts and sock glue; rfcomm-state-machines owns both FSMs and the SABM/UA/DM/DISC receive drivers; rfcomm-krfcommd owns the processing model and credit flow; rfcomm-mcc owns control-channel commands; rfcomm-tty owns the TTY device. Seams: rfcomm_recv_frame (state-machines owns its dispatch semantics; krfcommd owns when it runs), __rfcomm_dlc_open (session-dlc owns; state-machines cites the transition it triggers).

### Batch order (foundational → derived, ~5 pages per batch)

- B1: core/hci-dev-anatomy, core/hci-dev-lifecycle, core/hci-core-locks, core/hci-workqueues, core/bt-sockets
- B2: hci/hci-packets, hci/hci-cmd-sync, hci/hci-cmd-legacy, hci/hci-event-dispatch, core/hci-dev-power
- B3: hci/hci-conn-object, hci/hci-conn-lifecycle, hci/hci-conn-state-machine, hci/hci-cb-notifiers, hci/hci-tx-scheduling
- B4: core/hci-sock-channels, core/hci-monitor, mgmt/mgmt-channel, mgmt/mgmt-handlers, mgmt/mgmt-pending
- B5: mgmt/mgmt-events, le/eir-ad-builders, le/adv-instances, le/ext-advertising, le/adv-monitor
- B6: le/scanning, le/discovery, le/conn-params-autoconnect, le/le-connection, le/le-privacy-rpa
- B7: l2cap/l2cap-conn, l2cap/l2cap-chan, l2cap/l2cap-chan-state-machine, l2cap/l2cap-ops, l2cap/l2cap-signaling
- B8: l2cap/l2cap-modes-ertm, l2cap/l2cap-credit-modes, l2cap/l2cap-fixed-channels, l2cap/l2cap-sockets
- B9: security/key-storage, security/smp-fixed-channels, security/smp-chan-state, security/pairing-methods, security/conn-security-levels
- B10: security/smp-legacy-pairing, security/smp-secure-connections, security/cross-transport-keys, security/bredr-ssp, security/pairing-over-mgmt
- B11: audio/sco, audio/iso-sockets, audio/cig-cis, audio/big-bis-pa
- B12: drivers/hci-driver-callbacks, drivers/driver-seam, drivers/vhci, drivers/btusb-probe
- B13: drivers/btusb-urb-engine, drivers/btusb-pm-reset, drivers/btintel, drivers/btmtk, audio/codec-offload
- B14: drivers/hci-uart-core, drivers/hci-uart-h4, rfcomm/rfcomm-session-dlc, rfcomm/rfcomm-state-machines, rfcomm/rfcomm-krfcommd
- B15: rfcomm/rfcomm-mcc, rfcomm/rfcomm-tty, overview/bredr-overview, overview/ble-overview
- B16: overview/ble-host-userspace, overview/sdp

Ordering rationale: the hci_dev object and its locks/workqueues first (everything cites them); command/event machinery before the objects whose transitions those events drive; hci_conn before every layer that rides it; mgmt framework before the LE/security pages whose commands it carries; L2CAP before RFCOMM (which rides it) and before security (SMP is an L2CAP fixed channel); key storage before the pairing flows that populate it; drivers late so every core construct they exemplify is already written; codec-offload follows its contract page (review amendment 11: moved B11→B13, after drivers/hci-driver-callbacks); the four overview/ narratives last so they cite verified anchors. Recorded benign forward-cites (review amendment 12, mention-only by boundary rules, no reorder): hci/hci-cmd-legacy (B2) names the reset() contract in one line (owned by drivers/hci-driver-callbacks, B12); l2cap/l2cap-fixed-channels (B8) cites security/smp-fixed-channels (B9).

### Adversarial review outcome (2026-07-18)

Reviewer ran 80+ anchor checks across all ten groups (prioritizing v7.0-new symbols): zero failures; the only not-found probes (btusb_setup_intel, btusb_setup_intel_new) confirm this file's own drift claims. Twelve amendments returned; disposition:
1. ACCEPTED — mgmt_config.c handlers folded into mgmt/mgmt-handlers.md scope (four hdev-tunable get/set commands were uncited anywhere).
2. ACCEPTED — Area C digest was missing from this file despite the Phase-1-complete log entry; digest recorded, CORRECTION logged in Status.
3. ACCEPTED — l2cap_conn_param_update_req added to l2cap/l2cap-signaling.md scope (LE conn-param-update PDU was unowned).
4. ACCEPTED — boundary rule 14 rescoped: driver examples bind seam-level constructs only; upper-layer pages state the seam is at HCI instead of inventing nonexistent examples.
5. ACCEPTED — hci_recv_frame/hci_send_frame walkthroughs deeded to drivers/driver-seam.md; hci/hci-packets names them as entry/exit points only (rule 12 updated).
6. ACCEPTED — get_data_path_id/get_codec_config_data contracts deeded to drivers/hci-driver-callbacks.md; audio/codec-offload cites (rule 11 updated).
7. ACCEPTED — SMP CID 6/7 registration walkthrough deeded to security/smp-fixed-channels.md; l2cap/l2cap-fixed-channels lists + cites (seam smp_add_cid).
8. ACCEPTED — resolving-list/privacy-mode programming deeded to le/scanning.md; le/le-privacy-rpa owns local RPA + IRK semantics and cites (rule 7 updated, seam hci_le_add_resolve_list_sync).
9. ACCEPTED — rfcomm/rfcomm-session-dlc.md split: objects/lifecycle/sock-glue vs new rfcomm/rfcomm-state-machines.md (both FSMs + SABM/UA/DM/DISC drivers); rule 15 added; catalog 70→71.
10. DECLINED — key-storage.md split into storage vs notifications: store_hint semantics are derived from key properties at storage time and the notification half alone is too thin to stand; the single row already separates the two halves internally. (Reviewer marked the split optional.)
11. ACCEPTED — audio/codec-offload moved B11→B13, after its contract page drivers/hci-driver-callbacks (B12); paired with amendment 6.
12. ACCEPTED AS RECORDED FORWARD-CITES (no reorder) — hci-cmd-legacy→reset() contract and l2cap-fixed-channels→smp-fixed-channels are mention-only under the boundary rules; noted in the ordering rationale.
Also applied: configure_datapath_sync line hint corrected to hci_conn.c:235; reviewer flagged overview/sdp.md as the one defensibly-thin row (kept: it is a distinct prompt bullet; merge target recorded as overview/ble-host-userspace.md if the user prefers).

## Execution & verification

- Pipeline: per SKILL.md ("Modes") — one writer per page (strongest model; passes 00-02 inside the writer), orchestrator check per page (pass 03, never delegated), batches of ~5 with a hard checkpoint between batches; certification by a later `bluetooth-verify` campaign (`guidelines/passes/04-verify.md`); its cadence is a user decision taken at the phase-3 checkpoint.
- Project-specific write-time rules (from the constraints above, on top of Gate A/B):
  - Every major construct documented carries at least one concrete example from btusb, btintel, btmtk, or vhci (constraint 2, rule 7k); pages that document a core function cite driver usage of it (constraint 15).
  - Ops-structure coverage is exhaustive: every callback of a documented ops struct gets its contract (when called, context/locks, what it must do), and every state machine lists all states and all transitions with the code that drives each (constraints 8, 13).
  - Lifecycle sections (alloc/free/refcount/locking) and async-behavior sections (work deferral, completions, timers, lazy processing) are mandatory wherever the construct has them (constraints 11, 12).
  - Packet formats get 7h-style byte/bit figures; struct relationships and state machines get 7i figures (constraint 16); figures follow `guidelines/rules/diagrams.md`.
  - The kernel/userspace split is stated explicitly wherever a protocol layer lives partly in userspace (GAP/GATT/ATT/SDP; constraint on the BLE-host and SDP bullets).
  - Elixir links pin `v7.0`; excerpts byte-compared against the tree (7e, 7l).
- Write-time cautions: prompt.md details are stale by declaration — nothing from it lands without on-disk verification; inventory-digest line numbers are hints to re-verify. Known version-drift list (facts a writer must not import from older documentation; each verified by an inventory agent against this tree, commit ids given for provenance):
  - `hci_request.c`/`hci_request.h` do not exist (removed by 936daee9cf08); the old hci_req_add/hci_req_run builder API is gone; `struct hci_request` survives only as an hci_sync.c-internal shim; `msft_req_add_set_filter_enable` is a dead vestige with zero callers.
  - `hdev->cmd_timeout` driver callback does not exist (removed by f07d478090b0); the core's hci_cmd_timeout work calls `hdev->reset()` directly.
  - A2MP/AMP/BT_HS are fully removed (e7b02296fb40): no a2mp.c/amp.c, no Create/Move-Channel L2CAP opcodes; the WAIT_P/WAIT_F ERTM rx states, L2CAP_MOVE_* enums, and `chan->chan_policy` are unreachable/inert vestiges; document them only as such.
  - `hdev->destruct` (pre-2014 docs) does not exist; teardown is device-model-driven via bt_host_release.
  - btusb_setup_intel/btusb_setup_intel_new/btusb_shutdown_intel do not exist; Intel setup is btintel_setup_combined via btintel_configure_setup.
  - New at/near v7.0 (do not omit as "future"): hci_drv protocol + HCI_DRV_PKT (04425292a62c), classify_pkt_type (f25b7fd36cc3), le_features[248] + HCI_OP_LE_READ_ALL_LOCAL_FEATURES (a106e50be74b), dedicated hdev->mgmt_pending_lock (6fe26f694c82), MGMT_OP_HCI_CMD_SYNC 0x005B (827af4787e74), iso_conn kref (dc26097bdb86), smp_e via AES library `struct aes_enckey` (7f6dfeb943bf), kzalloc_obj/kmalloc_obj allocator idiom treewide (69050f8d6d07) — excerpts must show the kzalloc_obj form, not the classic kzalloc(sizeof()) form older docs show.
  - disable_delayed_work_sync/disable_work_sync (not cancel_*) is the teardown idiom in hci_conn_del, hci_unregister_dev, hci_adv_instances_clear, iso_conn_free.
  - ISO sockets (BTPROTO_ISO) are exp-feature opt-in via MGMT_OP_SET_EXP_FEATURE(iso_socket_uuid), not always-on.
  - L2CAP: ident allocation is a per-conn IDA; L2CAP_MODE_RETRANS/FLOWCTL are defined but dead; LE fixed-chan FC bits are never advertised; SMP CIDs are 0x0006/0x0007.
  - SDP has no kernel implementation beyond the PSM constant and a sec_level default; GAP/GATT/ATT are userspace (state the boundary, never document kernel internals for them).
  - RFCOMM runs on the krfcommd kthread (no workqueue conversion); rfcomm_dev refcounts via tty_port kref, not its own kref.
  - CSRKs have no hdev storage or lookup helpers; they exist transiently in smp_chan and are reported to userspace once.
- Save policy: pages land only under `docs/bluetooth/<group>/`; no navigation-file edits; no git commits without an explicit user go.
