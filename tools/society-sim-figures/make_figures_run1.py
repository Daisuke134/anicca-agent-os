#!/usr/bin/env python3
"""Regenerate the 4 figure SVGs for the Society Simulation run 1 blog post.

Stdlib only. Every number drawn comes from the frozen results file
anicca-ops tools/society-sim/run1_results.json at run time -- no hand-typed
values. Written 2026-11-25 to repair the incident where the 4 figures were
committed to anicca-products as 0-byte files and served empty (HTTP 200,
Content-Length: 0) while a status-only check reported them verified.

Usage:
  make_figures_run1.py RESULTS_JSON OUT_DIR
"""
import json
import math
import random
import sys

INK = "#16283f"
MUTED = "#5b6b7f"
GRID = "#dde3ea"
STRAT_COLORS = {"random": "#7a8ba0", "clustered": "#0e7c7b", "hub": "#e07a3f"}
STRATS = ["random", "clustered", "hub"]
NET_ORDER = ["lattice_ws_k6_p0", "smallworld_ws_k6_p0.1", "random_er", "scalefree_ba_m3"]
NET_SHORT = {
    "lattice_ws_k6_p0": "Lattice",
    "smallworld_ws_k6_p0.1": "Small-world",
    "random_er": "Random ER",
    "scalefree_ba_m3": "Scale-free BA",
}
FONT = "font-family=\"'Segoe UI', 'Helvetica Neue', Arial, sans-serif\""


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=14, fill=INK, anchor="start", weight=None, opacity=None):
    w = f' font-weight="{weight}"' if weight else ""
    o = f' opacity="{opacity}"' if opacity is not None else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" {FONT}{w}{o}>{esc(s)}</text>')


def get_cond(data, network, strategy, model):
    for c in data["conditions"]:
        if c["network"] == network and c["strategy"] == strategy and c["model"] == model:
            return c
    raise KeyError((network, strategy, model))


def clustering_of(data, network):
    for c in data["conditions"]:
        if c["network"] == network:
            return c["clustering"]
    raise KeyError(network)


# ---------------------------------------------------------------- cover
def make_cover(data):
    sw_clu = get_cond(data, "smallworld_ws_k6_p0.1", "clustered", "complex")["final_adoption_mean"]
    sw_rnd = get_cond(data, "smallworld_ws_k6_p0.1", "random", "complex")["final_adoption_mean"]
    lat_clu_13 = [p for p in data["tipping_sweep"]
                  if p["network"] == "lattice_ws_k6_p0" and p["strategy"] == "clustered"
                  and abs(p["seed_fraction"] - 0.13) < 1e-9][0]["final_adoption_mean"]
    # decorative small-world ring, deterministic
    rng = random.Random(20261125)
    n, cx, cy, r = 42, 985, 300, 185
    pts = [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    edges = set()
    for i in range(n):
        for d in (1, 2):
            edges.add((i, (i + d) % n))
    for _ in range(9):
        a, b = rng.randrange(n), rng.randrange(n)
        if a != b:
            edges.add((min(a, b), max(a, b)))
    seeds = set(range(18, 23))  # one clustered block, decorative
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">',
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#0d1b2e"/><stop offset="1" stop-color="#173656"/></linearGradient></defs>',
        '<rect width="1200" height="630" fill="url(#bg)"/>',
    ]
    for a, b in edges:
        parts.append(f'<line x1="{pts[a][0]:.0f}" y1="{pts[a][1]:.0f}" x2="{pts[b][0]:.0f}" y2="{pts[b][1]:.0f}" stroke="#33507a" stroke-width="1" opacity="0.7"/>')
    for i, (x, y) in enumerate(pts):
        if i in seeds:
            parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="7" fill="#e07a3f"/>')
        else:
            parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="4" fill="#7f9bb8"/>')
    parts.append(text(70, 108, "ANICCA RESEARCH — SOCIETY SIMULATION RUN 1", 19, "#8fb0d1", weight="600"))
    parts.append(text(70, 208, "Placement Beats Volume", 64, "#ffffff", weight="700"))
    parts.append(text(70, 268, "How a behavior-change app tips a society", 30, "#c7d8ea"))
    parts.append(text(70, 318, "1,000 agents · 4 networks · 3 contagion models · 3 seeding strategies", 19, "#8fb0d1"))
    stats = [
        (f"{sw_clu:.2f}", "adoption from 1% of seeds placed inside one community (small-world, complex contagion)"),
        (f"{sw_rnd:.2f}", "adoption from the same 1% scattered at random"),
        (f"{lat_clu_13:.2f}", "adoption from 13% of seeds clustered on a lattice with no shortcuts"),
    ]
    x = 70
    for val, lab in stats:
        parts.append(f'<rect x="{x}" y="392" width="330" height="168" rx="12" fill="#122a47" stroke="#33507a"/>')
        parts.append(text(x + 24, 462, val, 52, "#ffffff", weight="700"))
        # wrap label to <= 34 chars/line
        words, lines, cur = lab.split(), [], ""
        for wd in words:
            if len(cur) + len(wd) + 1 > 36:
                lines.append(cur); cur = wd
            else:
                cur = (cur + " " + wd).strip()
        if cur:
            lines.append(cur)
        for j, ln in enumerate(lines[:3]):
            parts.append(text(x + 24, 496 + 20 * j, ln, 14.5, "#a9c2da"))
        x += 352
    parts.append("</svg>")
    return "\n".join(parts)


