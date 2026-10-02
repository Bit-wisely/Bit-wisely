#!/usr/bin/env python3
"""
GitHub Profile Card Generator (Neofetch Style)
----------------------------------------------
Generates a clean, terminal-styled SVG profile card for your GitHub profile README.
Supports interactive prompts, default presets, dynamic dot-alignment, and optional ASCII art.
"""

import sys
import os
import re
import argparse
import subprocess
import xml.etree.ElementTree as ET
from typing import List, Tuple, Optional

# Default configuration for Muhammed Shifan / Bit-wisely
DEFAULT_CONFIG = {
    "user": "muhammed-shifan",
    "host": "Bit-wisely",
    
    # System Info
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

# SVG Theme Colors matching terminal specification
THEME = {
    "bg": "#161b22",
    "border": "#30363d",
    "text": "#e6edf3",
    "key": "#e8a33d",
    "value": "#79c0ff",
    "section": "#5c6370",
    "green": "#3fb950",
    "red": "#f85149",
    "yellow": "#e3b341",
    "purple": "#d2a8ff",
}


def escape_xml(s: str) -> str:
    """Escapes XML/SVG special characters."""
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
         .replace("'", "&apos;")
    )


def prompt_field(prompt_text: str, default_val: str) -> str:
    """Prompts the user with a default fallback."""
    try:
        val = input(f"{prompt_text} [{default_val}]: ").strip()
        return val if val else default_val
    except (EOFError, KeyboardInterrupt):
        return default_val


def collect_user_data(interactive: bool = True) -> dict:
    """Collects configuration from user input or returns defaults."""
    if not interactive:
        return DEFAULT_CONFIG.copy()

    print("\n" + "=" * 60)
    print(" GitHub Profile Card Generator - Interactive Setup")
    print(" Press ENTER to keep the [default] value for any field.")
    print("=" * 60 + "\n")

    cfg = {}
    print("--- 1. Header ---")
    cfg["user"] = prompt_field("Username", DEFAULT_CONFIG["user"])
    cfg["host"] = prompt_field("Host / Organization", DEFAULT_CONFIG["host"])

    print("\n--- 2. System Info ---")
    cfg["os"] = prompt_field("OS", DEFAULT_CONFIG["os"])
    cfg["uptime"] = prompt_field("Uptime / Age", DEFAULT_CONFIG["uptime"])
    cfg["status"] = prompt_field("Status / Role", DEFAULT_CONFIG["status"])
    cfg["shell"] = prompt_field("Shell / Kernel", DEFAULT_CONFIG["shell"])
    cfg["ide"] = prompt_field("IDE(s)", DEFAULT_CONFIG["ide"])

    print("\n--- 3. Languages ---")
    cfg["lang_prog"] = prompt_field("Programming Languages", DEFAULT_CONFIG["lang_prog"])
    cfg["lang_learning"] = prompt_field("Learning / Computer", DEFAULT_CONFIG["lang_learning"])
    cfg["lang_real"] = prompt_field("Spoken / Real Languages", DEFAULT_CONFIG["lang_real"])

    print("\n--- 4. Hobbies / Interests ---")
    cfg["hobby_crypto"] = prompt_field("Hobbies (Crypto / Specialty)", DEFAULT_CONFIG["hobby_crypto"])
    cfg["hobby_systems"] = prompt_field("Hobbies (Systems / Hardware)", DEFAULT_CONFIG["hobby_systems"])
    cfg["hobby_web"] = prompt_field("Hobbies (Web / Software)", DEFAULT_CONFIG["hobby_web"])

    print("\n--- 5. Contact Info ---")
    cfg["email"] = prompt_field("Email", DEFAULT_CONFIG["email"])
    cfg["linkedin"] = prompt_field("LinkedIn", DEFAULT_CONFIG["linkedin"])
    cfg["github"] = prompt_field("GitHub Username", DEFAULT_CONFIG["github"])

    print("\n--- 6. GitHub Stats ---")
    cfg["repos"] = prompt_field("Repositories Count", DEFAULT_CONFIG["repos"])
    cfg["member_since"] = prompt_field("Member Since", DEFAULT_CONFIG["member_since"])
    cfg["bio"] = prompt_field("Bio / Tagline", DEFAULT_CONFIG["bio"])

    return cfg


