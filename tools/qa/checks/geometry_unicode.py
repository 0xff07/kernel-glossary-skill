"""Find ASCII connectors, preserving the literal text and source exceptions."""
import re

from report import Finding, observations

RULE = 'geometry.unicode'
TITLE_CLIP = 70
ASCII_CONNECTOR = re.compile(r'[\\/|]')
TEXT = r'[^\s\\/|\u2500-\u259f\u2190-\u21ff\u25a0-\u25ff]'
CONNECTOR_EXEMPT = re.compile(
    r'\|\||/\*.*?\*/|(?<=' + TEXT + r') ?/ ?(?=' + TEXT + r')'
    r'|(?<!\S)/(?=\w)|(?<=\w)/(?!\S)|(?<=\w)\|(?=\w)'
)


def check(page, inputs):
    listing = []
    total_connectors = 0
    for number, fence in enumerate(page.figures, 1):
        body = fence.body
        connectors = [row for row, line in enumerate(body)
                      if ASCII_CONNECTOR.search(CONNECTOR_EXEMPT.sub('', line))]
        for row in connectors:
            yield Finding(fence.start + 1 + row, 'review',
                          f'figure {number} ASCII \\, / or | '
                          '(allowed only as a word separator, a path, a C expression or reproduced source)')

        total_connectors += len(connectors)
        title = next((line.strip()[:TITLE_CLIP] for line in body if line.strip()), '')
        listing.append(f'fig {number}: {len(body)} lines | ascii connectors {len(connectors)} | {title}')

    yield from observations(rows=listing,
                            summary=f'figures={len(page.figures)} ascii-connectors={total_connectors}',
                            data={'figures': len(page.figures), 'ascii_connectors': total_connectors})
