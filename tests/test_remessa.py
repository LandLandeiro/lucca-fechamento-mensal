"""Remessa: leitor do e-mail da Ponte, elegibilidade, comissão e divergência de spread.

Casos conferidos à mão contra o anexo (aba Operações; R = linha da planilha).
"""

from datetime import date
from decimal import Decimal

import pytest

from tarvo.cadastro import taxa_contratada
from tarvo.calculos.divergencias import divergencias_remessa
from tarvo.calculos.remessa import classificar_remessa, comissao_remessa, participacao
from tarvo.leitores.ponte_email import ler_email, ler_operacoes
from conftest import DADOS

EML = DADOS / "03_email_ponte_cambio_relatorio_set2026.eml"


@pytest.fixture(scope="module")
def ponte(regras):
    mail = ler_email(EML)
    from tarvo.regras import valor_da_regra
    return ler_operacoes(mail.anexo_xlsx, EML.name, mail.nome_anexo, valor_da_regra(regras, "ponte.linhas_que_nao_sao_dados"))


@pytest.fixture(scope="module")
def cls(ponte, cadastro, regras):
    return classificar_remessa(ponte.operacoes, ponte.competencia, cadastro, regras)


@pytest.fixture(scope="module")
def rem(cls, cadastro, regras):
    return comissao_remessa(cls, cadastro, regras)


@pytest.fixture(scope="module")
def divr(cls, cadastro, regras):
    return divergencias_remessa(cls, cadastro, regras)


def _rastro(rem, ref):
    return [l for l in rem.rastro if l["ref_origem"] == ref]


# --- leitor -----------------------------------------------------------------

def test_le_o_anexo_dentro_do_eml():
    mail = ler_email(EML)
    assert mail.nome_anexo == "PonteCambio_Relatorio_TARVO_092026.xlsx"
    assert "50% (cinquenta por cento) do spread realizado" in mail.corpo.replace("=\n", "")


def test_operacoes_e_totais(ponte):
    assert ponte.competencia == (2026, 9)  # "Competência: 09/2026" (R3)
    assert len(ponte.operacoes) == ponte.total_linhas_dados == 233
    assert ponte.linhas_invalidas == [] and ponte.avisos == []
    assert ponte.totais_declarados == {"Total de operações:": Decimal("233"), "Spread total R$:": Decimal("78073.59")}
    assert sum(o.spread_brl for o in ponte.operacoes) == Decimal("78073.59")


def test_numeros_sem_ruido_de_float(ponte):
    op = next(o for o in ponte.operacoes if o.ref_origem == "PC-0926-0014")  # R13: 72214.46000000001
    assert op.valor_brl == Decimal("72214.46") and op.spread_brl == Decimal("892.19")


# --- elegibilidade ----------------------------------------------------------

def test_pc_0926_0002_liquidada_em_outubro_entra(cls, rem):
    # R6: contratada 30/09, liquidada 01/10 → competência pela contratação
    op = next(o for o, _ in cls.elegiveis if o.ref_origem == "PC-0926-0002")
    assert (op.data_contratacao, op.data_liquidacao) == (date(2026, 9, 30), date(2026, 10, 1))
    # 50% × 262,01 = 131,005 → meio centavo para cima → 131,01 (o exemplo da própria Helena, Q-H d)
    (linha,) = _rastro(rem, "PC-0926-0002")
    assert linha["id_saida"] == "COM-34671260000100-REMESSA" and linha["valor"] == Decimal("131.01")
    assert "liquidada em 2026-10-01" in linha["nota"]


def test_pc_0926_0162_conta_uma_vez(rem):
    linhas = _rastro(rem, "PC-0926-0162")
    assert {(l["id_saida"], l["linha_arquivo"]) for l in linhas} == {
        ("COM-50900987000179-REMESSA", 76),  # fica a primeira
        ("EXC-REMESSA-DUPLICATA", 77),  # a "reprocessada" fica fora, anotada
    }
    exc = next(l for l in linhas if l["linha_arquivo"] == 77)
    assert exc["valor"] == Decimal("821.88") and "reprocessada" in exc["nota"]


def test_pc_0926_0210_spread_negativo_fora_da_comissao(cls, rem, divr):
    # R96: Ponte Aérea, spread −687,52, "Taxa travada no pedido (D-1)"
    assert all(o.ref_origem != "PC-0926-0210" for o, _ in cls.elegiveis)
    (exc,) = _rastro(rem, "PC-0926-0210")
    assert exc["id_saida"] == "EXC-REMESSA-SPREAD_NEGATIVO" and exc["valor"] == Decimal("-687.52")
    d = next(x for x in divr.linhas if x["ref_origem"] == "PC-0926-0210")
    assert d["linha_negocio"] == "REMESSA" and d["direcao"] == "COBROU_A_MENOS"
    assert "trava vencida (2h); em contestação com a Ponte (Helena)" in d["motivo"] and "desconto" not in d["motivo"]
    # D28: round((−1,5523% − 1,5% padrão) × PTAX × ME) = −1.351,87 (valor cheio contra o contrato, D21)
    assert d["diferenca_brl"] == Decimal("-1351.87")
    assert d["participacao_tarvo_no_spread"] == Decimal("-343.76")  # 50% × −687,52


