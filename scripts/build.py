#!/usr/bin/env python3
"""Writes the SVGs in assets/ for the profile README.

GitHub shows README SVGs as images, which can't load web fonts, so all text
is converted to outlines here. Each SVG carries a light and a dark palette
and switches on the viewer's colour scheme.

    pip install -r scripts/requirements.txt
    python3 scripts/build.py
"""

import pathlib

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ROOT / "scripts" / "fonts"
OUT = ROOT / "assets"
W = 900


def num(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


class Font:
    def __init__(self, file):
        path = str(FONTS / file)
        self.tt = TTFont(path)
        self.glyphs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        face = hb.Face(hb.Blob.from_file_path(path))
        self.hb = hb.Font(face)
        self.upem = face.upem

    def _shape(self, text):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf, {"kern": True, "liga": True})
        return buf.glyph_infos, buf.glyph_positions

    def width(self, text, size, track=0.0):
        infos, pos = self._shape(text)
        return (sum(p.x_advance for p in pos) * size / self.upem
                + track * size * (len(infos) - 1))

    def path(self, text, size, x, y, track=0.0, anchor="start", cls=""):
        """`track` is letter spacing in em; `y` is the baseline."""
        if anchor != "start":
            w = self.width(text, size, track)
            x -= w if anchor == "end" else w / 2
        infos, pos = self._shape(text)
        s = size / self.upem
        pen = SVGPathPen(self.glyphs, ntos=num)
        cx = x
        for info, p in zip(infos, pos):
            tp = TransformPen(pen, (s, 0, 0, -s, cx + p.x_offset * s, y - p.y_offset * s))
            self.glyphs[self.order[info.codepoint]].draw(tp)
            cx += p.x_advance * s + track * size
        c = f' class="{cls}"' if cls else ""
        return f'<path{c} d="{pen.getCommands()}"/>'


DISPLAY = Font("ArchivoExtraCondensed-Black.ttf")
TAGLINE = Font("ArchivoCondensed-ExtraBold.ttf")
MONO = Font("IBMPlexMono-Medium.ttf")
TRACK = 0.18  # the site's mono label tracking

# Same values as HomePalette / CustomColor / DarkColor in the portfolio.
LIGHT = {
    "bg0": "#FFF1E6", "bg1": "#F5DCC6", "bg2": "#D7B49E",
    "ink": "#5C4033", "soft": "#6B4F3A", "tag": "#A67B5B",
    "card": "#FFF7F0", "chip": "#F5E6D6", "line": "#EAD7C2",
    "glass": "rgba(255,255,255,.55)",
}
DARK = {
    "bg0": "#1A1410", "bg1": "#231A12", "bg2": "#3A2A1C",
    "ink": "#F2E4D1", "soft": "#B8A896", "tag": "#D4B896",
    "card": "#241C16", "chip": "#2C231C", "line": "#3D2F24",
    "glass": "rgba(255,255,255,.08)",
}
# Landing tile colours: the same in both themes, like the site's phone.
CORAL, PHOTO, BROWN, TAN = "#E6A4A4", "#CDBFB3", "#5C4033", "#C9A982"
ON_TILE = {CORAL: "#5C4033", PHOTO: "#5C4033", BROWN: "#F2E4D1", TAN: "#5C4033"}


def palette(t):
    return (
        "".join(f".{k}{{fill:{t[k]}}}" for k in ("ink", "soft", "tag", "card", "chip"))
        + f".line{{stroke:{t['line']}}}.glass{{stroke:{t['glass']}}}"
        + "".join(f".{k}{{stop-color:{t[k]}}}" for k in ("bg0", "bg1", "bg2"))
    )


def svg(h, body, label, css=""):
    style = (
        palette(LIGHT)
        + f"@media (prefers-color-scheme:dark){{{palette(DARK)}}}"
        + css
        + "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" '
        f'width="{W}" height="{h}" role="img" aria-label="{label}">'
        f"<title>{label}</title><style>{style}</style>{body}</svg>\n"
    )


