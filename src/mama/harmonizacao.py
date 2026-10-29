"""Funções de padronização aplicadas a colunas de qualquer fonte."""
import numpy as np
import pandas as pd

from mama import codigos as c


def sigla_de_cod_uf(cod: pd.Series) -> pd.Series:
    return cod.astype("string").str[:2].map(lambda x: c.UF.get(x, (pd.NA,))[0]).astype("string")


def uf_de_municipio(cod: pd.Series) -> pd.Series:
    """Sigla da UF a partir do código IBGE do município (6 ou 7 dígitos)."""
    return sigla_de_cod_uf(cod)


def regiao_de_sigla(sigla: pd.Series) -> pd.Series:
    return sigla.map(c.SIGLA_PARA_REGIAO).astype("string")


def municipio6(cod: pd.Series) -> pd.Series:
    """Código de município com 6 dígitos; inválidos (ignorados, '0000' no fim) viram NA."""
    s = cod.astype("string").str.strip().str[:6]
    return s.where(s.str.fullmatch(r"\d{6}") & ~s.str.endswith("0000"))


def idade(s: pd.Series) -> pd.Series:
    x = pd.to_numeric(s, errors="coerce")
    return x.where((x >= 0) & (x < 130))


def faixa_etaria(idade_anos: pd.Series) -> pd.Series:
    return pd.cut(idade_anos, c.FAIXAS, right=False, labels=c.FAIXAS_ROTULOS)


def mapear(s: pd.Series, mapa: dict) -> pd.Series:
    """Aplica o dicionário; códigos fora dele (9, 99, brancos) viram 'Sem informação'."""
    return s.astype("string").str.strip().map(mapa).fillna(c.SEM_INFO).astype("string")


def estadio_rhc(s: pd.Series) -> pd.Series:
    """ESTADIAM do RHC ('0', '1A', '2B', '3C', '4', '88', '99'...) -> '0'..'IV' ou NA."""
    s = s.astype("string").str.strip()
    valido = s.str.fullmatch(r"[0-4][ABC]?")
    return s.str[0].where(valido).map({"0": "0", "1": "I", "2": "II", "3": "III", "4": "IV"}).astype("string")


def estadio_painel(s: pd.Series) -> pd.Series:
    """ESTADIAM do Painel e da APAC: 0-4 válidos; demais (não se aplica, ignorado) -> NA."""
    return s.astype("string").str.strip().map({"0": "0", "1": "I", "2": "II", "3": "III", "4": "IV"}).astype("string")


def estadio_avancado(estadio: pd.Series) -> pd.Series:
    """1 se III/IV, 0 se 0/I/II, NA se ignorado (denominador = casos com estádio conhecido)."""
    return estadio.map({"0": 0, "I": 0, "II": 0, "III": 1, "IV": 1}).astype("Int8")


def histologia(tipohist: pd.Series) -> pd.Series:
    return tipohist.astype("string").str[:4].map(c.HISTOLOGIA).fillna("Outros tipos").astype("string")


def data_br(s: pd.Series) -> pd.Series:
    """'dd/mm/aaaa' -> datetime; datas inválidas ('99/99/9999', '  /  /') -> NaT."""
    return pd.to_datetime(s.astype("string").str.strip(), format="%d/%m/%Y", errors="coerce")


def dias_entre(inicio: pd.Series, fim: pd.Series, maximo: int = 3650) -> pd.Series:
    """Diferença em dias; descarta negativos e valores implausíveis (> ~10 anos)."""
    d = (fim - inicio).dt.days
    return d.where((d >= 0) & (d <= maximo))


def intervalo_dias(dias: pd.Series) -> pd.Series:
    """Classifica dias nas faixas usadas em todo o projeto (até 30 dias ... mais de 2 anos)."""
    return pd.cut(dias, c.INTERVALOS_DIAS, right=True, include_lowest=True, labels=c.INTERVALOS_ROTULOS)


def distancia_km(lat1, lon1, lat2, lon2) -> np.ndarray:
    """Distância em linha reta (haversine) entre dois pontos, em km."""
    lat1, lon1, lat2, lon2 = (np.radians(np.asarray(v, dtype=float)) for v in (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * np.arcsin(np.sqrt(a))


def taxa(numerador, denominador, por: float = 100_000):
    return (numerador / denominador.replace(0, np.nan)) * por


def grupo_50(idade_anos: pd.Series) -> pd.Series:
    """'Menos de 50 anos' / '50 anos ou mais' (limite inferior da faixa do rastreamento)."""
    return pd.cut(idade_anos, [0, 50, 200], right=False,
                  labels=["Menos de 50 anos", "50 anos ou mais"]).astype("string")
