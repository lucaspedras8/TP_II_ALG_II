from time import perf_counter
import numpy as np

def solve(weights: np.ndarray, values: np.ndarray, capacity: int, epsilon: float):
    """
    Retorna (valor_total, vetor_decisao_0_1, tempo_ms) para o FPTAS.
    
    Args:
        weights: Vetor de pesos dos itens.
        values: Vetor de valores dos itens.
        capacity: Capacidade da mochila.
        epsilon: Parâmetro de erro (ex: 0.1 para 10% de erro).
    """
    t0 = perf_counter()
    n = len(weights)

    if n == 0:
        return 0, [], (perf_counter() - t0) * 1_000

    # 1: Calcular fator de escala (μ) 
    v_max = np.max(values)
    if v_max == 0: 
        return 0, [0] * n, (perf_counter() - t0) * 1_000

    mu = (epsilon * v_max) / n

    # 2: Escalonar e arredondar os valores 
    scaled_values = np.floor(values / mu).astype(int) if mu > 0 else np.zeros_like(values)
    
    v_prime_max_sum = int(np.sum(scaled_values))

    # 3: Resolver com Programação Dinâmica
    M = np.full(v_prime_max_sum + 1, fill_value=np.inf)
    M[0] = 0
    
    items_for_M = [[] for _ in range(v_prime_max_sum + 1)]

    for i in range(n):
        w_i = weights[i]
        v_prime_i = scaled_values[i]
        
        for v_prime in range(v_prime_max_sum, v_prime_i - 1, -1):
            if M[v_prime - v_prime_i] + w_i < M[v_prime]:
                M[v_prime] = M[v_prime - v_prime_i] + w_i
                items_for_M[v_prime] = items_for_M[v_prime - v_prime_i] + [i]


    # 4: Encontrar o melhor valor escalado que cabe na mochila
    possible_v_primes = np.where(M <= capacity)[0]
    if len(possible_v_primes) == 0: # Nenhum item coube
        return 0, [0] * n, (perf_counter() - t0) * 1_000
    
    best_v_prime = np.max(possible_v_primes)

    # 5: Montar o resultado final 
    chosen_indices = items_for_M[best_v_prime]
    
    total_value = values[chosen_indices].sum()
    
    decision = np.zeros(n, dtype=int)
    decision[chosen_indices] = 1
    
    return total_value, decision.tolist(), (perf_counter() - t0) * 1_000