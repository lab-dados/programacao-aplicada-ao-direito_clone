"""Análise da base de processos: taxa de êxito do autor, acordos e seis gráficos.

É o analise.py que saiu do Colab, melhorado com o Claude Code no Encontro 6. As tabelas são
calculadas por funções; nada roda sozinho quando o arquivo é importado.

Para rodar tudo de uma vez:

    python analise_2.py

Isso imprime as tabelas na tela e grava os seis gráficos na pasta graficos/. O significado de
cada coluna da base está no AGENTS.md.
"""
from pathlib import Path

import numpy as np
import pandas as pd

# Os gráficos precisam do matplotlib. Sem ele, as tabelas continuam funcionando.
try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

PASTA = Path(__file__).parent
PASTA_DADOS = PASTA / "dados"
PASTA_GRAFICOS = PASTA / "graficos"

RESULTADOS = [
    "PROCEDENTE", "PARCIALMENTE PROCEDENTE", "IMPROCEDENTE", "EXTINTO SEM MÉRITO", "ACORDO HOMOLOGADO",
]
# Abaixo disso, a taxa de um ano diz pouco, e o ano sai dos gráficos por ano.
MINIMO_CASOS_ANO = 30

# Cores e estilo dos gráficos.
INK, MUTED, GRID, BLUE, GRAY = "#1f2328", "#656d76", "#e6e8eb", "#2a6fdb", "#b8bec6"
CORES_RESULTADO = ["#1b4f9c", "#7fa8e8", "#d9822b", "#9aa3ad", "#2a9d8f"]
ESTILO = {
    # Segoe UI existe em todo Windows. Em outro sistema, o matplotlib usa a DejaVu Sans.
    "font.family": ["Segoe UI", "DejaVu Sans"],
    "axes.edgecolor": GRID,
    "axes.labelcolor": MUTED,
    "xtick.color": MUTED,
    "ytick.color": INK,
    "axes.spines.top": False,
    "axes.spines.right": False,
}


# ------------------------------------------------------------------------------- leitura

def carregar_processos(caminho=PASTA_DADOS / "processos.csv"):
    """Lê processos.csv com tipos corretos (ganhou_autor como booleano anulável)."""
    df = pd.read_csv(caminho, dtype={"processo": str})
    df["ganhou_autor"] = df["ganhou_autor"].astype("boolean")
    return df


def carregar_dispositivos(caminho=PASTA_DADOS / "dispositivos.csv"):
    """Lê o texto do dispositivo de cada processo. Junte com os processos pela coluna processo."""
    return pd.read_csv(caminho, dtype={"processo": str})


# ------------------------------------------------------------------------------- tabelas

def intervalo_wilson(sucessos, n, z=1.96):
    """Intervalo de confiança de Wilson (95%) para uma proporção. Aceita arrays."""
    sucessos, n = np.asarray(sucessos, dtype=float), np.asarray(n, dtype=float)
    p = sucessos / n
    centro = (p + z**2 / (2 * n)) / (1 + z**2 / n)
    margem = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / (1 + z**2 / n)
    return centro - margem, centro + margem


def calcular_taxa_exito_por_setor(df, n_minimo=1):
    """
    Calcula a taxa de êxito do autor por setor, com intervalo de confiança de Wilson.

    Considera apenas processos com mérito decidido (ganhou_autor não nulo). Acordos
    homologados e registros sem resultado ficam de fora, e o setor ausente é excluído
    do agrupamento. Use `resumo_cobertura` para ver o tamanho dessas exclusões.

    Args:
        df: DataFrame de processos (ver `carregar_processos`).
        n_minimo: número mínimo de casos para o setor aparecer no resultado.

    Returns:
        DataFrame indexado por setor com colunas contagem, vitorias, taxa_exito,
        ic_inf e ic_sup, ordenado por taxa_exito decrescente.
    """
    base = df.dropna(subset=["ganhou_autor", "setor"])
    por_setor = base.groupby("setor")["ganhou_autor"].agg(
        contagem="count", vitorias="sum"
    )
    por_setor["vitorias"] = por_setor["vitorias"].astype(int)
    por_setor["taxa_exito"] = por_setor["vitorias"] / por_setor["contagem"]
    por_setor["ic_inf"], por_setor["ic_sup"] = intervalo_wilson(
        por_setor["vitorias"], por_setor["contagem"]
    )
    por_setor = por_setor[por_setor["contagem"] >= n_minimo]
    return por_setor.sort_values("taxa_exito", ascending=False)


