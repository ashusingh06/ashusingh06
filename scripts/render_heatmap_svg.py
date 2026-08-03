#!/usr/bin/env python3
"""
render_heatmap_svg.py

Production-ready, standalone Python script to render a fully animated, responsive
GitHub contribution graph SVG from 'data/contributions.json'.

Features:
- 100% Python Standard Library (no external dependencies, no svgwrite).
- Strict Sunday-first week calendar layout with dynamic week calculations.
- Responsive scaling (400px to 1400px) with SVG viewBox & preserveAspectRatio.
- Accessibility-first with <title>, <desc>, aria-labelledby, and day tooltips.
- Production CSS animation: opacity (0->1), translateY(8px->0), scale(0.92->1).
- Single-run diagonal stagger animation using reusable CSS classes (.d-0, .d-1...).
- Automatic contribution statistics (total, active days, streaks, averages).
- Configurable color themes (DARK_PALETTE and LIGHT_PALETTE).
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ==============================================================================
# COLOR PALETTES & THEMES
# ==============================================================================

PALETTES = {
    "dark": {
        "bg": "#0d1117",
        "border": "#30363d",
        "text": "#8b949e",
        "text_sub": "#7d8590",
        "text_title": "#c9d1d9",
        "levels": [
            "#161b22",  # Level 0: Empty / No contributions
            "#0e4429",  # Level 1: Low
            "#006d32",  # Level 2: Medium-Low
            "#26a641",  # Level 3: Medium-High
            "#39d353"   # Level 4: High
        ]
    },
    "light": {
        "bg": "#ffffff",
        "border": "#d0d7de",
        "text": "#57606a",
        "text_sub": "#6e7781",
        "text_title": "#24292f",
        "levels": [
            "#ebedf0",  # Level 0
            "#9be9a8",  # Level 1
            "#40c463",  # Level 2
            "#30a14e",  # Level 3
            "#216e39"   # Level 4
        ]
    }
}

# Change default theme here ("dark" or "light")
DEFAULT_THEME = "dark"

# ==============================================================================
# LAYOUT & METRICS CONFIGURATION
# ==============================================================================

CELL_SIZE = 11       # Square width and height (px)
CELL_GAP = 3         # Gap between adjacent squares (px)
CELL_STEP = CELL_SIZE + CELL_GAP  # Grid step size (14px)
CORNER_RADIUS = 2.5  # Corner radius rx/ry (px)

TOTAL_ROWS = 7       # Sunday (0) to Saturday (6)

MARGIN_LEFT = 36     # Space for weekday labels (Mon, Wed, Fri)
MARGIN_TOP = 54      # Top margin for card header and month labels
MARGIN_RIGHT = 25    # Right padding
MARGIN_BOTTOM = 52   # Bottom margin for footer and legend

# ==============================================================================
# DATA LOADING & STATISTICS COMPUTATION
# ==============================================================================


def load_contributions(json_path: Path) -> list:
    """Load contribution dataset from JSON file."""
    if not json_path.exists():
        cwd_json = Path("data/contributions.json")
        if cwd_json.exists():
            json_path = cwd_json
        else:
            raise FileNotFoundError(f"Contributions JSON file not found at: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


def parse_and_sort_entries(raw_data: list) -> list:
    """Parse string dates to datetime.date objects and normalize entries."""
    parsed = []
    for item in raw_data:
        dt = datetime.strptime(item["date"], "%Y-%m-%d").date()
        count = int(item.get("count", 0))
        level = min(max(int(item.get("level", 0)), 0), 4)
        parsed.append({
            "date": dt,
            "date_str": item["date"],
            "count": count,
            "level": level
        })

    parsed.sort(key=lambda x: x["date"])
    return parsed


def compute_statistics(entries: list) -> dict:
    """Calculate summary metrics: total, streaks, active days, and average."""
    if not entries:
        return {
            "total": 0,
            "active_days": 0,
            "avg_per_day": 0.0,
            "longest_streak": 0,
            "current_streak": 0
        }

    total = sum(e["count"] for e in entries)
    active_days = sum(1 for e in entries if e["count"] > 0 or e["level"] > 0)
    avg_per_day = total / len(entries) if entries else 0.0

    # Longest streak calculation
    longest_streak = 0
    curr = 0
    for e in entries:
        if e["count"] > 0 or e["level"] > 0:
            curr += 1
            if curr > longest_streak:
                longest_streak = curr
        else:
            curr = 0

    # Current streak calculation (backwards from latest date)
    current_streak = 0
    if entries:
        idx = len(entries) - 1
        # Allow today to be 0 if yesterday was active
        if (entries[idx]["count"] == 0 and entries[idx]["level"] == 0) and idx > 0 and (entries[idx - 1]["count"] > 0 or entries[idx - 1]["level"] > 0):
            idx -= 1
        while idx >= 0 and (entries[idx]["count"] > 0 or entries[idx]["level"] > 0):
            current_streak += 1
            idx -= 1

    return {
        "total": total,
        "active_days": active_days,
        "avg_per_day": avg_per_day,
        "longest_streak": longest_streak,
        "current_streak": current_streak
    }


def compute_calendar_grid(entries: list):
    """
    Compute exact Sunday-first GitHub calendar grid matrix.
    Dynamically determines start Sunday and week count from data.
    """
    if not entries:
        raise ValueError("Cannot compute calendar grid for empty entries dataset.")

    dates = [e["date"] for e in entries]
    min_date = min(dates)
    max_date = max(dates)

    # Sunday-first DOW calculation: Python Monday=0..Sun=6 -> Sunday=0, Mon=1..Sat=6
    first_dow = (min_date.weekday() + 1) % 7
    first_sunday = min_date - timedelta(days=first_dow)

    last_dow = (max_date.weekday() + 1) % 7
    last_sunday = max_date - timedelta(days=last_dow)

    total_weeks = (last_sunday - first_sunday).days // 7 + 1
    total_weeks = max(total_weeks, 53)  # Standard GitHub calendar spans 53 weeks

    grid = {}
    for entry in entries:
        dt = entry["date"]
        col = (dt - first_sunday).days // 7
        row = (dt.weekday() + 1) % 7
        if 0 <= col < total_weeks and 0 <= row < TOTAL_ROWS:
            grid[(col, row)] = entry

    return grid, first_sunday, total_weeks


# ==============================================================================
# SVG RENDERER
# ==============================================================================


def generate_svg(entries: list, theme_name: str = DEFAULT_THEME) -> str:
    """Generate production-grade SVG XML text representation."""
    palette = PALETTES.get(theme_name, PALETTES["dark"])
    stats = compute_statistics(entries)
    grid, first_sunday, total_weeks = compute_calendar_grid(entries)

    grid_width = total_weeks * CELL_STEP - CELL_GAP
    grid_height = TOTAL_ROWS * CELL_STEP - CELL_GAP

    svg_width = MARGIN_LEFT + grid_width + MARGIN_RIGHT
    svg_height = MARGIN_TOP + grid_height + MARGIN_BOTTOM

    # Calculate month labels
    month_labels = []
    prev_month = None
    last_col = -5

    for col in range(total_weeks):
        col_date = first_sunday + timedelta(days=col * 7)
        if col_date.month != prev_month:
            if col - last_col >= 2:
                month_name = col_date.strftime("%b")
                month_labels.append((col, month_name))
                last_col = col
            prev_month = col_date.month

    # Generate reusable animation delay CSS classes to minimize SVG size
    max_diag = (total_weeks - 1) + (TOTAL_ROWS - 1)
    delay_css_rules = []
    for diag in range(max_diag + 1):
        delay_sec = diag * 0.025
        delay_css_rules.append(f"      .d-{diag} {{ animation-delay: {delay_sec:.3f}s; }}")
    delay_css_str = "\n".join(delay_css_rules)

    svg = []
    # Root SVG tag with accessibility and responsive parameters
    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" '
        f'width="100%" height="100%" preserveAspectRatio="xMidYMid meet" '
        f'style="max-width: {svg_width}px; height: auto;" role="img" '
        f'aria-labelledby="heatmap-title heatmap-desc">'
    )

    # Accessible title and description
    svg.append('  <title id="heatmap-title">GitHub Contribution Heatmap</title>')
    svg.append(
        '  <desc id="heatmap-desc">Animated contribution graph showing public activity over the past year.</desc>'
    )

    # Internal CSS Styles
    svg.append(f"""  <defs>
    <style>
      .bg-card {{
        fill: {palette["bg"]};
        stroke: {palette["border"]};
        stroke-width: 1px;
        rx: 6px;
      }}
      .title-text {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        font-size: 12px;
        font-weight: 600;
        fill: {palette["text_title"]};
      }}
      .stats-text {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        font-size: 10px;
        fill: {palette["text"]};
      }}
      .label-text {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        font-size: 10px;
        fill: {palette["text"]};
      }}
      .footer-text {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        font-size: 10px;
        fill: {palette["text_sub"]};
      }}
      @keyframes fadeInReveal {{
        0% {{
          opacity: 0;
          transform: translateY(8px) scale(0.92);
        }}
        100% {{
          opacity: 1;
          transform: translateY(0) scale(1);
        }}
      }}
      .day-cell {{
        opacity: 0;
        transform-box: fill-box;
        transform-origin: center;
        animation: fadeInReveal 0.45s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        transition: stroke 0.15s ease;
      }}
      .day-cell:hover {{
        stroke: {palette["text_title"]};
        stroke-width: 1px;
      }}
{delay_css_str}
    </style>
  </defs>""")

    # Background Card
    svg.append(f'  <rect class="bg-card" width="{svg_width}" height="{svg_height}" />')

    # Card Header / Statistics Bar
    stats_str = (
        f"Total: {stats['total']}  •  Active: {stats['active_days']}d  •  "
        f"Streak: {stats['current_streak']}d ({stats['longest_streak']}d max)  •  "
        f"Avg: {stats['avg_per_day']:.2f}/day"
    )
    svg.append('  <!-- Header & Statistics -->')
    svg.append(f'  <text x="{MARGIN_LEFT}" y="25" class="title-text">GitHub Activity</text>')
    svg.append(
        f'  <text x="{svg_width - MARGIN_RIGHT}" y="25" class="stats-text" text-anchor="end">{stats_str}</text>'
    )

    # Month Labels
    svg.append('  <!-- Month Labels -->')
    svg.append('  <g class="month-labels">')
    for col, m_name in month_labels:
        x_pos = MARGIN_LEFT + col * CELL_STEP
        y_pos = MARGIN_TOP - 8
        svg.append(f'    <text x="{x_pos}" y="{y_pos}" class="label-text">{m_name}</text>')
    svg.append('  </g>')

    # Weekday Labels (Mon, Wed, Fri)
    svg.append('  <!-- Weekday Labels -->')
    svg.append('  <g class="weekday-labels">')
    weekdays_to_show = [(1, "Mon"), (3, "Wed"), (5, "Fri")]
    for row, w_name in weekdays_to_show:
        x_pos = MARGIN_LEFT - 8
        y_pos = MARGIN_TOP + row * CELL_STEP + 9
        svg.append(
            f'    <text x="{x_pos}" y="{y_pos}" class="label-text" text-anchor="end">{w_name}</text>'
        )
    svg.append('  </g>')

    # Contribution Day Rectangles
    svg.append('  <!-- Contribution Day Grid -->')
    svg.append('  <g class="heatmap-grid">')

    for col in range(total_weeks):
        for row in range(TOTAL_ROWS):
            x_pos = MARGIN_LEFT + col * CELL_STEP
            y_pos = MARGIN_TOP + row * CELL_STEP

            entry = grid.get((col, row))
            if entry:
                count = entry["count"]
                level = entry["level"]
                date_str = entry["date_str"]
                color = palette["levels"][level]
                if count > 0:
                    count_text = f"{count} contribution{'s' if count != 1 else ''}"
                elif level > 0:
                    count_text = f"Level {level} activity"
                else:
                    count_text = "No contributions"
                tooltip = f"{date_str}\n{count_text}"
            else:
                color = palette["levels"][0]
                tooltip = "No contributions"

            diag_index = col + row
            svg.append(
                f'    <rect class="day-cell d-{diag_index}" x="{x_pos}" y="{y_pos}" '
                f'width="{CELL_SIZE}" height="{CELL_SIZE}" rx="{CORNER_RADIUS}" ry="{CORNER_RADIUS}" '
                f'fill="{color}"><title>{tooltip}</title></rect>'
            )

    svg.append('  </g>')

    # Footer & Less -> More Legend
    y_footer = MARGIN_TOP + grid_height + 28
    svg.append('  <!-- Footer & Legend -->')
    svg.append(
        f'  <text x="{MARGIN_LEFT}" y="{y_footer}" class="footer-text">'
        f'Generated automatically from public GitHub contribution data.</text>'
    )

    legend_right_x = MARGIN_LEFT + grid_width
    legend_rect_size = 10
    legend_gap = 3
    legend_total_width = 5 * (legend_rect_size + legend_gap) - legend_gap
    rects_start_x = legend_right_x - legend_total_width - 32
    text_less_x = rects_start_x - 26
    text_more_x = legend_right_x

    svg.append('  <g class="legend">')
    svg.append(f'    <text x="{text_less_x}" y="{y_footer}" class="label-text">Less</text>')
    for idx, color_hex in enumerate(palette["levels"]):
        lx = rects_start_x + idx * (legend_rect_size + legend_gap)
        ly = y_footer - 8
        svg.append(
            f'    <rect x="{lx}" y="{ly}" width="{legend_rect_size}" height="{legend_rect_size}" '
            f'rx="2" ry="2" fill="{color_hex}" />'
        )
    svg.append(f'    <text x="{text_more_x}" y="{y_footer}" class="label-text">More</text>')
    svg.append('  </g>')

    svg.append('</svg>')
    return "\n".join(svg)


# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================


def main():
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    json_path = project_root / "data" / "contributions.json"
    output_svg_path = project_root / "contrib-heatmap.svg"

    contributions_raw = load_contributions(json_path)
    entries = parse_and_sort_entries(contributions_raw)

    svg_content = generate_svg(entries, theme_name=DEFAULT_THEME)

    with open(output_svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

    # Save copy to data/ folder
    data_svg_path = project_root / "data" / "contrib-heatmap.svg"
    with open(data_svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)


if __name__ == "__main__":
    main()
