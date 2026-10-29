"""Baixa todos os arquivos brutos usados no projeto para data/raw/.

Uso:
    python scripts/baixar_dados.py            # tudo
    python scripts/baixar_dados.py rhc sim    # só algumas fontes

Os downloads são retomáveis: arquivos que já existem são pulados.
"""
import sys

from mama.config import (ANOS_APAC, ANOS_PAINEL, ANOS_RHC, ANOS_SIM, ANOS_SISCAN_HISTO, ANOS_SISCAN_MAMOGRAFIA,
                         COMPETENCIAS_CNES)
from mama.download import datasus, rhc_inca
from mama.fontes import geografia


def anos(inicio, fim):
    return [str(a) for a in range(inicio, fim + 1)]


TAREFAS = {
    # RHC: inclui o ano seguinte ao último completo, para acompanhar a atualização da base
    "rhc": lambda: (rhc_inca.baixar_documento(), rhc_inca.baixar(anos(ANOS_RHC[0], ANOS_RHC[1] + 1))),
    "painel": lambda: datasus.baixar("painel", anos(ANOS_PAINEL[0], ANOS_PAINEL[1] + 2)),
    "sim": lambda: datasus.baixar("sim", anos(*ANOS_SIM)),
    "pop": lambda: datasus.baixar("pop", anos(ANOS_RHC[0], ANOS_SIM[1] + 1)),
    "cnes": lambda: [datasus.baixar(f, COMPETENCIAS_CNES) for f in ("cnes_st", "cnes_eq", "cnes_hb")],
    "apac": lambda: datasus.baixar("apac_quimio", [f"{str(a)[2:]}{m:02d}" for a in anos(*ANOS_APAC)
                                                   for m in range(1, 13)]),
    "apac_radio": lambda: datasus.baixar("apac_radio", [f"{str(a)[2:]}{m:02d}" for a in anos(*ANOS_APAC)
                                                        for m in range(1, 13)]),
    "siscan": lambda: (datasus.baixar("siscan_histo", anos(*ANOS_SISCAN_HISTO)),
                       datasus.baixar("siscan_mamografia", [str(a) for a in ANOS_SISCAN_MAMOGRAFIA])),
    "geo": geografia.baixar,
}

if __name__ == "__main__":
    for nome in sys.argv[1:] or TAREFAS:
        print(f"== {nome}")
        TAREFAS[nome]()
