# Writing a kernel-glossary page

The reader knows the kernel and not this subsystem, and has the page open with no terminal and no tree. Everything the page explains is on the page, and everything on the page is there because that reader needs it. Every fact is checked against the on-disk tree at the documented version; a hint from an index or a dossier is never a citation.

## The page [page]

What a Linux-kernel page is made of, its sources, its fixed sections and their forms, its links and the coverage its constructs demand, is the profile's: `guidelines/kernel.md`. What holds for any page:

1. [page.self-contained, qa] No link points to another page of the knowledge base (a target ending in `.md` that is not a URL) and no page of it is named in prose: each page is self-contained, reaches as far as its subject drives the code, and stops where the code stops being about that subject. A boundary is a floor and never a fence: it fixes what a page must cover exhaustively and what it may not catalog, and it never stops a page explaining a symbol its own narrative reaches. So a page that would write "the arithmetic behind each is bandwidth/credits.md's" writes the arithmetic, and one that would write "which owns those bits" draws the bits; where the fact is too large for the space it has, the sentence stops at what this page's own code does and points nowhere. Deleting the page's name and leaving the handoff, "a callback another page owns", "documented elsewhere", is the same defect and the QA reading inventory carries those and the table column that says which page owns a row rather than what the row holds. No template residue (`{{`, `TODO`, `XXX`, `FIXME`) survives outside a fence; a source's own marker named as such, "the FIXME in the switch above", is a mention and stays.

2. [page.one-line-paragraphs, qa] Every paragraph is one unwrapped line, and a blank line separates it from the next; only fences, figures, list items, table rows and blockquotes break lines. Cited code keeps its tabs, which [excerpts.verbatim] compares byte for byte.

## Lead and SUMMARY [lead-summary]

1. [lead-summary.lead, qa] The lead says what the mechanism is for, where it sits and what the page traces, and then stops; every sentence is purpose, position or promise, with the promise last, and none opens on a symbol, count, size or ordinal. Normally 60 to 120 words, one or two paragraphs and four to six sentences, with at most one figure of 8 to 80 lines and no table, list or excerpt. 121 to 220 words, three paragraphs or seven or eight sentences are review candidates with a recorded reason, and more than that fails; a figure over 80 lines is read for what it could drop. The lead may end on its figure. The rules measure the bands and the blocks and list the sentences; their roles are tagged by hand in the dossier.

2. [lead-summary.summary, qa] SUMMARY is a map: the model, then the primary journey with its governing invariant or boundary, every sentence carrying one of those four roles, and a claim the lead already makes kept only where it adds a relationship, phase or constraint. Normally 80 to 160 words, two paragraphs and four to six sentences; 161 to 300 words, three paragraphs or seven to nine sentences are review candidates, and more fails. It may carry one table of at most six body rows and four columns or one figure of 8 to 80 lines, read over 80, never both and never an excerpt, with prose on both sides; beside a block the prose is 60 to 140 words in total, across both sides of the block, and never more than 220. Inventories belong in COVERAGE, bit and register breakdowns in section six, and execution, variants and error paths in DETAILS. The rules measure the bands and the blocks and list the sentences; their roles are tagged by hand in the dossier.

3. [lead-summary.claims-audited] Quantified and universal claims in the lead and SUMMARY are audited like any other and agree with the DETAILS evidence; compression drops detail, never accuracy.

## Purpose, then model, then symbols [purpose]

1. [purpose.openers, qa] The lead and the first paragraph of every section and subsection open on what the thing is for and the conditions under which its result holds, and introduce the implementing symbols after that. Delete a number from a first sentence: if what remains still says what the thing is for, the number was incidental; if nothing remains, the sentence was a count. The listing prints every opener and flags one led by a symbol; the purpose test is read.

2. [purpose.spine, qa] DETAILS is organized as the model or the journey: one subsection per phase in run order, or per role, state or class, with each cataloged symbol shown inside the phase where it acts. One subsection per symbol in catalog order is the failure to avoid.

3. [purpose.state-sets] A fixed set of states, modes or classes is a table of member, meaning and defining construct; a state set also shows its transitions and what drives each, and a taxonomy says what distinguishes each class.
4. [purpose.transitions] A transition carries forward the condition or relationship that makes the next explanation necessary, in the order the source establishes, with an explanatory sequence kept distinct from runtime order. Recurring objects keep the names a figure or an earlier paragraph gave them, and an object is identified again where another function calls it by a different local name.
5. [purpose.generic-first] Order DETAILS generic to specific: the shared mechanism first, then the vendor, channel or driver instances. A reason behind a result stays the comment's or the commit's words, attributed.

