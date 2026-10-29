"""Mortalidade por câncer de mama em mulheres (SIM + população)."""
import pandas as pd

from mama import harmonizacao as h

# População padrão mundial de Segi (modificada por Doll), usada pelo INCA; 80+ agrega 80-84 e 85+
SEGI = {0: 12000, 5: 10000, 10: 9000, 15: 9000, 20: 8000, 25: 8000, 30: 6000, 35: 6000, 40: 6000,
        45: 6000, 50: 5000, 55: 4000, 60: 4000, 65: 3000, 70: 2000, 75: 1000, 80: 1000}

GRUPOS_50 = {"<40": "Menos de 50 anos", "40-49": "Menos de 50 anos", "50-69": "50 anos ou mais", "70+": "50 anos ou mais"}


def obitos_por_ano(sim: pd.DataFrame, por: str | None = None) -> pd.DataFrame:
    chaves = ["ano"] + ([por] if por else [])
    return sim.groupby(chaves, observed=True).size().rename("obitos").reset_index()


def taxa_padronizada(sim: pd.DataFrame, pop: pd.DataFrame, por: str = "regiao") -> pd.DataFrame:
    """Taxa bruta e padronizada por idade (método direto, Segi) por 100 mil mulheres."""
    s = sim.rename(columns={"regiao_res": "regiao", "uf_res": "uf"}).dropna(subset=[por, "idade"])
    s = s.assign(faixa5=(s.idade // 5 * 5).clip(upper=80).astype(int))
    obitos = s.groupby(["ano", por, "faixa5"]).size().rename("obitos")
    p = pop.groupby(["ano", por, "faixa5"])["pop"].sum()
    t = pd.concat([obitos, p], axis=1).fillna({"obitos": 0}).dropna(subset=["pop"]).reset_index()
    t = t[t.ano.isin(s.ano.unique())]
    t["peso"] = t.faixa5.map(SEGI) / sum(SEGI.values())
    t["taxa_especifica"] = t.obitos / t["pop"]
    t["contrib"] = t.taxa_especifica * t.peso
    g = t.groupby(["ano", por])
    out = pd.DataFrame({"obitos": g.obitos.sum(), "mulheres": g["pop"].sum(),
                        "taxa_padronizada": g.contrib.sum() * 1e5})
    out["taxa_bruta"] = out.obitos / out.mulheres * 1e5
    return out.round(2).reset_index()


def taxa_por_grupo_etario(sim: pd.DataFrame, pop: pd.DataFrame, agrupamento: dict | None = None,
                          por: str | None = "regiao") -> pd.DataFrame:
    """Óbitos e taxa por 100 mil mulheres de cada grupo etário (faixas amplas ou <50 / 50+)."""
    s = sim.rename(columns={"regiao_res": "regiao"}).dropna(subset=["faixa_etaria"] + ([por] if por else []))
    p = pop.assign(faixa_etaria=h.faixa_etaria(pop.faixa5))
    s = s.assign(grupo=s.faixa_etaria.astype(str))
    p = p.assign(grupo=p.faixa_etaria.astype(str))
    if agrupamento:
        s["grupo"], p["grupo"] = s.grupo.map(agrupamento), p.grupo.map(agrupamento)
    chaves = ["ano", "grupo"] + ([por] if por else [])
    t = pd.concat([s.groupby(chaves).size().rename("obitos"), p.groupby(chaves)["pop"].sum()], axis=1).dropna()
    t["taxa"] = (t.obitos / t["pop"] * 1e5).round(2)
    return t.reset_index()


def variacao(t: pd.DataFrame, col: str, grupos: list[str], ano0: int, ano1: int) -> pd.DataFrame:
    """Variação percentual de `col` entre dois anos, para cada grupo."""
    a = t[t.ano == ano0].set_index(grupos)[col]
    b = t[t.ano == ano1].set_index(grupos)[col]
    return pd.DataFrame({ano0: a, ano1: b, "variacao_pct": ((b / a - 1) * 100).round(1)}).reset_index()
