"""Validador da saída: recusa total que não fecha.

Responsabilidade: conferir os CSVs escritos (colunas obrigatórias, separador, ponto
decimal, datas ISO, CNPJ com 14 dígitos, enums) e que a soma do `rastro.csv` por
`id_saida` bate com o número reportado em cada arquivo.
"""

from __future__ import annotations

from pathlib import Path


def validar_saida(pasta: Path) -> list[str]:
    """Devolve a lista de erros encontrados (vazia = saída válida)."""
    raise NotImplementedError
