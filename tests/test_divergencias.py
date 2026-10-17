"""Divergências de taxa CHECKOUT (casos conferidos à mão contra as linhas da Orbe e da planilha).

diferenca = round(valor_bruto × (taxa aplicada − contratada)), só quando as taxas diferem
(Helena 21:13, Q-H c); o centavo de truncamento da Orbe é resíduo, não divergência.
"""

from datetime import date
from decimal import Decimal

import pytest

from tarvo.calculos.divergencias import divergencias_checkout, divergencias_remessa
from tarvo.formatos import fmt_dinheiro


@pytest.fixture(scope="module")
def divs(checkout, cadastro, regras):
    return divergencias_checkout(checkout, cadastro, regras)


def _div(divs, ref):
    return next((d for d in divs.linhas if d["ref_origem"] == ref), None)


def _rastro(divs, ref):
    return [r for r in divs.rastro if r["id_saida"] == f"DIV-{ref}"]


def test_venda_divergente_estornada_no_mes_lista_as_duas_com_sinal(divs):
    """D77 (Q-AB 3): transação por transação; o estorno de uma venda com taxa errada entra com valor negativo.
    L1056 TX88428676: round(10.420,13 × (4,09% − 3,59%)) = 52,10; L1471 TX88446419 (estorno): −52,10 → líquido 0."""
    venda, estorno = _div(divs, "TX88428676"), _div(divs, "TX88446419")
    assert (venda["diferenca_brl"], estorno["diferenca_brl"]) == (Decimal("52.10"), Decimal("-52.10"))
    assert estorno["direcao"] == "ESTORNO_DE_VENDA_ACIMA_DO_CONTRATO" and "o líquido é 0" in estorno["motivo"]  # D86
    assert estorno["motivo"].startswith("estorno de venda cobrada acima do contrato (TX88428676)")
    assert estorno["liquida_com"] == "TX88428676" and venda["liquida_com"] == "TX88446419"


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
    assert "condicoes_especiais[casa_do_estudante_2026]" in d["motivo"]


def test_casa_estorno_de_agosto_nao_lista_e_par_de_setembro_lista(divs):
    # L433 TX88445133: estorno de venda de 21/08 (fora da condição): aplicada 1,49% = contratada → 0, não lista
    assert _div(divs, "TX88445133") is None
    # L1779 TX88441917 + L1835 TX88446763 (estorno integral em setembro): +x e −x, as duas listadas (D77)
    assert _div(divs, "TX88441917")["diferenca_brl"] == -_div(divs, "TX88446763")["diferenca_brl"] != 0


def test_casa_total(divs):
    casa = [d for d in divs.linhas if d["cnpj"] == "00520815000100"]
    assert len(casa) == 118  # 113 vendas, 4 antecipações e 1 estorno de venda de setembro (D77)
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
    assert len(divs.linhas) == 210  # D77: + os 5 pares venda/estorno, cada um com o seu sinal
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
        ("PEN-DEVOLUCAO_CONCESSAO_COMERCIAL-00520815000100", Decimal("15396.77"), "Helena + comercial"),  # D71: valor a devolver
        ("PEN-DIVERGENCIA_CHECKOUT-95927868000148", Decimal("1545.86"), "Helena"),
        ("PEN-DIVERGENCIA_CHECKOUT-22224579000109", Decimal("29.94"), "Helena"),  # D76: contrato (aditivo assinado)  # D63: condição não informada
    }
    casa = pend["PEN-DEVOLUCAO_CONCESSAO_COMERCIAL-00520815000100"]
    assert "O que foi cobrado eu devolvo ao lojista, junto com o comercial." in casa.motivo
    assert "cobro a Orbe" not in casa.motivo  # a Casa é devolução ao lojista, não cobrança da Orbe
    assert "Isso eu decido, não vai automático." in pend["PEN-DIVERGENCIA_CHECKOUT-95927868000148"].motivo
    for pid, p in pend.items():
        linhas = [r for r in divs.rastro_pendencias if r["id_saida"] == pid]
        assert sum(r["valor"] for r in linhas) == p.valor_brl
        cnpj = pid.rsplit("-", 1)[1]
        assert set(p.ref_origem.split("|")) == {d["ref_origem"] for d in divs.linhas if d["cnpj"] == cnpj}


