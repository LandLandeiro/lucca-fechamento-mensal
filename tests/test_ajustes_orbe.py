"""D75: o arquivo 06 de ajustes tardios da Orbe faz parte do relatório do mês (opcional)."""

import csv
from decimal import Decimal

from tarvo.__main__ import executar
from conftest import DADOS, RAIZ, copiar_dados

AJ = "06_orbe_ajustes_tardios_set2026.csv"


def _csv(pasta, nome):
    with open(pasta / nome, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def test_06_entra_no_fechamento(tmp_path):
    """As 14 linhas (10 estornos, 3 reversões, 1 venda) entram na comissão: −3.304,39; notas 243.284,29."""
    r = executar(DADOS, tmp_path / "s", RAIZ / "regras.yaml")
    assert r["erros_validacao"] == [] and r["transacoes_lidas"] == 1943 + 14
    assert AJ in r["arquivos"]
    rastro = [l for l in _csv(tmp_path / "s", "rastro.csv") if l["arquivo_origem"] == AJ]
    assert len({l["ref_origem"] for l in rastro if l["id_saida"].startswith("COM-")}) == 14
    com = {c["id_saida"]: Decimal(c["comissao_brl"]) for c in _csv(tmp_path / "s", "comissoes_por_lojista.csv")}
    assert sum(v for k, v in com.items() if k.endswith("CHECKOUT")) == Decimal("203735.34")
    assert com["COM-23109187000161-CHECKOUT"] == Decimal("13845.71")  # Oxford: 2 estornos + 2 reversões
    assert sum(Decimal(n["valor_brl"]) for n in _csv(tmp_path / "s", "notas_a_emitir.csv")) == Decimal("243284.29")
    est = next(l for l in rastro if l["ref_origem"] == "TX88447087")
    assert "estorno de TX88422829" in est["nota"]  # pela taxa da venda original (Q-B)


def test_sem_o_06_segue_sem_aviso(tmp_path):
    dados = tmp_path / "d"
    copiar_dados(dados)
    (dados / AJ).unlink()
    r = executar(dados, tmp_path / "s", RAIZ / "regras.yaml")
    assert r["erros_validacao"] == [] and r["transacoes_lidas"] == 1943
    assert not any("06_orbe" in a.arquivo or "06_orbe" in a.mensagem for a in r["avisos"])


def test_id_repetido_entre_01_e_06_vira_pendencia(tmp_path):
    """Um ajuste com id que já está no 01 (correção?): nenhuma das duas linhas conta; pendência para a Helena."""
    linha_01 = b"TX88410316;01/09/2026;1000960410;OXFORD PREP CURSOS;VENDA;CREDITO A VISTA;1;VISA;1645,47;2,59;42,61;1602,86;;"
    dados = copiar_dados(tmp_path / "d", {AJ: [(b"TX88447225;", b"TX88410316;")]})
    r = executar(dados, tmp_path / "s", RAIZ / "regras.yaml")
    assert r["erros_validacao"] == []
    (p,) = [p for p in _csv(tmp_path / "s", "pendencias.csv") if p["tipo"] == "ID_REPETIDO_ORBE"]
    assert p["id_saida"] == "PEN-ID_REPETIDO_ORBE-TX88410316" and p["quem_decide"] == "Helena"
    destinos = {(l["id_saida"], l["arquivo_origem"]) for l in _csv(tmp_path / "s", "rastro.csv") if l["ref_origem"] == "TX88410316"
                and not l["id_saida"].startswith(("NF-", "DIV-"))}
    assert destinos == {(p["id_saida"], "01_orbe_relatorio_comissoes_set2026.csv"), (p["id_saida"], AJ)}
    assert linha_01  # a linha do 01 que o ajuste repete


def test_arquivo_que_ninguem_le_vira_aviso(tmp_path):
    dados = copiar_dados(tmp_path / "d")
    (dados / "07_novo_arquivo_da_orbe.csv").write_text("a;b\n1;2\n", encoding="utf-8")
    r = executar(dados, tmp_path / "s", RAIZ / "regras.yaml")
    assert any(a.arquivo == "07_novo_arquivo_da_orbe.csv" and "nenhum leitor reconhece" in a.mensagem for a in r["avisos"])
    assert not any(a.arquivo == "00_LEIA-ME.md" for a in r["avisos"])
