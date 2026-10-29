"""SISCAN (DATASUS): exames de histopatologia de mama e mamografias registrados no SUS.

A histopatologia traz o resultado dos receptores hormonais (estrogênio e progesterona) medido por
imuno-histoquímica, a única informação pública de perfil molecular do tumor. A mamografia traz a
indicação (rastreamento ou diagnóstica), a categoria BI-RADS e o tempo até o resultado.
"""
import re

import pandas as pd

from mama import codigos as c
from mama import harmonizacao as h
from mama.config import BRUTOS, INTERMEDIARIOS

HISTO = INTERMEDIARIOS / "siscan_histopatologia.parquet"
MAMOGRAFIA = INTERMEDIARIOS / "siscan_mamografia.parquet"

COLS_HISTO = ["CO_MUN_RESIDENCIA", "NU_ANO_COMPETENCIA", "CO_RACA_COR", "CO_IDADE_PACIENTE", "CO_ESCOLARIDADE",
              "TP_DETECCAO_LESAO", "TP_LESAO", "TP_LESAO_CARAT_NEOPL_MALI", "TP_GRAU_HISTOLOGICO", "SG_SEXO",
              "TP_RECEPTOR_HORMONAL_ESTROG", "TP_RECEPTOR_HORMONAL_PROGES", "ST_OUTRO_ESTUDO_IMUNOLO_HISTOQ",
              "TP_TAMANHO_TUMOR", "CO_INTERVALO_EXAME"]
# O município do prestador (CO_MUN_PREST_SERVICO) vem sempre em branco nos CSVs públicos
COLS_MAMO = ["CO_MUN_RESIDENCIA", "NU_ANO_COMPETENCIA", "CO_RACA_COR",
             "CO_IDADE_PACIENTE", "CO_IND_CLINICA", "TP_MAMOGRAFIA_RASTREAMENT", "CO_BIRADS",
             "CO_INTERVALO_RESULTADO", "SG_SEXO"]


def _ler_csv(caminho, colunas, filtro=None, pedaco=500_000) -> pd.DataFrame:
    """Lê o CSV do SISCAN em pedaços, só com as colunas pedidas (os de mamografia têm ~1 GB)."""
    partes = []
    for d in pd.read_csv(caminho, sep=";", encoding="latin-1", usecols=colunas, dtype=str,
                         chunksize=pedaco, keep_default_na=False):
        partes.append(filtro(d) if filtro else d)
    return pd.concat(partes, ignore_index=True)


def _comum(d: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({"ano": pd.to_numeric(d.NU_ANO_COMPETENCIA, errors="coerce").astype("Int16"),
                        "idade": h.idade(d.CO_IDADE_PACIENTE)})
    out["faixa_etaria"] = h.faixa_etaria(out.idade)
    out["mun_res"] = h.municipio6(d.CO_MUN_RESIDENCIA).to_numpy()
    out["uf_res"] = h.uf_de_municipio(out.mun_res)
    out["regiao_res"] = h.regiao_de_sigla(out.uf_res)
    out["raca_cor"] = h.mapear(d.CO_RACA_COR, c.RACA_COR_SISCAN).to_numpy()
    return out


def construir_histopatologia() -> pd.DataFrame:
    """Uma linha por laudo de histopatologia com lesão maligna invasiva, em mulheres."""
    partes = []
    for p in sorted((BRUTOS / "siscan_histo").glob("SISCAN_HISTO_MAMA_*.csv")):
        d = _ler_csv(p, COLS_HISTO, lambda x: x[(x.SG_SEXO == "F") & (x.TP_LESAO == "04")
                                                & x.TP_LESAO_CARAT_NEOPL_MALI.isin(c.INVASIVO_SISCAN)])
        print(f"{p.name}: {len(d):,} laudos de carcinoma invasivo")
        partes.append(d)
    d = pd.concat(partes, ignore_index=True)
    out = _comum(d)
    out["escolaridade_grupo"] = h.mapear(d.CO_ESCOLARIDADE, c.ESCOLARIDADE_SISCAN_GRUPO).to_numpy()
    out["histologia"] = d.TP_LESAO_CARAT_NEOPL_MALI.map(c.HISTOLOGIA_SISCAN).fillna("Outros tipos").to_numpy()
    out["receptor_estrogenio"] = h.mapear(d.TP_RECEPTOR_HORMONAL_ESTROG, c.RECEPTOR).to_numpy()
    out["receptor_progesterona"] = h.mapear(d.TP_RECEPTOR_HORMONAL_PROGES, c.RECEPTOR).to_numpy()
    er, pr = out.receptor_estrogenio, out.receptor_progesterona
    # Receptor hormonal positivo se estrogênio OU progesterona positivo; negativo só se ambos negativos
    out["receptor_hormonal"] = pd.Series(pd.NA, index=out.index, dtype="string")
    out.loc[(er == "Positivo") | (pr == "Positivo"), "receptor_hormonal"] = "Positivo"
    out.loc[(er == "Negativo") & (pr == "Negativo"), "receptor_hormonal"] = "Negativo"
    out["grau_histologico"] = d.TP_GRAU_HISTOLOGICO.map(c.GRAU_HISTOLOGICO).to_numpy()
    out["tamanho_tumor"] = d.TP_TAMANHO_TUMOR.map(c.TAMANHO_TUMOR).to_numpy()
    out["deteccao"] = d.TP_DETECCAO_LESAO.map(c.DETECCAO_LESAO).to_numpy()
    out.to_parquet(HISTO, index=False)
    return out


def construir_mamografia() -> pd.DataFrame:
    """Uma linha por mamografia em mulher, com indicação, BI-RADS e tempo até o resultado."""
    partes = []
    for p in sorted((BRUTOS / "siscan_mamografia").glob("SISCAN_MAMOGRAFIA_*.csv")):
        d = _ler_csv(p, COLS_MAMO, lambda x: x[x.SG_SEXO == "F"])
        print(f"{p.name}: {len(d):,} mamografias em mulheres")
        d["arquivo"] = int(re.search(r"(\d{4})", p.name).group(1))
        partes.append(d)
    d = pd.concat(partes, ignore_index=True)
    out = _comum(d)
    out["ano"] = d.arquivo.astype("int16").to_numpy()
    out["indicacao"] = h.mapear(d.CO_IND_CLINICA, c.INDICACAO_MAMOGRAFIA).to_numpy()
    out["rastreamento_populacao_alvo"] = (d.CO_IND_CLINICA == "02").to_numpy() & (d.TP_MAMOGRAFIA_RASTREAMENT == "01").to_numpy()
    out["birads"] = d.CO_BIRADS.str.strip().map(c.BIRADS).to_numpy()
    out["intervalo_resultado"] = d.CO_INTERVALO_RESULTADO.str.strip().map(c.INTERVALO_RESULTADO).to_numpy()
    for col in ["faixa_etaria", "uf_res", "regiao_res", "raca_cor", "indicacao", "birads", "intervalo_resultado"]:
        out[col] = out[col].astype("category")
    out.to_parquet(MAMOGRAFIA, index=False)
    return out


def construir():
    construir_histopatologia()
    construir_mamografia()