def _com_condicoes(regras, *itens):
    import copy
    r = copy.deepcopy(regras)
    r["cadastro.condicoes_especiais"]["valor"] = r["cadastro.condicoes_especiais"]["valor"] + list(itens)
    return r


ROTA = "95927868000148"
ITEM_ROTA = {"id": "rota_teste", "cnpj": ROTA, "linhas_negocio": ["CHECKOUT"], "taxa": {"MDR": 0.0359},
             "vigencia": {"inicio": "2026-09-12", "fim": "2026-12-31"}, "fonte": "teste"}


def test_segunda_condicao_especial_e_so_um_item_no_regras(cadastro, regras):
    """D61: uma condição nova é um item da lista em regras.yaml; o código não muda (o README promete isso)."""
    from datetime import date
    from tarvo.cadastro import taxa_contratada
    r = _com_condicoes(regras, ITEM_ROTA)
    enc = taxa_contratada(cadastro, ROTA, "Créd. 2-6x", date(2026, 9, 20), r)
    assert enc.taxa == Decimal("0.0359") and "condicoes_especiais[rota_teste]" in enc.fonte
    assert taxa_contratada(cadastro, ROTA, "Créd. 2-6x", date(2026, 9, 5), r).fonte.startswith("planilha")  # antes da vigência
    assert taxa_contratada(cadastro, ROTA, "Antecipação", date(2026, 9, 20), r).fonte.startswith("planilha")  # grupo fora do item
    casa = taxa_contratada(cadastro, "00520815000100", "Débito", date(2026, 9, 20), regras)
    assert casa.taxa == 0 and casa.condicao["quem_decide_divergencia"] == "Helena + comercial"


def test_duas_condicoes_vigentes_nao_escolhe(cadastro, regras):
    from datetime import date
    from tarvo.cadastro import taxa_contratada
    r = _com_condicoes(regras, ITEM_ROTA, {**ITEM_ROTA, "id": "rota_teste_2", "taxa": {"MDR": 0.03}})
    enc = taxa_contratada(cadastro, ROTA, "Débito", date(2026, 9, 20), r)
    assert enc.taxa is None and "2 condições especiais vigentes" in enc.fonte


def test_condicao_especial_de_remessa(cadastro, regras):
    """Grupo REMESSA (spread contratado) também vem da lista, antes da planilha."""
    from datetime import date
    from tarvo.cadastro import condicao_especial
    item = {"id": "mundo_aberto_teste", "cnpj": "17217888000111", "linhas_negocio": ["REMESSA"], "taxa": {"REMESSA": 0.015},
            "vigencia": {"inicio": "2026-09-01", "fim": "2026-09-30"}, "fonte": "teste"}
    enc = condicao_especial(_com_condicoes(regras, item), "17217888000111", "REMESSA", date(2026, 9, 10))
    assert enc.taxa == Decimal("0.015")
    assert condicao_especial(regras, "00520815000100", "REMESSA", date(2026, 9, 10)) is None  # Casa: "Remessa segue normal"


def test_item_sem_campo_obrigatorio_e_erro(cadastro, regras):
    from datetime import date
    from tarvo.cadastro import taxa_contratada
    from tarvo.regras import RegraInvalida
    r = _com_condicoes(regras, {k: v for k, v in ITEM_ROTA.items() if k != "fonte"})
    with pytest.raises(RegraInvalida, match="faltam campos"):
        taxa_contratada(cadastro, ROTA, "Débito", date(2026, 9, 20), r)