# ---------------------------------------------------------------- diagram
def ring_graph(n=48, seed=20261125):
    rng = random.Random(seed)
    edges = set()
    for i in range(n):
        for d in (1, 2):
            a, b = i, (i + d) % n
            edges.add((min(a, b), max(a, b)))
    for _ in range(7):
        a, b = rng.randrange(n), rng.randrange(n)
        if a != b:
            edges.add((min(a, b), max(a, b)))
    deg = [0] * n
    for a, b in edges:
        deg[a] += 1; deg[b] += 1
    return edges, deg


def make_diagram(data):
    n = 48
    edges, deg = ring_graph(n)
    rng = random.Random(7)
    seed_sets = {
        "random": sorted(rng.sample(range(n), 5)),
        "clustered": list(range(10, 15)),
        "hub": sorted(sorted(range(n), key=lambda i: (-deg[i], i))[:5]),
    }
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="360" viewBox="0 0 960 360">',
             '<rect width="960" height="360" fill="#ffffff"/>']
    parts.append(text(480, 34, "Three placements of the same seed budget", 20, INK, anchor="middle", weight="700"))
    for pi, strat in enumerate(STRATS):
        cx, cy, r = 165 + pi * 315, 168, 108
        pts = [(cx + r * math.cos(2 * math.pi * i / n - math.pi / 2),
                cy + r * math.sin(2 * math.pi * i / n - math.pi / 2)) for i in range(n)]
        for a, b in edges:
            parts.append(f'<line x1="{pts[a][0]:.0f}" y1="{pts[a][1]:.0f}" x2="{pts[b][0]:.0f}" y2="{pts[b][1]:.0f}" stroke="#d5dce4" stroke-width="1"/>')
        ss = set(seed_sets[strat])
        for i, (x, y) in enumerate(pts):
            if i in ss:
                parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="6" fill="#d6495b" stroke="#ffffff" stroke-width="1.5"/>')
            else:
                parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="3.6" fill="#b9c4d0"/>')
        parts.append(text(cx, 312, strat.capitalize(), 17, INK, anchor="middle", weight="600"))
        sub = {"random": "seeds scattered", "clustered": "seeds inside one community",
               "hub": "highest-degree nodes"}[strat]
        parts.append(text(cx, 336, sub, 13, MUTED, anchor="middle"))
    parts.append("</svg>")
    return "\n".join(parts)


