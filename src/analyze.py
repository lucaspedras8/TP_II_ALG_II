# src/analyze.py
"""
Lê o CSV completo gerado por experiment.py e produz:
  - um dashboard de gráficos 2x2 (tempo e fator de aproximação)
  - uma tabela resumo com estatísticas detalhadas.
"""
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np

def main(csv_path: str):
    # --- 1. Carregamento e Preparação dos Dados ---
    print(f"Analisando o arquivo: {csv_path}")
    df = pd.read_csv(csv_path)

    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df['time_ms'] = pd.to_numeric(df['time_ms'], errors='coerce')
    df.dropna(subset=['value'], inplace=True)

    opt_values = df.loc[df.groupby('instance')['value'].idxmax()]
    df = pd.merge(df, opt_values[['instance', 'value']], on='instance', suffixes=('', '_opt'))
    
    # Calcula o Fator de Aproximação (Razão Ótimo/Aproximado)
    # Adiciona um valor pequeno para evitar divisão por zero se o valor for 0
    df['approx_ratio'] = df['value_opt'] / (df['value'] + 1e-9)

    TIMEOUT_MS = 30 * 60 * 1000
    df['is_timeout'] = df['time_ms'] >= TIMEOUT_MS

    # --- 2. Geração do Dashboard de Gráficos 2x2 ---
    print("Gerando dashboard de gráficos...")
    sns.set_theme(style="whitegrid", palette="deep")
    fig, axes = plt.subplots(2, 2, figsize=(18, 14)) # Grid 2x2
    fig.suptitle('Análise Comparativa de Algoritmos para o Problema da Mochila', fontsize=20, y=0.95)

    # ----- Gráfico [0, 0]: Tempo de Execução (Branch-and-Bound) -----
    ax = axes[0, 0]
    df_bnb = df[df['algorithm'] == 'branch_and_bound']
    normal = df_bnb[~df_bnb['is_timeout']]
    timeouts = df_bnb[df_bnb['is_timeout']]
    ax.scatter(normal['n'], normal['time_ms'], s=50, alpha=0.7, label='Execução Normal')
    if not timeouts.empty:
        ax.scatter(timeouts['n'], timeouts['time_ms'], marker='x', color='red', s=120, label='Timeout (>30min)')
    ax.set_yscale('log')
    ax.set_title('Tempo de Execução (Branch-and-Bound)')
    ax.set_xlabel('Tamanho da Instância (n)')
    ax.set_ylabel('Tempo (ms) - Escala Log')
    ax.legend()

    # ----- Gráfico [0, 1]: Tempo de Execução (2-Approximation) -----
    ax = axes[0, 1]
    df_2approx = df[df['algorithm'] == 'two_approx']
    ax.scatter(df_2approx['n'], df_2approx['time_ms'], s=50, alpha=0.7, color='green')
    ax.set_title('Tempo de Execução (2-Approximation)')
    ax.set_xlabel('Tamanho da Instância (n)')
    ax.set_ylabel('Tempo (ms)')
    # A escala log não é necessária aqui pois os tempos são muito baixos e uniformes

    # ----- Gráfico [1, 0]: Tempo de Execução (FPTAS) -----
    ax = axes[1, 0]
    df_fptas = df[df['algorithm'] == 'fptas']
    sns.lineplot(data=df_fptas, x='n', y='time_ms', hue='epsilon', palette='viridis',
                 marker='o', ax=ax, errorbar=None)
    ax.set_yscale('log')
    ax.set_title('Tempo de Execução (FPTAS)')
    ax.set_xlabel('Tamanho da Instância (n)')
    ax.set_ylabel('Tempo (ms) - Escala Log')
    ax.legend(title='Epsilon')

    # ----- Gráfico [1, 1]: Fator de Aproximação vs. n -----
    ax = axes[1, 1]
    df_approx = df[df['algorithm'].isin(['two_approx', 'fptas'])].copy()
    # Adiciona nome do algoritmo com epsilon para a legenda
    df_approx['alg_name'] = df_approx.apply(
        lambda row: f"FPTAS (e={row['epsilon']})" if row['algorithm'] == 'fptas' else '2-Approx', axis=1)
    
    sns.scatterplot(data=df_approx, x='n', y='approx_ratio', hue='alg_name', style='alg_name',
                    palette='Paired', s=70, ax=ax)
    
    ax.axhline(1.0, color='red', linestyle='--', lw=1.5, label='Solução Ótima (Fator=1.0)')
    ax.set_title('Qualidade da Solução (Fator de Aproximação)')
    ax.set_xlabel('Tamanho da Instância (n)')
    ax.set_ylabel('Fator de Aproximação (Ótimo / Obtido)')
    ax.legend(title='Algoritmo')
    
    # Ajusta o layout e salva a figura
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    out_path_fig = Path(csv_path).with_name("dashboard_analise.png")
    fig.savefig(out_path_fig, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"Dashboard de gráficos salvo em: {out_path_fig}")

    # (A parte do resumo estatístico pode continuar a mesma)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python -m src.analyze <caminho_para_o_csv_de_resultados>")
        sys.exit(1)
    main(sys.argv[1])