"""Casos-ouro: cada exemplo concreto da Helena vira teste com o valor que ela afirmou, citando a fala.

Os casos que já tinham teste ganharam a marca `caso_ouro` no próprio arquivo (não foram duplicados); a tabela
CASOS abaixo é o registro de todos, e `test_registro_de_casos_ouro_completo` garante que nenhum some sem querer.
Rodar só eles: `pytest -m caso_ouro`. Falas literais em docs/FINANCEIRO_SLACK.md.
"""
import importlib
from decimal import Decimal
from pathlib import Path

import pytest

from tarvo.__main__ import executar
from tarvo.formatos import centavos, modo_arredondamento
from tarvo.regras import carregar_regras, valor_da_regra
from conftest import DADOS, RAIZ

# (caso, fala da Helena, onde está o teste)
CASOS = [
    ("131,005 → 131,01", "Q-H a 21:13: 'Meio centavo vai para cima'",
     "test_casos_ouro::test_meio_centavo_vai_para_cima"),
    ("131,005 → 131,01 (PC-0926-0002, 50% × 262,01)", "Q-H a/d 21:13",
     "test_remessa::test_pc_0926_0002_liquidada_em_outubro_entra"),
    ("−0,005 → −0,01", "Q-H a 21:13: '-0,005 vira -0,01'",
     "test_casos_ouro::test_meio_centavo_vai_para_cima"),
    ("TX88444848: estorno de agosto entra em setembro pela taxa de 22/08 (3,79% → −83,12)",
     "Q-B 20:06: 'pela taxa contratada que valia em 22/08'",
     "test_comissao_checkout::test_oxford_estorno_de_venda_de_agosto"),
    ("TX88445133: Casa, estorno de venda de 21/08 pela taxa de agosto (1,49% → −5,50)",
     "Q-N 4 09:44: 'Em 21/08 a isenção ainda não valia'",
     "test_comissao_checkout::test_casa_do_estudante_total_e_o_estorno_de_agosto"),
    ("PC-0926-0011: divergência de R$ 29,56 (valor cheio)", "Q-G 20:58: 'É o valor cheio'",
     "test_remessa::test_pc_0926_0011_mundo_aberto"),
    ("PC-0926-0162: duplicata conta uma vez", "Q-L 22:34: 'A duplicada vocês contam uma vez'",
     "test_remessa::test_pc_0926_0162_conta_uma_vez"),
    ("PC-0926-0210: os dois valores (−687,52 do relatório; −1.351,87 até o contrato)",
     "Q-AA 3 11:37: 'Coloquem os dois na pendência, deixando claro qual é qual'",
     "test_remessa::test_pc_0926_0210_spread_negativo_fora_da_comissao"),
    ("PC-0926-0210 e os outros 3 negativos: pendência com os dois valores rotulados", "Q-AA 3 11:37",
     "test_notas::test_spread_negativo_com_os_dois_valores_rotulados"),
    ("Bridge: contrato_orbe", "Q-AA 1 11:37: 'O que decide é o contrato, não o aviso'",
     "test_divergencias::test_natureza_de_cada_divergencia"),
    ("Par venda e estorno: as duas linhas, o estorno negativo; cobrança pelo líquido",
     "Q-AB 3 11:38: 'também entra, com valor negativo'; Q-N 3 09:44: 'A venda e o estorno se anulam'",
     "test_divergencias::test_venda_divergente_estornada_no_mes_lista_as_duas_com_sinal"),
    ("PIX de 18.240: remessa de outubro", "Q-N 5 09:44: 'A operação sai em outubro.'",
     "test_extratos::test_pix_de_18240_e_acompanhamento_da_remessa_de_outubro"),
    ("AN88445172 e as outras 3 antecipações da Casa: isentas pela data da antecipação",
     "Q-AI 13:34: 'Vale pela data da antecipação.'",
     "test_casos_ouro::test_antecipacao_da_casa_isenta_pela_data_dela"),
    ("TX88447011 (e os outros 6 estornos do 06 com bandeira trocada): sem pendência nem aviso",
     "Q-AK 14:08: 'Bandeira não muda a taxa para a gente.'",
     "test_casos_ouro::test_bandeira_trocada_no_estorno_nao_abre_pendencia"),
]


