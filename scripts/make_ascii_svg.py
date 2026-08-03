#!/usr/bin/env python3
"""
make_ascii_svg.py

Converts preprocessed portrait image ('assets/source-prepped.png') into an animated
monochrome ASCII SVG portrait ('avi-ascii.svg').

Features:
- Configurable parameters (ASCII columns, rows, colors, font, animation speed).
- Monochrome density mapping using " .`:-=+*cs#%@".
- Pure SVG + CSS animations (no JavaScript, no external assets).
- Top-to-bottom row-by-row typing reveal with moving block cursor (█ or ▌).
- Accessible (<title>, <desc>, aria-labelledby).
- Optimized SVG size with reusable delay classes and clipPath definitions.
"""

import sys
from pathlib import Path
from PIL import Image

# ==============================================================================
# CONFIGURATION SECTION
# ==============================================================================

ASCII_COLS = 100               # Number of character columns (~100)
ASCII_ROWS = 53                # Number of character rows (~53)

DENSITY_RAMP = " .`:-=+*cs#%@" # Bright -> Dark character density ramp

FOREGROUND_COLOR = "#c9d1d9"   # Monochrome text & cursor color (GitHub dark theme white/silver)
FONT_FAMILY = "Consolas, Menlo, Monaco, 'Courier New', monospace"
FONT_SIZE = 12                 # Monospace font size (px)
CELL_ASPECT = 0.60             # Character width-to-height ratio (width = size * 0.6)
LINE_HEIGHT_RATIO = 1.15       # Line height multiplier

ANIM_SPEED_SEC = 3.5           # Total typing animation duration (seconds)
CURSOR_CHAR = "█"              # Cursor character ("█" or "▌")

PADDING_X = 20                 # Horizontal padding (px)
PADDING_Y = 30                 # Vertical padding (px)


def load_and_sample_image(img_path: Path, cols: int, rows: int) -> list:
    """
    Load prepped image, crop to target aspect ratio, and sample into a 2D matrix
    of ASCII characters based on pixel density.
    """
    if not img_path.exists():
        cwd_img = Path("assets/source-prepped.png")
        if cwd_img.exists():
            img_path = cwd_img
        else:
            raise FileNotFoundError(f"Prepped image not found at: {img_path}")

    img = Image.open(img_path).convert("L")
    img_w, img_h = img.size

    # Calculate grid dimensions and cell aspect ratios
    char_w = FONT_SIZE * CELL_ASPECT
    char_h = FONT_SIZE * LINE_HEIGHT_RATIO
    target_grid_w = cols * char_w
    target_grid_h = rows * char_h

    # Calculate target aspect ratio to avoid facial distortion
    target_aspect = target_grid_w / target_grid_h
    img_aspect = img_w / float(img_h)

    if img_aspect > target_aspect:
        # Image is wider -> crop left/right margins
        crop_w = int(img_h * target_aspect)
        left = (img_w - crop_w) // 2
        crop_box = (left, 0, left + crop_w, img_h)
    else:
        # Image is taller -> crop top/bottom margins
        crop_h = int(img_w / target_aspect)
        top = (img_h - crop_h) // 2
        crop_box = (0, top, img_w, top + crop_h)

    cropped = img.crop(crop_box)
    resized = cropped.resize((cols, rows), Image.Resampling.LANCZOS)

    # Convert grayscale values (0=black, 255=white) to ASCII density ramp
    # Bright pixels (255) -> sparse chars (ramp[0]), Dark pixels (0) -> dense chars (ramp[-1])
    ramp_len = len(DENSITY_RAMP)
    ascii_matrix = []

    for r in range(rows):
        row_chars = []
        for c in range(cols):
            val = resized.getpixel((c, r))
            idx = int((255 - val) / 255.0 * (ramp_len - 1))
            row_chars.append(DENSITY_RAMP[idx])
        ascii_matrix.append("".join(row_chars))

    return ascii_matrix


