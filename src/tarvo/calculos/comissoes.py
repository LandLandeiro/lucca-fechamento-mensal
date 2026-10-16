"""Comissão por lojista e linha de negócio (CHECKOUT e REMESSA).

Responsabilidade: compor a comissão segundo as regras confirmadas (quais lançamentos
entram e com qual sinal; base e participação da remessa) e gerar o rastro por linha
de origem. `id_saida`: `COM-<cnpj>-<CHECKOUT|REMESSA>`.
"""

from __future__ import annotations

from tarvo.modelo import ItemRastro, OperacaoPonte, TransacaoOrbe


def comissao_checkout(
    transacoes: list[TransacaoOrbe], cadastro: dict, regras: dict
) -> tuple[list[dict], list[ItemRastro]]:
    """Comissão CHECKOUT por lojista, com rastro."""
    raise NotImplementedError


def comissao_remessa(
    operacoes: list[OperacaoPonte], cadastro: dict, regras: dict
) -> tuple[list[dict], list[ItemRastro]]:
    """Comissão REMESSA por lojista, com rastro."""
    raise NotImplementedError
