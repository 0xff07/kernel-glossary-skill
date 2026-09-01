# FACT-04: Activation delta

**INPUT:** Every mechanism on the page that can be switched on and off at runtime — a mode, a feature bit, a power state, an offload, an optimization — together with the source of the code that runs while it is on, the code that engages and disengages it, and the call sites elsewhere in the tree that behave differently once it is engaged.

**OUTPUT:** For each such mechanism, a facet of DETAILS stating what changes about the system once the mechanism is active: what now runs that did not, what stops running, which existing paths gain a precondition, and what forces the return to the inactive state; delivered with the call-site population that gained the precondition enumerated and cited, and with the engage and disengage paths shown as code.

**Rule:**

1. Documenting the registers, fields, and helpers that turn a mechanism on is not documenting the mechanism. A reader who finishes the page knowing every bit of the enable register and not knowing what the machine does differently afterwards has learned an encoding, not a mechanism.
2. A page that documents an activatable mechanism carries an activation-delta facet. It answers four questions, each from cited code:
   1. What runs while the mechanism is active that did not run before, including any worker, timer, or interrupt path that only exists in the active state.
   2. What CODE stops running while it is active. Where the mechanism executes in silicon or firmware, no function stops being called and the honest answer to this question is short or empty; say so and put the disengaging write under question 4 rather than manufacturing a code path for it.
   3. Which pre-existing call sites gain a precondition — the paths that must now disengage the mechanism, wait for it, or check its state before doing what they always did.
   4. What drives the return to the inactive state: the events, the timeouts, and the error conditions, each named with the code that acts on them.
3. The call sites in question 3 are a population, counted and cited, never characterized as "several callers" or "the display code". They are the part a reader cannot reconstruct from the page's own subject, because they live in files the page is otherwise not about. Cite the set exhaustively when it is small enough to read; when it is too large to cite exhaustively, cite a representative spread — the sites that carry the distinct kinds of precondition — and state how many exist in total, never silently narrowing to one.
4. State the test that decides membership, in the page's own prose, before the sites. "Callers of the mechanism" is not a population: a mechanism's own setup, teardown, and debugfs registration call it too and gained nothing. Without the published test the count is not reproducible, and two writers on one tree will both claim compliance with different numbers.
5. Where the mechanism has more than one active mode, the delta is stated per mode wherever the modes differ, and once where they do not. Stating it once requires naming the construct that makes the modes identical — the shared predicate, iterator, lock, or work item the code actually uses — so that "once" is a finding rather than an omission.
6. A mechanism whose active state is genuinely invisible to the rest of the tree is a finding worth stating: say that nothing else changes, name the search that establishes it, and move on.

**Rule:**

1. The facet is scoped by what drives the mechanism, not by which directory the code sits in. Follow the engage and disengage paths into driver code as far as the page's own subject drives them, and stop where the code stops being about this mechanism.
2. The mechanism's own functions are the page's wherever they are called from, including from a neighbouring subsystem's code. A call site is named, and its enclosing subsystem is not documented: the site tells the reader that the precondition exists, and the surrounding machinery belongs to whoever owns it.
3. Name the stopping point with the symbol at which the page hands off, so a reader can tell a boundary from an omission.

**Before:**

```
DP_PSR_EN_CFG bit 0 enables PSR. The source writes it after the sink
capability block is cached, and writes it again with the enable bit last
so the configuration lands before the feature starts.
```

**After:**

```
DP_PSR_EN_CFG bit 0 enables PSR. The source writes it after the sink
capability block is cached, and writes it again with the enable bit last
so the configuration lands before the feature starts.

Once the sink is refreshing itself, the source stops sending frames and
two paths behave differently. A worker re-arms the hardware after each
exit, and every write to the front buffer now reaches a pair of hooks
that were inert while PSR was off, so a frame that would previously have
been scanned out directly must first bring the link back.
```

**PASS CRITERIA:**

1. Enumerate the page's activatable mechanisms; for a page with none, record that and pass.
2. For each one, confirm DETAILS carries a facet answering all four questions of rule 2, each backed by a fenced block or an inline citation, and that no answer is an assertion without code.
3. Confirm the membership test is stated in the page's prose, and that the call sites are cited exhaustively or as a representative spread with the total stated; re-derive the total on a basis shaped differently from the writer's and reconcile.
4. Confirm the return-to-inactive drivers are named individually — events, timeouts, and error conditions — with the code that acts on each.
5. Where a mechanism has multiple active modes, confirm the delta is stated per mode wherever the modes differ, and that any delta stated once names the shared construct that makes the modes identical.
6. Confirm the facet's handoff points are named by symbol, so every stop reads as a boundary rather than an omission.
7. Pass at one activation-delta facet per activatable mechanism, every claim in it cited, and the precondition population counted.
