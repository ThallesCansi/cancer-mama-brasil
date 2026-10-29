"""Tabelas de códigos dos sistemas (IBGE, RHC, SIM, CNES, SIGTAP) usadas na limpeza."""

# Código IBGE da UF -> (sigla, região)
UF = {
    "11": ("RO", "Norte"), "12": ("AC", "Norte"), "13": ("AM", "Norte"), "14": ("RR", "Norte"),
    "15": ("PA", "Norte"), "16": ("AP", "Norte"), "17": ("TO", "Norte"),
    "21": ("MA", "Nordeste"), "22": ("PI", "Nordeste"), "23": ("CE", "Nordeste"),
    "24": ("RN", "Nordeste"), "25": ("PB", "Nordeste"), "26": ("PE", "Nordeste"),
    "27": ("AL", "Nordeste"), "28": ("SE", "Nordeste"), "29": ("BA", "Nordeste"),
    "31": ("MG", "Sudeste"), "32": ("ES", "Sudeste"), "33": ("RJ", "Sudeste"), "35": ("SP", "Sudeste"),
    "41": ("PR", "Sul"), "42": ("SC", "Sul"), "43": ("RS", "Sul"),
    "50": ("MS", "Centro-Oeste"), "51": ("MT", "Centro-Oeste"), "52": ("GO", "Centro-Oeste"),
    "53": ("DF", "Centro-Oeste"),
}
SIGLA_PARA_COD = {s: c for c, (s, _) in UF.items()}
SIGLA_PARA_REGIAO = {s: r for s, r in UF.values()}
SIGLAS_UF = [s for s, _ in UF.values()]
REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]

SEM_INFO = "Sem informação"

# Faixas etárias. A amplas segue a lógica do rastreamento (50-69 é a faixa-alvo).
FAIXAS = [0, 40, 50, 70, 200]
FAIXAS_ROTULOS = ["<40", "40-49", "50-69", "70+"]

RACA_COR = {"1": "Branca", "2": "Preta", "3": "Amarela", "4": "Parda", "5": "Indígena"}  # RHC e SIM
RACA_COR_SIA = {"01": "Branca", "02": "Preta", "03": "Parda", "04": "Amarela", "05": "Indígena"}  # APAC
ESCOLARIDADE_RHC = {
    "1": "Nenhuma", "2": "Fundamental incompleto", "3": "Fundamental completo",
    "4": "Médio", "5": "Superior incompleto", "6": "Superior completo",
}
ESCOLARIDADE_GRUPO = {
    "Nenhuma": "Até fundamental incompleto", "Fundamental incompleto": "Até fundamental incompleto",
    "Fundamental completo": "Fundamental completo/médio", "Médio": "Fundamental completo/médio",
    "Superior incompleto": "Superior", "Superior completo": "Superior",
}
ESCOLARIDADE_GRUPO_ORDEM = ["Até fundamental incompleto", "Fundamental completo/médio", "Superior"]
ESTADO_CONJUGAL_RHC = {"1": "Solteira", "2": "Casada", "3": "Viúva", "4": "Separada", "5": "União consensual"}
ESCOLARIDADE_SIM = {"1": "Nenhuma", "2": "1 a 3 anos", "3": "4 a 7 anos", "4": "8 a 11 anos", "5": "12 anos ou mais"}
ORIGEM_ENCAMINHAMENTO = {"1": "SUS", "2": "Não SUS", "3": "Conta própria"}
DIAG_TRAT_ANTERIOR = {"1": "Sem diagnóstico e sem tratamento", "2": "Com diagnóstico e sem tratamento",
                      "3": "Com diagnóstico e com tratamento", "4": "Outros"}
PRIMEIRO_TRATAMENTO_RHC = {"1": "Nenhum", "2": "Cirurgia", "3": "Radioterapia", "4": "Quimioterapia",
                           "5": "Hormonioterapia", "6": "Transplante de medula", "7": "Imunoterapia", "8": "Outras"}
TRATAMENTO_PAINEL = {"1": "Cirurgia", "2": "Quimioterapia", "3": "Radioterapia", "4": "Quimioterapia + Radioterapia"}

# Morfologia CID-O (4 primeiros dígitos de TIPOHIST)
HISTOLOGIA = {"8500": "Carcinoma ductal", "8520": "Carcinoma lobular"}
HISTOLOGIA_ORDEM = ["Carcinoma ductal", "Carcinoma lobular", "Outros tipos"]

