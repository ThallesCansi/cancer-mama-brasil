"""Estádio ao diagnóstico (TNM) e tipo histológico (RHC)."""
import pandas as pd

from mama import codigos as c
from mama.analises.base import distribuicao, proporcao

ORDEM_ESTADIO = ["0", "I", "II", "III", "IV", c.SEM_INFO]


def distribuicao_estadio(d: pd.DataFrame, por: str = "regiao_res") -> pd.DataFrame:
    x = d.assign(estadio_rotulo=d.estadio.fillna(c.SEM_INFO))
    return distribuicao(x, "estadio_rotulo", por, ORDEM_ESTADIO)


def avancado(d: pd.DataFrame, por: list[str]) -> pd.DataFrame:
    """% em estádio III ou IV entre os casos com estádio conhecido, com IC 95%."""
    return proporcao(d, "estadio_avancado", por)


def avancado_por_histologia_uf(d: pd.DataFrame) -> dict:
    """Um mapa por tipo histológico; UFs com menos de 100 casos com estádio ficam sem cor."""
    t = avancado(d, ["histologia", "uf_res"])
    t = t[t.n >= 100]
    return {h: t[t.histologia == h].set_index("uf_res").pct for h in c.HISTOLOGIA_ORDEM}
