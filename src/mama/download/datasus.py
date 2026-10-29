"""Download de arquivos do FTP do DATASUS e leitura de DBC/DBF.

Uso pela linha de comando: ver scripts/baixar_dados.py.
"""
import struct
import tempfile
import zipfile
from ftplib import FTP
from pathlib import Path

import datasus_dbc
import pandas as pd
import pyogrio
from dbfread import DBF

from mama.config import BRUTOS as RAW

HOST = "ftp.datasus.gov.br"
UFS = ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA",
       "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"]

FONTES = {
    "painel": ("/dissemin/publicos/PAINEL_ONCOLOGIA/Dados", lambda a: [f"POBR{a}.dbc"]),
    "sim": ("/dissemin/publicos/SIM/CID10/DORES", lambda a: [f"DOBR{a}.dbc"]),
    "pop": ("/dissemin/publicos/IBGE/POPSVS", lambda a: [f"POPSBR{str(a)[-2:]}.zip"]),
    "cnes_eq": ("/dissemin/publicos/CNES/200508_/Dados/EQ", lambda c: [f"EQ{uf}{c}.dbc" for uf in UFS]),
    "cnes_hb": ("/dissemin/publicos/CNES/200508_/Dados/HB", lambda c: [f"HB{uf}{c}.dbc" for uf in UFS]),
    "cnes_st": ("/dissemin/publicos/CNES/200508_/Dados/ST", lambda c: [f"ST{uf}{c}.dbc" for uf in UFS]),
    # APAC de quimioterapia e de radioterapia: periodo = AAMM
    "apac_quimio": ("/dissemin/publicos/SIASUS/200801_/Dados", lambda c: [f"AQ{uf}{c}.dbc" for uf in UFS]),
    "apac_radio": ("/dissemin/publicos/SIASUS/200801_/Dados", lambda c: [f"AR{uf}{c}.dbc" for uf in UFS]),
    # SISCAN (CSV anuais): periodo = ano
    "siscan_histo": ("/dissemin/publicos/SISCAN/SISCAN", lambda a: [f"SISCAN_HISTO_MAMA_{a}.csv"]),
    "siscan_mamografia": ("/dissemin/publicos/SISCAN/SISCAN", lambda a: [f"SISCAN_MAMOGRAFIA_{a}.csv"]),
}


def baixar(fonte: str, periodos: list[str]) -> list[Path]:
    pasta, nomes = FONTES[fonte]
    dest = RAW / fonte
    dest.mkdir(parents=True, exist_ok=True)
    ftp = FTP(HOST, timeout=120)
    ftp.login()
    ftp.cwd(pasta)
    disponiveis = set(ftp.nlst())
    baixados = []
    for p in periodos:
        for nome in nomes(p):
            alvo = dest / nome
            if nome not in disponiveis:
                print(f"[aviso] {nome} não existe em {pasta}")
                continue
            if not alvo.exists():
                tmp = alvo.with_suffix(alvo.suffix + ".part")
                with open(tmp, "wb") as f:
                    ftp.retrbinary(f"RETR {nome}", f.write)
                tmp.rename(alvo)
                print(alvo)
            baixados.append(alvo)
    ftp.quit()
    return baixados


def ler_dbf(caminho: Path, colunas: list[str] | None = None) -> pd.DataFrame:
    """Lê .dbc, .dbf ou .zip contendo um .dbf; todas as colunas como texto."""
    caminho = Path(caminho)
    with tempfile.TemporaryDirectory() as tmp:
        if caminho.suffix.lower() == ".dbc":
            dbf = Path(tmp) / (caminho.stem + ".dbf")
            datasus_dbc.decompress(str(caminho), str(dbf))
        elif caminho.suffix.lower() == ".zip":
            with zipfile.ZipFile(caminho) as z:
                nome = next(n for n in z.namelist() if n.lower().endswith(".dbf"))
                dbf = Path(z.extract(nome, tmp))
        else:
            dbf = caminho
        try:
            df = _ler_dbfread(dbf, colunas)
        except (struct.error, ValueError):
            # Cabeçalhos muito longos (ex.: CNES-ST, 208 campos) quebram o dbfread
            df = _ler_pyogrio(dbf, colunas)
    return df.astype("string")


def _ler_dbfread(dbf: Path, colunas):
    tabela = DBF(str(dbf), encoding="latin-1", char_decode_errors="replace",
                 raw=False, ignore_missing_memofile=True)
    # Alguns anos trazem nomes de campos em minúsculas (ex.: POPSBR25)
    nomes = {c.upper(): c for c in tabela.field_names}
    campos = [c for c in (colunas or nomes) if c in nomes]
    linhas = ({c: r.get(nomes[c]) for c in campos} for r in tabela)
    return pd.DataFrame(linhas, columns=campos)


def _ler_pyogrio(dbf: Path, colunas):
    nomes = {c.upper(): c for c in pyogrio.read_info(dbf, encoding="latin-1")["fields"]}
    campos = [c for c in (colunas or nomes) if c in nomes]
    df = pyogrio.read_dataframe(dbf, columns=[nomes[c] for c in campos], read_geometry=False,
                                encoding="latin-1")
    # pyogrio devolve as colunas na ordem do arquivo, não na ordem pedida
    return df[[nomes[c] for c in campos]].set_axis(campos, axis=1)

