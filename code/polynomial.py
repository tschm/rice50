"""Problem 3: the root nearest the origin of sum_{k=0}^{10000} p_{k+1} x^k.

The note truncates the series at degree 300 and reads the smallest
eigenvalue of the companion matrix.  The bound it gives controls
|p - p_M| and says nothing about where the roots go; Rouche's theorem on
|x| = 0.82 closes that gap, and the root is then polished on the full
polynomial.
"""
from __future__ import annotations

import mpmath as mp
import numpy as np
import sympy

DEGREE = 10000
TRUNCATION = 300
CIRCLE = mp.mpf("0.82")

PRIMES = list(sympy.primerange(2, 110000))[:DEGREE + 1]


# <<poly-companion
def companion(coefficients):
    """Companion matrix of the monic multiple of the polynomial.

    coefficients[k] multiplies x^k, so the leading one is last.
    """
    a = np.array(coefficients, dtype=float)
    a = -a[:-1] / a[-1]
    n = len(a)
    A = np.zeros((n, n))
    A[0] = a[::-1]
    A[1:, :-1] = np.eye(n - 1)
    return A
# >>poly-companion


# <<poly-tail
def tail_bound(M=TRUNCATION, radius=CIRCLE):
    """A bound for |p - p_M| on |x| = radius.

    The coefficients increase, so every one of the omitted terms is at
    most a_10000 radius^(M+1).
    """
    mp.mp.dps = 40
    terms = DEGREE - M
    return terms * PRIMES[DEGREE] * radius ** (M + 1)
# >>poly-tail


# <<poly-rouche
def minimum_modulus(M=TRUNCATION, radius=CIRCLE, samples=4096):
    """min |p_M| on the circle of the given radius.

    Sampled, then polished by a local search: the modulus of a
    polynomial has no flat minima on a circle, so a fine sample finds
    every basin.
    """
    mp.mp.dps = 40
    coefficients = [mp.mpf(q) for q in PRIMES[:M + 1]][::-1]
    def modulus(theta):
        z = radius * mp.expjpi(2 * theta)
        return abs(mp.polyval(coefficients, z))
    grid = [(modulus(mp.mpf(j) / samples), mp.mpf(j) / samples)
            for j in range(samples)]
    value, theta = min(grid)
    step = mp.mpf(1) / samples
    for _ in range(60):
        step /= 2
        for candidate in (theta - step, theta + step):
            trial = modulus(candidate)
            if trial < value:
                value, theta = trial, candidate
    return value
# >>poly-rouche


# <<poly-polish
def polish(seed, dps=50):
    """Newton on the full degree-10000 polynomial, from a seed."""
    mp.mp.dps = dps
    a = [mp.mpf(q) for q in PRIMES][::-1]
    d = [a[i] * (DEGREE - i) for i in range(DEGREE)]
    return mp.findroot(lambda x: mp.polyval(a, x) / mp.polyval(d, x),
                       mp.mpc(seed), tol=mp.mpf(10) ** -40)
# >>poly-polish


def results():
    eigenvalues = np.linalg.eigvals(companion(PRIMES[:TRUNCATION + 1]))
    seed = min(eigenvalues, key=abs)
    inside = int(np.sum(np.abs(eigenvalues) < float(CIRCLE)))
    root = polish(seed)
    mp.mp.dps = 40
    return dict(eigenvalues=eigenvalues, seed=seed, inside=inside,
                tail=tail_bound(), floor=minimum_modulus(),
                root=root, magnitude=abs(root),
                leading=PRIMES[DEGREE], truncated=PRIMES[TRUNCATION])


if __name__ == "__main__":
    r = results()
    mp.mp.dps = 30
    print(f"a_10000 = {r['leading']}, a_300 = {r['truncated']}")
    print(f"companion eigenvalue nearest 0: {r['seed']:.12f}")
    print(f"roots of p_300 inside |x| < 0.82: {r['inside']}")
    print(f"|p - p_300| <= {mp.nstr(r['tail'], 4)} on the circle")
    print(f"min |p_300|  =  {mp.nstr(r['floor'], 6)} on the circle")
    print(f"polished root {mp.nstr(r['root'], 22)}")
    print(f"magnitude     {mp.nstr(r['magnitude'], 22)}")
