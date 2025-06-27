import sys
from pathlib import Path
from time import perf_counter
from multiprocessing import Process, Queue

import pandas as pd
import numpy as np

from src.utils import io
from src.bnb import solve as solve_bnb
from src.fptas import solve as solve_fptas
from src.two_approx import solve as solve_two_approx

# 1. Define os algoritmos que você quer testar.
ALGORITHMS = {
    "branch_and_bound": solve_bnb,
    "two_approx": solve_two_approx,
}

# 2. Define os valores de Epsilon para o FPTAS.
EPSILONS = [0.1, 0.3, 0.5, 0.8]

# 3. Define os diretórios com as instâncias de teste.
DATA_FOLDERS = [
    "data/low_dimensional",
    "data/large_scale/large_scale",
]

# 4. Define o tempo máximo de execução em segundos.
TIMEOUT_SECONDS = 30 * 60  # 30 minutos

# 5. Define o nome do arquivo de saída.
OUTPUT_CSV_PATH = "results/final_results.csv"


def run_with_timeout(func, args, timeout, result_queue):
    """
    Roda uma função em um processo separado e impõe um timeout.
    """
    try:
        result = func(*args)
        result_queue.put(result)
    except Exception as e:
        result_queue.put(e)


def main():
    """
    Função principal que orquestra a execução dos experimentos.
    """
    results_list = []

    instance_files = []
    for folder in DATA_FOLDERS:
        path = Path(folder)
        instance_files.extend(path.glob("*_info.csv"))
        instance_files.extend([p for p in path.glob("*") if p.suffix == ''])

    print(f"Encontradas {len(instance_files)} instâncias para processar.")

    for i, instance_path in enumerate(instance_files):
        print(f"\nProcessando instância {i+1}/{len(instance_files)}: {instance_path.name}")
        
        try:
            weights, values, capacity = io.load_instance(instance_path)
            n = len(weights)
        except Exception as e:
            print(f"  -> Erro ao carregar instância: {e}")
            continue

        for alg_name, solve_func in ALGORITHMS.items():
            print(f"  -> Rodando {alg_name}...")
            
            result_queue = Queue()
            p = Process(target=run_with_timeout, args=(solve_func, (weights, values, capacity), TIMEOUT_SECONDS, result_queue))
            p.start()
            p.join(TIMEOUT_SECONDS)

            if p.is_alive():
                p.terminate()
                p.join()
                print(f"  -> TIMEOUT! ({TIMEOUT_SECONDS}s)")
                value, time_ms = "NA", TIMEOUT_SECONDS * 1000
            else:
                result = result_queue.get()
                if isinstance(result, Exception):
                    print(f"  -> ERRO! {result}")
                    value, time_ms = "ERROR", -1
                else:
                    value, _, time_ms = result
            
            results_list.append({
                "instance": instance_path.name,
                "n": n,
                "algorithm": alg_name,
                "epsilon": "NA",
                "value": value,
                "time_ms": time_ms,
            })

        for eps in EPSILONS:
            alg_name = f"fptas_e={eps}"
            print(f"  -> Rodando {alg_name}...")
            
            result_queue = Queue()
            p = Process(target=run_with_timeout, args=(solve_fptas, (weights, values, capacity, eps), TIMEOUT_SECONDS, result_queue))
            p.start()
            p.join(TIMEOUT_SECONDS)

            if p.is_alive():
                p.terminate()
                p.join()
                print(f"  -> TIMEOUT! ({TIMEOUT_SECONDS}s)")
                value, time_ms = "NA", TIMEOUT_SECONDS * 1000
            else:
                result = result_queue.get()
                if isinstance(result, Exception):
                    print(f"  -> ERRO! {result}")
                    value, time_ms = "ERROR", -1
                else:
                    value, _, time_ms = result

            results_list.append({
                "instance": instance_path.name,
                "n": n,
                "algorithm": "fptas",
                "epsilon": eps,
                "value": value,
                "time_ms": time_ms,
            })

    print("\nSalvando resultados...")
    results_df = pd.DataFrame(results_list)
    results_df.to_csv(OUTPUT_CSV_PATH, index=False)
    print(f"Resultados salvos em: {OUTPUT_CSV_PATH}")


if __name__ == "__main__":
    main()