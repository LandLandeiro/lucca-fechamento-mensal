"""Fixtures compartilhadas: o pipeline do nível mínimo rodado uma vez sobre o data pack real."""

import os
from pathlib import Path

import pytest

from tarvo.cadastro import montar_cadastro
from tarvo.calculos.comissoes import comissao_checkout
from tarvo.leitores.orbe import ler_orbe
from tarvo.leitores.taxas import ler_taxas_vigentes
from tarvo.regras import carregar_regras, valor_da_regra

RAIZ = Path(__file__).resolve().parents[1]
DADOS = RAIZ / "data"
ORBE = DADOS / "01_orbe_relatorio_comissoes_set2026.csv"
TAXAS = DADOS / "02_tabela_taxas_contratadas.xlsx"

# testes nunca usam rede: a IA só responde pelo cache commitado ou por um cliente mockado
os.environ["TARVO_SEM_REDE"] = "1"


@pytest.fixture(scope="session")
def regras():
    return carregar_regras(RAIZ / "regras.yaml")


@pytest.fixture(scope="session")
def orbe():
    return ler_orbe(ORBE)


@pytest.fixture(scope="session")
def taxas(regras):
    colunas = list(valor_da_regra(regras, "taxas.coluna_por_produto").values())
    return ler_taxas_vigentes(
        TAXAS, valor_da_regra(regras, "taxas.aba_vigente"), colunas, valor_da_regra(regras, "taxas.casas_decimais_taxa")
    )


@pytest.fixture(scope="session")
def cadastro(taxas, regras):
    return montar_cadastro(taxas.linhas, regras, TAXAS.name)


@pytest.fixture(scope="session")
def checkout(orbe, cadastro, regras):
    return comissao_checkout(orbe.transacoes, cadastro, regras)
