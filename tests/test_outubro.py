"""Ponta a ponta em outubro: o mesmo código e o mesmo regras.yaml fecham um mês novo (DADO SINTÉTICO DE TESTE).

A fixture é gerada a partir de setembro por `tests/fixtures/gerar_outubro.py` (datas deslocadas um mês +
5 novidades). Sem rede e sem chave: a IA é um cliente mockado, e só o PIX de nome novo (Nórdica) vai para ela.
"""

import csv
import importlib.util
from decimal import Decimal

import pytest

from tarvo.__main__ import executar
from tarvo.classificacao.por_ia import SugestaoIA
from conftest import DADOS, RAIZ

CASA, BRIDGE, EDU, NORDICA = "00520815000100", "22224579000109", "16181276000153", "14760206000124"


class IAFalsa:
    """Responde o que uma IA responderia para o nome novo: aporte da Nórdica. Nunca toca a rede."""

    def __init__(self):
        self.chamadas = []

    def sugerir(self, sistema, entrada):
        self.chamadas.append(entrada)
        return SugestaoIA(conta_codigo="2.1.02.001", lojista_cnpj=NORDICA, justificativa="aporte da Nórdica (sigla NEI)",
                          confianca=0.9), {"input_tokens": 1000, "output_tokens": 100}


def _gerador():
    spec = importlib.util.spec_from_file_location("gerar_outubro", RAIZ / "tests" / "fixtures" / "gerar_outubro.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def outubro(tmp_path_factory):
    dados = _gerador().gerar(DADOS, tmp_path_factory.mktemp("dados_outubro"))
    saida = tmp_path_factory.mktemp("saida_outubro")
    ia = IAFalsa()
    resumo = executar(dados, saida, RAIZ / "regras.yaml", cliente_ia=ia, cache_ia=tmp_path_factory.mktemp("cache_outubro"))
    resumo["ia_falsa"] = ia

    def ler(nome):
        with open(saida / nome, encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f, delimiter=";"))
    return resumo, ler


def test_roda_e_valida(outubro):
    resumo, _ = outubro
    assert resumo["erros_validacao"] == []
    assert resumo["transacoes_lidas"] == 1943 + 3  # setembro deslocado + 2 vendas do EC novo + 1 estorno


def test_competencia_10_2026_nas_notas(outubro):
    _, ler = outubro
    notas = ler("notas_a_emitir.csv")
    assert {n["competencia"] for n in notas} == {"10/2026"}
    assert all(n["discriminacao"].endswith("competência 10/2026") for n in notas)


def test_casa_do_estudante_segue_com_taxa_zero(outubro):
    """Condição especial de set a dez (Helena 20:49): em outubro a taxa contratada continua 0."""
    _, ler = outubro
    casa = [r for r in ler("rastro.csv") if r["id_saida"] == f"COM-{CASA}-CHECKOUT"]
    assert casa and {r["taxa_contratada_pct"] for r in casa} == {"0"}


def test_ec_novo_vira_pendencia_sem_quebrar(outubro):
    _, ler = outubro
    (p,) = [p for p in ler("pendencias.csv") if p["id_saida"] == "PEN-EC_SEM_CADASTRO-EC1099000001"]
    assert p["valor_brl"] == "71.87" and p["quem_decide"]  # 64,75 + 7,12 cobrados pela Orbe (informativo)
    assert not any("1099000001" in c["id_saida"] for c in ler("comissoes_por_lojista.csv"))


def test_estorno_da_bridge_usa_a_taxa_antiga(outubro):
    """Venda de 05/09 (antes da taxa nova de 15/09) estornada em 08/10: taxa da data da venda original (Q-B)."""
    _, ler = outubro
    (r,) = [r for r in ler("rastro.csv") if r["id_saida"] == f"COM-{BRIDGE}-CHECKOUT" and r["ref_origem"] == "TX89500001"]
    assert r["taxa_contratada_pct"] == "2.59" and r["valor"] == "-37.86"  # pela taxa nova (2,19%) seria −32,01
    assert "venda de 2026-09-05" in r["nota"]
    assert not any(d["ref_origem"] == "TX89500001" for d in ler("divergencias_taxa.csv"))


def test_pix_da_eduabroad_por_regra(outubro):
    _, ler = outubro
    edu = [l for l in ler("lancamentos_classificados.csv") if "EDU ABROAD" in l["descricao"]]
    assert len(edu) == 7 and all(l["metodo"] == "REGRA" for l in edu)
    assert {l["regra_aplicada"] for l in edu if l["banco"] == "MERIDIANO"} == {"meridiano.aporte_lojista"}


