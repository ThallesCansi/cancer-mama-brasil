"""Intervalos entre consulta, diagnóstico e tratamento (RHC e Painel de Oncologia)."""
import pandas as pd

from mama import codigos as c
from mama import harmonizacao as h


def distribuicao_intervalos(d: pd.DataFrame, coluna_dias: str, por: str) -> pd.DataFrame:
    """% de casos em cada faixa de tempo (até 30 dias ... mais de 2 anos), dentro de cada grupo."""
    x = d.dropna(subset=[coluna_dias])
    x = x.assign(intervalo=h.intervalo_dias(x[coluna_dias]))
    t = pd.crosstab(x[por], x.intervalo, normalize="index").mul(100).round(1)
    t = t.reindex(columns=c.INTERVALOS_ROTULOS, fill_value=0)
    if por.startswith("regiao"):
        t = t.reindex([r for r in c.REGIOES if r in t.index])
    return t


def resumo(d: pd.DataFrame, coluna_dias: str, por: list[str]) -> pd.DataFrame:
    x = d.dropna(subset=[coluna_dias])
    g = x.groupby(por, observed=True)[coluna_dias]
    return g.agg(
        n="size", mediana="median", p25=lambda s: s.quantile(.25), p75=lambda s: s.quantile(.75),
        pct_mais_60_dias=lambda s: (s > 60).mean() * 100,
        pct_mais_6_meses=lambda s: (s > 180).mean() * 100,
        pct_mais_1_ano=lambda s: (s > 365).mean() * 100,
    ).reset_index().round(1)


def painel_tratadas(d: pd.DataFrame) -> pd.DataFrame:
    """Casos do Painel com tratamento registrado depois do diagnóstico (base da Lei dos 60 dias)."""
    x = d[d.tratado & d.dias_diagnostico_tratamento.notna()].copy()
    # Tratamento registrado antes do laudo (valor negativo) conta como tempo zero
    x["dias_diagnostico_tratamento"] = x.dias_diagnostico_tratamento.clip(lower=0)
    return x
