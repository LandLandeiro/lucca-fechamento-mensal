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
    assert sum(Decimal(n["valor_brl"]) for n in notas) == Decimal("203740.84")  # 203.735,34 (com o 06, D75) + 5,50 (Casa fora)
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
        "PEN-CONTESTACAO_PONTE-SPREAD_NEGATIVO": "-3565.98",  # D80: o que pedir à Ponte (até o contrato)
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
    for p in pasta.glob("*.csv"):
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
    for p in pasta.glob("*.csv"):
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


def _planilha_com_celula(destino, lojista, coluna, valor):
    """Cópia do data pack com uma célula da aba vigente trocada (o data/ original não muda)."""
    import openpyxl
    from conftest import copiar_dados
    copiar_dados(destino)
    caminho = next(destino.glob("02_tabela_taxas_contratadas*.xlsx"))
    wb = openpyxl.load_workbook(caminho)
    ws = wb["Taxas vigentes"]
    cab = next(r for r in ws.iter_rows() if any(c.value == "Lojista" for c in r))
    col = next(c.column for c in cab if c.value == coluna)
    linha = next(r[0].row for r in ws.iter_rows(min_row=cab[0].row + 1) if r[0].value == lojista)
    ws.cell(linha, col).value = valor
    wb.save(caminho)
    return destino


def test_nota_nao_sai_com_valor_parcial(tmp_path):
    """D57 (avaliação simulada): com 'a confirmar' na taxa de crédito à vista da Rota, as transações dessa
    coluna ficam em pendência e a comissão calculada é parcial; a nota da Rota não é emitida e vira
    NOTA_BLOQUEADA com o motivo. As outras notas não mudam."""
    rota = "95927868000148"
    dados = _planilha_com_celula(tmp_path / "dados", "Rota Global Intercâmbio Ltda", "Crédito à vista", "a confirmar")
    r = executar(dados, tmp_path / "s", RAIZ / "regras.yaml")
    assert r["erros_validacao"] == []
    notas = {n["tomador_cnpj"]: n for n in _csv(tmp_path / "s", "notas_a_emitir.csv")}
    assert rota not in notas and len(notas) == 20  # 19 de checkout + a da Ponte
    pend = {p["id_saida"]: p for p in _csv(tmp_path / "s", "pendencias.csv")}
    b = pend[f"PEN-NOTA_BLOQUEADA-{rota}"]
    com = next(c for c in _csv(tmp_path / "s", "comissoes_por_lojista.csv") if c["id_saida"] == f"COM-{rota}-CHECKOUT")
    assert b["valor_brl"] == com["comissao_brl"] and b["quem_decide"] == "Helena"
    assert "é parcial" in b["motivo"] and "PEN-TAXA_CONTRATADA_INDEFINIDA-" in b["motivo"]
    assert any(p["tipo"] == "TAXA_CONTRATADA_INDEFINIDA" and "a confirmar" in p["motivo"] for p in pend.values())


def test_validador_recusa_nota_de_lojista_bloqueado(saida, tmp_path):
    from tarvo.saida.validador import validar_saida
    pasta, _ = saida
    for p in pasta.glob("*.csv"):
        (tmp_path / p.name).write_bytes(p.read_bytes())

    def bloquear(linhas):  # uma NOTA_BLOQUEADA da Rota, que tem nota emitida
        return linhas + [["PEN-NOTA_BLOQUEADA-95927868000148", "NOTA_BLOQUEADA", "TX88440860", "", "teste", "Helena"]]
    _reescrever(tmp_path / "pendencias.csv", bloquear)
    erros = validar_saida(tmp_path)
    assert any("NF-95927868000148-CHECKOUT" in e and "NOTA_BLOQUEADA" in e for e in erros)


