"""Render 64x32 notification cards as (animated) WebP for the Tidbyt."""

import io

from PIL import Image, ImageDraw

from .font import GLYPH_HEIGHT, draw_text, text_width, wrap

WIDTH, HEIGHT = 64, 32
BANNER_HEIGHT = 7
MARGIN = 2
LINE_PITCH = GLYPH_HEIGHT + 1
MESSAGE_TOP = BANNER_HEIGHT + 2
MAX_STATIC_LINES = 3

SCROLL_MS_PER_FRAME = 60
SCROLL_HOLD_FRAMES = 12  # pause before the marquee starts moving

AGENTS = {
    "claude": {"label": "CLAUDE", "color": (217, 119, 87)},
    "codex": {"label": "CODEX", "color": (16, 163, 127)},
    "shortcut": {"label": "SHORTCUT", "color": (99, 102, 241)},
}
DEFAULT_AGENT_COLOR = (140, 140, 150)

STATUSES = {
    "done": {"color": (80, 220, 80), "icon": "check"},
    "input": {"color": (255, 204, 0), "icon": "?"},
    "error": {"color": (255, 70, 60), "icon": "!"},
    "working": {"color": (80, 140, 255), "icon": "dots"},
    "info": {"color": (235, 235, 235), "icon": None},
}

ICONS = {
    "check": ["00000", "00001", "00010", "10100", "01000"],
    "?": ["1100", "0010", "0100", "0000", "0100"],
    "!": ["11", "11", "11", "00", "11"],
    "dots": ["00000", "00000", "10101", "00000", "00000"],
}


def _luminance(rgb):
    r, g, b = rgb
    return 0.299 * r + 0.587 * g + 0.114 * b


def _draw_icon(draw, xy, name, fill):
    x, y = xy
    for ry, row in enumerate(ICONS[name]):
        for rx, bit in enumerate(row):
            if bit == "1":
                draw.point((x + rx, y + ry), fill=fill)


def _base_frame(agent, status):
    """Black canvas with the agent banner; message area left empty."""
    preset = AGENTS.get(agent.lower())
    label = preset["label"] if preset else agent.upper()
    color = preset["color"] if preset else DEFAULT_AGENT_COLOR

    img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, WIDTH - 1, BANNER_HEIGHT - 1], fill=color)

    ink = (0, 0, 0) if _luminance(color) > 110 else (255, 255, 255)
    icon = STATUSES[status]["icon"]
    icon_w = len(ICONS[icon][0]) + MARGIN + 1 if icon else 0

    max_label_w = WIDTH - 2 * MARGIN - icon_w
    while label and text_width(label) > max_label_w:
        label = label[:-1]
    draw_text(draw, (MARGIN, 1), label, ink)

    if icon:
        _draw_icon(draw, (WIDTH - MARGIN - len(ICONS[icon][0]), 1), icon, ink)
    return img


def render_frames(message, agent="agent", status="info"):
    """Render a notification into a list of PIL frames.

    Returns a single frame when the message fits statically, otherwise a
    horizontal marquee animation.
    """
    if status not in STATUSES:
        raise ValueError(f"unknown status {status!r}; expected one of {sorted(STATUSES)}")
    text_color = STATUSES[status]["color"]
    max_line_w = WIDTH - 2 * MARGIN

    lines = wrap(message, max_line_w)
    if len(lines) <= MAX_STATIC_LINES:
        img = _base_frame(agent, status)
        draw = ImageDraw.Draw(img)
        block_h = len(lines) * LINE_PITCH - 1
        top = MESSAGE_TOP + max(0, (HEIGHT - MESSAGE_TOP - block_h) // 2)
        for i, line in enumerate(lines):
            x = max(MARGIN, (WIDTH - text_width(line)) // 2)
            draw_text(draw, (x, top + i * LINE_PITCH), line, text_color)
        return [img]

    # Marquee: single line scrolling right-to-left through the message area.
    base = _base_frame(agent, status)
    y = MESSAGE_TOP + (HEIGHT - MESSAGE_TOP - GLYPH_HEIGHT) // 2
    w = text_width(message)
    frames = []
    offsets = [MARGIN] * SCROLL_HOLD_FRAMES + list(range(MARGIN, -(w + 1), -1))
    for off in offsets:
        img = base.copy()
        draw_text(ImageDraw.Draw(img), (off, y), message, text_color)
        frames.append(img)
    return frames


def to_webp(frames):
    """Encode frames as WebP bytes (animated when multiple frames)."""
    buf = io.BytesIO()
    if len(frames) == 1:
        frames[0].save(buf, format="WEBP", lossless=True)
    else:
        frames[0].save(
            buf,
            format="WEBP",
            save_all=True,
            append_images=frames[1:],
            duration=SCROLL_MS_PER_FRAME,
            loop=0,
            lossless=True,
        )
    return buf.getvalue()