## Excerpts and their explanation [excerpts]

The provenance comment every fenced C block opens with is kernel.md [provenance].

1. [excerpts.verbatim, qa] Whatever the page explains, the real code is on it, verbatim: never fabricated, paraphrased or approximated, located with the semcode tools and read on disk, tabs and comments kept. A symbol whose code cannot be located gets no block.

2. [excerpts.catalog-parity, qa] Every catalog symbol appears in at least one fenced C block; the rule checks that much and no more.

3. [excerpts.definition-and-usage] Every catalog symbol gets its definition excerpt and at least one usage excerpt, evidenced row by row in the dossier's PARITY table (dossier.md [parity.closed]). A call-chain walk shows the invocation site and the callee body as separate blocks; a switch, loop or condition whose structure is the point is reproduced, never paraphrased; a macro or static array the prose depends on is reproduced where first depended on; a commit message with a table or figure is reproduced in a plain fence.
4. [excerpts.whole-definitions] A definition is reproduced whole in one excerpt, comments and `#ifdef` regions included, never split across excerpts and never thinned to the members the prose happens to explain; `...` drops only a run of members the page never mentions, and the prose says so. A long definition is explained beside its one excerpt under [excerpts.members-named], whose member table carries what one paragraph cannot.
5. [excerpts.function-splits] A function of up to about forty lines is shown whole. A longer one is split at the boundaries of its stages, each part the stage entire: the signature with the first part, a condition beside the write it guards, a loop, branch chain or locked region unbroken, the error labels with the writes they undo, and each later part reintroduced by function and stage and opening on the signature it belongs to ([excerpts.enclosing]). The lines a claim rests on are shown with the statements around them that make the site unmistakable, because a function can repeat a pattern, the same assignment in two branches, and a cut that shows only the pattern shows neither. Elsewhere `...` elides only intermediate code that changes nothing for the reader, never a truncation.
6. [excerpts.introduced, qa] The sentence above a fence names the construct the excerpt shows, or the function a body fragment belongs to, as a link to its definition line, and says what to notice. A mention in a heading, a table cell, the provenance comment or a location link does not count, a mention above a previous heading, figure, table, list or excerpt does not carry, and a fence with several units is introduced for every unit. The rule checks the name and the link; what to notice is read.

7. [excerpts.post-fence-subject, qa] The first sentence after the fence names that construct again by symbol, linked, and explains the behavior, condition or consequence the lines establish; "it", "this" or "the flag" as its opener sends the reader back across the fence. A conclusion is stated on one side of the excerpt only. The listing flags a pronoun opener and a sentence naming no symbol; the explanation and the one-side rule are read.

8. [excerpts.members-named, qa] Beside a definition, every member shown is explained, what it holds and which path writes or reads it; a run the source's own comment groups, or the neighbours shown around the member a paragraph is about ([excerpts.contiguity]), may take one phrase naming them and what they hold. A table above the fence naming each shown member with its purpose serves as that explanation, and the paragraph after it then says only what the table leaves out. How many members there are or where the struct sits is shape, and shape is not explanation.

