# kernel-glossary-skill

This is an experimental, LLM-generated version of [0xff07/kernel-glossary](https://github.com/0xff07/kernel-glossary).

> WARNING: due to its LLM-generated nature, DO NOT attempt to upstream any docs from this project, unless you are already a renowned expert in that area.

This agent skill creates ad-hoc cross references for topics in various kernel subsystems. Use this as a fast scout to explore the Linux kernel source code, or as a way to bookmark it, or with other agentic tools (e.g., Hermes, Claws) to create a persistent knowledge base, or whatever you like.

> WARNING: due to its LLM-generated nature, DO NOT attempt to upstream any docs from this project, unless you are already a renowned expert in that area.

I use it primarily for bookmarking the Linux kernel source code, to help me track what has been touched but not yet fully explored. Pages here are for this purpose only. DO NOT treat them as authentic sources of kernel knowledge.

> WARNING: due to its LLM-generated nature, DO NOT attempt to upstream any docs from this project, unless you are already a renowned expert in that area.

The output of this skill varies greatly between LLM models. Use it with care. 

> WARNING: due to this nature, never attempt to upstream any docs from this project, unless you are already a renowned expert in that area.

**AI CAN MAKE MISTAKES, SO VERIFY.**

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

