"""Painel de Oncologia (DATASUS): diagnósticos de câncer no SUS e o primeiro tratamento."""
import pandas as pd

from mama import codigos as c
from mama import harmonizacao as h
from mama.config import BRUTOS, INTERMEDIARIOS
from mama.download.datasus import ler_dbf

ARQUIVO = INTERMEDIARIOS / "painel.parquet"


def _tempo(s: pd.Series) -> pd.Series:
    """TEMPO_TRAT: '+0106' = 106 dias depois do diagnóstico; '-0010' = antes; '99999' = sem tratamento."""
    s = s.astype("string").str.strip()
    v = pd.to_numeric(s.str[1:], errors="coerce")
    return v.where(s.str[0] == "+", -v).where(s != "99999")


def construir() -> pd.DataFrame:
    partes = []
    for p in sorted((BRUTOS / "painel").glob("POBR*.dbc")):
        d = ler_dbf(p)
        # CNS_PAC identifica a paciente e não é necessário: descartado na leitura
        d = d[d.DIAG_DETH.isin(["C50", "D05"]) & (d.SEXO == "F")].drop(columns=["CNS_PAC"])
        print(f"{p.name}: {len(d)} casos C50/D05 feminino")
        partes.append(d)
    d = pd.concat(partes, ignore_index=True)

    out = pd.DataFrame({
        "ano_diagnostico": pd.to_numeric(d.ANO_DIAGN, errors="coerce").astype("Int16"),
        "mes_diagnostico": pd.to_numeric(d.ANOMES_DIA.str[4:6], errors="coerce").astype("Int8"),
        "cid": d.DIAG_DETH,
        "idade": h.idade(d.IDADE.where(d.IDADE != "999")),
    })
    out["faixa_etaria"] = h.faixa_etaria(out.idade)
    out["uf_res"] = h.sigla_de_cod_uf(d.UF_RESID)
    out["regiao_res"] = h.regiao_de_sigla(out.uf_res)
    out["uf_diag"] = h.sigla_de_cod_uf(d.UF_DIAGN)
    out["uf_trat"] = h.sigla_de_cod_uf(d.UF_TRATAM)
    out["mun_res"], out["mun_diag"], out["mun_trat"] = h.municipio6(d.MUN_RESID), h.municipio6(d.MUN_DIAG), h.municipio6(d.MUN_TRATAM)
    out["cnes_diag"], out["cnes_trat"] = d.CNES_DIAG, d.CNES_TRAT.where(d.CNES_TRAT.str.strip() != "")
    out["tratamento"] = h.mapear(d.TRATAMENTO, c.TRATAMENTO_PAINEL)
    out["tratado"] = d.TRATAMENTO.isin(list(c.TRATAMENTO_PAINEL))
    out["estadio"] = h.estadio_painel(d.ESTADIAM)
    out["estadio_avancado"] = h.estadio_avancado(out.estadio)
    out["dias_diagnostico_tratamento"] = _tempo(d.TEMPO_TRAT)
    out["fora_uf_tratamento"] = (out.uf_res != out.uf_trat).where(out.tratado & out.uf_trat.notna()).astype("boolean")
    out["fora_municipio_tratamento"] = (out.mun_res != out.mun_trat).where(
        out.tratado & out.mun_trat.notna() & out.mun_res.notna()).astype("boolean")

    out.to_parquet(ARQUIVO, index=False)
    return out
