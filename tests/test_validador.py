"""Validador: a saída real passa; total que não fecha, linha perdida e formato errado falham."""

import csv
from decimal import Decimal
from pathlib import Path

import pytest

from tarvo.__main__ import executar
from conftest import DADOS, RAIZ


@pytest.fixture(scope="module")
def saida(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("saida")
    resumo = executar(DADOS, pasta, RAIZ / "regras.yaml")
    return pasta, resumo


def _reescrever(caminho: Path, transformar):
    with open(caminho, encoding="utf-8", newline="") as f:
        linhas = list(csv.reader(f, delimiter=";"))
    linhas = transformar(linhas)
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        csv.writer(f, delimiter=";", lineterminator="\n").writerows(linhas)


def _copia(saida, tmp_path):
    pasta, _ = saida
    for p in pasta.glob("*.csv"):
        (tmp_path / p.name).write_bytes(p.read_bytes())
    return tmp_path


def test_saida_real_valida(saida):
    _, resumo = saida
    assert resumo["erros_validacao"] == []


def test_formato_dos_csvs(saida):
    pasta, _ = saida
    texto = (pasta / "comissoes_por_lojista.csv").read_text(encoding="utf-8")
    cab = texto.splitlines()[0]
    assert cab.startswith("id_saida;cnpj;lojista;linha_negocio;comissao_brl")
    assert "COM-95927868000148-CHECKOUT;95927868000148;" in texto
    assert ";15621.27;" in texto
    rastro = (pasta / "rastro.csv").read_text(encoding="utf-8")
    assert rastro.splitlines()[0].startswith("id_saida;arquivo_origem;ref_origem;valor")
    assert "COM-95927868000148-CHECKOUT;01_orbe_relatorio_comissoes_set2026.csv;TX88428676;374.08;1056;" in rastro


def test_total_que_nao_fecha_e_erro(saida, tmp_path):
    from tarvo.saida.validador import validar_saida

    pasta = _copia(saida, tmp_path)

    def adulterar(linhas):
        for l in linhas[1:]:
            if l[0] == "COM-95927868000148-CHECKOUT":
                l[4] = "15620.56"
        return linhas

    _reescrever(pasta / "comissoes_por_lojista.csv", adulterar)
    erros = validar_saida(pasta)
    assert any("COM-95927868000148-CHECKOUT" in e and "soma do rastro" in e for e in erros)


def test_linha_da_orbe_sumida_e_erro(saida, tmp_path, orbe):
    from tarvo.saida.validador import validar_saida

    pasta = _copia(saida, tmp_path)
    _reescrever(pasta / "rastro.csv", lambda ls: [l for l in ls if l[2] != "TX88444848"])
    erros = validar_saida(pasta, {orbe.arquivo: {(t.ref_origem, t.linha_arquivo) for t in orbe.transacoes}})
    assert any("sem rastro nem pendência" in e for e in erros)


def _conservacao(orbe):
    return {
        "fonte_orbe": {orbe.arquivo: {t.ref_origem: (t.valor_taxa, t.valor_bruto, t.taxa_aplicada_pct / 100)
                                      for t in orbe.transacoes}},
        "modo_checkout": "ROUND_HALF_UP",
    }


def test_conservacao_quebra_se_divergencia_sumir(saida, tmp_path, orbe):
    from tarvo.saida.validador import validar_saida

    pasta = _copia(saida, tmp_path)
    alvo = "DIV-TX88423647"
    _reescrever(pasta / "divergencias_taxa.csv", lambda ls: [l for l in ls if l[0] != alvo])
    _reescrever(pasta / "rastro.csv", lambda ls: [l for l in ls if l[0] != alvo])
    erros = validar_saida(pasta, **_conservacao(orbe))
    assert any("listadas" in e and "recalculadas da fonte" in e for e in erros)


def test_divergencia_de_linha_pendente_e_erro(saida, tmp_path, orbe):
    from tarvo.saida.validador import validar_saida

    pasta = _copia(saida, tmp_path)

    def apontar_atlas(linhas):
        for l in linhas[1:]:
            if l[0] == "DIV-TX88423647":
                l[2] = "AN88445637"  # antecipação da Atlas (em pendência)
        return linhas

    _reescrever(pasta / "rastro.csv", apontar_atlas)
    erros = validar_saida(pasta, **_conservacao(orbe))
    assert any("não está em nenhuma comissão" in e for e in erros)


def test_residuo_de_mais_de_um_centavo_e_erro(saida, tmp_path, orbe):
    from tarvo.saida.validador import validar_saida

    pasta = _copia(saida, tmp_path)

    def adulterar(linhas):
        for l in linhas[1:]:
            if l[0] == "COM-23109187000161-CHECKOUT" and l[2] == "TX88444848":
                l[3] = "-83.15"  # comissão contratada é −83,12; −0,03 de resíduo não é truncamento
        return linhas

    _reescrever(pasta / "rastro.csv", adulterar)
    erros = validar_saida(pasta, **_conservacao(orbe))
    assert any("TX88444848: resíduo" in e for e in erros)


def _spread_ponte():
    from tarvo.leitores.ponte_email import ler_email, ler_operacoes

    eml = DADOS / "03_email_ponte_cambio_relatorio_set2026.eml"
    mail = ler_email(eml)
    p = ler_operacoes(mail.anexo_xlsx, eml.name, mail.nome_anexo, ["Total de operações:", "Spread total R$:"])
    return {p.arquivo: {(o.ref_origem, o.linha_planilha): o.spread_brl for o in p.operacoes}}, p


def test_remessa_exclusao_sumida_e_erro(saida, tmp_path):
    from tarvo.saida.validador import validar_saida

    pasta = _copia(saida, tmp_path)
    spread, p = _spread_ponte()
    _reescrever(pasta / "rastro.csv", lambda ls: [l for l in ls if l[0] != "EXC-REMESSA-DUPLICATA"])
    erros = validar_saida(pasta, refs_esperadas={p.arquivo: {(o.ref_origem, o.linha_planilha) for o in p.operacoes}},
                          spread_ponte=spread, spread_declarado=Decimal("78073.59"))
    assert any("conservação REMESSA" in e for e in erros)
    assert any("sem rastro nem pendência" in e for e in erros)


def test_remessa_comissao_que_nao_e_metade_e_erro(saida, tmp_path):
    from tarvo.saida.validador import validar_saida

    pasta = _copia(saida, tmp_path)
    spread, _ = _spread_ponte()

    def adulterar(linhas):
        for l in linhas[1:]:
            if l[0] == "COM-17217888000111-REMESSA" and l[2] == "PC-0926-0011":
                l[3] = "80.00"  # metade de 147,53 é 73,76/73,77
        return linhas

    _reescrever(pasta / "rastro.csv", adulterar)
    erros = validar_saida(pasta, spread_ponte=spread)
    assert any("não é metade do spread" in e for e in erros)


def test_cnpj_e_decimal_fora_do_formato_sao_erro(saida, tmp_path):
    from tarvo.saida.validador import validar_saida

    pasta = _copia(saida, tmp_path)

    def adulterar(linhas):
        linhas[1][1] = "3229837000103"  # CNPJ com 13 dígitos
        linhas[1][4] = linhas[1][4].replace(".", ",")  # vírgula decimal
        return linhas

    _reescrever(pasta / "comissoes_por_lojista.csv", adulterar)
    erros = validar_saida(pasta)
    assert any("CNPJ" in e for e in erros) and any("fora do formato 0.00" in e for e in erros)


def _copiar(pasta, destino):
    for p in pasta.glob("*.csv"):
        (destino / p.name).write_bytes(p.read_bytes())


def test_nenhum_ponto_e_virgula_dentro_de_campo(saida):
    """D45: nenhum ';' dentro de campo em nenhum CSV de saída (um split(';') ingênuo não desalinha)."""
    pasta = saida[0] if isinstance(saida, tuple) else saida
    for p in pasta.glob("*.csv"):
        with open(p, encoding="utf-8", newline="") as f:
            for linha in csv.reader(f, delimiter=";"):
                assert not any(";" in v for v in linha), p.name


def test_validador_recusa_ponto_e_virgula_em_campo(saida, tmp_path):
    pasta = saida[0] if isinstance(saida, tuple) else saida
    _copiar(pasta, tmp_path)
    caminho = tmp_path / "pendencias.csv"
    with open(caminho, encoding="utf-8", newline="") as f:
        linhas = list(csv.reader(f, delimiter=";"))
    linhas[1][4] = "motivo; com ponto e vírgula"
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        csv.writer(f, delimiter=";", lineterminator="\n").writerows(linhas)
    from tarvo.saida.validador import validar_saida
    assert any("pendencias.csv" in e and "';' dentro do campo" in e for e in validar_saida(tmp_path))


def test_validador_recusa_rastro_sem_linha_de_origem(saida, tmp_path):
    """D45: toda linha do rastro existe na fonte, inclusive em NF-, DIV- da remessa e pendências derivadas."""
    from tarvo.__main__ import executar
    from conftest import DADOS, RAIZ as R
    pasta = tmp_path / "s"
    r = executar(DADOS, pasta, R / "regras.yaml")
    assert r["erros_validacao"] == []
    caminho = pasta / "rastro.csv"
    with open(caminho, encoding="utf-8", newline="") as f:
        linhas = list(csv.reader(f, delimiter=";"))
    i = next(i for i, l in enumerate(linhas) if l[0].startswith("PEN-CONTESTACAO_PONTE-"))
    linhas[i][2] = "PC-9999-9999"
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        csv.writer(f, delimiter=";", lineterminator="\n").writerows(linhas)
    from tarvo.saida.validador import validar_saida as v
    fontes = r["fontes_rastro"]
    erros = v(pasta, fontes_rastro=fontes)
    assert any("PC-9999-9999" in e and "não existe na fonte" in e for e in erros)



def test_ref_origem_das_pendencias_so_ids_puros(saida):
    """D55: ids puros (id_transacao, Nº Operação, L<n>, FITID), lista completa separada por '|', sem prosa."""
    pasta, _ = saida
    with open(pasta / "pendencias.csv", encoding="utf-8", newline="") as f:
        pend = {p["id_saida"]: p for p in csv.DictReader(f, delimiter=";")}
    for p in pend.values():
        assert " " not in p["ref_origem"] and "," not in p["ref_origem"] and "mais" not in p["ref_origem"], p["id_saida"]
    assert len(pend["PEN-EXCESSO_REMESSA-17217888000111"]["ref_origem"].split("|")) == 23
    assert pend["PEN-CONTESTACAO_PONTE-DUPLICATA"]["ref_origem"] == "PC-0926-0162"
    assert len(pend["PEN-SEM_CONTRATO_VIGENTE-EC1076801732"]["ref_origem"].split("|")) == 57
    assert len(pend["PEN-CONFERENCIA_REPASSE-REMESSA"]["ref_origem"].split("|")) == 228
    assert "NF-75374179000146-REMESSA" in pend["PEN-CONFERENCIA_REPASSE-REMESSA"]["motivo"]  # a explicação vai no motivo


@pytest.mark.parametrize("ref, trecho", [
    ("PC-0926-0011, PC-0926-0016 e mais 21", "não é id puro"),
    ("PC-0926-0011|PC-0926-0016", "ref_origem ≠ ids do rastro"),  # lista incompleta
])
def test_validador_recusa_ref_origem_de_pendencia_em_prosa_ou_incompleta(saida, tmp_path, ref, trecho):
    from tarvo.saida.validador import validar_saida
    pasta = _copia(saida, tmp_path)

    def trocar(linhas):
        for l in linhas[1:]:
            if l[0] == "PEN-EXCESSO_REMESSA-17217888000111":
                l[2] = ref
        return linhas
    _reescrever(pasta / "pendencias.csv", trocar)
    assert any("PEN-EXCESSO_REMESSA-17217888000111" in e and trecho in e for e in validar_saida(pasta))


def test_validador_recusa_valor_a_devolver_que_nao_fecha(saida, tmp_path):
    """D71: valor_a_devolver_brl tem que ser valor_taxa_orbe − comissao_contratada da própria linha."""
    from tarvo.saida.validador import validar_saida
    pasta = _copia(saida, tmp_path)

    def estragar(linhas):
        i = linhas[0].index("valor_a_devolver_brl")
        linhas[1][i] = "1.00"
        return linhas
    _reescrever(pasta / "divergencias_taxa.csv", estragar)
    assert any("valor_a_devolver_brl" in e for e in validar_saida(pasta))
