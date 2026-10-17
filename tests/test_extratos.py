"""Extratos: leitores, classificação por regra e conferências (casos = linhas reais de setembro)."""

import csv
from datetime import date
from decimal import Decimal

import pytest

from tarvo.__main__ import executar
from tarvo.cadastro import lojista_por_nome_bancario, normalizar_nome
from tarvo.classificacao.conferencias import dias_uteis_entre
from tarvo.classificacao.por_regra import classificar_por_regra
from tarvo.leitores.extrato_aurora import ler_extrato_aurora
from tarvo.leitores.extrato_meridiano import ler_extrato_meridiano
from tarvo.leitores.plano_contas import contas_lancaveis, ler_plano_contas
from tarvo.modelo import LancamentoBancario
from conftest import DADOS, RAIZ

AURORA = DADOS / "05a_extrato_banco_aurora_cc4471_set2026.csv"
MERIDIANO = DADOS / "05b_extrato_banco_meridiano_cc90233_set2026.ofx"
PLANO = DADOS / "04_plano_de_contas_fenix_erp.csv"


@pytest.fixture(scope="module")
def aurora():
    return ler_extrato_aurora(AURORA)


@pytest.fixture(scope="module")
def meridiano():
    return ler_extrato_meridiano(MERIDIANO)


@pytest.fixture(scope="module")
def plano():
    return contas_lancaveis(ler_plano_contas(PLANO))


