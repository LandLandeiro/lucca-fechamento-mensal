"""Validação da estrutura de regras.yaml (sem regra de negócio)."""

from pathlib import Path

import pytest

from tarvo.regras import RegraInvalida, RegraPendente, carregar_regras, validar_regras, valor_da_regra

RAIZ = Path(__file__).resolve().parents[1]


def test_regras_yaml_do_projeto_e_valido():
    regras = carregar_regras(RAIZ / "regras.yaml")
    assert regras["orbe.arredondamento_valor_taxa"]["status"] == "SEI"
    assert regras["ponte.tolerancia_spread_pct"]["status"] == "ASSUMO"
    assert regras["ponte.tomador_nf_remessa"]["status"] == "CONFIRMADO"
    assert regras["cadastro.mapeamento_ec_confirmado"]["status"] == "CONFIRMADO"
    assert "checkout.comissao_e_valor_taxa_integral" not in regras  # removida (obsoleta desde 20:05)


def test_regra_pendente_bloqueia_valor():
    regras = validar_regras({"g": {"r": {"valor": None, "status": "PENDENTE", "fonte": None, "pergunta_ref": None}}})
    with pytest.raises(RegraPendente):
        valor_da_regra(regras, "g.r")


def _regra(**kw):
    base = {"valor": 1, "status": "SEI", "fonte": "x", "pergunta_ref": None}
    base.update(kw)
    return {"g": {"r": base}}


@pytest.mark.parametrize(
    "arvore",
    [
        _regra(status="TALVEZ"),
        _regra(status="PENDENTE"),  # PENDENTE com valor
        _regra(valor=None),  # SEI sem valor
        _regra(fonte=None),  # SEI sem fonte
        {"g": {"r": {"valor": 1, "status": "SEI"}}},  # faltam campos
    ],
)
def test_estruturas_invalidas_sao_recusadas(arvore):
    with pytest.raises(RegraInvalida):
        validar_regras(arvore)


def test_pendente_sem_valor_e_aceita():
    regras = validar_regras(_regra(valor=None, status="PENDENTE", fonte=None))
    assert regras["g.r"]["status"] == "PENDENTE"


def test_aprovado_por_em_toda_regra_confirmada(regras):
    """Q-S (Helena 09:49): taxa e condição comercial quem aprova é o comercial (ela registra); regra de fechamento, ela."""
    confirmadas = {k: r for k, r in regras.items() if r["status"] == "CONFIRMADO"}
    assert confirmadas and all("aprovado_por" in r for r in confirmadas.values())
    assert all(r["aprovado_por"].startswith("comercial") for k, r in confirmadas.items() if k.startswith("cadastro."))
    assert all(r["aprovado_por"] == "Helena" for k, r in confirmadas.items() if not k.startswith("cadastro."))


def test_venda_e_estorno_se_anulam_confirmado(regras):
    """Q-N 3 (Helena 09:44) confirma a D10."""
    r = regras["divergencias.estorno_de_venda_divergente"]
    assert r["status"] == "CONFIRMADO" and "Q-N 3" in r["fonte"]
