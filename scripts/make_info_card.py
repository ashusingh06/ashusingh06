#!/usr/bin/env python3
"""
make_info_card.py

Generates a Neofetch-style terminal information card SVG ('info-card.svg')
for a GitHub Profile README.

Uses 100% Python Standard Library to output raw, production-grade SVG text with:
- GitHub Dark theme styling (#0d1117 background, #30363d border, curated accents).
- Terminal window titlebar with window control buttons and prompt.
- Two-column Neofetch layout (System, Stack, Projects, Current Mission).
- Single-run sequential CSS line-reveal animation (opacity 0->1, translateY 6px->0px).
- Accessibility attributes (<title>, <desc>, aria-labelledby).
- Responsive viewBox parameters (490 x 320).
"""

import sys
from pathlib import Path

# ==============================================================================
# CONFIGURATION & THEME METRICS
# ==============================================================================

SVG_WIDTH = 490
SVG_HEIGHT = 320
BORDER_RADIUS = 8

FONT_FAMILY = "Consolas, Menlo, Monaco, 'Courier New', monospace"

# GitHub Dark Theme Colors
COLOR_BG = "#0d1117"
COLOR_BORDER = "#30363d"
COLOR_TEXT_MAIN = "#c9d1d9"
COLOR_TEXT_MUTED = "#8b949e"
COLOR_ACCENT_BLUE = "#58a6ff"
COLOR_ACCENT_GREEN = "#3fb950"
COLOR_ACCENT_YELLOW = "#d29922"
COLOR_ACCENT_CYAN = "#a5d6ff"
COLOR_ACCENT_RED = "#ff7b72"

# Window Control Dot Colors
DOT_RED = "#ff5f56"
DOT_YELLOW = "#ffbd2e"
DOT_GREEN = "#27c93f"


# ==============================================================================
# SVG BUILDER
# ==============================================================================

