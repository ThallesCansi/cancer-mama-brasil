"""Distribuição dos diagnósticos ao longo dos meses do ano."""
import pandas as pd

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def contagem_mensal(d: pd.DataFrame, col_ano: str, col_mes: str, por: str | None = None) -> pd.DataFrame:
    chaves = [col_ano, col_mes] + ([por] if por else [])
    return d.dropna(subset=[col_ano, col_mes]).groupby(chaves, observed=True).size().rename("casos").reset_index()


def indice_mensal(d: pd.DataFrame, col_ano: str, col_mes: str, por: str | None = None,
                  excluir_anos=(2020,)) -> pd.DataFrame:
    """Índice sazonal: casos por dia no mês / média do ano x 100 (100 = mês típico).

    Usar casos por dia evita que fevereiro pareça baixo só por ter menos dias. Dividir pela média
    do próprio ano remove o crescimento de casos ao longo do tempo. Depois, tira-se a média do
    índice entre os anos. 2020 é excluído por padrão (pandemia).
    """
    t = contagem_mensal(d, col_ano, col_mes, por)
    t = t[~t[col_ano].isin(excluir_anos)]
    dias = pd.to_datetime(dict(year=t[col_ano].astype(int), month=t[col_mes].astype(int), day=1)).dt.days_in_month
    t["por_dia"] = t.casos / dias.to_numpy()
    grupo = [col_ano] + ([por] if por else [])
    t["indice"] = t.por_dia / t.groupby(grupo, observed=True).por_dia.transform("mean") * 100
    chaves = [col_mes] + ([por] if por else [])
    out = t.groupby(chaves, observed=True).indice.mean().round(1).reset_index()
    out["mes_nome"] = out[col_mes].astype(int).map(lambda m: MESES[m - 1])
    return out