def test_negativos_d21_d28(divr):
    neg = {d["ref_origem"]: d for d in divr.linhas if d["spread_brl"] < 0}
    assert neg["PC-0926-0326"]["diferenca_brl"] == Decimal("-1001.30")  # Canguru (R141), pela coluna "Spread %"
    assert sum(d["diferenca_brl"] for d in neg.values()) == Decimal("-3565.98")
    # −172,515 → −172,52 (meio para longe do zero)
    assert sum(d["participacao_tarvo_no_spread"] for d in neg.values()) == Decimal("-917.03")
    assert all(d["participacao_tarvo_no_spread"] is None for d in divr.linhas if d["spread_brl"] >= 0)


def test_ressalva_conta_normalmente(cls):
    assert any(o.ref_origem == "PC-0926-0089" and o.status_compliance == "APROVADO C/ RESSALVA" for o, _ in cls.elegiveis)
    assert sum(1 for o, _ in cls.elegiveis if o.status_compliance == "APROVADO C/ RESSALVA") == 16


def test_destinos_somam_233(cls, ponte):
    assert len(cls.elegiveis) + len(cls.excluidas) + len(cls.pendentes) == len(ponte.operacoes)
    assert (len(cls.elegiveis), len(cls.excluidas), len(cls.pendentes)) == (228, 5, 0)


# --- comissão ---------------------------------------------------------------

def test_participacao_meio_centavo_longe_do_zero():
    # Q-H: "Meio centavo vai para cima, e no negativo ... -0,005 vira -0,01"
    assert participacao(Decimal("262.01"), Decimal("0.5"), "ROUND_HALF_UP") == Decimal("131.01")
    assert participacao(Decimal("262.03"), Decimal("0.5"), "ROUND_HALF_UP") == Decimal("131.02")
    assert participacao(Decimal("-1.01"), Decimal("0.5"), "ROUND_HALF_UP") == Decimal("-0.51")


def test_total_remessa_e_comparacao_de_arredondamento(rem, cls):
    elegivel = sum(o.spread_brl for o, _ in cls.elegiveis)
    assert elegivel == Decimal("79085.76")  # 78.073,59 − duplicata 821,88 + negativos 1.834,05
    total = sum(c["comissao_brl"] for c in rem.comissoes)
    assert total == Decimal("39543.45")  # previsão independente
    assert sum(a["total_uma_vez"] for a in rem.comparacao_arredondamento) == Decimal("39542.92")


def test_mundo_aberto_comissao_sobre_o_spread_realizado(rem):
    c = next(c for c in rem.comissoes if c["cnpj"] == "17217888000111")
    assert c["comissao_brl"] == Decimal("3547.69")  # Σ por operação de round(50% × Spread R$), excesso incluído (Q-J)


# --- divergência ------------------------------------------------------------

def test_pc_0926_0011_mundo_aberto(divr):
    # R10 (D28): round((1,5007% − 1,20%) × 4,0315 × 2.438,46) = round(29,5605) = 29,56
    d = next(x for x in divr.linhas if x["ref_origem"] == "PC-0926-0011")
    assert d["diferenca_brl"] == Decimal("29.56")
    assert (d["taxa_contratada_pct"], d["taxa_aplicada_pct"]) == (Decimal("0.0120"), Decimal("0.015007"))
    assert d["direcao"] == "COBROU_A_MAIS" and d["decisao"] == "Helena"


def test_mundo_aberto_total(divr):
    mundo = [d for d in divr.linhas if d["cnpj"] == "17217888000111"]
    assert len(mundo) == 23 and sum(d["diferenca_brl"] for d in mundo) == Decimal("1418.85")  # = Q-G (Fox AI)


def test_canguru_padrao_sem_divergencia(divr, cls):
    # planilha R29 J = "padrão" → 1,5% sobre a PTAX; as 22 elegíveis da Canguru estão no ruído (≤ 0,005 p.p.)
    canguru = [d for d in divr.linhas if d["cnpj"] == "53857560000123"]
    assert [d["ref_origem"] for d in canguru] == ["PC-0926-0326"]  # só o spread negativo
    assert "'padrão' → padrão" in canguru[0]["motivo"]
    assert sum(1 for _, c in cls.elegiveis if c == "53857560000123") == 22


