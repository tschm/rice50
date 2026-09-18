"""Problem 5: two balls loose inside an open spherical bowl.

Every impulse a ball can receive lies in the plane of the two centres, so
the problem is planar: two discs of radius 1/4 whose centres are confined
to the circle of radius 3/4 and which touch each other at distance 1/2.

The 2005 note had the two balls exchange their velocity vectors on impact,
which is the head-on case.  For smooth spheres of equal mass the contact
impulse is along the line of centres, so only the normal component of the
relative velocity reverses.  Both rules conserve energy and momentum,
which is why the error survived every check the note made.
"""
from __future__ import annotations

import mpmath as mp

RADIUS = mp.mpf(1) / 4
TEND = 10


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def norm(a):
    return mp.sqrt(dot(a, a))


def unit(a):
    s = norm(a)
    return (a[0] / s, a[1] / s)


# <<bowl-flight
def flight(dp, dv, target, leaving):
    """Smallest t > 0 with |dp + t dv| = target, or infinity.

    `leaving` says the state is already on this surface, so t = 0 is a
    root of the quadratic.  Dividing it out leaves -b/a exactly and no
    tolerance enters.  After a collision it returns a negative number,
    which correctly reports that the discs are separating.
    """
    a = dot(dv, dv)
    if a == 0:
        return mp.inf
    b = 2 * dot(dp, dv)
    if leaving:
        t = -b / a
        return t if t > 0 else mp.inf
    c = dot(dp, dp) - target ** 2
    disc = b * b - 4 * a * c
    if disc < 0:
        return mp.inf
    root = mp.sqrt(disc)
    ts = [t for t in ((-b - root) / (2 * a), (-b + root) / (2 * a))
          if t > 0]
    return min(ts) if ts else mp.inf
# >>bowl-flight


# <<bowl-collide
def collide(p1, p2, v1, v2):
    """Elastic impact of two smooth unit masses in contact.

    The impulse is a multiple of the line of centres n, and
    conservation of energy fixes the multiple.  The normal part of
    the relative velocity reverses, the tangential part does not.
    """
    n = unit((p1[0] - p2[0], p1[1] - p2[1]))
    s = dot((v1[0] - v2[0], v1[1] - v2[1]), n)
    return ((v1[0] - s * n[0], v1[1] - s * n[1]),
            (v2[0] + s * n[0], v2[1] + s * n[1]))
# >>bowl-collide


def swap(p1, p2, v1, v2):
    """The rule of the 2005 note, kept to reproduce its number."""
    return v2, v1


# <<bowl-run
def run(dps=40, rule=collide, shift=0, trace=False):
    """Distance between the two centres at t = 10."""
    mp.mp.dps = dps
    wall = 1 - RADIUS                 # a centre touches the bowl here
    touch = 2 * RADIUS                # the centres touch here
    p1 = (mp.mpf(1) / 2 + shift, mp.mpf(1) / 8)
    p2 = (mp.mpf(0), mp.mpf(1) / 2)
    v1, v2 = unit((-p1[0], -p1[1])), unit((-p2[0], -p2[1]))

    path1, path2 = [p1], [p2]
    on, walls, contacts, angle, rem = None, 0, 0, None, mp.mpf(TEND)
    while rem > 0:
        dp = (p1[0] - p2[0], p1[1] - p2[1])
        dv = (v1[0] - v2[0], v1[1] - v2[1])
        dt, kind = min((flight(p1, v1, wall, on == "w1"), "w1"),
                       (flight(p2, v2, wall, on == "w2"), "w2"),
                       (flight(dp, dv, touch, on == "c"), "c"))
        if dt >= rem:
            dt, kind = rem, "stop"
        p1 = (p1[0] + dt * v1[0], p1[1] + dt * v1[1])
        p2 = (p2[0] + dt * v2[0], p2[1] + dt * v2[1])
        rem -= dt
        if trace:
            path1.append(p1)
            path2.append(p2)
        if kind == "stop":
            break
        if kind == "w1":
            v1, walls = reflect(p1, v1), walls + 1
        elif kind == "w2":
            v2, walls = reflect(p2, v2), walls + 1
        else:
            if angle is None:
                angle = impact_angle(p1, p2, v1, v2)
            v1, v2 = rule(p1, p2, v1, v2)
            contacts += 1
        on = kind
    return dict(distance=norm((p1[0] - p2[0], p1[1] - p2[1])),
                walls=walls, contacts=contacts, angle=angle,
                energy=(dot(v1, v1) + dot(v2, v2)) / 2,
                path1=path1, path2=path2)
# >>bowl-run


def reflect(p, v):
    """Specular reflection off the bowl, whose normal at p is radial."""
    n = unit(p)
    s = 2 * dot(v, n)
    return (v[0] - s * n[0], v[1] - s * n[1])


def impact_angle(p1, p2, v1, v2):
    """Angle between the relative velocity and the line of centres."""
    n = unit((p1[0] - p2[0], p1[1] - p2[1]))
    w = (v1[0] - v2[0], v1[1] - v2[1])
    return mp.acos(abs(dot(w, n)) / norm(w)) * 180 / mp.pi


def refinement():
    return [(dps, run(dps)["distance"]) for dps in (25, 40, 60)]


def conditioning(dps=60):
    base = run(dps)["distance"]
    rows = []
    for k in (30, 25, 20, 15):
        delta = mp.mpf(10) ** -k
        moved = run(dps, shift=delta)["distance"]
        rows.append((k, abs(moved - base), abs(moved - base) / delta))
    return rows


def results():
    reference = run(60, trace=True)
    return dict(refinement=refinement(), conditioning=conditioning(),
                old=run(40, rule=swap)["distance"], **reference)


if __name__ == "__main__":
    r = results()
    mp.mp.dps = 30
    for dps, value in r["refinement"]:
        print(f"  {dps:3d} digits   {mp.nstr(value, 22)}")
    print(f"{r['walls']} rebounds, {r['contacts']} contacts, "
          f"energy {mp.nstr(r['energy'], 10)}")
    print(f"first contact {mp.nstr(r['angle'], 6)} degrees from head-on")
    print(f"the 2005 rule gives {mp.nstr(r['old'], 22)}")