9. [excerpts.claims-nearby] A behavioral claim has its condition, operation or ordering in nearby source: a caller excerpt proves the call, the callee's lines prove what it does. A sentence names the operation and the condition that controls it and claims only what that operation establishes; a claim about an author's motivation is attributed to a comment or a recorded discussion.
10. [excerpts.sufficiency, qa] The page passes the sufficiency test when a reader with only the page open can say exactly which lines run on the documented path. A location link names a site and never stands in for its code: a sentence that says what happens at a line names the function and the operation there, and when the page reproduces the line elsewhere it says where; the location links to lines no excerpt reproduces are listed for reading, a range counting as reproduced only when every line of it is, and a paragraph whose unreproduced links reach two files is [excerpts.cited-shown]'s.
11. [excerpts.cited-shown, qa] Prose that says what happens at a site shows the site. A paragraph or list item whose location links reach two or more files that no excerpt on the page reproduces is a file jump and fails: the reader follows one sentence with several files open, and the page's flow breaks at every link. Where the prose explains what a function does at a line, those lines are reproduced beside it, as many blocks as the explanation takes, each introduced and explained like any excerpt; this is the floor of [excerpts.claims-nearby] where a claim reaches across files, and a reach the page's subject does not drive is cut under [page.self-contained], never cited unshown. A census is different: a paragraph that cites the members of a set as evidence for a claim states the set's total, by number or by the quantifier the claim carries, and lists the members with nothing longer than a label between them; the rule lists it for reading instead of failing it, and a census of four or more members is a table under [style.run-on-enumeration]. A total followed by what each member does is an explanation and shows the code. A table row is a lookup and is not counted. The rule counts, per paragraph, the files its location links reach whose cited line, or any line of a cited range, no excerpt unit on the page reproduces.
12. [excerpts.enclosing, qa] An excerpt says what it shows lines of without the prose. Every construct a unit reproduces lines from, a function, a struct, union or enum definition, a macro, a top-level initializer or a kerneldoc block, has its opening line in the unit: the first line of the signature, the `struct foo {` line, the `#define`, or the `/**` with the title line beneath it that names what the kerneldoc documents. The unit begins there, elides with `...` to the lines it is about, shown with their neighbours ([excerpts.contiguity]), and may close on the construct's `}` or `};`, which an elision reaches as the first column-0 closing brace that follows. A member reproduced alone, `bool is_unplugged;`, is otherwise indistinguishable from a local. A later unit of the same fence continuing a construct an earlier unit opened is covered by that unit; a unit in another fence opens the construct again. The rule maps each reproduced line onto the tree, finds the construct it lies in and looks for that construct's opening line among the unit's lines.
13. [excerpts.contiguity, qa] An excerpt reads as code, not as a skeleton of it. A unit carries at most two elisions, one between its opening line and the lines it is about and one before its closing line, and every run of reproduced lines after an elision is at least three lines and normally the stage entire, a member with its neighbours, or a statement from the condition that guards it to the return or label that follows it, unless the run is the construct's closing line alone. One line between two elisions is a fragment; where the lines a unit is about lie far apart, show what lies between or, for a function, open it again in a second unit ([excerpts.function-splits]); a definition is never split ([excerpts.whole-definitions]). The rule counts the elisions and the run lengths of every unit.

## Arrangement [arrangement]

1. [arrangement.units, qa] Each DETAILS subsection is one unit of understanding: a behavior, relationship or stage, with its prose, source and figures beside each other. Its blocks are prose (P), excerpts (C), figures (D), tables (T) and other fences (Q); a list or a `####` heading is neither prose nor a block and gives no recovery.

2. [arrangement.open-close, qa] A subsection opens with a prose paragraph of normally two to four sentences and closes with one of one to three. No block directly follows a heading or a `####` heading, and no block touches the end of the subsection or another block. The prose between two blocks explains what the first established and connects it to the next, and one sentence can do that when it also names the subject and introduces the next construct; when it would have to reconstruct context the excerpts omitted, enlarge or combine the excerpts instead.

3. [arrangement.paragraphs, qa] A paragraph carries one relationship, normally two to four sentences and 45 to 80 words; over 80 it is read for a second relationship, and over 120 words or more than five sentences it is reviewed. Sentences run 18 to 28 words, and three consecutive over 35 are reviewed. No two directly consecutive one-sentence paragraphs, no more than three ordinary paragraphs in a row, no three consecutive paragraphs over 80 words, and a subsection without a block stays under about 250 words.

4. [arrangement.subsection-size, qa] A subsection is normally under 400 prose words; over 600 words or more than eight paragraphs it is read for a second explanatory question, a repeated conclusion or missing evidence, and split at the boundary between its parts or kept whole with the reason recorded. Boundaries follow the explanation, never block count, and no count of blocks bounds a subsection.

5. [arrangement.block-size, qa] An excerpt normally runs 6 to 40 source lines, provenance comments and elision markers excluded, which is room for a stage entire, a whole short function or a definition with its neighbours; over 40 it is read for whether its lines are one stage or one definition reproduced whole. A figure normally runs 8 to 80 visible lines, room for a topology, a timeline or a register map drawn as the writer sees it; over 80 it is read for what it could drop. A local figure may be smaller when its objects stay recognizable.

6. [arrangement.headings, qa] A `###` heading is a declarative clause of at most ten words, true of everything in its section; a condition or implementation detail the reader does not need to find the subsection moves into its opening paragraph.