def generate_info_card_svg() -> str:
    """Generate Neofetch-style terminal information card SVG text."""
    svg = []

    # Root <svg> element
    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}" '
        f'width="100%" height="100%" preserveAspectRatio="xMidYMid meet" '
        f'style="max-width: {SVG_WIDTH}px; height: auto;" role="img" '
        f'aria-labelledby="card-title card-desc">'
    )

    # Accessibility tags
    svg.append('  <title id="card-title">Ashish Singh - Developer Profile Card</title>')
    svg.append(
        '  <desc id="card-desc">Neofetch-style terminal card displaying system info, tech stack, projects, and current mission.</desc>'
    )

    # CSS Definitions & Keyframe Animation
    svg.append(f"""  <defs>
    <style>
      .bg-card {{
        fill: {COLOR_BG};
        stroke: {COLOR_BORDER};
        stroke-width: 1px;
        rx: {BORDER_RADIUS}px;
      }}
      .titlebar-line {{
        stroke: {COLOR_BORDER};
        stroke-width: 1px;
      }}
      .term-text {{
        font-family: {FONT_FAMILY};
        font-size: 11px;
        fill: {COLOR_TEXT_MAIN};
        white-space: pre;
      }}
      .line {{
        opacity: 0;
        animation: lineFadeIn 0.35s ease-out forwards;
      }}
      @keyframes lineFadeIn {{
        0% {{
          opacity: 0;
          transform: translateY(6px);
        }}
        100% {{
          opacity: 1;
          transform: translateY(0);
        }}
      }}
      .l-0 {{ animation-delay: 0.05s; }}
      .l-1 {{ animation-delay: 0.12s; }}
      .l-2 {{ animation-delay: 0.19s; }}
      .l-3 {{ animation-delay: 0.26s; }}
      .l-4 {{ animation-delay: 0.33s; }}
      .l-5 {{ animation-delay: 0.40s; }}
      .l-6 {{ animation-delay: 0.47s; }}
      .l-7 {{ animation-delay: 0.54s; }}
      .l-8 {{ animation-delay: 0.61s; }}
      .l-9 {{ animation-delay: 0.68s; }}
      .l-10 {{ animation-delay: 0.75s; }}
      .l-11 {{ animation-delay: 0.82s; }}
    </style>
  </defs>""")

    # Background Card & Terminal Header Bar
    svg.append(f'  <rect class="bg-card" width="{SVG_WIDTH}" height="{SVG_HEIGHT}" />')

    # Window Control Buttons
    svg.append(f'  <circle cx="16" cy="16" r="4.5" fill="{DOT_RED}" />')
    svg.append(f'  <circle cx="30" cy="16" r="4.5" fill="{DOT_YELLOW}" />')
    svg.append(f'  <circle cx="44" cy="16" r="4.5" fill="{DOT_GREEN}" />')

    # Header Titlebar Text & Divider
    svg.append(
        f'  <text x="{SVG_WIDTH / 2}" y="19" class="term-text" fill="{COLOR_TEXT_MUTED}" '
        f'text-anchor="middle" font-size="10">ashu@dev:~ (neofetch)</text>'
    )
    svg.append(f'  <line x1="0" y1="30" x2="{SVG_WIDTH}" y2="30" class="titlebar-line" />')

    # Content Lines Container
    svg.append('  <!-- Terminal Content Lines -->')

    # Line 0: Command Prompt Line
    svg.append(
        f'  <g class="line l-0"><text x="20" y="50" class="term-text">'
        f'<tspan fill="{COLOR_ACCENT_BLUE}">ashu@dev</tspan>'
        f'<tspan fill="{COLOR_ACCENT_GREEN}">:~$</tspan> '
        f'<tspan fill="{COLOR_TEXT_MAIN}">neofetch --user ashusingh06</tspan>'
        f'</text></g>'
    )

    # Line 1: Header Profile Name & Subtitle
    svg.append(
        f'  <g class="line l-1"><text x="20" y="68" class="term-text">'
        f'<tspan fill="{COLOR_ACCENT_BLUE}" font-weight="bold" font-size="13">Ashish Singh</tspan> '
        f'<tspan fill="{COLOR_TEXT_MUTED}" font-size="10">  •  Student • Full Stack Developer • AI Learner</tspan>'
        f'</text></g>'
    )

    # Line 2: Divider Line
    divider_chars = "─" * 58
    svg.append(
        f'  <g class="line l-2"><text x="20" y="82" class="term-text" fill="{COLOR_BORDER}">{divider_chars}</text></g>'
    )

    # Section Headers (Line 3)
    svg.append(
        f'  <g class="line l-3"><text x="20" y="102" class="term-text">'
        f'<tspan fill="{COLOR_ACCENT_YELLOW}" font-weight="bold">SYSTEM</tspan>'
        f'<tspan x="245" fill="{COLOR_ACCENT_YELLOW}" font-weight="bold">PROJECTS</tspan>'
        f'</text></g>'
    )

    # Row 1 (Line 4)
    svg.append(
        f'  <g class="line l-4"><text x="20" y="120" class="term-text">'
        f'<tspan fill="{COLOR_TEXT_MUTED}">OS        </tspan><tspan fill="{COLOR_TEXT_MAIN}">Windows 11</tspan>'
        f'<tspan x="245" fill="{COLOR_ACCENT_GREEN}">❯ </tspan><tspan fill="{COLOR_TEXT_MAIN}">AI Agents</tspan>'
        f'</text></g>'
    )

    # Row 2 (Line 5)
    svg.append(
        f'  <g class="line l-5"><text x="20" y="138" class="term-text">'
        f'<tspan fill="{COLOR_TEXT_MUTED}">Editor    </tspan><tspan fill="{COLOR_TEXT_MAIN}">VS Code</tspan>'
        f'<tspan x="245" fill="{COLOR_ACCENT_GREEN}">❯ </tspan><tspan fill="{COLOR_TEXT_MAIN}">Discord Logger</tspan>'
        f'</text></g>'
    )

    # Row 3 (Line 6)
    svg.append(
        f'  <g class="line l-6"><text x="20" y="156" class="term-text">'
        f'<tspan fill="{COLOR_TEXT_MUTED}">Shell     </tspan><tspan fill="{COLOR_TEXT_MAIN}">PowerShell</tspan>'
        f'<tspan x="245" fill="{COLOR_ACCENT_GREEN}">❯ </tspan><tspan fill="{COLOR_TEXT_MAIN}">Study Tracker</tspan>'
        f'</text></g>'
    )

    # Row 4 (Line 7)
    svg.append(
        f'  <g class="line l-7"><text x="20" y="174" class="term-text">'
        f'<tspan fill="{COLOR_TEXT_MUTED}">GitHub    </tspan><tspan fill="{COLOR_TEXT_MAIN}">ashusingh06</tspan>'
        f'<tspan x="245" fill="{COLOR_ACCENT_GREEN}">❯ </tspan><tspan fill="{COLOR_TEXT_MAIN}">Portfolio Website</tspan>'
        f'</text></g>'
    )

    # Section Headers 2 (Line 8)
    svg.append(
        f'  <g class="line l-8"><text x="20" y="198" class="term-text">'
        f'<tspan fill="{COLOR_ACCENT_BLUE}" font-weight="bold">STACK</tspan>'
        f'<tspan x="245" fill="{COLOR_ACCENT_BLUE}" font-weight="bold">CURRENT MISSION</tspan>'
        f'</text></g>'
    )

    # Row 5 (Line 9)
    svg.append(
        f'  <g class="line l-9"><text x="20" y="216" class="term-text">'
        f'<tspan fill="{COLOR_TEXT_MAIN}">Next.js • Node.js • TS</tspan>'
        f'<tspan x="245" fill="{COLOR_ACCENT_CYAN}">❯ </tspan><tspan fill="{COLOR_TEXT_MAIN}">Build AI Agents</tspan>'
        f'</text></g>'
    )

    # Row 6 (Line 10)
    svg.append(
        f'  <g class="line l-10"><text x="20" y="234" class="term-text">'
        f'<tspan fill="{COLOR_TEXT_MAIN}">Python  • Supabase • Git</tspan>'
        f'<tspan x="245" fill="{COLOR_ACCENT_CYAN}">❯ </tspan><tspan fill="{COLOR_TEXT_MAIN}">Master AI Architectures</tspan>'
        f'</text></g>'
    )

    # Row 7 & 8 Missions (Line 11)
    svg.append(
        f'  <g class="line l-11"><text x="245" y="252" class="term-text">'
        f'<tspan fill="{COLOR_ACCENT_CYAN}">❯ </tspan><tspan fill="{COLOR_TEXT_MAIN}">Contribute to Open Source</tspan>'
        f'</text>'
        f'<text x="245" y="270" class="term-text">'
        f'<tspan fill="{COLOR_ACCENT_CYAN}">❯ </tspan><tspan fill="{COLOR_TEXT_MAIN}">Ship Production Software</tspan>'
        f'</text>'
        f'<text x="20" y="295" class="term-text">'
        f'<tspan fill="{COLOR_ACCENT_GREEN}">❯ </tspan>'
        f'<tspan fill="{COLOR_TEXT_MUTED}">Status: </tspan>'
        f'<tspan fill="{COLOR_ACCENT_BLUE}">Building &amp; Shipping</tspan> '
        f'<tspan fill="{COLOR_ACCENT_BLUE}">█</tspan>'
        f'</text></g>'
    )

    svg.append('</svg>')
    return "\n".join(svg)


def main():
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    output_svg_path = project_root / "info-card.svg"

    print(f"Generating Neofetch-style terminal info card...")
    svg_content = generate_info_card_svg()

    print(f"Writing SVG to: {output_svg_path}")
    with open(output_svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

    # Save copy in data/ folder for convenience
    data_svg_path = project_root / "data" / "info-card.svg"
    data_svg_path.parent.mkdir(parents=True, exist_ok=True)
    with open(data_svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

    print("Successfully generated info-card.svg!")


if __name__ == "__main__":
    main()
