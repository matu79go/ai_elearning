"""シンプルなチャート SVG 生成サービス (Python純正、依存なし)。

対応済み:
  - pie_chart(data)              : 円グラフ
  - bar_chart(data)              : 棒グラフ (gap 付き)
  - line_chart(points)           : 折れ線
  - function_plot(expr, x_range) : y = f(x) のグラフ (二次/三次/一般)
"""
from __future__ import annotations

import math

PALETTE = [
    '#6366f1', '#f59e0b', '#10b981', '#ef4444',
    '#8b5cf6', '#14b8a6', '#f97316', '#ec4899',
]


def pie_chart(data: list[dict], size: int = 320, show_legend: bool = True) -> str:
    """Pie chart SVG を返す。

    data: [{"label": str, "value": number, "color"?: str}, ...]
    """
    total = sum(float(d['value']) for d in data) or 1
    cx = size / 2
    cy = size / 2 - (10 if show_legend else 0)
    r = size * 0.35

    paths = []
    start_angle = -math.pi / 2  # 12時から時計回り

    for i, d in enumerate(data):
        frac = float(d['value']) / total
        angle = frac * 2 * math.pi
        end_angle = start_angle + angle
        large_arc = 1 if angle > math.pi else 0
        color = d.get('color') or PALETTE[i % len(PALETTE)]

        x1 = cx + r * math.cos(start_angle)
        y1 = cy + r * math.sin(start_angle)
        x2 = cx + r * math.cos(end_angle)
        y2 = cy + r * math.sin(end_angle)

        if frac >= 0.999:
            # 1つだけの場合、円をそのまま
            paths.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" stroke="white" stroke-width="2"/>'
            )
        else:
            paths.append(
                f'<path d="M{cx:.1f},{cy:.1f} L{x1:.1f},{y1:.1f} '
                f'A{r:.1f},{r:.1f} 0 {large_arc},1 {x2:.1f},{y2:.1f} Z" '
                f'fill="{color}" stroke="white" stroke-width="2"/>'
            )
        start_angle = end_angle

    # ラベル (中心から半径 0.65 の位置、十分広いスライスのみ)
    labels = []
    start_angle = -math.pi / 2
    for i, d in enumerate(data):
        frac = float(d['value']) / total
        angle = frac * 2 * math.pi
        mid = start_angle + angle / 2
        start_angle += angle
        if frac < 0.06:
            continue  # 小さすぎるスライスは内側ラベル省略
        lx = cx + r * 0.65 * math.cos(mid)
        ly = cy + r * 0.65 * math.sin(mid) + 4
        labels.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" '
            f'font-size="12" fill="white" font-weight="700">{d["label"]}</text>'
        )

    # 凡例 (サイズの下)
    legend = ''
    if show_legend:
        legend_items = []
        lgy = size - 20
        lgx = 16
        for i, d in enumerate(data):
            color = d.get('color') or PALETTE[i % len(PALETTE)]
            legend_items.append(
                f'<rect x="{lgx}" y="{lgy - 10}" width="12" height="12" fill="{color}"/>'
                f'<text x="{lgx + 18}" y="{lgy}" font-size="11" fill="#334155">{d["label"]} ({d["value"]})</text>'
            )
            # 次のアイテム位置 (改行考慮せず横並び、text幅概算)
            lgx += 18 + 8 * len(str(d['label'])) + 8 * len(str(d['value'])) + 20
        legend = ''.join(legend_items)

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'style="max-width:100%; height:auto;">'
        f'{"".join(paths)}{"".join(labels)}{legend}'
        f'</svg>'
    )


# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------

def _nice_step(range_val: float) -> float:
    """軸目盛りを "きれいな数" にする (1, 2, 5, 10, 20, 50 ...)"""
    if range_val <= 0:
        return 1
    rough = range_val / 5
    mag = 10 ** math.floor(math.log10(rough))
    norm = rough / mag
    if norm < 1.5:
        return 1 * mag
    if norm < 3:
        return 2 * mag
    if norm < 7:
        return 5 * mag
    return 10 * mag


def _fmt_num(v: float) -> str:
    """軸ラベル整形: 整数なら整数、小数ならざっくり。"""
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f'{v:g}'


# ---------------------------------------------------------------------------
# Bar Chart
# ---------------------------------------------------------------------------

