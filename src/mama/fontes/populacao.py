"""População feminina (estimativas IBGE disponibilizadas pelo DATASUS, POPSVS)."""
import re

import pandas as pd

from mama import harmonizacao as h
from mama.config import BRUTOS, INTERMEDIARIOS
from mama.download.datasus import ler_dbf

ARQUIVO_UF = INTERMEDIARIOS / "populacao_uf.parquet"
ARQUIVO_MUN = INTERMEDIARIOS / "populacao_municipio.parquet"
ARQUIVO_TOTAL_UF = INTERMEDIARIOS / "populacao_total_uf.parquet"


def construir() -> pd.DataFrame:
    """Gera população feminina por ano, UF e faixa quinquenal; população total (ambos os sexos) por UF e
    ano; e, por município, mulheres, mulheres de 50-69 anos e total de habitantes no ano mais recente."""
    partes, totais, ultimo, ultimo_total = [], [], None, None
    for p in sorted((BRUTOS / "pop").glob("POPSBR*.zip")):
        ano = 2000 + int(re.search(r"(\d{2})\.zip", p.name).group(1))
        todos = ler_dbf(p)
        todos = todos.assign(uf=h.uf_de_municipio(todos.COD_MUN), idade=pd.to_numeric(todos.IDADE, errors="coerce"),
                             pop=pd.to_numeric(todos.POP, errors="coerce"))
        totais.append(todos.groupby("uf", as_index=False)["pop"].sum().assign(ano=ano))
        ultimo_total = todos
        d = todos[todos.SEXO == "2"].copy()
        d["faixa5"] = (d.idade // 5 * 5).clip(upper=80).astype(int)
        g = d.groupby(["uf", "faixa5"], as_index=False)["pop"].sum().assign(ano=ano)
        print(f"{p.name}: {g['pop'].sum():,.0f} mulheres")
        partes.append(g)
        ultimo = d
    uf = pd.concat(partes, ignore_index=True)
    uf["regiao"] = h.regiao_de_sigla(uf.uf)
    uf.to_parquet(ARQUIVO_UF, index=False)
    total = pd.concat(totais, ignore_index=True)
    total["regiao"] = h.regiao_de_sigla(total.uf)
    total.to_parquet(ARQUIVO_TOTAL_UF, index=False)

    # Por município: total de mulheres e mulheres de 50-69 anos no ano mais recente
    ultimo = ultimo.assign(mun=ultimo.COD_MUN.str[:6], alvo=ultimo.idade.between(50, 69))
    mun = ultimo.groupby("mun").agg(mulheres=("pop", "sum"))
    mun["mulheres_50_69"] = ultimo[ultimo.alvo].groupby("mun")["pop"].sum()
    mun["habitantes"] = ultimo_total.groupby(ultimo_total.COD_MUN.str[:6])["pop"].sum()
    mun.reset_index().to_parquet(ARQUIVO_MUN, index=False)
    return uf
