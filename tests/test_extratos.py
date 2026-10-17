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


def test_sobras_com_o_cache_commitado_da_ia(saida):
    """E6b parte 2 (D42), resposta real em cache_ia/: os 5 aportes da EduAbroad passam na prova (Σ = Ponte) e
    viram IA; os 2 PIX ENVIADO (a IA recusou o vínculo) têm decisão humana explícita do Lucca (D44)."""
    pasta, r = saida
    lan = {l["id_saida"]: l for l in _csv(pasta, "lancamentos_classificados.csv")}
    humanos = sorted(k for k, l in lan.items() if l["metodo"] == "HUMANO")
    assert humanos == ["LAN-AURORA-L28", "LAN-AURORA-L69"]
    for h in humanos:
        assert (lan[h]["conta_codigo"], lan[h]["confianca"], lan[h]["lado_contrapartida"]) == ("2.1.01.001", "", "D")
        assert lan[h]["regra_aplicada"] == f"decisoes_humanas.aurora_{h[11:]}_2026_09"
    ia = sorted(k for k, l in lan.items() if l["metodo"] == "IA")
    assert ia == ["LAN-MERIDIANO-MRD2026090036", "LAN-MERIDIANO-MRD2026090180", "LAN-MERIDIANO-MRD2026090340",
                  "LAN-MERIDIANO-MRD2026090484", "LAN-MERIDIANO-MRD2026090636"]
    assert all(lan[k]["conta_codigo"] == "2.1.02.001" and Decimal(lan[k]["confianca"]) >= Decimal("0.8") for k in ia)
    pend = {p["id_saida"] for p in _csv(pasta, "pendencias.csv")}
    assert not any("AURORA-L28" in p or "AURORA-L69" in p for p in pend)
    assert len(r["extratos"]["ia"].decisoes) == 5 and r["extratos"]["ia"].chamadas_api == 0  # decididas não vão à IA
    edu = next(a for a in r["extratos"]["conf"].aportes if a["cnpj"] == "16181276000153")
    assert edu["sobra"] == 0 and not edu["nao_conferido"]


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
    assert p["ref_origem"] == "L92" and p["valor_brl"] == "-300000.00" and "01/10" in p["motivo"]


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


def test_nomes_da_orbe_so_para_ec_sem_vinculo(cadastro, orbe, regras):
    import copy
    from tarvo.cadastro import adicionar_nomes_orbe
    cad = copy.deepcopy(cadastro)
    adicionar_nomes_orbe(cad, orbe.transacoes, regras)
    assert set(cad.nomes_extras) == {"EC1076801732"}  # só a Atlas: os outros ECs já têm CNPJ na planilha
    assert lojista_por_nome_bancario(cad, "ATLAS IDIOMAS LTDA")[0] == "EC1076801732"
    assert lojista_por_nome_bancario(cad, "EDU ABROAD CONSULTORIA LTD")[0] is None  # fica para a IA (D37)


def test_total_de_pendencias(saida):
    tipos = sorted(p["tipo"] for p in _csv(saida[0], "pendencias.csv"))
    assert len(tipos) == 11 and "IA_REPROVADA" not in tipos and "SEM_REGRA" not in tipos
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


def test_sugestao_aprovada_no_csv(saida):
    (s,) = _csv(saida[0], "sugestoes_regra.csv")
    assert (s["id_sugestao"], s["status"]) == ("SUG-001", "APROVADA") and "vigência 2026-10-01" in s["aprovacao"]


def test_decisao_humana_so_vale_para_a_linha_exata(cadastro, regras):
    """Mesma ref e descrição, valor diferente (outro mês, outra linha): a decisão não se aplica."""
    from tarvo.classificacao.decisoes import aplicar_decisoes_humanas
    from tarvo.classificacao.por_regra import classificar_por_regra
    from tarvo.leitores.plano_contas import contas_lancaveis, ler_plano_contas
    from tarvo.modelo import LancamentoBancario
    from datetime import date as _date
    plano = contas_lancaveis(ler_plano_contas(next(DADOS.glob("04_*"))))
    lan = LancamentoBancario("AURORA", "L28", _date(2026, 9, 9), "PIX ENVIADO EDU ABROAD CONSULTORIA LTD", Decimal("-1.00"), None, "t")
    r = classificar_por_regra([lan], {"L28": 28}, plano, regras, cadastro, (2026, 9))
    avisos = aplicar_decisoes_humanas([r], regras, (2026, 9))
    assert r.linhas[0]["conta_codigo"] == "" and r.sem_regra
    assert any("aurora_L28_2026_09" in a for a in avisos)


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
    for l in linhas[1:]:
        if l[0] == "LAN-AURORA-L28":
            l[col] = ""
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

