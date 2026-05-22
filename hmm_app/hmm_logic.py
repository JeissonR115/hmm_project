"""
Lógica del Modelo Oculto de Markov.
Separado de Django para poder importarse y testearse independientemente.
"""

import json
import math


def forward(obs, pi, A, B):
    """
    Algoritmo Forward.
    Retorna (alpha, prob) donde prob = P(obs | modelo).
    """
    T = len(obs)
    N = len(pi)
    alpha = [[0.0] * N for _ in range(T)]

    for i in range(N):
        alpha[0][i] = pi[i] * B[i][obs[0]]

    for t in range(1, T):
        for j in range(N):
            s = sum(alpha[t-1][i] * A[i][j] for i in range(N))
            alpha[t][j] = s * B[j][obs[t]]

    prob = sum(alpha[T-1])
    return alpha, prob


def backward(obs, A, B):
    """Algoritmo Backward. Retorna beta."""
    T = len(obs)
    N = len(A)
    beta = [[0.0] * N for _ in range(T)]
    for i in range(N):
        beta[T-1][i] = 1.0

    for t in range(T-2, -1, -1):
        for i in range(N):
            beta[t][i] = sum(A[i][j] * B[j][obs[t+1]] * beta[t+1][j] for j in range(N))

    return beta


def viterbi(obs, pi, A, B):
    """
    Algoritmo de Viterbi.
    Retorna la secuencia de estados más probable.
    """
    T = len(obs)
    N = len(pi)
    delta = [[0.0] * N for _ in range(T)]
    psi   = [[0]   * N for _ in range(T)]

    for i in range(N):
        delta[0][i] = pi[i] * B[i][obs[0]]

    for t in range(1, T):
        for j in range(N):
            vals = [(delta[t-1][i] * A[i][j], i) for i in range(N)]
            best_val, best_i = max(vals)
            delta[t][j] = best_val * B[j][obs[t]]
            psi[t][j]   = best_i

    # Backtrack
    states = [0] * T
    states[T-1] = max(range(N), key=lambda i: delta[T-1][i])
    for t in range(T-2, -1, -1):
        states[t] = psi[t+1][states[t+1]]

    return states


def baum_welch(obs, pi, A, B, n_iter=10):
    """
    Baum-Welch (EM). Re-estima pi, A, B.
    Retorna (pi_new, A_new, B_new).
    """
    N = len(pi)
    M = len(B[0])
    pi = list(pi)
    A  = [list(row) for row in A]
    B  = [list(row) for row in B]

    for _ in range(n_iter):
        alpha, prob = forward(obs, pi, A, B)
        beta        = backward(obs, A, B)
        T           = len(obs)

        if prob == 0:
            break

        # Gamma
        gamma = [[0.0]*N for _ in range(T)]
        for t in range(T):
            denom = sum(alpha[t][i]*beta[t][i] for i in range(N))
            if denom == 0:
                continue
            for i in range(N):
                gamma[t][i] = alpha[t][i]*beta[t][i] / denom

        # Xi
        xi = [[[0.0]*N for _ in range(N)] for _ in range(T-1)]
        for t in range(T-1):
            denom = sum(
                alpha[t][i]*A[i][j]*B[j][obs[t+1]]*beta[t+1][j]
                for i in range(N) for j in range(N)
            )
            if denom == 0:
                continue
            for i in range(N):
                for j in range(N):
                    xi[t][i][j] = alpha[t][i]*A[i][j]*B[j][obs[t+1]]*beta[t+1][j] / denom

        # Re-estimar
        pi = [gamma[0][i] for i in range(N)]

        for i in range(N):
            denom = sum(gamma[t][i] for t in range(T-1))
            for j in range(N):
                A[i][j] = sum(xi[t][i][j] for t in range(T-1)) / (denom or 1e-10)

        for i in range(N):
            denom = sum(gamma[t][i] for t in range(T))
            for k in range(M):
                B[i][k] = sum(gamma[t][i] for t in range(T) if obs[t]==k) / (denom or 1e-10)

    return pi, A, B


def parse_obs_string(s):
    """Convierte '0,1,2,0' en [0, 1, 2, 0]. Valida que sean 0, 1 o 2."""
    try:
        vals = [int(x.strip()) for x in s.split(',') if x.strip()]
        if not vals:
            raise ValueError("Secuencia vacía")
        if any(v not in (0, 1, 2) for v in vals):
            raise ValueError("Solo se permiten valores 0, 1 o 2")
        return vals
    except ValueError as e:
        raise ValueError(str(e))


def safe_log_prob(prob):
    """Retorna log-probabilidad o -inf si prob <= 0."""
    if prob <= 0:
        return float('-inf')
    return math.log(prob)