def test_natureza_de_cada_divergencia(divs):
    """D63 (Q-N 1, Q-V, Q-T 1): Casa (condição especial) e Bridge (a Orbe aplicou a taxa da linha anterior da
    planilha) são condição não informada à Orbe: devolução ao lojista, sem cobrar a Orbe. Rota: contrato."""
    por_lojista = {}
    for d in divs.linhas:
        por_lojista.setdefault(d["cnpj"], set()).add(d["natureza"])
    assert por_lojista == {"00520815000100": {"condicao_nao_informada"}, "22224579000109": {"contrato_orbe"},
                           "95927868000148": {"contrato_orbe"}}  # D76: "O que decide é o contrato, não o aviso" (Q-AA 1)
    bridge = {p.id_saida: p for p in divs.pendencias}["PEN-DIVERGENCIA_CHECKOUT-22224579000109"]
    assert "Devolver 29.94 ao lojista" in bridge.motivo and "recuperar o mesmo valor da Orbe" in bridge.motivo
    casa = {p.id_saida: p for p in divs.pendencias}["PEN-DEVOLUCAO_CONCESSAO_COMERCIAL-00520815000100"]
    assert "Quem abriu mão da receita fomos nós" in casa.motivo


def test_natureza_da_remessa(divr_saida):
    nat = {}
    for d in divr_saida:
        nat.setdefault(d["natureza"], []).append(d)
    assert {k: len(v) for k, v in nat.items()} == {"spread_acima_contrato": 23, "spread_negativo": 4}
    assert all(d["diferenca_brl"] < 0 for d in nat["spread_negativo"])


@pytest.fixture(scope="module")
def divr_saida(cadastro, regras):
    from tarvo.calculos.remessa import classificar_remessa
    from tarvo.leitores.ponte_email import ler_email, ler_operacoes
    from tarvo.regras import valor_da_regra
    from conftest import DADOS
    eml = next(DADOS.glob("03_*.eml"))
    mail = ler_email(eml)
    ponte = ler_operacoes(mail.anexo_xlsx, eml.name, mail.nome_anexo, valor_da_regra(regras, "ponte.linhas_que_nao_sao_dados"))
    return divergencias_remessa(classificar_remessa(ponte.operacoes, ponte.competencia, cadastro, regras), cadastro, regras).linhas


@pytest.mark.parametrize("valor", ["", "isencao_nao_informada", "spread_negativo"])
def test_validador_recusa_natureza_vazia_ou_fora_da_lista(tmp_path, valor):
    """Vazia, nome antigo, ou natureza de remessa numa linha de checkout: erro."""
    import csv as _csv
    from tarvo.__main__ import executar
    from tarvo.saida.validador import validar_saida
    from conftest import DADOS, RAIZ
    pasta = tmp_path / "s"
    executar(DADOS, pasta, RAIZ / "regras.yaml")
    caminho = pasta / "divergencias_taxa.csv"
    with open(caminho, encoding="utf-8", newline="") as f:
        linhas = list(_csv.reader(f, delimiter=";"))
    i = linhas[0].index("natureza")
    linhas[1][i] = valor  # a primeira é de checkout (ordenadas por diferença)
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        _csv.writer(f, delimiter=";", lineterminator="\n").writerows(linhas)
    assert any("natureza" in e and linhas[1][0] in e for e in validar_saida(pasta))


def test_orbe_cobrando_abaixo_do_contrato_vira_pendencia(regras):
    """Q-N 7 (Helena 09:44): 'Também é divergência e eu decido caso a caso.' Diferença negativa → pendência."""
    from datetime import date
    from tarvo.calculos.divergencias import ResultadoDivergencias, _pendencias_por_lojista
    res = ResultadoDivergencias()
    from tarvo.calculos.comissoes import ComissaoTransacao
    from tarvo.modelo import TransacaoOrbe
    tx = TransacaoOrbe("TXN1", 2, date(2026, 10, 5), "1074504011", "ROTA", "VENDA", "PIX", 1, None, Decimal("1000"),
                       Decimal("0.89"), Decimal("8.90"), Decimal("991.10"), None, None, "o.csv")
    res.linhas = [{"id_saida": "DIV-TXN1", "cnpj": "95927868000148", "ref_origem": "TXN1", "diferenca_brl": Decimal("-12.34"),
                   "valor_a_devolver_brl": Decimal("-12.34"), "natureza": "contrato_orbe", "lojista": "Rota",
                   "data": date(2026, 10, 5)}]
    res.itens_por_div = {"DIV-TXN1": [ComissaoTransacao(tx, "95927868000148", Decimal("0.0213"), Decimal("21.24"), "")]}
    _pendencias_por_lojista(res, {}, regras)
    (p,) = res.pendencias
    assert p.valor_brl == Decimal("-12.34") and "12.34 a menos" in p.motivo and p.quem_decide == "Helena"


