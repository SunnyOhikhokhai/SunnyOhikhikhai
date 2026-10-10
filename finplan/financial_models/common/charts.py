"""
Tiny server-side SVG chart renderer.

Charts are drawn from the project's calculated figures, so no JavaScript
charting library (or CDN) is needed and charts also print correctly.
Colours come from CSS classes that use the FINPLAN design tokens.
"""
from __future__ import annotations

import math
from decimal import Decimal

from django.utils.html import escape
from django.utils.safestring import mark_safe

from .report import Chart, Formatter

WIDTH, HEIGHT = 720, 300
PAD_LEFT, PAD_RIGHT, PAD_TOP, PAD_BOTTOM = 72, 16, 16, 44


def _nice_step(span: float, target_ticks: int = 4) -> float:
    if span <= 0:
        return 1.0
    raw = span / target_ticks
    magnitude = 10 ** math.floor(math.log10(raw))
    for multiplier in (1, 2, 2.5, 5, 10):
        if raw <= multiplier * magnitude:
            return multiplier * magnitude
    return 10 * magnitude


def _scale(chart: Chart) -> tuple[float, float, float]:
    values = [float(v) for s in chart.series for v in s.values]
    low = min([0.0, *values])
    high = max([0.0, *values])
    if low == high:
        high = low + 1
    step = _nice_step(high - low)
    low = math.floor(low / step) * step
    high = math.ceil(high / step) * step
    return low, high, step


def render_svg(chart: Chart, fmt: Formatter) -> str:
    if not chart.labels or not chart.series:
        return ""
    low, high, step = _scale(chart)
    plot_w = WIDTH - PAD_LEFT - PAD_RIGHT
    plot_h = HEIGHT - PAD_TOP - PAD_BOTTOM

    def y_pos(value: float) -> float:
        return PAD_TOP + plot_h * (high - value) / (high - low)

    parts = [
        f'<svg class="chart-svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" '
        f'aria-label="{escape(chart.title)}" preserveAspectRatio="xMidYMid meet">',
        f"<title>{escape(chart.title)}</title>",
    ]
    if chart.description:
        parts.append(f"<desc>{escape(chart.description)}</desc>")

    # Grid lines and Y-axis labels.
    tick = low
    while tick <= high + step / 2:
        y = y_pos(tick)
        css = "chart-zero" if abs(tick) < step / 1000 else "chart-gridline"
        parts.append(f'<line class="{css}" x1="{PAD_LEFT}" x2="{WIDTH - PAD_RIGHT}" y1="{y:.1f}" y2="{y:.1f}"/>')
        label = escape(fmt.compact(Decimal(str(round(tick, 6)))))
        parts.append(f'<text class="chart-axis" x="{PAD_LEFT - 8}" y="{y + 4:.1f}" text-anchor="end">{label}</text>')
        tick += step

    count = len(chart.labels)
    slot = plot_w / count
    label_every = max(1, math.ceil(count / 12))
    for i, label in enumerate(chart.labels):
        if i % label_every == 0:
            x = PAD_LEFT + slot * (i + 0.5)
            parts.append(f'<text class="chart-axis" x="{x:.1f}" y="{HEIGHT - PAD_BOTTOM + 18}" text-anchor="middle">{escape(label)}</text>')

    zero_y = y_pos(0.0)
    if chart.kind == "bar":
        n = len(chart.series)
        group_w = slot * 0.72
        bar_w = group_w / n
        for s_index, series in enumerate(chart.series):
            for i, value in enumerate(series.values):
                v = float(value)
                x = PAD_LEFT + slot * i + (slot - group_w) / 2 + bar_w * s_index
                top = min(y_pos(v), zero_y)
                height = max(abs(y_pos(v) - zero_y), 0.5 if v != 0 else 0)
                colour = series.colour
                if series.colour == "auto":
                    colour = "green" if v >= 0 else "red"
                tip = f"{series.name}, {chart.labels[i]}: {fmt.money(value)}"
                parts.append(
                    f'<rect class="chart-fill-{colour}" x="{x:.1f}" y="{top:.1f}" width="{max(bar_w - 1, 1):.1f}" '
                    f'height="{height:.1f}"><title>{escape(tip)}</title></rect>'
                )
    else:
        for series in chart.series:
            points = []
            for i, value in enumerate(series.values):
                x = PAD_LEFT + slot * (i + 0.5)
                points.append(f"{x:.1f},{y_pos(float(value)):.1f}")
            parts.append(f'<polyline class="chart-line chart-stroke-{series.colour}" points="{" ".join(points)}"/>')
            if count <= 40:
                for i, value in enumerate(series.values):
                    x = PAD_LEFT + slot * (i + 0.5)
                    tip = f"{series.name}, {chart.labels[i]}: {fmt.money(value)}"
                    parts.append(
                        f'<circle class="chart-dot chart-fill-{series.colour}" cx="{x:.1f}" cy="{y_pos(float(value)):.1f}" r="3">'
                        f"<title>{escape(tip)}</title></circle>"
                    )
    parts.append("</svg>")
    return mark_safe("".join(parts))
