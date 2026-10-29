"""Carregamento das bases limpas e estatísticas comuns a todos os temas."""
import numpy as np
import pandas as pd

from mama import codigos as c
from mama.config import ANOS_PAINEL, ANOS_RHC, INTERMEDIARIOS, PROCESSADOS


def carregar(nome: str) -> pd.DataFrame:
    return pd.read_parquet(INTERMEDIARIOS / f"{nome}.parquet")


def rhc() -> pd.DataFrame:
    """Casos analíticos de câncer de mama feminino (RHC), anos completos, com UF de residência válida."""
    d = carregar("rhc")
    return d[d.caso_analitico & d.ano_consulta.between(*ANOS_RHC) & d.regiao_res.notna()].copy()


def painel() -> pd.DataFrame:
    """Diagnósticos de câncer de mama invasivo (C50) no SUS, anos completos."""
    d = carregar("painel")
    return d[(d.cid == "C50") & d.ano_diagnostico.between(*ANOS_PAINEL) & d.regiao_res.notna()].copy()


def apac() -> pd.DataFrame:
    d = carregar("apac_quimio_pacientes")
    return d[d.regiao_res.notna()].copy()


def ordenar_regioes(df: pd.DataFrame, col: str = "regiao") -> pd.DataFrame:
    df = df.copy()
    df[col] = pd.Categorical(df[col], c.REGIOES, ordered=True)
    return df.sort_values(col)


def ic_wilson(sucessos, n, z: float = 1.96):
    """Intervalo de confiança de 95% para uma proporção (Wilson), em %."""
    sucessos, n = np.asarray(sucessos, float), np.asarray(n, float)
    p = sucessos / n
    centro = (p + z**2 / (2 * n)) / (1 + z**2 / n)
    meia = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / (1 + z**2 / n)
    return (centro - meia) * 100, (centro + meia) * 100


def proporcao(d: pd.DataFrame, indicador: str, por: list[str]) -> pd.DataFrame:
    """% de linhas com indicador == 1 (ignorando NA) por grupo, com n e IC 95%."""
    t = d[d[indicador].notna()].groupby(por, observed=True)[indicador].agg(n="size", eventos="sum").reset_index()
    t["pct"] = t.eventos / t.n * 100
    t["ic_inf"], t["ic_sup"] = ic_wilson(t.eventos, t.n)
    return t.round({"pct": 1, "ic_inf": 1, "ic_sup": 1})


def distribuicao(d: pd.DataFrame, var: str, por: str = "regiao_res", ordem=None) -> pd.DataFrame:
    """% de cada categoria de `var` dentro de cada grupo (cada linha soma 100)."""
    t = pd.crosstab(d[por], d[var], normalize="index").mul(100).round(1)
    if ordem:
        t = t[[o for o in ordem if o in t.columns] + [x for x in t.columns if x not in ordem]]
    if por.startswith("regiao"):
        t = t.reindex([r for r in c.REGIOES if r in t.index])
    return t


def salvar_tabela(df: pd.DataFrame, nome: str, index: bool = False):
    PROCESSADOS.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSADOS / f"{nome}.csv", index=index, encoding="utf-8-sig")
    return df
