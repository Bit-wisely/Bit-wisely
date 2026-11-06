#!/usr/bin/env python3
"""
GitHub Profile Card Generator (Neofetch Style)
----------------------------------------------
Builds profile-card.svg: ASCII portrait on the left, neofetch-style info on the
right, every value flush against the same right edge (dot leaders fill the gap).

Why it is built this way
  * The font (JetBrains Mono, subset, ~9 KB) is EMBEDDED in the SVG. Every
    character is exactly 0.6em wide on every device, so counting characters is
    pixel-exact alignment. No dependence on Consolas / local fonts.
  * The card is ~860px wide so GitHub shows it at 1:1 instead of shrinking it.
    Text is therefore the real size you set (FONT_SIZE), not a scaled-down one.
  * The portrait lives in portrait.txt (plain text). Regenerate it from a photo
    with:  python generate_card.py --image photo.png

Usage
  python generate_card.py --defaults             # rebuild using DEFAULT_CONFIG
  python generate_card.py                        # interactive prompts
  python generate_card.py --image photo.png      # also rebuild the portrait
"""

import argparse
import base64
import os
import sys
import xml.etree.ElementTree as ET
from typing import List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------------------
# Your data
# --------------------------------------------------------------------------
DEFAULT_CONFIG = {
    "user": "muhammed-shifan",
    "host": "Bit-wisely",

    # System Info (not shown on the card; kept so existing scripts keep working)
    "os": "Parrot OS / Arch Linux / Windows",
    "uptime": "20 years, 9 months",
    "status": "Student",
    "shell": "Curiosity + C",
    "ide": "VSCode, STM32CubeIDE",

    # Languages
    "lang_prog": "C, HTML, CSS, JavaScript, Python",
    "lang_learning": "Web Dev, OS / Kernel Dev, Cybersecurity",
    "lang_real": "English",

    # Hobbies
    "hobby_crypto": "Classical Ciphers, RSA, Key Exchange",
    "hobby_systems": "Low-Level C, Memory Management",
    "hobby_web": "Building things from scratch",

    # Contact
    "email": "muhammedshifanvm12@gmail.com",
    "linkedin": "muhammedshifanvm",
    "github": "Bit-wisely",

    # GitHub Stats
    "repos": "10",
    "member_since": "Dec 2024",
    "bio": "Learning curiously.",
}

# --------------------------------------------------------------------------
# Look & layout  (all sizes in SVG px; the card is shown ~1:1 on GitHub)
# --------------------------------------------------------------------------
THEME = {
    "bg": "#161b22",
    "border": "#30363d",
    "text": "#f0f6fc",      # header / section titles
    "key": "#ffa657",       # orange keys
    "value": "#a5d6ff",     # light-blue values
    "dots": "#6e7681",      # dot leaders, bullets, rules
    "rule": "#484f58",
}

CARD_W = 860            # keep <= ~880 so GitHub does not scale the card down
PAD = 22                # outer padding
GAP = 24                # space between portrait and text
FONT_SIZE = 15          # info text size (px)  <- raise/lower for readability
ROW_H = 25              # info row pitch
SECTION_GAP = 14        # extra space before "- Contact" / "- GitHub Stats"
CHAR_W = FONT_SIZE * 0.6    # exact for JetBrains Mono (advance = 0.600 em)
MIN_DOTS = 2
FLATTEN = 1.0       # 0 = keep photo lighting, 1 = fully even lighting
FLATTEN_SIGMA_DIV = 12  # larger = flatten at finer scale (more local contrast)
TONE_GAMMA = 0.9    # <1 brightens midtones of the portrait

PORTRAIT_FONT = 6.5     # portrait glyph size (px): small glyphs = more detail
PORTRAIT_CELL_W = PORTRAIT_FONT * 0.6
PORTRAIT_CELL_H = PORTRAIT_FONT * 1.0

# glyphs ordered light -> dense by measured ink coverage in JetBrains Mono
RAMP = " `.-:\"=|*uZ9H0M%W@"
FONT_STACK = "'BWMono', 'JetBrains Mono', Consolas, 'DejaVu Sans Mono', monospace"


