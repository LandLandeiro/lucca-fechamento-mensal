"""Pendências: tudo que exige uma pessoa, com motivo e quem decide.

Responsabilidade: reunir as pendências geradas por cadastro, cálculos e classificação
(lojista sem chave, regra vazia, duplicidade, spread negativo, lançamento sem
classificação segura etc.) num formato único, sem repetir.
`id_saida`: `PEN-<tipo>-<ref_origem>`.
"""

from __future__ import annotations

from tarvo.modelo import Pendencia


def consolidar_pendencias(*listas: list[Pendencia]) -> list[Pendencia]:
    """Junta as pendências de todas as etapas, sem repetição."""
    raise NotImplementedError
