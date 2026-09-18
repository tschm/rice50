"""Problem 4: five point masses in the plane, and where p4 is at t = 5.

Positions are complex numbers, so the phase space is C^10 and Newton's law
reads a_i = sum_j m_j (u_j - u_i)/|u_j - u_i|^3.

The note answered "how do I know ten digits are right?" by perturbing the
initial data and watching the spread.  That measures the conditioning of
the problem; the error of the integration is common to all those runs,
since they share a solver and a tolerance, and so cannot appear in their
spread.  Both experiments are run here, separately.
"""
from __future__ import annotations

import mpmath as mp
import numpy as np
from scipy.integrate import solve_ivp

import taylor

MASSES = (10.0, 1.0, 1.0, 1.0, 1.0)
POSITIONS = (0, 1j, 2, -3j, -4)
VELOCITIES = (0, 1, -1j, -1, 1j)      # clockwise, unit speed, radial normal
TEND = 5
WATCHED = 4                            # the mass whose distance is asked for


# <<planets-field
def field(u, v, masses=MASSES):
    """The acceleration of each mass, positions as complex numbers."""
    a = np.zeros(len(u), dtype=complex)
    for i in range(len(u)):
        for j in range(len(u)):
            if i != j:
                d = u[j] - u[i]
                a[i] += masses[j] * d / abs(d) ** 3
    return a
# >>planets-field


# <<planets-integrate
def integrate(rtol, shift=0.0, method="DOP853"):
    """|u_4(5)|, from a start optionally displaced by shift."""
    u0 = np.array(POSITIONS, dtype=complex)
    u0[WATCHED] += shift
    y0 = np.concatenate([u0.real, u0.imag,
                         np.real(VELOCITIES), np.imag(VELOCITIES)])

    def rhs(t, y):
        u = y[:5] + 1j * y[5:10]
        v = y[10:15] + 1j * y[15:]
        a = field(u, v)
        return np.concatenate([v.real, v.imag, a.real, a.imag])

    s = solve_ivp(rhs, [0, TEND], y0, method=method,
                  rtol=rtol, atol=1e-17)
    y = s.y[:, -1]
    return abs(complex(y[WATCHED], y[5 + WATCHED])), s.nfev
# >>planets-integrate


# <<planets-reference
def reference(order=40, dps=30, tol=24):
    """|u_4(5)| from the Taylor integrator, outside floating point."""
    masses = [mp.mpf(m) for m in MASSES]
    state = ([mp.re(z) for z in POSITIONS],
             [mp.im(z) for z in POSITIONS],
             [mp.re(z) for z in VELOCITIES],
             [mp.im(z) for z in VELOCITIES])
    before = taylor.energy(*state, masses)
    x, y, vx, vy, steps = taylor.integrate(
        state, masses, mp.mpf(TEND), order=order, dps=dps,
        tol=mp.mpf(10) ** -tol)
    after = taylor.energy(x, y, vx, vy, masses)
    return dict(distance=mp.sqrt(x[WATCHED] ** 2 + y[WATCHED] ** 2),
                steps=steps, drift=abs(after - before), order=order)
# >>planets-reference


def refinement():
    """The experiment the note should have run: vary the tolerance."""
    return [(rtol,) + integrate(rtol)
            for rtol in (1e-10, 1e-11, 1e-12, 1e-13, 3e-14)]


def conditioning(rtol=1e-13):
    """The experiment the note did run: vary the data."""
    base, _ = integrate(rtol)
    rows = []
    for k in (12, 10, 8):
        delta = 10.0 ** -k
        moved, _ = integrate(rtol, shift=delta)
        rows.append((k, abs(moved - base), abs(moved - base) / delta))
    return rows


def separation(rtol=1e-13):
    """Closest approach of any pair, which sets the cost of the flight."""
    u0 = np.array(POSITIONS, dtype=complex)
    y0 = np.concatenate([u0.real, u0.imag,
                         np.real(VELOCITIES), np.imag(VELOCITIES)])

    def rhs(t, y):
        u = y[:5] + 1j * y[5:10]
        v = y[10:15] + 1j * y[15:]
        a = field(u, v)
        return np.concatenate([v.real, v.imag, a.real, a.imag])

    s = solve_ivp(rhs, [0, TEND], y0, method="DOP853", rtol=rtol,
                  atol=1e-17, dense_output=True)
    ts = np.linspace(0, TEND, 5001)
    u = s.sol(ts)[:5] + 1j * s.sol(ts)[5:10]
    return min(np.abs(u[i] - u[j]).min()
               for i in range(5) for j in range(i + 1, 5))


def results():
    ref = reference()
    return dict(refinement=refinement(), conditioning=conditioning(),
                separation=separation(), **ref)


if __name__ == "__main__":
    r = results()
    for rtol, value, nfev in r["refinement"]:
        print(f"  rtol {rtol:.0e}  |u4(5)| = {value:.14f}  nfev {nfev}")
    print(f"Taylor order {r['order']}, {r['steps']} steps, "
          f"energy drift {mp.nstr(r['drift'], 3)}")
    print(f"  {mp.nstr(r['distance'], 22)}")
    for k, moved, amp in r["conditioning"]:
        print(f"  shift 1e-{k:<3d} -> {moved:.3e}  amplification {amp:.1f}")
    print(f"closest approach {r['separation']:.4f}")