def bar_chart(data: list[dict], *, width: int = 360, height: int = 260,
              x_label: str = '', y_label: str = '', with_gap: bool = True) -> str:
    """棒グラフ SVG (gaps between bars)。

    data: [{"label": str, "value": number, "color"?: str}, ...]
    """
    if not data:
        return ''
    m_left, m_right, m_top, m_bot = 40, 12, 18, 50
    plot_w = width - m_left - m_right
    plot_h = height - m_top - m_bot

    max_v = max(float(d['value']) for d in data)
    # y軸目盛り
    if max_v <= 0:
        max_v = 1
    step = _nice_step(max_v)
    y_max = math.ceil(max_v / step) * step

    # 軸
    parts = []
    parts.append(f'<line x1="{m_left}" y1="{m_top}" x2="{m_left}" y2="{m_top + plot_h}" '
                 'stroke="#334155" stroke-width="1"/>')
    parts.append(f'<line x1="{m_left}" y1="{m_top + plot_h}" x2="{m_left + plot_w}" y2="{m_top + plot_h}" '
                 'stroke="#334155" stroke-width="1"/>')

    # y軸ラベル + gridline
    y = 0
    while y <= y_max + 1e-9:
        yp = m_top + plot_h - (y / y_max) * plot_h
        parts.append(f'<line x1="{m_left}" y1="{yp:.1f}" x2="{m_left + plot_w}" y2="{yp:.1f}" '
                     'stroke="#e2e8f0" stroke-width="0.5"/>')
        parts.append(f'<text x="{m_left - 6}" y="{yp + 4:.1f}" text-anchor="end" '
                     f'font-size="10" fill="#64748b">{_fmt_num(y)}</text>')
        y += step

    # Bars
    n = len(data)
    gap_ratio = 0.25 if with_gap else 0
    cell_w = plot_w / n
    bar_w = cell_w * (1 - gap_ratio)
    for i, d in enumerate(data):
        v = float(d['value'])
        bar_h = (v / y_max) * plot_h
        bx = m_left + i * cell_w + (cell_w - bar_w) / 2
        by = m_top + plot_h - bar_h
        color = d.get('color') or PALETTE[i % len(PALETTE)]
        parts.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" '
                     f'fill="{color}" rx="2"/>')
        # value on top
        parts.append(f'<text x="{bx + bar_w/2:.1f}" y="{by - 4:.1f}" text-anchor="middle" '
                     f'font-size="10" fill="#1e293b" font-weight="700">{_fmt_num(v)}</text>')
        # category label
        parts.append(f'<text x="{bx + bar_w/2:.1f}" y="{m_top + plot_h + 16}" text-anchor="middle" '
                     f'font-size="11" fill="#334155">{d["label"]}</text>')

    # Axis labels
    if x_label:
        parts.append(f'<text x="{m_left + plot_w/2}" y="{height - 6}" text-anchor="middle" '
                     f'font-size="11" fill="#475569" font-weight="600">{x_label}</text>')
    if y_label:
        parts.append(f'<text transform="translate(10,{m_top + plot_h/2}) rotate(-90)" '
                     f'text-anchor="middle" font-size="11" fill="#475569" font-weight="600">{y_label}</text>')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'style="max-width:100%; height:auto;">{"".join(parts)}</svg>')


# ---------------------------------------------------------------------------
# Line Chart (including time series)
# ---------------------------------------------------------------------------