7. [arrangement.tables] A comparison of operations under conditions is a table before the excerpt, with plain-English cells and every symbol linked in every row, and a member table beside a definition keeps the placement that makes the explanation available. Two representations may cover one relationship when each adds something; prose that reads a table row by row is removed.
8. [arrangement.figure-placement, qa] Place a local figure where a spatial, temporal or transformational relationship would cost the reader effort to hold, before or after source that needs continuous reading and never inside it; no figure count is a target, and variation follows size, role and stage.

## Links [links-pointer]

Every symbol outside a fence links to its definition line, and every location the prose describes links to that line; the URL forms, the classes that are always linked and the settled bare spans are kernel.md [links].

## Facts [facts]

Which constructs, sites and limits a kernel page covers, and which drivers may serve as its examples, is kernel.md [coverage]. What holds for any page's claims:

1. [facts.universal-claims, qa] "Only", "never", "always", "all", "every", "exactly N", "the single" and "once" assert the size of a set: enumerate it first, with `find_callers` plus a tree-wide grep that includes headers, then cite every member with location links or weaken the sentence. A per-member claim is verified by building the member-to-property mapping; one exception falsifies it, so restrict the family or name the classifier and what falls outside it.

2. [facts.two-bases, qa] Every count is re-derived on a second, differently shaped basis before the page is reported, and the dossier records both bases and every enumeration's search scope. The page publishes the result and the scope condition that makes it true (version, architecture, CONFIG option, file or directory), never the search: no grep, index, basis or negative search on the page, and an exhaustive member list only when the members teach a sequence, taxonomy, contrast or ownership boundary.

3. [facts.guards] A restated guard or threshold is derived from the reproduced code by exact negation of its operator with the exact constants, shown as a code block beside the sentence. Prose never outruns its excerpt, and the semantics a primitive's name carries (an ordering suffix, a `_locked` variant, an RCU flavor, saturation) are stated. An invariant ("set once", "always under lock L", "freed only through F") gets a counterexample search over every assignment site, lock-less caller and free path, citing the kernel's own enforcement where it exists. Headings are claims, true of everything in their section, re-checked after every rewording.
4. [facts.activation-delta] A mechanism that can be switched on carries its activation delta, each answer from cited code: what runs while it is active, what code stops (say when nothing does, and put the disengaging write under the fourth question), which pre-existing call sites gain a precondition, counted and cited or a representative spread with the total, after the membership test is stated in prose, and what drives the return to inactive. State the delta per active mode where modes differ and once where they do not, naming the construct that makes them identical; follow the engage and disengage paths as far as the page's subject drives them and name the symbol at which the page hands off.
5. [facts.counts-serve-claims, qa] A count that serves no claim is noise. Counts are what survive checking, so a writer drifts toward producing them; what the reader understands is the test, and an enumeration that is the finding says what it shows before its size. A population of code locations counted for its own sake teaches nothing: the reader learns a number and no mechanism. Such a count earns its place only where it establishes an invariant, a boundary or an ownership split, and then the paragraph states that claim before the count and the count proves it. A closed set whose members are themselves the content, the fields of a register, the values of an enumeration, the states of a machine, is enumerated because a reader must be able to look each member up, and needs no such warrant.

6. [facts.derived-pages] A page derived from prior material inventories the source (catalog, sections, behaviors, enumerations, figures, references), gives every item a disposition (kept and where, merged where, or cut with the reason), shrinks the catalog and the scope statement in the same change as any cut and reports it, and passes the parity audit on its own; every claim taken from a draft is re-found on disk. The catalog and the scope statement define done-ness, and compression removes words, never coverage; every anchor the scope names has a location on the page or a recorded scope reduction, and removing a catalog entry never discharges it.
7. [facts.unwitnessed] A claim the tree cannot witness, such as intent or motivation, is scoped out, weakened to what the evidence shows, or stated with its basis disclosed; "could not verify" is reserved for that class.

## Figures [figures-pointer]

Draw a figure where a spatial, temporal or transformational relationship would cost the reader effort to reconstruct, never for a call chain, a two-state toggle or anything one sentence conveys with less effort; strip the labels, and what remains must still assert something. `guidelines/figures.md` carries the banned shapes, the geometry, the register styles and the pattern index.

## Style [style]

Each row states the form a sentence takes, what the check sweeps for its absence, and what is exempt. The check runs its sweep over a prose view of the page (fences dropped, links reduced to their text, code spans, quoted text and file:line citations masked), case-insensitively and never anchored to line start, because a paragraph is one line and an anchored pattern sees only its first clause (a heading sweep anchors, since a heading is one clause), and again after every edit; its `tools/qa/checks/<id>.py` module implements the sweep, with dots and hyphens in the ID replaced by underscores. A pattern generates candidates and the exempt column decides; an exempt construct stands as written, and a new exemption lands only through the user. An exemption a regex can name is implemented and tested in the check; one that needs reading is recorded in the dossier's LINT as `EXEMPT <rule-id> "<a fragment of the flagged text>": <the ruling applied>`, which `kg check` reads (dossier.md [lint]).