@pytest.mark.caso_ouro
@pytest.mark.parametrize("regra", ["checkout.arredondamento_comissao_contratada", "remessa.arredondamento_participacao"])
def test_meio_centavo_vai_para_cima(regra):
    """Q-H a (Helena 21:13): 'Arredondamento comum para o centavo. Meio centavo vai para cima, e no negativo vale a
    mesma regra com o sinal: -0,005 vira -0,01.' O modo vem do regras.yaml: se a regra mudar errado, quebra aqui."""
    modo = modo_arredondamento(valor_da_regra(carregar_regras(RAIZ / "regras.yaml"), regra))
    assert centavos(Decimal("131.005"), modo) == Decimal("131.01")
    assert centavos(Decimal("-0.005"), modo) == Decimal("-0.01")
    assert centavos(Decimal("0.005"), modo) == Decimal("0.01")
    assert centavos(Decimal("131.0049"), modo) == Decimal("131.00")  # abaixo do meio não sobe (não é teto)


@pytest.mark.caso_ouro
def test_registro_de_casos_ouro_completo():
    """Cada caso da tabela aponta para um teste que existe e tem a marca caso_ouro."""
    for caso, fala, alvo in CASOS:
        modulo, nome = alvo.split("::")
        funcao = getattr(importlib.import_module(modulo), nome, None)
        assert funcao is not None, f"{caso}: teste {alvo} não existe"
        marcas = {m.name for m in getattr(funcao, "pytestmark", [])}
        assert "caso_ouro" in marcas, f"{caso}: {alvo} sem a marca caso_ouro"
        assert fala.split(" ")[0] and Path(RAIZ / "tests" / f"{modulo}.py").exists()


@pytest.mark.caso_ouro
def test_antecipacao_da_casa_isenta_pela_data_dela(checkout):
    """Q-AI (Helena 13:34): 'Vale pela data da antecipação. A antecipação é um serviço que a gente presta no dia em
    que ela acontece: se foi em setembro, está dentro da isenção. Não precisa ir atrás das vendas de origem.'
    AN88445172 (09/09) não traz as vendas de origem: taxa 0 pela data dela; o que a Orbe cobrou volta ao lojista."""
    antecipacoes = {r: c for r, c in checkout.por_transacao.items()
                    if c.cnpj == "00520815000100" and c.transacao.tipo_lancamento == "ANTECIPACAO"}
    assert sorted(antecipacoes) == ["AN88445172", "AN88445486", "AN88445740", "AN88445802"]
    for c in antecipacoes.values():
        assert c.data_ref == c.transacao.data_movimento and c.data_ref.month == 9
        assert (c.taxa_contratada, c.comissao) == (Decimal("0"), Decimal("0.00"))
    an = antecipacoes["AN88445172"]
    assert (an.transacao.valor_bruto, an.transacao.valor_taxa) == (Decimal("4937.92"), Decimal("103.69"))


BANDEIRA_TROCADA = ["TX88447011", "TX88447030", "TX88447044", "TX88447057", "TX88447070", "TX88447093", "TX88447109"]


@pytest.fixture(scope="module")
def fechamento(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("casos_ouro")
    return pasta, executar(DADOS, pasta, RAIZ / "regras.yaml")


def _linhas(pasta, nome):
    import csv
    with open(pasta / nome, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


@pytest.mark.caso_ouro
def test_bandeira_trocada_no_estorno_nao_abre_pendencia(fechamento):
    """Q-AK (Helena 14:08): 'Bandeira não muda a taxa para a gente. A Orbe às vezes troca a bandeira no estorno; não
    precisa contestar nem abrir pendência. Sigam com o vínculo pela referência, como vocês fizeram.'
    TX88447011 (06, VISA) estorna TX88413573 (01, AMEX, débito de 03/09 na Maple): −420,77 × 1,49% = −6,27."""
    pasta, resumo = fechamento
    textos = [str(a) for a in resumo["avisos"]]
    for nome in ("pendencias.csv", "divergencias_taxa.csv", "contestacao_ponte.csv"):
        conteudo = (pasta / nome).read_text(encoding="utf-8")
        assert not any(i in conteudo for i in BANDEIRA_TROCADA), nome
    assert not any(i in a for i in BANDEIRA_TROCADA for a in textos)
    (estorno,) = [l for l in _linhas(pasta, "rastro.csv") if l["ref_origem"] == "TX88447011" and l["id_saida"].startswith("COM-")]
    assert (estorno["id_saida"], estorno["valor"], estorno["taxa_contratada_pct"]) == ("COM-34671260000100-CHECKOUT", "-6.27", "1.49")
    assert estorno["nota"].startswith("estorno de TX88413573 (venda de 2026-09-03)")
