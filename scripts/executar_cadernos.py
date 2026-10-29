"""Executa todos os cadernos em ordem, regravando as saídas, tabelas e figuras.

Uso:
    python scripts/executar_cadernos.py          # todos
    python scripts/executar_cadernos.py 03 05    # só alguns, pelo número
"""
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

PASTA = Path(__file__).resolve().parents[1] / "notebooks"

if __name__ == "__main__":
    filtro = sys.argv[1:]
    for caminho in sorted(PASTA.glob("[0-9][0-9]_*.ipynb")):
        if filtro and caminho.name[:2] not in filtro:
            continue
        print(f"executando {caminho.name}")
        nb = nbformat.read(caminho, as_version=4)
        NotebookClient(nb, timeout=1800, kernel_name="python3", resources={"metadata": {"path": str(PASTA)}}).execute()
        nbformat.write(nb, caminho)
