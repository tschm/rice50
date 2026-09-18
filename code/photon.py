"""Problem 2: a photon in the annulus between two elliptic mirrors.

Between reflections the photon travels in a straight line, so every event
time is the smallest positive root of a quadratic and the trajectory is
exact up to rounding.  The 2005 note concluded from a Mathematica
experiment that "a loss of 43 digits is unavoidable"; that was the
worst-case bound significance arithmetic carries, not the conditioning of
the billiard, which is measured here instead.
"""
from __future__ import annotations

import mpmath as mp

# semi-axes (a, b) of the inner mirror 4x^2 + y^2 = 4 and of the
# outer mirror 9x^2 + 16y^2 = 144
MIRRORS = ((1, 2), (4, 3))
START = (2, 0)
DIRECTION = (0, 1)
TEND = 60


# <<photon-hit
def hit(p, v, a, b, leaving):
    """Smallest t > 0 with (px+t vx)^2/a^2 + (py+t vy)^2/b^2 = 1.

    `leaving` says the photon is sitting on this mirror, so t = 0 is a
    root: divide it out rather than filter roots by a threshold.
    """
    qa = v[0] ** 2 / a ** 2 + v[1] ** 2 / b ** 2
    qb = 2 * (p[0] * v[0] / a ** 2 + p[1] * v[1] / b ** 2)
    if leaving:
        t = -qb / qa
        return t if t > 0 else mp.inf
    qc = p[0] ** 2 / a ** 2 + p[1] ** 2 / b ** 2 - 1
    disc = qb * qb - 4 * qa * qc
    if disc < 0:
        return mp.inf
    root = mp.sqrt(disc)
    ts = [t for t in ((-qb - root) / (2 * qa),
                      (-qb + root) / (2 * qa)) if t > 0]
    return min(ts) if ts else mp.inf
# >>photon-hit


# <<photon-reflect
def reflect(p, v, a, b):
    """Specular reflection at p on the ellipse with semi-axes a, b.

    The outward normal of x^2/a^2 + y^2/b^2 = 1 at p is
    (px/a^2, py/b^2); the tangential part of v survives and the
    normal part changes sign.
    """
    n = (p[0] / a ** 2, p[1] / b ** 2)
    scale = mp.sqrt(n[0] ** 2 + n[1] ** 2)
    n = (n[0] / scale, n[1] / scale)
    s = 2 * (v[0] * n[0] + v[1] * n[1])
    return (v[0] - s * n[0], v[1] - s * n[1])
# >>photon-reflect


# <<photon-fly
def fly(dps, shift=0, trace=False):
    """Distance from the origin at t = 60, at dps working digits."""
    mp.mp.dps = dps
    p = (mp.mpf(START[0]) + shift, mp.mpf(START[1]))
    v = (mp.mpf(DIRECTION[0]), mp.mpf(DIRECTION[1]))
    path, on, bounces, rem = [p], None, 0, mp.mpf(TEND)
    while rem > 0:
        dt, k = min((hit(p, v, a, b, on == i), i)
                    for i, (a, b) in enumerate(MIRRORS))
        dt = min(dt, rem)
        p, rem = (p[0] + dt * v[0], p[1] + dt * v[1]), rem - dt
        if trace:
            path.append(p)
        if rem > 0:
            v = reflect(p, v, *MIRRORS[k])
            on, bounces = k, bounces + 1
    return dict(distance=mp.sqrt(p[0] ** 2 + p[1] ** 2),
                bounces=bounces, path=path)
# >>photon-fly


def refinement(reference_dps=140):
    """How many digits survive, as a function of the working precision."""
    mp.mp.dps = reference_dps
    exact = fly(reference_dps)["distance"]
    rows = []
    for dps in (20, 25, 30, 40, 50, 70):
        value = fly(dps)["distance"]
        mp.mp.dps = reference_dps
        err = abs(value - exact)
        digits = reference_dps if err == 0 else int(-mp.log10(err / exact))
        rows.append((dps, value, digits))
    return exact, rows


def conditioning(reference_dps=140):
    """Amplification of a perturbation of the starting point."""
    mp.mp.dps = reference_dps
    exact = fly(reference_dps)["distance"]
    rows = []
    for k in (40, 30, 20, 15):
        delta = mp.mpf(10) ** -k
        mp.mp.dps = reference_dps
        moved = fly(reference_dps, shift=delta)["distance"]
        rows.append((k, abs(moved - exact), abs(moved - exact) / delta))
    return rows


def results():
    exact, rows = refinement()
    amp = conditioning()
    mp.mp.dps = 140
    run = fly(140, trace=True)
    return dict(distance=exact, bounces=run["bounces"], path=run["path"],
                refinement=rows, conditioning=amp,
                amplification=amp[0][2])


if __name__ == "__main__":
    r = results()
    mp.mp.dps = 30
    print(f"{r['bounces']} reflections, "
          f"|p(60)| = {mp.nstr(r['distance'], 27)}")
    for dps, value, digits in r["refinement"]:
        print(f"  {dps:3d} working digits -> {digits:3d} correct")
    print(f"amplification {mp.nstr(r['amplification'], 5)}")
