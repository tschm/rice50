# /// script
# requires-python = ">=3.11"
# dependencies = ["mpmath", "numpy", "scipy", "sympy", "matplotlib"]
# ///
"""Reproduce every number, table, figure and listing in the corrected note.

    uv run code/paper.py

Writes figs/*.pdf, tables/*.tex and snippets/*.tex.  The paper \\input{}s all
three, so no number and no line of code in it is typed by hand.
"""
from __future__ import annotations

import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mpmath as mp
import numpy as np

import fishbowl
import integral
import knights
import photon
import planets
import polynomial
import snippets

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIGSIZE = (4.2, 4.2)


def sig(x, n):
    """x to n significant digits, as the paper prints it."""
    mp.mp.dps = max(n + 10, 30)
    return mp.nstr(mp.mpf(x) if not isinstance(x, mp.mpc) else x, n,
                   strip_zeros=False)


def power_of_ten(x):
    """A tolerance as LaTeX, as a power of ten where it is one."""
    e = np.log10(x)
    if abs(e - round(e)) < 1e-9:
        return f"$10^{{{int(round(e))}}}$"
    mantissa, exponent = f"{x:.0e}".split("e")
    return f"${mantissa}\\cdot 10^{{{int(exponent)}}}$"


def figure(name):
    fig, ax = plt.subplots(figsize=FIGSIZE)
    return fig, ax, ROOT / "figs" / f"{name}.pdf"


def save(fig, path):
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    print(f"  {path.relative_to(ROOT)}")


def bare(ax):
    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_visible(False)


# ---------------------------------------------------------------- figures

def board_figure():
    fig, ax, path = figure("board")
    for r in range(8):
        for c in range(8):
            if (r + c) % 2 == 0:
                ax.add_patch(plt.Rectangle((c, r), 1, 1, color="0.88"))
    for (r, c) in ((0, 0), (7, 7)):
        ax.text(c + 0.5, r + 0.5, "N", ha="center", va="center",
                fontsize=15, fontweight="bold")
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 8)
    ax.set_aspect("equal")
    ax.set_xticks(np.arange(8) + 0.5)
    ax.set_yticks(np.arange(8) + 0.5)
    ax.set_xticklabels("abcdefgh", fontsize=8)
    ax.set_yticklabels(range(1, 9), fontsize=8)
    ax.tick_params(length=0)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    save(fig, path)


def spy_figure(A):
    fig, ax, path = figure("spy")
    ax.spy(A, markersize=0.06, color="0.25")
    ax.set_xticks([0, 2048, 4096])
    ax.set_yticks([0, 2048, 4096])
    ax.tick_params(labelsize=8)
    save(fig, path)


def mirrors_figure(path_points):
    fig, ax, path = figure("mirrors")
    t = np.linspace(0, 2 * np.pi, 400)
    for a, b, style in ((1, 2, "-"), (4, 3, "-")):
        ax.plot(a * np.cos(t), b * np.sin(t), style, color="0.35", lw=0.9)
    xs = [float(p[0]) for p in path_points]
    ys = [float(p[1]) for p in path_points]
    ax.plot(xs, ys, lw=0.6, color="C0")
    ax.plot(xs[0], ys[0], "o", ms=3, color="C1")
    ax.set_aspect("equal")
    ax.set_xticks([-4, 0, 4])
    ax.set_yticks([-3, 0, 3])
    bare(ax)
    save(fig, path)


def spectrum_figure(eigenvalues):
    fig, ax, path = figure("spectrum")
    t = np.linspace(0, 2 * np.pi, 400)
    for radius, style in ((1.0, "-"), (float(polynomial.CIRCLE), "--")):
        ax.plot(radius * np.cos(t), radius * np.sin(t), style,
                color="0.5", lw=0.8)
    ax.plot(eigenvalues.real, eigenvalues.imag, ".", ms=2, color="C0")
    nearest = min(eigenvalues, key=abs)
    ax.plot(nearest.real, nearest.imag, "o", ms=5, mfc="none", color="C1")
    ax.set_aspect("equal")
    ax.set_xticks([-1, 0, 1])
    ax.set_yticks([-1, 0, 1])
    bare(ax)
    save(fig, path)


