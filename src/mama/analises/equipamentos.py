"""Equipamentos de diagnóstico por imagem (CNES): quantidade, uso, disponibilidade ao SUS e vazios."""
import pandas as pd

from mama import codigos as c
from mama.analises.base import carregar
from mama.config import COMPETENCIA_CNES


def _habitantes(ano: int) -> pd.Series:
    pop = carregar("populacao_total_uf")
    ano = min(ano, int(pop.ano.max()))
    return pop[pop.ano == ano].set_index("uf")["pop"]


def por_uf(competencia: str = COMPETENCIA_CNES) -> pd.DataFrame:
    """Por UF e tipo de equipamento: existentes, em uso, disponíveis ao SUS, por 100 mil habitantes."""
    e = carregar("cnes_equipamentos").query("competencia == @competencia")
    t = e.groupby(["uf", "equipamento"])[["qt_existente", "qt_em_uso", "qt_sus", "qt_em_uso_sus"]].sum().reset_index()
    t["habitantes"] = t.uf.map(_habitantes(2000 + int(competencia[:2])))
    t["regiao"] = t.uf.map(c.SIGLA_PARA_REGIAO)
    return t


def _indicadores(t: pd.DataFrame) -> pd.DataFrame:
    t = t.copy()
    t["em_uso_por_100mil_hab"] = (t.qt_em_uso / t.habitantes * 1e5).round(2)
    t["em_uso_sus_por_100mil_hab"] = (t.qt_em_uso_sus / t.habitantes * 1e5).round(2)
    t["pct_disponivel_sus"] = (t.qt_sus / t.qt_existente * 100).round(1)
    return t


def por_regiao(competencia: str = COMPETENCIA_CNES) -> pd.DataFrame:
    t = por_uf(competencia)
    hab = t.drop_duplicates("uf").groupby("regiao").habitantes.sum()
    g = t.groupby(["regiao", "equipamento"])[["qt_existente", "qt_em_uso", "qt_sus", "qt_em_uso_sus"]].sum().reset_index()
    g["habitantes"] = g.regiao.map(hab)
    return _indicadores(g)


def brasil(competencia: str = COMPETENCIA_CNES) -> pd.DataFrame:
    t = por_uf(competencia)
    hab = t.drop_duplicates("uf").habitantes.sum()
    g = t.groupby("equipamento")[["qt_existente", "qt_em_uso", "qt_sus", "qt_em_uso_sus"]].sum().reset_index()
    g["habitantes"] = hab
    return _indicadores(g)


def municipios_com_equipamento_sus(equipamento: str, competencia: str = COMPETENCIA_CNES) -> set:
    e = carregar("cnes_equipamentos").query("competencia == @competencia and equipamento == @equipamento")
    return set(e[e.qt_sus > 0].mun.dropna())


def municipios_sem_equipamento_sus(competencia: str = COMPETENCIA_CNES) -> pd.DataFrame:
    """Por região e equipamento: municípios sem nenhum aparelho disponível ao SUS e quanta gente vive neles."""
    mun = carregar("municipios").merge(carregar("populacao_municipio"), on="mun", how="left")
    linhas = []
    for eq in c.EQUIPAMENTOS:
        tem = mun.mun.isin(municipios_com_equipamento_sus(eq, competencia))
        g = mun.assign(sem_equip=~tem).groupby("regiao")
        linhas.append(pd.DataFrame({
            "equipamento": eq,
            "municipios": g.size(),
            "municipios_sem_sus": g.sem_equip.sum(),
            "pct_municipios_sem_sus": (g.sem_equip.mean() * 100).round(1),
            "pct_habitantes_em_municipio_sem_sus": (g.apply(lambda x: x.habitantes[x.sem_equip].sum() / x.habitantes.sum(),
                                                            include_groups=False) * 100).round(1),
        }).reset_index())
    return pd.concat(linhas, ignore_index=True)


def evolucao(equipamentos=("Mamógrafo", "Tomógrafo", "Ressonância magnética")) -> pd.DataFrame:
    """Equipamentos em uso disponíveis ao SUS por 100 mil habitantes, por região, em cada competência."""
    linhas = []
    for comp in sorted(carregar("cnes_equipamentos").competencia.unique()):
        t = por_regiao(comp)
        linhas.append(t[t.equipamento.isin(equipamentos)].assign(ano=2000 + int(comp[:2])))
    return pd.concat(linhas, ignore_index=True)
