"""Rede de serviços: natureza dos hospitais (público, filantrópico, privado) e oferta no território (CNES)."""
import pandas as pd

from mama import codigos as c
from mama.analises.base import carregar
from mama.config import COMPETENCIA_CNES

ORDEM_NATUREZA = ["Público", "Filantrópico/sem fins lucrativos", "Privado"]


def natureza_por_cnes() -> pd.Series:
    """Natureza jurídica de cada estabelecimento, pela competência mais recente em que aparece."""
    e = carregar("cnes_estabelecimentos").sort_values("competencia")
    return e.drop_duplicates("CNES", keep="last").set_index("CNES").natureza


def com_natureza(d: pd.DataFrame, col_cnes: str) -> pd.DataFrame:
    """Acrescenta a natureza do estabelecimento indicado em `col_cnes`."""
    return d.assign(natureza=d[col_cnes].map(natureza_por_cnes()).fillna(c.SEM_INFO))


def oferta_por_uf(competencia: str = COMPETENCIA_CNES) -> pd.DataFrame:
    """Quantidade absoluta de serviços por UF numa competência, e por 100 mil mulheres."""
    e = carregar("cnes_estabelecimentos").query("competencia == @competencia")
    m = carregar("cnes_equipamentos").query("competencia == @competencia and equipamento == 'Mamógrafo'")
    hb = carregar("cnes_habilitacoes").query("competencia == @competencia")
    pop = carregar("populacao_uf")
    pop = pop[pop.ano == pop.ano.max()]

    t = pd.DataFrame({
        "unidades_atencao_primaria": e[e.atencao_primaria].groupby("uf").size(),
        "mamografos": m.groupby("uf").qt_existente.sum(),
        "mamografos_sus": m.groupby("uf").qt_sus.sum(),
    })
    for servico in c.HABILITACOES:
        t[servico] = hb[hb.servico == servico].groupby("uf").CNES.nunique()
    t = t.fillna(0).astype(int)
    t["mulheres"] = pop.groupby("uf")["pop"].sum()
    t["mulheres_50_69"] = pop[pop.faixa5.between(50, 65)].groupby("uf")["pop"].sum()
    t["regiao"] = t.index.map(c.SIGLA_PARA_REGIAO)
    t.index.name = "uf"
    return t.reset_index()


def oferta_por_regiao(competencia: str = COMPETENCIA_CNES) -> pd.DataFrame:
    t = oferta_por_uf(competencia).drop(columns="uf").groupby("regiao").sum().reindex(c.REGIOES)
    t["mamografos_sus_por_100mil_50_69"] = (t.mamografos_sus / t.mulheres_50_69 * 1e5).round(1)
    t["unacon_cacon_por_milhao"] = (t["UNACON/CACON"] / t.mulheres * 1e6).round(2)
    t["atencao_primaria_por_100mil"] = (t.unidades_atencao_primaria / t.mulheres * 1e5).round(1)
    return t


def evolucao_oferta() -> pd.DataFrame:
    """Serviços oncológicos e mamógrafos SUS por região em cada competência baixada."""
    linhas = []
    for comp in sorted(carregar("cnes_habilitacoes").competencia.unique()):
        t = oferta_por_regiao(comp).reset_index().assign(competencia=comp, ano=2000 + int(comp[:2]))
        linhas.append(t)
    return pd.concat(linhas, ignore_index=True)


def municipios_com_servico(competencia: str = COMPETENCIA_CNES) -> pd.DataFrame:
    """Lista de municípios que têm cada serviço oncológico (com número de estabelecimentos)."""
    hb = carregar("cnes_habilitacoes").query("competencia == @competencia")
    return hb.groupby(["servico", "mun", "uf", "regiao"]).CNES.nunique().rename("estabelecimentos").reset_index()
