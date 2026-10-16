"""Cadastro unificado de lojistas e taxas contratadas com vigência.

Responsabilidade: normalizar CNPJ para 14 dígitos (com validação de DV), ligar EC Orbe
→ CNPJ só por chave (nunca por semelhança de nome) e interpretar a tabela de taxas
(faixas, vigência, "padrão") segundo `regras.yaml`. O que não tiver chave confiável
vira pendência.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from tarvo.modelo import Lojista, TaxaContratada


def normalizar_cnpj(valor: object) -> str | None:
    """Devolve o CNPJ com 14 dígitos, ou None se não for possível."""
    raise NotImplementedError


def cnpj_valido(cnpj: str) -> bool:
    """Confere os dígitos verificadores do CNPJ."""
    raise NotImplementedError


def montar_cadastro(taxas: list[TaxaContratada], regras: dict) -> dict[str, Lojista]:
    """Monta o cadastro por CNPJ."""
    raise NotImplementedError


def lojista_por_ec(cadastro: dict[str, Lojista], ec: str) -> Lojista | None:
    """Busca o lojista pelo EC da Orbe (só correspondência exata)."""
    raise NotImplementedError


def taxa_contratada(
    taxas: list[TaxaContratada], cnpj: str, produto: str, data_ref: date, regras: dict
) -> Decimal | None:
    """Taxa contratada vigente para o produto na data de referência, ou None."""
    raise NotImplementedError
