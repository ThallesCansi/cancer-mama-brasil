"""Download dos microdados públicos do RHC (IntegradorRHC/INCA).

O site gera os arquivos sob demanda: faz-se POST do formulário, consulta-se o
status até ficar pronto e então baixa-se o arquivo pela mesma sessão.

Atenção: a opção "todosho" do site (todos os estados exceto SP) vem com ~50% de
linhas duplicadas. A base "todosho_sp" é a nacional completa (inclui SP e todo o
conteúdo da outra) e é a usada aqui.
"""
import re
import time
from pathlib import Path

import requests

from mama.config import BRUTOS

BASE = "https://irhc.inca.gov.br/RHCNet/"
OUT = BRUTOS / "rhc"
RUNNING, DONE = 1, 2


def _session(local: str) -> requests.Session:
    s = requests.Session()
    # Abre a página do formulário para inicializar a sessão no servidor.
    s.get(BASE + "selecionaDownloadTabWin.action",
          params={"initial": 1, "local": local, "unidFed": ""}, timeout=60).raise_for_status()
    return s


def _wait_and_get(s: requests.Session, url: str, data: dict | None, dest: Path) -> Path:
    payload = {**(data or {}), "wwajax": 1, "wwresult": 0}
    for _ in range(600):
        if data is None:
            r = s.get(BASE + url, params={"wwajax": 1, "wwresult": 0}, timeout=120)
        else:
            r = s.post(BASE + url, data=payload, timeout=120)
        r.raise_for_status()
        # O servidor devolve JSON fora do padrão, ex.: {'status':'1'}
        m = re.search(r"status'?\"?\s*:\s*'?\"?(\d+)", r.text)
        status = int(m.group(1)) if m else None
        if status == DONE:
            break
        if status != RUNNING:
            raise RuntimeError(f"Falha no download ({url}): {r.text[:300]}")
        time.sleep(2)
    else:
        raise TimeoutError(url)

    with s.get(BASE + url, stream=True, timeout=600) as r:
        r.raise_for_status()
        cd = r.headers.get("content-disposition", "")
        m = re.search(r'filename="?([^";]+)', cd)
        name = m.group(1) if m else dest.name
        path = dest.parent / name
        with open(path, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    return path


def baixar_anos(anos: list[str], local: str = "todosho_sp") -> Path:
    """local='todosho_sp' (base nacional, com SP) ou 'todosho' (sem SP)."""
    OUT.mkdir(parents=True, exist_ok=True)
    s = _session(local)
    data = {"local": local, "unidFed": "", "anoPrimeiraConsulta": "",
            "downloadToken": str(int(time.time() * 1000)),
            "anosSelecionados": anos}
    return _wait_and_get(s, "downloadTabWin!bases.action", data,
                         OUT / f"rhc_{local}_{'_'.join(anos)}.zip")


def baixar_documento(doc: str = "dicionario.dados") -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    s = _session("todosho_sp")
    return _wait_and_get(s, f"downloadTabWin!document.action?doc={doc}", None, OUT / f"{doc}.pdf")



def baixar(anos: list[str]) -> list[Path]:
    """Um zip por ano (cada DBF anual tem ~300 MB); pula os que já existem."""
    caminhos = []
    for ano in anos:
        destino = OUT / f"rhc_{ano}.zip"
        if not destino.exists():
            baixar_anos([ano]).rename(destino)
        caminhos.append(destino)
    return caminhos
