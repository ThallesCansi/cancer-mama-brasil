"""SIM (DATASUS): óbitos de mulheres com causa básica câncer de mama (C50)."""
import re

import pandas as pd

from mama import codigos as c
from mama import harmonizacao as h
from mama.config import BRUTOS, INTERMEDIARIOS
from mama.download.datasus import ler_dbf

ARQUIVO = INTERMEDIARIOS / "sim.parquet"
COLUNAS = ["CAUSABAS", "SEXO", "IDADE", "RACACOR", "ESC", "ESTCIV", "CODMUNRES", "DTOBITO"]


def _idade(s: pd.Series) -> pd.Series:
    """IDADE do SIM: 1º dígito é a unidade (4 = anos, 5 = 100 anos ou mais); menores de 1 ano -> 0."""
    s = s.astype("string").str.strip()
    v = pd.to_numeric(s.str[1:], errors="coerce")
    anos = v.where(s.str[0] == "4", (v + 100).where(s.str[0] == "5"))
    return anos.where(s.str[0].isin(["4", "5"]), 0.0).where(s.str.fullmatch(r"\d{3}"))


def construir() -> pd.DataFrame:
    partes = []
    for p in sorted((BRUTOS / "sim").glob("DOBR*.dbc")):
        d = ler_dbf(p, COLUNAS)
        d = d[d.CAUSABAS.str.startswith("C50") & (d.SEXO == "2")].copy()
        d["ano"] = int(re.search(r"(\d{4})", p.name).group(1))
        print(f"{p.name}: {len(d)} óbitos C50 feminino")
        partes.append(d)
    d = pd.concat(partes, ignore_index=True)

    out = pd.DataFrame({"ano": d.ano.astype("int16"), "idade": h.idade(_idade(d.IDADE))})
    out["mes"] = pd.to_numeric(d.DTOBITO.str[2:4], errors="coerce").astype("Int8")
    out["faixa_etaria"] = h.faixa_etaria(out.idade)
    out["uf_res"] = h.uf_de_municipio(d.CODMUNRES)
    out["regiao_res"] = h.regiao_de_sigla(out.uf_res)
    out["raca_cor"] = h.mapear(d.RACACOR, c.RACA_COR)
    out["escolaridade"] = h.mapear(d.ESC, c.ESCOLARIDADE_SIM)
    out["estado_civil"] = h.mapear(d.ESTCIV, {"1": "Solteira", "2": "Casada", "3": "Viúva",
                                               "4": "Separada", "5": "União estável"})
    out.to_parquet(ARQUIVO, index=False)
    return out