def orbits_figure():
    fig, ax, path = figure("orbits")
    u0 = np.array(planets.POSITIONS, dtype=complex)
    y0 = np.concatenate([u0.real, u0.imag,
                         np.real(planets.VELOCITIES),
                         np.imag(planets.VELOCITIES)])
    from scipy.integrate import solve_ivp

    def rhs(t, y):
        u = y[:5] + 1j * y[5:10]
        v = y[10:15] + 1j * y[15:]
        a = planets.field(u, v)
        return np.concatenate([v.real, v.imag, a.real, a.imag])

    s = solve_ivp(rhs, [0, planets.TEND], y0, method="DOP853", rtol=1e-12,
                  atol=1e-16, dense_output=True)
    ts = np.linspace(0, planets.TEND, 3000)
    u = s.sol(ts)[:5] + 1j * s.sol(ts)[5:10]
    for i in range(5):
        style = "-" if i else "--"
        ax.plot(u[i].real, u[i].imag, style, lw=0.9,
                color="0.3" if i == 0 else f"C{i - 1}")
        ax.plot(u[i].real[-1], u[i].imag[-1], ".", ms=6,
                color="0.3" if i == 0 else f"C{i - 1}")
    ax.set_aspect("equal")
    bare(ax)
    ax.tick_params(labelsize=8)
    save(fig, path)


def fishbowl_figure(result):
    fig, ax, path = figure("fishbowl")
    wall = float(1 - fishbowl.RADIUS)
    ax.add_patch(plt.Circle((0, 0), wall, fill=False, lw=0.9, color="0.4"))
    for points, style, label in ((result["path1"], "-", "ball 1"),
                                 (result["path2"], "--", "ball 2")):
        ax.plot([float(p[0]) for p in points],
                [float(p[1]) for p in points], style, lw=0.8, label=label)
    ax.set_aspect("equal")
    ax.set_xlim(-0.8, 0.8)
    ax.set_ylim(-0.8, 0.95)
    ax.legend(frameon=False, fontsize=8, ncol=2, loc="upper center")
    ax.set_xticks([-0.75, 0, 0.75])
    ax.set_yticks([-0.75, 0, 0.75])
    bare(ax)
    save(fig, path)


def contour_figure():
    fig, ax, path = figure("contour")
    fig.set_size_inches(4.2, 2.6)
    ax.plot([0, 1, 1, 0, 0], [0.18, 0.18, 1.25, 1.25, 0.18],
            color="0.25", lw=1.0)
    ax.annotate("", xy=(0.55, 0.18), xytext=(0.45, 0.18),
                arrowprops=dict(arrowstyle="->", color="0.25"))
    ax.annotate("", xy=(0.45, 1.25), xytext=(0.55, 1.25),
                arrowprops=dict(arrowstyle="->", color="0.25"))
    ax.text(0.5, 0.08, "$c_1$", ha="center", fontsize=9)
    ax.text(0.5, 1.32, "$c_2$", ha="center", fontsize=9)
    ax.text(-0.06, 0.72, "$A$", ha="center", fontsize=9)
    ax.text(1.06, 0.72, "$C$", ha="center", fontsize=9)
    ax.plot([0, 1], [0, 0], color="0.7", lw=0.8)
    ax.text(1.12, 0.0, r"$\Re z$", fontsize=9, va="center")
    ax.text(0.0, 1.45, r"$\Im z$", fontsize=9, ha="center")
    ax.set_xlim(-0.2, 1.3)
    ax.set_ylim(-0.15, 1.55)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["0", "1"], fontsize=9)
    ax.set_yticks([])
    bare(ax)
    save(fig, path)


# ----------------------------------------------------------------- tables

def rule(rows, header, spec):
    out = [r"\begin{tabular}{" + spec + "}", r"\hline",
           " & ".join(header) + r"\\", r"\hline"]
    out += [" & ".join(r) + r"\\" for r in rows]
    out += [r"\hline", r"\end{tabular}"]
    return "\n".join(out) + "\n"