def write(name, content):
    (OUT / name).write_text(content)
    print(f"{name:24} {len(content) / 1024:6.1f} KB")


def fit(font, text, size, max_w, track=0.0):
    w = font.width(text, size, track)
    return size if w <= max_w else size * max_w / w


# ---------------------------------------------------------------- header

def phone():
    """The landing page's phone: four tiles, one per README section."""
    tw, th, gap = 57, 112, 6
    x0, y0 = -60, -110
    tiles = []
    specs = [
        ("WORK", CORAL, 0, 0), ("ABOUT", PHOTO, 1, 0),
        ("WRITING", BROWN, 0, 1), ("CONTACT", TAN, 1, 1),
    ]
    for i, (label, color, col, row) in enumerate(specs):
        x, y = x0 + col * (tw + gap), y0 + row * (th + gap)
        fg = ON_TILE[color]
        art = {
            "WORK": f'<rect x="{x+14}" y="{y+36}" width="29" height="52" rx="6" fill="none" stroke="{fg}" stroke-opacity=".55" stroke-width="2"/>'
                    f'<rect x="{x+19}" y="{y+46}" width="19" height="7" rx="2" fill="{fg}" fill-opacity=".55"/>'
                    f'<rect x="{x+19}" y="{y+57}" width="5" height="20" rx="2" fill="{fg}" fill-opacity=".55"/>',
            "ABOUT": f'<circle cx="{x+28.5}" cy="{y+56}" r="11" fill="{fg}" fill-opacity=".35"/>'
                     f'<path d="M{x+10} {y+98}c0-14 8-22 18.5-22s18.5 8 18.5 22z" fill="{fg}" fill-opacity=".35"/>',
            "WRITING": "".join(
                f'<rect x="{x+10}" y="{y+44+k*9}" width="{w}" height="{4 if k else 6}" rx="2" fill="{fg}" fill-opacity="{.9 if k == 0 else .55}"/>'
                for k, w in enumerate((34, 30, 22, 26, 10))),
            "CONTACT": f'<rect x="{x+7}" y="{y+56}" width="43" height="24" rx="7" fill="#FFF1E6" fill-opacity=".45" stroke="{fg}" stroke-opacity=".3"/>'
                       f'<rect x="{x+12}" y="{y+63}" width="26" height="3" rx="1.5" fill="{fg}" fill-opacity=".5"/>'
                       f'<rect x="{x+12}" y="{y+70}" width="14" height="3" rx="1.5" fill="{fg}" fill-opacity=".5"/>',
        }[label]
        tiles.append(
            f'<g class="tile" style="animation-delay:{.25 + i * .12:.2f}s">'
            f'<rect x="{x}" y="{y}" width="{tw}" height="{th}" rx="9" fill="{color}"/>'
            f'<g fill="{fg}">{MONO.path(label, 5.6, x + 6, y + 13, TRACK)}</g>{art}</g>'
        )
    return (
        '<g class="float"><g transform="translate(742 172) rotate(-7)">'
        '<rect x="-80" y="-140" width="160" height="280" rx="28" fill="#000" opacity=".12" transform="translate(6 10)"/>'
        '<rect x="-80" y="-140" width="160" height="280" rx="28" fill="#2A201A"/>'
        '<rect x="-80" y="-140" width="160" height="280" rx="28" fill="none" stroke="#fff" stroke-opacity=".12"/>'
        '<rect x="-72" y="-132" width="144" height="264" rx="21" fill="#17110D"/>'
        '<rect x="-14" y="-127" width="28" height="4" rx="2" fill="#000" opacity=".6"/>'
        + "".join(tiles)
        + "</g></g>"
    )


