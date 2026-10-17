"""Leitores da Orbe e da planilha de taxas (casos conferidos contra as linhas de origem)."""

from datetime import date
from decimal import Decimal

import pytest

from tarvo.formatos import FormatoInvalido, cnpj_valido, decimal_br, normalizar_cnpj, taxa_de_celula
from tarvo.leitores.orbe import ErroLeitura, ler_orbe
from conftest import ORBE


# --- formatos ---------------------------------------------------------------

def test_decimal_br():
    assert decimal_br("5773,57") == Decimal("5773.57")
    assert decimal_br("-2193,16") == Decimal("-2193.16")
    assert decimal_br("-1.019.882,54", milhar=True) == Decimal("-1019882.54")
    with pytest.raises(FormatoInvalido):
        decimal_br("1.234,56")  # milhar onde não se espera: aviso, não chute


@pytest.mark.parametrize(
    "valor, esperado",
    [
        (3229837000103, "03229837000103"),  # planilha R14: número sem zero à esquerda
        (8780784000120, "08780784000120"),  # planilha R25
        ("22.224.579/0001-09", "22224579000109"),
        ("78576234000179", "78576234000179"),
        ("123", None),
        ("EC pendente", None),
        (None, None),
    ],
)
def test_normalizar_cnpj(valor, esperado):
    assert normalizar_cnpj(valor) == esperado


def test_cnpj_valido():
    assert cnpj_valido("03229837000103")
    assert not cnpj_valido("38686002000180")  # PIX sem identificação (Aurora L50): DV inválido
    assert not cnpj_valido("11111111111111")


def test_taxa_de_celula():
    assert taxa_de_celula(0.007900000000000001, 4) == Decimal("0.0079")  # ruído de float (R14 H)
    assert taxa_de_celula("3,09%", 4) == Decimal("0.0309")  # texto (R20)
    assert taxa_de_celula("padrão", 4) == "padrão"  # texto não interpretado
    assert taxa_de_celula(None, 4) is None
    with pytest.raises(FormatoInvalido):
        taxa_de_celula(0.02695, 4)  # mais casas que o permitido: não arredonda calado


# --- Orbe -------------------------------------------------------------------

def test_orbe_le_todas_as_linhas(orbe):
    assert orbe.total_linhas_dados == 1943
    assert len(orbe.transacoes) == 1943
    assert orbe.linhas_invalidas == []
    assert orbe.avisos == []


def test_orbe_campos_tx88428676(orbe):
    t = next(x for x in orbe.transacoes if x.ref_origem == "TX88428676")
    assert t.linha_arquivo == 1056
    assert t.data_movimento == date(2026, 9, 16)
    assert t.cod_estabelecimento == "1074504011"
    assert (t.modalidade, t.qtd_parcelas) == ("CREDITO PARCELADO", 10)
    assert t.valor_bruto == Decimal("10420.13")
    assert t.taxa_aplicada_pct == Decimal("4.09")
    assert t.valor_taxa == Decimal("426.18")


def test_orbe_estorno_de_agosto(orbe):
    t = next(x for x in orbe.transacoes if x.ref_origem == "TX88444848")
    assert t.linha_arquivo == 39
    assert t.valor_bruto == Decimal("-2193.16")
    assert t.id_referencia == "TX87651902"
    assert t.data_venda_original == date(2026, 8, 22)


def test_orbe_antecipacao_sem_modalidade(orbe):
    t = next(x for x in orbe.transacoes if x.ref_origem == "AN88444882")
    assert t.tipo_lancamento == "ANTECIPACAO"
    assert t.modalidade is None and t.qtd_parcelas is None and t.bandeira is None


def test_orbe_linha_estranha_vira_invalida(tmp_path, orbe):
    origem = (tmp_path / "orbe.csv")
    linhas = open(ORBE, encoding="utf-8").read().splitlines()
    linhas[1] = linhas[1].replace("608,88", "608.88")  # ponto no lugar da vírgula
    linhas[2] = linhas[2] + ";extra"  # coluna a mais
    origem.write_text("\n".join(linhas[:4]) + "\n", encoding="utf-8")
    r = ler_orbe(origem)
    assert [li.linha_arquivo for li in r.linhas_invalidas] == [2, 3]
    assert len(r.transacoes) == 1 and r.total_linhas_dados == 3


def test_orbe_cabecalho_diferente_e_erro(tmp_path):
    p = tmp_path / "orbe.csv"
    p.write_text("id;data\n1;2\n", encoding="utf-8")
    with pytest.raises(ErroLeitura):
        ler_orbe(p)


# --- Taxas ------------------------------------------------------------------

def _linha(taxas, nome):
    return next(l for l in taxas.linhas if l.lojista == nome)


def test_taxas_so_lojistas(taxas):
    assert len(taxas.linhas) == 25  # R6–R30
    assert all(not l.lojista.startswith("*") for l in taxas.linhas)  # rodapé R32 não é lojista
    assert any(a.local == "R32" for a in taxas.avisos)


def test_taxas_cnpj_sem_zero_a_esquerda(taxas):
    assert _linha(taxas, "Fluente Idiomas Online Ltda").cnpj == "03229837000103"
    assert _linha(taxas, "Campus Global Ltda").cnpj == "08780784000120"


def test_taxas_percentual_texto_e_numero(taxas):
    oxford = _linha(taxas, "Oxford Prep Cursos Ltda")  # R20 em texto
    assert oxford.taxas["Créd. 2-6x"] == Decimal("0.0309")
    assert oxford.taxas["Crédito à vista"] == Decimal("0.0259")
    assert _linha(taxas, "Fluente Idiomas Online Ltda").taxas["Pix"] == Decimal("0.0079")
    assert _linha(taxas, "Canguru").taxas["Spread remessa"] == "padrão"


def test_taxas_bridge_duas_vigencias_e_comentario(taxas):
    bridge = [l for l in taxas.linhas if l.cnpj == "22224579000109"]
    assert [(l.linha_planilha, l.vigencia_texto) for l in bridge] == [
        (6, "até 14/09/2026"), (7, "a partir de 15/09/2026")
    ]
    casa = _linha(taxas, "Casa do Estudante Viagens Ltda")
    assert "condição especial" in casa.comentario
