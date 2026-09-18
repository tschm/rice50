"""The appendix: the integral of sin^2(tan(tan(pi x))) over [0, 1].

The integrand is undefined on a countable set and oscillates without bound
between its poles, so no quadrature rule on the real line has a chance.
Lifting the contour to the line Im z = c makes the analytic factor
exp(2i tan(tan(pi z))) tend to a constant, and Cauchy's theorem says the
integral does not notice the lift.  The checks here confirm the two claims
the argument rests on: the lifted integral is independent of c, and its
value is the constant the c -> infinity limit predicts.
"""
from __future__ import annotations

import mpmath as mp


# <<integral-closed
def closed_form(dps=40):
    """(1 - e^{-2 tanh 1})/2, the value the contour argument gives."""
    mp.mp.dps = dps
    return (1 - mp.e ** (-2 * mp.tanh(1))) / 2
# >>integral-closed


# <<integral-lift
def lifted(c, n, dps=40):
    """The trapezoid rule for the integral of f_c^+ over one period.

    f_c^+(x) = exp(2i tan(tan(pi (x + i c)))) is analytic and has
    period 1 for c > 0, so the trapezoid rule converges
    geometrically and the answer must not depend on c at all.
    """
    mp.mp.dps = dps
    total = mp.mpc(0)
    for j in range(n):
        z = mp.mpf(j) / n + mp.mpc(0, 1) * c
        total += mp.e ** (2j * mp.tan(mp.tan(mp.pi * z)))
    return total / n
# >>integral-lift


def real_axis(n, dps=25):
    """The average of sin^2(tan(tan(pi x))) over an equispaced grid."""
    mp.mp.dps = dps
    total = mp.mpf(0)
    for j in range(1, n):
        x = mp.mpf(j) / n
        total += mp.sin(mp.tan(mp.tan(mp.pi * x))) ** 2
    return total / (n - 1)


def results():
    value = closed_form()
    mp.mp.dps = 40
    lift = [(c, n, (1 - mp.re(lifted(mp.mpf(c), n))) / 2)
            for c in ("1", "0.25", "0.05")
            for n in (64, 256)]
    naive = [(n, real_axis(n)) for n in (10 ** 4, 10 ** 5)]
    return dict(value=value, constant=mp.e ** (-2 * mp.tanh(1)),
                lifted=lift, naive=naive)


if __name__ == "__main__":
    r = results()
    mp.mp.dps = 30
    print(f"closed form   {mp.nstr(r['value'], 30)}")
    for c, n, v in r["lifted"]:
        print(f"  c = {c:>4}, n = {n:4d}   {mp.nstr(v, 30)}")
    for n, v in r["naive"]:
        print(f"  grid average, n = {n:6d}   {mp.nstr(v, 8)}")
