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

For a single page, just ask for one topic (for example, "write a page on the xHCI command ring for v7.0"): one agent runs the whole pipeline inline and asks before saving. Larger work flows through two separable phases, each resumable from files under `campaign/`, so a phase can run in a different session — or on a different machine — from the one before it. The skill's full contract lives in `SKILL.md`; the per-stage procedures and dispatch briefs live under `guidelines/passes/`.

```
plan ──────────────► write campaign
produces              writer, then orchestrator check
campaign/<c>.md       pages: WRITTEN → LINTED
(no pages yet)        docs/<dir>/...
```

### 1. Planning

Turns a rough topic list into a user-approved campaign plan at `campaign/<campaign>.md`: parallel read-only inventory agents digest the subsystem, the orchestrator curates the page catalog itself (scope statements, anchor symbols, boundary rules with seam symbols, fold-in adjudications, batch order), a fresh agent adversarially reviews the catalog, and planning ends at a user checkpoint — the genuine scope questions, then an explicit go. No page is generated in this phase.

Example prompts:

> /kernel-glossary-skill read prompt.md and plan

> Plan a documentation campaign for the DRM/KMS subsystem at v7.0. The topic list is in prompt.md; it is rough, so inventory the tree and curate the catalog. Don't write any page yet.

What to expect back: a plan file under `campaign/`, a summary of the catalog, and 2-4 checkpoint questions (scope options, optional pages, granularity). Generation starts only after you answer and give the go.

Procedure: `guidelines/passes/plan.md`.

### 2. Writing campaign

Executes an approved plan in batches of about five pages. Per page, a writer agent researches with semcode and writes the complete page — it owns all the facts, closes the catalog-to-DETAILS parity table, runs the mechanical exit suite (excerpt byte-compare, link-anchor confirmation, second-basis count re-derivation), and persists the evidence into the page's dossier.

Then the orchestrator re-runs those same procedures itself and compares the answers against what the writer recorded; a disagreement is a finding. It adjudicates every residual against the waivers and applies the fixes in place, never delegating either. Pages land under `docs/<dir>/` in state WRITTEN → LINTED, which is where a page's pipeline ends. A write campaign can also start from a list of findings against pages already on disk instead of a fresh topic list; the plan pass calls that a repair campaign.

Example prompts:

> Resume the drm campaign and start batch B1 per the plan.

> Execute the approved plan at campaign/drm.md. Run batches B1 through B3, checkpointing between batches.

What to expect back: per-batch checkpoints reporting pages done/remaining with writer and check evidence, the plan file's Status section updated after every page, and dossiers/parity tables/lint reports accumulating under `progress/<campaign>/`.

Procedure: `SKILL.md` ("Modes"), with the writer brief in `guidelines/passes/02-write.md` and the check procedure in `guidelines/passes/03-check.md`.

### Notes

- The documented kernel version is pinned once per run (tag plus commit) and every citation checks against that tree; state it in the prompt or let the skill derive it from the local checkout.
- Pages save under `docs/` without per-page asks once a catalog is approved, but the skill never makes git commits without your explicit go.
- `progress/` entries are per-run and isolated; a new run never reads another run's files unless you explicitly ask it to resume or reuse that run.