def escape_xml(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# --------------------------------------------------------------------------
# Input helpers (unchanged behaviour)
# --------------------------------------------------------------------------
def prompt_field(prompt_text: str, default_val: str) -> str:
    try:
        val = input(f"{prompt_text} [{default_val}]: ").strip()
        return val if val else default_val
    except (EOFError, KeyboardInterrupt):
        return default_val


def collect_user_data(interactive: bool = True) -> dict:
    if not interactive:
        return DEFAULT_CONFIG.copy()

    print("\n" + "=" * 60)
    print(" GitHub Profile Card Generator - Interactive Setup")
    print(" Press ENTER to keep the [default] value for any field.")
    print("=" * 60 + "\n")
    cfg = {}
    groups = [
        ("1. Header", [("user", "Username"), ("host", "Host / Organization")]),
        ("2. System Info", [("os", "OS"), ("shell", "Shell"), ("ide", "IDE(s)")]),
        ("3. Languages", [("lang_prog", "Programming Languages"),
                          ("lang_learning", "Learning"),
                          ("lang_real", "Spoken Languages")]),
        ("4. Hobbies", [("hobby_crypto", "Hobbies (Crypto)"),
                        ("hobby_systems", "Hobbies (Systems)"),
                        ("hobby_web", "Hobbies (Web)")]),
        ("5. Contact", [("email", "Email"), ("linkedin", "LinkedIn"),
                        ("github", "GitHub Username")]),
        ("6. GitHub Stats", [("repos", "Repositories"), ("member_since", "Member Since"),
                             ("bio", "Bio")]),
    ]
    for title, fields in groups:
        print(f"--- {title} ---")
        for key, label in fields:
            cfg[key] = prompt_field(label, DEFAULT_CONFIG[key])
        print()
    for k, v in DEFAULT_CONFIG.items():
        cfg.setdefault(k, v)
    return cfg


# --------------------------------------------------------------------------
# Portrait: photo -> ASCII text
# --------------------------------------------------------------------------
def convert_image_to_ascii(image_path: str, width: int, height: int) -> List[str]:
    """Photo -> `height` lines of `width` characters (light ink = bright area).

    Crops a tall head-and-shoulders window that matches the character-cell
    aspect ratio, stretches contrast using only the subject's own tones, then
    maps brightness onto RAMP. Transparent background stays blank.
    """
    try:
        import numpy as np
        from PIL import Image, ImageFilter
    except ImportError:
        print("[!] Pillow + numpy are required for --image (pip install pillow numpy)")
        return []
    if not os.path.exists(image_path):
        print(f"[!] Image not found: {image_path}")
        return []

    img = Image.open(image_path).convert("RGBA")
    W, H = img.size
    a = np.asarray(img)[..., 3] / 255.0
    ys, xs = np.where(a > 0.5)
    if len(ys) == 0:            # no transparency info: treat whole image as subject
        a = np.ones_like(a)
        ys, xs = np.where(a > 0.5)
    top = int(ys.min())
    # head centre = centroid of the top 35% of the subject
    band = ys < top + 0.35 * (ys.max() - top)
    cx = float(xs[band].mean())

    aspect = (width * PORTRAIT_CELL_W) / (height * PORTRAIT_CELL_H)   # crop w/h
    y0 = max(0, top - int(0.03 * H))
    ch = H - y0
    cw = int(ch * aspect)
    if cw > W:
        cw = W
        ch = int(cw / aspect)
    x0 = int(min(max(cx - cw / 2, 0), W - cw))
    img = img.crop((x0, y0, x0 + cw, y0 + ch))

    alpha = np.asarray(img)[..., 3] / 255.0
    lum = np.asarray(img.convert("RGB").convert("L")).astype(float)

    # --- local-contrast flattening (retinex-style): lifts features hidden in shadow ---
    sub = (alpha > 0.5).astype(float)
    def blur(arr, sigma, scale):
        im8 = Image.fromarray(np.clip(arr * scale, 0, 255).astype("uint8"), mode="L")
        return np.asarray(im8.filter(ImageFilter.GaussianBlur(sigma))).astype(float) / scale
    sigma = max(4, cw / FLATTEN_SIGMA_DIV)
    base = blur(lum * sub, sigma, 1.0) / np.maximum(blur(sub, sigma, 255.0), 1e-3)   # smooth lighting, subject only
    flat = (lum + 6) / (base + 6) ** FLATTEN                              # divide out part of the lighting
    flat = flat * sub
    flat_img = Image.fromarray(np.clip(flat / max(flat.max(), 1e-6) * 255, 0, 255).astype("uint8"))
    flat_img = flat_img.filter(ImageFilter.UnsharpMask(radius=max(2, cw // 110), percent=160, threshold=1))
    lum = np.asarray(flat_img).astype(float)

    # downsample (area average)
    small_l = np.asarray(Image.fromarray(lum.astype("uint8")).resize((width, height), Image.BOX)).astype(float)
    small_a = np.asarray(Image.fromarray((alpha * 255).astype("uint8")).resize((width, height), Image.BOX)) / 255.0

    mask = small_a > 0.35
    vals = small_l[mask]
    lo, hi = np.percentile(vals, [3, 99.5])
    t = np.clip((small_l - lo) / max(hi - lo, 1), 0, 1) ** TONE_GAMMA

    n = len(RAMP) - 1
    lines = []
    for r in range(height):
        row = []
        for c in range(width):
            if not mask[r, c]:
                row.append(" ")
                continue
            idx = max(1, int(round(t[r, c] * n)))      # subject cells never fully blank
            row.append(RAMP[idx])
        lines.append("".join(row))
    return lines


def portrait_lines() -> List[str]:
    path = os.path.join(HERE, "portrait.txt")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().split("\n")
    while lines and lines[-1] == "":
        lines.pop()
    return lines


# glyph tier -> colour so the portrait has more tonal range than ink alone
def _tier(ch: str) -> int:
    i = RAMP.find(ch)
    if i <= 0:
        return 0
    if i <= 4:
        return 1      # faint
    if i <= 10:
        return 2      # mid
    return 3          # bright


PORTRAIT_TIER_FILL = {1: "#6e7681", 2: "#adbac7", 3: "#f0f6fc"}


def portrait_svg(lines: List[str], x: float, y: float) -> str:
    out = [f'<g class="art" font-size="{PORTRAIT_FONT}">']
    for r, line in enumerate(lines):
        if not line.strip():
            continue
        base = y + r * PORTRAIT_CELL_H + PORTRAIT_FONT * 0.8
        runs, cur_t, cur = [], None, ""
        for ch in line:
            t = _tier(ch)
            if t != cur_t and cur:
                runs.append((cur_t, cur))
                cur = ""
            cur_t = t
            cur += ch
        if cur:
            runs.append((cur_t, cur))
        spans = "".join(
            f'<tspan fill="{PORTRAIT_TIER_FILL.get(t, "#adbac7")}">{escape_xml(s)}</tspan>' for t, s in runs
        )
        out.append(f'<text x="{x:.1f}" y="{base:.1f}" xml:space="preserve">{spans}</text>')
    out.append("</g>")
    return "\n".join(out)


# --------------------------------------------------------------------------
# Card
# --------------------------------------------------------------------------
def _font_face(name: str, weight: int, filename: str) -> str:
    path = os.path.join(HERE, "fonts", filename)
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return (f"@font-face{{font-family:'{name}';font-weight:{weight};"
            f"src:url(data:font/ttf;base64,{b64}) format('truetype');}}")


def build_rows(cfg: dict):
    """Ordered rows: ('hdr',text) ('kv',key,val) ('sec',title) ('gap',) ('pal',)"""
    rows = [("hdr", f"{cfg['user']}@{cfg['host']}")]
    for k, v in [
        ("OS:", cfg["os"]),
        ("Shell:", cfg["shell"]),
        ("IDE:", cfg["ide"]),
        ("Languages.Programming:", cfg["lang_prog"]),
        ("Languages.Learning:", cfg["lang_learning"]),
        ("Languages.Real:", cfg["lang_real"]),
        ("Hobbies.Crypto:", cfg["hobby_crypto"]),
        ("Hobbies.Systems:", cfg["hobby_systems"]),
        ("Hobbies.Web:", cfg["hobby_web"]),
    ]:
        rows.append(("kv", k, v))
    rows += [("gap",), ("sec", "- Contact")]
    for k, v in [("Email:", cfg["email"]), ("LinkedIn:", cfg["linkedin"]), ("GitHub:", cfg["github"])]:
        rows.append(("kv", k, v))
    rows += [("gap",), ("sec", "- GitHub Stats")]
    for k, v in [("Repos:", cfg["repos"]), ("Member Since:", cfg["member_since"]), ("Bio:", cfg["bio"])]:
        rows.append(("kv", k, v))
    rows += [("gap",), ("pal",)]
    return rows


def generate_svg(cfg: dict, portrait_svg_override: Optional[str] = None, **_ignored) -> str:
    rows = build_rows(cfg)

    # one shared line length (in characters) -> every row ends at the same x
    need = 0
    for r in rows:
        if r[0] == "kv":
            # ". " + key + " " + dots(>=MIN_DOTS) + " " + value
            need = max(need, 2 + len(r[1]) + 1 + MIN_DOTS + 1 + len(r[2]))
        elif r[0] in ("hdr", "sec"):
            need = max(need, len(r[1]) + 1 + 6)
    L = need
    text_w = L * CHAR_W

    # vertical layout of the info column
    y = PAD
    ys = []
    for r in rows:
        if r[0] == "gap":
            y += SECTION_GAP
            ys.append(None)
        else:
            ys.append(y)
            y += ROW_H
    inner_h = y - PAD
    height = inner_h + 2 * PAD

    text_x = CARD_W - PAD - text_w
    portrait_x = PAD
    portrait_w = text_x - GAP - portrait_x
    cols = int(portrait_w // PORTRAIT_CELL_W)
    rows_p = int(inner_h // PORTRAIT_CELL_H)

    lines = portrait_lines() if portrait_svg_override is None else []
    # centre the stored portrait inside the available box
    if lines:
        pw = max(len(s) for s in lines) * PORTRAIT_CELL_W
        ph = len(lines) * PORTRAIT_CELL_H
        px = portrait_x + max(0, (portrait_w - pw) / 2)
        py = PAD + max(0, (inner_h - ph) / 2)
    else:
        px = py = 0

    key_c, val_c, dot_c, hdr_c, rule_c = (THEME[k] for k in ("key", "value", "dots", "text", "rule"))
    parts = [f'<?xml version="1.0" encoding="UTF-8"?>\n'
             f'<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W}" height="{height:.0f}" '
             f'viewBox="0 0 {CARD_W} {height:.0f}" role="img" aria-label="Profile card">']
    parts.append("<style>")
    parts.append(_font_face("BWMono", 400, "JetBrainsMono-Regular.subset.ttf"))
    parts.append(_font_face("BWMono", 700, "JetBrainsMono-Bold.subset.ttf"))
    parts.append(f"text{{font-family:{FONT_STACK};white-space:pre;}}"
                 f".t{{font-size:{FONT_SIZE}px;}}"
                 f".k{{fill:{key_c};font-weight:700;}}"
                 f".v{{fill:{val_c};}}"
                 f".d{{fill:{dot_c};}}"
                 f".h{{fill:{hdr_c};font-weight:700;}}"
                 f".r{{fill:{rule_c};}}")
    parts.append("</style>")
    parts.append(f'<rect width="{CARD_W}" height="{height:.0f}" rx="10" fill="{THEME["bg"]}"/>')

    if portrait_svg_override:
        parts.append(portrait_svg_override)
    elif lines:
        parts.append(portrait_svg(lines, px, py))

    for r, yy in zip(rows, ys):
        if r[0] == "gap":
            continue
        base = yy + ROW_H / 2 + FONT_SIZE * 0.36
        if r[0] == "hdr":
            rule = "\u2500" * (L - len(r[1]) - 1)
            parts.append(f'<text class="t" x="{text_x:.1f}" y="{base:.1f}" xml:space="preserve">'
                         f'<tspan class="h">{escape_xml(r[1])}</tspan><tspan class="r"> {rule}</tspan></text>')
        elif r[0] == "sec":
            rule = "\u2500" * (L - len(r[1]) - 1)
            parts.append(f'<text class="t" x="{text_x:.1f}" y="{base:.1f}" xml:space="preserve">'
                         f'<tspan class="h">{escape_xml(r[1])}</tspan><tspan class="r"> {rule}</tspan></text>')
        elif r[0] == "kv":
            key, val = r[1], r[2]
            n_dots = L - (2 + len(key) + 1 + 1 + len(val))
            parts.append(f'<text class="t" x="{text_x:.1f}" y="{base:.1f}" xml:space="preserve">'
                         f'<tspan class="d">. </tspan><tspan class="k">{escape_xml(key)}</tspan>'
                         f'<tspan class="d"> {"." * n_dots} </tspan><tspan class="v">{escape_xml(val)}</tspan></text>')
        elif r[0] == "pal":
            cols16 = ['#ff5f56', '#ffbd2e', '#27c93f', '#00c7fd', '#a06cff', '#ff6bcb', '#f0f0f0', '#8a8a8a',
                      '#ff8a3d', '#e0e04a', '#3ddc97', '#33b1ff', '#7b61ff', '#ff5c9e', '#ffffff', '#4d4d4d']
            rad = 6
            step = (text_w - 2 * rad) / (len(cols16) - 1)
            for i, col in enumerate(cols16):
                parts.append(f'<circle cx="{text_x + rad + i * step:.1f}" cy="{yy + ROW_H / 2:.1f}" r="{rad}" fill="{col}"/>')

    parts.append(f'<rect x="0.75" y="0.75" width="{CARD_W - 1.5}" height="{height - 1.5:.2f}" rx="10" '
                 f'fill="none" stroke="{THEME["border"]}" stroke-width="1.5"/>')
    parts.append("</svg>\n")
    return "\n".join(p for p in parts if p)


def portrait_box(cfg: Optional[dict] = None):
    """(cols, rows) of the portrait grid that fits beside the info column."""
    cfg = cfg or DEFAULT_CONFIG
    rows = build_rows(cfg)
    need = 0
    for r in rows:
        if r[0] == "kv":
            need = max(need, 2 + len(r[1]) + 1 + MIN_DOTS + 1 + len(r[2]))
        elif r[0] in ("hdr", "sec"):
            need = max(need, len(r[1]) + 7)
    text_w = need * CHAR_W
    inner_h = sum(SECTION_GAP if r[0] == "gap" else ROW_H for r in rows)
    portrait_w = (CARD_W - PAD - text_w) - GAP - PAD
    return int(portrait_w // PORTRAIT_CELL_W), int(inner_h // PORTRAIT_CELL_H)


def main():
    parser = argparse.ArgumentParser(description="Generate the neofetch-style GitHub profile card SVG.")
    parser.add_argument("-o", "--output", default=os.path.join(HERE, "profile-card.svg"))
    parser.add_argument("--image", default=None, help="Photo to convert into portrait.txt (ASCII art)")
    parser.add_argument("--defaults", action="store_true", help="Use DEFAULT_CONFIG without prompting")
    args = parser.parse_args()

    cfg = collect_user_data(interactive=(not args.defaults and sys.stdin.isatty()))

    if args.image:
        cols, rws = portrait_box(cfg)
        print(f"[*] Converting {args.image} -> {cols}x{rws} ASCII portrait...")
        lines = convert_image_to_ascii(args.image, cols, rws)
        if lines:
            with open(os.path.join(HERE, "portrait.txt"), "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            print("[+] Wrote portrait.txt (edit it by hand if you like)")

    svg = generate_svg(cfg)
    ET.fromstring(svg)           # must be valid XML
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"[+] Wrote {args.output}")


if __name__ == "__main__":
    main()