def test_estorno_da_casa_usa_a_taxa_de_21_08_sem_isencao(checkout):
    """Q-N 4: 'Vale a taxa da data da venda original ... Em 21/08 a isenção ainda não valia.'"""
    c = checkout.por_transacao["TX88445133"]
    assert c.transacao.data_venda_original == date(2026, 8, 21) and c.condicao is None
    assert c.taxa_contratada > 0 and c.fonte_taxa.startswith("planilha R13")


def test_valor_a_devolver_separado_da_diferenca_da_q_h(divs):
    """D71: diferenca_brl segue a Q-H c (bruto × (aplicada − contratada)); valor_a_devolver_brl = valor cobrado pela
    Orbe − comissão contratada (o lojista recebeu o líquido, Q-U 4). Casa: 15.397,42 × 15.396,77 (116 linhas; o par
    TX88441917/TX88446763, venda e estorno do mês, se anula e não é listado: são as 118 do cálculo linha a linha)."""
    tot = {}
    for d in divs.linhas:
        a = tot.setdefault(d["cnpj"], [0, Decimal(0), Decimal(0)])
        a[0] += 1; a[1] += d["diferenca_brl"]; a[2] += d["valor_a_devolver_brl"]
        assert d["valor_a_devolver_brl"] == d["valor_taxa_orbe"] - d["comissao_contratada"]
    assert tot == {"00520815000100": [118, Decimal("15397.42"), Decimal("15396.77")],
                   "95927868000148": [87, Decimal("1546.28"), Decimal("1545.86")],
                   "22224579000109": [5, Decimal("29.95"), Decimal("29.94")]}


def test_devolver_e_recuperar(divs):
    """D74 (Q-A, Q-U 4): toda divergência de checkout é devolução ao lojista; contrato_orbe também se recupera da
    Orbe (o mesmo valor); condicao_nao_informada não. Devolver − recuperar = Casa + Bridge (Orbe não avisada)."""
    devolver = sum(d["valor_a_devolver_brl"] for d in divs.linhas)
    recuperar = sum(d["valor_a_devolver_brl"] for d in divs.linhas if d["natureza"] == "contrato_orbe")
    assert (devolver, recuperar, devolver - recuperar) == (Decimal("16972.57"), Decimal("1575.80"), Decimal("15396.77"))
    pend = {p.id_saida: p for p in divs.pendencias}
    rota = pend["PEN-DIVERGENCIA_CHECKOUT-95927868000148"].motivo
    assert "Devolver 1545.86 ao lojista" in rota and "recuperar o mesmo valor da Orbe" in rota and "Q-U 4" in rota
    casa = pend["PEN-DEVOLUCAO_CONCESSAO_COMERCIAL-00520815000100"].motivo
    assert "Devolver 15396.77 ao lojista" in casa and "nada a recuperar da Orbe" in casa


def test_devolucao_da_casa_tem_tipo_proprio(divs):
    """D85 (Q-N 1: 'Deixem separado das divergências de contrato'; Q-AA 1): a devolução da Casa, concessão do comercial,
    não é DIVERGENCIA_CHECKOUT; as 118 linhas dela têm decisão 'Helena + comercial'."""
    tipos = {p.id_saida: p.tipo for p in divs.pendencias}
    assert tipos["PEN-DEVOLUCAO_CONCESSAO_COMERCIAL-00520815000100"] == "DEVOLUCAO_CONCESSAO_COMERCIAL"
    assert {tipos["PEN-DIVERGENCIA_CHECKOUT-95927868000148"], tipos["PEN-DIVERGENCIA_CHECKOUT-22224579000109"]} == {"DIVERGENCIA_CHECKOUT"}
    casa = [d for d in divs.linhas if d["cnpj"] == "00520815000100"]
    assert len(casa) == 118 and {d["decisao"] for d in casa} == {"Helena + comercial"}
