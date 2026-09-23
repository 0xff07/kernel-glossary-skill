# Configuration requests

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A connection manager reads and writes registers inside routers several links away, one control packet out and one reply back for each access. Only the route, the packet type and size, and a two-bit sequence number tie a reply to the question that caused it. A router that answers late could therefore answer the next question asked, the hazard this layer is built to close.

The configuration request pairs the two packets, one layer above the channel that moves the bytes and one below the helpers that name registers. This page follows one request from allocation through the queue, the pairing callbacks and the retry loop to the result its caller reads.

```
    One configuration read across the three contexts that touch it
    ──────────────────────────────────────────────────────────────
    time ↓
    submitting thread            │ control-channel receive       │ system per-CPU workqueue
    ─────────────────────────────┼───────────────────────────────┼──────────────────────────
    ① built, one reference       │                               │
    ② queue's reference taken,   │                               │
      linked, ACTIVE set ───────▶│ request on the queue          │
    ③ packet sent, thread asleep │                               │
      on its stack completion    │ ④ reply offered to each       │
                                 │   queued request in turn      │
                                 │ ⑤ reply accepted, verdict     │
                                 │   stored, work queued ───────▶│ ⑥ waiter signalled,
                                 │                               │   request unlinked,
      awake ◀────────────────────┼───────────────────────────────┼── ACTIVE clear, the
                                 │                               │   queue's reference dropped
    ⑦ result read, the builder's │                               │
      reference dropped          │                               │

    ① tb_cfg_read_raw      ctl.c:976  allocates the request with its first reference
    ② tb_cfg_request       ctl.c:558  takes the queue's reference before the enqueue
    ③ tb_cfg_request_sync  ctl.c:631  sleeps until the completion or the timeout
    ④ tb_cfg_request_find  ctl.c:181  asks each queued request's match callback
    ⑤ tb_ctl_rx_callback   ctl.c:515  lets the accepting request copy the reply
    ⑥ tb_cfg_request_work  ctl.c:529  signals the waiter, then unlinks and puts
    ⑦ tb_cfg_read_raw      ctl.c:995  drops the builder's reference
```

## SUMMARY

A request is one reference-counted allocation, [`struct tb_cfg_request`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L77), that carries the packet going out and the shape of the reply that may come back. Its builder chooses two callbacks. [`match`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L87) decides whether an arriving frame answers the request, and [`copy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L89) takes the frame in and records a verdict in the embedded [`struct tb_cfg_result`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L32).

The submitter publishes the request, transmits and sleeps on a completion, while the receive path offers each frame to the queued requests in order. A request leaves the queue once per submission, with [`TB_CFG_REQUEST_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L98) as the witness, and a waiter that times out waits for that exit. Above this core a raw read or write retries with a fresh sequence number, and inline wrappers supply the route for the rest of the driver.

## SPECIFICATIONS

