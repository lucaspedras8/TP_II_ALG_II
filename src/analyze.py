"""
Lê o CSV completo gerado por experiment.py e produz:
  - um dashboard de gráficos 2x2 (tempo e fator de aproximação)
  - um gráfico de análise de memória
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

    # Converte colunas para numérico, tratando "NA" e "ERROR" como Nulos
    for col in ['value', 'time_ms', 'peak_mem_kb']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Remove linhas onde a conversão para número falhou
    df.dropna(subset=['value', 'time_ms', 'peak_mem_kb'], inplace=True)

    # Encontra o valor ótimo para cada instância (normalmente do B&B)
    # .loc é usado para evitar SettingWithCopyWarning
    opt_indices = df.loc[df.groupby('instance')['value'].idxmax()].index
    opt_df = df.loc[opt_indices][['instance', 'value']].rename(columns={'value': 'value_opt'})
    
    df = pd.merge(df, opt_df, on='instance')
    
    # Calcula Fator de Aproximação (Ótimo/Obtido) e Erro Percentual
    df['approx_ratio'] = df['value_opt'] / (df['value'] + 1e-9)
    df['error_pct'] = 100 * (df['value_opt'] - df['value']) / (df['value_opt'] + 1e-9)

    TIMEOUT_MS = 30 * 60 * 1000
    df['is_timeout'] = df['time_ms'] >= TIMEOUT_MS
    
    # Cria uma coluna 'alg_name' para agrupar FPTAS por epsilon nas legendas
    df['alg_name'] = df.apply(
        lambda row: f"FPTAS (e={row['epsilon']})" if row['algorithm'] == 'fptas' else row['algorithm'],
        axis=1
    )

    # --- 2. Geração do Dashboard Comparativo (Tempo e Qualidade) ---
    print("Gerando dashboard de Tempo e Qualidade...")
    sns.set_theme(style="whitegrid", palette="deep")
    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    fig.suptitle('Análise Comparativa de Algoritmos para o Problema da Mochila', fontsize=22, y=1.0)

    # Filtra os dataframes por algoritmo
    df_bnb = df[df['algorithm'] == 'branch_and_bound']
    df_2approx = df[df['algorithm'] == 'two_approx']
    df_fptas = df[df['algorithm'] == 'fptas']

    # Gráfico [0, 0]: Tempo B&B
    ax = axes[0, 0]
    ax.scatter(df_bnb[~df_bnb['is_timeout']]['n'], df_bnb[~df_bnb['is_timeout']]['time_ms'], s=50, alpha=0.7, label='Execução Normal')
    if not df_bnb[df_bnb['is_timeout']].empty:
        ax.scatter(df_bnb[df_bnb['is_timeout']]['n'], df_bnb[df_bnb['is_timeout']]['time_ms'], marker='x', color='red', s=120, label='Timeout (>30min)')
    ax.set(yscale='log', title='Tempo de Execução (Branch-and-Bound)', xlabel='Tamanho da Instância (n)', ylabel='Tempo (ms) - Escala Log')
    ax.legend()

    # Gráfico [0, 1]: Tempo 2-Approximation
    ax = axes[0, 1]
    ax.scatter(df_2approx['n'], df_2approx['time_ms'], s=50, alpha=0.7, color='green')
    ax.set(title='Tempo de Execução (2-Approximation)', xlabel='Tamanho da Instância (n)', ylabel='Tempo (ms)')

    # Gráfico [1, 0]: Tempo FPTAS
    ax = axes[1, 0]
    sns.lineplot(data=df_fptas, x='n', y='time_ms', hue='epsilon', palette='viridis', marker='o', ax=ax, errorbar=None)
    ax.set(yscale='log', title='Tempo de Execução (FPTAS)', xlabel='Tamanho da Instância (n)', ylabel='Tempo (ms) - Escala Log')
    ax.legend(title='Epsilon')

    # Gráfico [1, 1]: Fator de Aproximação
    ax = axes[1, 1]
    df_approx = df[df['algorithm'].isin(['two_approx', 'fptas'])]
    sns.scatterplot(data=df_approx, x='n', y='approx_ratio', hue='alg_name', style='alg_name', palette='Paired', s=70, ax=ax)
    ax.axhline(1.0, color='red', linestyle='--', lw=1.5, label='Solução Ótima (Fator=1.0)')
    ax.set(title='Qualidade da Solução (Fator de Aproximação)', xlabel='Tamanho da Instância (n)', ylabel='Fator de Aproximação (Ótimo / Obtido)')
    ax.legend(title='Algoritmo')
    
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    out_path_fig = Path(csv_path).with_name("dashboard_analise.png")
    fig.savefig(out_path_fig, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"Dashboard salvo em: {out_path_fig}")

    # --- 3. Geração do Gráfico Individual de Memória ---
    print("Gerando gráfico de Análise de Memória...")
    fig_mem, ax_mem = plt.subplots(figsize=(12, 8))
    
    # Plota todos os algoritmos juntos para comparação de memória
    sns.scatterplot(data=df, x='n', y='peak_mem_kb', hue='alg_name', style='algorithm', s=80, alpha=0.8, ax=ax_mem)
    
    ax_mem.set(yscale='log', title='Análise de Consumo de Memória vs. Tamanho da Instância (n)', xlabel='Tamanho da Instância (n)', ylabel='Pico de Memória (KB) - Escala Log')
    ax_mem.legend(title='Algoritmo / Epsilon')
    
    out_path_mem_fig = Path(csv_path).with_name("grafico_memoria_vs_n.png")
    fig_mem.savefig(out_path_mem_fig, bbox_inches="tight", dpi=150)
    plt.close(fig_mem)
    print(f"Gráfico de Memória salvo em: {out_path_mem_fig}")

    # --- 4. Geração do Resumo Estatístico Final ---
    print("Gerando resumo estatístico detalhado...")
    summary = df.groupby('alg_name').agg(
        num_execucoes=('instance', 'nunique'),
        num_timeouts=('is_timeout', 'sum'),
        tempo_medio_ms=('time_ms', lambda x: x[x < TIMEOUT_MS].mean()),
        memoria_media_kb=('peak_mem_kb', 'mean'),
        fator_aprox_medio=('approx_ratio', 'mean')
    ).round(2)
    
    out_path_summary = Path(csv_path).with_name("resumo_final.csv")
    summary.to_csv(out_path_summary)
    print(f"Resumo detalhado salvo em: {out_path_summary}")
    print("\n--- Resumo Final ---")
    print(summary)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python -m src.analyze <caminho_para_o_csv_de_resultados>")
        sys.exit(1)
    main(sys.argv[1])