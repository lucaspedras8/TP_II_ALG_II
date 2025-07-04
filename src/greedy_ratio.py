# src/greedy_ratio.py
"""
Heurística gulosa: ordena itens por valor/peso e inclui enquanto couber.
Retorna (valor_total, vetor_0_1, tempo_ms).
"""
from time import perf_counter
import numpy as np


def solve(weights: np.ndarray, values: np.ndarray, capacity: int):
    t0 = perf_counter()

    order = np.argsort(values / weights)[::-1]
    weights, values = weights[order], values[order]

    chosen = np.zeros(len(weights), dtype=int)
    total_w = total_v = 0

    for i, (w, v) in enumerate(zip(weights, values)):
        if total_w + w <= capacity:
            chosen[i] = 1
            total_w += w
            total_v += v

    # reordenar para os índices originais
    decision = np.zeros_like(chosen)
    decision[order] = chosen

    return total_v, decision.tolist(), (perf_counter() - t0) * 1_000
