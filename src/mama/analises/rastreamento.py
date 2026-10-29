"""Rastreamento e diagnóstico no SUS (SISCAN): mamografias e laudos de histopatologia."""
import pandas as pd

from mama import codigos as c
from mama.analises.base import carregar, proporcao


def mamografias() -> pd.DataFrame:
    d = carregar("siscan_mamografia")
    return d[d.regiao_res.notna()].copy()


def histopatologia() -> pd.DataFrame:
    d = carregar("siscan_histopatologia")
    return d[d.regiao_res.notna()].copy()


def cobertura_rastreamento(m: pd.DataFrame) -> pd.DataFrame:
    """Mamografias de rastreamento em mulheres de 50 a 69 anos dividido pela metade dessa população.

    A recomendação do Ministério da Saúde é uma mamografia a cada dois anos nessa faixa; por isso,
    num ano, a meta é examinar metade das mulheres. O resultado é uma razão de exames, não uma
    cobertura exata (uma mulher pode fazer mais de um exame, e exames fora do SISCAN não entram).
    """
    x = m[(m.indicacao == "Rastreamento") & m.idade.between(50, 69)]
    exames = x.groupby(["ano", "regiao_res"], observed=True).size().rename("mamografias_rastreamento_50_69")
    pop = carregar("populacao_uf")
    pop = pop[pop.faixa5.between(50, 65)].groupby(["ano", "regiao"])["pop"].sum().rename("mulheres_50_69")
    pop.index.names = ["ano", "regiao_res"]
    t = pd.concat([exames, pop], axis=1, join="inner").reset_index()
    t["razao_pct_da_meta"] = (t.mamografias_rastreamento_50_69 / (t.mulheres_50_69 / 2) * 100).round(1)
    t["regiao_res"] = pd.Categorical(t.regiao_res, c.REGIOES, ordered=True)
    return t.sort_values(["ano", "regiao_res"])


def birads_suspeito(m: pd.DataFrame, por: list[str]) -> pd.DataFrame:
    """% de mamografias com BI-RADS 4 ou 5 (achado suspeito ou altamente suspeito de câncer)."""
    x = m[m.birads.notna()].assign(suspeito=lambda t: t.birads.isin(["4", "5"]).astype("Int8"))
    return proporcao(x, "suspeito", por)


def receptor_hormonal(hp: pd.DataFrame, por: list[str]) -> pd.DataFrame:
    """% de tumores com receptor hormonal positivo (estrogênio ou progesterona), entre os testados."""
    x = hp[hp.receptor_hormonal.notna()].assign(positivo=lambda t: (t.receptor_hormonal == "Positivo").astype("Int8"))
    return proporcao(x, "positivo", por)


def palpavel(hp: pd.DataFrame, por: list[str]) -> pd.DataFrame:
    """% de tumores descobertos por serem palpáveis (e não por exame de imagem)."""
    x = hp[hp.deteccao.notna()].assign(p=lambda t: (t.deteccao == "Palpável (exame clínico)").astype("Int8"))
    return proporcao(x, "p", por)
