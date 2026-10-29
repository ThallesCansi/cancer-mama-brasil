"""APAC de quimioterapia (SIA/SUS): coorte de mulheres com câncer de mama diagnosticadas em um ano.

O procedimento autorizado indica o perfil do tumor, o que permite aproximar o subtipo molecular:
anti-HER2 -> HER2 positivo; hormonioterapia ou procedimento "receptor positivo" -> luminal;
apenas quimioterapia citotóxica -> provável triplo-negativo.

Para não acumular pacientes antigas em hormonioterapia (que dura anos e inflaria o grupo luminal),
a análise usa uma coorte: mulheres cuja data do diagnóstico patológico (AQ_DTIDEN) cai em
ANO_COORTE_APAC, acompanhadas por todas as autorizações de ANOS_APAC. Ver notebook 04.
"""
import hashlib

import numpy as np
import pandas as pd

from mama import codigos as c
from mama import harmonizacao as h
from mama.config import ANO_COORTE_APAC, ANOS_APAC, BRUTOS, INTERMEDIARIOS
from mama.download.datasus import ler_dbf

ARQUIVO = INTERMEDIARIOS / "apac_quimio_pacientes.parquet"
TRATAMENTOS = INTERMEDIARIOS / "apac_quimio_tratamentos.parquet"
ANO_TRATAMENTOS = ANOS_APAC[1]
COLUNAS = ["AP_CNSPCN", "AP_CIDPRI", "AP_SEXO", "AP_NUIDADE", "AP_COIDADE", "AP_RACACOR", "AP_MUNPCN",
           "AP_UFMUN", "AP_CODUNI", "AP_NATJUR", "AP_PRIPAL", "AQ_ESTADI", "AQ_DTIDEN", "AP_CMP"]


def _subtipo(her2: bool, receptor: bool) -> str:
    if her2:
        return "HER2 positivo"
    if receptor:
        return "Luminal (receptor hormonal +)"
    return "Provável triplo-negativo"


def _ler() -> pd.DataFrame:
    partes = []
    for ano in range(ANOS_APAC[0], ANOS_APAC[1] + 1):
        for p in sorted((BRUTOS / "apac_quimio").glob(f"AQ??{str(ano)[2:]}??.dbc")):
            d = ler_dbf(p, COLUNAS)
            partes.append(d[d.AP_CIDPRI.str.startswith("C50") & (d.AP_SEXO == "F")])
    d = pd.concat(partes, ignore_index=True)
    print(f"APAC {ANOS_APAC}: {len(d):,} autorizações de quimioterapia/hormonioterapia de mama")
    return d


def paciente_hash(cns: pd.Series) -> pd.Series:
    """O CNS já vem codificado no SIA; guardamos só um hash curto dele, suficiente para agrupar."""
    return cns.map(lambda s: hashlib.sha1(s.encode()).hexdigest()[:16])


def _tratamentos(d: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por paciente e tipo de tratamento sistêmico no ano mais recente (para distâncias)."""
    x = d[d.AP_CMP.str.startswith(str(ANO_TRATAMENTOS))].copy()
    x["tipo"] = np.select([x.her2, x.receptor, x.quimio], ["Anti-HER2", "Hormonioterapia", "Quimioterapia"],
                          default="")
    x = x.drop_duplicates(["paciente", "tipo"])  # já ordenado por competência: fica a primeira do ano
    out = pd.DataFrame({"paciente": x.paciente, "tipo": x.tipo, "cnes_trat": x.AP_CODUNI,
                        "mun_res": h.municipio6(x.AP_MUNPCN), "mun_trat": h.municipio6(x.AP_UFMUN),
                        "idade": h.idade(x.AP_NUIDADE.where(x.AP_COIDADE == "4")),
                        "natureza": x.AP_NATJUR.map(c.natureza_juridica)})
    out["uf_res"] = h.uf_de_municipio(out.mun_res)
    out["regiao_res"] = h.regiao_de_sigla(out.uf_res)
    out.to_parquet(TRATAMENTOS, index=False)
    print(f"-> {len(out):,} pares paciente-tratamento em {ANO_TRATAMENTOS}: {out.tipo.value_counts().to_dict()}")
    return out


def construir() -> pd.DataFrame:
    d = _ler()
    d["paciente"] = paciente_hash(d.AP_CNSPCN)
    d["her2"] = d.AP_PRIPAL.isin(c.PROC_ANTI_HER2)
    d["receptor"] = d.AP_PRIPAL.isin(c.PROC_RECEPTOR_POSITIVO)
    d["quimio"] = d.AP_PRIPAL.isin(c.PROC_QUIMIO)
    d = d[d.her2 | d.receptor | d.quimio]
    d["data_diagnostico"] = pd.to_datetime(d.AQ_DTIDEN, format="%Y%m%d", errors="coerce")
    d = d.sort_values("AP_CMP")  # a primeira autorização define residência e estabelecimento
    _tratamentos(d)

    g = d.groupby("paciente")
    out = g.agg(her2=("her2", "any"), receptor=("receptor", "any"), autorizacoes=("AP_PRIPAL", "size"),
                data_diagnostico=("data_diagnostico", "min"), primeira_competencia=("AP_CMP", "first"),
                idade=("AP_NUIDADE", "first"), unidade_idade=("AP_COIDADE", "first"),
                raca=("AP_RACACOR", "first"), mun_res=("AP_MUNPCN", "first"), mun_trat=("AP_UFMUN", "first"),
                cnes_trat=("AP_CODUNI", "first"), natjur=("AP_NATJUR", "first"),
                estadio=("AQ_ESTADI", "max")).reset_index()
    out = out[out.data_diagnostico.dt.year == ANO_COORTE_APAC].copy()

    out["subtipo"] = [_subtipo(a, b) for a, b in zip(out.her2, out.receptor)]
    out["idade"] = h.idade(out.idade.where(out.unidade_idade == "4"))
    out["faixa_etaria"] = h.faixa_etaria(out.idade)
    out["raca_cor"] = h.mapear(out.raca, c.RACA_COR_SIA)
    out["mun_res"], out["mun_trat"] = h.municipio6(out.mun_res), h.municipio6(out.mun_trat)
    out["uf_res"] = h.uf_de_municipio(out.mun_res)
    out["regiao_res"] = h.regiao_de_sigla(out.uf_res)
    out["uf_trat"] = h.uf_de_municipio(out.mun_trat)
    out["natureza"] = out.natjur.map(c.natureza_juridica)
    out["estadio"] = h.estadio_painel(out.estadio)
    out = out.drop(columns=["unidade_idade", "raca", "natjur"])
    out.to_parquet(ARQUIVO, index=False)
    print(f"-> coorte {ANO_COORTE_APAC}: {len(out):,} pacientes; "
          f"{out.subtipo.value_counts(normalize=True).round(3).to_dict()}")
    return out
