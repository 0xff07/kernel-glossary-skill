# WRITING: What a page is for

> Replaces PAGE-07, PAGE-08, PLOT-01, PLOT-02 and PLOT-03; restores the June 2026 doctrine on code walkthroughs and the sound campaign's rule of 2026-08-20 on counts. Read this file first, before any rule below it: it says what every other rule exists to protect.

The reader knows the kernel but not this subsystem, and has the page open with no terminal and no tree. Everything the page explains has to be on the page, and everything on the page is there because that reader needs it.

**1. Purpose before mechanism.** The lead, and the first paragraph of every section, opens on what the thing is for and where it sits: the problem it solves, who decides and who performs, what is above it and what is below it, in words that need nothing the reader has not read yet. A symbol name, a count, a size, a position, or "the second of the three" is never a first statement; each comes once the reader knows what is being named or counted. Delete the number from a first sentence: if what remains still says what the thing is for, the number was incidental; if nothing remains, the sentence was a count and not an opener.

**2. The model before the symbols.** The lead and SUMMARY say what the topic is as a model, the states and their transitions, the phases of the process, or the taxonomy of the parts, mapped onto the kernel constructs that carry them. DETAILS is organized as that journey or model: one section per phase in run order, or per role, state or class, with each cataloged symbol shown inside the phase or facet where it acts. One section per symbol in catalog order is the failure this rule names. A fixed set of states, modes or classes is a table with a member, a meaning and the defining construct; a state set also shows its legal transitions and what drives each; a taxonomy says what distinguishes each class from its siblings.

**3. The excerpt and its explanation, side by side.** An excerpt is a claim that the reader needs to see those lines, and the paragraph beside it pays that claim off. Beside a definition it names each member the excerpt shows and says what the member holds and which path writes or reads it; beside a function body it says what the shown lines do to the objects the page is about. How many members there are, which pass writes them, or where the struct sits relative to another is the excerpt's shape, and shape is not explanation. A member the paragraph does not explain is not shown: elide it with `...` and say what the elision drops. A long definition is several excerpts of a few members each, each explained where it stands, never one excerpt with one paragraph. Show the code, then explain it, interleaved through DETAILS.

**4. Counts serve claims.** A number is on the page to support something the reader is meant to understand: an organizing observation, a structural claim, a limit the code enforces. An inventory with no claim behind it is noise, and "the table holds 30 members, 24 function pointers plus 6 data members" teaches less than "the callbacks fall into four groups by when they run". Where an enumeration is the finding, say what it shows before its size. Every count that does ship is verified against the tree (FACT-03).

**5. SUMMARY is short.** It carries the model in prose and the state set with its transitions, at most one table and one figure. A member table, a per-bit or per-request table, and the detail of any one path sit in DETAILS beside the excerpt they describe, never in SUMMARY.

**6. The page is the whole source.** Whatever the page explains, the real code is on it, verbatim and with provenance (PAGE-02, PAGE-03); a link navigates, the excerpt teaches. Figures show structure the prose cannot carry, never a call chain (DIAG-01).

## Before and after

A lead. **Before:**

```
A root-hub port on a PCI-attached xHCI host carries three groups of
writable control bits that decide whether it is powered, what link state
it holds, and which events wake the machine through it.
```

**After:**

```
A USB port carries both the power a device draws and the link it talks
over, and the kernel controls each of them on its own, apart from the
data traffic through the port. Powering a port off saves the current a
device would draw and isolates a device that has stopped behaving. A
device the USB core suspends needs its link driven into a low-power
state, and driven back out of it when the device is needed again. ...
```

The paragraph beside a struct excerpt. **Before:**

```
One struct xhci_port exists per hardware port for the lifetime of the
host controller's memory setup. The first five fields are what the
construction pass writes, and everything after them belongs to paths
that run once the root hubs are live.
```

**After:**

```
port_reg is the port's register quad in MMIO, and every PORTSC read or
write on this page goes through it. hw_portnum is the port's index in
the flat hw_ports array, the numbering a Port Status Change Event
carries minus one, which is how handle_port_status finds the port.
hcd_portnum is its index inside the root hub that claimed it ...
```

A count standing in for a claim. **Before:**

```
At v7.0 the table holds 30 members, 24 function pointers plus 6 data and
policy members. Twenty-two of them are reached through a
snd_soc_dai_set_sysclk() style function ...
```

**After:**

```
The callbacks fall into four groups by when they run. The driver
callbacks (probe, remove, pcm_new, compress_new) run once as the DAI is
brought up, the clocking and format callbacks are driven by the machine
driver from its hw_params hook, and the PCM callbacks ...
```

## Checked by

ROUTINE-04's two generators run over the raw file: the opener generator prints the first sentence of the lead and of every section and tags numbers and ordinals; the member generator prints, per definition excerpt, the members the adjacent paragraphs name and the ones they do not. Both print candidates and neither is the gate. Every printed first sentence is read for rule 1, the paragraph beside every excerpt for rule 3, the DETAILS headings for rule 2 (one heading per symbol in catalog order is a hit), and SUMMARY's tables and figures are counted for rule 5. The evidence is the list of leading paragraphs with verdicts, the per-excerpt members shown and named, and the SUMMARY counts, recorded in the dossier. Pass at zero unadjudicated openers, zero excerpts without their explanation, a journey or model spine, and a SUMMARY within rule 5.
