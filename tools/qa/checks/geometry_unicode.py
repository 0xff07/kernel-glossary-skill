"""Find emoji and pictographs in figures; any other character may draw."""
import re

from report import Finding, observations

RULE = 'geometry.unicode'
TITLE_CLIP = 70
# the emoji blocks of the supplementary plane (pictographs, emoticons, transport, symbols,
# regional indicators, skin tones), the BMP characters that render as emoji by default, and the
# variation selector that turns a text symbol into an emoji
EMOJI = re.compile(
    '[\U0001F000-\U0001FAFF]'
    '|[⌚⌛⏩-⏬⏰⏳◽◾☔☕♈-♓♿⚓⚡⚪⚫'
    '⚽⚾⛄⛅⛎⛔⛪⛲⛳⛵⛺⛽✅✊✋✨❌❎'
    '❓-❕❗➕-➗➰➿⬛⬜⭐⭕]'
    '|️'
)


def emoji_in(line):
    return [m.group(0) for m in EMOJI.finditer(line)]


def check(page, inputs):
    listing = []
    total = 0
    for number, fence in enumerate(page.figures, 1):
        body = fence.body
        hits = 0
        for row, line in enumerate(body):
            found = emoji_in(line)
            if not found:
                continue
            hits += len(found)
            shown = ' '.join(f'U+{ord(c):04X}' for c in found[:4])
            yield Finding(fence.start + 1 + row, 'FAIL',
                          f'figure {number} carries an emoji or pictograph ({shown}); any other character may draw, an emoji never')
        total += hits
        title = next((line.strip()[:TITLE_CLIP] for line in body if line.strip()), '')
        listing.append(f'fig {number}: {len(body)} lines | emoji {hits} | {title}')

    yield from observations(rows=listing,
                            summary=f'figures={len(page.figures)} emoji={total}',
                            data={'figures': len(page.figures), 'emoji': total})