def line_chart(points: list[tuple], *, width: int = 400, height: int = 280,
               x_label: str = '', y_label: str = '', title: str = '',
               mark_points: bool = True) -> str:
    """折れ線グラフ SVG。

    points: [(x_num_or_label, y_num), ...]
    x は数値または文字列 (時系列ラベル) のどちらも可。
    """
    if not points:
        return ''
    m_left, m_right, m_top, m_bot = 44, 14, 30 if title else 18, 52

    # x 軸が文字列(カテゴリ)か数値かを判定
    xs_raw = [p[0] for p in points]
    ys = [float(p[1]) for p in points]
    x_is_numeric = all(isinstance(x, (int, float)) for x in xs_raw)
    xs = [float(x) for x in xs_raw] if x_is_numeric else list(range(len(xs_raw)))

    plot_w = width - m_left - m_right
    plot_h = height - m_top - m_bot

    x_min, x_max = min(xs), max(xs)
    if x_max == x_min:
        x_max = x_min + 1
    y_min = min(0, min(ys))
    y_max = max(ys)
    y_range = y_max - y_min or 1
    y_step = _nice_step(y_range)
    y_top = math.ceil(y_max / y_step) * y_step
    y_bot = math.floor(y_min / y_step) * y_step
    y_range2 = y_top - y_bot or 1

    def sx(x): return m_left + (x - x_min) / (x_max - x_min) * plot_w
    def sy(y): return m_top + plot_h - (y - y_bot) / y_range2 * plot_h

    parts = []

    # title
    if title:
        parts.append(f'<text x="{width/2}" y="18" text-anchor="middle" '
                     f'font-size="13" fill="#1e293b" font-weight="700">{title}</text>')

    # gridlines + y labels
    yv = y_bot
    while yv <= y_top + 1e-9:
        py = sy(yv)
        parts.append(f'<line x1="{m_left}" y1="{py:.1f}" x2="{m_left + plot_w}" y2="{py:.1f}" '
                     'stroke="#e2e8f0" stroke-width="0.5"/>')
        parts.append(f'<text x="{m_left - 6}" y="{py + 4:.1f}" text-anchor="end" '
                     f'font-size="10" fill="#64748b">{_fmt_num(yv)}</text>')
        yv += y_step

    # x axis + y axis
    parts.append(f'<line x1="{m_left}" y1="{m_top + plot_h}" x2="{m_left + plot_w}" y2="{m_top + plot_h}" '
                 'stroke="#334155" stroke-width="1"/>')
    parts.append(f'<line x1="{m_left}" y1="{m_top}" x2="{m_left}" y2="{m_top + plot_h}" '
                 'stroke="#334155" stroke-width="1"/>')

    # x labels
    for i, xr in enumerate(xs_raw):
        px = sx(xs[i])
        parts.append(f'<text x="{px:.1f}" y="{m_top + plot_h + 16}" text-anchor="middle" '
                     f'font-size="10" fill="#334155">{xr}</text>')

    # line
    path_pts = ' '.join(f'{sx(xs[i]):.1f},{sy(ys[i]):.1f}' for i in range(len(xs)))
    parts.append(f'<polyline points="{path_pts}" fill="none" stroke="#6366f1" stroke-width="2.5" '
                 'stroke-linejoin="round"/>')

    # point markers
    if mark_points:
        for i in range(len(xs)):
            parts.append(f'<circle cx="{sx(xs[i]):.1f}" cy="{sy(ys[i]):.1f}" r="3.5" '
                         'fill="white" stroke="#6366f1" stroke-width="2"/>')

    # Axis labels
    if x_label:
        parts.append(f'<text x="{m_left + plot_w/2}" y="{height - 6}" text-anchor="middle" '
                     f'font-size="11" fill="#475569" font-weight="600">{x_label}</text>')
    if y_label:
        parts.append(f'<text transform="translate(12,{m_top + plot_h/2}) rotate(-90)" '
                     f'text-anchor="middle" font-size="11" fill="#475569" font-weight="600">{y_label}</text>')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'style="max-width:100%; height:auto;">{"".join(parts)}</svg>')


# ---------------------------------------------------------------------------
# Function plot (y = f(x))
# ---------------------------------------------------------------------------

