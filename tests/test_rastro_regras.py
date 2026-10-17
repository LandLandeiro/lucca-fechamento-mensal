"""D96 (Q-AM, Organização 14:11): 'em cada linha, a regra aplicada (taxa contratada usada, isenção, estorno pela
venda original)'. `saida/rastro_regras.csv` liga cada linha do rastro às regras do regras.yaml, sem mudar o rastro."""

import csv

import pytest

from tarvo.__main__ import executar
from tarvo.regras import carregar_regras
from tarvo.saida.rastro_regras import SEM_REGRA
from conftest import DADOS, RAIZ


@pytest.fixture(scope="module")
def saida(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("rastro_regras")
    executar(DADOS, pasta, RAIZ / "regras.yaml")
    return pasta


def _csv(pasta, nome):
    with open(pasta / nome, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def test_toda_linha_do_rastro_tem_regra_existente_com_status(saida):
    regras = carregar_regras(RAIZ / "regras.yaml")
    rr = _csv(saida, "rastro_regras.csv")
    assert {(l["id_saida"], l["ref_origem"]) for l in _csv(saida, "rastro.csv")} == {(l["id_saida"], l["ref_origem"]) for l in rr}
    assert not [l for l in rr if l["regra"] == SEM_REGRA]  # setembro: toda linha tem regra no regras.yaml
    for l in rr:
        assert l["status"] == regras[l["regra"]]["status"], l
        assert l["fonte"] and ";" not in l["fonte"]


def test_regra_aplicada_nos_casos_que_a_organizacao_citou(saida):
    por = {}
    for l in _csv(saida, "rastro_regras.csv"):
        por.setdefault((l["id_saida"], l["ref_origem"]), set()).add(l["regra"])
    # taxa contratada usada (venda), isenção (Casa), estorno pela venda original (Oxford, agosto)
    assert por[("COM-23109187000161-CHECKOUT", "TX88444848")] == {"checkout.estorno"}
    assert por[("COM-00520815000100-CHECKOUT", "AN88445172")] >= {"cadastro.condicoes_especiais", "checkout.data_base_antecipacao"}
    assert "cadastro.condicoes_especiais" not in por[("COM-00520815000100-CHECKOUT", "TX88445133")]  # venda de agosto: sem isenção
    assert por[("NF-75374179000146-REMESSA", "PC-0926-0002")] >= {"ponte.participacao_tarvo", "ponte.tomador_nf_remessa",
                                                                  "remessa.liquidacao_no_mes_seguinte"}
    assert por[("EXC-REMESSA-DUPLICATA", "PC-0926-0162")] == {"remessa.operacao_duplicada"}
    assert por[("DIV-PC-0926-0011", "PC-0926-0011")] >= {"remessa.divergencia_spread"}
    assert por[("LAN-AURORA-L9", "L9")] == {"classificacao_extratos.aurora.orbe_recebivel"}
    assert por[("PEN-DEVOLUCAO_CONCESSAO_COMERCIAL-00520815000100", "AN88445172")] >= {"cadastro.condicoes_especiais"}


def test_rastro_csv_nao_muda_de_formato(saida):
    with open(saida / "rastro.csv", encoding="utf-8") as f:
        assert f.readline().strip() == ("id_saida;arquivo_origem;ref_origem;valor;linha_arquivo;tipo_lancamento;"
                                        "valor_bruto;taxa_contratada_pct;nota;spread_brl")