def write_tables(k, ph, po, pl, fb, it):
    tables = ROOT / "tables"
    tables.mkdir(exist_ok=True)

    (tables / "photon.tex").write_text(rule(
        [[str(dps), f"${sig(value, 20)}$", str(digits)]
         for dps, value, digits in ph["refinement"]],
        ["working digits", "$|p(60)|$", "correct digits"],
        "r@{\\hspace{1.5em}}l@{\\hspace{1.5em}}r"))

    (tables / "planets.tex").write_text(rule(
        [[power_of_ten(rtol), f"${value:.14f}$", f"{nfev}"]
         for rtol, value, nfev in pl["refinement"]],
        ["tolerance", "$|u_4(5)|$", "evaluations"],
        "l@{\\hspace{1.5em}}l@{\\hspace{1.5em}}r"))

    (tables / "answers.tex").write_text(rule(
        [["1", f"${sig(k['answer'], 10)}$"],
         ["2", f"${sig(ph['distance'], 10)}$"],
         ["3", f"${sig(po['magnitude'], 10)}$"],
         ["4", f"${sig(pl['distance'], 10)}$"],
         ["5", f"${sig(fb['distance'], 10)}$"]],
        ["Problem", "Result"],
        "c@{\\hspace{2em}}l"))

    macros = {
        "knightsanswer": sig(k["answer"], 10),
        "knightslong": sig(k["answer"], 15),
        "knightsnnz": f"{k['nnz']}",
        "knightssecond": sig(k["second"], 10),
        "knightsdecay": f"{k['decay']:.1e}".replace("e-", r"\cdot10^{-") + "}",
        "knightsstationary": sig(k["stationary"], 12),
        "photonanswer": sig(ph["distance"], 10),
        "photonlong": sig(ph["distance"], 27),
        "photonbounces": f"{ph['bounces']}",
        "photonamp": sig(ph["amplification"], 3),
        "polyanswer": sig(po["magnitude"], 10),
        "polylong": sig(po["magnitude"], 22),
        "polyreal": sig(po["root"].real, 16),
        "polyimag": sig(po["root"].imag, 16),
        "polyleading": f"{po['leading']}",
        "polytruncated": f"{po['truncated']}",
        "polytail": sig(po["tail"], 3),
        "polyfloor": sig(po["floor"], 4),
        "polyinside": f"{po['inside']}",
        "planetsanswer": sig(pl["distance"], 10),
        "planetslong": sig(pl["distance"], 22),
        "planetssteps": f"{pl['steps']}",
        "planetsorder": f"{pl['order']}",
        "planetsdrift": sig(pl["drift"], 2),
        "planetsseparation": f"{pl['separation']:.4f}",
        "planetsamp": f"{pl['conditioning'][0][2]:.0f}",
        "bowlanswer": sig(fb["distance"], 10),
        "bowllong": sig(fb["distance"], 22),
        "bowlold": sig(fb["old"], 10),
        "bowloldlong": sig(fb["old"], 22),
        "bowlwalls": f"{fb['walls']}",
        "bowlcontacts": f"{fb['contacts']}",
        "bowlangle": sig(fb["angle"], 3),
        "bowlamp": f"{float(fb['conditioning'][0][2]):.0f}",
        "integralvalue": sig(it["value"], 21),
        "integralshort": sig(it["value"], 10),
        "integralnaive": sig(it["naive"][-1][1], 6),
        "integralgrid": f"{it['naive'][-1][0]}",
    }
    (tables / "numbers.tex").write_text(
        "\n".join(rf"\newcommand{{\{k}}}{{{v}}}" for k, v in macros.items())
        + "\n")
    print(f"  tables/ ({len(macros)} macros)")


# ------------------------------------------------------------------ main

def main() -> None:
    started = time.time()
    print("Problem 1, the knights")
    k = knights.results()
    print(f"  {sig(k['answer'], 12)}")
    print("Problem 2, the photon")
    ph = photon.results()
    print(f"  {sig(ph['distance'], 12)}")
    print("Problem 3, the polynomial")
    po = polynomial.results()
    print(f"  {sig(po['magnitude'], 12)}")
    print("Problem 4, the five bodies")
    pl = planets.results()
    print(f"  {sig(pl['distance'], 12)}  "
          f"({pl['steps']} Taylor steps at order {pl['order']})")
    print("Problem 5, the fishbowl")
    fb = fishbowl.results()
    print(f"  {sig(fb['distance'], 12)}  "
          f"(the 2005 rule gives {sig(fb['old'], 10)})")
    print("Appendix, the integral")
    it = integral.results()
    print(f"  {sig(it['value'], 12)}")

    print("figures")
    board_figure()
    spy_figure(knights.transition())
    mirrors_figure(ph["path"])
    spectrum_figure(po["eigenvalues"])
    orbits_figure()
    fishbowl_figure(fb)
    contour_figure()

    print("tables")
    write_tables(k, ph, po, pl, fb, it)
    print(f"snippets\n  {snippets.write()} listings")
    print(f"done in {time.time() - started:.0f} s")


if __name__ == "__main__":
    main()
