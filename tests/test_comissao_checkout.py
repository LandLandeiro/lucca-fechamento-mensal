"""Comissão CHECKOUT por transação e por lojista (valores conferidos contra as fontes).

Cada caso cita a linha de origem e a conta feita à mão: bruto × taxa contratada, truncado
no centavo (D09).
"""

from datetime import date
from decimal import Decimal

from tarvo.cadastro import interpretar_vigencia, taxa_contratada


def _com(checkout, ref):
    return checkout.por_transacao[ref]


def _total(checkout, cnpj):
    return next(c["comissao_brl"] for c in checkout.comissoes if c["cnpj"] == cnpj)


# --- cadastro ---------------------------------------------------------------

def test_ec_mapeado_manualmente(cadastro):
    # cadastro.mapeamento_ec_confirmado (Helena 20:24); a planilha não tem esses ECs
    assert cadastro.por_ec["1043300981"] == "66564512000199"  # Novo Horizonte Intercambio (R28)
    assert cadastro.por_ec["1043396662"] == "78576234000179"  # Horizonte Viagens (R8)
    assert cadastro.por_ec["1038867654"] == "07752116000126"  # Kiwi Experience (R9)


def test_ec_da_planilha(cadastro):
    assert cadastro.por_ec["1074504011"] == "95927868000148"  # Rota Global R10
    assert "1076801732" not in cadastro.por_ec  # Atlas: sem linha na aba vigente


def test_vigencia():
    assert interpretar_vigencia("até 14/09/2026").contem(date(2026, 9, 14))
    assert not interpretar_vigencia("até 14/09/2026").contem(date(2026, 9, 15))
    assert interpretar_vigencia("a partir de 15/09/2026").contem(date(2026, 9, 15))
    assert interpretar_vigencia("01/01/2026").contem(date(2026, 8, 22))
    assert interpretar_vigencia("INATIVO") is None


def test_bridge_troca_de_taxa_em_15_09(cadastro, regras):
    antes = taxa_contratada(cadastro, "22224579000109", "Crédito à vista", date(2026, 9, 14), regras)
    depois = taxa_contratada(cadastro, "22224579000109", "Crédito à vista", date(2026, 9, 15), regras)
    assert (antes.taxa, depois.taxa) == (Decimal("0.0259"), Decimal("0.0219"))


# --- por transação ----------------------------------------------------------

def test_rota_tx88428676_e_estorno(checkout):
    # L1056: 10.420,13 × 3,59% (contratada, 7–12x; a Orbe cobrou 4,09%) = 374,0826… → 374,08
    venda = _com(checkout, "TX88428676")
    assert venda.taxa_contratada == Decimal("0.0359")
    assert venda.comissao == Decimal("374.08")
    assert "estornada em 2026-09-23 por TX88446419" in venda.nota
    # L1471: estorno da mesma venda, pela taxa da venda original
    assert _com(checkout, "TX88446419").comissao == Decimal("-374.08")


def test_oxford_estorno_de_venda_de_agosto(checkout):
    # L39: −2.193,16 × 3,79% (Oxford R20, 7–12x, vigente em 22/08) = −83,1207… → −83,12
    e = _com(checkout, "TX88444848")
    assert e.cnpj == "23109187000161"
    assert e.taxa_contratada == Decimal("0.0379")
    assert e.comissao == Decimal("-83.12")


def test_bridge_venda_de_15_09_pela_taxa_nova(checkout):
    # L938: a Orbe cobrou 2,59%; contratada desde 15/09 = 2,19% (R7)
    c = _com(checkout, "TX88428053")
    assert c.taxa_contratada == Decimal("0.0219")
    assert c.comissao == (c.transacao.valor_bruto * Decimal("0.0219")).quantize(Decimal("0.01"), rounding="ROUND_DOWN")


