"""Estilo único e funções de gráfico reutilizadas pelos cadernos (PNG estático, 300 dpi)."""
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, Normalize

from mama import codigos as c
from mama.config import FIGURAS

SUPERFICIE, TEXTO, TEXTO_2, GRADE = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
CINZA = "#b4b2ab"  # reservado para "Sem informação"
# Paleta categórica em ordem fixa (validada para daltonismo em pares adjacentes)
CATEGORICAS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
COR_REGIAO = dict(zip(c.REGIOES, CATEGORICAS))
AZUL = CATEGORICAS[0]
AZUL_SEQ = LinearSegmentedColormap.from_list(
    "azul", ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"])

mpl.rcParams.update({
    "figure.facecolor": SUPERFICIE, "axes.facecolor": SUPERFICIE, "savefig.facecolor": SUPERFICIE,
    "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.edgecolor": GRADE, "axes.labelcolor": TEXTO_2, "xtick.color": TEXTO_2, "ytick.color": TEXTO_2,
    "text.color": TEXTO, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRADE, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "lines.linewidth": 2, "legend.frameon": False, "figure.dpi": 100, "savefig.dpi": 300,
})


def salvar(fig, nome: str, fonte: str):
    """Grava figures/<nome>.png com a fonte dos dados abaixo de todo o conteúdo."""
    fig.canvas.draw()
    base = fig.get_tightbbox().y0 / fig.get_figheight()
    fig.text(0.01, base - 0.02, f"Fonte: {fonte}", fontsize=7.5, color=TEXTO_2, ha="left", va="top")
    FIGURAS.mkdir(exist_ok=True)
    fig.savefig(FIGURAS / f"{nome}.png", bbox_inches="tight")
    return fig


def texto_sobre(cor) -> str:
    """Branco sobre fundos escuros, preto sobre fundos claros (luminância relativa)."""
    r, g_, b = mpl.colors.to_rgb(cor)
    return "white" if 0.2126 * r + 0.7152 * g_ + 0.0722 * b < 0.45 else TEXTO


def _cores(grupos, cores=None):
    if cores:
        return cores
    if set(grupos) <= set(c.REGIOES):
        return COR_REGIAO
    return dict(zip(grupos, CATEGORICAS))


def barras_h(serie, titulo, rotulo_x, fmt="{:.1f}", ref=None, ref_rotulo=None, figsize=(6.6, 3.3)):
    """Barras horizontais de uma série; a ordem do índice é mantida de cima para baixo."""
    s = serie.iloc[::-1]
    fig, ax = plt.subplots(figsize=figsize)
    ax.barh(s.index.astype(str), s.values, color=AZUL, height=0.6, edgecolor=SUPERFICIE, linewidth=2)
    for y, v in enumerate(s.values):
        ax.text(v, y, " " + fmt.format(v), va="center", fontsize=9)
    if ref is not None:
        ax.axvline(ref, color=TEXTO_2, lw=1, ls="--")
        ax.text(ref, len(s) - 0.45, f" {ref_rotulo}", fontsize=8, color=TEXTO_2)
    ax.set(title=titulo, xlabel=rotulo_x, xlim=(0, s.max() * 1.18))
    ax.grid(axis="y", visible=False)
    return fig, ax


def empilhadas_100(tabela, titulo, rotulo_x="% das pacientes", cores=None, minimo_rotulo=6, figsize=(7.2, 3.4)):
    """Barras 100% empilhadas: linhas da tabela são as barras, colunas são as categorias."""
    t = tabela.iloc[::-1]
    cats = list(t.columns)
    paleta = cores or {k: (CINZA if k == c.SEM_INFO else v) for k, v in zip(cats, CATEGORICAS)}
    fig, ax = plt.subplots(figsize=figsize)
    esq = np.zeros(len(t))
    for cat in cats:
        v = t[cat].values
        ax.barh(t.index.astype(str), v, left=esq, color=paleta[cat], height=0.62, edgecolor=SUPERFICIE,
                linewidth=2, label=cat)
        for y, (x0, w) in enumerate(zip(esq, v)):
            if w >= minimo_rotulo:
                ax.text(x0 + w / 2, y, f"{w:.0f}%", ha="center", va="center", fontsize=8,
                        color=texto_sobre(paleta[cat]))
        esq += v
    ax.set(title=titulo, xlabel=rotulo_x, xlim=(0, 100))
    ax.legend(ncol=min(len(cats), 3), loc="upper left", bbox_to_anchor=(0, -0.2), fontsize=8)
    ax.grid(visible=False)
    return fig, ax


def pontos_ic(t, categoria, grupo, titulo, rotulo_x, ordem_cat=None, ordem_grupo=None, cores=None, figsize=(6.8, 3.6)):
    """Pontos com IC 95% (colunas pct, ic_inf, ic_sup); um ponto por categoria e grupo."""
    cats = ordem_cat or list(dict.fromkeys(t[categoria]))
    grupos = ordem_grupo or list(dict.fromkeys(t[grupo]))
    paleta = _cores(grupos, cores)
    fig, ax = plt.subplots(figsize=figsize)
    desloc = np.linspace(0.18, -0.18, len(grupos)) if len(grupos) > 1 else [0]
    pos = np.arange(len(cats))[::-1]
    for g, dy in zip(grupos, desloc):
        s = t[t[grupo] == g].set_index(categoria).reindex(cats)
        y = pos + dy
        ax.errorbar(s.pct, y, xerr=[s.pct - s.ic_inf, s.ic_sup - s.pct], fmt="o", ms=7, color=paleta[g],
                    elinewidth=1.5, capsize=0, label=g, markeredgecolor=SUPERFICIE)
        for yy, v, sup in zip(y, s.pct, s.ic_sup):
            if np.isfinite(v):
                ax.text(sup + 0.4, yy, f"{v:.0f}%", va="center", fontsize=8)
    ax.set_yticks(pos, cats)
    ax.set(title=titulo, xlabel=rotulo_x)
    ax.grid(axis="y", visible=False)
    if len(grupos) > 1:
        ax.legend(loc="upper left", bbox_to_anchor=(0, -0.18), ncol=len(grupos), fontsize=8)
    return fig, ax


def _rotulos_finais(ax, finais, xmax, xmin, ymin, ymax, fmt):
    """Rótulo direto no fim de cada linha, afastando os que se sobrepõem."""
    finais.sort()
    passo = (ymax - ymin) * 0.07
    for i in range(1, len(finais)):
        finais[i][1] = max(finais[i][1], finais[i - 1][1] + passo)
    if finais:
        finais[-1][1] = min(finais[-1][1], ymax)
    for i in range(len(finais) - 2, -1, -1):
        finais[i][1] = min(finais[i][1], finais[i + 1][1] - passo)
    for valor, pos, nome in finais:
        ax.text(xmax + (xmax - xmin) * 0.02, pos, f"{nome} {fmt.format(valor)}", va="center", fontsize=8)


def linhas(df, x, y, grupo, titulo, rotulo_y, fmt="{:.1f}", ordem=None, cores=None, ax=None, legenda=True,
           figsize=(7, 3.8), rotulo_x=None, rotulos_finais=True):
    """Uma linha por grupo; por padrão, rótulo direto com o valor do último ponto."""
    grupos = ordem or list(dict.fromkeys(df[grupo]))
    paleta = _cores(grupos, cores)
    fig, ax = (ax.figure, ax) if ax is not None else plt.subplots(figsize=figsize)
    finais = []
    for g in grupos:
        d = df[df[grupo] == g].sort_values(x)
        if d.empty:
            continue
        ax.plot(d[x], d[y], color=paleta[g], marker="o", ms=3.5, label=g)
        finais.append([d[y].iloc[-1], d[y].iloc[-1], g])
    xmin, xmax = df[x].min(), df[x].max()
    if rotulos_finais:
        _rotulos_finais(ax, finais, xmax, xmin, df[y].min(), df[y].max(), fmt)
        ax.set_xlim(xmin - (xmax - xmin) * 0.02, xmax + (xmax - xmin) * 0.25)
        if np.issubdtype(np.asarray(df[x]).dtype, np.number) and xmax - xmin > 3:
            ax.set_xticks(range(int(xmin), int(xmax) + 1, 2))
    ax.set(title=titulo, ylabel=rotulo_y)
    if rotulo_x:
        ax.set_xlabel(rotulo_x)
    if legenda and len(grupos) > 1:
        ax.legend(ncol=min(len(grupos), 5), loc="upper left", bbox_to_anchor=(0, -0.22 if rotulo_x else -0.12),
                  fontsize=8)
    return fig, ax


def mapa_uf(valores, titulo, rotulo, ax=None, norm=None, fmt="{:.0f}", barra=True):
    """Coroplético por UF (valores indexados pela sigla), com rótulos externos nas UFs pequenas."""
    from mama.fontes.geografia import ufs
    valores = valores.astype("float64").rename("valor")
    g = ufs().merge(valores, left_on="uf", right_index=True, how="left")
    g["valor"] = g.valor.astype("float64")
    fig, ax = (ax.figure, ax) if ax is not None else plt.subplots(figsize=(6.4, 6.4))
    norm = norm or Normalize(g.valor.min(), g.valor.max())
    g.plot(column="valor", cmap=AZUL_SEQ, norm=norm, ax=ax, edgecolor=SUPERFICIE, linewidth=0.8,
           missing_kwds={"color": CINZA})
    for _, r in g.iterrows():
        if not np.isfinite(r.valor):
            continue
        p = r.geometry.representative_point()
        txt = fmt.format(r.valor)
        if r.uf in ROTULO_EXTERNO:
            dx, dy = ROTULO_EXTERNO[r.uf]
            ax.annotate(f"{r.uf} {txt}", (p.x, p.y), xytext=(p.x + dx, p.y + dy), fontsize=6.5, va="center",
                        arrowprops=dict(arrowstyle="-", color=TEXTO_2, lw=0.6))
        else:
            escuro = norm(r.valor) >= 0.6
            ax.text(p.x, p.y, f"{r.uf}\n{txt}", ha="center", va="center", fontsize=6.5,
                    color="white" if escuro else TEXTO)
    if barra:
        sm = mpl.cm.ScalarMappable(norm=norm, cmap=AZUL_SEQ)
        cb = fig.colorbar(sm, ax=ax, shrink=0.55, pad=0.02)
        cb.set_label(rotulo, fontsize=8)
        cb.ax.tick_params(labelsize=8)
    ax.set_axis_off()
    ax.set_title(titulo)
    return fig, ax


# Deslocamento (graus) do rótulo das UFs pequenas demais para o texto caber dentro
ROTULO_EXTERNO = {"RN": (3.5, 1.0), "PB": (4.0, 0.0), "PE": (4.5, -0.9), "AL": (4.0, -1.6),
                  "SE": (4.0, -2.3), "DF": (12.5, -1.5), "ES": (3.5, -0.5), "RJ": (3.0, -2.0)}


def mapas_uf_multiplos(series: dict, titulo, rotulo, fmt="{:.0f}", ncol=3):
    """Vários coropléticos lado a lado com a mesma escala de cor (comparáveis entre si)."""
    vmin = min(float(s.min()) for s in series.values())
    vmax = max(float(s.max()) for s in series.values())
    norm = Normalize(vmin, vmax)
    nlin = int(np.ceil(len(series) / ncol))
    fig, axes = plt.subplots(nlin, ncol, figsize=(4.2 * ncol, 4.4 * nlin))
    axes = np.atleast_1d(axes).ravel()
    for ax, (nome, s) in zip(axes, series.items()):
        mapa_uf(s, nome, rotulo, ax=ax, norm=norm, fmt=fmt, barra=False)
        ax.title.set_fontsize(10)
    for ax in axes[len(series):]:
        ax.set_axis_off()
    sm = mpl.cm.ScalarMappable(norm=norm, cmap=AZUL_SEQ)
    cb = fig.colorbar(sm, ax=axes.tolist(), shrink=0.5, orientation="horizontal", pad=0.03, aspect=40)
    cb.set_label(rotulo, fontsize=9)
    fig.suptitle(titulo, x=0.02, ha="left", fontweight="bold", fontsize=12)
    return fig, axes


def mapa_pontos(pontos, tamanho, titulo, rotulo_tamanho, cor=AZUL, escala=None, ax=None, legenda_valores=None):
    """Círculos proporcionais sobre o contorno das UFs (pontos com colunas lat, lon e `tamanho`)."""
    from mama.fontes.geografia import ufs
    fig, ax = (ax.figure, ax) if ax is not None else plt.subplots(figsize=(6.4, 6.4))
    ufs().plot(ax=ax, color="#f0efec", edgecolor="#cfcdc6", linewidth=0.6)
    escala = escala or 300 / max(pontos[tamanho].max(), 1)
    ax.scatter(pontos.lon, pontos.lat, s=pontos[tamanho] * escala, color=cor, alpha=0.55,
               edgecolor=SUPERFICIE, linewidth=0.6)
    for v in legenda_valores or []:
        ax.scatter([], [], s=v * escala, color=cor, alpha=0.55, label=f"{v:g}")
    if legenda_valores:
        ax.legend(title=rotulo_tamanho, loc="lower left", fontsize=7, title_fontsize=8, labelspacing=1.2,
                  borderpad=1)
    ax.set_axis_off()
    ax.set_title(titulo)
    return fig, ax


def calor(tabela, titulo, rotulo, fmt="{:.0f}", figsize=(8, 3.2), vmin=None, vmax=None, textos=None):
    """Mapa de calor sequencial (linhas x colunas) com o valor escrito em cada célula.

    vmin/vmax limitam a escala de cor (valores fora dela ficam com a cor do extremo), útil quando
    poucos valores extremos achatariam o contraste do restante. `textos` (mesma forma da tabela)
    permite colorir por uma medida e escrever outra, por exemplo cor relativa e valor absoluto.
    """
    fig, ax = plt.subplots(figsize=figsize)
    v = tabela.values.astype(float)
    escrito = (textos if textos is not None else tabela).values.astype(float)
    im = ax.imshow(v, cmap=AZUL_SEQ, aspect="auto", vmin=vmin, vmax=vmax)
    norm = im.norm
    for i in range(v.shape[0]):
        for j in range(v.shape[1]):
            ax.text(j, i, fmt.format(escrito[i, j]), ha="center", va="center", fontsize=7.5,
                    color="white" if norm(v[i, j]) >= 0.6 else TEXTO)
    ax.set_xticks(range(v.shape[1]), tabela.columns)
    ax.set_yticks(range(v.shape[0]), tabela.index)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.01)
    cb.set_label(rotulo, fontsize=8)
    ax.set_title(titulo)
    return fig, ax


def mapa_municipios(valores, titulo, rotulo, limites, rotulos_classes, cores=None):
    """Coroplético por município em classes (ex.: faixas de distância), com contorno das UFs."""
    import geopandas as gpd

    from mama.fontes.geografia import MUNICIPIOS_GEO, ufs
    m = gpd.read_file(MUNICIPIOS_GEO)
    m["mun"] = m.codarea.str[:6]
    m["classe"] = pd.cut(m.mun.map(valores).astype(float), limites, labels=rotulos_classes)
    cores = cores or dict(zip(rotulos_classes, ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]))
    fig, ax = plt.subplots(figsize=(6.8, 6.8))
    for classe in rotulos_classes:
        sel = m[m.classe == classe]
        if not sel.empty:
            sel.plot(ax=ax, color=cores[classe], linewidth=0)
    ufs().boundary.plot(ax=ax, color=SUPERFICIE, linewidth=0.7)
    alcas = [mpl.patches.Patch(color=cores[k], label=k) for k in rotulos_classes]
    ax.legend(handles=alcas, title=rotulo, loc="lower left", fontsize=7.5, title_fontsize=8)
    ax.set_axis_off()
    ax.set_title(titulo)
    return fig, ax
