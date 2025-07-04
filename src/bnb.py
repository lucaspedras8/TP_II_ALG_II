from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple
import heapq, time
import numpy as np


# Nó da árvore de Branch-and-Bound
@dataclass(order=True)
class Node:
    sort_key: float = field(init=False, repr=False)       # para heapq (bound negativo)
    bound: float
    level: int
    total_w: int
    total_v: int
    taken: List[int]                                      # 1 = item incluído

    def __post_init__(self):
        object.__setattr__(self, "sort_key", -self.bound)  # max-heap via bound negativo


# Bound fracionário (relaxação do knapsack fracionário)
def fractional_bound(level: int, cur_w: int, cur_v: int,
                     weights: np.ndarray, values: np.ndarray,
                     capacity: int) -> float:
    if cur_w >= capacity:
        return 0
    bound = cur_v
    w = cur_w
    n = len(weights)
    for i in range(level, n):
        if w + weights[i] <= capacity:
            w += weights[i]
            bound += values[i]
        else:                               # pega fração do próximo item
            bound += (capacity - w) * values[i] / weights[i]
            break
    return bound


# Função principal
def solve(weights: np.ndarray,
          values:  np.ndarray,
          capacity: int) -> Tuple[int, List[int], float]:
    """Retorna (valor_ótimo, vetor_itens_0-1, tempo_ms)."""
    t0 = time.perf_counter()

    # 1. ordenar por razão valor/peso (melhor bound)
    order = np.argsort(values / weights)[::-1]
    weights, values = weights[order], values[order]
    n = len(weights)

    best_val = 0
    best_taken = [0] * n
    pq: list[Node] = []

    # 2. nó raiz
    root = Node(bound=fractional_bound(0, 0, 0, weights, values, capacity),
                level=0, total_w=0, total_v=0, taken=[])
    heapq.heappush(pq, root)

    # 3. exploração best-first
    while pq:
        node = heapq.heappop(pq)
        if node.bound <= best_val:          # poda
            continue
        lvl = node.level
        if lvl == n:                        # folhas já tratadas
            continue

        # ─ filho que INCLUI o item lvl
        w_inc = node.total_w + weights[lvl]
        v_inc = node.total_v + values[lvl]
        taken_inc = node.taken + [1]
        if w_inc <= capacity:
            if v_inc > best_val:            # nova melhor solução inteira
                best_val   = v_inc
                best_taken = taken_inc + [0]*(n - len(taken_inc))
            b_inc = fractional_bound(lvl+1, w_inc, v_inc, weights, values, capacity)
            if b_inc > best_val:
                heapq.heappush(pq, Node(b_inc, lvl+1, w_inc, v_inc, taken_inc))

        # ─ filho que EXCLUI o item lvl
        b_exc = fractional_bound(lvl+1, node.total_w, node.total_v, weights, values, capacity)
        if b_exc > best_val:
            heapq.heappush(pq,
                Node(b_exc, lvl+1, node.total_w, node.total_v, node.taken + [0]))

    # 4. reordenar vetor de decisão para os índices originais
    decision = [0]*n
    for pos, flag in enumerate(best_taken):
        decision[order[pos]] = flag

    dt_ms = (time.perf_counter() - t0) * 1_000
    return best_val, decision, dt_ms
