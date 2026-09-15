"""Check figure width and vertical connections, including the register exception."""
import re

from pagemodel import BOX_DRAWING
from report import Finding, observations

RULE = 'geometry.layout'
MAX_COLUMNS = 120
RULER = re.compile(r'^\s*bit\s+\d')
ELBOW = '─┘'
TITLE_CLIP = 70
PLACEHOLDER = '·'


def character_at(body, row, column):
    if 0 <= row < len(body) and column < len(body[row]):
        return body[row][column]
    return ' '


def joins(character):
    return character == PLACEHOLDER or bool(BOX_DRAWING.match(character))


def loose_verticals(body):
    return sum(
        character == '│'
        and not joins(character_at(body, row - 1, column))
        and not joins(character_at(body, row + 1, column))
        for row, line in enumerate(body)
        for column, character in enumerate(line)
    )


def check(page, inputs):
    for fence in page.quotations:
        yield Finding(fence.start, 'note',
                      'fence skipped as a quotation or listing (no drawing character)')

    listing = []
    total_over = total_loose = 0
    for number, fence in enumerate(page.figures, 1):
        body = fence.body
        over = [row for row, line in enumerate(body) if len(line) > MAX_COLUMNS]
        loose = loose_verticals(body)
        register_exception = any(RULER.match(line) for line in body) and any(ELBOW in line for line in body)

        for row in over:
            message = f'figure {number} line over {MAX_COLUMNS} columns ({len(body[row])})'
            if register_exception:
                message += '; a single-row L-connector register, the exception the register rules name, read it'
            yield Finding(fence.start + 1 + row, 'review' if register_exception else 'FAIL', message)
        if loose:
            yield Finding(fence.start, 'review',
                          f'figure {number} has {loose} loose vertical bar(s) '
                          '(a │ with nothing drawn above or below; a swimlane crossing is allowed)')

        total_over += len(over)
        total_loose += loose
        title = next((line.strip()[:TITLE_CLIP] for line in body if line.strip()), '')
        listing.append(f'fig {number}: {len(body)} lines | >{MAX_COLUMNS} cols {len(over)} | loose │ {loose} | {title}')

    summary = f'figures={len(page.figures)} over-{MAX_COLUMNS}-columns={total_over} loose-verticals={total_loose}'
    yield from observations(rows=listing, summary=summary,
                            data={'figures': len(page.figures), 'over_width': total_over,
                                  'loose_verticals': total_loose})