def test_pix_de_nome_novo_vai_para_a_ia_e_o_codigo_prova(outubro):
    """A IA só recebe o que nenhuma regra reconhece: o aporte com nome novo. A soma dos aportes da Nórdica
    (4 por regra + 1 pela IA) bate com as operações dela na Ponte, então a sugestão é aceita (D42)."""
    resumo, ler = outubro
    assert [c["descricao"] for c in resumo["ia_falsa"].chamadas] == ["PIX RECEB NEI EDUCACAO INTERNACIONAL"]
    (l,) = [l for l in ler("lancamentos_classificados.csv") if l["descricao"] == "PIX RECEB NEI EDUCACAO INTERNACIONAL"]
    assert (l["metodo"], l["conta_codigo"], l["confianca"]) == ("IA", "2.1.02.001", "0.90")
    (d,) = resumo["extratos"]["ia"].decisoes
    assert d.aceita and any(item == "c" and ok for item, ok, _ in d.checagens)
    (s,) = ler("sugestoes_regra.csv")
    assert (s["tipo"], s["padrao_ou_nome"], s["lojista_cnpj"], s["status"]) == (
        "ALIAS_LOJISTA", "NEI EDUCACAO INTERNACIONAL", NORDICA, "PROPOSTA")


def test_ted_de_300_mil_por_regra(outubro):
    _, ler = outubro
    (l,) = [l for l in ler("lancamentos_classificados.csv") if l["ref_origem"] == "MRD2026100001"]
    assert (l["data"], l["valor"], l["metodo"], l["regra_aplicada"], l["conta_codigo"]) == (
        "2026-10-01", "300000.00", "REGRA", "meridiano.mesma_titularidade", "1.1.09.001")


def test_rastro_fecha(outubro):
    _, ler = outubro
    soma = {}
    for r in ler("rastro.csv"):
        soma[r["id_saida"]] = soma.get(r["id_saida"], Decimal(0)) + Decimal(r["valor"])
    for c in ler("comissoes_por_lojista.csv"):
        assert soma[c["id_saida"]] == Decimal(c["comissao_brl"])


def test_nenhuma_pendencia_de_outubro_cita_setembro(outubro):
    """D48: textos derivados da data; a transferência em trânsito de 30/10 manda conferir em novembro."""
    _, ler = outubro
    pend = ler("pendencias.csv")
    assert not [p["id_saida"] for p in pend if "setembro" in (p["motivo"] + p["quem_decide"]).lower()]
    (t,) = [p for p in pend if p["tipo"] == "TRANSFERENCIA_EM_TRANSITO"]
    assert "conferir no extrato de novembro" in t["motivo"] and t["quem_decide"] == "analista (conferir em novembro)"
    (x,) = [p for p in pend if p["tipo"] == "EXCESSO_REMESSA"]
    assert "A nota de outubro sai pelo realizado" in x["motivo"]


def test_sem_a_flag_a_ted_de_300_mil_vira_pendencia_nova(outubro, tmp_path):
    """Sem --pendencias-anteriores o comportamento não muda: entrada sem saída no mês é pendência."""
    _, ler = outubro
    assert any(p["id_saida"] == "PEN-TRANSFERENCIA_SEM_ORIGEM-MERIDIANO-MRD2026100001" for p in ler("pendencias.csv"))


def test_com_a_flag_a_pendencia_de_setembro_sai_resolvida(tmp_path_factory):
    """D50: com o pendencias.csv de setembro, a TED de 01/10 casa com a transferência em trânsito de 30/09."""
    dados = _gerador().gerar(DADOS, tmp_path_factory.mktemp("dados_flag"))
    saida = tmp_path_factory.mktemp("saida_flag")
    r = executar(dados, saida, RAIZ / "regras.yaml", pendencias_anteriores=RAIZ / "saida" / "pendencias.csv")
    assert r["erros_validacao"] == []
    with open(saida / "pendencias.csv", encoding="utf-8", newline="") as f:
        pend = list(csv.DictReader(f, delimiter=";"))
    assert not any(p["tipo"] == "TRANSFERENCIA_SEM_ORIGEM" for p in pend)
    with open(saida / "pendencias_resolvidas.csv", encoding="utf-8", newline="") as f:
        (res,) = list(csv.DictReader(f, delimiter=";"))
    assert (res["id_pendencia_anterior"], res["valor_brl"], res["resolvida_por"]) == (
        "PEN-TRANSFERENCIA_EM_TRANSITO-AURORA-L92", "-300000.00", "LAN-MERIDIANO-MRD2026100001")
    assert res["motivo"].startswith("pendência de setembro resolvida")

