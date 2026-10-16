"""Classificação por IA, só nas sobras sem regra clara.

Responsabilidade: pedir ao modelo uma conta analítica do plano com saída estruturada
(pydantic), registrar `metodo=IA` e `confianca`, com cache em disco para que a
reexecução seja determinística. Abaixo do limiar de `regras.yaml` → `HUMANO` +
pendência. A chave da API vem só do `.env.local`; sem chave, o que sobrar vira HUMANO.
"""

from __future__ import annotations

from tarvo.modelo import ContaContabil, LancamentoBancario


def classificar_por_ia(
    sobras: list[LancamentoBancario], plano: list[ContaContabil], regras: dict
) -> list[dict]:
    """Classifica as sobras; cada item com metodo, conta_codigo e confianca."""
    raise NotImplementedError
