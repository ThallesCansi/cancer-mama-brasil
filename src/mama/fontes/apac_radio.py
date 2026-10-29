"""APAC de radioterapia (SIA/SUS): mulheres com câncer de mama que iniciaram radioterapia pelo SUS.

Cada APAC informa a data do diagnóstico (AR_DTIDEN) e a data de início da radioterapia (AR_INIAR1),
o que permite medir a espera até a radioterapia, além do município da paciente e do serviço.
"""
import pandas as pd

from mama import codigos as c
from mama import harmonizacao as h
from mama.config import ANOS_APAC, BRUTOS, INTERMEDIARIOS
from mama.download.datasus import ler_dbf
from mama.fontes.apac import paciente_hash

ARQUIVO = INTERMEDIARIOS / "apac_radio_pacientes.parquet"
COLUNAS = ["AP_CNSPCN", "AP_CIDPRI", "AP_SEXO", "AP_NUIDADE", "AP_COIDADE", "AP_RACACOR", "AP_MUNPCN",
           "AP_UFMUN", "AP_CODUNI", "AP_NATJUR", "AP_CMP", "AR_ESTADI", "AR_DTIDEN", "AR_INIAR1", "AR_FINALI"]
# Tabela FINALID.CNV do TAB_SIA
FINALIDADE = {"1": "Radical", "2": "Adjuvante", "3": "Antiálgica", "4": "Paliativa", "5": "Prévia",
              "6": "Anti-hemorrágica"}


def construir() -> pd.DataFrame:
    partes = []
    for ano in range(ANOS_APAC[0], ANOS_APAC[1] + 1):
        for p in sorted((BRUTOS / "apac_radio").glob(f"AR??{str(ano)[2:]}??.dbc")):
            d = ler_dbf(p, COLUNAS)
            partes.append(d[d.AP_CIDPRI.str.startswith("C50") & (d.AP_SEXO == "F")])
    d = pd.concat(partes, ignore_index=True)
    print(f"APAC radioterapia {ANOS_APAC}: {len(d):,} autorizações de mama")

    d["paciente"] = paciente_hash(d.AP_CNSPCN)
    d["inicio"] = pd.to_datetime(d.AR_INIAR1, format="%Y%m%d", errors="coerce")
    d["diagnostico"] = pd.to_datetime(d.AR_DTIDEN, format="%Y%m%d", errors="coerce")
    # Um curso de radioterapia gera várias APACs mensais: fica a primeira, pela data de início
    d = d.sort_values(["inicio", "AP_CMP"]).drop_duplicates("paciente")

    out = pd.DataFrame({"paciente": d.paciente, "ano_inicio": d.inicio.dt.year.astype("Int16"),
                        "data_diagnostico": d.diagnostico, "data_inicio": d.inicio,
                        "idade": h.idade(d.AP_NUIDADE.where(d.AP_COIDADE == "4")),
                        "raca_cor": h.mapear(d.AP_RACACOR, c.RACA_COR_SIA),
                        "mun_res": h.municipio6(d.AP_MUNPCN), "mun_trat": h.municipio6(d.AP_UFMUN),
                        "cnes_trat": d.AP_CODUNI, "natureza": d.AP_NATJUR.map(c.natureza_juridica),
                        "estadio": h.estadio_painel(d.AR_ESTADI),
                        "finalidade": h.mapear(d.AR_FINALI, FINALIDADE)})
    # Fica quem iniciou a radioterapia nos anos baixados; datas fora disso são erros de digitação
    # ou cursos iniciados antes, que só continuaram no período
    out = out[out.ano_inicio.between(*ANOS_APAC)].copy()
    out["faixa_etaria"] = h.faixa_etaria(out.idade)
    out["dias_diagnostico_radioterapia"] = h.dias_entre(out.data_diagnostico, out.data_inicio)
    out["uf_res"] = h.uf_de_municipio(out.mun_res)
    out["regiao_res"] = h.regiao_de_sigla(out.uf_res)
    out["uf_trat"] = h.uf_de_municipio(out.mun_trat)
    out.to_parquet(ARQUIVO, index=False)
    print(f"-> {len(out):,} mulheres; início por ano: {out.ano_inicio.astype(int).value_counts().sort_index().to_dict()}")
    return out
