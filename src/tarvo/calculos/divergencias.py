"""Divergências entre taxa contratada e taxa aplicada, transação por transação.

Responsabilidade: comparar a taxa aplicada com a contratada vigente e calcular a
diferença em R$ com o mesmo arredondamento da fonte; reportar só diferença real
(alarme falso conta contra). `id_saida`: `DIV-<ref_origem>`.
"""

from __future__ import annotations

from tarvo.modelo import ItemRastro, OperacaoPonte, TransacaoOrbe


def divergencias_checkout(
    transacoes: list[TransacaoOrbe], cadastro: dict, taxas: list, regras: dict
) -> tuple[list[dict], list[ItemRastro]]:
    """Divergências de MDR e antecipação na Orbe."""
    raise NotImplementedError


def divergencias_remessa(
    operacoes: list[OperacaoPonte], cadastro: dict, taxas: list, regras: dict
) -> tuple[list[dict], list[ItemRastro]]:
    """Divergências de spread na Ponte."""
    raise NotImplementedError
