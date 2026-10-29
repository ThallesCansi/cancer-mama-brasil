"""CNES (DATASUS): estabelecimentos, equipamentos de imagem e habilitações oncológicas, por estabelecimento."""
import pandas as pd

from mama import codigos as c
from mama import harmonizacao as h
from mama.config import BRUTOS, COMPETENCIAS_CNES, INTERMEDIARIOS
from mama.download.datasus import ler_dbf

ESTABELECIMENTOS = INTERMEDIARIOS / "cnes_estabelecimentos.parquet"
EQUIPAMENTOS = INTERMEDIARIOS / "cnes_equipamentos.parquet"
HABILITACOES = INTERMEDIARIOS / "cnes_habilitacoes.parquet"


def _ler(pasta: str, prefixo: str, colunas: list[str]) -> pd.DataFrame:
    arquivos = [p for comp in COMPETENCIAS_CNES for p in sorted((BRUTOS / pasta).glob(f"{prefixo}??{comp}.dbc"))]
    return pd.concat([ler_dbf(p, colunas).assign(competencia=p.stem[-4:]) for p in arquivos], ignore_index=True)


def _localizar(d: pd.DataFrame) -> pd.DataFrame:
    d["mun"] = h.municipio6(d.CODUFMUN)
    d["uf"] = h.uf_de_municipio(d.CODUFMUN)
    d["regiao"] = h.regiao_de_sigla(d.uf)
    d["ano"] = 2000 + d.competencia.str[:2].astype(int)
    return d.drop(columns=["CODUFMUN"])


def construir():
    st = _ler("cnes_st", "ST", ["CNES", "CODUFMUN", "TP_UNID", "NAT_JUR", "VINC_SUS"])
    st["atencao_primaria"] = st.TP_UNID.str.zfill(2).isin(c.ATENCAO_PRIMARIA)
    st["natureza"] = st.NAT_JUR.map(c.natureza_juridica)
    st["atende_sus"] = st.VINC_SUS == "1"
    _localizar(st).to_parquet(ESTABELECIMENTOS, index=False)

    eq = _ler("cnes_eq", "EQ", ["CNES", "CODUFMUN", "TIPEQUIP", "CODEQUIP", "QT_EXIST", "QT_USO", "IND_SUS"])
    eq = eq[eq.TIPEQUIP.str.lstrip("0") == "1"].copy()
    codigo_para_categoria = {cod: nome for nome, cods in c.EQUIPAMENTOS.items() for cod in cods}
    eq["equipamento"] = eq.CODEQUIP.str.zfill(2).map(codigo_para_categoria)
    eq = eq.dropna(subset=["equipamento"])
    eq["qt_existente"] = pd.to_numeric(eq.QT_EXIST, errors="coerce").fillna(0)
    eq["qt_em_uso"] = pd.to_numeric(eq.QT_USO, errors="coerce").fillna(0)
    # IND_SUS = 1: o equipamento está disponível para atendimento SUS
    eq["qt_sus"] = eq.qt_existente.where(eq.IND_SUS == "1", 0)
    eq["qt_em_uso_sus"] = eq.qt_em_uso.where(eq.IND_SUS == "1", 0)
    cols = ["CNES", "CODUFMUN", "competencia", "equipamento", "qt_existente", "qt_em_uso", "qt_sus", "qt_em_uso_sus"]
    _localizar(eq[cols].copy()).to_parquet(EQUIPAMENTOS, index=False)

    hb = _ler("cnes_hb", "HB", ["CNES", "CODUFMUN", "SGRUPHAB"])
    linhas = [hb[hb.SGRUPHAB.isin(cods)].assign(servico=nome) for nome, cods in c.HABILITACOES.items()]
    hb = pd.concat(linhas, ignore_index=True).drop_duplicates(["CNES", "competencia", "servico"])
    _localizar(hb.drop(columns="SGRUPHAB")).to_parquet(HABILITACOES, index=False)
    print(f"CNES: {len(st):,} estabelecimentos, {len(eq):,} registros de equipamentos, {len(hb):,} habilitações")