def test_rascunhos_de_contestacao(saida):
    """D68 (Q-T 2, Q-X 1): um rascunho por contraparte e lojista, com a lista anexa; Casa e Bridge
    (condição não informada à Orbe) não ganham rascunho para a Orbe."""
    import re
    pasta = saida[0] / "rascunhos"
    assert sorted(p.name for p in pasta.glob("*.md")) == [
        "orbe_escola_bridge.md", "orbe_rota_global.md", "ponte_duplicata.md", "ponte_mundo_aberto.md", "ponte_spreads_negativos.md"]
    totais = {p.stem: re.search(r"total_brl=(-?\d+\.\d{2})", p.read_text(encoding="utf-8")).group(1) for p in pasta.glob("*.md")}
    assert totais == {"orbe_rota_global": "1545.86", "orbe_escola_bridge": "29.94",  # D74, D76: recuperar = a devolver
                       "ponte_mundo_aberto": "1418.85", "ponte_spreads_negativos": "-3565.98",
                      "ponte_duplicata": "821.88"}
    for nome, total in totais.items():
        assert sum(Decimal(l["valor_brl"]) for l in _csv(pasta, f"{nome}.csv")) == Decimal(total)
    assert len(_csv(pasta, "orbe_rota_global.csv")) == 87  # D77: os 4 pares venda/estorno entram, com sinal
    assert "RASCUNHO para a Helena revisar" in (pasta / "orbe_rota_global.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("estrago, trecho", [("total", "≠ Σ"), ("casa", "condicao_nao_informada")])
def test_validador_recusa_rascunho_errado(saida, tmp_path, estrago, trecho):
    import shutil
    from tarvo.saida.validador import validar_saida
    shutil.copytree(saida[0], tmp_path / "s")
    rasc = tmp_path / "s" / "rascunhos"
    if estrago == "total":
        md = rasc / "ponte_mundo_aberto.md"
        md.write_text(md.read_text(encoding="utf-8").replace("total_brl=1418.85", "total_brl=1418.88"), encoding="utf-8")
    else:  # uma transação da Casa (devolução, nunca cobrança da Orbe) no rascunho para a Orbe
        with open(rasc / "orbe_rota_global.csv", "a", encoding="utf-8", newline="") as f:
            f.write("AN88445802;2026-09-16;ANTECIPACAO;57456.27;2.1;0;0.00\n")
    assert any(trecho in e for e in validar_saida(tmp_path / "s"))


def test_rascunhos_deterministicos(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    executar(DADOS, a, RAIZ / "regras.yaml")
    executar(DADOS, b, RAIZ / "regras.yaml")
    for p in (a / "rascunhos").iterdir():
        assert p.read_bytes() == (b / "rascunhos" / p.name).read_bytes(), p.name


def test_spread_negativo_com_os_dois_valores_rotulados(saida):
    """D80 (Q-AA 3): 'o spread negativo do relatório, que é o que aconteceu, e a diferença até o spread do contrato,
    que é o que eu vou pedir à Ponte'."""
    pasta, _ = saida
    (p,) = [p for p in _csv(pasta, "pendencias.csv") if p["id_saida"] == "PEN-CONTESTACAO_PONTE-SPREAD_NEGATIVO"]
    assert p["valor_brl"] == "-3565.98"
    assert "Spread negativo do relatório (o que aconteceu): -1834.05" in p["motivo"]
    assert "o que pedir à Ponte, valor desta pendência): -3565.98" in p["motivo"]
    md = (pasta / "rascunhos" / "ponte_spreads_negativos.md").read_text(encoding="utf-8")
    assert "(o que aconteceu):** -R$ 1.834,05" in md and "(o que pedimos à Ponte):** -R$ 3.565,98" in md
    lista = _csv(pasta / "rascunhos", "ponte_spreads_negativos.csv")
    assert sum(Decimal(l["spread_brl"]) for l in lista) == Decimal("-1834.05")
    assert sum(Decimal(l["valor_brl"]) for l in lista) == Decimal("-3565.98")