def header():
    h, left, col = 340, 60, 540
    name = "AABHASH RAI"
    name_size = fit(DISPLAY, name, 128, col)
    tagline = "IOS & ANDROID, EMPTY REPO TO STORE"
    tag_size = fit(TAGLINE, tagline, 30, col)
    stack = "FLUTTER · KOTLIN · SWIFT · FIREBASE"
    stack_w = MONO.width(stack, 13, TRACK)
    body = (
        '<defs><radialGradient id="bg" cx="18%" cy="0%" r="115%">'
        '<stop offset="0" class="bg0"/><stop offset=".55" class="bg1"/><stop offset="1" class="bg2"/>'
        "</radialGradient></defs>"
        f'<rect width="{W}" height="{h}" rx="28" fill="url(#bg)"/>'
        f'<rect x="12" y="12" width="{W-24}" height="{h-24}" rx="20" fill="none" class="glass" stroke-width="1.5"/>'
        f'<g class="rise">'
        + MONO.path("SYDNEY, AUSTRALIA  ·  MOBILE ENGINEER", 13, left, 92, TRACK, cls="soft")
        + DISPLAY.path(name, name_size, left - 3, 204, -0.01, cls="ink")
        + TAGLINE.path(tagline, tag_size, left, 250, cls="tag")
        + MONO.path(stack, 13, left, 292, TRACK, cls="soft")
        + f'<rect class="caret tag" x="{left + stack_w + 8:.1f}" y="281" width="8" height="13"/>'
        + "</g>"
        + phone()
    )
    css = (
        ".rise{animation:rise .7s cubic-bezier(.2,.8,.2,1) both}"
        "@keyframes rise{from{opacity:0;transform:translateY(10px)}}"
        ".tile{transform-box:fill-box;transform-origin:center;animation:pop .5s cubic-bezier(.2,1.5,.4,1) both}"
        "@keyframes pop{from{opacity:0;transform:scale(.6)}}"
        ".float{animation:float 4.5s ease-in-out 1s infinite alternate}"
        "@keyframes float{to{transform:translateY(-6px)}}"
        ".caret{animation:blink 1.1s steps(1) infinite}"
        "@keyframes blink{50%{opacity:0}}"
    )
    write("header.svg", svg(h, body, "Aabhash Rai, mobile engineer in Sydney. iOS and Android, empty repo to store.", css))


# ------------------------------------------------------- section headings

def heading(slug, label, color):
    h = 48
    text_w = MONO.width(label, 14, TRACK)
    x_line = 34 + text_w + 18
    body = (
        '<defs><linearGradient id="g"><stop offset="0" stop-color="#BFA181"/>'
        '<stop offset="1" stop-color="#E6A4A4" stop-opacity="0"/></linearGradient></defs>'
        f'<rect x="2" y="17" width="16" height="16" rx="5" fill="{color}"/>'
        + MONO.path(label, 14, 34, 30, TRACK, cls="ink")
        + f'<rect x="{x_line:.1f}" y="24" width="{W - x_line:.1f}" height="2" rx="1" fill="url(#g)"/>'
    )
    write(f"h-{slug}.svg", svg(h, body, label.title()))


# ---------------------------------------------------------- contact pills

def pill(slug, label):
    h, size, pad = 44, 13, 22
    text = f"{label} ↗"
    w = round(MONO.width(text, size, TRACK) + pad * 2)
    body = (
        f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="{(h-2) / 2}" class="card line" stroke-width="1.5"/>'
        + MONO.path(text, size, pad, 27, TRACK, cls="ink")
    )
    content = svg(h, body, label.title()).replace(f'viewBox="0 0 {W} {h}" width="{W}"', f'viewBox="0 0 {w} {h}" width="{w}"')
    write(f"contact-{slug}.svg", content)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    header()
    heading("contact", "CONTACT", TAN)
    pill("website", "WEBSITE")
    pill("linkedin", "LINKEDIN")
    pill("email", "EMAIL")
    pill("resume", "RÉSUMÉ")