| form | the check sweeps | exempt | requirement |
|---|---|---|---|
| A second sentence, or a parenthesis, where an em dash would go. | the em dash character | a verbatim quotation; figure text is swept | style.em-dash, qa |
| Plain text; emphasis comes from the shape of the sentence. | `**` on the raw file | `/**` kerneldoc openers inside fences | style.boldface, qa |
| A sentence states what the thing is and does; the design it is not is named only where a reader would otherwise assume it. | a denial joined by a comma or "and", "rather than" and "instead of", then read | a quoted comment; a comparison whose denied alternative is a real design the reader could otherwise assume | style.negative-construction, qa |
| A location is stated as its mechanism: defined in a file, held in a struct, attached behind a pointer, occupying a slot; a field transitions through its values. | the lemmas live, sit, hang, want | the adjective ("the live ring"); a real actor; a verbatim quote; hardware earns no exemption | style.placement-verbs, qa |
| A scalar advances, increments or wraps; a data structure is walked. | the verb "walk", then read | traversing a data structure | style.walk, qa |
| A struct of function pointers is named by its type, or as a function pointer struct. | the word "vtable" | nothing | style.vtable, qa |
| A heading names what the section is about; the count opens the paragraph beneath it. | a heading opening on a cardinal number, word or digit; every DETAILS H3 and H4 read | nothing | style.counting-headings, qa |
| A DETAILS heading is a declarative clause with a verb, what does what. | a heading opening on Why, How, Where or What, or ending in a question mark, and a DETAILS H3 with no word that reads as a verb, listed for reading; every DETAILS H3 and H4 read | the H3 catalog labels of COVERAGE | style.headings, qa |
| A relation is one declarative sentence with its own verb; a quotation is introduced as "According to the comment <quote>, ...". | a short label ending in a colon before a word, a digit or a span, outside table cells | the paragraph-final colon that introduces the fenced excerpt on the next non-blank line; colons in H3/H4 labels, link titles, code, URLs, ratios, catalog bullets, table cells and double-quoted text | style.label-colon, qa |
| Under DETAILS and SUMMARY the members of a set are one flowing paragraph or a table, one row per member. | every list under DETAILS or SUMMARY, which fails; the lead's is [lead-summary.lead]'s | the catalog lists of COVERAGE, DOCUMENTATION and OTHER SOURCES; the entry bullets of section six; tables | style.lists, qa |
| A ranking or importance word sits in the same clause as the mechanic that makes it true and goes when the mechanic is absent; an "is what" or "matters" frame becomes the plain claim. | the words listed below, the "is what" and "matters" frames and "the reasoning"; every adjective read with the deletion test | "fast path" and "slow path" where the kernel names them; verbatim quotes | style.superlatives, qa |
| The rule, count or helper a word stands in for is named: a rule for "contract", a count for "tally", the defining site for "canonical", and "branch", "case" or "side" for the noun arm. | contract, tally in every form, canonical, and the noun arm for a branch or case | Arm, ARM64, arm64; the verb ("arms a timer"); verbatim quotes | style.banned-words, qa |
| A claim names the exact condition the code tests; a frequency or a degree comes with the counter or branch it was measured on. | usually, typically, generally, often, normally, commonly, mostly, in practice, tends to, on a hot CPU, simply, essentially, basically, arguably | hyphenated compounds; a hedge inside a quote; a measured statistic that cites its counter | style.hedges, qa |
| The page states the result with its scope condition; how it was established lives in the dossier. | grep, semcode, the caller index, a search or second basis, re-derived, verified negative, verified absent, and a tree-wide search, scan or sweep | verbatim quotations; a page about search tooling; a scope condition is never a hit | style.verification-narration, qa |
| Four or more members of one set are a table, one row per member, every construct linked in every row. | a sentence carrying four or more members of one set (three commas plus " and ", ranked by distinct file:line locations, read) | the steps of one operation; the member-by-member walk beside the excerpt that shows those members | style.run-on-enumeration, qa |

