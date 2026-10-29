"""Distância entre o município onde a paciente mora e onde é tratada, e acesso geográfico aos centros."""
import numpy as np
import pandas as pd

from mama import codigos as c
from mama import harmonizacao as h
from mama.analises.base import carregar

FAIXAS_KM = [-0.1, 0.1, 50, 150, 300, 100_000]
FAIXAS_KM_ROTULOS = ["No próprio município", "Até 50 km", "50 a 150 km", "150 a 300 km", "Mais de 300 km"]


def adicionar_distancia(d: pd.DataFrame, col_origem: str, col_destino: str) -> pd.DataFrame:
    """Distância em linha reta entre os centroides dos dois municípios (0 se forem o mesmo)."""
    m = carregar("municipios").set_index("mun")[["lat", "lon"]]
    o = m.reindex(d[col_origem]).to_numpy()
    t = m.reindex(d[col_destino]).to_numpy()
    km = h.distancia_km(o[:, 0], o[:, 1], t[:, 0], t[:, 1])
    mesmo = (d[col_origem] == d[col_destino]).fillna(False).to_numpy(dtype=bool)
    km = np.where(mesmo, 0.0, km)
    out = d.copy()
    out["distancia_km"] = km
    out["faixa_distancia"] = pd.cut(out.distancia_km, FAIXAS_KM, labels=FAIXAS_KM_ROTULOS)
    return out


def distribuicao_distancia(d: pd.DataFrame, por: str = "regiao_res") -> pd.DataFrame:
    x = d.dropna(subset=["faixa_distancia"])
    t = pd.crosstab(x[por], x.faixa_distancia, normalize="index").mul(100).round(1)
    t = t.reindex(columns=FAIXAS_KM_ROTULOS, fill_value=0)
    return t.reindex([r for r in c.REGIOES if r in t.index]) if por.startswith("regiao") else t


def resumo_distancia(d: pd.DataFrame, por: list[str]) -> pd.DataFrame:
    x = d.dropna(subset=["distancia_km"])
    g = x.groupby(por, observed=True).distancia_km
    return g.agg(n="size", pct_outro_municipio=lambda s: (s > 0).mean() * 100,
                 mediana_km_quem_viaja=lambda s: s[s > 0].median(),
                 pct_mais_150km=lambda s: (s > 150).mean() * 100,
                 pct_mais_300km=lambda s: (s > 300).mean() * 100).reset_index().round(1)


def polos_de_atendimento(d: pd.DataFrame, col_origem: str, col_destino: str, n: int = 15) -> pd.DataFrame:
    """Municípios que mais recebem pacientes de outros municípios."""
    x = d.dropna(subset=[col_origem, col_destino])
    x = x[x[col_origem] != x[col_destino]]
    t = x.groupby(col_destino).agg(pacientes_de_fora=(col_origem, "size"), municipios_de_origem=(col_origem, "nunique"))
    nomes = carregar("municipios").set_index("mun")
    t = t.join(nomes[["nome", "uf", "lat", "lon"]]).sort_values("pacientes_de_fora", ascending=False)
    return t.head(n).reset_index().rename(columns={col_destino: "mun"})


def distancia_ao_mais_proximo(municipios_alvo) -> pd.DataFrame:
    """Para cada município do país: distância em linha reta até o município mais próximo da lista."""
    mun = carregar("municipios")
    alvo = mun[mun.mun.isin(set(municipios_alvo))]
    la1, lo1 = np.radians(mun.lat.to_numpy())[:, None], np.radians(mun.lon.to_numpy())[:, None]
    la2, lo2 = np.radians(alvo.lat.to_numpy())[None, :], np.radians(alvo.lon.to_numpy())[None, :]
    a = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
    dist = 2 * 6371 * np.arcsin(np.sqrt(a))
    out = mun.copy()
    out["km_servico_mais_proximo"] = dist.min(axis=1)
    out["municipio_servico_mais_proximo"] = alvo.nome.to_numpy()[dist.argmin(axis=1)]
    pop = carregar("populacao_municipio")
    return out.merge(pop, on="mun", how="left")


def distancia_ao_servico_mais_proximo(servico: str = "UNACON/CACON", competencia: str | None = None) -> pd.DataFrame:
    """Distância de cada município até o município mais próximo com o serviço oncológico habilitado."""
    from mama.analises.rede import municipios_com_servico
    from mama.config import COMPETENCIA_CNES
    alvo = municipios_com_servico(competencia or COMPETENCIA_CNES)
    return distancia_ao_mais_proximo(alvo[alvo.servico == servico].mun)


def distancias_por_tratamento() -> pd.DataFrame:
    """Distância casa-serviço para cada etapa do cuidado, juntando as fontes que registram as duas pontas.

    Cirurgia como primeiro tratamento: Painel de Oncologia; quimioterapia, hormonioterapia e anti-HER2:
    APAC de quimioterapia; radioterapia: APAC de radioterapia. A mamografia fica de fora porque o
    SISCAN público não informa o município onde o exame foi feito.
    """
    from mama.analises import base
    partes = []
    p = base.painel()
    p = p[p.tratamento == "Cirurgia"]
    partes.append(pd.DataFrame({"tipo": "Cirurgia", "regiao_res": p.regiao_res, "mun_res": p.mun_res,
                                "mun_trat": p.mun_trat}))
    q = carregar("apac_quimio_tratamentos")
    partes.append(q[["tipo", "regiao_res", "mun_res", "mun_trat"]])
    r = carregar("apac_radio_pacientes")
    partes.append(pd.DataFrame({"tipo": "Radioterapia", "regiao_res": r.regiao_res, "mun_res": r.mun_res,
                                "mun_trat": r.mun_trat}))
    d = pd.concat(partes, ignore_index=True).dropna(subset=["regiao_res", "mun_res", "mun_trat"])
    return adicionar_distancia(d, "mun_res", "mun_trat")


def populacao_por_faixa_de_distancia(t: pd.DataFrame, col_pop: str = "mulheres_50_69") -> pd.DataFrame:
    """% das mulheres de cada região que vivem em cada faixa de distância do serviço mais próximo."""
    faixas = [-0.1, 0.1, 50, 150, 300, 100_000]
    t = t.assign(faixa=pd.cut(t.km_servico_mais_proximo, faixas, labels=FAIXAS_KM_ROTULOS))
    p = t.pivot_table(index="regiao", columns="faixa", values=col_pop, aggfunc="sum", observed=False)
    p = p.div(p.sum(axis=1), axis=0).mul(100).round(1)
    return p.reindex(c.REGIOES).rename(columns={"No próprio município": "Serviço no próprio município"})