# ---------------------------------------------------------------- chart complex
def make_chart_complex(data):
    W, H = 920, 564
    x0, y0, pw, ph = 84, 124, 780, 344
    base = y0 + ph
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
             '<rect width="920" height="564" fill="#ffffff"/>']
    parts.append(text(W / 2, 40, "Complex contagion: final adoption by network and seeding strategy", 19, INK, anchor="middle", weight="700"))
    parts.append(text(W / 2, 66, "Adoption needs at least 2 adopted neighbors · seeds = 1% · N = 1,000 · mean of 10 replications", 13.5, MUTED, anchor="middle"))
    for gv in (0, 0.25, 0.5, 0.75, 1.0):
        y = base - gv * ph
        parts.append(f'<line x1="{x0}" y1="{y:.0f}" x2="{x0 + pw}" y2="{y:.0f}" stroke="{GRID}" stroke-width="1"/>')
        parts.append(text(x0 - 10, y + 5, f"{gv:.2f}", 12.5, MUTED, anchor="end"))
    parts.append(f'<line x1="{x0}" y1="{base}" x2="{x0 + pw}" y2="{base}" stroke="{INK}" stroke-width="1.4"/>')
    group_w = pw / 4
    bar_w = 52
    for gi, net in enumerate(NET_ORDER):
        gx = x0 + gi * group_w
        for si, strat in enumerate(STRATS):
            v = get_cond(data, net, strat, "complex")["final_adoption_mean"]
            bx = gx + 22 + si * (bar_w + 8)
            bh = v * ph
            parts.append(f'<rect x="{bx:.0f}" y="{base - bh:.0f}" width="{bar_w}" height="{bh:.0f}" fill="{STRAT_COLORS[strat]}"/>')
            parts.append(text(bx + bar_w / 2, base - bh - 7, f"{v:.2f}", 12.5, INK, anchor="middle", weight="600"))
        clu = clustering_of(data, net)
        parts.append(text(gx + group_w / 2, base + 26, NET_SHORT[net], 14.5, INK, anchor="middle", weight="600"))
        parts.append(text(gx + group_w / 2, base + 47, f"clustering {clu:.2f}", 12, MUTED, anchor="middle"))
    lx = x0 + pw - 330
    for si, strat in enumerate(STRATS):
        parts.append(f'<rect x="{lx + si * 112}" y="{y0 - 42}" width="14" height="14" fill="{STRAT_COLORS[strat]}"/>')
        parts.append(text(lx + si * 112 + 20, y0 - 30, strat.capitalize(), 13, INK))
    parts.append(text(W / 2, H - 14, "Source: run1_results.json — Anicca society-sim run 1", 12, MUTED, anchor="middle"))
    parts.append("</svg>")
    return "\n".join(parts)


