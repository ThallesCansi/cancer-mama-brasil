"""Converte os arquivos brutos em tabelas limpas (data/interim/*.parquet).

Uso:
    python scripts/construir_bases.py              # todas as fontes
    python scripts/construir_bases.py rhc painel   # só algumas
"""
import sys

from mama.config import INTERMEDIARIOS
from mama.fontes import apac, apac_radio, cnes, geografia, painel, populacao, rhc, sim, siscan

FONTES = {"rhc": rhc, "painel": painel, "sim": sim, "pop": populacao, "cnes": cnes, "apac": apac,
          "apac_radio": apac_radio, "siscan": siscan, "geo": geografia}

if __name__ == "__main__":
    INTERMEDIARIOS.mkdir(parents=True, exist_ok=True)
    for nome in sys.argv[1:] or FONTES:
        print(f"== {nome}")
        FONTES[nome].construir()