Superlative and importance words: the most invasive, the most fragmenting, the most aggressive, the most consequential, the most or least preferred, the most expensive, the cheapest, the cheap path, the slow path, the fast path, the strongest or weakest guarantee, the worst or best outcome, the entire performance or correctness benefit, the key invariant, the key difference, the key innovation, the key role, the design assumption, the design intent, X matters, X matters because Y, X is what makes Y, what makes X work, the only mode that, elaborate, elegant, fundamental, cornerstone, linchpin, crucial, critical. Label-colon families, all one shape: "The reasoning:", "The intent:", "The asymmetry:", "The fix:", "The point is:", "The takeaway:", "The pattern is:", "is the key:", "is essential:", "is explicit:", "is significant:", "is conservative:", "is deliberate:", "is the linchpin:", "is asymmetric:", "is intentional:", "is correct:", "becomes clear here:", `says: "`, `spells this out: "`, `makes explicit: "`, `Comment: "` (the COVERAGE bullet form `Comment: "..."` is a catalog entry and stays).

The sweeps reach body prose and headings, and figure text for the em dash, the negative construction and the placement verbs; never a source excerpt or a verbatim quotation.

## Before and after [before-after]

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

A verification narrated. **Before:**

```
Those three are the complete caller set at this tree, by a tree-wide grep
and the semcode caller index alike.
```

**After:**

```
Three paths call the helper. Hot-unplug, system resume, and runtime resume
all use it before removing router state.
```

An opening that names the helper before the result. **Before:**

```
Turning the lane back on is the first step of bonding it, and the enable
has to be followed by a wait, because a lane whose Lane Disable bit was
just cleared has not trained yet. tb_xdomain_lane_bonding_enable() does
the two in order before it touches the bonding bit.
```

**After:**

```
The XDomain bonding path checks that the secondary lane has come up after
enabling it. tb_xdomain_lane_bonding_enable() calls tb_wait_for_port() on
the secondary adapter after tb_port_enable() succeeds.
```

A transition that leaves the previous result behind. **Before:**

```
A host router has no DROM to describe itself, and some device DROMs omit
the pairing, so the driver needs a rule that produces the same answer the
hardware uses. The rule is adjacency, because lane adapters are numbered
in pairs and the lower number is the primary, so
tb_switch_default_link_ports() scans the adapter array for a lane adapter
immediately followed by another one.
```

**After:**

```
Pairing left unset by the DROM can be supplied by the default pass.
tb_switch_default_link_ports() examines adjacent lane adapters and
assigns their pairing when both dual_link_port pointers are unset.
```

Objects that lose their identity across functions. **Before:**

```
tb_configure_link() sets remote on the downstream and upstream primary
adapters unconditionally and on their siblings whenever both ends have a
dual_link_port, so on a two-lane link four adapters end up with a peer
pointer.
```

**After:**

```
tb_configure_link() connects the parent's primary adapter to the child's
primary adapter through their remote pointers. When both ends have a
dual_link_port, it also connects the parent's lane 1 adapter to the
child's lane 1 adapter. Each dual_link_port continues to identify a
sibling on the same router.
```

A producer and its consumer explained apart. **Before:**

```
The predicate that reads the pointer is where the two lanes part, and
tb_port_has_remote() is that predicate.

tb_port_has_remote() answers false for three cases before it answers
true, and the third is the lane rule, under which an adapter that has a
dual_link_port and a non-zero link_nr is the secondary lane and is
treated as having nothing behind it.
```

**After:**

```
The peer pointer and the traversal decision describe different properties
of a lane adapter. tb_port_has_remote() checks the adapter's direction
and peer presence before applying its secondary-lane condition.

    /* drivers/thunderbolt/tb.h:620 */
    static inline bool tb_port_has_remote(const struct tb_port *port)
    {
    	if (tb_is_upstream_port(port))
    		return false;
    	if (!port->remote)
    		return false;
    	if (port->dual_link_port && port->link_nr)
    		return false;

    	return true;
    }

tb_port_has_remote() rejects the secondary adapter when
port->dual_link_port is set and port->link_nr is nonzero. The peer
pointer remains populated on the adapter this condition excludes. The
upstream guard also applies to primary adapters.
```

A sentence that outruns its operation. **Before:**

```
A failed write returns before the log line, so a message in the log
means the register really changed.
```

**After:**

```
__tb_port_enable() returns immediately when tb_port_write() reports an
error. A zero result allows execution to reach tb_port_dbg().
```

The passages are plain text so that no line number or link in this file goes stale; on a page every symbol is linked.
