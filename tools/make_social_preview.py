#!/usr/bin/python3
# -----------------------------------------------------------------------------
# project:  calendarium
# authors:  1966bc aka Giuseppe Costanzi
# licence:  MIT, see LICENSE
# -----------------------------------------------------------------------------
"""Compose the GitHub social preview, docs/social-preview.png.

A build tool like make_icon.py, and like it it needs Pillow. The image is
1280 by 640, the size GitHub asks for, with everything that matters kept
away from the edges, which some sites crop.

On the left the icon, the name and what it is; on the right the demo, from
docs/demo-large.png. That one is a capture of the demo drawn by Tk at a
larger scale, so the text is sharp instead of an enlarged small picture:

    python3 -c "import runpy, sys, tkinter
    original = tkinter.Tk.__init__
    def scaled(self, *a, **k):
        original(self, *a, **k)
        self.tk.call('tk', 'scaling', 2.6)
    tkinter.Tk.__init__ = scaled
    sys.path.insert(0, 'examples')
    runpy.run_path('examples/demo.py', run_name='__main__')"

    import -window <window id> docs/demo-large.png   (ImageMagick, no frame)

GitHub has no API for the social preview: upload the result by hand, in
Settings > General > Social preview.

    python3 tools/make_social_preview.py
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from make_icon import draw as draw_icon  # noqa: E402

WIDTH, HEIGHT = 1280, 640
MARGIN = 70

BACKGROUND = (246, 245, 240)
INK = (33, 37, 41)
MUTED = (110, 115, 120)
ACCENT = (192, 57, 43)          # the red of the icon's header
CARD_EDGE = (150, 150, 150)
SHADOW = (0, 0, 0, 60)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
REGULAR = os.path.join(FONT_DIR, "DejaVuSans.ttf")

TITLE = "Calendarium"
TAGLINE = "Date picker widget for Tkinter"
POINTS = (
    "One file, no dependencies",
    "Typed from the keyboard, validated",
    "tk and ttk",
    "Europe, USA and ISO date order",
)
FOOTER = "github.com/1966bc/calendarium"


def paste_card(canvas, card, x, y):
    """The demo as a card: a soft shadow under it and a thin edge round it."""
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rectangle(
        (x + 8, y + 10, x + card.width + 8, y + card.height + 10), fill=SHADOW)
    canvas.alpha_composite(shadow)
    canvas.paste(card, (x, y))
    ImageDraw.Draw(canvas).rectangle(
        (x - 1, y - 1, x + card.width, y + card.height), outline=CARD_EDGE, width=2)


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), BACKGROUND + (255,))
    pen = ImageDraw.Draw(canvas)

    card = Image.open(os.path.join(root, "docs", "demo-large.png")).convert("RGBA")
    card_x = WIDTH - MARGIN - card.width
    card_y = (HEIGHT - card.height) // 2
    paste_card(canvas, card, card_x, card_y)

    x = MARGIN
    icon = draw_icon(128)
    canvas.alpha_composite(icon, (x - 6, 78))

    title = ImageFont.truetype(BOLD, 64)
    tagline = ImageFont.truetype(REGULAR, 30)
    point = ImageFont.truetype(REGULAR, 25)
    footer = ImageFont.truetype(REGULAR, 22)

    pen.text((x, 222), TITLE, font=title, fill=INK)
    pen.text((x, 304), TAGLINE, font=tagline, fill=ACCENT)

    y = 370
    for text in POINTS:
        pen.ellipse((x + 2, y + 10, x + 12, y + 20), fill=ACCENT)
        pen.text((x + 26, y), text, font=point, fill=INK)
        y += 40

    pen.text((x, HEIGHT - MARGIN - 22), FOOTER, font=footer, fill=MUTED)

    # The text is measured where it was drawn: the points start 26 further in.
    right = max([pen.textbbox((x, 0), TITLE, font=title)[2],
                 pen.textbbox((x, 0), TAGLINE, font=tagline)[2]]
                + [pen.textbbox((x + 26, 0), p, font=point)[2] for p in POINTS])
    if right + 26 > card_x:
        raise SystemExit(f"text runs into the demo: {right + 26} > {card_x}")

    path = os.path.join(root, "docs", "social-preview.png")
    canvas.convert("RGB").save(path, optimize=True)
    print(f"{path}: {WIDTH}x{HEIGHT}, {os.path.getsize(path)} bytes")


if __name__ == "__main__":
    main()
