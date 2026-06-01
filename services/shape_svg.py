"""立体図形 (cuboid / cube / triangular prism) のラベル付き SVG 生成。

chart_svg.py (グラフ系) と対になる「図形系」サービス。
すべて Python 純正・依存なし。oblique projection で PDF に近い見た目。

使い方:
    from services.shape_svg import cuboid_svg, triangular_prism_svg
    svg = cuboid_svg('5 cm', '3 cm', '4 cm', wv=5, hv=3, dv=4)
"""
from __future__ import annotations

import math

STROKE = '#4b3f72'
F_TOP = '#cabfe6'
F_RIGHT = '#b6a7da'
F_FRONT = '#ded7f0'


def _pts(*ps):
    return ' '.join(f'{p[0]:.1f},{p[1]:.1f}' for p in ps)


def cuboid_svg(w_label, h_label, d_label, *, wv, hv, dv,
               face_label=None, vb_w=260, vb_h=210):
    """直方体 (cube は wv=hv=dv で表現) を斜投影で描く。

    wv/hv/dv: 見た目の比率に使う相対値 (幅/高さ/奥行)
    w_label/h_label/d_label: 各辺に表示する文字 (例 '5 cm', '? cm')
    face_label: 前面中央に表示する文字 (例 'V = 84 cm³')
    """
    mx = max(wv, hv, dv) or 1
    k = 92.0 / mx
    fw = max(46, wv * k)
    fh = max(38, hv * k)
    depth = max(26, dv * k * 0.65)
    dx = depth * 0.9
    dy = -depth * 0.55

    x0 = 46.0
    y0 = vb_h - 46.0
    A = (x0, y0)
    B = (x0 + fw, y0)
    C = (x0 + fw, y0 - fh)
    D = (x0, y0 - fh)
    Ap = (A[0] + dx, A[1] + dy)
    Bp = (B[0] + dx, B[1] + dy)
    Cp = (C[0] + dx, C[1] + dy)
    Dp = (D[0] + dx, D[1] + dy)

    parts = [
        # 隠れ辺 (破線): 奥下左の頂点 Ap から伸びる3辺
        f'<polyline points="{_pts(Bp, Ap)}" fill="none" stroke="{STROKE}" stroke-width="1" stroke-dasharray="4 3" opacity="0.55"/>',
        f'<polyline points="{_pts(Dp, Ap)}" fill="none" stroke="{STROKE}" stroke-width="1" stroke-dasharray="4 3" opacity="0.55"/>',
        f'<polyline points="{_pts(A, Ap)}" fill="none" stroke="{STROKE}" stroke-width="1" stroke-dasharray="4 3" opacity="0.55"/>',
        # 面
        f'<polygon points="{_pts(D, C, Cp, Dp)}" fill="{F_TOP}" stroke="{STROKE}" stroke-width="1.6" stroke-linejoin="round"/>',
        f'<polygon points="{_pts(B, C, Cp, Bp)}" fill="{F_RIGHT}" stroke="{STROKE}" stroke-width="1.6" stroke-linejoin="round"/>',
        f'<polygon points="{_pts(A, B, C, D)}" fill="{F_FRONT}" stroke="{STROKE}" stroke-width="1.8" stroke-linejoin="round"/>',
    ]

    parts.append(
        f'<text x="{(A[0]+B[0])/2:.1f}" y="{y0+18:.1f}" text-anchor="middle" '
        f'font-size="14" fill="#1e293b" font-weight="700">{w_label}</text>'
    )
    parts.append(
        f'<text x="{B[0]+9:.1f}" y="{(B[1]+C[1])/2+5:.1f}" text-anchor="start" '
        f'font-size="14" fill="#1e293b" font-weight="700">{h_label}</text>'
    )
    midC = ((C[0]+Cp[0])/2, (C[1]+Cp[1])/2)
    parts.append(
        f'<text x="{midC[0]+11:.1f}" y="{midC[1]-9:.1f}" text-anchor="start" '
        f'font-size="14" fill="#1e293b" font-weight="700">{d_label}</text>'
    )
    if face_label:
        parts.append(
            f'<text x="{(A[0]+C[0])/2:.1f}" y="{(A[1]+C[1])/2+5:.1f}" text-anchor="middle" '
            f'font-size="13" fill="#312e54" font-weight="700">{face_label}</text>'
        )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vb_w} {vb_h}" '
        f'style="max-width:280px; height:auto;">{"".join(parts)}</svg>'
    )


