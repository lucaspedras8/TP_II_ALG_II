# src/analyze.py
"""
Lê o CSV completo gerado por experiment.py e produz:
  - um dashboard de gráficos (tempo e erro)
  - uma tabela resumo com estatísticas detalhadas.
"""
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def main(csv_path: str):
    # --- 1. Carregamento e Preparação dos Dados ---
    print(f"Analisando o arquivo: {csv_path}")
    df = pd.read_csv(csv_path)

    # Converte colunas para numérico, tratando erros (ex: 'NA')
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df['time_ms'] = pd.to_numeric(df['time_ms'], errors='coerce')
    df.dropna(subset=['value'], inplace=True) # Remove linhas onde o valor não pôde ser lido

    # Encontra o valor ótimo para cada instância (normalmente do B&B)
    opt_values = df.loc[df.groupby('instance')['value'].idxmax()]
    df = pd.merge(df, opt_values[['instance', 'value']], on='instance', suffixes=('', '_opt'))
    
    # Calcula o erro relativo em porcentagem
    df['error_pct'] = 100 * (df['value_opt'] - df['value']) / df['value_opt']

    # Identifica os casos de timeout
    TIMEOUT_MS = 30 * 60 * 1000
    df['is_timeout'] = df['time_ms'] >= TIMEOUT_MS

    # --- 2. Geração do Dashboard de Gráficos ---
    print("Gerando gráficos...")
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 1, figsize=(12, 18), sharex=True)
    fig.suptitle('Análise de Desempenho dos Algoritmos para o Problema da Mochila', fontsize=16)

    # ----- Gráfico 1: Tempo de Execução vs. N -----
    ax1 = axes[0]
    # Plota os algoritmos que não dependem de epsilon
    for alg in ['branch_and_bound', 'two_approx']:
        subset = df[df['algorithm'] == alg]
        # Separa execuções normais de timeouts
        normal = subset[~subset['is_timeout']]
        timeouts = subset[subset['is_timeout']]
        ax1.scatter(normal['n'], normal['time_ms'], label=alg, s=40, alpha=0.8)
        if not timeouts.empty:
            ax1.scatter(timeouts['n'], timeouts['time_ms'], 
                        marker='x', color='red', s=100, label=f'{alg} (timeout)')

    # Plota o FPTAS, uma cor para cada epsilon
    fptas_df = df[df['algorithm'] == 'fptas']
    sns.scatterplot(data=fptas_df, x='n', y='time_ms', hue='epsilon', palette='viridis',
                    ax=ax1, s=50, alpha=0.9)
    
    ax1.set_yscale('log')
    ax1.set_title('Tempo de Execução vs. Tamanho da Instância (n)')
    ax1.set_ylabel('Tempo (ms) - Escala Log')
    ax1.legend(title='Algoritmo / Epsilon')

    # ----- Gráfico 2: Erro Relativo vs. N -----
    ax2 = axes[1]
    approx_df = df[df['algorithm'].isin(['two_approx', 'fptas'])]
    
    sns.scatterplot(data=approx_df, x='n', y='error_pct', hue='epsilon', style='algorithm',
                    palette='viridis', ax=ax2, s=60, alpha=0.9)
    
    ax2.set_title('Erro Relativo vs. Tamanho da Instância (n)')
    ax2.set_xlabel('Tamanho da Instância (n)')
    ax2.set_ylabel('Erro Relativo (%)')
    ax2.axhline(0, color='grey', linestyle='--', lw=1) # Linha do ótimo
    ax2.legend(title='Algoritmo / Epsilon')

    # Salva a figura
    out_path_fig = Path(csv_path).with_name("grafico_analise_completa.png")
    fig.savefig(out_path_fig, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"Dashboard de gráficos salvo em: {out_path_fig}")

    # --- 3. Geração de um Resumo Estatístico Detalhado ---
    print("Gerando resumo estatístico...")
    
    # Adiciona uma coluna 'nome_alg' para agrupar FPTAS
    df['alg_name'] = df.apply(
        lambda row: f"fptas (e={row['epsilon']})" if row['algorithm'] == 'fptas' else row['algorithm'],
        axis=1
    )

    summary = df.groupby('alg_name').agg(
        num_execucoes=('instance', 'count'),
        num_timeouts=('is_timeout', 'sum'),
        tempo_medio_ms=('time_ms', lambda x: x[x < TIMEOUT_MS].mean()), # Média sem timeouts
        erro_medio_pct=('error_pct', 'mean'),
        erro_max_pct=('error_pct', 'max')
    ).round(2)
    
    out_path_summary = Path(csv_path).with_name("resumo_detalhado.csv")
    summary.to_csv(out_path_summary)
    print(f"Resumo detalhado salvo em: {out_path_summary}")
    print("\n--- Resumo Detalhado ---")
    print(summary)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python -m src.analyze <caminho_para_o_csv_de_resultados>")
        sys.exit(1)
    main(sys.argv[1])