def resumo_cobertura(df):
    """Quantifica quantos processos entram e por que os demais ficam de fora."""
    total = len(df)
    sem_merito = df["ganhou_autor"].isna()
    sem_setor = df["setor"].isna()
    return pd.Series(
        {
            "total": total,
            "sem resultado de mérito (acordo ou resultado ausente)": int(sem_merito.sum()),
            "  dos quais acordo homologado": int((df["resultado"] == "ACORDO HOMOLOGADO").sum()),
            "  dos quais resultado ausente": int(df["resultado"].isna().sum()),
            "com mérito mas sem setor": int((~sem_merito & sem_setor).sum()),
            "usados na análise": int((~sem_merito & ~sem_setor).sum()),
        }
    )


def calcular_taxa_exito_por_ano(df, n_minimo=MINIMO_CASOS_ANO):
    """
    Taxa de êxito do autor por ano de ajuizamento, com intervalo de confiança de Wilson.

    Usa todos os processos com mérito decidido, com ou sem setor. Anos com menos de
    `n_minimo` casos ficam de fora. Colunas: n (casos), v (vitórias), p (taxa), ic_inf e ic_sup.
    """
    b = df.dropna(subset=["ganhou_autor"])
    g = b.groupby("ano")["ganhou_autor"].agg(n="count", v="sum")
    g["v"] = g["v"].astype(int)
    g = g[g.n >= n_minimo].copy()
    g["p"] = g.v / g.n
    g["ic_inf"], g["ic_sup"] = intervalo_wilson(g.v, g.n)
    return g


def calcular_resultados_por_ano(df, n_minimo=MINIMO_CASOS_ANO):
    """
    Quantos processos terminaram em cada resultado, ano a ano (contagens, não proporções).

    Processos sem resultado ficam de fora. Anos com menos de `n_minimo` processos com
    resultado também. As colunas seguem a ordem de RESULTADOS.
    """
    d = df.dropna(subset=["resultado"])
    c = pd.crosstab(d.ano, d.resultado)[RESULTADOS]
    return c[c.sum(axis=1) >= n_minimo]


def calcular_acordo_e_exito_por_setor(df):
    """
    Taxa de acordo e taxa de êxito lado a lado, uma linha por setor.

    A taxa de acordo é a proporção de ACORDO HOMOLOGADO entre os processos do setor com
    resultado (coluna total). A taxa de êxito vem de `calcular_taxa_exito_por_setor`, e
    por isso não conta os acordos. Ordenado pela taxa de êxito, da menor para a maior.
    """
    t = calcular_taxa_exito_por_setor(df).sort_values("taxa_exito")
    b = df.dropna(subset=["setor", "resultado"])
    ac = (b.resultado == "ACORDO HOMOLOGADO").groupby(b.setor).agg(["mean", "size"])
    return t.join(ac.rename(columns={"mean": "acordo", "size": "total"}))


# ------------------------------------------------------------------------------- gráficos

def _pct(v, _):
    return f"{v:.0%}"


def _preparar():
    """Confere se o matplotlib está instalado e aplica o estilo dos gráficos."""
    if plt is None:
        raise ImportError(
            "Os gráficos precisam do matplotlib, que não está instalado. "
            "Instale com: python -m pip install matplotlib"
        )
    # Só as fontes instaladas: assim o matplotlib não avisa que a Segoe UI falta fora do Windows.
    instaladas = {f.name for f in matplotlib.font_manager.fontManager.ttflist}
    fontes = [f for f in ESTILO["font.family"] if f in instaladas] or ["DejaVu Sans"]
    plt.rcParams.update({**ESTILO, "font.family": fontes})


