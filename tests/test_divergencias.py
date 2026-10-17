"""Divergências de taxa CHECKOUT (casos conferidos à mão contra as linhas da Orbe e da planilha).

diferenca = round(valor_bruto × (taxa aplicada − contratada)), só quando as taxas diferem
(Helena 21:13, Q-H c); o centavo de truncamento da Orbe é resíduo, não divergência.
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
    # L1056 TX88428676: round(10.420,13 × (4,09% − 3,59%)) = 52,10
    # L1471 TX88446419 (estorno da mesma venda): round(−10.420,13 × 0,50%) = −52,10 → líquido 0
    assert _div(divs, "TX88428676") is None
    assert _div(divs, "TX88446419") is None


def test_rota_depois_de_12_09(divs):
    # L749 TX88423647 (12/09, 10x): round(13.256,06 × (4,09% − 3,59%)) = round(66,2803) = 66,28
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
    # L1043 AN88445802 (antecipação 16/09): round(57.456,27 × (2,10% − 0%)) = round(1.206,5817) = 1.206,58
    d = _div(divs, "AN88445802")
    assert d["diferenca_brl"] == Decimal("1206.58")
    assert d["comissao_contratada"] == 0 and d["taxa_contratada_pct"] == 0
    assert "condicao_especial_casa_do_estudante" in d["motivo"]


def test_casa_estorno_de_agosto_e_par_de_setembro_nao_listam(divs):
    # L433 TX88445133: estorno de venda de 21/08 (fora da condição): aplicada 1,49% = contratada → 0
    assert _div(divs, "TX88445133") is None
    # L1779 TX88441917 + L1835 TX88446763 (estorno integral em setembro): +x − x → líquido 0
    assert _div(divs, "TX88441917") is None and _div(divs, "TX88446763") is None


def test_casa_total(divs):
    casa = [d for d in divs.linhas if d["cnpj"] == "00520815000100"]
    assert len(casa) == 116
    assert sum(d["diferenca_brl"] for d in casa) == Decimal("15397.42")


def test_bridge_virada_de_15_09(divs):
    # L938 TX88428053 (15/09, à vista): round(1.124,71 × (2,59% − 2,19% da R7)) = round(4,49884) = 4,50
    d = _div(divs, "TX88428053")
    assert d["diferenca_brl"] == Decimal("4.50")
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
    # previsão independente: 224.004,31 = 207.039,73 + 16.973,65 + resíduo de truncamento (−9,07)
    fonte = sum(c.transacao.valor_taxa for c in checkout.por_transacao.values())
    com = sum(c["comissao_brl"] for c in checkout.comissoes)
    div = sum(d["diferenca_brl"] for d in divs.linhas)
    assert (fonte, com, div, divs.residuo) == (
        Decimal("224004.31"), Decimal("207039.73"), Decimal("16973.65"), Decimal("-9.07")
    )
    assert fonte == com + div + divs.residuo
    assert len(divs.linhas) == 200
    assert divs.grupos_zerados == 5  # 4 vendas da Rota + 1 da Casa, estornadas por inteiro no mês


def test_centavo_de_truncamento_nao_e_divergencia(divs, checkout):
    # L6 TX88410316 (Oxford, à vista 2,59% = contratada R20): 1.645,47 × 2,59% = 42,6177;
    # a Orbe truncou (42,61), nós arredondamos (42,62): mesma taxa → resíduo, não divergência
    c = checkout.por_transacao["TX88410316"]
    assert c.taxa_contratada == Decimal("0.0259")
    assert (c.transacao.valor_taxa, c.comissao) == (Decimal("42.61"), Decimal("42.62"))
    assert _div(divs, "TX88410316") is None


def test_rastro_de_cada_divergencia_fecha(divs):
    for d in divs.linhas:
        assert sum(r["valor"] for r in _rastro(divs, d["ref_origem"])) == d["diferenca_brl"]


def test_sem_zero_negativo_na_saida():
    assert fmt_dinheiro(Decimal("-1021.01") * Decimal("0")) == "0.00"


def test_uma_pendencia_por_lojista_para_decidir(divs):
    """D53: o que a Helena decide vira pendência, uma por lojista, com valor e as transações no rastro.
    Casa (condição especial do comercial): Helena + comercial, com a fala dela da Q-F 2."""
    pend = {p.id_saida: p for p in divs.pendencias}
    assert {(k, p.valor_brl, p.quem_decide) for k, p in pend.items()} == {
        ("PEN-DIVERGENCIA_CHECKOUT-00520815000100", Decimal("15397.42"), "Helena + comercial"),
        ("PEN-DIVERGENCIA_CHECKOUT-95927868000148", Decimal("1546.28"), "Helena"),
        ("PEN-DIVERGENCIA_CHECKOUT-22224579000109", Decimal("29.95"), "Helena"),
    }
    casa = pend["PEN-DIVERGENCIA_CHECKOUT-00520815000100"]
    assert "O que foi cobrado eu devolvo ao lojista, junto com o comercial." in casa.motivo
    assert "cobro a Orbe" not in casa.motivo  # a Casa é devolução ao lojista, não cobrança da Orbe
    assert "Isso eu decido, não vai automático." in pend["PEN-DIVERGENCIA_CHECKOUT-95927868000148"].motivo
    for pid, p in pend.items():
        linhas = [r for r in divs.rastro_pendencias if r["id_saida"] == pid]
        assert sum(r["valor"] for r in linhas) == p.valor_brl
        cnpj = pid.rsplit("-", 1)[1]
        assert set(p.ref_origem.split("|")) == {d["ref_origem"] for d in divs.linhas if d["cnpj"] == cnpj}
