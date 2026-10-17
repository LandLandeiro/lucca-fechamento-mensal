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


def test_sem_o_06_segue_com_aviso_informativo(tmp_path):
    """D89 (Turma 12:31): 'Prefiro que a solução avise a que quebre sem ninguém perceber.' Sem o 06, o fechamento
    segue com o 01 e avisa; não vira erro nem pendência."""
    dados = tmp_path / "d"
    copiar_dados(dados)
    (dados / AJ).unlink()
    r = executar(dados, tmp_path / "s", RAIZ / "regras.yaml")
    assert r["erros_validacao"] == [] and r["transacoes_lidas"] == 1943
    (aviso,) = [a for a in r["avisos"] if "06_orbe" in a.arquivo]
    assert aviso.mensagem.startswith("sem arquivo de ajustes tardios da Orbe neste mês")


def test_com_o_06_nao_avisa_falta(tmp_path):
    r = executar(DADOS, tmp_path / "s", RAIZ / "regras.yaml")
    assert not any("sem arquivo de ajustes tardios" in a.mensagem for a in r["avisos"])


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


def _ajuste_de_agosto(tmp_path):
    """Cópia de setembro em que a linha TX88446992 do 06 tem movimento em 29/08 (ajuste de agosto chegando agora)."""
    dados = tmp_path / "d"
    copiar_dados(dados, {AJ: [(b"TX88446992;30/09/2026;", b"TX88446992;29/08/2026;")]})
    return dados


def test_ajuste_de_mes_ja_aprovado_entra_no_mes_seguinte_com_a_opcao(tmp_path):
    """D91 (Q-AJ 1, Helena 13:34): 'Se chega antes de eu aprovar o fechamento, entra no mês do movimento, como agora.
    Se chegar depois da aprovação, entra no mês seguinte.' Com --fechamento-anterior-aprovado, o ajuste de agosto
    entra em setembro; sem a opção, fica fora da comissão como linha de outro mês (pendência)."""
    dados = _ajuste_de_agosto(tmp_path)
    sem = executar(dados, tmp_path / "sem", RAIZ / "regras.yaml")
    com = executar(dados, tmp_path / "com", RAIZ / "regras.yaml", fechamento_anterior_aprovado=True)
    assert sem["erros_validacao"] == [] and com["erros_validacao"] == []
    pend_sem = {p["id_saida"] for p in _csv(tmp_path / "sem", "pendencias.csv")}
    pend_com = {p["id_saida"] for p in _csv(tmp_path / "com", "pendencias.csv")}
    assert "PEN-ORBE_FORA_COMPETENCIA-TX88446992" in pend_sem and "PEN-ORBE_FORA_COMPETENCIA-TX88446992" not in pend_com
    rastro = [l for l in _csv(tmp_path / "com", "rastro.csv") if l["ref_origem"] == "TX88446992"]
    assert {l["id_saida"] for l in rastro} >= {"COM-68567965000102-CHECKOUT"}
    assert any("entram em 09/2026 (Q-AJ 1): TX88446992" in a.mensagem for a in com["avisos"])
    # setembro do jeito que chegou: a opção não muda nada (o 06 é todo de setembro)
    a = executar(DADOS, tmp_path / "a", RAIZ / "regras.yaml")
    b = executar(DADOS, tmp_path / "b", RAIZ / "regras.yaml", fechamento_anterior_aprovado=True)
    assert all((tmp_path / "a" / n).read_bytes() == (tmp_path / "b" / n).read_bytes()
               for n in ("comissoes_por_lojista.csv", "notas_a_emitir.csv", "pendencias.csv", "rastro.csv"))