def grafico_cobertura(df):
    """Barras: quantos dos processos entram na análise de êxito, e por que os outros ficam fora."""
    _preparar()
    r = resumo_cobertura(df)
    partes = [("Usados na análise", r["usados na análise"], BLUE),
              ("Acordo homologado", r["  dos quais acordo homologado"], GRAY),
              ("Mérito sem setor", r["com mérito mas sem setor"], GRAY),
              ("Resultado ausente", r["  dos quais resultado ausente"], GRAY)]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    labels = [p[0] for p in partes][::-1]
    vals = [p[1] for p in partes][::-1]
    cols = [p[2] for p in partes][::-1]
    ax.barh(labels, vals, color=cols, height=0.55)
    for i, v in enumerate(vals):
        ax.text(v + 30, i, f"{int(v):,}  ({v/r['total']:.0%})".replace(",", "."), va="center", color=INK)
    ax.set_xlim(0, max(vals) * 1.25)
    ax.set_title(f"Quantos dos {int(r['total']):,} processos entram na análise".replace(",", "."),
                 loc="left", color=INK, fontsize=13)
    ax.xaxis.grid(True, color=GRID); ax.set_axisbelow(True)
    fig.tight_layout()
    return fig


def grafico_exito_intervalo(df):
    """Pontos: taxa de êxito por setor, com o intervalo de confiança de 95% e a média geral."""
    _preparar()
    t = calcular_taxa_exito_por_setor(df).sort_values("taxa_exito")
    # A "média" é a taxa de êxito de todos os processos com setor, não a média das taxas.
    geral = t["vitorias"].sum() / t["contagem"].sum()
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    y = np.arange(len(t))
    ax.hlines(y, t.ic_inf, t.ic_sup, color=BLUE, lw=2, alpha=.5)
    ax.scatter(t.taxa_exito, y, s=60, color=BLUE, edgecolor="white", linewidth=2, zorder=3)
    ax.axvline(geral, color=MUTED, ls="--", lw=1)
    ax.text(geral + .005, -.9, f"média {geral:.0%}", color=MUTED, fontsize=9, va="center")
    ax.set_yticks(y, [f"{s}  (n={n})" for s, n in zip(t.index, t.contagem)])
    ax.xaxis.set_major_formatter(_pct)
    ax.set_ylim(-1.3, len(t) - .5); ax.set_xlim(0, 1); ax.xaxis.grid(True, color=GRID); ax.set_axisbelow(True)
    ax.set_title("Taxa de êxito do autor por setor (IC 95% de Wilson)", loc="left", color=INK, fontsize=13)
    fig.tight_layout()
    return fig


def grafico_exito_por_ano(df):
    """Linha: taxa de êxito do autor ano a ano, com a faixa do intervalo de confiança."""
    _preparar()
    g = calcular_taxa_exito_por_ano(df)
    fig, ax = plt.subplots(figsize=(8.5, 4))
    ax.fill_between(g.index, g.ic_inf, g.ic_sup, color=BLUE, alpha=.15, lw=0)
    ax.plot(g.index, g.p, color=BLUE, lw=2, marker="o", ms=8, mec="white", mew=2)
    ax.yaxis.set_major_formatter(_pct)
    ax.set_ylim(0, 1); ax.yaxis.grid(True, color=GRID); ax.set_axisbelow(True)
    ax.set_xticks(g.index)
    ax.set_title("Taxa de êxito do autor por ano de distribuição (IC 95%)", loc="left", color=INK, fontsize=13)
    fig.tight_layout()
    return fig


def grafico_barras_setor(df):
    """Barras: taxa de êxito do autor por setor, com o número de casos ao lado de cada barra."""
    _preparar()
    t = calcular_taxa_exito_por_setor(df).sort_values("taxa_exito")
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    ax.barh(t.index, t.taxa_exito, color=BLUE, height=.6)
    for i, (v, n) in enumerate(zip(t.taxa_exito, t.contagem)):
        ax.text(v + .01, i, f"{v:.0%}  (n={n})", va="center", color=INK, fontsize=9)
    ax.set_xlim(0, .75); ax.xaxis.set_major_formatter(_pct)
    ax.xaxis.grid(True, color=GRID); ax.set_axisbelow(True)
    ax.set_title("Taxa de êxito do autor por setor", loc="left", color=INK, fontsize=13)
    fig.tight_layout()
    return fig