def function_plot(expr: str, *, x_min: float = -5, x_max: float = 5,
                  width: int = 340, height: int = 280,
                  n_samples: int = 200, title: str = '',
                  show_grid: bool = True) -> str:
    """y = f(x) 式 (例: 'x**2 - 2*x - 3') の SVG グラフ。

    安全な ast ベースの評価を使用。x 範囲内でサンプリング、必要なら y 範囲自動。
    """
    from services.math_generator import safe_eval

    # sample points
    pts = []
    for i in range(n_samples + 1):
        x = x_min + (x_max - x_min) * i / n_samples
        try:
            y = float(safe_eval(expr, {'x': x}))
            if math.isfinite(y):
                pts.append((x, y))
        except Exception:
            continue

    if not pts:
        return ''

    ys = [p[1] for p in pts]
    y_min_raw, y_max_raw = min(ys), max(ys)
    # 少し余白
    pad = max(abs(y_max_raw), abs(y_min_raw), 1) * 0.1
    y_min, y_max = y_min_raw - pad, y_max_raw + pad

    m_left, m_right, m_top, m_bot = 36, 12, 30 if title else 12, 32
    plot_w = width - m_left - m_right
    plot_h = height - m_top - m_bot

    def sx(x): return m_left + (x - x_min) / (x_max - x_min) * plot_w
    def sy(y): return m_top + plot_h - (y - y_min) / (y_max - y_min) * plot_h

    parts = []
    if title:
        parts.append(f'<text x="{width/2}" y="18" text-anchor="middle" '
                     f'font-size="13" fill="#1e293b" font-weight="700">{title}</text>')

    # grid
    if show_grid:
        x_step = _nice_step(x_max - x_min)
        y_step = _nice_step(y_max - y_min)
        xv = math.floor(x_min / x_step) * x_step
        while xv <= x_max + 1e-9:
            if x_min <= xv <= x_max:
                px = sx(xv)
                parts.append(f'<line x1="{px:.1f}" y1="{m_top}" x2="{px:.1f}" y2="{m_top + plot_h}" '
                             'stroke="#e2e8f0" stroke-width="0.5"/>')
                if xv != 0:
                    parts.append(f'<text x="{px:.1f}" y="{m_top + plot_h + 14}" text-anchor="middle" '
                                 f'font-size="10" fill="#64748b">{_fmt_num(xv)}</text>')
            xv += x_step
        yv = math.floor(y_min / y_step) * y_step
        while yv <= y_max + 1e-9:
            if y_min <= yv <= y_max:
                py = sy(yv)
                parts.append(f'<line x1="{m_left}" y1="{py:.1f}" x2="{m_left + plot_w}" y2="{py:.1f}" '
                             'stroke="#e2e8f0" stroke-width="0.5"/>')
                if yv != 0:
                    parts.append(f'<text x="{m_left - 4}" y="{py + 4:.1f}" text-anchor="end" '
                                 f'font-size="10" fill="#64748b">{_fmt_num(yv)}</text>')
            yv += y_step

    # axes (x=0 と y=0 線)
    if x_min <= 0 <= x_max:
        x0 = sx(0)
        parts.append(f'<line x1="{x0:.1f}" y1="{m_top}" x2="{x0:.1f}" y2="{m_top + plot_h}" '
                     'stroke="#475569" stroke-width="1"/>')
    else:
        parts.append(f'<line x1="{m_left}" y1="{m_top}" x2="{m_left}" y2="{m_top + plot_h}" '
                     'stroke="#475569" stroke-width="1"/>')
    if y_min <= 0 <= y_max:
        y0 = sy(0)
        parts.append(f'<line x1="{m_left}" y1="{y0:.1f}" x2="{m_left + plot_w}" y2="{y0:.1f}" '
                     'stroke="#475569" stroke-width="1"/>')
    else:
        parts.append(f'<line x1="{m_left}" y1="{m_top + plot_h}" x2="{m_left + plot_w}" y2="{m_top + plot_h}" '
                     'stroke="#475569" stroke-width="1"/>')

    # curve
    poly = ' '.join(f'{sx(x):.1f},{sy(y):.1f}' for x, y in pts)
    parts.append(f'<polyline points="{poly}" fill="none" stroke="#ef4444" stroke-width="2.2" '
                 'stroke-linejoin="round"/>')

    # expression label
    parts.append(f'<text x="{m_left + plot_w - 6}" y="{m_top + 14}" text-anchor="end" '
                 f'font-size="11" fill="#991b1b" font-weight="700">y = {expr}</text>')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'style="max-width:100%; height:auto;">{"".join(parts)}</svg>')


if __name__ == '__main__':
    samples = {
        'pie': pie_chart([
            {'label': 'Strawberry', 'value': 5},
            {'label': 'Orange', 'value': 3},
            {'label': 'Purple', 'value': 6},
            {'label': 'Green', 'value': 2},
            {'label': 'Other', 'value': 2},
        ]),
        'bar': bar_chart([
            {'label': 'Apples', 'value': 8},
            {'label': 'Bananas', 'value': 12},
            {'label': 'Oranges', 'value': 5},
            {'label': 'Grapes', 'value': 10},
        ], x_label='Fruit', y_label='Frequency'),
        'line (time series)': line_chart([
            (2012, 26), (2013, 30), (2014, 49),
        ], x_label='Year', y_label='Sales (k)', title='Company sales 2012-2014'),
        'quadratic': function_plot('x**2 - 2*x - 3', x_min=-3, x_max=5, title='y = x² - 2x - 3'),
        'cubic': function_plot('x**3 - 3*x', x_min=-2.5, x_max=2.5, title='y = x³ - 3x'),
    }
    html = '<!DOCTYPE html><html><body>'
    for name, svg in samples.items():
        html += f'<h3>{name}</h3>{svg}<hr/>'
    html += '</body></html>'
    with open('/tmp/sample_charts.html', 'w') as f:
        f.write(html)
    print(f'Saved {len(samples)} chart samples to /tmp/sample_charts.html')
