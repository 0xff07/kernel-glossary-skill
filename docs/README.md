# kernel-glossary-skill

>**!!! STOP: BEYOND THIS POINT YOU ARE ON YOUR OWN !!!**
>
>Navigate these pages at your own risk. This assumes:
>
>>**`PROPER EXPECTATIONS`**
>
>You know this is NOT the authoritative source of kernel knowledge.
>
>>**`SELF-RESCUE SKILLS`**
>
>You can read C code yourself. So even if the output is an LLM hallucination, you can still track the code and get oriented yourself.
>
>>**`BASELINE EXPERIENCE`**
>
>You are NOT entirely unfamiliar to the given subsystem.
>
>>**`HUMAN ENGAGEMENT`**
>
>You understand that reading these pages is NOT the same as participating in the kernel community. Interacting with humans in the community is.
>
>>**`NO UPSTREAM SUBMISSION`**
>
>Unverified AI patches only create noise and waste maintainers' time. DO NOT attempt to upstream any docs from this project unless you are intimately familiar with that area.
>
>**!!! STOP: BEYOND THIS POINT YOU ARE ON YOUR OWN !!!**

This is an experimental, LLM-generated version of [0xff07/kernel-glossary](https://github.com/0xff07/kernel-glossary).

This agent skill creates ad-hoc write-ups for topics in various kernel subsystems. Use this as a fast scout to explore the Linux kernel source code, or generating good bed-time stories, or use it with other agentic tools (e.g., Hermes, Claws) to create a persistent knowledge base, or whatever you like.

I use this to make temporary save points when exploring the Linux kernel, tracking what has been touched but not yet fully explored. Pages here are for this purpose only. DO NOT treat them as authentic sources of kernel knowledge.

## Setup

### Prerequisites

Set up [`facebookexperimental/semcode`](https://github.com/facebookexperimental/semcode). You need both the binaries and the MCP.

After installation, create your first semcode DB by indexing a range of commits. For example, to index all commits from v6.17 to v7.0:

```
semcode-index --git 'v6.17..v7.0' --db-threads $(nproc)
```

Optionally, you may want to index the mailing list archive with `semcode-index --lore`, for example:

```
semcode-index --lore lkml
```

That way, you can reference the mailing list archive locally from an LLM. See [`lore.md`](https://github.com/facebookexperimental/semcode/blob/main/docs/lore.md) for more information.

### Use with Claude Code

To use it with Claude Code, simply clone it into the `.claude/skills/`:

```
# In kernel root
git clone https://github.com/0xff07/kernel-glossary-skill.git ./.claude/skills/
```

Launch Claude Code in the root directory of the kernel source code:

```
# In kernel root
claude
```

Confirm the skill is loaded by running `/skills`.

```
# In Claude Code
> /skills
```

If this is loaded, Claude will output something like this:

```
  Skills
  1 skill

  Project skills (.claude/skills)
  kernel-glossary-skill · ~68 description tokens
```

You can now start using it!

## Usage

For a single page, just ask for one topic (for example, "write a page on the xHCI command ring for v7.0"): one agent runs the whole pipeline inline and asks before saving. Larger work flows through three separable phases, each resumable from files under `campaign/`, so a phase can run in a different session — or on a different machine — from the one before it. The skill's full contract lives in `SKILL.md`; the per-stage procedures and dispatch briefs live under `guidelines/passes/`.

```
plan ──────────────► write campaign ─────────────► verify campaign
produces              writer → fixer per page       find-only verifiers + fixers
campaign/<c>.md       pages: WRITTEN → LINTED       pages: CERTIFIED or deferred
(no pages yet)        docs/<dir>/...                campaign/<c>-verify.md (committable)
                            ▲                              │
                            └──────── delta catalog ◄──────┘
                                      seeds a delta write campaign
```

### 1. Planning

Turns a rough topic list into a user-approved campaign plan at `campaign/<campaign>.md`: parallel read-only inventory agents digest the subsystem, the orchestrator curates the page catalog itself (scope statements, anchor symbols, boundary rules with seam symbols, fold-in adjudications, batch order), a fresh agent adversarially reviews the catalog, and planning ends at a user checkpoint — the genuine scope questions plus the standing verification-cadence question, then an explicit go. No page is generated in this phase.

Example prompts:

> /kernel-glossary-skill read prompt.md and plan

> Plan a documentation campaign for the DRM/KMS subsystem at v7.0. The topic list is in prompt.md; it is rough, so inventory the tree and curate the catalog. Don't write any page yet.

What to expect back: a plan file under `campaign/`, a summary of the catalog, and 2-4 checkpoint questions (scope options, optional pages, when verification should run). Generation starts only after you answer and give the go.

Procedure: `guidelines/passes/plan.md`.

### 2. Writing campaign

Executes an approved plan in batches of about five pages. Per page, a writer agent researches with semcode and writes the complete page — it owns all the facts, closes the catalog-to-DETAILS parity table, runs the mechanical exit suite (excerpt byte-compare, link-anchor confirmation, second-basis count re-derivation), and persists the evidence into the page's dossier.

Then, a cheaper fresh-context fixer sweeps the prose, fixes the settled style classes in place, and escalates anything unsettled for the orchestrator to adjudicate at the batch checkpoint. Pages land under `docs/<dir>/` in state WRITTEN → LINTED; they are deliberately not yet certified. A write campaign can also start from a verify campaign's delta catalog instead of a fresh topic list — that loop is described under Verification below.

Example prompts:

> Resume the drm campaign and start batch B1 per the plan.

> Execute the approved plan at campaign/drm.md. Run batches B1 through B3, checkpointing between batches.

What to expect back: per-batch checkpoints reporting pages done/remaining with writer and fixer evidence, the plan file's Status section updated after every page, and dossiers/parity tables/lint reports accumulating under `progress/<campaign>/`.

Procedure: `SKILL.md` ("Modes"), with the writer brief in `guidelines/passes/02-write.md` and the fixer brief in `guidelines/passes/03-lint.md`.

### 3. Verification campaign

Certifies written pages, per the cadence chosen at the planning checkpoint or whenever you ask. It is its own run: the orchestrator curates a verify plan at `campaign/<campaign>-verify.md` (page-by-page check inventory plus the cross-page checklist: seam consistency, fold-in landing, catalog coverage), dispatches find-only verifier agents (one per page running Gate A and Gate B with recorded evidence, plus one cross-page agent), adjudicates every finding itself, and stamps each clean page CERTIFIED — mirrored into the parent plan's Status.

Its only in-place edits are settled style fixes applied through fixers; factual findings are never edited during verification. Instead they accumulate — with the verifier's evidence and fix specifications, plus the page's boundary rules and tree pin copied in — into a delta catalog inside the verify plan. Plan files are committable under `campaign/` (artifact directories stay local), so the certification census and the delta catalog travel with the repository in the verify plan. It also works on a corpus with no artifacts at all (pages written elsewhere): the plan is then regenerated from the pages themselves.

Closing the loop: the delta catalog seeds a delta write campaign. Its rows become that campaign's page catalog and the verifier evidence stands in for the inventory, so planning skips straight to your checkpoint; the delta write campaign's writers repair their pages under the derivation rules, fixers sweep as usual, and the next verify campaign re-checks only the still-uncertified pages — each write → verify → delta round shrinks.

Example prompts:

> Run a verify campaign over the drm campaign.

> Verify docs/drm against the v7.0 tree. There are no campaign artifacts on this machine; plan the verification from the pages alone.

> The first write batch is done — run the calibration verify pass over those five pages before batch 2 launches.

> The drm-verify campaign deferred six pages. Start a delta write campaign from its delta catalog, then re-verify those pages.

What to expect back: a committable verify plan carrying the census and the delta catalog, per-page verify reports as local artifacts under `progress/<campaign>-verify/`, style fixes applied and re-checked, and a final per-page CERTIFIED / deferred (delta recorded) / waived census — with the deferred pages' findings ready to seed a delta write campaign.

Procedure: the verify-campaign section of `guidelines/passes/04-verify.md`; delta campaigns in `guidelines/passes/plan.md` ("Delta write campaigns").

### Notes

- The documented kernel version is pinned once per run (tag plus commit) and every citation checks against that tree; state it in the prompt or let the skill derive it from the local checkout.
- Pages save under `docs/` without per-page asks once a catalog is approved, but the skill never makes git commits without your explicit go.
- `progress/` entries are per-run and isolated; a new run never reads another run's files unless you explicitly ask it to resume, reuse, or verify that run.

