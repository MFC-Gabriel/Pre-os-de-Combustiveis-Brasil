"""Figuras estáticas produzidas a partir das mesmas séries do artigo."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, PercentFormatter
import numpy as np

INK = "#172b28"
MUTED = "#566361"
TEAL = "#1b7467"
ORANGE = "#ad502d"


def sparkline(series, path):
    peak = series.idxmax()
    period = series.loc["2021":]
    fig, ax = plt.subplots(figsize=(6, 1.8), dpi=190)
    fig.subplots_adjust(left=0.04, right=0.96, top=0.88, bottom=0.16)
    ax.plot(period.index, period, color="#a7ebc7", linewidth=3.4)
    ax.fill_between(
        period.index, period.to_numpy(), 4, color="#a7ebc7", alpha=0.13,
    )
    ax.axvline(peak, linestyle=(0, (3, 4)), color="#a7ebc7", alpha=0.65, linewidth=1)
    ax.scatter([peak], [period.loc[peak]], color="#d9f8df", edgecolors="#203b35", s=78, zorder=5)
    ax.axhline(4, color="#c9e2d6", alpha=0.28, linewidth=1)
    ax.set_xlim(period.index.min(), period.index.max())
    ax.set_ylim(3.95, 7.85)
    ax.set_axis_off()
    fig.savefig(path, transparent=True)
    plt.close(fig)


def histograma_variacoes(report, path):
    values = report["gasolina_var_pct"]
    minimum = values.min()
    left = report["limite_inferior_pct"].iloc[0]
    right = report["limite_superior_pct"].iloc[0]
    edges = np.arange(np.floor(minimum) - 0.5, np.ceil(values.max()) + 1.5, 1)
    marked = report["fora_dos_limites_iqr"]
    regular, _ = np.histogram(values.loc[~marked], bins=edges)
    extreme, _ = np.histogram(values.loc[marked], bins=edges)
    counts = regular + extreme
    centers = (edges[:-1] + edges[1:]) / 2
    colors = ["#acc2bb"] * len(centers)
    colors[0] = ORANGE

    fig, ax = plt.subplots(figsize=(10, 4.0), dpi=190)
    fig.subplots_adjust(left=0.11, right=0.975, top=0.91, bottom=0.22)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color="#dce5e0", linewidth=0.9)
    ax.bar(centers, regular, width=0.86, color=TEAL)
    ax.bar(centers, extreme, bottom=regular, width=0.86, color=colors)
    for limit in (left, right):
        ax.axvline(limit, linestyle=(0, (4, 3)), color="#526c65", linewidth=1.0)
    ax.text(
        0.5, 1.015, "Limites de Tukey", transform=ax.transAxes,
        horizontalalignment="center", color=MUTED, fontsize=11,
    )
    min_label = f"{minimum:.2f}".replace(".", ",").replace("-", "−")
    date = values.idxmin()
    months = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    ax.annotate(
        f"{months[date.month - 1]}/{date.year}\n{min_label}%",
        xy=(centers[0], counts[0]), xytext=(centers[0] + 0.7, max(counts) * 0.38),
        color=ORANGE, fontsize=11, fontweight="semibold",
        arrowprops={"arrowstyle": "-", "color": ORANGE, "linewidth": 1},
    )
    ax.set_xlim(edges[0] - 0.7, edges[-1] + 0.2)
    ax.set_ylim(0, max(counts) * 1.13)
    ax.set_xticks(np.arange(-15, 14, 5))
    ax.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    ax.yaxis.set_major_locator(MaxNLocator(5, integer=True))
    ax.set_xlabel("Variação em relação ao mês anterior", color=INK, fontsize=12, labelpad=10)
    ax.set_ylabel("Quantidade de meses", color=INK, fontsize=12, labelpad=10)
    ax.tick_params(colors=MUTED, labelsize=11, length=0, pad=6)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#bcc9c4")
    fig.savefig(path, facecolor="white")
    plt.close(fig)
