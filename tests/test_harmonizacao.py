import pandas as pd

from mama import codigos as c
from mama import harmonizacao as h


def test_todas_ufs_tem_regiao():
    assert len(c.UF) == 27
    assert {r for _, r in c.UF.values()} == set(c.REGIOES)


def test_uf_de_municipio():
    s = pd.Series(["3550308", "530010", "999999", None])
    assert h.uf_de_municipio(s).tolist()[:2] == ["SP", "DF"]
    assert h.uf_de_municipio(s).isna().tolist()[2:] == [True, True]


def test_municipio6_descarta_ignorados():
    s = pd.Series(["3550308", "350000", "", None])
    assert h.municipio6(s).tolist()[0] == "355030"
    assert h.municipio6(s).iloc[1:].isna().all()


def test_faixas_cobrem_todas_idades():
    f = h.faixa_etaria(pd.Series(range(0, 120)))
    assert f.notna().all()
    assert (f.iloc[39], f.iloc[40], f.iloc[69], f.iloc[70]) == ("<40", "40-49", "50-69", "70+")


def test_estadio_rhc():
    s = pd.Series(["0", "1A", "2B", "3C", "4", "88", "99", "11", " "])
    assert h.estadio_rhc(s).tolist()[:5] == ["0", "I", "II", "III", "IV"]
    assert h.estadio_rhc(s).iloc[5:].isna().all()
    assert h.estadio_avancado(h.estadio_rhc(s)).tolist()[:5] == [0, 0, 0, 1, 1]


def test_mapear_sem_informacao():
    assert h.mapear(pd.Series(["1", "9", None]), c.RACA_COR).tolist() == ["Branca", c.SEM_INFO, c.SEM_INFO]


def test_dias_entre_descarta_negativos():
    a = h.data_br(pd.Series(["01/01/2022", "10/01/2022", "99/99/9999"]))
    b = h.data_br(pd.Series(["31/01/2022", "01/01/2022", "01/01/2022"]))
    d = h.dias_entre(a, b)
    assert d.iloc[0] == 30 and d.iloc[1:].isna().all()


def test_intervalos_de_tempo():
    r = h.intervalo_dias(pd.Series([0, 30, 31, 61, 200, 400, 800])).astype(str).tolist()
    assert r == ["até 30 dias", "até 30 dias", "31 a 60 dias", "61 a 90 dias",
                 "6 meses a 1 ano", "1 a 2 anos", "mais de 2 anos"]


def test_distancia_sao_paulo_rio():
    km = h.distancia_km(-23.55, -46.63, -22.91, -43.17)
    assert 350 < float(km) < 365


def test_natureza_juridica():
    assert c.natureza_juridica("1244") == "Público"
    assert c.natureza_juridica("3069") == "Filantrópico/sem fins lucrativos"
    assert c.natureza_juridica("2062") == "Privado"
    assert c.natureza_juridica("") == c.SEM_INFO


def test_subtipos_sem_sobreposicao():
    assert not (c.PROC_ANTI_HER2 & c.PROC_RECEPTOR_POSITIVO)
    assert not (c.PROC_QUIMIO & (c.PROC_ANTI_HER2 | c.PROC_RECEPTOR_POSITIVO))


def test_equipamentos_sem_sobreposicao():
    vistos = set()
    for codigos in c.EQUIPAMENTOS.values():
        assert not (codigos & vistos)
        vistos |= codigos
    assert c.EQUIPAMENTOS["Mamógrafo"] == c.MAMOGRAFOS


def test_birads_cobre_categorias_0_a_6():
    assert sorted(c.BIRADS.values()) == [str(i) for i in range(7)]


def test_invasivo_exclui_in_situ():
    assert not ({"01", "02", "03", "04", "05"} & c.INVASIVO_SISCAN)