def test_so_mundo_aberto_e_negativos_divergem(divr):
    assert len(divr.linhas) == 27  # 23 Mundo Aberto + 4 negativos; nenhum alarme de ruído


def test_casa_do_estudante_remessa_normal(cadastro, regras, divr):
    # condição especial vale só para MDR e antecipação (Helena 20:49): o spread segue o da planilha (R13 J = 1,5%)
    t = taxa_contratada(cadastro, "00520815000100", "Spread remessa", date(2026, 9, 15), regras)
    assert t.taxa == Decimal("0.0150")
    assert taxa_contratada(cadastro, "00520815000100", "Pix", date(2026, 9, 15), regras).taxa == 0
    assert not any(d["cnpj"] == "00520815000100" for d in divr.linhas)


@pytest.mark.parametrize("observacao", [None, "Cliente pediu desconto", "taxa  travada no PEDIDO (d-1)"])
def test_spread_negativo_depende_da_observacao(ponte, cadastro, regras, observacao):
    """D60: só a trava vencida ("Taxa travada no pedido (D-1)", sem diferença de caixa/espaço) vai para
    divergência e contestação; observação vazia ou outra vira pendência para a Helena, fora da comissão."""
    from dataclasses import replace
    ops = [replace(o, observacao=observacao) if o.ref_origem == "PC-0926-0210" else o for o in ponte.operacoes]
    c = classificar_remessa(ops, ponte.competencia, cadastro, regras)
    negativos = {o.ref_origem for o, _ in c.negativos}
    pendentes = {o.ref_origem: tipo for o, tipo, _ in c.pendentes}
    assert {"PC-0926-0326", "PC-0926-0491", "PC-0926-0545"} <= negativos  # os outros 3 continuam trava vencida
    if observacao and "TRAVADA" in observacao.upper():
        assert "PC-0926-0210" in negativos and "PC-0926-0210" not in pendentes
    else:
        assert "PC-0926-0210" not in negativos and pendentes["PC-0926-0210"] == "SPREAD_NEGATIVO_SEM_TRAVA"
        rem = comissao_remessa(c, cadastro, regras)
        (p,) = [p for p in rem.pendencias if p.id_saida == "PEN-SPREAD_NEGATIVO_SEM_TRAVA-PC-0926-0210"]
        assert p.valor_brl < 0 and "Helena" in p.quem_decide
        assert "PC-0926-0210" not in {o.ref_origem for o, _ in c.elegiveis}


def test_criterio_da_mundo_aberto_escrito_com_a_diferenca(divr, regras, cadastro, cls):
    """D64 (Q-X 4, Q-G): Spread % do relatório (1.418,85); pelo Spread R$ seria 1.418,88 (R$ 0,03 a mais)."""
    from tarvo.cadastro import linha_vigente
    from tarvo.formatos import centavos
    regra = regras["remessa.formula_divergencia"]
    assert regra["status"] == "ASSUMO" and "Q-X 4" in regra["aceite"] and "0,03" in regra["valor"]["diferenca_para_spread_rs"]
    mundo = [d for d in divr.linhas if d["cnpj"] == "17217888000111"]
    assert sum(d["diferenca_brl"] for d in mundo) == Decimal("1418.85")
    ops = {o.ref_origem: o for o, _ in cls.elegiveis}
    pelo_spread_rs = sum(centavos(ops[d["ref_origem"]].spread_brl - d["taxa_contratada_pct"] * ops[d["ref_origem"]].ptax_ref
                                  * ops[d["ref_origem"]].valor_me, "ROUND_HALF_UP") for d in mundo)
    assert pelo_spread_rs == Decimal("1418.88")


def test_cnpj_fora_da_planilha_calcula_e_abre_pendencia_de_cadastro(ponte, cadastro, regras):
    """D69 (Q-P 2): calcula a metade do spread e abre pendência de cadastro para o comercial."""
    import copy
    nordica = "14760206000124"
    cad = copy.deepcopy(cadastro)
    del cad.lojistas[nordica]
    del cad.linhas_por_cnpj[nordica]
    c = classificar_remessa(ponte.operacoes, ponte.competencia, cad, regras)
    assert nordica in c.sem_cadastro and any(cn == nordica for _, cn in c.elegiveis)
    rem = comissao_remessa(c, cad, regras)
    com = next(x for x in rem.comissoes if x["cnpj"] == nordica)
    (p,) = [p for p in rem.pendencias if p.id_saida == f"PEN-CADASTRO_REMESSA-{nordica}"]
    assert (p.valor_brl, p.quem_decide) == (com["comissao_brl"], "comercial") and "Q-P 2" in p.motivo
    assert sum(l["valor"] for l in rem.rastro if l["id_saida"] == p.id_saida) == p.valor_brl
