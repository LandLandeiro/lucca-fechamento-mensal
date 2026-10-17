"""Divergências de taxa CHECKOUT (casos conferidos à mão contra as linhas da Orbe e da planilha).

diferenca = valor_taxa cobrado pela Orbe − bruto × taxa contratada (ambos truncados no centavo).
"""

from decimal import Decimal

import pytest

from tarvo.calculos.divergencias import divergencias_checkout
from tarvo.formatos import fmt_dinheiro


@pytest.fixture(scope="module")
def divs(checkout, cadastro, regras):
    return divergencias_checkout(checkout, cadastro, regras)


def _div(divs, ref):
    return next((d for d in divs.linhas if d["ref_origem"] == ref), None)


def _rastro(divs, ref):
    return [r for r in divs.rastro if r["id_saida"] == f"DIV-{ref}"]


def test_venda_divergente_estornada_no_mes_nao_lista(divs):
    # L1056 TX88428676: Orbe 426,18 (4,09%) − contratada 374,08 (3,59%) = +52,10
    # L1471 TX88446419 (estorno da mesma venda): −426,18 − (−374,08) = −52,10 → líquido 0
    assert _div(divs, "TX88428676") is None
    assert _div(divs, "TX88446419") is None


def test_rota_depois_de_12_09(divs):
    # L749 TX88423647 (12/09, 10x): 13.256,06 × 4,09% = 542,17 (Orbe); × 3,59% = 475,89 → 66,28
    d = _div(divs, "TX88423647")
    assert d["diferenca_brl"] == Decimal("66.28")
    assert (d["taxa_contratada_pct"], d["taxa_aplicada_pct"]) == (Decimal("0.0359"), Decimal("0.0409"))
    assert d["direcao"] == "COBROU_A_MAIS" and d["decisao"] == "Helena"
    assert "planilha R10" in d["motivo"]
    assert [r["valor"] for r in _rastro(divs, "TX88423647")] == [Decimal("66.28")]


def test_rota_antes_de_12_09_nao_diverge(divs, checkout):
    # vendas da Rota até 11/09 vieram com a taxa contratada (ex.: 2,49% à vista)
    rota_ate_11 = [c for c in checkout.por_transacao.values()
                   if c.cnpj == "95927868000148" and c.transacao.tipo_lancamento == "VENDA" and c.transacao.data_movimento.day <= 11]
    assert rota_ate_11 and all(_div(divs, c.transacao.ref_origem) is None for c in rota_ate_11)


def test_casa_do_estudante_tudo_que_a_orbe_cobrou(divs):
    # L1043 AN88445802 (antecipação 16/09): 57.456,27 × 2,10% = 1.206,58; contratada 0 (condição especial)
    d = _div(divs, "AN88445802")
    assert d["diferenca_brl"] == Decimal("1206.58")
    assert d["comissao_contratada"] == 0 and d["taxa_contratada_pct"] == 0
    assert "condicao_especial_casa_do_estudante" in d["motivo"]


def test_casa_estorno_de_agosto_e_par_de_setembro_nao_listam(divs):
    # L433 TX88445133: estorno de venda de 21/08 (fora da condição): Orbe −5,50, contratada −5,50 → 0
    assert _div(divs, "TX88445133") is None
    # L1779 TX88441917 + L1835 TX88446763 (estorno integral em setembro): 9,08 − 9,08 → líquido 0
    assert _div(divs, "TX88441917") is None and _div(divs, "TX88446763") is None


def test_casa_total(divs):
    casa = [d for d in divs.linhas if d["cnpj"] == "00520815000100"]
    assert len(casa) == 116
    assert sum(d["diferenca_brl"] for d in casa) == Decimal("15396.77")


def test_bridge_virada_de_15_09(divs):
    # L938 TX88428053 (15/09, à vista): 1.124,71 × 2,59% = 29,12 (Orbe); × 2,19% (R7, desde 15/09) = 24,63 → 4,49
    d = _div(divs, "TX88428053")
    assert d["diferenca_brl"] == Decimal("4.49")
    assert "planilha R7" in d["motivo"]
    # L859 TX88425274 (13/09) a 2,59%: ainda vigente a R6 → sem divergência
    assert _div(divs, "TX88425274") is None
    bridge = [x for x in divs.linhas if x["cnpj"] == "22224579000109"]
    assert len(bridge) == 5 and sum(x["diferenca_brl"] for x in bridge) == Decimal("29.95")


def test_atlas_fora(divs):
    assert all(d["cnpj"] for d in divs.linhas)
    assert all("1076801732" not in d["motivo"] for d in divs.linhas)
    refs_rastro = {r["ref_origem"] for r in divs.rastro}
    assert not any(ref.startswith("AN88445637") for ref in refs_rastro)  # antecipação da Atlas (L949)


def test_conservacao_prevista(divs, checkout):
    # previsão independente: 224.004,31 = 207.031,31 + 16.973,00
    fonte = sum(c.transacao.valor_taxa for c in checkout.por_transacao.values())
    com = sum(c["comissao_brl"] for c in checkout.comissoes)
    div = sum(d["diferenca_brl"] for d in divs.linhas)
    assert (fonte, com, div) == (Decimal("224004.31"), Decimal("207031.31"), Decimal("16973.00"))
    assert divs.grupos_zerados == 5  # 4 vendas da Rota + 1 da Casa, estornadas por inteiro no mês


def test_rastro_de_cada_divergencia_fecha(divs):
    for d in divs.linhas:
        assert sum(r["valor"] for r in _rastro(divs, d["ref_origem"])) == d["diferenca_brl"]


def test_sem_zero_negativo_na_saida():
    assert fmt_dinheiro(Decimal("-1021.01") * Decimal("0")) == "0.00"