# ---------------------------------------------------------------- chart tipping
def make_chart_tipping(data):
    W, H = 920, 600
    x0, y0, pw, ph = 84, 150, 780, 344
    base = y0 + ph
    sweep = data["tipping_sweep"]
    fracs = sorted(set(p["seed_fraction"] for p in sweep))
    series = {}
    for p in sweep:
        series.setdefault((p["network"], p["strategy"]), []).append(p)
    for k in series:
        series[k].sort(key=lambda p: p["seed_fraction"])
    focus = {("smallworld_ws_k6_p0.1", "random"), ("lattice_ws_k6_p0", "clustered")}
    net_ls = {"lattice_ws_k6_p0": "#0e7c7b", "smallworld_ws_k6_p0.1": "#d6495b",
              "random_er": "#4361a8", "scalefree_ba_m3": "#e07a3f"}
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
             '<rect width="920" height="600" fill="#ffffff"/>']
    parts.append(text(W / 2, 40, "Tipping sweep: final adoption vs seed share (Granovetter threshold model)", 18.5, INK, anchor="middle", weight="700"))
    parts.append(text(W / 2, 66, "N = 1,000 · mean of 10 replications per point · whiskers = ±1 SD", 13.5, MUTED, anchor="middle"))
    for gv in (0, 0.25, 0.5, 0.75, 1.0):
        y = base - gv * ph
        parts.append(f'<line x1="{x0}" y1="{y:.0f}" x2="{x0 + pw}" y2="{y:.0f}" stroke="{GRID}" stroke-width="1"/>')
        parts.append(text(x0 - 10, y + 5, f"{gv:.2f}", 12.5, MUTED, anchor="end"))
    parts.append(f'<line x1="{x0}" y1="{base}" x2="{x0 + pw}" y2="{base}" stroke="{INK}" stroke-width="1.4"/>')

    def X(fr):
        return x0 + fracs.index(fr) * (pw / (len(fracs) - 1))

    for fr in fracs:
        parts.append(text(X(fr), base + 26, f"{fr * 100:g}%", 12.5, MUTED, anchor="middle"))
    parts.append(text(x0 + pw / 2, base + 52, "seed share of population", 13, MUTED, anchor="middle"))
    # non-focus series first (faint), focus last (bold)
    for key in sorted(series, key=lambda k: k in focus):
        pts = series[key]
        col = net_ls[key[0]]
        bold = key in focus
        op = 1.0 if bold else 0.45
        swd = 3 if bold else 1.6
        path = " ".join(f"{'M' if i == 0 else 'L'}{X(p['seed_fraction']):.0f},{base - p['final_adoption_mean'] * ph:.0f}" for i, p in enumerate(pts))
        parts.append(f'<path d="{path}" fill="none" stroke="{col}" stroke-width="{swd}" opacity="{op}"/>')
        for p in pts:
            yy = base - p["final_adoption_mean"] * ph
            sd = p["final_adoption_sd"] * ph
            parts.append(f'<line x1="{X(p["seed_fraction"]):.0f}" y1="{yy - sd:.0f}" x2="{X(p["seed_fraction"]):.0f}" y2="{yy + sd:.0f}" stroke="{col}" stroke-width="1" opacity="{op * 0.6}"/>')
            parts.append(f'<circle cx="{X(p["seed_fraction"]):.0f}" cy="{yy:.0f}" r="{4 if bold else 3}" fill="{col}" opacity="{op}"/>')
    # legend: two columns in the band above the plot (no data there)
    lx, ly = x0 + 8, 96
    keys = sorted(series, key=lambda k: (NET_ORDER.index(k[0]), STRATS.index(k[1])))
    for i, key in enumerate(keys):
        col_x = lx + (i % 2) * 268
        row_y = ly + (i // 2) * 21
        col = net_ls[key[0]]
        bold = key in focus
        parts.append(f'<line x1="{col_x}" y1="{row_y - 4}" x2="{col_x + 22}" y2="{row_y - 4}" stroke="{col}" stroke-width="{3 if bold else 1.6}" opacity="{1.0 if bold else 0.55}"/>')
        parts.append(text(col_x + 28, row_y, f"{NET_SHORT[key[0]]} · {key[1]}", 12, INK, opacity=None if bold else 0.65))
    parts.append(text(W / 2, H - 14, "Source: run1_results.json — Anicca society-sim run 1", 12, MUTED, anchor="middle"))
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    results_path, out_dir = sys.argv[1], sys.argv[2]
    with open(results_path) as f:
        data = json.load(f)
    import os
    os.makedirs(out_dir, exist_ok=True)
    figs = {
        "cover.svg": make_cover(data),
        "diagram-strategies.svg": make_diagram(data),
        "chart-complex.svg": make_chart_complex(data),
        "chart-tipping.svg": make_chart_tipping(data),
    }
    for name, svg in figs.items():
        p = os.path.join(out_dir, name)
        with open(p, "w") as f:
            f.write(svg + "\n")
        print(f"{name}: {len(svg.encode()) + 1} bytes")


if __name__ == "__main__":
    main()