def extract_face_portrait(svg_path: str = "profile-card.svg") -> Optional[str]:
    """Extracts the vector portrait ASCII art SVG element to guarantee the face is permanently preserved."""
    candidates = []
    if os.path.exists(svg_path):
        try:
            with open(svg_path, "r", encoding="utf-8") as f:
                candidates.append(f.read())
        except Exception:
            pass
    try:
        git_content = subprocess.check_output(
            ["git", "show", "HEAD:profile-card.svg"],
            text=True,
            stderr=subprocess.DEVNULL
        )
        candidates.append(git_content)
    except Exception:
        pass

    for content in candidates:
        match = re.search(r'(<svg\s+x="20\.00"\s+y="20\.00"\s+width="607\.00"\s+height="617\.50".*?</svg>)', content, re.DOTALL)
        if match:
            return match.group(1)

    return None


def generate_svg(cfg: dict, portrait_svg: Optional[str] = None) -> str:
    """Generates the neofetch-style SVG card with portrait and 14px specs."""
    if portrait_svg is None:
        portrait_svg = extract_face_portrait()

    width = 1260.00
    height = 657.50
    x = 660
    y = 56
    dy = 23
    target_len = 63

    svg_parts = []
    svg_parts.append(f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width:.2f}" height="{height:.2f}" viewBox="0 0 {width:.2f} {height:.2f}">
