"""Notas a emitir e pendências derivadas (Helena 20:47), sobre a saída real do pipeline."""

import csv
from decimal import Decimal

import pytest

from tarvo.__main__ import executar
from conftest import DADOS, RAIZ


@pytest.fixture(scope="module")
def saida(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("saida_notas")
    resumo = executar(DADOS, pasta, RAIZ / "regras.yaml")
    return pasta, resumo


def _csv(pasta, nome):
    with open(pasta / nome, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def test_validador_ok(saida):
    assert saida[1]["erros_validacao"] == []


def test_uma_nota_por_lojista_checkout_positivo(saida):
    pasta, _ = saida
    notas = [n for n in _csv(pasta, "notas_a_emitir.csv") if n["linha_negocio"] == "CHECKOUT"]
    com = {c["cnpj"]: Decimal(c["comissao_brl"]) for c in _csv(pasta, "comissoes_por_lojista.csv") if c["linha_negocio"] == "CHECKOUT"}
    assert len(notas) == 20 == sum(1 for v in com.values() if v > 0)
    assert sum(Decimal(n["valor_brl"]) for n in notas) == Decimal("207045.23")  # 207.039,73 + 5,50 (Casa fora)
    rota = next(n for n in notas if n["tomador_cnpj"] == "95927868000148")
    assert rota["id_saida"] == "NF-95927868000148-CHECKOUT" and rota["valor_brl"] == "15621.27"
    assert rota["discriminacao"] == "Serviço de intermediação de pagamentos (checkout) - competência 09/2026"


def test_casa_negativa_nao_emite_e_vira_pendencia(saida):
    pasta, _ = saida
    assert not any(n["tomador_cnpj"] == "00520815000100" for n in _csv(pasta, "notas_a_emitir.csv"))
    p = next(p for p in _csv(pasta, "pendencias.csv") if p["id_saida"] == "PEN-NF_NEGATIVA-00520815000100")
    assert p["valor_brl"] == "-5.50" and p["quem_decide"] == "Helena"
    assert "TX88445133" in p["motivo"] and "2026-08-21" in p["motivo"]


def test_nota_remessa_unica_para_a_ponte(saida):
    pasta, _ = saida
    (nf,) = [n for n in _csv(pasta, "notas_a_emitir.csv") if n["linha_negocio"] == "REMESSA"]
    assert nf["id_saida"] == "NF-75374179000146-REMESSA"
    assert (nf["tomador_cnpj"], nf["tomador"], nf["valor_brl"]) == ("75374179000146", "Ponte Câmbio S.A.", "39543.45")
    assert nf["discriminacao"] == (
        "Intermediação de operações de câmbio - participação de 50% do spread realizado - competência 09/2026"
    )


def test_rastro_da_nota_e_o_da_comissao(saida):
    pasta, _ = saida
    rastro = _csv(pasta, "rastro.csv")
    nota = sorted((l["ref_origem"], l["linha_arquivo"], l["valor"]) for l in rastro if l["id_saida"] == "NF-95927868000148-CHECKOUT")
    com = sorted((l["ref_origem"], l["linha_arquivo"], l["valor"]) for l in rastro if l["id_saida"] == "COM-95927868000148-CHECKOUT")
    assert nota == com and len(nota) == 159
    nf_rem = [l for l in rastro if l["id_saida"] == "NF-75374179000146-REMESSA"]
    assert len(nf_rem) == 228  # as operações elegíveis


def test_conferencia_do_ted_sem_prever_desconto(saida):
    """Q-K (Helena 22:33): conferir o TED quando cair; não contar que a Ponte vai descontar nada."""
    pasta, _ = saida
    p = next(p for p in _csv(pasta, "pendencias.csv") if p["tipo"] == "CONFERENCIA_REPASSE")
    assert p["quem_decide"] == "Helena" and p["valor_brl"] == "39543.45"  # o faturado
    assert p["motivo"] == (
        "Conferir o TED da Ponte quando cair (previsto 06/10). Faturado: 39543.45 (NF-75374179000146-REMESSA, 228 operações). "
        "Total do relatório da Ponte: "
        "78073.59, que inclui 4 spreads negativos (-1834.05) e a duplicata PC-0926-0162 (821.88), ambos em contestação."
    )
    assert "descont" not in p["motivo"] and "seria" not in p["motivo"]
    rastro = [l for l in _csv(pasta, "rastro.csv") if l["id_saida"] == p["id_saida"]]
    nota = [l for l in _csv(pasta, "rastro.csv") if l["id_saida"] == "NF-75374179000146-REMESSA"]
    assert sum(Decimal(l["valor"]) for l in rastro) == Decimal("39543.45")
    assert sorted((l["ref_origem"], l["linha_arquivo"]) for l in rastro) == sorted((l["ref_origem"], l["linha_arquivo"]) for l in nota)


def test_divergencia_de_remessa_sem_coluna_de_impacto(saida):
    pasta, _ = saida
    linhas = _csv(pasta, "divergencias_taxa.csv")
    assert "impacto_repasse_tarvo" not in linhas[0] and "participacao_tarvo_no_spread" in linhas[0]


def test_contestacao_ponte_uma_pendencia_por_motivo(saida):
    """Q-L (Helena 22:34): uma pendência por motivo, com valor e operações; duplicata conta uma vez e entra na lista."""
    pasta, _ = saida
    pend = {p["id_saida"]: p for p in _csv(pasta, "pendencias.csv") if p["tipo"] == "CONTESTACAO_PONTE"}
    assert {k: v["valor_brl"] for k, v in pend.items()} == {
        "PEN-CONTESTACAO_PONTE-SPREAD_ACIMA_DO_CONTRATADO-17217888000111": "1418.85",
        "PEN-CONTESTACAO_PONTE-SPREAD_NEGATIVO": "-1834.05",
        "PEN-CONTESTACAO_PONTE-DUPLICATA": "821.88",
    }
    assert all(p["quem_decide"] == "Helena" for p in pend.values())
    lista = _csv(pasta, "contestacao_ponte.csv")
    por_pid: dict[str, list] = {}
    for l in lista:
        por_pid.setdefault(l["id_pendencia"], []).append(l)
    assert {k: len(v) for k, v in por_pid.items()} == {
        "PEN-CONTESTACAO_PONTE-SPREAD_ACIMA_DO_CONTRATADO-17217888000111": 23,
        "PEN-CONTESTACAO_PONTE-SPREAD_NEGATIVO": 4,
        "PEN-CONTESTACAO_PONTE-DUPLICATA": 1,
    }
    for pid, ls in por_pid.items():
        assert sum(Decimal(l["valor_contestado_brl"]) for l in ls) == Decimal(pend[pid]["valor_brl"])
    assert {l["ref_origem"] for l in por_pid["PEN-CONTESTACAO_PONTE-SPREAD_NEGATIVO"]} == {
        "PC-0926-0210", "PC-0926-0326", "PC-0926-0491", "PC-0926-0545"}
    (dup,) = por_pid["PEN-CONTESTACAO_PONTE-DUPLICATA"]
    assert (dup["ref_origem"], dup["linha_anexo"]) == ("PC-0926-0162", "77") and "R76" in dup["observacao"]
    # a duplicata continua contando uma vez: a comissão da R76 está no rastro de um COM-, a R77 em EXC-
    rastro = [l for l in _csv(pasta, "rastro.csv") if l["ref_origem"] == "PC-0926-0162" and not l["id_saida"].startswith(("PEN-", "NF-"))]
    assert sorted((l["id_saida"][:4], l["linha_arquivo"]) for l in rastro) == [("COM-", "76"), ("EXC-", "77")]


def test_validador_recusa_contestacao_que_nao_fecha(saida, tmp_path):
    from tarvo.saida.validador import validar_saida

    pasta, _ = saida
    for p in pasta.iterdir():
        (tmp_path / p.name).write_bytes(p.read_bytes())

    def adulterar(linhas):
        linhas[1][4] = "0.00"
        return linhas

    _reescrever(tmp_path / "contestacao_ponte.csv", adulterar)
    erros = validar_saida(tmp_path)
    assert any("contestacao_ponte.csv" in e and "≠ Σ" in e for e in erros)


def test_pendencia_metade_do_excesso_da_mundo_aberto(saida):
    # Q-J (Helena 21:45) + Q-H (b): metade de cada operação, arredondada, depois soma = 709,46 (D45)
    pasta, _ = saida
    p = next(p for p in _csv(pasta, "pendencias.csv") if p["id_saida"] == "PEN-EXCESSO_REMESSA-17217888000111")
    assert p["valor_brl"] == "709.46" and p["quem_decide"] == "Helena"
    assert "1418.85" in p["motivo"] and "sai pelo realizado" in p["motivo"]
    rastro = [l for l in _csv(pasta, "rastro.csv") if l["id_saida"] == p["id_saida"]]
    assert sum(Decimal(l["valor"]) for l in rastro) == Decimal("709.46")
    assert len(rastro) == 23 and all(l["ref_origem"].startswith("PC-") for l in rastro)  # sem linha "arredondamento"


def _reescrever(caminho, f):
    with open(caminho, encoding="utf-8", newline="") as fh:
        linhas = list(csv.reader(fh, delimiter=";"))
    with open(caminho, "w", encoding="utf-8", newline="") as fh:
        csv.writer(fh, delimiter=";", lineterminator="\n").writerows(f(linhas))


def test_validador_recusa_nota_errada(saida, tmp_path):
    from tarvo.saida.validador import validar_saida

    pasta, _ = saida
    for p in pasta.iterdir():
        (tmp_path / p.name).write_bytes(p.read_bytes())

    def adulterar(linhas):
        for l in linhas[1:]:
            if l[0] == "NF-95927868000148-CHECKOUT":
                l[4] = "0.00"
        return linhas

    _reescrever(tmp_path / "notas_a_emitir.csv", adulterar)
    erros = validar_saida(tmp_path)
    assert any("≤ 0" in e for e in erros)
    assert any("Σ comissões CHECKOUT positivas" in e for e in erros)
    assert any("NF-95927868000148-CHECKOUT" in e and "comissão CHECKOUT do lojista" in e for e in erros)