def generate_ascii_svg(ascii_matrix: list) -> str:
    """Generate animated monochrome ASCII SVG XML text."""
    rows = len(ascii_matrix)
    cols = len(ascii_matrix[0]) if rows > 0 else 0

    char_w = FONT_SIZE * CELL_ASPECT
    char_h = FONT_SIZE * LINE_HEIGHT_RATIO

    grid_w = cols * char_w
    grid_h = rows * char_h

    svg_w = int(PADDING_X * 2 + grid_w)
    svg_h = int(PADDING_Y * 2 + grid_h)

    # Time calculations
    total_time = float(ANIM_SPEED_SEC)
    time_per_row = total_time / float(rows)
    row_type_duration = max(time_per_row * 1.2, 0.06)

    # Generate CSS reusable animation delay classes and keyframes
    delay_css_rules = []
    clip_defs = []

    for r in range(rows):
        row_delay = r * time_per_row
        delay_css_rules.append(f"      .cd-{r} {{ animation-delay: {row_delay:.3f}s; }}")

        # Clip rect for line r
        clip_y = PADDING_Y + r * char_h - (char_h * 0.2)
        clip_h = char_h * 1.3
        clip_defs.append(
            f'    <clipPath id="cp-{r}"><rect class="cr cd-{r}" x="{PADDING_X}" y="{clip_y:.1f}" '
            f'width="0" height="{clip_h:.1f}" /></clipPath>'
        )

    # Generate Cursor movement keyframes
    cursor_keyframes = []
    cursor_keyframes.append("      @keyframes moveCursor {")

    for r in range(rows):
        t_start = r * time_per_row
        t_end = t_start + row_type_duration
        pct_start = (t_start / total_time) * 100.0
        pct_end = min((t_end / total_time) * 100.0, 100.0)

        y_pos = PADDING_Y + r * char_h

        cursor_keyframes.append(
            f"        {pct_start:.2f}% {{ transform: translate({PADDING_X}px, {y_pos:.1f}px); opacity: 1; }}"
        )
        cursor_keyframes.append(
            f"        {pct_end:.2f}% {{ transform: translate({PADDING_X + grid_w:.1f}px, {y_pos:.1f}px); opacity: 1; }}"
        )

    cursor_keyframes.append("        100% { opacity: 0; }")
    cursor_keyframes.append("      }")

    delay_css_str = "\n".join(delay_css_rules)
    clip_defs_str = "\n".join(clip_defs)
    cursor_keyframes_str = "\n".join(cursor_keyframes)

    svg = []
    # Root SVG with accessibility and responsive scaling
    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" '
        f'width="100%" height="100%" preserveAspectRatio="xMidYMid meet" '
        f'style="max-width: {svg_w}px; height: auto;" role="img" '
        f'aria-labelledby="ascii-title ascii-desc">'
    )

    # Accessible Title & Description
    svg.append('  <title id="ascii-title">Animated Monochrome ASCII Portrait</title>')
    svg.append(
        '  <desc id="ascii-desc">A self-typing monochrome ASCII art representation of a human portrait for GitHub profile.</desc>'
    )

    # Embedded CSS Definitions
    svg.append(f"""  <defs>
    <style>
      .ascii-text {{
        font-family: {FONT_FAMILY};
        font-size: {FONT_SIZE}px;
        fill: {FOREGROUND_COLOR};
        white-space: pre;
      }}
      .cursor-text {{
        font-family: {FONT_FAMILY};
        font-size: {FONT_SIZE}px;
        fill: {FOREGROUND_COLOR};
        opacity: 0;
        animation: moveCursor {total_time:.2f}s linear forwards;
      }}
      @keyframes revealRow {{
        0% {{ width: 0px; }}
        100% {{ width: {grid_w:.1f}px; }}
      }}
      .cr {{
        animation: revealRow {row_type_duration:.3f}s linear forwards;
      }}
{delay_css_str}
{cursor_keyframes_str}
    </style>
{clip_defs_str}
  </defs>""")

    # ASCII Text Rows
    svg.append('  <!-- ASCII Art Text Grid -->')
    svg.append('  <g class="ascii-art">')
    for r, row_str in enumerate(ascii_matrix):
        y_pos = PADDING_Y + r * char_h + (FONT_SIZE * 0.8)
        # Escape any XML special characters if present
        escaped_str = (
            row_str.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        svg.append(
            f'    <text x="{PADDING_X}" y="{y_pos:.1f}" class="ascii-text" '
            f'clip-path="url(#cp-{r})" xml:space="preserve">{escaped_str}</text>'
        )
    svg.append('  </g>')

    # Animated Block Cursor
    svg.append('  <!-- Typing Cursor -->')
    svg.append(f'  <text class="cursor-text" xml:space="preserve">{CURSOR_CHAR}</text>')

    svg.append('</svg>')
    return "\n".join(svg)


def main():
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    prepped_img_path = project_root / "assets" / "source-prepped.png"
    output_svg_path = project_root / "avi-ascii.svg"

    print(f"Loading prepped image from: {prepped_img_path}")
    ascii_matrix = load_and_sample_image(prepped_img_path, ASCII_COLS, ASCII_ROWS)

    print(f"Generating ASCII SVG ({ASCII_COLS} cols x {ASCII_ROWS} rows)...")
    svg_content = generate_ascii_svg(ascii_matrix)

    print(f"Writing SVG to: {output_svg_path}")
    with open(output_svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

    print("Successfully generated avi-ascii.svg!")


if __name__ == "__main__":
    main()
