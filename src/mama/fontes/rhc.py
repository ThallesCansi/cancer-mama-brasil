"""RHC (INCA): casos de câncer de mama feminino atendidos em hospitais com registro hospitalar."""
import re

import pandas as pd

from mama import codigos as c
from mama import harmonizacao as h
from mama.config import BRUTOS, INTERMEDIARIOS
from mama.download.datasus import ler_dbf

ARQUIVO = INTERMEDIARIOS / "rhc.parquet"


def _ler_ano(zp) -> pd.DataFrame:
    bruto = ler_dbf(zp)
    n0 = len(bruto)
    bruto = bruto.drop_duplicates()  # a exportação do IntegradorRHC pode repetir linhas idênticas
    d = bruto[(bruto.LOCTUDET == "C50") & (bruto.SEXO == "2")].copy()
    d["ano_consulta"] = int(re.search(r"(\d{4})", zp.name).group(1))
    print(f"{zp.name}: {n0} linhas, {n0 - len(bruto)} duplicadas, {len(d)} C50 feminino")
    return d


def construir() -> pd.DataFrame:
    d = pd.concat([_ler_ano(zp) for zp in sorted((BRUTOS / "rhc").glob("rhc_*.zip"))], ignore_index=True)

    out = pd.DataFrame({"ano_consulta": d.ano_consulta.astype("int16"),
                        "caso_analitico": d.TPCASO == "1",
                        "idade": h.idade(d.IDADE)})
    out["faixa_etaria"] = h.faixa_etaria(out.idade)

    # Onde mora, onde nasceu e onde foi atendida
    out["uf_res"] = d.ESTADRES.where(d.ESTADRES.isin(c.SIGLA_PARA_COD)).astype("string")
    out["regiao_res"] = h.regiao_de_sigla(out.uf_res)
    out["mun_res"] = h.municipio6(d.PROCEDEN)
    out["uf_nasc"] = d.LOCALNAS.where(d.LOCALNAS.isin(c.SIGLA_PARA_COD)).astype("string")
    out["regiao_nasc"] = h.regiao_de_sigla(out.uf_nasc)
    out["uf_hosp"] = d.UFUH.astype("string")
    out["regiao_hosp"] = h.regiao_de_sigla(out.uf_hosp)
    out["mun_hosp"] = h.municipio6(d.MUUH)
    out["cnes_hosp"] = d.CNES.astype("string")
    out["fora_uf"] = (out.uf_res != out.uf_hosp).where(out.uf_res.notna()).astype("boolean")
    out["fora_municipio"] = (out.mun_res != out.mun_hosp).where(out.mun_res.notna() & out.mun_hosp.notna()).astype("boolean")

    # Perfil sociodemográfico
    out["raca_cor"] = h.mapear(d.RACACOR, c.RACA_COR)
    out["escolaridade"] = h.mapear(d.INSTRUC, c.ESCOLARIDADE_RHC)
    out["escolaridade_grupo"] = out.escolaridade.map(c.ESCOLARIDADE_GRUPO).fillna(c.SEM_INFO)
    out["estado_conjugal"] = h.mapear(d.ESTCONJ, c.ESTADO_CONJUGAL_RHC)
    out["historico_familiar"] = h.mapear(d.HISTFAMC, {"1": "Sim", "2": "Não"})
    out["origem_encaminhamento"] = h.mapear(d.ORIENC, c.ORIGEM_ENCAMINHAMENTO)
    out["diag_trat_anteriores"] = h.mapear(d.DIAGANT, c.DIAG_TRAT_ANTERIOR)

    # Tumor e tratamento
    out["estadio"] = h.estadio_rhc(d.ESTADIAM)
    out["estadio_avancado"] = h.estadio_avancado(out.estadio)
    out["histologia"] = h.histologia(d.TIPOHIST)
    out["primeiro_tratamento"] = h.mapear(d.PRITRATH.str[:1], c.PRIMEIRO_TRATAMENTO_RHC)
    out["estado_fim_tratamento"] = h.mapear(d.ESTDFIMT, {
        "1": "Sem evidência da doença", "2": "Remissão parcial", "3": "Doença estável",
        "4": "Doença em progressão", "5": "Suporte terapêutico", "6": "Óbito"})

    # Datas e intervalos
    dt_cons, dt_diag, dt_trat = h.data_br(d.DATAPRICON), h.data_br(d.DTDIAGNO), h.data_br(d.DATAINITRT)
    out["data_consulta"], out["data_diagnostico"], out["data_tratamento"] = dt_cons, dt_diag, dt_trat
    out["dias_consulta_diagnostico"] = h.dias_entre(dt_cons, dt_diag)
    out["dias_diagnostico_tratamento"] = h.dias_entre(dt_diag, dt_trat)
    out["dias_consulta_tratamento"] = h.dias_entre(dt_cons, dt_trat)

    out.to_parquet(ARQUIVO, index=False)
    return out
