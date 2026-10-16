"""Carrega e valida `regras.yaml`.

Responsabilidade: regra de negócio é dado, não código. Este módulo só lê o YAML,
confere que cada regra tem `valor`, `status` (SEI | ASSUMO | CONFIRMADO), `fonte` e
`pergunta_ref`, e expõe os valores. Regra sem valor bloqueia o cálculo que depende
dela (vira pendência), em vez de o código inventar um padrão.
"""

from __future__ import annotations

from pathlib import Path

STATUS_VALIDOS = ("SEI", "ASSUMO", "CONFIRMADO")


def carregar_regras(caminho: Path) -> dict:
    """Lê o YAML e valida a estrutura."""
    raise NotImplementedError


def valor_da_regra(regras: dict, chave: str):
    """Valor de uma regra; erro explícito se a regra estiver vazia."""
    raise NotImplementedError
