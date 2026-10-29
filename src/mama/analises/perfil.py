"""Perfil sociodemográfico das mulheres com câncer de mama (RHC)."""
import pandas as pd

from mama import codigos as c


def resumo_regional(d: pd.DataFrame) -> pd.DataFrame:
    g = d.groupby("regiao_res", observed=True)
    t = pd.DataFrame({
        "casos": g.size(),
        "idade_mediana": g.idade.median(),
        "pct_menores_40": g.idade.apply(lambda s: (s < 40).mean() * 100),
        "pct_menores_50": g.idade.apply(lambda s: (s < 50).mean() * 100),
        "pct_escolaridade_sem_info": g.escolaridade.apply(lambda s: (s == c.SEM_INFO).mean() * 100),
        "pct_raca_sem_info": g.raca_cor.apply(lambda s: (s == c.SEM_INFO).mean() * 100),
    }).round(1)
    return t.reindex(c.REGIOES)


def distribuicao_idade(d: pd.DataFrame, por: str = "regiao_res") -> pd.DataFrame:
    """% de casos em cada faixa de 5 anos de idade, dentro de cada grupo."""
    x = d.dropna(subset=["idade"]).assign(faixa5=lambda t: (t.idade // 5 * 5).clip(20, 85).astype(int))
    t = pd.crosstab(x.faixa5, x[por], normalize="columns").mul(100)
    return t[[r for r in c.REGIOES if r in t.columns]] if por == "regiao_res" else t


def migracao(d: pd.DataFrame) -> pd.DataFrame:
    """Matriz região de nascimento x região de residência (% de cada região de residência)."""
    x = d.dropna(subset=["regiao_nasc"])
    t = pd.crosstab(x.regiao_res, x.regiao_nasc, normalize="index").mul(100).round(1)
    return t.reindex(index=c.REGIOES, columns=c.REGIOES)


def nascidas_em_outra_uf(d: pd.DataFrame) -> pd.Series:
    x = d.dropna(subset=["uf_nasc"])
    return (x.uf_nasc != x.uf_res).groupby(x.regiao_res).mean().mul(100).round(1).reindex(c.REGIOES)