@pytest.fixture(scope="module")
def saida(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("saida_extratos")
    return pasta, executar(DADOS, pasta, RAIZ / "regras.yaml")


def _csv(pasta, nome):
    with open(pasta / nome, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def _lan(pasta, ida):
    return next(l for l in _csv(pasta, "lancamentos_classificados.csv") if l["id_saida"] == ida)


# --- leitores ---------------------------------------------------------------

def test_aurora_linhas_e_saldos(aurora):
    assert len(aurora.lancamentos) == 84
    assert (aurora.lancamentos[0].ref_origem, aurora.lancamentos[-1].ref_origem) == ("L9", "L92")
    assert aurora.saldo_inicial == Decimal("612334.81") and aurora.saldo_final == Decimal("-1920088.60")
    assert sum(l.valor for l in aurora.lancamentos) == Decimal("-2532423.41")
    assert aurora.avisos == [] and aurora.linhas_invalidas == []  # saldo corrido bate linha a linha
    assert not any("SALDO" in l.descricao for l in aurora.lancamentos)


def test_meridiano_ofx(meridiano):
    assert len(meridiano.lancamentos) == 100
    assert meridiano.saldo_inicial is None and meridiano.saldo_final == Decimal("1320453.26")
    l = next(x for x in meridiano.lancamentos if x.ref_origem == "MRD2026090008")
    assert l.descricao == "PIX RECEB MUNDO ABERTO INTERCÂMBIO"  # cp1252, não ASCII
    assert (l.data, l.valor) == (date(2026, 9, 1), Decimal("115004.93"))


def test_plano_so_analiticas_lancaveis(plano):
    assert len(plano) == 32
    assert "1.1.01" not in plano and "4.2" not in plano  # sintéticas
    assert plano["2.1.03.004"].natureza == "C"  # IRRF a recolher: natureza C, mas recebe débito na baixa (D12)


# --- nome do lojista no extrato (prefixo exato, D31) ---------------------------

@pytest.mark.parametrize("texto, cnpj", [
    ("ROTA GLOBAL INTERCAMBIO LT", "95927868000148"),  # banco corta o nome da planilha
    ("KIWI EXPERIENCE TURISMO LT", "07752116000126"),  # nome da planilha ("Kiwi Experience") é prefixo
    ("HORIZONTE VIAGENS E TURISM", "78576234000179"),  # e não "Novo Horizonte Intercambio"
    ("NOVO HORIZONTE INTERCÂMB", "66564512000199"),
    ("ANDES EXPEDICÕES LTDA", "85694108000184"),  # acento diferente do da planilha
])
def test_lojista_por_prefixo_exato(cadastro, texto, cnpj):
    assert lojista_por_nome_bancario(cadastro, texto)[0] == cnpj


@pytest.mark.parametrize("texto", ["EDU ABROAD CONSULTORIA LTD", "ATLAS IDIOMAS LTDA", "KIWIX TURISMO"])
def test_sem_prefixo_exato_nao_casa(cadastro, texto):
    # "EDU ABROAD" × "EduAbroad" (espaço): não é similaridade, não casa; Atlas não está na aba vigente;
    # "KIWIX" não casa com "Kiwi Experience" (fronteira de palavra)
    assert lojista_por_nome_bancario(cadastro, texto)[0] is None


def test_normalizar_nome():
    assert normalizar_nome("  Dublin Hub  Intercâmbio ") == "DUBLIN HUB INTERCAMBIO"


# --- classificação por regra (cada regra com o seu caso de setembro) ----------

@pytest.mark.parametrize("ida, conta, regra", [
    ("LAN-AURORA-L9", "1.1.03.001", "aurora.orbe_recebivel"),
    ("LAN-AURORA-L10", "4.2.01", "aurora.tarifa"),
    ("LAN-AURORA-L12", "1.1.09.001", "aurora.transferencia_meridiano"),
    ("LAN-AURORA-L15", "2.1.04.001", "aurora.folha_mes_anterior"),
    ("LAN-AURORA-L16", "4.2.02", "aurora.condominio"),
    ("LAN-AURORA-L18", "2.1.01.001", "aurora.repasse_lojista"),
    ("LAN-AURORA-L42", "2.1.03.003", "aurora.iss"),
    ("LAN-AURORA-L47", "4.2.03", "aurora.cloud"),
    ("LAN-AURORA-L48", "4.2.04", "aurora.assinatura"),
    ("LAN-AURORA-L50", "1.1.09.002", "aurora.pix_sem_identificacao"),
    ("LAN-AURORA-L53", "4.2.06", "aurora.servicos_contabeis"),  # PIX ENVIADO CONTABILIDADE: não é repasse
    ("LAN-AURORA-L54", "2.1.04.002", "aurora.inss"),
    ("LAN-AURORA-L55", "2.1.04.003", "aurora.fgts"),
    ("LAN-AURORA-L57", "2.1.03.004", "aurora.irrf"),
    ("LAN-AURORA-L65", "2.1.01.001", "aurora.devolucao_pix_lojista"),
    ("LAN-AURORA-L86", "2.1.03.001", "aurora.pis"),
    ("LAN-AURORA-L87", "2.1.03.002", "aurora.cofins"),
    ("LAN-MERIDIANO-MRD2026090003", "2.1.02.001", "meridiano.aporte_lojista"),
    ("LAN-MERIDIANO-MRD2026090094", "2.1.02.001", "meridiano.liquidacao_ponte"),
    ("LAN-MERIDIANO-MRD2026090103", "4.2.01", "meridiano.tarifa"),
    ("LAN-MERIDIANO-MRD2026090107", "1.1.09.001", "meridiano.mesma_titularidade"),
    ("LAN-MERIDIANO-MRD2026090132", "1.1.03.002", "meridiano.repasse_comissao_ponte"),
    ("LAN-MERIDIANO-MRD2026090143", "1.1.02.001", "meridiano.aplicacao_automatica"),
    ("LAN-MERIDIANO-MRD2026090254", "1.1.02.001", "meridiano.resgate_automatico"),
    ("LAN-MERIDIANO-MRD2026090292", "4.2.05", "meridiano.seguro"),
    ("LAN-MERIDIANO-MRD2026090586", "4.3.01", "meridiano.iof"),
    ("LAN-MERIDIANO-MRD2026090425", "2.1.02.001", "meridiano.aporte_lojista"),  # "PONTE AEREA" sem acento
    ("LAN-MERIDIANO-MRD2026090680", "3.2.01", "meridiano.rendimento_aplicacao"),  # H37
    ("LAN-AURORA-L34", "2.1.01.001", "aurora.repasse_lojista"),  # Atlas: nome da Orbe do EC sem vínculo (D35)
    ("LAN-AURORA-L60", "2.1.01.001", "aurora.repasse_lojista"),
])
def test_regra_por_caso_de_setembro(saida, ida, conta, regra):
    l = _lan(saida[0], ida)
    assert (l["conta_codigo"], l["regra_aplicada"], l["metodo"], l["confianca"]) == (conta, regra, "REGRA", "1.00")


def test_lado_pelo_sinal(saida):
    assert _lan(saida[0], "LAN-AURORA-L57")["lado_contrapartida"] == "D"  # pagar IRRF debita conta de natureza C
    assert _lan(saida[0], "LAN-AURORA-L9")["lado_contrapartida"] == "C"
    assert _lan(saida[0], "LAN-AURORA-L9")["contrapartida_banco"] == "1.1.01.001"
    assert _lan(saida[0], "LAN-MERIDIANO-MRD2026090003")["contrapartida_banco"] == "1.1.01.002"


def test_eduabroad_por_regra_pelo_nome_da_orbe(saida):
    """D52 (corrige a D35): 'EDU ABROAD CONSULTORIA' é o nome da Orbe do EC 1020660828, ligado à EduAbroad na
    planilha; as 7 linhas casam por REGRA, a IA fica com 0 linhas e as decisões L28/L69 não se aplicam."""
    pasta, r = saida
    lan = {l["id_saida"]: l for l in _csv(pasta, "lancamentos_classificados.csv")}
    assert {l["metodo"] for l in lan.values()} == {"REGRA"}
    edu = {k: l for k, l in lan.items() if "EDU ABROAD" in l["descricao"]}
    assert len(edu) == 7
    assert {(l["banco"], l["regra_aplicada"], l["conta_codigo"]) for l in edu.values()} == {
        ("AURORA", "aurora.repasse_lojista", "2.1.01.001"), ("MERIDIANO", "meridiano.aporte_lojista", "2.1.02.001")}
    assert r["extratos"]["ia"].decisoes == []
    assert not [a for a in r["avisos"] if "decisoes_humanas" in a.local]  # substituídas: nem aviso
    aporte = next(a for a in r["extratos"]["conf"].aportes if a["cnpj"] == "16181276000153")
    assert aporte["aportes"] == aporte["operacoes"] == Decimal("394222.69") and aporte["sobra"] == 0


def _lanc(desc, valor, ref="X1", data=date(2026, 9, 10)):
    return LancamentoBancario("AURORA", ref, data, desc, Decimal(valor), arquivo_origem="t.csv")


def test_folha_de_outro_mes_nao_casa(regras, cadastro, plano):
    # "FOLHA <mês anterior>": folha de setembro paga em setembro não é baixa do provisionado de agosto
    r = classificar_por_regra([_lanc("PAGTO SALARIOS - FOLHA 09/2026", "-100.00")], {}, plano, regras, cadastro, (2026, 9))
    assert r.linhas[0]["metodo"] == "HUMANO" and "não é o anterior" in r.sem_regra[0][1]
    r = classificar_por_regra([_lanc("PAGTO SALARIOS - FOLHA 09/2026", "-100.00")], {}, plano, regras, cadastro, (2026, 10))
    assert r.linhas[0]["conta_codigo"] == "2.1.04.001"  # em outubro, a folha de setembro é a do mês anterior


def test_sinal_errado_nao_casa(regras, cadastro, plano):
    r = classificar_por_regra([_lanc("TED RECEBIDA 99.876.669/0001-09 ORBE ADQUIRENCIA SA", "-10.00")], {}, plano,
                              regras, cadastro, (2026, 9))
    assert r.linhas[0]["metodo"] == "HUMANO"


# --- conferências -----------------------------------------------------------

def test_dias_uteis():
    assert dias_uteis_entre(date(2026, 9, 30), date(2026, 10, 1)) == 1
    assert dias_uteis_entre(date(2026, 9, 11), date(2026, 9, 14)) == 1  # sexta → segunda


def test_transferencias(saida):
    _, r = saida
    pares = {s.ref_origem: (p.ref_origem if p else None) for s, p in r["extratos"]["conf"].transferencias}
    assert pares == {"L12": "MRD2026090107", "L44": "MRD2026090274", "L58": "MRD2026090454", "L92": None}
    p = next(p for p in _csv(saida[0], "pendencias.csv") if p["tipo"] == "TRANSFERENCIA_EM_TRANSITO")
    assert p["ref_origem"] == "L92" and p["valor_brl"] == "-300000.00"
    assert "conferir no extrato de outubro" in p["motivo"] and p["quem_decide"] == "analista (conferir em outubro)"


def test_aporte_sem_operacao_ponte_aerea(saida):
    p = next(p for p in _csv(saida[0], "pendencias.csv") if p["tipo"] == "APORTE_SEM_OPERACAO")
    assert (p["ref_origem"], p["valor_brl"]) == ("MRD2026090425", "18240.00")
    # Bagagem (duplicata PC-0926-0162) não acusa: a duplicata conta uma vez nas operações
    assert not any("50900987000179" in x["id_saida"] for x in _csv(saida[0], "pendencias.csv"))
    # EduAbroad: aportes identificados pela IA e provados (D42) → soma fecha, sem pendência
    assert not any(x["tipo"] == "APORTE_DIVERGENTE" for x in _csv(saida[0], "pendencias.csv"))


def test_resgate_acima_do_aplicado(saida):
    _, r = saida
    resgates = {x["resgate"].ref_origem: x["excesso"] for x in r["extratos"]["conf"].resgates}
    assert resgates == {"MRD2026090254": Decimal("392.00"), "MRD2026090445": 0, "MRD2026090670": 0}
    # D36: saldo aplicado anterior a 01/09 → reportado, sem pendência
    assert not any(p["tipo"] == "RESGATE_ACIMA_DO_APLICADO" for p in _csv(saida[0], "pendencias.csv"))
    assert _lan(saida[0], "LAN-MERIDIANO-MRD2026090254")["conta_codigo"] == "1.1.02.001"  # linha inteira


# --- validador --------------------------------------------------------------

def test_validador_ok(saida):
    assert saida[1]["erros_validacao"] == []


def _reescrever(caminho, f):
    with open(caminho, encoding="utf-8", newline="") as fh:
        linhas = list(csv.reader(fh, delimiter=";"))
    with open(caminho, "w", encoding="utf-8", newline="") as fh:
        csv.writer(fh, delimiter=";", lineterminator="\n").writerows(f(linhas))


def test_validador_extratos_recusa(saida, tmp_path, aurora, meridiano, plano):
    from tarvo.saida.validador import validar_saida

    for p in saida[0].iterdir():
        (tmp_path / p.name).write_bytes(p.read_bytes())

    def adulterar(linhas):
        cab = linhas[0]
        i_conta, i_valor = cab.index("conta_codigo"), cab.index("valor")
        for l in linhas[1:]:
            if l[0] == "LAN-AURORA-L10":
                l[i_conta] = "4.2"  # sintética
            if l[0] == "LAN-AURORA-L16":
                l[i_valor] = "-28450.01"
        return [l for l in linhas if l[0] != "LAN-AURORA-L90"]

    _reescrever(tmp_path / "lancamentos_classificados.csv", adulterar)
    _reescrever(tmp_path / "rastro.csv", lambda ls: [l for l in ls if l[0] != "LAN-AURORA-L90"])
    erros = validar_saida(
        tmp_path,
        refs_extratos={e.arquivo: {(l.ref_origem, e.linhas_arquivo[l.ref_origem]) for l in e.lancamentos} for e in (aurora, meridiano)},
        saldos_extratos={"AURORA": (aurora.saldo_inicial, aurora.saldo_final)},
        contas_lancaveis=set(plano),
    )
    assert any("1 lançamentos sem classificação" in e for e in erros)
    assert any("AURORA: Σ lançamentos" in e for e in erros)
    assert any("conta 4.2 não existe ou não aceita lançamento" in e for e in erros)


def test_nomes_da_orbe_pelo_ec(cadastro, orbe, regras):
    """D52: EC ligado → o nome da Orbe vale para o CNPJ do EC; EC sem vínculo (Atlas) → "EC<n>"."""
    import copy
    from tarvo.cadastro import adicionar_nomes_orbe
    cad = copy.deepcopy(cadastro)
    adicionar_nomes_orbe(cad, orbe.transacoes, regras)
    assert cad.nomes_orbe["16181276000153"] == {"EDU ABROAD CONSULTORIA", "EDUABROAD"}
    assert cad.nomes_orbe["EC1076801732"] == {"ATLAS IDIOMAS"}
    assert lojista_por_nome_bancario(cad, "ATLAS IDIOMAS LTDA")[0] == "EC1076801732"
    assert lojista_por_nome_bancario(cad, "EDU ABROAD CONSULTORIA LTD")[0] == "16181276000153"
    assert lojista_por_nome_bancario(cadastro, "EDU ABROAD CONSULTORIA LTD")[0] is None  # só a planilha: não casa


def test_total_de_pendencias(saida):
    tipos = sorted(p["tipo"] for p in _csv(saida[0], "pendencias.csv"))
    assert len(tipos) == 15 and "IA_REPROVADA" not in tipos and "SEM_REGRA" not in tipos
    assert tipos.count("CONTESTACAO_PONTE") == 3


def _lan_edu(data, desc="PIX RECEB EDU ABROAD CONSULTORIA L", valor="1000.00", banco="MERIDIANO"):
    from datetime import date as _date
    from tarvo.modelo import LancamentoBancario
    return LancamentoBancario(banco, "X1", _date.fromisoformat(data), desc, Decimal(valor), None, "teste")


@pytest.mark.parametrize("data, banco, desc, valor, esperado", [
    ("2026-10-02", "MERIDIANO", "PIX RECEB EDU ABROAD CONSULTORIA L", "1000.00", "REGRA"),
    ("2026-10-15", "AURORA", "PIX ENVIADO EDU ABROAD CONSULTORIA LTD", "-1000.00", "REGRA"),
    ("2026-09-30", "MERIDIANO", "PIX RECEB EDU ABROAD CONSULTORIA L", "1000.00", "HUMANO"),
    ("2026-09-09", "AURORA", "PIX ENVIADO EDU ABROAD CONSULTORIA LTD", "-1000.00", "HUMANO"),
])
def test_alias_edu_abroad_so_a_partir_de_outubro(cadastro, regras, data, banco, desc, valor, esperado):
    """D44: SUG-001 aprovada, alias com vigencia_inicio 2026-10-01; não muda setembro."""
    from tarvo.classificacao.por_regra import classificar_por_regra
    from tarvo.leitores.plano_contas import contas_lancaveis, ler_plano_contas
    plano = contas_lancaveis(ler_plano_contas(next(DADOS.glob("04_*"))))
    lan = _lan_edu(data, desc, valor, banco)
    r = classificar_por_regra([lan], {"X1": 1}, plano, regras, cadastro, (int(data[:4]), int(data[5:7])))
    assert r.linhas[0]["metodo"] == esperado
    if esperado == "REGRA":
        assert r.lojista_por_lancamento[(banco, "X1")] == "16181276000153"


def test_setembro_sem_sugestao_de_regra(saida):
    """Nenhuma linha foi para a IA, então não há alias a propor (o arquivo sai só com o cabeçalho)."""
    assert _csv(saida[0], "sugestoes_regra.csv") == []


def _regras_com_decisao_ativa(regras):
    """Cópia das regras com a decisão L28 sem a marca `substituida` (para testar o mecanismo)."""
    import copy
    r = copy.deepcopy(regras)
    del r["decisoes_humanas.aurora_L28_2026_09"]["substituida"]
    return r


def test_decisao_humana_so_vale_para_a_linha_exata(cadastro, regras):
    """Mesma ref e descrição, valor diferente (outro mês, outra linha): a decisão não se aplica."""
    from tarvo.classificacao.decisoes import aplicar_decisoes_humanas
    from tarvo.classificacao.por_regra import classificar_por_regra
    from tarvo.leitores.plano_contas import contas_lancaveis, ler_plano_contas
    from tarvo.modelo import LancamentoBancario
    from datetime import date as _date
    plano = contas_lancaveis(ler_plano_contas(next(DADOS.glob("04_*"))))
    ativa = _regras_com_decisao_ativa(regras)
    lan = LancamentoBancario("AURORA", "L28", _date(2026, 9, 9), "PIX ENVIADO EDU ABROAD CONSULTORIA LTD", Decimal("-1.00"), None, "t")
    r = classificar_por_regra([lan], {"L28": 28}, plano, ativa, cadastro, (2026, 9))
    avisos = aplicar_decisoes_humanas([r], ativa, (2026, 9))
    assert r.linhas[0]["conta_codigo"] == "" and r.sem_regra
    assert any("aurora_L28_2026_09" in a for a in avisos)
    # a linha exata recebe a decisão (HUMANO com a conta decidida)
    lan = LancamentoBancario("AURORA", "L28", _date(2026, 9, 9), "PIX ENVIADO EDU ABROAD CONSULTORIA LTD", Decimal("-14147.48"), None, "t")
    r = classificar_por_regra([lan], {"L28": 28}, plano, ativa, cadastro, (2026, 9))
    assert aplicar_decisoes_humanas([r], ativa, (2026, 9)) == []
    assert (r.linhas[0]["metodo"], r.linhas[0]["conta_codigo"]) == ("HUMANO", "2.1.01.001")


def test_decisao_substituida_nao_se_aplica_nem_avisa(cadastro, regras):
    """D52: L28/L69 ficam no regras.yaml como histórico ('substituída pela regra')."""
    from tarvo.classificacao.decisoes import aplicar_decisoes_humanas
    from tarvo.classificacao.por_regra import classificar_por_regra
    from tarvo.leitores.plano_contas import contas_lancaveis, ler_plano_contas
    from tarvo.modelo import LancamentoBancario
    from datetime import date as _date
    assert "substituída pela regra" in regras["decisoes_humanas.aurora_L28_2026_09"]["substituida"]
    plano = contas_lancaveis(ler_plano_contas(next(DADOS.glob("04_*"))))
    lan = LancamentoBancario("AURORA", "L28", _date(2026, 9, 9), "PIX ENVIADO EDU ABROAD CONSULTORIA LTD", Decimal("-14147.48"), None, "t")
    r = classificar_por_regra([lan], {"L28": 28}, plano, regras, cadastro, (2026, 9))  # cadastro sem nomes da Orbe
    assert aplicar_decisoes_humanas([r], regras, (2026, 9)) == []
    assert r.linhas[0]["metodo"] == "HUMANO" and r.linhas[0]["conta_codigo"] == ""


def test_validador_recusa_humano_com_conta_sem_decisao(saida, tmp_path):
    import csv as _csvmod
    from tarvo.saida.validador import validar_saida
    pasta, _ = saida
    for p in pasta.iterdir():
        (tmp_path / p.name).write_bytes(p.read_bytes())
    caminho = tmp_path / "lancamentos_classificados.csv"
    with open(caminho, encoding="utf-8", newline="") as f:
        linhas = list(_csvmod.reader(f, delimiter=";"))
    col = linhas[0].index("regra_aplicada")
    col_metodo = linhas[0].index("metodo")
    for l in linhas[1:]:
        if l[0] == "LAN-AURORA-L28":  # HUMANO com conta, sem decisão registrada
            l[col], l[col_metodo] = "", "HUMANO"
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        _csvmod.writer(f, delimiter=";", lineterminator="\n").writerows(linhas)
    from tarvo.leitores.plano_contas import contas_lancaveis, ler_plano_contas
    plano = set(contas_lancaveis(ler_plano_contas(next(DADOS.glob("04_*")))))
    erros = validar_saida(tmp_path, contas_lancaveis=plano)
    assert any("LAN-AURORA-L28" in e and "sem decisão explícita" in e for e in erros)


def test_saldo_negativo_do_aurora_nao_vira_pendencia(saida):
    """Q-M (Helena 22:34): o saldo negativo é a conta garantida do Aurora; não é pendência."""
    pasta, r = saida
    aurora = r["extratos"]["leituras"][0]
    saldo, minimo = aurora.saldo_inicial, aurora.saldo_inicial
    for lan in aurora.lancamentos:
        saldo += lan.valor
        minimo = min(minimo, saldo)
    assert minimo < 0  # o caso existe em setembro
    pend = _csv(pasta, "pendencias.csv")
    assert not any("saldo" in p["tipo"].lower() or "garantida" in p["motivo"].lower() or "saldo negativo" in p["motivo"].lower()
                   for p in pend)


def _resgate_sem_saldo(rendimento: bool):
    """Aplicação de 100,00 e resgate de 150,00 no mês: o resgate excede o aplicado em 50,00."""
    from datetime import date as _date
    from tarvo.classificacao.conferencias import conferir
    from tarvo.modelo import LancamentoBancario
    lan = [LancamentoBancario("MERIDIANO", "A1", _date(2026, 10, 5), "APLIC AUTOMATICA", Decimal("-100.00"), None, "t"),
           LancamentoBancario("MERIDIANO", "R1", _date(2026, 10, 9), "RESGATE AUTOMATICO", Decimal("150.00"), None, "t")]
    regra = {("MERIDIANO", "A1"): "meridiano.aplicacao_automatica", ("MERIDIANO", "R1"): "meridiano.resgate_automatico"}
    if rendimento:
        lan.append(LancamentoBancario("MERIDIANO", "Y1", _date(2026, 10, 31), "RENDIMENTO APLIC AUTOMATICA", Decimal("3.00"), None, "t"))
        regra[("MERIDIANO", "Y1")] = "meridiano.rendimento_aplicacao"
    return conferir(regra, lan, {}, {}, [], {}, None, "SALDO_APLICADO_ANTERIOR_SE_HA_RENDIMENTO")


def test_resgate_acima_com_linha_de_rendimento_e_saldo_anterior():
    """D49 (refina a D36): com linha própria de rendimento no mês, o excesso é saldo aplicado anterior."""
    r = _resgate_sem_saldo(rendimento=True)
    assert r.resgates[0]["excesso"] == Decimal("50.00") and r.pendencias == []


def test_resgate_acima_sem_linha_de_rendimento_vira_pendencia_para_a_helena():
    r = _resgate_sem_saldo(rendimento=False)
    (p,) = r.pendencias
    assert (p.tipo, p.valor_brl, p.quem_decide) == ("RESGATE_ACIMA_DO_APLICADO", Decimal("50.00"), "Helena")
    assert "2026-10-01" in p.motivo and "09/" not in p.motivo  # data derivada do lançamento, nada fixo


def test_setembro_tem_linha_de_rendimento(regras):
    from tarvo.regras import valor_da_regra
    assert valor_da_regra(regras, "classificacao_extratos.conferencias")["resgate_acima_do_aplicado"] == \
        "SALDO_APLICADO_ANTERIOR_SE_HA_RENDIMENTO"



def test_confianca_nunca_vazia(saida, tmp_path):
    """D54: REGRA = 1.00; HUMANO com conta (decisão registrada) = 1.00; HUMANO sem conta = 0.00; IA = a da IA.
    O validador recusa confiança vazia ou fora de 0–1."""
    from tarvo.saida.validador import validar_saida
    pasta, _ = saida
    lan = _csv(pasta, "lancamentos_classificados.csv")
    assert all(l["confianca"] == "1.00" for l in lan)  # setembro: tudo por regra
    for p in pasta.iterdir():
        (tmp_path / p.name).write_bytes(p.read_bytes())

    def adulterar(linhas):
        i = linhas[0].index("confianca")
        for l in linhas[1:]:
            if l[0] == "LAN-AURORA-L9":
                l[i] = ""
            if l[0] == "LAN-AURORA-L10":
                l[i] = "1.20"
        return linhas
    _reescrever(tmp_path / "lancamentos_classificados.csv", adulterar)
    erros = validar_saida(tmp_path, contas_lancaveis=None, refs_extratos={})
    assert any("LAN-AURORA-L9: confiança ''" in e for e in erros)
    assert any("LAN-AURORA-L10: confiança '1.20'" in e for e in erros)


def test_humano_sem_conta_tem_confianca_zero(regras, cadastro, plano):
    r = classificar_por_regra([_lanc("PIX ENVIADO FORNECEDOR DESCONHECIDO", "-10.00")], {}, plano, regras, cadastro, (2026, 9))
    assert (r.linhas[0]["metodo"], r.linhas[0]["conta_codigo"], r.linhas[0]["confianca"]) == ("HUMANO", "", Decimal("0"))


@pytest.fixture(scope="module")
def cadastro_com_orbe(cadastro, orbe, regras):
    import copy
    from tarvo.cadastro import adicionar_nomes_orbe
    cad = copy.deepcopy(cadastro)
    adicionar_nomes_orbe(cad, orbe.transacoes, regras)
    return cad


@pytest.mark.parametrize("texto", ["VELA TRANSPORTES", "CANGURU MUDANCAS", "VELA", "MAPLE ST", "ROTA G"])
def test_prefixo_de_uma_palavra_nao_casa(cadastro_com_orbe, texto):
    """D58: "Vela" e "Canguru" são uma palavra só na planilha; um fornecedor que começa igual não é o lojista.
    E um texto cortado precisa de 2 palavras inteiras do nome."""
    assert lojista_por_nome_bancario(cadastro_com_orbe, texto)[0] is None


@pytest.mark.parametrize("texto, cnpj", [
    ("VELA TURISMO EDUCACIONAL L", "20987545000140"),  # pelo nome da Orbe do EC da Vela
    ("CANGURU INTERCAMBIOS LTDA", "53857560000123"),
    ("MUNDO ABERTO INTERC", "17217888000111"),  # "Mundo Aberto": 2 palavras, nome completo
    ("NORDICA EDUCACAO INTERNA", "14760206000124"),  # cortado pelo banco, 2 palavras inteiras
])
def test_nomes_reais_de_setembro_continuam_casando(cadastro_com_orbe, texto, cnpj):
    assert lojista_por_nome_bancario(cadastro_com_orbe, texto)[0] == cnpj


def test_fornecedor_com_prefixo_de_lojista_fica_sem_regra(regras, cadastro_com_orbe, plano):
    """Antes, "PIX ENVIADO VELA TRANSPORTES" virava repasse à Vela por REGRA, com confiança 1.00, em silêncio."""
    lan = [_lanc("PIX ENVIADO VELA TRANSPORTES", "-500.00", "X1"), _lanc("PIX ENVIADO CANGURU MUDANCAS", "-800.00", "X2")]
    r = classificar_por_regra(lan, {}, plano, regras, cadastro_com_orbe, (2026, 9))
    assert [(l["metodo"], l["conta_codigo"]) for l in r.linhas] == [("HUMANO", ""), ("HUMANO", "")]
    assert len(r.sem_regra) == 2  # vão para a IA, e o código prova antes de aceitar


def _transferencia(saida_data, entrada_data, feriados):
    from tarvo.classificacao.conferencias import conferir
    lan = [LancamentoBancario("AURORA", "L1", saida_data, "TRANSF ENTRE CONTAS P/ BCO MERIDIANO", Decimal("-1000.00"), None, "a"),
           LancamentoBancario("MERIDIANO", "M1", entrada_data, "TED RECEBIDA TARVO PAGAMENTOS LTDA - MESMA TITULARIDADE",
                              Decimal("1000.00"), None, "m")]
    regra = {("AURORA", "L1"): "aurora.transferencia_meridiano", ("MERIDIANO", "M1"): "meridiano.mesma_titularidade"}
    return conferir(regra, lan, {}, {}, [], {}, None, "PENDENCIA", None, feriados)


def test_feriado_nao_e_dia_util(regras):
    """D59: sexta 09/10/2026 → terça 13/10 (12/10 é feriado nacional) = 1 dia útil: transferência casada, sem
    pendência. Sem o calendário, eram 2 dias úteis e duas pendências falsas (em trânsito + sem origem)."""
    from tarvo.regras import valor_da_regra
    feriados = frozenset(date.fromisoformat(str(d)) for d in valor_da_regra(regras, "calendario.feriados_nacionais"))
    assert {date(2026, 10, 12), date(2026, 11, 2), date(2026, 11, 15), date(2026, 11, 20), date(2026, 12, 25)} <= feriados
    assert dias_uteis_entre(date(2026, 10, 9), date(2026, 10, 13), feriados) == 1
    r = _transferencia(date(2026, 10, 9), date(2026, 10, 13), feriados)
    assert r.pendencias == [] and r.transferencias[0][1] is not None
    sem = _transferencia(date(2026, 10, 9), date(2026, 10, 13), frozenset())
    assert sorted(p.tipo for p in sem.pendencias) == ["TRANSFERENCIA_EM_TRANSITO", "TRANSFERENCIA_SEM_ORIGEM"]


def test_ano_sem_feriados_no_calendario_gera_aviso(tmp_path):
    texto = (RAIZ / "regras.yaml").read_text(encoding="utf-8")
    regras = tmp_path / "regras.yaml"
    import re
    novo, n = re.subn(r"(feriados_nacionais:.*\n\s*valor: )\[[^\]]*\]", r"\g<1>[2025-12-25]", texto)
    assert n == 1
    regras.write_text(novo, encoding="utf-8")
    r = executar(DADOS, tmp_path / "s", regras)
    assert r["erros_validacao"] == [] and any("sem feriados de 2026" in a.mensagem for a in r["avisos"])


def test_devolucao_volta_para_a_conta_do_repasse(saida, regras):
    """D65 (Q-R 2, Q-I a, Q-X 2): a devolução L65 baixa a conta onde o repasse à Mundo Aberto foi registrado."""
    lan = {l["id_saida"]: l for l in _csv(saida[0], "lancamentos_classificados.csv")}
    repasse, devolucao = lan["LAN-AURORA-L26"], lan["LAN-AURORA-L65"]
    assert "MUNDO ABERTO" in repasse["descricao"] and repasse["data"] == "2026-09-09"
    assert devolucao["conta_codigo"] == repasse["conta_codigo"] == "2.1.01.001"
    assert (repasse["lado_contrapartida"], devolucao["lado_contrapartida"]) == ("D", "C")  # a obrigação volta
    assert "baixa a conta onde o repasse estava" in devolucao["motivo_conta"]
    assert "Q-R 2" in regras["classificacao_extratos.aurora.devolucao_pix_lojista"]["aceite"]
