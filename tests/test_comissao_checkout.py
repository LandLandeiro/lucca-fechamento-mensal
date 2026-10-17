"""Comissão CHECKOUT por transação e por lojista (valores conferidos contra as fontes).

Cada caso cita a linha de origem e a conta feita à mão: bruto × taxa contratada, com
arredondamento comum no centavo (meio para longe do zero), linha por linha (Helena 21:13, Q-H).
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
    # L60 AN88444882: 31.765,12 × 2,10% = 667,0675… → 667,07 (a Orbe truncou em 667,06)
    assert _com(checkout, "AN88444882").comissao == Decimal("667.07")
    # L252 AN88445076 (Kiwi) 52.314,21 × 2,10% = 1.098,598… → 1.098,60; L266 AN88445093 a anula
    assert _com(checkout, "AN88445076").comissao == Decimal("1098.60")
    assert _com(checkout, "AN88445093").comissao == Decimal("-1098.60")


def test_arredondamento_comum_por_linha(checkout):
    # Q-H: meio centavo para longe do zero (−0,005 → −0,01); nunca truncar
    for c in checkout.por_transacao.values():
        if c.transacao.tipo_lancamento != "REVERSAO ANTECIPACAO":
            esperado = (c.transacao.valor_bruto * c.taxa_contratada).quantize(Decimal("0.01"), rounding="ROUND_HALF_UP")
            assert c.comissao == esperado, c.transacao.ref_origem


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


def test_totais_conferem_com_a_previsao_independente(checkout):
    # previsão independente do Lucca (outra sessão, sem ver o código) com o arredondamento da Q-H
    assert sum(c["comissao_brl"] for c in checkout.comissoes) == Decimal("207039.73")
    assert _total(checkout, "22224579000109") == Decimal("11916.02")  # Bridge
    assert _total(checkout, "95927868000148") == Decimal("15621.27")  # Rota


def test_linha_da_orbe_fora_da_competencia_nao_aborta(tmp_path):
    """D62 (avaliação simulada): uma linha de agosto no relatório de setembro abortava tudo, sem nenhum CSV.
    Agora vira aviso + pendência, fica fora da comissão e o resto roda (validador OK)."""
    import csv as _csv
    from tarvo.__main__ import executar, main
    from conftest import RAIZ, copiar_dados
    linha = b"TX88410316;01/09/2026;1000960410;OXFORD PREP CURSOS;VENDA"
    dados = copiar_dados(tmp_path / "dados", {"01_orbe_*.csv": [(linha, linha.replace(b"01/09/2026", b"31/08/2026"))]})
    r = executar(dados, tmp_path / "s", RAIZ / "regras.yaml")
    assert r["erros_validacao"] == [] and r["competencia"] == (2026, 9)
    with open(tmp_path / "s" / "pendencias.csv", encoding="utf-8", newline="") as f:
        pend = {p["id_saida"]: p for p in _csv.DictReader(f, delimiter=";")}
    p = pend["PEN-ORBE_FORA_COMPETENCIA-TX88410316"]
    assert (p["ref_origem"], p["valor_brl"]) == ("TX88410316", "42.61") and "2026-08-31" in p["motivo"]
    assert any(a.local == "TX88410316" and "fora da competência" in a.mensagem for a in r["avisos"])
    with open(tmp_path / "s" / "rastro.csv", encoding="utf-8", newline="") as f:
        destinos = {l["id_saida"] for l in _csv.DictReader(f, delimiter=";") if l["ref_origem"] == "TX88410316"}
    assert destinos == {"PEN-ORBE_FORA_COMPETENCIA-TX88410316"}  # fora da comissão (e da nota) da Oxford
    assert main(["--dados", str(dados), "--saida", str(tmp_path / "s2")]) == 0


def test_meses_empatados_e_erro_de_entrada():
    from datetime import date
    from decimal import Decimal
    import pytest
    from tarvo.calculos.comissoes import CompetenciaAmbigua, separar_competencia
    from tarvo.modelo import TransacaoOrbe
    def t(ref, d):
        return TransacaoOrbe(ref, 2, d, "1", "X", "VENDA", "PIX", 1, None, Decimal("1"), Decimal("1"), Decimal("0.01"),
                             Decimal("0.99"), None, None, "o.csv")
    with pytest.raises(CompetenciaAmbigua):
        separar_competencia([t("A", date(2026, 9, 1)), t("B", date(2026, 8, 31))])


def test_alerta_de_antecipacao_so_para_a_atlas(orbe, cadastro, regras):
    """D66 (Q-N 6): Atlas, sem histórico, antecipou 179.592,82 em 15/09 com 55.357,50 vendidos até a data.
    Lojistas com histórico (Oxford, Kiwi, Dublin, Canguru, Mundo Aberto) não alertam: a antecipação deles cobre
    recebíveis de meses anteriores, que não estão nos dados."""
    from decimal import Decimal
    from tarvo.calculos.alertas import alerta_antecipacao
    r = alerta_antecipacao(orbe.transacoes, cadastro, (2026, 9), regras)
    (p,) = r.pendencias
    assert (p.id_saida, p.valor_brl, p.quem_decide) == ("PEN-ALERTA_ANTECIPACAO-EC1076801732", Decimal("124235.32"), "Helena + comercial")
    assert "179592.82 até 2026-09-15" in p.motivo and "55357.50 vendidos" in p.motivo and "Q-N 6" in p.motivo
    assert sum(l["valor"] for l in r.rastro) == p.valor_brl
    assert set(p.ref_origem.split("|")) == {l["ref_origem"] for l in r.rastro}


def test_alerta_vale_para_lojista_novo_da_planilha(orbe, cadastro, regras):
    """Lojista com vigência só a partir do mês também é 'sem histórico'; com estorno de venda de mês anterior, não."""
    import copy
    from dataclasses import replace
    from datetime import date
    from decimal import Decimal
    from tarvo.calculos.alertas import alerta_antecipacao
    from tarvo.cadastro import Vigencia
    canguru = "53857560000123"
    cad = copy.deepcopy(cadastro)
    cad.linhas_por_cnpj[canguru] = [(l, Vigencia(date(2026, 9, 1), None)) for l, _ in cad.linhas_por_cnpj[canguru]]
    ts = [t for t in orbe.transacoes if t.cod_estabelecimento == "1061760196"]
    r = alerta_antecipacao(ts, cad, (2026, 9), regras)
    assert [p.id_saida for p in r.pendencias] == [f"PEN-ALERTA_ANTECIPACAO-{canguru}"]  # 31.765,12 em 01/09 × 1.934,10
    estorno_antigo = replace(ts[0], ref_origem="TXE", tipo_lancamento="ESTORNO", valor_bruto=Decimal("-1.00"),
                             data_venda_original=date(2026, 8, 20))
    assert alerta_antecipacao(ts + [estorno_antigo], cad, (2026, 9), regras).pendencias == []
