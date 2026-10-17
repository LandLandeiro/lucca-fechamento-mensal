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
    assert sum(Decimal(n["valor_brl"]) for n in notas) == Decimal("207036.81")  # 207.031,31 + 5,50 (Casa fora)
    rota = next(n for n in notas if n["tomador_cnpj"] == "95927868000148")
    assert rota["id_saida"] == "NF-95927868000148-CHECKOUT" and rota["valor_brl"] == "15620.55"
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
    assert (nf["tomador_cnpj"], nf["tomador"], nf["valor_brl"]) == ("75374179000146", "Ponte Câmbio S.A.", "39542.89")
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


def test_conferencia_do_repasse(saida):
    pasta, _ = saida
    p = next(p for p in _csv(pasta, "pendencias.csv") if p["tipo"] == "CONFERENCIA_REPASSE")
    assert p["valor_brl"] == "506.09" and p["quem_decide"] == "Helena"
    for trecho in ("TED da Ponte previsto para 06/10", "(78073.59)", "seria 39036.80", "faturamos 39542.89",
                   "Diferença 506.09 = 917.03", "− 410.94 (duplicata PC-0926-0162, a Ponte pagaria a mais; avisar)"):
        assert trecho in p["motivo"], trecho
    rastro = [l for l in _csv(pasta, "rastro.csv") if l["id_saida"] == p["id_saida"]]
    assert sum(Decimal(l["valor"]) for l in rastro) == Decimal("506.09")
    assert {l["ref_origem"] for l in rastro} == {"PC-0926-0210", "PC-0926-0326", "PC-0926-0491", "PC-0926-0545", "PC-0926-0162"}


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
