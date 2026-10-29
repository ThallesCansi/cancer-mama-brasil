"""Caminhos e recortes temporais usados em todo o projeto."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DADOS = RAIZ / "data"
BRUTOS = DADOS / "raw"          # arquivos como baixados (não versionados)
INTERMEDIARIOS = DADOS / "interim"  # parquets limpos, um por fonte
PROCESSADOS = DADOS / "processed"   # tabelas finais (CSV) usadas no texto
FIGURAS = RAIZ / "figures"

# Anos completos de cada fonte (ver notebook 01 para a justificativa)
ANOS_RHC = (2013, 2022)      # 2023 ainda incompleto no IntegradorRHC
ANOS_PAINEL = (2013, 2024)   # 2025-26: tratamentos ainda sendo registrados
ANOS_SIM = (2013, 2024)
ANOS_APAC = (2023, 2024)     # APAC de quimioterapia baixadas
ANO_COORTE_APAC = 2023       # coorte: mulheres com diagnóstico patológico neste ano
ANOS_SISCAN_HISTO = (2014, 2024)      # histopatologia de mama (receptores hormonais)
ANOS_SISCAN_MAMOGRAFIA = [2019, 2024]  # antes da pandemia e último ano completo (~1 GB cada)
COMPETENCIA_CNES = "2509"    # setembro de 2025, a mais recente
COMPETENCIAS_CNES = ["1312", "1812", "2312", "2509"]

# Texto de fonte usado nas legendas das figuras
FONTE_RHC = "INCA, Registros Hospitalares de Câncer (IntegradorRHC), casos analíticos 2013–2022."
FONTE_PAINEL = "DATASUS, Painel de Oncologia (SUS), diagnósticos C50 2013–2024."
FONTE_CNES = "DATASUS, CNES, competência 09/2025; IBGE/DATASUS, estimativas populacionais 2025."
FONTE_SIM = "DATASUS, Sistema de Informações sobre Mortalidade 2013–2024; IBGE/DATASUS, estimativas populacionais."
FONTE_APAC = "DATASUS, SIA/SUS, APAC de quimioterapia 2023–2024 (coorte diagnosticada em 2023)."
