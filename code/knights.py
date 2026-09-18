"""Problem 1: two knights jumping at random on a chessboard.

The state is the ordered pair of occupied squares, so the chain lives on
64^2 = 4096 states of which only the same-colour, distinct ones are reachable.
The answer is the probability that at least one knight stands on a corner
after 2005 turns.
"""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl

CORNERS = (1, 8, 57, 64)
START = (1, 64)
TURNS = 2005


# <<knights-moves
def moves(p):
    """The squares a knight standing on square p can jump to."""
    row, col = divmod(p - 1, 8)
    jumps = ((2, -1), (2, 1), (1, -2), (1, 2),
             (-2, -1), (-2, 1), (-1, -2), (-1, 2))
    return [8 * (row + dr) + (col + dc) + 1
            for dr, dc in jumps
            if 0 <= row + dr < 8 and 0 <= col + dc < 8]
# >>knights-moves


def state(a, b):
    """The state number of the ordered pair of squares (a, b)."""
    return 64 * (a - 1) + b


def colour(p):
    row, col = divmod(p - 1, 8)
    return (row + col) % 2


# <<knights-matrix
def transition():
    """The column-stochastic matrix of the chain on the 4096 states.

    Each player picks uniformly among the squares his knight can
    reach, the square held by the other knight excluded.  If both
    pick the same square nobody moves and the turn is passed, which
    is the diagonal entry.
    """
    A = sp.lil_matrix((64 * 64, 64 * 64))
    for i in range(1, 65):
        for j in range(1, 65):
            if i == j or colour(i) != colour(j):
                continue     # unreachable: they move together
            to_i = [q for q in moves(i) if q != j]
            to_j = [q for q in moves(j) if q != i]
            n = len(to_i) * len(to_j)
            passed = 0
            for a in to_i:
                for b in to_j:
                    if a == b:
                        passed += 1
                    else:
                        A[state(a, b) - 1, state(i, j) - 1] += 1 / n
            A[state(i, j) - 1, state(i, j) - 1] += passed / n
    return A.tocsc()
# >>knights-matrix


# <<knights-answer
def corner_indicator():
    """1 on every state with at least one knight on a corner."""
    w = np.zeros(64 * 64)
    for a in range(1, 65):
        for b in range(1, 65):
            if a in CORNERS or b in CORNERS:
                w[state(a, b) - 1] = 1.0
    return w


def solve():
    A = transition()
    v = np.zeros(64 * 64)
    v[state(*START) - 1] = 1.0
    for _ in range(TURNS):
        v = A @ v                      # not A**2005 applied to v
    w = corner_indicator()
    return A, v, w @ v
# >>knights-answer


def spectrum(A, k=5):
    """The k eigenvalues of largest modulus, sorted by modulus."""
    lam = spl.eigs(A, k=k, which="LM", return_eigenvectors=False, tol=0)
    return np.array(sorted(lam, key=lambda z: -abs(z)))


def stationary(A, w):
    """The answer read off the dominant eigenvector instead of the walk."""
    lam, u = spl.eigs(A, k=1, which="LM", tol=0)
    u = np.real(u[:, 0])
    return abs(w @ u / np.linalg.norm(u, 1))


def results():
    A, v, answer = solve()
    w = corner_indicator()
    lam = spectrum(A)
    second = max(abs(z) for z in lam[1:])
    return dict(answer=answer, mass=v.sum(), nnz=A.nnz,
                eigenvalues=lam, second=second,
                decay=second ** TURNS,
                stationary=stationary(A, w))


if __name__ == "__main__":
    r = results()
    print(f"nonzeros in A          {r['nnz']}")
    print(f"total mass after 2005  {r['mass']:.15f}")
    print(f"P(a knight in a corner) {r['answer']:.15f}")
    print(f"from the eigenvector    {r['stationary']:.15f}")
    print(f"|lambda_2| = {r['second']:.12f}, "
          f"|lambda_2|^2005 = {r['decay']:.3e}")