# Intervalos de tempo (dias) usados em todos os cadernos
INTERVALOS_DIAS = [0, 30, 60, 90, 180, 365, 730, 10_000]
INTERVALOS_ROTULOS = ["até 30 dias", "31 a 60 dias", "61 a 90 dias", "91 dias a 6 meses",
                      "6 meses a 1 ano", "1 a 2 anos", "mais de 2 anos"]

# CNES
MAMOGRAFOS = {"02", "03", "17", "19"}  # TIPEQUIP 1: comando simples, estereotaxia, digital, tomossíntese
HABILITACOES = {
    "UNACON/CACON": {"1701", "1702", "1703", "1706", "1707", "1708", "1709", "1712", "1713"},
    "Radioterapia": {"1704", "1707", "1715"},
    "Diagnóstico de mama (SDM)": {"1720"},
}
ATENCAO_PRIMARIA = {"01", "02", "32", "45", "71"}  # posto, centro de saúde/UBS, móvel fluvial, USF, apoio à saúde da família


def natureza_juridica(cod: str) -> str:
    """Natureza jurídica (tabela da Receita/CONCLA) agrupada em quatro categorias."""
    c = (cod or "").strip()
    if not c or not c[0].isdigit():
        return SEM_INFO
    return {"1": "Público", "2": "Privado", "3": "Filantrópico/sem fins lucrativos", "4": "Privado"}.get(c[0], SEM_INFO)


# SIGTAP: procedimentos de quimioterapia/hormonioterapia de mama usados como proxy de subtipo
# (tabela TB_SIGTAW do TAB_SIA). Ver notebook 04.
PROC_ANTI_HER2 = {
    "0304020419", "0304020427", "0304020435", "0304020443", "0304040185", "0304050261", "0304050270",
    "0304050288", "0304050296", "0304050300", "0304050318", "0304050350",
}
# Receptor hormonal positivo: hormonioterapia, inibidores de CDK4/6 e procedimentos "receptor positivo"
PROC_RECEPTOR_POSITIVO = {
    "0304020338", "0304020346", "0304020354", "0304020451", "0304020460", "0304020478", "0304020486",
    "0304020494", "0304040193", "0304050040", "0304050083", "0304050091", "0304050105", "0304050113",
    "0304050121", "0304050245",
}
PROC_QUIMIO = {
    "0304020133", "0304020141", "0304040029", "0304040037", "0304050059", "0304050067", "0304050075",
    "0304050130", "0304050148",
}
SUBTIPO_ORDEM = ["Luminal (receptor hormonal +)", "HER2 positivo", "Provável triplo-negativo"]

# SISCAN (dicionário TAB_SISCAN do DATASUS)
RACA_COR_SISCAN = {"01": "Branca", "02": "Preta", "03": "Amarela", "04": "Parda", "05": "Indígena"}
ESCOLARIDADE_SISCAN_GRUPO = {"1": "Até fundamental incompleto", "2": "Até fundamental incompleto",
                             "3": "Fundamental completo/médio", "4": "Fundamental completo/médio", "5": "Superior"}
RECEPTOR = {"01": "Positivo", "02": "Negativo", "03": "Não realizado"}
HISTOLOGIA_SISCAN = {"06": "Carcinoma ductal", "07": "Carcinoma ductal", "08": "Carcinoma lobular"}
INVASIVO_SISCAN = {"06", "07", "08", "09", "10", "11", "12"}  # exclui in situ (01-04) e Paget sem tumor (05)
GRAU_HISTOLOGICO = {"01": "I", "02": "II", "03": "III"}
TAMANHO_TUMOR = {"01": "Menos de 2 cm", "02": "2 a 5 cm", "03": "Mais de 5 cm"}
DETECCAO_LESAO = {"01": "Palpável (exame clínico)", "02": "Não palpável (imagem)"}
INTERVALO_RESULTADO = {"1": "0 a 10 dias", "2": "11 a 20 dias", "3": "21 a 30 dias", "4": "Mais de 30 dias"}
BIRADS = {"1": "0", "2": "1", "3": "2", "4": "3", "5": "4", "6": "5", "7": "6"}  # código -> categoria BI-RADS
INDICACAO_MAMOGRAFIA = {"01": "Diagnóstica", "02": "Rastreamento"}

# CNES: equipamentos de imagem (TIPEQUIP 1) agrupados; radioterapia (TIPEQUIP 12) só existe a partir de 08/2025
EQUIPAMENTOS = {
    "Mamógrafo": {"02", "03", "17", "19"},
    "Tomógrafo": {"11", "26", "27", "28", "29", "30"},
    "Ressonância magnética": {"12", "32", "33", "34", "35"},
    "Ultrassom": {"13", "14", "15"},
    "PET/CT": {"18"},
    "Gama câmara (medicina nuclear)": {"01"},
}
