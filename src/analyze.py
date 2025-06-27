# src/analyze.py
"""
Lê um CSV gerado por experiment.py e produz:
  • grafico_tempo_x_n.png
  • grafico_erro_x_n.png
  • resumo.csv  (estatísticas de tempo e erro)
Uso:
    python -m src.analyze results/low_small.csv
"""

import sys, pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def main(csv_path: str):
    df = pd.read_csv(csv_path)

    # ───────── tempo × n ─────────
    fig1 = plt.figure()
    for alg in df["algorithm"].unique():
        subset = df[df["algorithm"] == alg]
        plt.scatter(subset["n"], subset["time_ms"], label=alg, s=20)
    plt.xlabel("n (itens)"); plt.ylabel("tempo (ms)")
    plt.yscale("log"); plt.title("Tempo × n"); plt.legend()
    out1 = Path(csv_path).with_name("grafico_tempo_x_n.png")
    fig1.savefig(out1, bbox_inches="tight"); plt.close(fig1)

      # ───────── erro relativo × n ─────────
    pivot = df.pivot_table(index="instance",
                           columns="algorithm",
                           values="value",
                           aggfunc="max")
    pivot["opt"] = pivot.max(axis=1)

    # mapa instância → n
    n_map = df.groupby("instance")["n"].first()

    err_rows = []
    for alg in df["algorithm"].unique():
        err_pct = 100 * (pivot["opt"] - pivot[alg]) / pivot["opt"]
        for inst, pct in err_pct.items():
            err_rows.append(
                {"instance": inst,
                 "n": int(n_map[inst]),
                 "algorithm": alg,
                 "err_pct": pct}
            )
    err_df = pd.DataFrame(err_rows)

    fig2 = plt.figure()
    for alg in err_df["algorithm"].unique():
        subset = err_df[err_df["algorithm"] == alg]
        plt.scatter(subset["n"], subset["err_pct"], label=alg, s=20)
    plt.xlabel("n"); plt.ylabel("erro relativo (%)")
    plt.title("Erro relativo × n"); plt.legend()
    out2 = Path(csv_path).with_name("grafico_erro_x_n.png")
    fig2.savefig(out2, bbox_inches="tight"); plt.close(fig2)

    # ───────── resumo numérico ─────────
    summary = (df.groupby("algorithm")
                 .agg(media_tempo_ms=("time_ms", "mean"),
                      media_valor    =("value", "mean"))
                 .reset_index())
    summary_path = Path(csv_path).with_name("resumo.csv")
    summary.to_csv(summary_path, index=False)

    print("Figuras salvas em:", out1, out2)
    print("Resumo numérico  :", summary_path)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python -m src.analyze <csv>")
        sys.exit(1)
    main(sys.argv[1])
