"""Malhas do IBGE: contorno das UFs (mapas) e centroides dos municípios (distâncias)."""
import gzip
import json
import urllib.request

import geopandas as gpd
import pandas as pd

from mama import harmonizacao as h
from mama.config import BRUTOS, INTERMEDIARIOS

PASTA = BRUTOS / "geo"
UFS = PASTA / "ufs_ibge.geojson"
MUNICIPIOS_GEO = PASTA / "municipios_ibge.geojson"
MUNICIPIOS_NOMES = PASTA / "municipios_ibge.json"
MUNICIPIOS = INTERMEDIARIOS / "municipios.parquet"

API = "https://servicodados.ibge.gov.br/api"
URLS = {
    UFS: f"{API}/v3/malhas/paises/BR?formato=application/vnd.geo%2Bjson&intrarregiao=UF&qualidade=intermediaria",
    MUNICIPIOS_GEO: f"{API}/v3/malhas/paises/BR?formato=application/vnd.geo%2Bjson&intrarregiao=municipio&qualidade=minima",
    MUNICIPIOS_NOMES: f"{API}/v1/localidades/municipios",
}


def _sem_gzip(b: bytes) -> bytes:
    return gzip.decompress(b) if b[:2] == b"\x1f\x8b" else b  # a API do IBGE pode responder em gzip


def baixar():
    PASTA.mkdir(parents=True, exist_ok=True)
    for destino, url in URLS.items():
        if not destino.exists():
            destino.write_bytes(_sem_gzip(urllib.request.urlopen(url, timeout=300).read()))


def construir() -> pd.DataFrame:
    """Tabela de municípios (código de 6 dígitos) com nome, UF, região e centroide (lat/lon)."""
    g = gpd.read_file(MUNICIPIOS_GEO)
    # Centroide calculado em projeção de área (SIRGAS 2000 / Brazil Polyconic) e convertido para lat/lon
    centro = g.to_crs(5880).geometry.centroid.to_crs(4326)
    nomes = {str(m["id"]): m["nome"] for m in json.loads(_sem_gzip(MUNICIPIOS_NOMES.read_bytes()))}
    out = pd.DataFrame({"mun": g.codarea.str[:6], "nome": g.codarea.map(nomes),
                        "lat": centro.y.values, "lon": centro.x.values})
    out["uf"] = h.uf_de_municipio(out.mun)
    out["regiao"] = h.regiao_de_sigla(out.uf)
    out.to_parquet(MUNICIPIOS, index=False)
    return out


def ufs() -> gpd.GeoDataFrame:
    from mama import codigos as c
    g = gpd.read_file(UFS)
    g["uf"] = g.codarea.map(lambda x: c.UF[x][0])
    g["regiao"] = g.uf.map(c.SIGLA_PARA_REGIAO)
    return g
