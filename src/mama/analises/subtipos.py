"""Proxy de subtipo molecular a partir dos procedimentos de quimioterapia autorizados (APAC/SUS)."""
import pandas as pd

from mama import codigos as c
from mama.analises.base import distribuicao, proporcao


def distribuicao_subtipos(d: pd.DataFrame, por: str = "regiao_res") -> pd.DataFrame:
    return distribuicao(d, "subtipo", por, c.SUBTIPO_ORDEM)


def triplo_negativo_por(d: pd.DataFrame, por: list[str]) -> pd.DataFrame:
    """% de provável triplo-negativo, com IC 95%."""
    x = d.assign(tn=(d.subtipo == "Provável triplo-negativo").astype("Int8"))
    return proporcao(x, "tn", por)


def estadio_por_subtipo(d: pd.DataFrame) -> pd.DataFrame:
    x = d.assign(avancado=d.estadio.map({"0": 0, "I": 0, "II": 0, "III": 1, "IV": 1}).astype("Int8"))
    return proporcao(x, "avancado", ["subtipo"])


def com_seguimento_minimo(d: pd.DataFrame, ultimo_mes: int = 6) -> pd.DataFrame:
    """Restringe a coorte às diagnosticadas até `ultimo_mes` do ano, que têm ao menos 18 meses de
    autorizações observadas. Sem isso, pacientes luminais diagnosticadas no fim do ano, que ainda
    não começaram a hormonioterapia, seriam contadas como prováveis triplo-negativas."""
    return d[d.data_diagnostico.dt.month <= ultimo_mes].copy()


def por_trimestre_de_diagnostico(d: pd.DataFrame) -> pd.DataFrame:
    """Teste de sensibilidade: distribuição dos subtipos pelo trimestre do diagnóstico."""
    t = pd.crosstab(d.data_diagnostico.dt.quarter.rename("trimestre"), d.subtipo, normalize="index").mul(100)
    return t[c.SUBTIPO_ORDEM].round(1)