def grafico_resultados_por_ano(df):
    """Barras empilhadas: a proporção de cada resultado, ano a ano, com o total sobre a barra."""
    _preparar()
    c = calcular_resultados_por_ano(df)
    p = c.div(c.sum(axis=1), axis=0)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    base = np.zeros(len(p))
    for col, cor in zip(RESULTADOS, CORES_RESULTADO):
        ax.bar(p.index.astype(str), p[col], bottom=base, color=cor, width=.7,
               edgecolor="white", linewidth=1.5, label=col.capitalize())
        base += p[col].values
    for i, n in enumerate(c.sum(axis=1)):
        ax.text(i, 1.02, f"n={n}", ha="center", color=MUTED, fontsize=8)
    ax.set_ylim(0, 1.08); ax.yaxis.set_major_formatter(_pct)
    ax.legend(ncol=5, frameon=False, loc="upper center", bbox_to_anchor=(.5, -.08), fontsize=8)
    ax.set_title("Resultados dos processos por ano (% do total decidido)", loc="left", color=INK, fontsize=13, pad=18)
    fig.tight_layout()
    return fig


def grafico_acordo_exito(df):
    """Dispersão: um ponto por setor, taxa de acordo contra taxa de êxito; o tamanho é o nº de processos."""
    _preparar()
    s = calcular_acordo_e_exito_por_setor(df)
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.scatter(s.acordo, s.taxa_exito, s=s.total / 3 + 30, color=BLUE, alpha=.75, edgecolor="white", linewidth=2)
    # Deslocamento do rótulo, em pontos. Esses três foram ajustados à mão para esta base,
    # para não se sobreporem; com outra base, confira se os rótulos continuam legíveis.
    off = {"Ensino": (-8, 10, "right"), "Telecomunicações": (8, -12, "left"), "Energia": (-10, 8, "right")}
    for nome, r in s.iterrows():
        ax.annotate(nome, (r.acordo, r.taxa_exito), xytext=off.get(nome, (7, 5, "left"))[:2],
                    ha=off.get(nome, (7, 5, "left"))[2], textcoords="offset points", fontsize=8.5, color=INK)
    ax.xaxis.set_major_formatter(_pct); ax.yaxis.set_major_formatter(_pct)
    ax.grid(True, color=GRID); ax.set_axisbelow(True)
    ax.set_xlabel("Taxa de acordo (% dos processos do setor com resultado)")
    ax.set_ylabel("Taxa de êxito do autor (entre decididos no mérito)")
    ax.set_title("Acordo contra êxito por setor (tamanho = nº de processos)", loc="left", color=INK, fontsize=13)
    fig.tight_layout()
    return fig


GRAFICOS = {
    "grafico_cobertura.png": grafico_cobertura,
    "grafico_setor.png": grafico_exito_intervalo,
    "grafico_ano.png": grafico_exito_por_ano,
    "grafico_barras_setor.png": grafico_barras_setor,
    "grafico_resultados_ano.png": grafico_resultados_por_ano,
    "grafico_acordo_exito.png": grafico_acordo_exito,
}


def salvar_graficos(df, pasta=PASTA_GRAFICOS):
    """Grava os seis gráficos em PNG na pasta indicada (por padrão, graficos/) e devolve os caminhos."""
    pasta = Path(pasta)
    pasta.mkdir(exist_ok=True)
    caminhos = []
    for nome, funcao in GRAFICOS.items():
        fig = funcao(df)
        fig.savefig(pasta / nome, dpi=160)
        plt.close(fig)
        caminhos.append(pasta / nome)
    return caminhos


# ------------------------------------------------------------------------------- tudo junto

def main():
    processos = carregar_processos()
    print(resumo_cobertura(processos).to_string(), end="\n\n")

    print("Taxa de êxito do autor por setor")
    tabela = calcular_taxa_exito_por_setor(processos)
    print(tabela.to_string(float_format=lambda x: f"{x:.3f}"), end="\n\n")

    print(f"Taxa de êxito do autor por ano (anos com {MINIMO_CASOS_ANO} casos ou mais)")
    print(calcular_taxa_exito_por_ano(processos).to_string(float_format=lambda x: f"{x:.3f}"), end="\n\n")

    print("Taxa de acordo e taxa de êxito por setor")
    s = calcular_acordo_e_exito_por_setor(processos)
    print(s[["acordo", "taxa_exito", "total"]].to_string(float_format=lambda x: f"{x:.2f}"), end="\n\n")

    if plt is None:
        print("Gráficos não gerados: o matplotlib não está instalado.")
        print("Instale com: python -m pip install matplotlib")
        return
    print("Gráficos gravados")
    for caminho in salvar_graficos(processos):
        print(caminho.relative_to(PASTA))


if __name__ == "__main__":
    main()
