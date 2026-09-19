"""Helpers the engine's unit tests share: a rule from inline fields, a page from inline text."""
import os
import sys

QA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if QA_DIR not in sys.path:
    sys.path.insert(0, QA_DIR)

from pagemodel import Page          # noqa: E402


CAUTION = ("> CAUTION: AI-GENERATED CONTENT\n"
           ">\n"
           "> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.")
URL = "https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.h#L12"
LINKED = f"[`struct kg_ring`]({URL})"


def page(text):
    """A Page parsed from inline text."""
    return Page("<test>", text=text)


def skeleton(lead="A ring hands values from a producer to a consumer.", summary="The model is one struct.",
             details="### The ring keeps two indexes\n\nThe producer writes at the head.\n",
             registers=None):
    """A full page skeleton around the given lead, SUMMARY and DETAILS text."""
    six = f"## REGISTERS\n\n{registers}\n\n" if registers is not None else ""
    return (f"# The kg ring\n\n{CAUTION}\n\n{lead}\n\n"
            f"## SUMMARY\n\n{summary}\n\n"
            "## SPECIFICATIONS\n\nNone applies.\n\n"
            f"## COVERAGE\n\n### Structures\n\n- [`'\\<struct kg_ring\\>':'drivers/kg/ring.h'`]({URL}): the ring\n\n"
            "## DOCUMENTATION\n\n## OTHER SOURCES\n\n"
            f"{six}## DETAILS\n\n{details}")


EXCERPT = ("```c\n/* drivers/kg/ring.h:12 */\nstruct kg_ring {\n\tunsigned int head;\n\tunsigned int tail;\n};\n```")
FIGURE = ("```\n    Two indexes\n    ───────────\n    ┌────┬────┐\n    │ s0 │ s1 │\n    └────┴────┘\n```")
PROSE = "The producer writes at the head and the consumer reads at the tail."


class TestInputs:
    """Small resolved-input double; real resolver behavior is tested separately."""
    from inputs import Inputs as _Inputs
    require = _Inputs.require
    worksheet_section = _Inputs.worksheet_section
    complete = _Inputs.complete
    missing = _Inputs.missing
    incomplete_reason = _Inputs.incomplete_reason

    def __init__(self, tree=None, worksheet=None, baseline=None, **values):
        self.tree = tree
        self.git = bool(tree)
        self.cache = {}
        self.source_problems = []
        self.problems, self.notes = [], []
        self.worksheet = '<worksheet>' if worksheet is not None else None
        self.worksheet_lines = worksheet.split('\n') if worksheet is not None else None
        self.worksheet_how = 'convention'
        self.worksheet_rejected = []
        self.baseline = baseline
        self.page_digest = 'a' * 64
        self.qa_digest = 'c' * 64
        self.spec = None
        self.base = '/nonexistent/kg-test'
        self.page_path = self.base + '/page.md'
        self.__dict__.update(values)


def observed(findings):
    """Expose inventories and measurements when asserting the preserved algorithms."""
    from types import SimpleNamespace
    from report import Row
    found = list(findings)
    rows = [Row(f.line, f.message, set(f.data['flags'])) for f in found
            if isinstance(f.data, dict) and 'flags' in f.data]
    summaries = [f for f in found if isinstance(f.data, dict) and not ('flags' in f.data or f.data.get('inventory') is True)]
    return SimpleNamespace(findings=[f for f in found if f.data is None], rows=rows,
                           data=summaries[-1].data if summaries else {},
                           footer=summaries[-1].message if summaries else '', all=found)


MINIMAL_PAGE = """# The kg ring

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A bounded ring lets a producer hand values to a consumer without either waiting on the other. This page traces the ring from its definition to the probe that owns it.

## SUMMARY

The model is one struct with two indexes over a fixed slot array. The journey runs from allocation through activation to the drain that releases the slots.

## SPECIFICATIONS

None applies.

## COVERAGE

### Structures

- [`'\\<struct kg_ring\\>':'drivers/kg/ring.h'`](https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.h#L12): the ring and its two indexes

## DOCUMENTATION

- [`Documentation/kg/ring.rst`](https://elixir.bootlin.com/linux/v0.1/source/Documentation/kg/ring.rst): the ring's ABI

## OTHER SOURCES

- [kg: add the bounded ring (commit 0123456789ab)](https://lore.kernel.org/r/kg-ring@example.org)

## DETAILS

### The ring keeps two indexes over one array

The producer writes at the head and the consumer reads at the tail, and the difference between the two indexes is the number of stored values. [`struct kg_ring`](https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.h#L12) holds both indexes beside the slot array.

```c
/* drivers/kg/ring.h:12 */
struct kg_ring {
\tunsigned int head;
\tunsigned int tail;
\tint slots[16];
};
```

[`struct kg_ring`](https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.h#L12) records the head that the producer advances and the tail that the consumer advances. The figure below shows the two indexes on the array.

```
    The two indexes on the array
    ────────────────────────────
    ┌────┬────┬────┬────┐
    │ s0 │ s1 │ s2 │ s3 │
    └────┴────┴────┴────┘
      ▲         ▲
     tail      head
```

The head and the tail advance in the same direction and wrap on the slot array.
"""