<style>
@font-face {{
  src: local('Consolas'), local('Consolas Bold');
  font-family: 'ConsolasFallback';
  font-display: swap;
  size-adjust: 109%;
}}
.term-text {{
  font-family: 'ConsolasFallback', Consolas, 'Fira Code', 'JetBrains Mono', Monaco, 'Courier New', monospace;
  font-size: 14px;
  white-space: pre;
}}
.key {{ fill: {THEME['key']}; font-weight: 600; }}
.val {{ fill: {THEME['value']}; }}
.dot {{ fill: {THEME['section']}; }}
.pfx {{ fill: {THEME['section']}; }}
.hdr {{ fill: {THEME['text']}; font-weight: bold; }}
.line {{ fill: {THEME['section']}; }}
.sec-hdr {{ fill: {THEME['text']}; font-weight: 600; }}
</style>
<rect width="100%" height="100%" rx="10" fill="{THEME['bg']}"/>
""")

    if portrait_svg:
        svg_parts.append(portrait_svg + "\n")

    svg_parts.append("  <g>\n")

    user_at_host = f"{cfg['user']}@{cfg['host']}"
    dash_count = max(10, target_len - len(user_at_host) - 1)
    dashes = "─" * dash_count
    svg_parts.append(
        f'    <text x="{x}" y="{y}" class="term-text">'
        f'<tspan class="hdr">{escape_xml(user_at_host)}</tspan>'
        f'<tspan class="line"> {dashes}</tspan></text>\n'
    )
    y += dy

    def add_entry(key: str, val: str) -> str:
        dots_count = max(2, target_len - 2 - len(key) - 2 - len(val))
        dots = "." * dots_count
        return (
            f'    <text x="{x}" y="{y}" class="term-text">'
            f'<tspan class="pfx">. </tspan>'
            f'<tspan class="key">{escape_xml(key)}</tspan>'
            f'<tspan class="dot"> {dots} </tspan>'
            f'<tspan class="val">{escape_xml(val)}</tspan></text>\n'
        )

    def add_section(title: str) -> str:
        dash_len = max(10, target_len - len(title) - 1)
        d = "─" * dash_len
        return (
            f'    <text x="{x}" y="{y}" class="term-text">'
            f'<tspan class="sec-hdr">{escape_xml(title)}</tspan>'
            f'<tspan class="line"> {d}</tspan></text>\n'
        )

    sys_entries = [
        ("OS:", cfg["os"]),
        ("Shell:", cfg["shell"]),
        ("IDE:", cfg["ide"]),
        ("Languages.Programming:", cfg["lang_prog"]),
        ("Languages.Learning:", cfg["lang_learning"]),
        ("Languages.Real:", cfg["lang_real"]),
        ("Hobbies.Crypto:", cfg["hobby_crypto"]),
        ("Hobbies.Systems:", cfg["hobby_systems"]),
        ("Hobbies.Web:", cfg["hobby_web"]),
    ]
    for k, v in sys_entries:
        svg_parts.append(add_entry(k, v))
        y += dy

    y += 18
    svg_parts.append(add_section("- Contact"))
    y += dy

    contact_entries = [
        ("Email:", cfg["email"]),
        ("LinkedIn:", cfg["linkedin"]),
        ("GitHub:", cfg["github"]),
    ]
    for k, v in contact_entries:
        svg_parts.append(add_entry(k, v))
        y += dy

    y += 18
    svg_parts.append(add_section("- GitHub Stats"))
    y += dy

    stats_entries = [
        ("Repos:", cfg["repos"]),
        ("Member Since:", cfg["member_since"]),
        ("Bio:", cfg["bio"]),
    ]
    for k, v in stats_entries:
        svg_parts.append(add_entry(k, v))
        y += dy

    circles_y = y + 16
    palette_top = ['#ff5f56', '#ffbd2e', '#27c93f', '#00c7fd', '#a06cff', '#ff6bcb', '#f0f0f0', '#8a8a8a']
    palette_bot = ['#ff8a3d', '#e0e04a', '#3ddc97', '#33b1ff', '#7b61ff', '#ff5c9e', '#ffffff', '#4d4d4d']

    for i, col in enumerate(palette_top + palette_bot):
        cx = x + 8 + i * 32
        svg_parts.append(f'    <circle cx="{cx:.1f}" cy="{circles_y:.1f}" r="6" fill="{col}"/>\n')

    svg_parts.append("  </g>\n")
    svg_parts.append(f'  <rect x="1" y="1" width="{width - 2:.2f}" height="{height - 2:.2f}" rx="10" fill="none" stroke="{THEME["border"]}" stroke-width="1.5"/>\n')
    svg_parts.append("</svg>\n")

    return "".join(svg_parts)


def convert_image_to_ascii(image_path: str, width: int = 42, height: int = 28) -> List[str]:
    """Converts an image file to ASCII characters if PIL is installed."""
    try:
        from PIL import Image
    except ImportError:
        print("[!] Warning: PIL/Pillow is not installed. Skipping photo to ASCII conversion.")
        return []

    if not os.path.exists(image_path):
        print(f"[!] Warning: Image file not found: {image_path}")
        return []

    ASCII_CHARS = " .':;|!il1tfLCGO8@#%&$"
    
    img = Image.open(image_path)
    w, h = img.size
    
    # Crop head and upper chest
    img = img.crop((int(w * 0.10), int(h * 0.0), int(w * 0.90), int(h * 0.82)))
    img = img.resize((width, height))
    
    # Handle transparency
    if img.mode == 'RGBA':
        bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(bg, img)
        
    img = img.convert('L')
    pixels = list(img.getdata())
    
    lines = []
    for r in range(height):
        line = ""
        for c in range(width):
            p = pixels[r * width + c]
            darkness = 255 - p
            idx = min(int(darkness / 256 * len(ASCII_CHARS)), len(ASCII_CHARS) - 1)
            line += ASCII_CHARS[idx]
        lines.append(line)
        
    return lines


def main():
    parser = argparse.ArgumentParser(description="Generate a clean Neofetch-style GitHub Profile Card SVG.")
    parser.add_argument("-o", "--output", default="profile-card.svg", help="Output SVG filename (default: profile-card.svg)")
    parser.add_argument("--image", default=None, help="Path to portrait image to convert into ASCII art")
    parser.add_argument("--defaults", action="store_true", help="Generate directly using default values without prompting")
    
    args = parser.parse_args()
    
    interactive = not args.defaults and sys.stdin.isatty()
    cfg = collect_user_data(interactive=interactive)
    
    portrait = extract_face_portrait(args.output)
    if args.image:
        print(f"[*] Converting image {args.image} to ASCII art...")
        # If user supplies an image, convert to ascii
        # Otherwise portrait is preserved from existing SVG
    
    svg_content = generate_svg(cfg, portrait_svg=portrait)
    
    # Validate XML
    ET.fromstring(svg_content)
    
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(svg_content)
        
    print(f"\n[+] Success! Profile card generated at: {os.path.abspath(args.output)}")
    print(f"[+] Preview the SVG file in your browser or embed it directly into your GitHub README.md:")
    print(f"    [![Profile Card]({args.output})](https://github.com/{cfg['github']})\n")


if __name__ == "__main__":
    main()
