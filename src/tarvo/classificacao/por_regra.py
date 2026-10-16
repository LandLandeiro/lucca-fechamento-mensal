"""Classificação determinística por padrões de descrição (definidos em `regras.yaml`)."""

from __future__ import annotations

from tarvo.modelo import ContaContabil, LancamentoBancario


def classificar_por_regra(
    lancamentos: list[LancamentoBancario], plano: list[ContaContabil], regras: dict
) -> tuple[list[dict], list[LancamentoBancario]]:
    """Devolve (classificados com metodo=REGRA, sobras sem regra)."""
    raise NotImplementedError