def test_antecipacao_e_reversao(checkout):
    # L60 AN88444882: 31.765,12 × 2,10% = 667,0675… → 667,06
    assert _com(checkout, "AN88444882").comissao == Decimal("667.06")
    # L252 AN88445076 (Kiwi) 52.314,21 × 2,10% = 1.098,598… → 1.098,59; L266 AN88445093 a anula
    assert _com(checkout, "AN88445076").comissao == Decimal("1098.59")
    assert _com(checkout, "AN88445093").comissao == Decimal("-1098.59")


def test_truncamento_nunca_arredonda(checkout):
    for c in checkout.por_transacao.values():
        exato = c.transacao.valor_bruto * c.taxa_contratada
        if c.transacao.tipo_lancamento != "REVERSAO ANTECIPACAO":
            assert abs(c.comissao) <= abs(exato) < abs(c.comissao) + Decimal("0.01")


# --- Casa do Estudante ------------------------------------------------------

def test_casa_do_estudante_setembro_zerado(checkout):
    casa = [c for c in checkout.por_transacao.values() if c.cnpj == "00520815000100"]
    de_setembro = [c for c in casa if (c.transacao.data_venda_original or c.transacao.data_movimento) >= date(2026, 9, 1)]
    assert len(de_setembro) == 118
    assert all(c.taxa_contratada == 0 and c.comissao == 0 for c in de_setembro)


def test_casa_do_estudante_total_e_o_estorno_de_agosto(checkout):
    # L433 TX88445133: estorno de venda de 21/08 (fora da condição especial, que começa em 01/09);
    # pela regra 20:06 usa a taxa de 21/08: débito 1,49% × 369,39 = 5,5039… → −5,50
    e = _com(checkout, "TX88445133")
    assert (e.taxa_contratada, e.comissao) == (Decimal("0.0149"), Decimal("-5.50"))
    assert _total(checkout, "00520815000100") == Decimal("-5.50")


# --- pendências e totais ----------------------------------------------------

def test_atlas_vira_pendencia(checkout):
    assert all(c.transacao.cod_estabelecimento != "1076801732" for c in checkout.por_transacao.values())
    p = next(p for p in checkout.pendencias if p.ref_origem == "EC1076801732")
    assert p.tipo == "SEM_CONTRATO_VIGENTE" and p.quem_decide == "comercial"
    assert p.valor_brl == Decimal("7876.05")  # Σ valor_taxa da Atlas (informativo)
    assert sum(1 for pid in checkout.em_pendencia.values() if pid == p.id_saida) == 57


def test_toda_linha_em_um_lugar_so(orbe, checkout):
    calculadas = set(checkout.por_transacao)
    pendentes = set(checkout.em_pendencia)
    assert calculadas.isdisjoint(pendentes)
    assert calculadas | pendentes == {t.ref_origem for t in orbe.transacoes}


def test_ordem_deterministica_comissao_desc_depois_cnpj(checkout):
    chaves = [(-c["comissao_brl"], c["cnpj"]) for c in checkout.comissoes]
    assert chaves == sorted(chaves)
    ordem = [c["cnpj"] for c in checkout.comissoes]
    assert ordem.index("08780784000120") < ordem.index("20987545000140")  # Campus 9.335,56 antes de Vela 9.315,05


def test_totais_conferem_com_a_exploracao(checkout):
    # Conferência independente (docs/EXPLORACAO.md, centavos inteiros em outro programa):
    # Σ valor_taxa 231.880,36 − Atlas 7.876,05 − Casa cobrado 15.391,27 + Casa contratado (−5,50)
    # − divergências Rota 1.546,28 e Bridge 29,95 = 207.031,31
    assert sum(c["comissao_brl"] for c in checkout.comissoes) == Decimal("207031.31")
    assert _total(checkout, "95927868000148") == Decimal("15620.55")  # Rota: 17.166,83 − 1.546,28
    assert _total(checkout, "22224579000109") == Decimal("11915.51")  # Bridge: 11.945,46 − 29,95
