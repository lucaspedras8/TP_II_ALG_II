# src/two_approx.py
"""
2-aproximação: compara
  A) melhor item que caiba sozinho
  B) solução greedy razão valor/peso
e devolve o melhor dos dois.
"""
from time import perf_counter
import numpy as np
from src.greedy_ratio import solve as greedy_solve

def solve(weights: np.ndarray, values: np.ndarray, capacity: int):
    t0 = perf_counter()

    # A) melhor item isolado
    mask  = weights <= capacity
    best_single_idx = np.argmax(values * mask)          # valor 0 se não cabe
    single_value    = values[best_single_idx] if mask.any() else 0
    single_decision = np.zeros(len(weights), dtype=int)
    if single_value > 0:
        single_decision[best_single_idx] = 1

    # B) greedy
    greedy_value, greedy_decision, _ = greedy_solve(weights, values, capacity)

    # escolher
    if single_value >= greedy_value:
        best_val, decision = single_value, single_decision.tolist()
    else:
        best_val, decision = greedy_value, greedy_decision

    return best_val, decision, (perf_counter() - t0) * 1_000