- USB4 Specification version 1.0, section 6.4.2.7: the PG field of the notification packet that acknowledges a hot plug or unplug event, as commit 210e9f56e9e1 ("thunderbolt: Populate PG field in hot plug acknowledgment packet") describes the section. [`tb_cfg_ack_plug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L842) fills that field, which in the commit's words "tells whether the acknowledgment is for plug or unplug event".
- USB4 Specification, response time of a control packet, no section number recorded in the tree: commit 7f0a34d7900b ("thunderbolt: Decrease control channel timeout for software connection manager") states that "The USB4 spec recommends 10 ms +- 1 ms but we use slightly larger value (100 ms)", and [`TB_TIMEOUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L19) holds the 100 ms.
- USB4 Specification version 2, notification types, no section number recorded in the tree: commit 235d019481bc ("thunderbolt: Add the new USB4 v2 notification types") adds the seven codes from [`TB_CFG_ERROR_ROP_CMPLT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L33) to [`TB_CFG_ERROR_ASYM_LINK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L39) and says the driver needs "to ack the ones routers expect to be acked".
- The request object, its queue, its reference count and its retry loop follow no specification section. They are a kernel construct introduced by commit d7f781bfdbf4 ("thunderbolt: Rework control channel to be more reliable"), whose message says the model "is copied from Greybus implementation", and the model on this page is a synthesis of [`ctl.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c) and [`ctl.h`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h) at v7.2 with every fact cited to its line.

## COVERAGE

### The request object and its record (drivers/thunderbolt/ctl.h)

- [`'\<struct tb_cfg_request\>':'drivers/thunderbolt/ctl.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L77): one outstanding exchange, carrying both packets, the pairing callbacks, the flag word, the work item, the result and the queue link
- [`'\<struct tb_cfg_result\>':'drivers/thunderbolt/ctl.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L32): the outcome of an exchange, whose error member is negative for a local failure, 0 for success and 1 for a router's refusal
- [`'\<struct ctl_pkg\>':'drivers/thunderbolt/ctl.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L46): one control-channel buffer with its ring frame, the form in which a received frame reaches the pairing callbacks
- [`'\<TB_CFG_REQUEST_ACTIVE\>':'drivers/thunderbolt/ctl.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L98): bit 0 of the flag word, set with the link onto the channel's queue and cleared with the unlink
- [`'\<TB_CFG_REQUEST_CANCELED\>':'drivers/thunderbolt/ctl.h'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L99): bit 1 of the flag word, set when the waiter stops waiting

### Allocation and references (drivers/thunderbolt/ctl.c)

- [`'\<tb_cfg_request_alloc\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L88): allocate a zeroed request holding one reference
- [`'\<tb_cfg_request_get\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L105): take a reference under the file-wide reference mutex
- [`'\<tb_cfg_request_put\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L126): drop a reference under the same mutex, releasing the request at zero
- [`'\<tb_cfg_request_destroy\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L112): the release function, which frees the request and nothing else
- [`'\<tb_cfg_request_lock\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L78): the mutex that serializes every reference change on every request

### The queue (drivers/thunderbolt/ctl.c)

- [`'\<tb_cfg_request_enqueue\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L133): link the request and set its active bit under the queue mutex, refusing a stopped channel
- [`'\<tb_cfg_request_dequeue\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L151): unlink an active request, clear its active bit and wake a canceller
- [`'\<tb_cfg_request_is_active\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L168): read the active bit, the condition a canceller sleeps on
- [`'\<tb_cfg_request_find\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L174): return the first queued request whose match callback accepts a frame, with a reference taken
- [`'\<tb_cfg_request_cancel_queue\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L76): the wait queue on which every canceller sleeps until its request is unlinked

### Submission, completion and cancel (drivers/thunderbolt/ctl.c)

- [`'\<tb_cfg_request\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L547): take the queue's reference, enqueue and transmit, without waiting
- [`'\<tb_cfg_request_work\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L524): the work item that calls the submitter's callback, unlinks the request and drops the queue's reference
- [`'\<tb_cfg_request_sync\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L616): submit and sleep on a completion declared on the caller's stack, cancelling on timeout
- [`'\<tb_cfg_request_complete\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L597): the callback the synchronous path installs, which signals that completion
- [`'\<tb_cfg_request_cancel\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L589): mark the request cancelled, push its work item and sleep until it is unlinked

### The configuration pairing (drivers/thunderbolt/ctl.c)

- [`'\<tb_cfg_match\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L856): accept an error frame, or a frame whose type, route, size and sequence number agree with the request
- [`'\<tb_cfg_copy\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L883): store the header verdict, copy the reply when it passed, and finish the request

### Configuration commands (drivers/thunderbolt/ctl.c)

- [`'\<tb_cfg_read_raw\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956): read dwords of a configuration space, one request per try, returning the router's refusal untranslated
- [`'\<tb_cfg_write_raw\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1030): the writing counterpart, with the payload copied into the packet once
- [`'\<TB_CTL_RETRIES\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L22): 4, the tries a raw read or write makes against a silent router
- [`'\<tb_cfg_read\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1111): the raw read at the channel's timeout, with the result folded into an errno
- [`'\<tb_cfg_write\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1137): the raw write at the channel's timeout, with the same folding
- [`'\<tb_cfg_reset\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L911): send one reset packet to a router and wait once for its echo
- [`'\<tb_cfg_get_upstream_port\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1173): read one dword and return the number of the port the reply came from

### Error decoding (drivers/thunderbolt/ctl.c)

- [`'\<tb_cfg_get_error\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1088): turn a router's refusal into one of four errnos, quietly for an unimplemented adapter
- [`'\<tb_cfg_print_error\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L278): log a refusal at the severity its code is given, from silence to a backtrace

### Acknowledgements (drivers/thunderbolt/ctl.c)

- [`'\<tb_cfg_ack_plug\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L842): acknowledge a hot plug or unplug event with an error-type packet carrying the plug-group field
- [`'\<tb_cfg_ack_notification\>':'drivers/thunderbolt/ctl.c'`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778): acknowledge a notification with a header-only packet, naming the code in the debug log

## DOCUMENTATION

- [`Documentation/core-api/kref.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/core-api/kref.rst): the three reference-counting rules, including the answer to rule 3 for an object taken off a list, a lock around the lookup
- [`Documentation/scheduler/completion.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/scheduler/completion.rst): on-stack completions and the warning that a waiter which times out must keep the completion until every related [`complete()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/sched/completion.c#L50) has run
- [`Documentation/core-api/workqueue.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/core-api/workqueue.rst): the non-reentrance conditions under which one work item runs on at most one worker at a time
- [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst): the section on networking over a Thunderbolt cable, whose service driver logs in to the other host through the exported XDomain request

## OTHER SOURCES

### Added by Claude Opus 5.5

- [thunderbolt: Populate PG field in hot plug acknowledgment packet (commit 210e9f56e9e1)](https://lore.kernel.org/r/20191217123345.31850-4-mika.westerberg@linux.intel.com)
- [thunderbolt: Replace usage of found with dedicated list iterator variable (commit 03941ed91c72)](https://lore.kernel.org/all/CAHk-=wgRr_D8CB-D9Kg-c=EHreAsk5SqXPwr9Y7k9sA6cWXJ6w@mail.gmail.com/)

## REGISTERS

A configuration request owns no hardware register. Its paths touch two words, the request's own flag word and the address dword a read or write carries. The flag word records whether the request is linked on the channel's queue and whether its waiter gave up.

```
    The low byte of the flags word of struct tb_cfg_request
    ───────────────────────────────────────────────────────

    bit    7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┐
    flags │·│·│·│·│·│·│C│A│
          └─┴─┴─┴─┴─┴─┴─┴─┘
                       │ │
    CANCELED ──────────┘ │
    ACTIVE ──────────────┘

    ACTIVE = TB_CFG_REQUEST_ACTIVE (bit 0, set with the link, cleared with the unlink)
    CANCELED = TB_CFG_REQUEST_CANCELED (bit 1, the waiter stopped waiting)
    · = unused, as is every bit above bit 1 of the unsigned long
```

[`TB_CFG_REQUEST_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L98) is set by [`tb_cfg_request_enqueue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L133) and cleared by [`tb_cfg_request_dequeue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L151), both under the queue mutex. It therefore changes together with the link and the unlink. [`TB_CFG_REQUEST_CANCELED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L99) is set by [`tb_cfg_request_cancel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L589) and read by [`tb_cfg_request_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L524), where it stops the callback into a departed waiter.

The address dword follows the common header in both a read and a write. Its six fields are filled, echoed and compared at different stages of one exchange, and [`struct tb_cfg_address`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L50) gives the bit ranges the figure draws.

```
    The address dword of a configuration read or write
    ──────────────────────────────────────────────────

    bit    3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
           1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
    addr  │zero │seq│spc│   port    │  length   │         offset          │
          │31:29│   │   │  (24:19)  │  (18:13)  │         (12:0)          │
          └─────┴───┴───┴───────────┴───────────┴─────────────────────────┘

    offset = tb_cfg_address.offset (12:0, the first dword, counted in dwords)
    length = tb_cfg_address.length (18:13, dwords to move, at most 63)
    port   = tb_cfg_address.port (24:19, the adapter asked; in a reply, the sender's upstream adapter)
    spc    = tb_cfg_address.space (26:25, one enum tb_cfg_space value)
    seq    = tb_cfg_address.seq (28:27, the try number of this request)
    zero   = tb_cfg_address.zero (31:29, 0 in both directions)
```

[`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) fills [`offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L51), [`length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L52), [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L53) and [`space`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L54) from its arguments and writes [`seq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L55) once per try. [`tb_cfg_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L856) compares the echoed [`seq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L55), and [`check_config_address()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L223) requires [`zero`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L56) to read 0 and the other echoed fields to agree. The reply's [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L53) becomes the caller's upstream-port answer.

The one configuration-space register this layer names by itself is dword 0 of a router's space. [`tb_cfg_get_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1173) reads it and discards the data, keeping only the port its reply came from. Every other register reaches this layer as an offset and a length from a caller. The request layer exposes no sysfs attribute and no debugfs file of its own.

## DETAILS

The subsections follow one configuration read through the life of its request, in order. The first ones define the request and its result, count its references, and publish it on the channel's queue. The middle ones take the reply through the lookup, the pairing callbacks and the work item back to the waiter, or to the cancel. The last ones cover the commands, their retry loop and error decoding, the acknowledgements, then the wrappers and the XDomain users of the request.

### The request object carries both directions of one exchange

Everything one exchange needs is gathered into one allocation, which the submitting thread and the receive path share. A table of what each member of [`struct tb_cfg_request`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L77) holds comes first. Its kerneldoc and definition follow with the two flag macros, then a figure of where its pointers lead.

| member | what it holds | written by | read by |
|---|---|---|---|
| [`kref`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L78) | the reference count, 1 at allocation | [`kref_init()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kref.h#L29) in [`tb_cfg_request_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L88), then [`tb_cfg_request_get()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L105) and [`tb_cfg_request_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L126) | [`kref_put()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kref.h#L62), which releases the request at zero |
| [`ctl`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L79) | the channel whose queue holds the request | [`tb_cfg_request_enqueue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L133) | [`tb_cfg_request_dequeue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L151), to find the queue mutex |
| [`request`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L80), [`request_size`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L81), [`request_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L82) | the outgoing packet in the builder's memory, its length in bytes and its frame type | the builder | [`tb_cfg_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L547), which transmits it, and [`tb_cfg_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L856), which reads its route |
| [`response`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L83), [`response_size`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L84), [`response_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L85) | the buffer an accepted reply is copied into, the reply's expected size and its frame type, with no buffer meaning no reply is expected | the builder | [`tb_cfg_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L547), [`tb_cfg_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L856) and [`tb_cfg_copy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L883) |
| [`npackets`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L86) | a packet count that only ICM-only code writes and reads | ICM-only code | ICM-only code |
| [`match`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L87), [`copy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L89) | the pairing callbacks | the builder | [`tb_cfg_request_find()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L174) and [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) |
| [`callback`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L90), [`callback_data`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L91) | the submitter's completion hook and its argument | [`tb_cfg_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L547) | [`tb_cfg_request_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L524) |
| [`flags`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L92) | the active and cancelled bits | [`tb_cfg_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L547), [`tb_cfg_request_enqueue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L133), [`tb_cfg_request_dequeue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L151) and [`tb_cfg_request_cancel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L589) | [`tb_cfg_request_dequeue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L151), [`tb_cfg_request_is_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L168) and [`tb_cfg_request_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L524) |
| [`work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L93) | the work item that finishes the request | [`INIT_WORK()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/workqueue.h#L309) in [`tb_cfg_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L547) | [`schedule_work()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/workqueue.h#L758), from three sites |
| [`result`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L94) | the outcome the waiter returns | [`tb_cfg_copy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L883), [`tb_cfg_request_cancel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L589) and [`tb_xdomain_copy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L123) | [`tb_cfg_request_sync()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L616) |
| [`list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L95) | the link into the channel's queue | [`INIT_LIST_HEAD()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/list.h#L43) in [`tb_cfg_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L547), then the enqueue and the dequeue | [`tb_cfg_request_find()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L174) |

The builder writes its eight members before submission, and the machinery writes the rest as the request moves. The kerneldoc of [`struct tb_cfg_request`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L77) restricts [`ctl`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L79) to a queued request, and [`TB_CFG_REQUEST_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L98) and [`TB_CFG_REQUEST_CANCELED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L99) are bit numbers into [`flags`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L92).

```c
/* drivers/thunderbolt/ctl.h:52 */
/**
 * struct tb_cfg_request - Control channel request
 * @kref: Reference count
 * @ctl: Pointer to the control channel structure. Only set when the
 *	 request is queued.
 * @request: Request is stored here
 * @request_size: Size of the request packet (in bytes)
 * @request_type: Type of the request packet
 * @response: Response is stored here
 * @response_size: Maximum size of one response packet
 * @response_type: Expected type of the response packet
 * @npackets: Number of packets expected to be returned with this request
 * @match: Function used to match the incoming packet
 * @copy: Function used to copy the incoming packet to @response
 * @callback: Callback called when the request is finished successfully
 * @callback_data: Data to be passed to @callback
 * @flags: Flags for the request
 * @work: Work item used to complete the request
 * @result: Result after the request has been completed
 * @list: Requests are queued using this field
 *
 * An arbitrary request over Thunderbolt control channel. For standard
 * control channel message, one should use tb_cfg_read/write() and
 * friends if possible.
 */
struct tb_cfg_request {
	struct kref kref;
	struct tb_ctl *ctl;
	const void *request;
	size_t request_size;
	enum tb_cfg_pkg_type request_type;
	void *response;
	size_t response_size;
	enum tb_cfg_pkg_type response_type;
	size_t npackets;
	bool (*match)(const struct tb_cfg_request *req,
		      const struct ctl_pkg *pkg);
	bool (*copy)(struct tb_cfg_request *req, const struct ctl_pkg *pkg);
	void (*callback)(void *callback_data);
	void *callback_data;
	unsigned long flags;
	struct work_struct work;
	struct tb_cfg_result result;
	struct list_head list;
};
/* drivers/thunderbolt/ctl.h:98 */
#define TB_CFG_REQUEST_ACTIVE		0
#define TB_CFG_REQUEST_CANCELED		1
```

[`struct tb_cfg_request`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L77) owns no packet memory, so its pointers reach into three other places. The figure draws them for a configuration read.

```
    Where the request of one configuration read points
    ──────────────────────────────────────────────────

    struct tb_cfg_request, on the heap
    ┌──────────────────────────────────────────────────────────────┐
    │ request   response   ctl   list   work                       │
    │ result, a struct tb_cfg_result embedded by value             │
    └──┬─────────┬──────────┬─────┬──────┬─────────────────────────┘
       │         │          │     │      │
       │         │          │     │      └──▶ system per-CPU workqueue, once scheduled
       │         │          ▼     ▼
       │         │     struct tb_ctl of the domain
       │         │     ┌────────────────────────────────────────────────┐
       │         │     │ request_queue, which links the queued requests │
       │         │     │ request_queue_lock, running                    │
       │         │     └────────────────────────────────────────────────┘
       │         │
       ▼         ▼
    the builder's stack frame
    ┌──────────────────────────────────────────────────────────────┐
    │ struct cfg_read_pkg request, 12 bytes                        │
    │ struct cfg_write_pkg reply, 268 bytes                        │
    └──────────────────────────────────────────────────────────────┘
```

[`request`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L80) and [`response`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L83) point into the builder's stack frame. A builder must therefore be sure the request can no longer be reached before it returns. [`ctl`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L79) and [`list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L95) tie the request to the domain's [`struct tb_ctl`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L39), whose [`request_queue`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L47) links every queued request. [`work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L93) goes onto the system per-CPU workqueue when the request finishes.

The request object therefore carries both directions of one exchange, the packet out and the shape of the reply back.

### The result record carries the outcome a waiter reads back

A caller needs three answers from an exchange, and the result record carries them, whether it worked, what a refusing router said, and which adapter answered. [`struct tb_cfg_result`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L32) and [`struct ctl_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L46) come first, the second being the form in which a received frame reaches the pairing callbacks. A strip of the request's state fields over one read follows them.

```c
/* drivers/thunderbolt/ctl.h:32 */
struct tb_cfg_result {
	u64 response_route;
	u32 response_port; /*
			    * If err = 1 then this is the port that send the
			    * error.
			    * If err = 0 and if this was a cfg_read/write then
			    * this is the upstream port of the responding
			    * switch.
			    * Otherwise the field is set to zero.
			    */
	int err; /* negative errors, 0 for success, 1 for tb errors */
	enum tb_cfg_error tb_error; /* valid if err == 1 */
};

struct ctl_pkg {
	struct tb_ctl *ctl;
	void *buffer;
	struct ring_frame frame;
};
```

[`struct tb_cfg_result`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L32) encodes the outcome in [`err`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L42), as its own comment says. The value is negative for a local failure, 0 for success and 1 for a router's refusal. [`tb_error`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L43) is meaningful only when [`err`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L42) is 1, and [`response_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L34) then names the adapter that sent the refusal. After a successful read or write it names the responding router's upstream adapter instead, and [`response_route`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L33) is the route the reply carried.

[`struct ctl_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L46) keeps its channel in [`ctl`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L47), the packet bytes in [`buffer`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L48), and in [`frame`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L49) the [`struct ring_frame`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L627) the ring fills. The pairing callbacks read the frame's [`size`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L631) and [`eof`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L633), its length in bytes and its packet type.

The request's own state fields change hands at a few events. The strip draws them over a read answered in time, over one whose wait expires, and over an XDomain request.

```
    The state fields of one request, over a read answered in time
    ─────────────────────────────────────────────────────────────

    time ────────────────────────────────────────────────────────────────────────────────▶

    event         allocated     submitted      queued       reply copied       waiter back
                      ▼             ▼             ▼               ▼                 ▼
                      ┌─────────────┬──────────────────────────────────────────────────────────
    callback          │ NULL        │ the submitter's hook and its argument
                      └─────────────┴──────────────────────────────────────────────────────────
                      ┌───────────────────────────┬────────────────────────────────────────────
    ctl               │ NULL                      │ the channel, kept after the unlink
                      └───────────────────────────┴────────────────────────────────────────────
                      ┌───────────────────────────────────────────┬────────────────────────────
    result            │ zero from the allocation                  │ the reply's verdict
                      └───────────────────────────────────────────┴────────────────────────────
                                    ❶             ❷               ❸

    the same request when the wait expires first
                  allocated                         wait expires            unlinked
                      ▼                                   ▼                     ▼
                      ┌─────────────────────────────────────────────────────────┬──────────────
    result.err        │ 0, or the verdict of a copy that ran                    │ -ETIMEDOUT
                      └─────────────────────────────────────────────────────────┴──────────────
                                                                                ❹

    a request built for an XDomain message
                  allocated                                 reply copied
                      ▼                                           ▼
                      ┌───────────────────────────────────────────┬────────────────────────────
    result.err        │ 0 from the allocation                     │ 0 again, frame copied as is
                      └───────────────────────────────────────────┴────────────────────────────
                                                                  ❺

    ❶ tb_cfg_request          ctl.c:553      callback, callback_data ← the hook and its argument
    ❷ tb_cfg_request_enqueue  ctl.c:144      ctl ← the channel, under the queue mutex
    ❸ tb_cfg_copy             ctl.c:893      result ← the verdict of the header checks
    ❹ tb_cfg_request_cancel   ctl.c:594      err ← the caller's -ETIMEDOUT, after the unlink
    ❺ tb_xdomain_copy         xdomain.c:129  err ← 0 for every frame the match accepted
```

❶ [`tb_cfg_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L547) installs the submitter's hook and its argument in [`callback`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L90) and [`callback_data`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L91). ❷ [`tb_cfg_request_enqueue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L133) records the channel in [`ctl`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L79) under the queue mutex, and nothing clears it afterwards. ❸ [`tb_cfg_copy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L883) stores the verdict of a matched reply in [`result`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L94), the value the waiter returns. ❹ [`tb_cfg_request_cancel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L589) writes the caller's error into [`err`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L42) once the request is unlinked. ❺ [`tb_xdomain_copy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L123) writes 0 into [`err`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L42) for every frame its match accepted.

The result is a member of the request, and the waiter reads it back as a copy. The result record therefore carries the outcome a waiter reads back, whatever path wrote it.

### Every reference change on a request takes one file mutex

A request can have three holders at once, and every change to its count takes [`tb_cfg_request_lock`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L78). The holders are its builder, the channel's queue and a receive-path lookup. The mutex, [`tb_cfg_request_cancel_queue`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L76) and [`tb_cfg_request_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L88) come first, then [`tb_cfg_request_get()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L105), [`tb_cfg_request_destroy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L112) and [`tb_cfg_request_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L126), then a figure of the holders.

```c
/* drivers/thunderbolt/ctl.c:76 */
static DECLARE_WAIT_QUEUE_HEAD(tb_cfg_request_cancel_queue);
/* Serializes access to request kref_get/put */
static DEFINE_MUTEX(tb_cfg_request_lock);

/**
 * tb_cfg_request_alloc() - Allocates a new config request
 *
 * This is refcounted object so when you are done with this, call
 * tb_cfg_request_put() to it.
 *
 * Return: &struct tb_cfg_request on success, %NULL otherwise.
 */
struct tb_cfg_request *tb_cfg_request_alloc(void)
{
	struct tb_cfg_request *req;

	req = kzalloc_obj(*req);
	if (!req)
		return NULL;

	kref_init(&req->kref);

	return req;
}
```

[`tb_cfg_request_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L88) allocates with [`kzalloc_obj()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/slab.h#L1152), so every member starts at zero, and [`kref_init()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kref.h#L29) leaves the builder's count of one. [`tb_cfg_request_cancel_queue`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L76) and [`tb_cfg_request_lock`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L78) are file-scope, shared by every request of every domain. [`tb_cfg_request_get()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L105), the release [`tb_cfg_request_destroy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L112) and [`tb_cfg_request_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L126) follow in the file with their kerneldoc.

```c
/* drivers/thunderbolt/ctl.c:101 */
/**
 * tb_cfg_request_get() - Increase refcount of a request
 * @req: Request whose refcount is increased
 */
void tb_cfg_request_get(struct tb_cfg_request *req)
{
	mutex_lock(&tb_cfg_request_lock);
	kref_get(&req->kref);
	mutex_unlock(&tb_cfg_request_lock);
}

static void tb_cfg_request_destroy(struct kref *kref)
{
	struct tb_cfg_request *req = container_of(kref, typeof(*req), kref);

	kfree(req);
}

/**
 * tb_cfg_request_put() - Decrease refcount and possibly release the request
 * @req: Request whose refcount is decreased
 *
 * Call this function when you are done with the request. When refcount
 * goes to %0 the object is released.
 */
void tb_cfg_request_put(struct tb_cfg_request *req)
{
	mutex_lock(&tb_cfg_request_lock);
	kref_put(&req->kref, tb_cfg_request_destroy);
	mutex_unlock(&tb_cfg_request_lock);
}
```

[`tb_cfg_request_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L126) holds [`tb_cfg_request_lock`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L78) across [`kref_put()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kref.h#L62), so [`tb_cfg_request_destroy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L112) runs with the mutex held. The release recovers the request with [`container_of()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/container_of.h#L19) and frees it with [`kfree()`](https://elixir.bootlin.com/linux/v7.2/source/mm/slub.c#L6671), and touches no list, because the unlink happens earlier under another mutex.

Over one configuration read the count rises to three and falls back to zero. The figure draws who holds each reference between the six changes.

```
    Who holds one configuration read's request, and the count they add up to
    ────────────────────────────────────────────────────────────────────────

    time ──────────────────────────────────────────────────────────────────────────────▶
                        Ⓐ           Ⓑ           Ⓒ           Ⓓ           Ⓔ           Ⓕ
                        ╎           ╎           ╎           ╎           ╎           ╎
    builder             ├───────────────────────────────────────────────────────────┤
    queue                           ├───────────────────────────────────┤
    receive lookup                              ├───────────┤
                        ╎           ╎           ╎           ╎           ╎           ╎
    kref                1           2           3           2           1           0

    Ⓐ tb_cfg_request_alloc ctl.c:96   the count starts at 1, the builder's reference
    Ⓑ tb_cfg_request       ctl.c:558  takes the queue's reference before the enqueue
    Ⓒ tb_cfg_request_find  ctl.c:180  takes a reference before asking match
    Ⓓ tb_ctl_rx_callback   ctl.c:517  drops the lookup's reference after the copy
    Ⓔ tb_cfg_request_work  ctl.c:532  drops the queue's reference after the unlink
    Ⓕ tb_cfg_read_raw      ctl.c:995  drops the builder's reference, which frees it
```

Ⓐ [`tb_cfg_request_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L88) starts the count at 1, the builder's reference. Ⓑ [`tb_cfg_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L547) takes the queue's reference before the enqueue. Ⓒ [`tb_cfg_request_find()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L174) takes a reference on each request it asks and keeps it on the one that accepts. Ⓓ [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) drops that lookup reference after the copy. Ⓔ [`tb_cfg_request_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L524) drops the queue's reference after the unlink. Ⓕ [`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) drops the builder's reference, the last one in this run.

The lookup's drop can also land after the work item's or the builder's, and whichever holder drops last frees the request. Every reference change on a request therefore takes [`tb_cfg_request_lock`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L78).

### Submission takes the queue's reference, enqueues, then transmits

A request becomes reachable by the receive path before its packet leaves. A reply that arrives while the transmit is still returning therefore finds it queued. [`tb_cfg_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L547) is read whole, and its two error labels undo the enqueue and the reference in reverse order.

```c
/* drivers/thunderbolt/ctl.c:547 */
int tb_cfg_request(struct tb_ctl *ctl, struct tb_cfg_request *req,
		   void (*callback)(void *), void *callback_data)
{
	int ret;

	req->flags = 0;
	req->callback = callback;
	req->callback_data = callback_data;
	INIT_WORK(&req->work, tb_cfg_request_work);
	INIT_LIST_HEAD(&req->list);

	tb_cfg_request_get(req);
	ret = tb_cfg_request_enqueue(ctl, req);
	if (ret)
		goto err_put;

	ret = tb_ctl_tx(ctl, req->request, req->request_size,
			req->request_type);
	if (ret)
		goto err_dequeue;

	if (!req->response)
		schedule_work(&req->work);

	return 0;

err_dequeue:
	tb_cfg_request_dequeue(req);
err_put:
	tb_cfg_request_put(req);

	return ret;
}
```

[`tb_cfg_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L547) clears [`flags`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L92) and installs the submitter's hook. It prepares [`work`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L93) with [`INIT_WORK()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/workqueue.h#L309) and [`list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L95) with [`INIT_LIST_HEAD()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/list.h#L43) before the request is reachable. The reference [`tb_cfg_request_get()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L105) takes is the queue's, and [`tb_cfg_request_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L524) drops it when the request is finished.

Transmission through [`tb_ctl_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L366) follows the enqueue. An error from it leaves through `err_dequeue` and `err_put`, which unlink the request and drop the queue's reference in that order. A request without a [`response`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L83) buffer has its work item scheduled once the packet is on the ring, so it finishes without a matching frame.

So far, the request holds the builder's and the queue's references, is linked on the channel's queue, and has its packet on the transmit ring. Submission therefore publishes the request before it transmits, and unwinds both steps when the transmit fails.

### Enqueue publishes the request under the queue mutex

Linking the request, recording its channel and setting its active bit happen in one hold of the queue mutex. While the channel runs, a reader holding that mutex never sees the list and the bit disagree. [`tb_cfg_request_enqueue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L133) is read whole, and it touches three members of [`struct tb_ctl`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L39), [`request_queue_lock`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L46), [`request_queue`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L47) and [`running`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L48).

```c
/* drivers/thunderbolt/ctl.c:133 */
static int tb_cfg_request_enqueue(struct tb_ctl *ctl,
				  struct tb_cfg_request *req)
{
	WARN_ON(test_bit(TB_CFG_REQUEST_ACTIVE, &req->flags));
	WARN_ON(req->ctl);

	mutex_lock(&ctl->request_queue_lock);
	if (!ctl->running) {
		mutex_unlock(&ctl->request_queue_lock);
		return -ENOTCONN;
	}
	req->ctl = ctl;
	list_add_tail(&req->list, &ctl->request_queue);
	set_bit(TB_CFG_REQUEST_ACTIVE, &req->flags);
	mutex_unlock(&ctl->request_queue_lock);
	return 0;
}
```

[`tb_cfg_request_enqueue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L133) opens with two [`WARN_ON()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bug.h#L109) checks that catch a request submitted twice. The first tests [`TB_CFG_REQUEST_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L98), and the second tests [`ctl`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L79), which no path clears after this function sets it. Every in-tree builder allocates a fresh request for each submission, so neither fires on the paths this page reads.

Under [`request_queue_lock`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L46) the function returns -ENOTCONN when [`running`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L48) is clear. Otherwise it sets [`ctl`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L79), links [`list`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L95) at the tail of [`request_queue`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L47) with [`list_add_tail()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/list.h#L189), and sets the active bit with [`set_bit()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bitops/instrumented-atomic.h#L26). The tail insertion keeps the queue in submission order, the order in which a later lookup asks the requests.

The enqueue refuses a request only when the channel is stopped. Enqueue therefore makes a request reachable and active in one hold of the queue mutex.

### A stopped channel refuses every submission at the enqueue

The request layer serves submissions only while the channel runs, because the enqueue fails them with -ENOTCONN once [`running`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L48) is clear. The flag's two writers come first, the end of [`tb_ctl_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L730) and the head of [`tb_ctl_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L751). A table of the domain paths that call them follows.

```c
/* drivers/thunderbolt/ctl.c:736 */
	for (i = 0; i < TB_CTL_RX_PKG_COUNT; i++)
		tb_ctl_rx_submit(ctl->rx_packets[i]);

	ctl->running = true;
/* drivers/thunderbolt/ctl.c:753 */
	mutex_lock(&ctl->request_queue_lock);
	ctl->running = false;
	mutex_unlock(&ctl->request_queue_lock);

	tb_ring_stop(ctl->rx);
	tb_ring_stop(ctl->tx);

	if (!list_empty(&ctl->request_queue))
		tb_ctl_WARN(ctl, "dangling request in request_queue\n");
	INIT_LIST_HEAD(&ctl->request_queue);
```

[`tb_ctl_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L730) sets [`running`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L48) after the receive buffers are posted. [`tb_ctl_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L751) clears it under the mutex the enqueue reads it under. A submission therefore either finishes its enqueue before the stop or sees the flag clear. It then stops both rings, reports a request still linked through [`tb_ctl_WARN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L58), and reinitializes the queue head, which drops such a request from the list with its active bit still set.

While the channel runs, the enqueue accepts requests and the receive path offers frames to the lookup. Once it stops, the test of [`running`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L48) is a precondition every submission gains. The three callers of [`tb_cfg_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L547) meet it, [`tb_cfg_request_sync()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L616), [`__tb_xdomain_response()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L138) and one ICM-only caller.

The domain drives both writes from nine sites, four that start the channel and five that stop it. The page hands off to the channel's own lifecycle at [`tb_ctl_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L730) and [`tb_ctl_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L751).

| domain path | channel call | site |
|---|---|---|
| [`tb_domain_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L439) | [`tb_ctl_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L730) | [`domain.c:451`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L451) |
| [`tb_domain_add()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L439), error path | [`tb_ctl_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L751) | [`domain.c:490`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L490) |
| [`tb_domain_remove()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L503) | [`tb_ctl_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L751) | [`domain.c:509`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L509) |
| [`tb_domain_suspend_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L528) | [`tb_ctl_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L751) | [`domain.c:541`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L541) |
| [`tb_domain_resume_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L556) | [`tb_ctl_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L730) | [`domain.c:561`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L561) |
| [`tb_domain_freeze_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L574) | [`tb_ctl_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L751) | [`domain.c:582`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L582) |
| [`tb_domain_thaw_noirq()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L588) | [`tb_ctl_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L730) | [`domain.c:593`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L593) |
| [`tb_domain_runtime_suspend()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L607) | [`tb_ctl_stop()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L751) | [`domain.c:614`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L614) |
| [`tb_domain_runtime_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L618) | [`tb_ctl_start()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L730) | [`domain.c:620`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L620) |

Only a domain path that restarts the channel lets submissions through again. A stopped channel therefore turns every submission into -ENOTCONN at the enqueue.

### Dequeue unlinks a request once and wakes a canceller

A reply and a timeout can both try to finish one request, and a second unlink changes nothing on the queue. The unlink returns at once when the active bit is already clear. [`tb_cfg_request_dequeue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L151) and [`tb_cfg_request_is_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L168) are read whole, then a figure of the four states a request passes through.

```c
/* drivers/thunderbolt/ctl.c:151 */
static void tb_cfg_request_dequeue(struct tb_cfg_request *req)
{
	struct tb_ctl *ctl = req->ctl;

	mutex_lock(&ctl->request_queue_lock);
	if (!test_bit(TB_CFG_REQUEST_ACTIVE, &req->flags)) {
		mutex_unlock(&ctl->request_queue_lock);
		return;
	}

	list_del(&req->list);
	clear_bit(TB_CFG_REQUEST_ACTIVE, &req->flags);
	if (test_bit(TB_CFG_REQUEST_CANCELED, &req->flags))
		wake_up(&tb_cfg_request_cancel_queue);
	mutex_unlock(&ctl->request_queue_lock);
}

static bool tb_cfg_request_is_active(struct tb_cfg_request *req)
{
	return test_bit(TB_CFG_REQUEST_ACTIVE, &req->flags);
}
```

[`tb_cfg_request_dequeue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L151) takes the queue mutex through [`ctl`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L79), the pointer the enqueue set, and returns when [`TB_CFG_REQUEST_ACTIVE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L98) is clear. Commit 0f73628e9da1 ("thunderbolt: Do not double dequeue a configuration request") added that test after crashes in the work item. Its theory is that the work item "can be scheduled twice for a request".

When the request is active, [`list_del()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/list.h#L258) and [`clear_bit()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bitops/instrumented-atomic.h#L39) run under [`request_queue_lock`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L46). A canceller is woken through [`tb_cfg_request_cancel_queue`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L76) before the mutex drops. [`tb_cfg_request_is_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L168) reads the bit with [`test_bit()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/bitops.h#L60) and no lock, and a canceller sleeps until it reports false.

[`tb_cfg_request_dequeue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L151) is the only caller of [`list_del()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/list.h#L258) on a request, and its test limits the unlink to one per enqueue. The flag word and the queue give a request four states, and the figure draws every write that moves it between them.

```
    The states the flag word and the queue give one request
    ───────────────────────────────────────────────────────

            ⓐ flags ← 0
              │
              ▼
    ┌────────────────────┐  ⓑ linked  ┌────────────────────┐  ⓒ cancelled   ┌────────────────────┐
    │ fresh              │ ─────────▶ │ queued             │ ─────────────▶ │ queued, cancelled  │
    │ off the queue      │            │ on request_queue   │                │ on request_queue   │
    │ both bits clear    │            │ ACTIVE             │                │ ACTIVE, CANCELED   │
    └────────────────────┘            └─────────┬──────────┘                └─────────┬──────────┘
                                                │ ⓓ unlinked                          │ ⓓ unlinked,
                                                │                                     │ canceller woken
                                                ▼                                     │
                                      ┌────────────────────┐                          │
                                      │ retired            │ ◀────────────────────────┘
                                      │ off the queue      │ ──┐
                                      │ ACTIVE clear       │ ◀─┘ ⓒ cancelled after the unlink
                                      └────┬──────────▲────┘
                                           └──────────┘ ⓔ a second unlink returns at once

    ⓐ tb_cfg_request          ctl.c:552  flags ← 0, both bits clear before the enqueue
    ⓑ tb_cfg_request_enqueue  ctl.c:146  flags gains ACTIVE right after the link
    ⓒ tb_cfg_request_cancel   ctl.c:591  flags gains CANCELED, linked or not
    ⓓ tb_cfg_request_dequeue  ctl.c:162  flags loses ACTIVE right after the unlink
    ⓔ tb_cfg_request_dequeue  ctl.c:156  flags read with ACTIVE clear, nothing done
```

ⓐ [`tb_cfg_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L547) clears [`flags`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L92) before the enqueue. ⓑ [`tb_cfg_request_enqueue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L133) links the request and sets the active bit. ⓒ [`tb_cfg_request_cancel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L589) sets the cancelled bit, on a request still queued or on one already unlinked. ⓓ [`tb_cfg_request_dequeue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L151) unlinks an active request, clears its bit and wakes a canceller. ⓔ [`tb_cfg_request_dequeue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L151) returns without touching a request whose bit is already clear.

Dequeue therefore unlinks a request once per enqueue, however many times it runs, and wakes a canceller from inside the mutex that clears the bit.

### A frame goes to the first request that accepts it

A frame that reaches the queue is offered to the queued requests in submission order. The first whose [`match`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L87) callback accepts it copies the frame and has its work item scheduled. Three parts follow, the request-matching branch of [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445), then [`tb_cfg_request_find()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L174), then a figure of the two mutexes one lookup nests.

```c
/* drivers/thunderbolt/ctl.c:504 */
	/*
	 * The received packet will be processed only if there is an
	 * active request and that the packet is what is expected. This
	 * prevents packets such as replies coming after timeout has
	 * triggered from messing with the active requests.
	 */
	req = tb_cfg_request_find(pkg->ctl, pkg);

	trace_tb_rx(pkg->ctl->index, frame->eof, pkg->buffer, frame->size, !req);

	if (req) {
		if (req->copy(req, pkg))
			schedule_work(&req->work);
		tb_cfg_request_put(req);
	}

rx:
	tb_ctl_rx_submit(pkg);
```

[`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) processes a frame only if a queued request expects it, and its comment gives the reason. The lookup "prevents packets such as replies coming after timeout has triggered from messing with the active requests". A hit is handed to the request's own [`copy`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L89), and its work item is scheduled when that callback reports the request finished. [`tb_cfg_request_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L126) then drops the lookup's reference.

A frame no request accepts produces no log line. Its only record is the [`tb_rx`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/trace.h#L163) trace event, whose last argument is the negation of `req` and marks the frame as dropped. Either way the buffer goes back to the receive ring through [`tb_ctl_rx_submit()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L409). [`tb_cfg_request_find()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L174) asks the queued requests in list order and returns the first that accepts, with a reference taken on it.

```c
/* drivers/thunderbolt/ctl.c:173 */
static struct tb_cfg_request *
tb_cfg_request_find(struct tb_ctl *ctl, struct ctl_pkg *pkg)
{
	struct tb_cfg_request *req = NULL, *iter;

	mutex_lock(&pkg->ctl->request_queue_lock);
	list_for_each_entry(iter, &pkg->ctl->request_queue, list) {
		tb_cfg_request_get(iter);
		if (iter->match(iter, pkg)) {
			req = iter;
			break;
		}
		tb_cfg_request_put(iter);
	}
	mutex_unlock(&pkg->ctl->request_queue_lock);

	return req;
}
```

[`tb_cfg_request_find()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L174) calls [`tb_cfg_request_get()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L105) on each entry before its [`match`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L87) runs, and [`tb_cfg_request_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L126) on each that refuses. The request it returns therefore carries the only extra reference. The separate `iter` and the assignment to `req` on a hit follow commit 03941ed91c72 ("thunderbolt: Replace usage of found with dedicated list iterator variable"), so nothing reads the iterator after the loop.

The get and the put take [`tb_cfg_request_lock`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L78) while [`request_queue_lock`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L46) is held, which fixes the queue mutex as the outer one. Every match callback runs with the queue mutex held. The figure draws both brackets over a lookup of three queued requests whose third accepts the frame.

```
    The two mutexes one lookup nests, over a queue of three requests
    ────────────────────────────────────────────────────────────────

    time ────────────────────────────────────────────────────────────────────────────────▶
    request_queue_lock      ├─────────────────────────────────────────────────────────┤
    tb_cfg_request_lock       ├┤        ├┤        ├┤        ├┤        ├┤
    match callback               ├───┤               ├───┤               ├───┤
                            ╎                                                         ╎
    first request, kref   2 ╎ 3         2                                             ╎ 2
    second request, kref  2 ╎                     3         2                         ╎ 2
    third request, kref   2 ╎                                         3               ╎ 3, returned
```

[`request_queue_lock`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L46) brackets the whole lookup, and [`tb_cfg_request_lock`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L78) brackets each get and each put inside it. A count rises to 3 only while its request is being asked. The refusing requests leave with the count they entered with, and the accepting one leaves with one more.

So far, the reply has left the receive ring, found its request on the queue and reached that request's copy callback. A frame therefore goes to the first queued request that accepts it, and to no other.

### The configuration match compares type, route, size and sequence

A configuration reply is recognized by four comparisons against the request that caused it. An error frame is accepted before any of them runs. [`tb_cfg_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L856) is read whole, then [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L43) and [`tb_cfg_get_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L110), which say what the route comparison compares.

```c
/* drivers/thunderbolt/ctl.c:856 */
static bool tb_cfg_match(const struct tb_cfg_request *req,
			 const struct ctl_pkg *pkg)
{
	u64 route = tb_cfg_get_route(pkg->buffer) & ~BIT_ULL(63);

	if (pkg->frame.eof == TB_CFG_PKG_ERROR)
		return true;

	if (pkg->frame.eof != req->response_type)
		return false;
	if (route != tb_cfg_get_route(req->request))
		return false;
	if (pkg->frame.size != req->response_size)
		return false;

	if (pkg->frame.eof == TB_CFG_PKG_READ ||
	    pkg->frame.eof == TB_CFG_PKG_WRITE) {
		const struct cfg_read_pkg *req_hdr = req->request;
		const struct cfg_read_pkg *res_hdr = pkg->buffer;

		if (req_hdr->addr.seq != res_hdr->addr.seq)
			return false;
	}

	return true;
}
```

[`tb_cfg_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L856) returns true for a [`TB_CFG_PKG_ERROR`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L34) frame before it compares a route. An error frame from any router is therefore taken by the first queued request whose match accepts error frames. Every other frame must carry the request's [`response_type`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L85), its route and exactly its [`response_size`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L84).

A [`TB_CFG_PKG_READ`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L32) or [`TB_CFG_PKG_WRITE`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L33) frame must also echo the sequence number. Both headers are read as a [`struct cfg_read_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L60), so the same code reads [`seq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L55) from a read request and from a write reply. A reset reply carries no address dword and is paired on type, route and size alone. The route comes from [`tb_cfg_get_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L110), which reads the route fields of [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L43).

```c
/* drivers/thunderbolt/tb_msgs.h:43 */
struct tb_cfg_header {
	u32 route_hi:22;
	u32 unknown:10; /* highest order bit is set on replies */
	u32 route_lo;
} __packed;
/* drivers/thunderbolt/ctl.h:110 */
static inline u64 tb_cfg_get_route(const struct tb_cfg_header *header)
{
	return (u64) header->route_hi << 32 | header->route_lo;
}
```

[`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L43) splits the route across the 22-bit [`route_hi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L44) and [`route_lo`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L46), and its comment puts the reply's mark in the top bit of [`unknown`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L45). [`tb_cfg_get_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L110) assembles the value from the two route fields alone, so its bit 63 is already clear. Clearing that bit with [`BIT_ULL()`](https://elixir.bootlin.com/linux/v7.2/source/include/vdso/bits.h#L8) in the match therefore changes nothing.

The configuration match therefore accepts any error frame at once, and compares type, route, size and, for reads and writes, the sequence number.

### The configuration copy records a verdict before moving bytes

The copy stores the verdict of the header checks before it moves any byte, because a matched frame is not yet known to be well formed. The reply's bytes move only when the checks passed. [`tb_cfg_copy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L883) is read whole, then the stage of the packet parser it calls, [`decode_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L245) and [`parse_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L263).

```c
/* drivers/thunderbolt/ctl.c:883 */
static bool tb_cfg_copy(struct tb_cfg_request *req, const struct ctl_pkg *pkg)
{
	struct tb_cfg_result res;

	/* Now make sure it is in expected format */
	res = parse_header(pkg, req->response_size, req->response_type,
			   tb_cfg_get_route(req->request));
	if (!res.err)
		memcpy(req->response, pkg->buffer, req->response_size);

	req->result = res;

	/* Always complete when first response is received */
	return true;
}
```

[`tb_cfg_copy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L883) hands [`parse_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L263) the size and type the request expects and the route it was sent to. It calls [`memcpy()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/fortify-string.h#L640) for [`response_size`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L84) bytes only when the verdict carries no error. The verdict is stored in [`result`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L94) either way, and the function returns true, following its comment "Always complete when first response is received". [`parse_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L263) diverts an error frame to [`decode_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L245), which the file defines just above it.

```c
/* drivers/thunderbolt/ctl.c:245 */
static struct tb_cfg_result decode_error(const struct ctl_pkg *response)
{
	struct cfg_error_pkg *pkg = response->buffer;
	struct tb_cfg_result res = { 0 };
	res.response_route = tb_cfg_get_route(&pkg->header);
	res.response_port = 0;
	res.err = check_header(response, sizeof(*pkg), TB_CFG_PKG_ERROR,
			       tb_cfg_get_route(&pkg->header));
	if (res.err)
		return res;

	res.err = 1;
	res.tb_error = pkg->error;
	res.response_port = pkg->port;
	return res;

}

static struct tb_cfg_result parse_header(const struct ctl_pkg *pkg, u32 len,
					 enum tb_cfg_pkg_type type, u64 route)
{
	struct tb_cfg_header *header = pkg->buffer;
	struct tb_cfg_result res = { 0 };

	if (pkg->frame.eof == TB_CFG_PKG_ERROR)
		return decode_error(pkg);

	res.response_port = 0; /* will be updated later for cfg_read/write */
	res.response_route = tb_cfg_get_route(header);
	res.err = check_header(pkg, len, type, route);
	return res;
}
```

[`decode_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L245) checks the error packet against its own size and type, then sets [`err`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L42) to 1. It stores the router's code in [`tb_error`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L43) and the reporting adapter in [`response_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L34), and is the only place the driver sets that member to 1. For any other frame [`parse_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L263) records the route, leaves [`response_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L34) at 0, and returns whatever [`check_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L195) made of the frame.

A configuration reply therefore reaches its waiter as a verdict first, and its bytes move only when that verdict is 0.

### The work item signals, unlinks, then drops a reference

Every request finishes in its work item, which calls the submitter's callback unless the request was cancelled. The item then unlinks the request and drops the queue's reference. [`tb_cfg_request_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L524) is read whole, then [`schedule_work()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/workqueue.h#L758) with its kerneldoc, then the lookup's dependence on the order of the unlink and the drop.

```c
/* drivers/thunderbolt/ctl.c:524 */
static void tb_cfg_request_work(struct work_struct *work)
{
	struct tb_cfg_request *req = container_of(work, typeof(*req), work);

	if (!test_bit(TB_CFG_REQUEST_CANCELED, &req->flags))
		req->callback(req->callback_data);

	tb_cfg_request_dequeue(req);
	tb_cfg_request_put(req);
}
```

[`tb_cfg_request_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L524) calls [`callback`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L90) only while [`TB_CFG_REQUEST_CANCELED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L99) is clear. That test keeps a completion on a waiter's departed stack frame from being signalled. [`tb_cfg_request_dequeue()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L151) and [`tb_cfg_request_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L126) then run on every pass, in that order.

Three functions schedule the item, [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) after a reply matched, [`tb_cfg_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L547) for a request without a reply buffer, and [`tb_cfg_request_cancel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L589) when the waiter cancels. [`schedule_work()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/workqueue.h#L758) puts the item on the system per-CPU workqueue, and its kerneldoc covers an item already queued.

```c
/* include/linux/workqueue.h:744 */
/**
 * schedule_work - put work task in per-CPU workqueue
 * @work: job to be done
 *
 * Returns %false if @work was already on the system per-CPU workqueue and
 * %true otherwise.
 *
 * This puts a job in the system per-CPU workqueue if it was not already
 * queued and leaves it in the same position on the system per-CPU
 * workqueue otherwise.
 *
 * Shares the same memory-ordering properties of queue_work(), cf. the
 * DocBook header of queue_work().
 */
static inline bool schedule_work(struct work_struct *work)
{
	return queue_work(system_percpu_wq, work);
}
```

[`schedule_work()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/workqueue.h#L758) returns false and leaves an item that is already queued in place. Two schedulings before the item runs therefore produce one pass. According to [`Documentation/core-api/workqueue.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/core-api/workqueue.rst), a work item under its conditions "is guaranteed to be executed by at most one worker system-wide at any given time". Two passes of this item never overlap.

Commit 0f73628e9da1 describes a second pass as possible, and its guard makes the unlink safe to repeat. The [`tb_cfg_request_put()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L126) after the unlink has no such guard, and each pass drops one reference. The lookup depends on that order, as the head of [`tb_cfg_request_find()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L174) shows.

```c
/* drivers/thunderbolt/ctl.c:178 */
	mutex_lock(&pkg->ctl->request_queue_lock);
	list_for_each_entry(iter, &pkg->ctl->request_queue, list) {
		tb_cfg_request_get(iter);
		if (iter->match(iter, pkg)) {
```

[`tb_cfg_request_find()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L174) takes its reference under [`request_queue_lock`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L46) on a request it sees on the queue. A linked request still holds the queue's reference, because each pass unlinks under that mutex before it drops the reference. According to [`Documentation/core-api/kref.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/core-api/kref.rst), calling [`kref_get()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/kref.h#L43) on an item taken off a list "violates rule 3 because you are not already holding a valid pointer". The document's answer is "You must add a mutex (or some other lock)."

The work item therefore finishes every request in one order, the callback, then the unlink, then the drop of the queue's reference.

### The synchronous caller sleeps on a completion on its stack

A builder that needs the reply blocks in [`tb_cfg_request_sync()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L616). The function turns the asynchronous submission into a sleep on a completion declared in its own stack frame. [`tb_cfg_request_complete()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L597) and the kerneldoc and body of [`tb_cfg_request_sync()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L616) come first, then [`flush_work()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/workqueue.c#L4392), then a table of the builders that call it.

```c
/* drivers/thunderbolt/ctl.c:597 */
static void tb_cfg_request_complete(void *data)
{
	complete(data);
}

/**
 * tb_cfg_request_sync() - Start control request and wait until it completes
 * @ctl: Control channel to use
 * @req: Request to start
 * @timeout_msec: Timeout how long to wait @req to complete
 *
 * Starts a control request and waits until it completes. If timeout
 * triggers the request is canceled before function returns. Note the
 * caller needs to make sure only one message for given switch is active
 * at a time.
 *
 * Return: &struct tb_cfg_result with non-zero @err field if error
 * has occurred.
 */
struct tb_cfg_result tb_cfg_request_sync(struct tb_ctl *ctl,
					 struct tb_cfg_request *req,
					 int timeout_msec)
{
	unsigned long timeout = msecs_to_jiffies(timeout_msec);
	struct tb_cfg_result res = { 0 };
	DECLARE_COMPLETION_ONSTACK(done);
	int ret;

	ret = tb_cfg_request(ctl, req, tb_cfg_request_complete, &done);
	if (ret) {
		res.err = ret;
		return res;
	}

	if (!wait_for_completion_timeout(&done, timeout))
		tb_cfg_request_cancel(req, -ETIMEDOUT);

	flush_work(&req->work);

	return req->result;
}
```

[`tb_cfg_request_sync()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L616) converts the timeout with [`msecs_to_jiffies()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/jiffies.h#L550) and declares the completion with [`DECLARE_COMPLETION_ONSTACK()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/completion.h#L68). It passes the completion's address as the callback data, so [`tb_cfg_request_complete()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L597) calls [`complete()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/sched/completion.c#L50) knowing nothing about requests. A submission that fails queues nothing, and the function returns that error in [`err`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L42) of an otherwise zeroed result.

The kerneldoc states a rule this layer leaves to its callers. In its words, "the caller needs to make sure only one message for given switch is active at a time", and no part of the queue is indexed by route. After a timeout the function cancels with -ETIMEDOUT, waits in [`flush_work()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/workqueue.c#L4392) for the work item, and returns a copy of [`result`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L94).

Those two calls answer a warning in [`Documentation/scheduler/completion.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/scheduler/completion.rst). A waiter with a timeout must be sure that "memory de-allocation does not happen until all related activities (complete() or reinit_completion()) have taken place". [`flush_work()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/workqueue.c#L4392) waits for the last queueing of an item, and its kerneldoc limits that to an item not requeued since the flush began.

```c
/* kernel/workqueue.c:4381 */
/**
 * flush_work - wait for a work to finish executing the last queueing instance
 * @work: the work to flush
 *
 * Wait until @work has finished execution.  @work is guaranteed to be idle
 * on return if it hasn't been requeued since flush started.
 *
 * Return:
 * %true if flush_work() waited for the work to finish execution,
 * %false if it was already idle.
 */
bool flush_work(struct work_struct *work)
{
	might_sleep();
	return __flush_work(work, false);
}
EXPORT_SYMBOL_GPL(flush_work);
```

[`flush_work()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/workqueue.c#L4392) returns once the pass queued when it started has finished. The pass that [`tb_cfg_request_cancel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L589) scheduled has therefore run to its end when the result is copied. Seven functions call the synchronous path, six in the files the table names and one that is ICM-only.

| builder | call | timeout it passes |
|---|---|---|
| [`tb_cfg_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L911) | [`ctl.c:933`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L933) | the channel's [`timeout_msec`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L50) |
| [`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) | [`ctl.c:993`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L993) | the one its caller passed |
| [`tb_cfg_write_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1030) | [`ctl.c:1069`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1069) | the one its caller passed |
| [`__tb_xdomain_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L180) | [`xdomain.c:201`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L201) | the one its caller passed |
| [`dma_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L88) | [`dma_port.c:118`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L118) | the one its caller passed |
| [`dma_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L129) | [`dma_port.c:161`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L161) | the one its caller passed |

So far, the waiter has slept on its stack completion and woken to a stored result or to an expired timeout. The synchronous caller therefore sleeps on a completion on its own stack and returns only once the work item is done with it.

### A timeout cancels the request and waits for the unlink

A waiter that gives up cannot return while its request may still be reached. It marks the request cancelled, pushes the work item through, and sleeps until the request is unlinked. [`tb_cfg_request_cancel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L589) is read whole, then a figure of the window in which the receive path can still act.

```c
/* drivers/thunderbolt/ctl.c:581 */
/**
 * tb_cfg_request_cancel() - Cancel a control request
 * @req: Request to cancel
 * @err: Error to assign to the request
 *
 * This function can be used to cancel ongoing request. It will wait
 * until the request is not active anymore.
 */
void tb_cfg_request_cancel(struct tb_cfg_request *req, int err)
{
	set_bit(TB_CFG_REQUEST_CANCELED, &req->flags);
	schedule_work(&req->work);
	wait_event(tb_cfg_request_cancel_queue, !tb_cfg_request_is_active(req));
	req->result.err = err;
}
```

[`tb_cfg_request_cancel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L589) sets [`TB_CFG_REQUEST_CANCELED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L99) before it schedules anything, so the next pass of the work item skips the callback. [`wait_event()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/wait.h#L345) then sleeps uninterruptibly, with no timeout of its own, until [`tb_cfg_request_is_active()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L168) reports false. Only the dequeue makes that change, and it wakes the sleeper from inside the queue mutex.

The caller's error is written into [`err`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L42) after the unlink, and the waiter copies the result after [`flush_work()`](https://elixir.bootlin.com/linux/v7.2/source/kernel/workqueue.c#L4392). A receive path that found the request before the unlink holds its own reference and runs the copy outside the queue mutex. It can therefore store its verdict after the error is written, and the figure places those actions against the cancel's sleep.

```
    A timeout, the cancel's sleep and the receive path acting on one request
    ────────────────────────────────────────────────────────────────────────

    time ──────────────────────────────────────────────────────────────────────────────────▶
    waiter          ⓵ wait ends
                    ⓶ CANCELED      ├───────────────────────────────────────────┤ ⓶ err ← -ETIMEDOUT
                                                ▲                           ▲
    receive path                                │ ⓷ copy stores a verdict   │
    work item                                                               │ ⓸ unlinked, waiter woken

    a lookup that found the request before ⓸ can also run ⓷ after the err write

    ⓵ tb_cfg_request_sync    ctl.c:631  the wait for the completion returns 0
    ⓶ tb_cfg_request_cancel  ctl.c:591  CANCELED set and work scheduled, then err written after the sleep
    ⓷ tb_ctl_rx_callback     ctl.c:515  copy stores the reply's verdict in result
    ⓸ tb_cfg_request_work    ctl.c:531  the unlink clears ACTIVE and wakes the sleeper
```

⓵ [`tb_cfg_request_sync()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L616) sees the wait end without a completion. ⓶ [`tb_cfg_request_cancel()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L589) sets the cancelled bit, schedules the work item and sleeps, then writes -ETIMEDOUT into [`err`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L42). ⓷ [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445), holding the reference its lookup took, lets the copy store a verdict. ⓸ [`tb_cfg_request_work()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L524) unlinks the request, which clears the active bit and wakes the sleeper.

A copy that began before the unlink can still land after the error is written. A timeout therefore cancels the request and returns only after the unlink.

### The raw read retries with a fresh sequence number

A configuration read tries a silent router up to four times, and each try carries a new sequence number. A late reply to an earlier try therefore cannot satisfy a later one. [`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) is read in three pieces, the first two here with the packet definitions and [`TB_CTL_RETRIES`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L22), and a figure of four tries follows.

| piece | lines | stage |
|---|---|---|
| ① | [`ctl.c:956-972`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) | builds the read packet and the reply buffer on the stack |
| ② | [`ctl.c:973-1003`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L973) | tries up to four times, one request and one sequence number per try |
| ③ | [`ctl.c:1004-1012`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1004) | checks the echoed address and copies the data |

Piece ① of [`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) opens under a kerneldoc saying the function leaves the router's error untranslated. It declares both packets on the stack.

```c
/* drivers/thunderbolt/ctl.c:940 */
/**
 * tb_cfg_read_raw() - read from config space into buffer
 * @ctl: Pointer to the control channel
 * @buffer: Buffer where the data is read
 * @route: Route string of the router
 * @port: Port number when reading from %TB_CFG_PORT, %0 otherwise
 * @space: Config space selector
 * @offset: Dword word offset of the register to start reading
 * @length: Number of dwords to read
 * @timeout_msec: Timeout in ms how long to wait for the response
 *
 * Reads from router config space without translating the possible error.
 *
 * Return: &struct tb_cfg_result with non-zero @err field if error
 * has occurred.
 */
struct tb_cfg_result tb_cfg_read_raw(struct tb_ctl *ctl, void *buffer,
		u64 route, u32 port, enum tb_cfg_space space,
		u32 offset, u32 length, int timeout_msec)
{
	struct tb_cfg_result res = { 0 };
	struct cfg_read_pkg request = {
		.header = tb_cfg_make_header(route),
		.addr = {
			.port = port,
			.space = space,
			.offset = offset,
			.length = length,
		},
	};
	struct cfg_write_pkg reply;
	int retries = 0;

```

[`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) builds a [`struct cfg_read_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L60) whose header carries the route from [`tb_cfg_make_header()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L115). Its address dword carries the four addressing arguments and leaves [`seq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L55) and [`zero`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L56) at 0. The reply is a [`struct cfg_write_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L66), because a read is answered by the packet shape that carries data. The definitions of those packets and of [`struct tb_cfg_address`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L50) give the widths the loop depends on, and [`TB_CTL_RETRIES`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L22) gives the number of tries.

```c
/* drivers/thunderbolt/tb_msgs.h:50 */
struct tb_cfg_address {
	u32 offset:13; /* in dwords */
	u32 length:6; /* in dwords */
	u32 port:6;
	enum tb_cfg_space space:2;
	u32 seq:2; /* sequence number  */
	u32 zero:3;
} __packed;

/* TB_CFG_PKG_READ, response for TB_CFG_PKG_WRITE */
struct cfg_read_pkg {
	struct tb_cfg_header header;
	struct tb_cfg_address addr;
} __packed;

/* TB_CFG_PKG_WRITE, response for TB_CFG_PKG_READ */
struct cfg_write_pkg {
	struct tb_cfg_header header;
	struct tb_cfg_address addr;
	u32 data[64]; /* maximum size, tb_cfg_address.length has 6 bits */
} __packed;
/* drivers/thunderbolt/ctl.c:22 */
#define TB_CTL_RETRIES		4
```

[`struct tb_cfg_address`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L50) packs [`offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L51), [`length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L52), [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L53), [`space`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L54), [`seq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L55) and [`zero`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L56) into one dword. [`struct cfg_read_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L60) is a [`header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L61) followed by that dword in [`addr`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L62). [`struct cfg_write_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L66) adds [`data`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L69), 64 dwords for the at most 63 a six-bit length can name. [`TB_CTL_RETRIES`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L22) is 4, the number of values the two bits of [`seq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L55) can hold, and piece ② of [`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) is the loop it bounds.

```c
/* drivers/thunderbolt/ctl.c:973 */
	while (retries < TB_CTL_RETRIES) {
		struct tb_cfg_request *req;

		req = tb_cfg_request_alloc();
		if (!req) {
			res.err = -ENOMEM;
			return res;
		}

		request.addr.seq = retries++;

		req->match = tb_cfg_match;
		req->copy = tb_cfg_copy;
		req->request = &request;
		req->request_size = sizeof(request);
		req->request_type = TB_CFG_PKG_READ;
		req->response = &reply;
		req->response_size = 12 + 4 * length;
		req->response_type = TB_CFG_PKG_READ;

		res = tb_cfg_request_sync(ctl, req, timeout_msec);

		tb_cfg_request_put(req);

		if (res.err != -ETIMEDOUT)
			break;

		/* Wait a bit (arbitrary time) until we send a retry */
		usleep_range(10, 100);
	}

```

[`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) writes the try number into [`seq`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L55) and advances the counter in one expression. Try 0 therefore sends sequence 0 and try 3 sends sequence 3. Each try points a fresh request at the same two stack buffers and the configuration pair, and expects `12 + 4 * length` bytes back. The builder's reference is dropped before the loop decides whether to go round again.

The loop ends on every result except -ETIMEDOUT, so a refusal, a stopped channel or a failed check reaches the caller after one try. Only silence is retried, after a pause of 10 to 100 microseconds from [`usleep_range()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/delay.h#L75). The comment above it calls the pause an arbitrary time, and the pause also follows the fourth timeout.

Commit d7f781bfdbf4 introduced four tries, and commit 61ec15e5534b ("thunderbolt: Disable retry logic for intra-domain control packets") cut them to one. Commit 641cdbea7635 ("thunderbolt: Enable retry logic for intra-domain control packets") restored four. Its message says response packets "are lost sometimes within the stipulated time", and the figure draws a router that answers the first try late.

```
    Four tries of one read against a router that answers the first one late
    ───────────────────────────────────────────────────────────────────────
    time ↓
    reading thread                       │ router
    ─────────────────────────────────────┼──────────────────────────────────
    try 0 sends seq 0 ──────────────────▶│ reply delayed
    wait expires, request cancelled      │
    try 1 sends seq 1 ──────────────────▶│
      late reply with seq 0 ◀────────────│ reply to try 0 arrives
      match refuses it, frame dropped    │
    wait expires again                   │ reply to try 1 lost
    try 2 sends seq 2 ──────────────────▶│
      reply with seq 2 ◀─────────────────│ reply to try 2
      accepted, loop left                │

    TB_CTL_RETRIES is 4 and seq has two bits, so the tries of one call
    carry the sequence numbers 0 to 3 and no two of them share one
```

[`tb_cfg_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L856) refuses the late reply because its sequence number is 0 while the queued request's is 1. No other request expects it, so the lookup drops the frame. The raw read therefore tries four times at most, and a reply to an earlier try fails the sequence comparison.

### The read copies data only after the echoed address agrees

A reply that matched and parsed is still checked against the address the caller named. Only then do its data dwords reach the caller's buffer. Piece ③ of [`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) comes first, then [`check_config_address()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L223), the packet layer's check it relies on.

```c
/* drivers/thunderbolt/ctl.c:1004 */
	if (res.err)
		return res;

	res.response_port = reply.addr.port;
	res.err = check_config_address(reply.addr, space, offset, length);
	if (!res.err)
		memcpy(buffer, &reply.data, 4 * length);
	return res;
}
```

[`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) copies the reply's [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L53) into [`response_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L34) before checking anything. It copies `4 * length` bytes into the caller's buffer only when [`check_config_address()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L223) agrees, so a caller that receives an error finds its buffer as it left it. [`check_config_address()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L223) compares four of the address fields and explains in a comment why it leaves the port alone.

```c
/* drivers/thunderbolt/ctl.c:223 */
static int check_config_address(struct tb_cfg_address addr,
				enum tb_cfg_space space, u32 offset,
				u32 length)
{
	if (WARN(addr.zero, "addr.zero is %#x\n", addr.zero))
		return -EIO;
	if (WARN(space != addr.space, "wrong space (expected %x, got %x\n)",
			space, addr.space))
		return -EIO;
	if (WARN(offset != addr.offset, "wrong offset (expected %x, got %x\n)",
			offset, addr.offset))
		return -EIO;
	if (WARN(length != addr.length, "wrong space (expected %x, got %x\n)",
			length, addr.length))
		return -EIO;
	/*
	 * We cannot check addr->port as it is set to the upstream port of the
	 * sender.
	 */
	return 0;
}
```

[`check_config_address()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L223) requires [`zero`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L56) to be 0, and [`space`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L54), [`offset`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L51) and [`length`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L52) to be echoed. Each test goes through a [`WARN()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bug.h#L163) that returns -EIO. Its closing comment says the port "is set to the upstream port of the sender", which is the value the raw read keeps.

Data therefore moves into the caller's buffer only after the reply's address dword agrees in every field the check compares.

### The raw write copies its payload once for every try

A write copies its payload into the outgoing packet once, before the loop, and every try resends the same bytes. It differs from a read only in which packet carries the data. [`tb_cfg_write_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1030) is read in the three pieces outlined below.

| piece | lines | stage |
|---|---|---|
| ❶ | [`ctl.c:1030-1048`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1030) | builds the write packet with its payload and the reply buffer |
| ❷ | [`ctl.c:1049-1079`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1049) | tries up to four times, as the read does |
| ❸ | [`ctl.c:1080-1086`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1080) | checks the echoed address |

Piece ❶ of [`tb_cfg_write_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1030) opens under its kerneldoc and copies the payload into the packet before the loop begins.

```c
/* drivers/thunderbolt/ctl.c:1014 */
/**
 * tb_cfg_write_raw() - write from buffer into config space
 * @ctl: Pointer to the control channel
 * @buffer: Data to write
 * @route: Route string of the router
 * @port: Port number when writing to %TB_CFG_PORT, %0 otherwise
 * @space: Config space selector
 * @offset: Dword word offset of the register to start writing
 * @length: Number of dwords to write
 * @timeout_msec: Timeout in ms how long to wait for the response
 *
 * Writes to router config space without translating the possible error.
 *
 * Return: &struct tb_cfg_result with non-zero @err field if error
 * has occurred.
 */
struct tb_cfg_result tb_cfg_write_raw(struct tb_ctl *ctl, const void *buffer,
		u64 route, u32 port, enum tb_cfg_space space,
		u32 offset, u32 length, int timeout_msec)
{
	struct tb_cfg_result res = { 0 };
	struct cfg_write_pkg request = {
		.header = tb_cfg_make_header(route),
		.addr = {
			.port = port,
			.space = space,
			.offset = offset,
			.length = length,
		},
	};
	struct cfg_read_pkg reply;
	int retries = 0;

	memcpy(&request.data, buffer, length * 4);

```

[`tb_cfg_write_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1030) declares the data-carrying packet as its request and the header-and-address packet as its reply, the mirror of the read. It fills [`data`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L69) with one [`memcpy()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/fortify-string.h#L640) of `length * 4` bytes. Piece ❷ of [`tb_cfg_write_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1030) is the read's loop with the two sizes exchanged.

```c
/* drivers/thunderbolt/ctl.c:1049 */
	while (retries < TB_CTL_RETRIES) {
		struct tb_cfg_request *req;

		req = tb_cfg_request_alloc();
		if (!req) {
			res.err = -ENOMEM;
			return res;
		}

		request.addr.seq = retries++;

		req->match = tb_cfg_match;
		req->copy = tb_cfg_copy;
		req->request = &request;
		req->request_size = 12 + 4 * length;
		req->request_type = TB_CFG_PKG_WRITE;
		req->response = &reply;
		req->response_size = sizeof(reply);
		req->response_type = TB_CFG_PKG_WRITE;

		res = tb_cfg_request_sync(ctl, req, timeout_msec);

		tb_cfg_request_put(req);

		if (res.err != -ETIMEDOUT)
			break;

		/* Wait a bit (arbitrary time) until we send a retry */
		usleep_range(10, 100);
	}

```

[`tb_cfg_write_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1030) sets [`request_size`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L81) to `12 + 4 * length`, where the read computes its reply size that way. It fixes [`response_size`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L84) at the size of a reply that carries no data. The sequence number per try, the timeout test and the pause repeat the read's, and piece ❸ of [`tb_cfg_write_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1030) checks the echoed address.

```c
/* drivers/thunderbolt/ctl.c:1080 */
	if (res.err)
		return res;

	res.response_port = reply.addr.port;
	res.err = check_config_address(reply.addr, space, offset, length);
	return res;
}
```

[`tb_cfg_write_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1030) keeps the reply's port and returns the verdict of [`check_config_address()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L223) as the write's result. A reply naming another address therefore fails the write with -EIO.

So far, a raw read or write has turned one call into up to four requests. Its result carries 0, 1 or a negative errno. The raw write therefore resends one copied payload on each try and checks the echoed address as the read does.

### The cooked entry points fold the result into an errno

Two thin entry points turn the three-valued result into an errno and supply the channel's own timeout. Callers above this layer work in errnos, and the wrappers reach the layer only through these two. [`tb_cfg_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1111) and [`tb_cfg_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1137) are read whole, then the chain that gives [`timeout_msec`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L50) its 100 ms.

```c
/* drivers/thunderbolt/ctl.c:1111 */
int tb_cfg_read(struct tb_ctl *ctl, void *buffer, u64 route, u32 port,
		enum tb_cfg_space space, u32 offset, u32 length)
{
	struct tb_cfg_result res = tb_cfg_read_raw(ctl, buffer, route, port,
			space, offset, length, ctl->timeout_msec);
	switch (res.err) {
	case 0:
		/* Success */
		break;

	case 1:
		/* Thunderbolt error, tb_error holds the actual number */
		return tb_cfg_get_error(ctl, space, &res);

	case -ETIMEDOUT:
		tb_ctl_warn(ctl, "%llx: timeout reading config space %u from %#x\n",
			    route, space, offset);
		break;

	default:
		WARN(1, "tb_cfg_read: %d\n", res.err);
		break;
	}
	return res.err;
}
/* drivers/thunderbolt/ctl.c:1137 */
int tb_cfg_write(struct tb_ctl *ctl, const void *buffer, u64 route, u32 port,
		 enum tb_cfg_space space, u32 offset, u32 length)
{
	struct tb_cfg_result res = tb_cfg_write_raw(ctl, buffer, route, port,
			space, offset, length, ctl->timeout_msec);
	switch (res.err) {
	case 0:
		/* Success */
		break;

	case 1:
		/* Thunderbolt error, tb_error holds the actual number */
		return tb_cfg_get_error(ctl, space, &res);

	case -ETIMEDOUT:
		tb_ctl_warn(ctl, "%llx: timeout writing config space %u to %#x\n",
			    route, space, offset);
		break;

	default:
		WARN(1, "tb_cfg_write: %d\n", res.err);
		break;
	}
	return res.err;
}
```

[`tb_cfg_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1111) and [`tb_cfg_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1137) pass [`timeout_msec`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L50) to the raw helper and return 0 on success. A refusal goes to [`tb_cfg_get_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1088), and a timeout is logged through [`tb_ctl_warn`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L64) with the route, the space and the offset. Any other value trips the [`WARN()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bug.h#L163) of the default case.

The raw helpers return several such values. A stopped channel gives -ENOTCONN, a failed allocation -ENOMEM, and a failed address check -EIO. [`TB_TIMEOUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L19) is the software connection manager's timeout, which [`tb_probe()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L3374) passes to [`tb_domain_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/domain.c#L377) and that function hands to [`tb_ctl_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L653).

```c
/* drivers/thunderbolt/tb.c:19 */
#define TB_TIMEOUT		100	/* ms */
/* drivers/thunderbolt/tb.c:3374 */
struct tb *tb_probe(struct tb_nhi *nhi)
{
	struct tb_cm *tcm;
	struct tb *tb;

	tb = tb_domain_alloc(nhi, TB_TIMEOUT, sizeof(*tcm));
	if (!tb)
		return NULL;
/* drivers/thunderbolt/domain.c:404 */
	tb->ctl = tb_ctl_alloc(nhi, tb->index, timeout_msec, tb_domain_event_cb, tb);
	if (!tb->ctl)
		goto err_destroy_wq;
/* drivers/thunderbolt/ctl.c:661 */
	ctl->nhi = nhi;
	ctl->index = index;
	ctl->timeout_msec = timeout_msec;
```

[`TB_TIMEOUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L19) is 100 ms, and [`tb_ctl_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L653) stores it in [`timeout_msec`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L50). The cooked helpers, [`tb_cfg_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L911) and [`tb_cfg_get_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1173) pass that default. Commit 7f0a34d7900b introduced the value, recording that "The USB4 spec recommends 10 ms +- 1 ms but we use slightly larger value (100 ms)".

A cooked read of a silent router waits four times 100 ms, with four pauses, before it logs the timeout. The cooked entry points therefore fold the three-valued result into an errno.

### A router's refusal becomes one of four errnos

A refusal becomes the errno its caller can act on. One combination, an adapter-space access that an unimplemented adapter refuses, returns before anything is logged. A table of the four outcomes comes first, then [`tb_cfg_get_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1088) whole, then two callers that act on its values.

| refusal code | space | errno | logging |
|---|---|---|---|
| [`TB_CFG_ERROR_INVALID_CONFIG_SPACE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L25) | [`TB_CFG_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L17) | -ENODEV | none |
| [`TB_CFG_ERROR_LOCK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L31) | any | -EACCES | a warning from [`tb_cfg_print_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L278) |
| [`TB_CFG_ERROR_PORT_NOT_CONNECTED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L23) | any | -ENOTCONN | none, [`tb_cfg_print_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L278) returns silently |
| any other code | any | -EIO | by [`tb_cfg_print_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L278), at the code's severity |

[`tb_cfg_get_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1088) implements the table, and a comment explains its first test.

```c
/* drivers/thunderbolt/ctl.c:1088 */
static int tb_cfg_get_error(struct tb_ctl *ctl, enum tb_cfg_space space,
			    const struct tb_cfg_result *res)
{
	/*
	 * For unimplemented ports access to port config space may return
	 * TB_CFG_ERROR_INVALID_CONFIG_SPACE (alternatively their type is
	 * set to TB_TYPE_INACTIVE). In the former case return -ENODEV so
	 * that the caller can mark the port as disabled.
	 */
	if (space == TB_CFG_PORT &&
	    res->tb_error == TB_CFG_ERROR_INVALID_CONFIG_SPACE)
		return -ENODEV;

	tb_cfg_print_error(ctl, space, res);

	if (res->tb_error == TB_CFG_ERROR_LOCK)
		return -EACCES;
	if (res->tb_error == TB_CFG_ERROR_PORT_NOT_CONNECTED)
		return -ENOTCONN;

	return -EIO;
}
```

[`tb_cfg_get_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1088) returns -ENODEV for an adapter-space access refused with [`TB_CFG_ERROR_INVALID_CONFIG_SPACE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L25). Its comment gives the reason, so "that the caller can mark the port as disabled". Every other refusal passes through [`tb_cfg_print_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L278). [`TB_CFG_ERROR_LOCK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L31) then becomes -EACCES, [`TB_CFG_ERROR_PORT_NOT_CONNECTED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L23) becomes -ENOTCONN, and the rest become -EIO.

Commit d94dcbb10183 ("thunderbolt: Do not fail adding switch if some port is not implemented") introduced the function with the -ENODEV case. Commit 80e7c5dd1ee0 ("thunderbolt: Handle ERR_LOCK notification") added -EACCES, and commit 463e48fa5448 ("thunderbolt: Return -ENOTCONN when ERR_CONN is received") added -ENOTCONN. [`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) and [`usb4_switch_nvm_authenticate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L680) are two callers that act on those values.

```c
/* drivers/thunderbolt/switch.c:711 */
	res = tb_port_read(port, &port->config, TB_CFG_PORT, 0, 8);
	if (res) {
		if (res == -ENODEV) {
			tb_dbg(port->sw->tb, " Port %d: not implemented\n",
			       port->port);
			port->disabled = true;
			return 0;
		}
		return res;
	}
/* drivers/thunderbolt/usb4.c:684 */
	ret = usb4_switch_op(sw, USB4_SWITCH_OP_NVM_AUTH, NULL, NULL);
	switch (ret) {
	/*
	 * The router is power cycled once NVM_AUTH is started so it is
	 * expected to get any of the following errors back.
	 */
	case -EACCES:
	case -ENOTCONN:
	case -ETIMEDOUT:
		return 0;

	default:
		return ret;
	}
```

[`tb_init_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L700) marks the adapter disabled and returns 0 on -ENODEV, the use the comment in [`tb_cfg_get_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1088) names. [`usb4_switch_nvm_authenticate()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/usb4.c#L680) accepts -EACCES and -ENOTCONN as well as -ETIMEDOUT. In its comment's words, "The router is power cycled once NVM_AUTH is started".

The -ENODEV case never reaches the logger, and the -ENOTCONN case reaches it and stays silent. A router's refusal therefore reaches its caller as -ENODEV, -EACCES, -ENOTCONN or -EIO.

### The log severity follows the refusal code

The logger answers a refusal with silence, one debug line or a backtrace, chosen by the refusal code. A refusal can mean a removal in progress, a router with partial register blocks, or a route the driver built wrong. The channel's print macros come first, then [`tb_cfg_print_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L278) whole, and [`tb_ctl_WARN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L58) opens the run of macros.

```c
/* drivers/thunderbolt/ctl.c:58 */
#define tb_ctl_WARN(ctl, format, arg...) \
	dev_WARN((ctl)->nhi->dev, format, ## arg)

#define tb_ctl_err(ctl, format, arg...) \
	dev_err((ctl)->nhi->dev, format, ## arg)

#define tb_ctl_warn(ctl, format, arg...) \
	dev_warn((ctl)->nhi->dev, format, ## arg)

#define tb_ctl_info(ctl, format, arg...) \
	dev_info((ctl)->nhi->dev, format, ## arg)

#define tb_ctl_dbg(ctl, format, arg...) \
	dev_dbg((ctl)->nhi->dev, format, ## arg)

#define tb_ctl_dbg_once(ctl, format, arg...) \
	dev_dbg_once((ctl)->nhi->dev, format, ## arg)
```

[`tb_ctl_WARN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L58) expands to [`dev_WARN()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dev_printk.h#L271), which prints with a backtrace, and [`tb_ctl_warn`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L64) to [`dev_warn()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dev_printk.h#L155). [`tb_ctl_dbg_once`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L73) expands to [`dev_dbg_once()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/dev_printk.h#L206), which prints on the first occurrence only. All six print through the same [`nhi`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L40), and [`tb_cfg_print_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L278) picks among three of them by the refusal code.

```c
/* drivers/thunderbolt/ctl.c:278 */
static void tb_cfg_print_error(struct tb_ctl *ctl, enum tb_cfg_space space,
			       const struct tb_cfg_result *res)
{
	WARN_ON(res->err != 1);
	switch (res->tb_error) {
	case TB_CFG_ERROR_PORT_NOT_CONNECTED:
		/* Port is not connected. This can happen during surprise
		 * removal. Do not warn. */
		return;
	case TB_CFG_ERROR_INVALID_CONFIG_SPACE:
		/*
		 * Invalid cfg_space/offset/length combination in
		 * cfg_read/cfg_write.
		 */
		tb_ctl_dbg_once(ctl, "%llx:%x: invalid config space (%u) or offset\n",
				res->response_route, res->response_port, space);
		return;
	case TB_CFG_ERROR_NO_SUCH_PORT:
		/*
		 * - The route contains a non-existent port.
		 * - The route contains a non-PHY port (e.g. PCIe).
		 * - The port in cfg_read/cfg_write does not exist.
		 */
		tb_ctl_WARN(ctl, "CFG_ERROR(%llx:%x): Invalid port\n",
			res->response_route, res->response_port);
		return;
	case TB_CFG_ERROR_LOOP:
		tb_ctl_WARN(ctl, "CFG_ERROR(%llx:%x): Route contains a loop\n",
			res->response_route, res->response_port);
		return;
	case TB_CFG_ERROR_LOCK:
		tb_ctl_warn(ctl, "%llx:%x: downstream port is locked\n",
			    res->response_route, res->response_port);
		return;
	default:
		/* 5,6,7,9 and 11 are also valid error codes */
		tb_ctl_WARN(ctl, "CFG_ERROR(%llx:%x): Unknown error\n",
			res->response_route, res->response_port);
		return;
	}
}
```

[`tb_cfg_print_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L278) asserts with [`WARN_ON()`](https://elixir.bootlin.com/linux/v7.2/source/include/asm-generic/bug.h#L109) that it was handed a refusal. It returns silently for [`TB_CFG_ERROR_PORT_NOT_CONNECTED`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L23), which its comment says "can happen during surprise removal". [`TB_CFG_ERROR_INVALID_CONFIG_SPACE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L25) gets one debug line, once-only since commit c55017a0608e ("thunderbolt: Debug log an invalid config space reply just once"). That commit cites a router that "does not implement the config space register blocks fully".

[`TB_CFG_ERROR_NO_SUCH_PORT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L26), [`TB_CFG_ERROR_LOOP`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L28) and every code the switch leaves unnamed get [`tb_ctl_WARN`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L58). Their messages report an invalid port, a looping route and an unknown error. The default's comment lists codes 5, 6, 7, 9 and 11 as other valid values. [`TB_CFG_ERROR_LOCK`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L31) alone gets a plain warning, "just warning level" in the words of commit 80e7c5dd1ee0.

The log severity therefore follows the refusal code, from silence for a removal in progress to a backtrace for an address that cannot exist.

### Notification codes leave the receive path before the queue

An error frame is either a refusal of an outstanding request or a notification a router raises on its own. The receive path sends the eleven notification codes to the domain before the queue sees them. The type switch of [`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) comes first, then [`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419), the predicate it consults.

```c
/* drivers/thunderbolt/ctl.c:468 */
	switch (frame->eof) {
	case TB_CFG_PKG_READ:
	case TB_CFG_PKG_WRITE:
	case TB_CFG_PKG_ERROR:
	case TB_CFG_PKG_OVERRIDE:
	case TB_CFG_PKG_RESET:
		if (*(__be32 *)(pkg->buffer + frame->size) != crc32) {
			tb_ctl_err(pkg->ctl,
				   "RX: checksum mismatch, dropping packet\n");
			goto rx;
		}
		if (tb_async_error(pkg)) {
			tb_ctl_handle_event(pkg->ctl, frame->eof,
					    pkg, frame->size);
			goto rx;
		}
		break;

	case TB_CFG_PKG_EVENT:
	case TB_CFG_PKG_XDOMAIN_RESP:
	case TB_CFG_PKG_XDOMAIN_REQ:
		if (*(__be32 *)(pkg->buffer + frame->size) != crc32) {
			tb_ctl_err(pkg->ctl,
				   "RX: checksum mismatch, dropping packet\n");
			goto rx;
		}
		fallthrough;
	case TB_CFG_PKG_ICM_EVENT:
		if (tb_ctl_handle_event(pkg->ctl, frame->eof, pkg, frame->size))
			goto rx;
		break;

	default:
		break;
	}
```

[`tb_ctl_rx_callback()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L445) checks the checksum of every configuration-type frame. A frame that [`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419) accepts goes to [`tb_ctl_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L402), and the jump to `rx` keeps it from the lookup. Event and XDomain frames go to the domain as well, and reach the lookup only when [`tb_ctl_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L402) returns false. [`TB_CFG_PKG_ICM_EVENT`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L41) is ICM-only.

```c
/* drivers/thunderbolt/ctl.c:419 */
static int tb_async_error(const struct ctl_pkg *pkg)
{
	const struct cfg_error_pkg *error = pkg->buffer;

	if (pkg->frame.eof != TB_CFG_PKG_ERROR)
		return false;

	switch (error->error) {
	case TB_CFG_ERROR_LINK_ERROR:
	case TB_CFG_ERROR_HEC_ERROR_DETECTED:
	case TB_CFG_ERROR_FLOW_CONTROL_ERROR:
	case TB_CFG_ERROR_DP_BW:
	case TB_CFG_ERROR_ROP_CMPLT:
	case TB_CFG_ERROR_POP_CMPLT:
	case TB_CFG_ERROR_PCIE_WAKE:
	case TB_CFG_ERROR_DP_CON_CHANGE:
	case TB_CFG_ERROR_DPTX_DISCOVERY:
	case TB_CFG_ERROR_LINK_RECOVERY:
	case TB_CFG_ERROR_ASYM_LINK:
		return true;

	default:
		return false;
	}
}
```

[`tb_async_error()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L419) returns false for any frame that is not a [`TB_CFG_PKG_ERROR`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L34). It returns true for the eleven codes of [`enum tb_cfg_error`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L22) its switch names, the notifications. Every other error code falls through to the lookup, and the first queued request whose match accepts error frames, [`tb_cfg_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L856) among them, takes it as a refusal.

So far, a reply has become a result and then an errno, and a notification has gone to the domain before any request could take it. Notification codes therefore leave the receive path before the queue, and every other error frame reaches the queue as a refusal.

### The plug acknowledgement is a packet no request tracks

The plug acknowledgement goes straight to the channel's transmit path without a request, because it expects no reply. The router that reported the event needs it, as the commit quoted below explains. [`tb_cfg_ack_plug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L842) with its kerneldoc comes first, then the error packet it builds, then the stage of [`tb_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2916) that calls it.

```c
/* drivers/thunderbolt/ctl.c:831 */
/**
 * tb_cfg_ack_plug() - Ack hot plug/unplug event
 * @ctl: Control channel to use
 * @route: Router that originated the event
 * @port: Port where the hot plug/unplug happened
 * @unplug: Ack hot plug or unplug
 *
 * Call this as a response for hot plug/unplug event to ack it.
 *
 * Return: %0 on success, negative errno otherwise.
 */
int tb_cfg_ack_plug(struct tb_ctl *ctl, u64 route, u32 port, bool unplug)
{
	struct cfg_error_pkg pkg = {
		.header = tb_cfg_make_header(route),
		.port = port,
		.error = TB_CFG_ERROR_ACK_PLUG_EVENT,
		.pg = unplug ? TB_CFG_ERROR_PG_HOT_UNPLUG
			     : TB_CFG_ERROR_PG_HOT_PLUG,
	};
	tb_ctl_dbg(ctl, "acking hot %splug event on %llx:%u\n",
		   unplug ? "un" : "", route, port);
	return tb_ctl_tx(ctl, &pkg, sizeof(pkg), TB_CFG_PKG_ERROR);
}
```

[`tb_cfg_ack_plug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L842) fills a [`struct cfg_error_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L73) on its stack with the adapter number and the code [`TB_CFG_ERROR_ACK_PLUG_EVENT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L27). A plug-group value says which event is acknowledged, and [`tb_ctl_tx()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L366) sends the packet as a [`TB_CFG_PKG_ERROR`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L34) frame. With nothing queued, a transmit failure is the only failure the helper can report.

```c
/* drivers/thunderbolt/tb_msgs.h:73 */
struct cfg_error_pkg {
	struct tb_cfg_header header;
	enum tb_cfg_error error:8;
	u32 port:6;
	u32 reserved:16;
	u32 pg:2;
} __packed;

struct cfg_ack_pkg {
	struct tb_cfg_header header;
};

#define TB_CFG_ERROR_PG_HOT_PLUG	0x2
#define TB_CFG_ERROR_PG_HOT_UNPLUG	0x3
```

[`struct cfg_error_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L73) follows the common [`header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L74) with the eight-bit [`error`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L75) code, the six-bit [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L76), sixteen [`reserved`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L77) bits and the two-bit [`pg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L78). [`struct cfg_ack_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L81) is the header alone. [`TB_CFG_ERROR_PG_HOT_PLUG`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L85) is 2 and [`TB_CFG_ERROR_PG_HOT_UNPLUG`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L86) is 3.

Commit 210e9f56e9e1 added the field, which the router needs "in order the router to send further hot plug notifications". Its message adds "we fill the field unconditionally", because older devices ignore it. [`tb_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2916) acknowledges a plug event before it queues the work that handles it.

```c
/* drivers/thunderbolt/tb.c:2933 */
	if (tb_cfg_ack_plug(tb->ctl, route, pkg->port, pkg->unplug)) {
		tb_warn(tb, "could not ack plug event on %llx:%x\n", route,
			pkg->port);
	}

	tb_queue_hotplug(tb, route, pkg->port, pkg->unplug);
```

[`tb_handle_event()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2916) warns when the acknowledgement could not be sent and queues the event with [`tb_queue_hotplug()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L93) either way. The plug acknowledgement is therefore a packet no request tracks, sent before the domain queues the event it acknowledges.

### The notification acknowledgement names the code and sends a header

A notification is acknowledged with a packet that carries only the header. Most of the helper's lines name the code for the debug log. [`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) is read in the three pieces outlined below, then [`tb_handle_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2885), which decides which codes are acknowledged.

| piece | lines | stage |
|---|---|---|
| Ⓐ | [`ctl.c:778-785`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) | builds the header-only packet |
| Ⓑ | [`ctl.c:786-824`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L786) | names the code for the log |
| Ⓒ | [`ctl.c:825-829`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L825) | logs the name and transmits |

Piece Ⓐ of [`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) builds the whole packet, a [`struct cfg_ack_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L81) holding the header for the route.

```c
/* drivers/thunderbolt/ctl.c:768 */
/**
 * tb_cfg_ack_notification() - Ack notification
 * @ctl: Control channel to use
 * @route: Router that originated the event
 * @error: Pointer to the notification package
 *
 * Call this as a response for non-plug notification to ack it.
 *
 * Return: %0 on success, negative errno otherwise.
 */
int tb_cfg_ack_notification(struct tb_ctl *ctl, u64 route,
			    const struct cfg_error_pkg *error)
{
	struct cfg_ack_pkg pkg = {
		.header = tb_cfg_make_header(route),
	};
	const char *name;

```

[`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) takes only the code from the notification, because the packet it sends is the header for the route. Piece Ⓑ of [`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) assigns one word per notification code, the eleven codes the receive path diverts, and "unknown" for any other.

```c
/* drivers/thunderbolt/ctl.c:786 */
	switch (error->error) {
	case TB_CFG_ERROR_LINK_ERROR:
		name = "link error";
		break;
	case TB_CFG_ERROR_HEC_ERROR_DETECTED:
		name = "HEC error";
		break;
	case TB_CFG_ERROR_FLOW_CONTROL_ERROR:
		name = "flow control error";
		break;
	case TB_CFG_ERROR_DP_BW:
		name = "DP_BW";
		break;
	case TB_CFG_ERROR_ROP_CMPLT:
		name = "router operation completion";
		break;
	case TB_CFG_ERROR_POP_CMPLT:
		name = "port operation completion";
		break;
	case TB_CFG_ERROR_PCIE_WAKE:
		name = "PCIe wake";
		break;
	case TB_CFG_ERROR_DP_CON_CHANGE:
		name = "DP connector change";
		break;
	case TB_CFG_ERROR_DPTX_DISCOVERY:
		name = "DPTX discovery";
		break;
	case TB_CFG_ERROR_LINK_RECOVERY:
		name = "link recovery";
		break;
	case TB_CFG_ERROR_ASYM_LINK:
		name = "asymmetric link";
		break;
	default:
		name = "unknown";
		break;
	}

```

[`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) only assigns a string in each case of the switch, so the code changes the log line and nothing else. Piece Ⓒ of [`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) prints that word with the code and the route, and transmits the packet.

```c
/* drivers/thunderbolt/ctl.c:825 */
	tb_ctl_dbg(ctl, "acking %s (%#x) notification on %llx\n", name,
		   error->error, route);

	return tb_ctl_tx(ctl, &pkg, sizeof(pkg), TB_CFG_PKG_NOTIFY_ACK);
}
```

[`tb_cfg_ack_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L778) sends a [`TB_CFG_PKG_NOTIFY_ACK`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L35) frame, where the plug acknowledgement sends an error frame, and returns the transmit's result. [`tb_handle_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2885) acknowledges four of the eleven codes and starts further work for one of them.

```c
/* drivers/thunderbolt/tb.c:2885 */
static void tb_handle_notification(struct tb *tb, u64 route,
				   const struct cfg_error_pkg *error)
{

	switch (error->error) {
	case TB_CFG_ERROR_PCIE_WAKE:
	case TB_CFG_ERROR_DP_CON_CHANGE:
	case TB_CFG_ERROR_DPTX_DISCOVERY:
		if (tb_cfg_ack_notification(tb->ctl, route, error))
			tb_warn(tb, "could not ack notification on %llx\n",
				route);
		break;

	case TB_CFG_ERROR_DP_BW:
		if (tb_cfg_ack_notification(tb->ctl, route, error))
			tb_warn(tb, "could not ack notification on %llx\n",
				route);
		tb_queue_dp_bandwidth_request(tb, route, error->port, 0, 0);
		break;

	default:
		/* Ignore for now */
		break;
	}
}
```

[`tb_handle_notification()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2885) acknowledges [`TB_CFG_ERROR_PCIE_WAKE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L35), [`TB_CFG_ERROR_DP_CON_CHANGE`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L36), [`TB_CFG_ERROR_DPTX_DISCOVERY`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L37) and [`TB_CFG_ERROR_DP_BW`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L32). Only the last starts work, through [`tb_queue_dp_bandwidth_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.c#L2868). Every other code reaches the default case, whose comment reads "Ignore for now", and is neither acknowledged nor handled.

The software connection manager sends it for four codes. The notification acknowledgement therefore names the code for the log and sends a bare header.

### The reset command sends one packet and waits once

Resetting a router of the first generation takes one request and no retry. Its reply is a bare header, which the configuration match pairs on type, route and size alone. [`tb_cfg_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L911) with its kerneldoc comes first, then the branch of [`tb_switch_reset_host()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1581) that calls it.

```c
/* drivers/thunderbolt/ctl.c:899 */
/**
 * tb_cfg_reset() - send a reset packet and wait for a response
 * @ctl: Control channel pointer
 * @route: Router string for the router to send reset
 *
 * If the switch at route is incorrectly configured then we will not receive a
 * reply (even though the switch will reset). The caller should check for
 * -ETIMEDOUT and attempt to reconfigure the switch.
 *
 * Return: &struct tb_cfg_result with non-zero @err field if error
 * has occurred.
 */
struct tb_cfg_result tb_cfg_reset(struct tb_ctl *ctl, u64 route)
{
	struct cfg_reset_pkg request = { .header = tb_cfg_make_header(route) };
	struct tb_cfg_result res = { 0 };
	struct tb_cfg_header reply;
	struct tb_cfg_request *req;

	req = tb_cfg_request_alloc();
	if (!req) {
		res.err = -ENOMEM;
		return res;
	}

	req->match = tb_cfg_match;
	req->copy = tb_cfg_copy;
	req->request = &request;
	req->request_size = sizeof(request);
	req->request_type = TB_CFG_PKG_RESET;
	req->response = &reply;
	req->response_size = sizeof(reply);
	req->response_type = TB_CFG_PKG_RESET;

	res = tb_cfg_request_sync(ctl, req, ctl->timeout_msec);

	tb_cfg_request_put(req);

	return res;
}
```

[`tb_cfg_reset()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L911) sends a [`struct cfg_reset_pkg`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L97) and expects a [`struct tb_cfg_header`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L43) back, both typed [`TB_CFG_PKG_RESET`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L40). [`tb_cfg_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L856) therefore skips the sequence comparison it applies to reads and writes. The function makes one attempt at [`timeout_msec`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L50), and its kerneldoc warns that a misconfigured router resets without replying.

Commit 02729d17b1b8 ("thunderbolt: Fix reset response_type") corrected the expected type. Commit bda83aeca3cf ("thunderbolt: Do not pass timeout for tb_cfg_reset()") removed a timeout argument, because its one user passed the default anyway. [`tb_switch_reset_host()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1581) takes the branch below when the router's [`generation`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L188) is not above 1.

```c
/* drivers/thunderbolt/switch.c:1628 */
	} else {
		struct tb_cfg_result res;

		/* Thunderbolt 1 uses the "reset" config space packet */
		res.err = tb_sw_write(sw, ((u32 *) &sw->config) + 2,
				      TB_CFG_SWITCH, 2, 2);
		if (res.err)
			return res.err;
		res = tb_cfg_reset(sw->tb->ctl, tb_route(sw));
		if (res.err > 0)
			return -EIO;
		else if (res.err < 0)
			return res.err;
	}
```

[`tb_switch_reset_host()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L1581) writes dwords 2 and 3 of the cached router header back through [`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686). It then reads the three-valued [`err`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L42) of the reset directly, folding a refusal into -EIO and passing a negative value through. The reset command therefore sends one packet, waits once at the channel's timeout, and leaves its caller to fold the result.

### The upstream-port probe keeps only the reply's port number

The upstream-port probe reads one dword and keeps only the port number the reply came from. That number is the router's adapter that faces the host. [`tb_cfg_get_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1173) with its kerneldoc comes first, then its three call sites in the router code.

```c
/* drivers/thunderbolt/ctl.c:1163 */
/**
 * tb_cfg_get_upstream_port() - get upstream port number of switch at route
 * @ctl: Pointer to the control channel
 * @route: Route string of the router
 *
 * Reads the first dword from the switches TB_CFG_SWITCH config area and
 * returns the port number from which the reply originated.
 *
 * Return: Upstream port number on success or negative error code on failure.
 */
int tb_cfg_get_upstream_port(struct tb_ctl *ctl, u64 route)
{
	u32 dummy;
	struct tb_cfg_result res = tb_cfg_read_raw(ctl, &dummy, route, 0,
						   TB_CFG_SWITCH, 0, 1,
						   ctl->timeout_msec);
	if (res.err == 1)
		return -EIO;
	if (res.err)
		return res.err;
	return res.response_port;
}
```

[`tb_cfg_get_upstream_port()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1173) reads one dword at offset 0 of [`TB_CFG_SWITCH`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L18) into a local it never reads. It returns [`response_port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L34), which the raw read filled from the reply's [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb_msgs.h#L53). It calls the raw read because the cooked one discards that member, and folds a refusal into -EIO. [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) probes the route before it allocates anything.

```c
/* drivers/thunderbolt/switch.c:2467 */
	depth = tb_route_length(route);

	upstream_port = tb_cfg_get_upstream_port(tb->ctl, route);
	if (upstream_port < 0)
		return ERR_PTR(upstream_port);

	sw = kzalloc_obj(*sw);
	if (!sw)
		return ERR_PTR(-ENOMEM);

	sw->tb = tb;
	ret = tb_cfg_read(tb->ctl, &sw->config, route, 0, TB_CFG_SWITCH, 0, 5);
	if (ret)
		goto err_free_sw_ports;

	sw->generation = tb_switch_get_generation(sw);

	tb_dbg(tb, "current switch config:\n");
	tb_dump_switch(tb, sw);

	/* configure switch */
	sw->config.upstream_port_number = upstream_port;
	sw->config.depth = depth;
	sw->config.route_hi = upper_32_bits(route);
	sw->config.route_lo = lower_32_bits(route);
```

[`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451) returns the probe's error without building an object. It then reads five dwords of the router's header with [`tb_cfg_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1111) directly, naming the route it was given. The port number becomes the header's upstream port at [`switch.c:2488`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2488). [`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) calls the probe twice and reads only the sign of its result.

```c
/* drivers/thunderbolt/switch.c:3544 */
		err = tb_cfg_get_upstream_port(sw->tb->ctl, tb_route(sw));
		if (err < 0) {
			tb_sw_info(sw, "switch not present anymore\n");
			return err;
		}
/* drivers/thunderbolt/switch.c:3618 */
				err = tb_cfg_get_upstream_port(sw->tb->ctl,
							       port->xdomain->route);
				if (err > 0) {
					tb_port_warn(port,
						     "XDomain was disconnected\n");
					port->xdomain->is_unplugged = true;
				}
```

[`tb_switch_resume()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L3525) treats a negative result as a router that is gone. On an adapter that held an XDomain connection, a positive result means a router now answers where the other host was. The function then marks the XDomain unplugged.

So far, every command this layer exports has been read, from the raw and cooked accesses to this probe. The upstream-port probe therefore keeps only the reply's port number, used once as a number and twice as a presence test.

### Inline wrappers turn a router or adapter into a route

The rest of the driver reaches this layer through four inline wrappers. They turn an object into a route and an adapter number, and refuse a router already marked unplugged. [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) with the router pair, [`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) and [`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686), comes first, then the adapter pair, a table of their call sites, and a figure of the layers.

```c
/* drivers/thunderbolt/tb.h:583 */
static inline u64 tb_route(const struct tb_switch *sw)
{
	return ((u64) sw->config.route_hi) << 32 | sw->config.route_lo;
}
/* drivers/thunderbolt/tb.h:672 */
static inline int tb_sw_read(struct tb_switch *sw, void *buffer,
			     enum tb_cfg_space space, u32 offset, u32 length)
{
	if (sw->is_unplugged)
		return -ENODEV;
	return tb_cfg_read(sw->tb->ctl,
			   buffer,
			   tb_route(sw),
			   0,
			   space,
			   offset,
			   length);
}

static inline int tb_sw_write(struct tb_switch *sw, const void *buffer,
			      enum tb_cfg_space space, u32 offset, u32 length)
{
	if (sw->is_unplugged)
		return -ENODEV;
	return tb_cfg_write(sw->tb->ctl,
			    buffer,
			    tb_route(sw),
			    0,
			    space,
			    offset,
			    length);
}
```

[`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) and [`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686) return -ENODEV as soon as [`is_unplugged`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L193) is set. Otherwise they pass adapter 0 and the route [`tb_route()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L583) assembles from the router's cached header. [`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) and [`tb_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L714) differ only in the adapter they name and in where they find the unplug flag.

```c
/* drivers/thunderbolt/tb.h:700 */
static inline int tb_port_read(struct tb_port *port, void *buffer,
			       enum tb_cfg_space space, u32 offset, u32 length)
{
	if (port->sw->is_unplugged)
		return -ENODEV;
	return tb_cfg_read(port->sw->tb->ctl,
			   buffer,
			   tb_route(port->sw),
			   port->port,
			   space,
			   offset,
			   length);
}

static inline int tb_port_write(struct tb_port *port, const void *buffer,
				enum tb_cfg_space space, u32 offset, u32 length)
{
	if (port->sw->is_unplugged)
		return -ENODEV;
	return tb_cfg_write(port->sw->tb->ctl,
			    buffer,
			    tb_route(port->sw),
			    port->port,
			    space,
			    offset,
			    length);
}
```

[`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) and [`tb_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L714) test the unplug flag of the adapter's router through [`sw`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L282). They pass the adapter's own number from [`port`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L290).

Every caller of [`tb_cfg_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1137), and every caller of [`tb_cfg_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1111) except [`tb_switch_alloc()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/switch.c#L2451), is one of the wrappers. The wrappers in turn carry 247 call sites in eleven files, [`debugfs.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/debugfs.c) among them when [`CONFIG_DEBUG_FS`](https://elixir.bootlin.com/linux/v7.2/source/lib/Kconfig.debug#L708) is set.

| wrapper | call sites | files |
|---|---|---|
| [`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) | 54 | 8 |
| [`tb_sw_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L686) | 37 | 8 |
| [`tb_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L700) | 104 | 10 |
| [`tb_port_write()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L714) | 52 | 7 |

Each of those calls crosses the same layers on its way to the channel. The figure draws them with the boundary each crossing passes.

```
    One register access, from the helper that names a register to the channel
    ─────────────────────────────────────────────────────────────────────────

    a caller holding a struct tb_switch or a struct tb_port
                                  │  ⓐ route and adapter number supplied, unplugged router refused
                                  ▼
    ┌──────────────────────────────────────────────────────────────┐
    │ cooked read or write, result folded into an errno         ⓑ │
    └─────────────────────────────┬────────────────────────────────┘
                                  │  the channel's timeout supplied
                                  ▼
    ┌──────────────────────────────────────────────────────────────┐
    │ raw read or write, up to four requests, seq 0 to 3        ⓒ │
    └─────────────────────────────┬────────────────────────────────┘
                                  │  one request per try, freed after it
                                  ▼
    ┌──────────────────────────────────────────────────────────────┐
    │ request core, queue, completion, cancel on timeout        ⓓ │
    └─────────────────────────────┬────────────────────────────────┘
                                  │  packet out, reply back through the receive callback
                                  ▼
    the control channel and its two rings

    ⓐ tb_sw_read           tb.h:677   passes the router's route and adapter 0
    ⓑ tb_cfg_read          ctl.c:1114 calls the raw read at the channel's timeout
    ⓒ tb_cfg_read_raw      ctl.c:993  submits one try and waits for it
    ⓓ tb_cfg_request_sync  ctl.c:625  submits the request, then sleeps on its completion
```

ⓐ [`tb_sw_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/tb.h#L672) supplies the route and adapter 0, or refuses an unplugged router. ⓑ [`tb_cfg_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L1111) calls the raw read at the channel's timeout and folds its result. ⓒ [`tb_cfg_read_raw()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L956) submits one request per try and waits for each. ⓓ [`tb_cfg_request_sync()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L616) submits the request and sleeps on its completion.

Every access through them crosses the cooked, raw and core layers in that order. Inline wrappers therefore turn a router or adapter into a route and an adapter number.

### XDomain messages reuse the request with their own pairing

A message to another host uses the same request object, queue and completion as a configuration access. It differs only in the pair of callbacks that recognize its reply. [`__tb_xdomain_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L180) and the exported [`tb_xdomain_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L225) come first, then [`tb_xdomain_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L90) and [`tb_xdomain_copy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L123), then the DMA port's pair.

```c
/* drivers/thunderbolt/xdomain.c:180 */
static int __tb_xdomain_request(struct tb_ctl *ctl, const void *request,
	size_t request_size, enum tb_cfg_pkg_type request_type, void *response,
	size_t response_size, enum tb_cfg_pkg_type response_type,
	unsigned int timeout_msec)
{
	struct tb_cfg_request *req;
	struct tb_cfg_result res;

	req = tb_cfg_request_alloc();
	if (!req)
		return -ENOMEM;

	req->match = tb_xdomain_match;
	req->copy = tb_xdomain_copy;
	req->request = request;
	req->request_size = request_size;
	req->request_type = request_type;
	req->response = response;
	req->response_size = response_size;
	req->response_type = response_type;

	res = tb_cfg_request_sync(ctl, req, timeout_msec);

	tb_cfg_request_put(req);

	return res.err == 1 ? -EIO : res.err;
}
/* drivers/thunderbolt/xdomain.c:208 */
/**
 * tb_xdomain_request() - Send a XDomain request
 * @xd: XDomain to send the request
 * @request: Request to send
 * @request_size: Size of the request in bytes
 * @request_type: PDF type of the request
 * @response: Response is copied here
 * @response_size: Expected size of the response in bytes
 * @response_type: Expected PDF type of the response
 * @timeout_msec: Timeout in milliseconds to wait for the response
 *
 * This function can be used to send XDomain control channel messages to
 * the other domain. The function waits until the response is received
 * or when timeout triggers. Whichever comes first.
 *
 * Return: %0 on success, negative errno otherwise.
 */
int tb_xdomain_request(struct tb_xdomain *xd, const void *request,
	size_t request_size, enum tb_cfg_pkg_type request_type,
	void *response, size_t response_size,
	enum tb_cfg_pkg_type response_type, unsigned int timeout_msec)
{
	return __tb_xdomain_request(xd->tb->ctl, request, request_size,
				    request_type, response, response_size,
				    response_type, timeout_msec);
}
EXPORT_SYMBOL_GPL(tb_xdomain_request);
```

[`__tb_xdomain_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L180) fills a request as the configuration commands do, with [`tb_xdomain_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L90) and [`tb_xdomain_copy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L123) as its pair and its caller's timeout. It folds a refusal into -EIO. [`tb_xdomain_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L225) is the exported form, which takes the channel from the XDomain's domain. In its kerneldoc's words, it "waits until the response is received or when timeout triggers".

```c
/* drivers/thunderbolt/xdomain.c:90 */
static bool tb_xdomain_match(const struct tb_cfg_request *req,
			     const struct ctl_pkg *pkg)
{
	switch (pkg->frame.eof) {
	case TB_CFG_PKG_ERROR:
		return true;

	case TB_CFG_PKG_XDOMAIN_RESP: {
		const struct tb_xdp_header *res_hdr = pkg->buffer;
		const struct tb_xdp_header *req_hdr = req->request;

		if (pkg->frame.size < req->response_size / 4)
			return false;

		/* Make sure route matches */
		if ((res_hdr->xd_hdr.route_hi & ~BIT(31)) !=
		     req_hdr->xd_hdr.route_hi)
			return false;
		if ((res_hdr->xd_hdr.route_lo) != req_hdr->xd_hdr.route_lo)
			return false;

		/* Check that the XDomain protocol matches */
		if (!uuid_equal(&res_hdr->uuid, &req_hdr->uuid))
			return false;

		return true;
	}

	default:
		return false;
	}
}
/* drivers/thunderbolt/xdomain.c:123 */
static bool tb_xdomain_copy(struct tb_cfg_request *req,
			    const struct ctl_pkg *pkg)
{
	size_t len = min_t(size_t, pkg->frame.size, req->response_size);

	memcpy(req->response, pkg->buffer, len);
	req->result.err = 0;
	return true;
}
```

[`tb_xdomain_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L90) accepts [`TB_CFG_PKG_ERROR`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L34) as the configuration match does, and otherwise only [`TB_CFG_PKG_XDOMAIN_RESP`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L38). It rejects a frame whose size is below `response_size / 4`. It compares the route halves with bit 31 of the upper half cleared, and requires the protocol UUIDs to agree through [`uuid_equal()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/uuid.h#L71).

[`tb_xdomain_copy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L123) copies [`min_t()`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/minmax.h#L161) of the frame's size and the expected size and writes 0 into [`err`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L42) without reading a header. An accepted error frame therefore reaches its caller as a successful copy of an error packet. The DMA-port mailbox code builds its requests with a third pair, [`dma_port_match()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L65) and [`dma_port_copy()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L82), as [`dma_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L88) shows.

```c
/* drivers/thunderbolt/dma_port.c:105 */
	req = tb_cfg_request_alloc();
	if (!req)
		return -ENOMEM;

	req->match = dma_port_match;
	req->copy = dma_port_copy;
	req->request = &request;
	req->request_size = sizeof(request);
	req->request_type = TB_CFG_PKG_READ;
	req->response = &reply;
	req->response_size = 12 + 4 * length;
	req->response_type = TB_CFG_PKG_READ;

	res = tb_cfg_request_sync(ctl, req, timeout_msec);

	tb_cfg_request_put(req);
```

[`dma_port_read()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/dma_port.c#L88) installs the DMA-port pair, waits through [`tb_cfg_request_sync()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L616) with its caller's timeout, and drops its reference. The firmware connection manager's message path is a fourth user of the machinery and is ICM-only.

XDomain messages therefore reuse the request, its queue and its completion, and change only the pair of callbacks that recognize a reply.

### A reply-less message retires through its own callback

A message that expects no answer still travels as a request. Its own work item finishes it as soon as its packet is on the ring. [`__tb_xdomain_response()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L138) and its callback [`response_ready()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L133) come first, then the branch of [`tb_cfg_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L547) that serves them.

```c
/* drivers/thunderbolt/xdomain.c:133 */
static void response_ready(void *data)
{
	tb_cfg_request_put(data);
}

static int __tb_xdomain_response(struct tb_ctl *ctl, const void *response,
				 size_t size, enum tb_cfg_pkg_type type)
{
	struct tb_cfg_request *req;
	int ret;

	req = tb_cfg_request_alloc();
	if (!req)
		return -ENOMEM;

	req->match = tb_xdomain_match;
	req->copy = tb_xdomain_copy;
	req->request = response;
	req->request_size = size;
	req->request_type = type;

	ret = tb_cfg_request(ctl, req, response_ready, req);
	if (ret)
		tb_cfg_request_put(req);

	return ret;
}
```

[`__tb_xdomain_response()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L138) leaves [`response`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.h#L83) unset and passes the request itself as the callback data. The branch of [`tb_cfg_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L547) that serves it schedules the work item once the packet is on the ring.

```c
/* drivers/thunderbolt/ctl.c:563 */
	ret = tb_ctl_tx(ctl, req->request, req->request_size,
			req->request_type);
	if (ret)
		goto err_dequeue;

	if (!req->response)
		schedule_work(&req->work);

	return 0;
```

[`tb_cfg_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/ctl.c#L547) schedules the item at once only for a request without a reply buffer. Outside the ICM-only code, [`__tb_xdomain_response()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L138) is the one builder that leaves the buffer unset. The pass calls [`response_ready()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L133), which drops the builder's reference, then drops the queue's reference and frees the request.

A reply-less message therefore retires through its own callback, and the work item frees it without a waiter.

### The networking driver alone calls the exported request

Outside the thunderbolt module, one driver in the tree calls the exported request, the networking service driver. Its login and logout handshakes run through the request with timeouts of their own. The driver is built when [`CONFIG_USB4_NET`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/Kconfig#L2) is set, and its timeouts, [`TBNET_LOGIN_TIMEOUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L31) first, come with [`tbnet_login_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L259) and [`tbnet_logout_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L293).

```c
/* drivers/net/thunderbolt/main.c:31 */
#define TBNET_LOGIN_TIMEOUT	500
#define TBNET_LOGOUT_TIMEOUT	1000
/* drivers/net/thunderbolt/main.c:259 */
static int tbnet_login_request(struct tbnet *net, u8 sequence)
{
	struct thunderbolt_ip_login_response reply;
	struct thunderbolt_ip_login request;
	struct tb_xdomain *xd = net->xd;

	memset(&request, 0, sizeof(request));
	tbnet_fill_header(&request.hdr, xd->route, sequence, xd->local_uuid,
			  xd->remote_uuid, TBIP_LOGIN, sizeof(request),
			  atomic_inc_return(&net->command_id));

	request.proto_version = TBIP_LOGIN_PROTO_VERSION;
	request.transmit_path = net->local_transmit_path;

	return tb_xdomain_request(xd, &request, sizeof(request),
				  TB_CFG_PKG_XDOMAIN_RESP, &reply,
				  sizeof(reply), TB_CFG_PKG_XDOMAIN_RESP,
				  TBNET_LOGIN_TIMEOUT);
}
/* drivers/net/thunderbolt/main.c:293 */
static int tbnet_logout_request(struct tbnet *net)
{
	struct thunderbolt_ip_logout request;
	struct thunderbolt_ip_status reply;
	struct tb_xdomain *xd = net->xd;

	memset(&request, 0, sizeof(request));
	tbnet_fill_header(&request.hdr, xd->route, 0, xd->local_uuid,
			  xd->remote_uuid, TBIP_LOGOUT, sizeof(request),
			  atomic_inc_return(&net->command_id));

	return tb_xdomain_request(xd, &request, sizeof(request),
				  TB_CFG_PKG_XDOMAIN_RESP, &reply,
				  sizeof(reply), TB_CFG_PKG_XDOMAIN_RESP,
				  TBNET_LOGOUT_TIMEOUT);
}
```

[`tbnet_login_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L259) builds the login message and its reply buffer on its stack, and names [`TB_CFG_PKG_XDOMAIN_RESP`](https://elixir.bootlin.com/linux/v7.2/source/include/linux/thunderbolt.h#L38) for both packet types. It passes [`TBNET_LOGIN_TIMEOUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L31), 500 ms, where a configuration read takes the channel's 100 ms. [`tbnet_logout_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L293) passes [`TBNET_LOGOUT_TIMEOUT`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c#L32), 1000 ms, and the two are the only calls of [`tb_xdomain_request()`](https://elixir.bootlin.com/linux/v7.2/source/drivers/thunderbolt/xdomain.c#L225) in the tree.

The driver's source is [`main.c`](https://elixir.bootlin.com/linux/v7.2/source/drivers/net/thunderbolt/main.c), with commits into 2026. The latest at v7.2 is 68bf02b6b4ad ("net: thunderbolt: Tear down DMA paths before stopping the rings"). [`Documentation/admin-guide/thunderbolt.rst`](https://elixir.bootlin.com/linux/v7.2/source/Documentation/admin-guide/thunderbolt.rst) describes the network interface it creates.

The exported request therefore serves one driver in the tree, whose handshakes wait five and ten times the channel's timeout.
