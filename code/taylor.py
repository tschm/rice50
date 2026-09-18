"""A Taylor-series integrator for the gravitational N-body problem.

The right-hand side is built from products and one power, so the Taylor
coefficients of the solution satisfy recurrences that cost no more than the
right-hand side itself.  Carrying order-20 series in 30-digit arithmetic
puts the discretisation error far below anything the answer needs, which is
what lets the note claim ten digits rather than hope for them.

Writing u_ij = u_j - u_i and g_ij = |u_ij|^{-3},

    x_i'' = sum_j m_j dx_ij g_ij ,     g_ij = (r2_ij)^{-3/2} ,

and for a power w = v^alpha the coefficients obey

    n v_0 w_n = sum_{k<n} (alpha (n-k) - k) w_k v_{n-k} ,

which is the only ingredient beyond Cauchy products.
"""
from __future__ import annotations

import mpmath as mp

ALPHA = mp.mpf(-3) / 2


# <<taylor-power
def power_series(v, alpha, order):
    """Coefficients of v^alpha from the coefficients of v."""
    w = [v[0] ** alpha]
    for n in range(1, order + 1):
        acc = mp.mpf(0)
        for k in range(n):
            acc += (alpha * (n - k) - k) * w[k] * v[n - k]
        w.append(acc / (n * v[0]))
    return w
# >>taylor-power


# <<taylor-coefficients
def coefficients(x, y, vx, vy, masses, order):
    """Taylor coefficients of each coordinate about the state."""
    n_bodies = len(masses)
    X = [[xi] for xi in x]
    Y = [[yi] for yi in y]
    VX = [[vi] for vi in vx]
    VY = [[vi] for vi in vy]
    pairs = [(i, j) for i in range(n_bodies)
             for j in range(i + 1, n_bodies)]
    R2 = {p: [] for p in pairs}
    G = {p: [] for p in pairs}

    for n in range(order + 1):
        for (i, j) in pairs:
            dx = [X[j][k] - X[i][k] for k in range(n + 1)]
            dy = [Y[j][k] - Y[i][k] for k in range(n + 1)]
            R2[(i, j)].append(
                sum(dx[k] * dx[n - k] + dy[k] * dy[n - k]
                    for k in range(n + 1)))
            r2 = R2[(i, j)]
            if n == 0:
                G[(i, j)].append(r2[0] ** ALPHA)
            else:
                g = G[(i, j)]
                acc = sum((ALPHA * (n - k) - k) * g[k] * r2[n - k]
                          for k in range(n))
                g.append(acc / (n * r2[0]))
        if n == order:
            break
        ax = [mp.mpf(0)] * n_bodies
        ay = [mp.mpf(0)] * n_bodies
        for (i, j) in pairs:
            g = G[(i, j)]
            dx = [X[j][k] - X[i][k] for k in range(n + 1)]
            dy = [Y[j][k] - Y[i][k] for k in range(n + 1)]
            px = sum(dx[k] * g[n - k] for k in range(n + 1))
            py = sum(dy[k] * g[n - k] for k in range(n + 1))
            ax[i] += masses[j] * px
            ay[i] += masses[j] * py
            ax[j] -= masses[i] * px
            ay[j] -= masses[i] * py
        for i in range(n_bodies):
            X[i].append(VX[i][n] / (n + 1))
            Y[i].append(VY[i][n] / (n + 1))
            VX[i].append(ax[i] / (n + 1))
            VY[i].append(ay[i] / (n + 1))
    return X, Y, VX, VY
# >>taylor-coefficients


def horner(series, h):
    value = series[-1]
    for c in reversed(series[:-1]):
        value = value * h + c
    return value


# <<taylor-step
def step_size(series, order, tol):
    """Jorba-Zou: match the last two terms of each series to tol."""
    h = mp.inf
    for s in series:
        for n in (order - 1, order):
            c = abs(s[n])
            if c > 0:
                h = min(h, (tol / c) ** (mp.mpf(1) / n))
    return h / 2
# >>taylor-step


# <<taylor-integrate
def integrate(state, masses, tend, order=20, dps=30, tol=None):
    """Advance (x, y, vx, vy) to t = tend, returning the state."""
    mp.mp.dps = dps
    tol = tol if tol is not None else mp.mpf(10) ** (-dps + 4)
    x, y, vx, vy = ([mp.mpf(c) for c in part] for part in state)
    t, steps = mp.mpf(0), 0
    while t < tend:
        X, Y, VX, VY = coefficients(x, y, vx, vy, masses, order)
        h = min(step_size(X + Y + VX + VY, order, tol), tend - t)
        x = [horner(s, h) for s in X]
        y = [horner(s, h) for s in Y]
        vx = [horner(s, h) for s in VX]
        vy = [horner(s, h) for s in VY]
        t, steps = t + h, steps + 1
    return x, y, vx, vy, steps
# >>taylor-integrate


def energy(x, y, vx, vy, masses):
    kinetic = sum(m * (a * a + b * b) for m, a, b in zip(masses, vx, vy)) / 2
    potential = mp.mpf(0)
    for i in range(len(masses)):
        for j in range(i + 1, len(masses)):
            d = mp.sqrt((x[i] - x[j]) ** 2 + (y[i] - y[j]) ** 2)
            potential -= masses[i] * masses[j] / d
    return kinetic + potential