def triangular_prism_svg(base_label, height_label, hyp_label, length_label, *,
                         bv, hv, lv, vb_w=300, vb_h=210):
    """直角三角形を断面にもつ三角柱を斜投影で描く。

    bv/hv/lv: 相対値 (断面の底辺 / 断面の高さ / 角柱の長さ)
    *_label: 各辺の表示文字。直角は断面の左下。
    """
    mx = max(bv, hv) or 1
    k = 80.0 / mx
    base_px = max(54, bv * k)
    height_px = max(46, hv * k)
    depth = max(40, min(95, lv * k * 0.6))
    dx = depth * 0.85
    dy = -depth * 0.5

    x0 = 60.0
    y0 = vb_h - 48.0
    # 前面の直角三角形 (直角は P1)
    P1 = (x0, y0)                      # bottom-left (right angle)
    P2 = (x0 + base_px, y0)            # bottom-right
    P3 = (x0, y0 - height_px)          # top-left
    P1p = (P1[0] + dx, P1[1] + dy)
    P2p = (P2[0] + dx, P2[1] + dy)
    P3p = (P3[0] + dx, P3[1] + dy)

    parts = [
        # 隠れ辺 (破線): 奥の直角頂点 P1p から
        f'<polyline points="{_pts(P1p, P2p)}" fill="none" stroke="{STROKE}" stroke-width="1" stroke-dasharray="4 3" opacity="0.5"/>',
        f'<polyline points="{_pts(P1p, P3p)}" fill="none" stroke="{STROKE}" stroke-width="1" stroke-dasharray="4 3" opacity="0.5"/>',
        f'<polyline points="{_pts(P1, P1p)}" fill="none" stroke="{STROKE}" stroke-width="1" stroke-dasharray="4 3" opacity="0.5"/>',
        # 斜面 (hypotenuse face)
        f'<polygon points="{_pts(P3, P2, P2p, P3p)}" fill="{F_TOP}" stroke="{STROKE}" stroke-width="1.6" stroke-linejoin="round"/>',
        # 左の垂直面
        f'<polygon points="{_pts(P1, P3, P3p, P1p)}" fill="{F_RIGHT}" stroke="{STROKE}" stroke-width="1.6" stroke-linejoin="round"/>',
        # 前面の三角形
        f'<polygon points="{_pts(P1, P2, P3)}" fill="{F_FRONT}" stroke="{STROKE}" stroke-width="1.8" stroke-linejoin="round"/>',
        # 直角マーク
        f'<polyline points="{_pts((P1[0]+9, P1[1]), (P1[0]+9, P1[1]-9), (P1[0], P1[1]-9))}" '
        f'fill="none" stroke="{STROKE}" stroke-width="1"/>',
    ]

    # ラベル
    parts.append(
        f'<text x="{(P1[0]+P2[0])/2:.1f}" y="{y0+18:.1f}" text-anchor="middle" '
        f'font-size="14" fill="#1e293b" font-weight="700">{base_label}</text>'
    )
    parts.append(
        f'<text x="{P1[0]-8:.1f}" y="{(P1[1]+P3[1])/2+5:.1f}" text-anchor="end" '
        f'font-size="14" fill="#1e293b" font-weight="700">{height_label}</text>'
    )
    midHyp = ((P3[0]+P2[0])/2, (P3[1]+P2[1])/2)
    parts.append(
        f'<text x="{midHyp[0]+6:.1f}" y="{midHyp[1]-6:.1f}" text-anchor="start" '
        f'font-size="14" fill="#1e293b" font-weight="700">{hyp_label}</text>'
    )
    midL = ((P2[0]+P2p[0])/2, (P2[1]+P2p[1])/2)
    parts.append(
        f'<text x="{midL[0]+10:.1f}" y="{midL[1]+12:.1f}" text-anchor="start" '
        f'font-size="14" fill="#1e293b" font-weight="700">{length_label}</text>'
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vb_w} {vb_h}" '
        f'style="max-width:300px; height:auto;">{"".join(parts)}</svg>'
    )
